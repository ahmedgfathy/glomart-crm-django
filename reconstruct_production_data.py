#!/usr/bin/env python3
"""
Production Image Data Reconstruction Script
Restores complete image JSON data from SQLite to MariaDB on production server
"""

import sqlite3
import pymysql
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

class ProductionImageDataReconstructor:
    def __init__(self):
        # Production server configuration
        self.production_config = {
            'host': '5.180.148.92',
            'user': 'root', 
            'password': 'ZeroCall20!@HH##1655&&',
            'database': 'django_db_glomart_rs',
            'port': 3306,
            'charset': 'utf8mb4'
        }
        
        # Local configuration for source data
        self.local_sqlite_path = '/Users/ahmedgomaa/Downloads/crm/db.sqlite3'
        
    def extract_complete_data_local(self) -> Dict[str, str]:
        """Extract complete image data from local SQLite"""
        complete_data = {}
        
        if not os.path.exists(self.local_sqlite_path):
            raise FileNotFoundError(f"Local SQLite database not found: {self.local_sqlite_path}")
        
        sqlite_conn = sqlite3.connect(self.local_sqlite_path)
        cursor = sqlite_conn.cursor()
        
        cursor.execute('''
            SELECT property_id, primary_image 
            FROM properties_property 
            WHERE primary_image IS NOT NULL 
            AND primary_image != "" 
            AND primary_image != "[]"
            AND LENGTH(primary_image) > 191
        ''')
        
        for property_id, primary_image in cursor.fetchall():
            # Validate JSON
            try:
                images = json.loads(primary_image)
                if isinstance(images, list) and images:
                    complete_data[property_id] = primary_image
            except json.JSONDecodeError:
                print(f"⚠️  Skipping {property_id}: Invalid JSON")
        
        sqlite_conn.close()
        return complete_data
    
    def analyze_production_truncation(self, mariadb_conn) -> Dict:
        """Analyze the extent of truncation on production"""
        cursor = mariadb_conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as total_properties,
                COUNT(CASE WHEN primary_image IS NOT NULL AND primary_image != "" AND primary_image != "[]" THEN 1 END) as with_images,
                COUNT(CASE WHEN CHAR_LENGTH(primary_image) = 191 THEN 1 END) as exactly_191_chars,
                AVG(CHAR_LENGTH(primary_image)) as avg_length,
                MAX(CHAR_LENGTH(primary_image)) as max_length
            FROM properties_property
            WHERE primary_image IS NOT NULL AND primary_image != ""
        ''')
        stats = cursor.fetchone()
        
        return {
            'total_properties': stats[0],
            'with_images': stats[1],
            'exactly_191_chars': stats[2],
            'avg_length': stats[3],
            'max_length': stats[4]
        }
    
    def validate_reconstruction(self, mariadb_conn, property_id: str, new_data: str) -> bool:
        """Validate that reconstruction would fix the property"""
        cursor = mariadb_conn.cursor()
        cursor.execute('SELECT CHAR_LENGTH(primary_image) FROM properties_property WHERE property_id = %s', (property_id,))
        result = cursor.fetchone()
        
        if result and result[0] == 191:  # Currently truncated
            try:
                json.loads(new_data)  # Validate JSON
                return True
            except json.JSONDecodeError:
                return False
        return False
    
    def reconstruct_production_data(self, dry_run: bool = True) -> Dict:
        """Reconstruct the truncated data on production"""
        
        print("🔧 Production Image Data Reconstruction")
        print("=" * 50)
        
        # Extract complete data from local SQLite
        print("🔍 Extracting complete data from local SQLite...")
        complete_data = self.extract_complete_data_local()
        print(f"✅ Found {len(complete_data)} properties with complete data")
        
        # Connect to production MariaDB
        print("📡 Connecting to production MariaDB...")
        mariadb_conn = pymysql.connect(**self.production_config)
        print("✅ Production database connection established")
        
        # Analyze production truncation
        print("🔍 Analyzing production truncation...")
        analysis = self.analyze_production_truncation(mariadb_conn)
        print(f"📊 Production: {analysis['with_images']} properties with images")
        print(f"📊 Production: {analysis['exactly_191_chars']} properties truncated at 191 chars")
        
        # Validate each reconstruction
        print("🔍 Validating reconstruction candidates...")
        valid_reconstructions = {}
        for property_id, complete_json in complete_data.items():
            if self.validate_reconstruction(mariadb_conn, property_id, complete_json):
                valid_reconstructions[property_id] = complete_json
        
        print(f"✅ {len(valid_reconstructions)} properties validated for reconstruction")
        
        reconstruction_results = {
            'total_candidates': len(complete_data),
            'valid_reconstructions': len(valid_reconstructions),
            'analysis': analysis,
            'executed': 0,
            'errors': []
        }
        
        if not dry_run and valid_reconstructions:
            print(f"\n🚀 Executing production reconstruction for {len(valid_reconstructions)} properties...")
            
            mariadb_cursor = mariadb_conn.cursor()
            for property_id, complete_json in valid_reconstructions.items():
                try:
                    mariadb_cursor.execute(
                        'UPDATE properties_property SET primary_image = %s WHERE property_id = %s',
                        (complete_json, property_id)
                    )
                    reconstruction_results['executed'] += 1
                    if reconstruction_results['executed'] % 100 == 0:
                        print(f"   📈 Progress: {reconstruction_results['executed']}/{len(valid_reconstructions)} properties")
                except Exception as e:
                    error_msg = f"Error updating {property_id}: {str(e)}"
                    reconstruction_results['errors'].append(error_msg)
                    print(f"   ❌ {error_msg}")
            
            mariadb_conn.commit()
            print(f"✅ Production reconstruction complete: {reconstruction_results['executed']} properties updated")
            
            if reconstruction_results['errors']:
                print(f"⚠️  {len(reconstruction_results['errors'])} errors occurred")
        
        elif dry_run:
            print("\n🔎 DRY RUN - No changes made to production database")
            print("   Use reconstruct_production_data(dry_run=False) to execute reconstruction")
            
            # Show sample of what would be reconstructed
            print("\n📝 Sample reconstruction preview:")
            for i, (property_id, complete_json) in enumerate(list(valid_reconstructions.items())[:3]):
                try:
                    images = json.loads(complete_json)
                    print(f"   🏠 {property_id}: {len(images)} images ({len(complete_json)} chars)")
                    for j, img in enumerate(images[:2]):
                        print(f"      📸 {j+1}: {img.get('fileUrl', 'N/A')}")
                    if len(images) > 2:
                        print(f"      ... and {len(images) - 2} more images")
                except json.JSONDecodeError:
                    print(f"   ❌ {property_id}: Invalid JSON")
        
        mariadb_conn.close()
        return reconstruction_results
    
    def verify_production_reconstruction(self) -> Dict:
        """Verify the reconstruction was successful on production"""
        mariadb_conn = pymysql.connect(**self.production_config)
        cursor = mariadb_conn.cursor()
        
        # Check how many properties still have 191-char truncation
        cursor.execute('''
            SELECT COUNT(*) 
            FROM properties_property 
            WHERE CHAR_LENGTH(primary_image) = 191
            AND primary_image IS NOT NULL 
            AND primary_image != ""
        ''')
        still_truncated = cursor.fetchone()[0]
        
        # Check how many now have complete JSON
        cursor.execute('''
            SELECT COUNT(*) 
            FROM properties_property 
            WHERE CHAR_LENGTH(primary_image) > 191
            AND primary_image IS NOT NULL 
            AND primary_image != ""
        ''')
        now_complete = cursor.fetchone()[0]
        
        # Sample verification
        cursor.execute('''
            SELECT property_id, CHAR_LENGTH(primary_image), primary_image 
            FROM properties_property 
            WHERE CHAR_LENGTH(primary_image) > 191
            ORDER BY CHAR_LENGTH(primary_image) DESC 
            LIMIT 5
        ''')
        
        samples = []
        for property_id, length, data in cursor.fetchall():
            try:
                images = json.loads(data)
                samples.append({
                    'property_id': property_id,
                    'length': length,
                    'image_count': len(images),
                    'valid_json': True
                })
            except json.JSONDecodeError:
                samples.append({
                    'property_id': property_id,
                    'length': length,
                    'image_count': 0,
                    'valid_json': False
                })
        
        mariadb_conn.close()
        return {
            'still_truncated': still_truncated,
            'now_complete': now_complete,
            'samples': samples
        }

def main():
    """Main reconstruction process for production"""
    reconstructor = ProductionImageDataReconstructor()
    
    try:
        # Run reconstruction (dry run first)
        print("🔍 PHASE 1: PRODUCTION DRY RUN ANALYSIS")
        print("=" * 50)
        dry_run_results = reconstructor.reconstruct_production_data(dry_run=True)
        
        # Ask for confirmation
        print("\n" + "=" * 50)
        if dry_run_results['valid_reconstructions'] > 0:
            response = input(f"🚀 Execute PRODUCTION reconstruction for {dry_run_results['valid_reconstructions']} properties? (y/N): ").strip().lower()
            
            if response == 'y':
                print("🔄 PHASE 2: EXECUTING PRODUCTION RECONSTRUCTION")
                print("=" * 50)
                results = reconstructor.reconstruct_production_data(dry_run=False)
                
                if results['executed'] > 0:
                    print("\n" + "=" * 50)
                    print("🔍 PHASE 3: PRODUCTION VERIFICATION")
                    print("=" * 50)
                    verification = reconstructor.verify_production_reconstruction()
                    
                    print(f"📊 Production Verification Results:")
                    print(f"   Still truncated: {verification['still_truncated']} properties")
                    print(f"   Now complete: {verification['now_complete']} properties")
                    print(f"   Sample verification:")
                    for sample in verification['samples']:
                        status = "✅" if sample['valid_json'] else "❌"
                        print(f"      {status} {sample['property_id']}: {sample['image_count']} images ({sample['length']} chars)")
            else:
                print("❌ Production reconstruction cancelled by user")
        else:
            print("ℹ️  No properties found for production reconstruction")
        
        print("\n✅ All production operations completed successfully!")
        
    except Exception as e:
        print(f"❌ Production error: {e}")

if __name__ == '__main__':
    main()