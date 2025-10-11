#!/usr/bin/env python3
"""
Comprehensive Image Data Reconstruction Script
Restores complete image JSON data from SQLite to MariaDB
"""

import sqlite3
import pymysql
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple

class ImageDataReconstructor:
    def __init__(self):
        self.crm_path = Path('.')
        self.sqlite_paths = [self.crm_path / 'db.sqlite3', self.crm_path / 'local_db.sqlite3']
        self.mariadb_config = {
            'host': 'localhost',
            'user': 'root', 
            'password': 'zerocall',
            'database': 'django_db_glomart_rs',
            'port': 3306,
            'charset': 'utf8mb4'
        }
        
    def find_sqlite_database(self) -> str:
        """Find available SQLite database"""
        for path in self.sqlite_paths:
            if path.exists():
                return str(path)
        raise FileNotFoundError("No SQLite database found")
    
    def analyze_truncation(self, sqlite_conn, mariadb_conn) -> Dict:
        """Analyze the extent of truncation"""
        analysis = {}
        
        # SQLite stats
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute('''
            SELECT 
                COUNT(*) as total_properties,
                COUNT(CASE WHEN primary_image IS NOT NULL AND primary_image != "" AND primary_image != "[]" THEN 1 END) as with_images,
                COUNT(CASE WHEN LENGTH(primary_image) > 191 THEN 1 END) as truncated_in_mariadb,
                AVG(LENGTH(primary_image)) as avg_length,
                MAX(LENGTH(primary_image)) as max_length
            FROM properties_property
            WHERE primary_image IS NOT NULL AND primary_image != ""
        ''')
        sqlite_stats = sqlite_cursor.fetchone()
        
        # MariaDB stats
        mariadb_cursor = mariadb_conn.cursor()
        mariadb_cursor.execute('''
            SELECT 
                COUNT(*) as total_properties,
                COUNT(CASE WHEN primary_image IS NOT NULL AND primary_image != "" AND primary_image != "[]" THEN 1 END) as with_images,
                COUNT(CASE WHEN CHAR_LENGTH(primary_image) = 191 THEN 1 END) as exactly_191_chars,
                AVG(CHAR_LENGTH(primary_image)) as avg_length,
                MAX(CHAR_LENGTH(primary_image)) as max_length
            FROM properties_property
            WHERE primary_image IS NOT NULL AND primary_image != ""
        ''')
        mariadb_stats = mariadb_cursor.fetchone()
        
        analysis = {
            'sqlite': {
                'total_properties': sqlite_stats[0],
                'with_images': sqlite_stats[1],
                'truncated_in_mariadb': sqlite_stats[2],
                'avg_length': sqlite_stats[3],
                'max_length': sqlite_stats[4]
            },
            'mariadb': {
                'total_properties': mariadb_stats[0],
                'with_images': mariadb_stats[1],
                'exactly_191_chars': mariadb_stats[2],
                'avg_length': mariadb_stats[3],
                'max_length': mariadb_stats[4]
            }
        }
        
        return analysis
    
    def extract_complete_data(self, sqlite_conn) -> Dict[str, str]:
        """Extract complete image data from SQLite"""
        complete_data = {}
        
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
        
        return complete_data
    
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
    
    def reconstruct_data(self, sqlite_conn, mariadb_conn, dry_run: bool = True) -> Dict:
        """Reconstruct the truncated data"""
        
        print("🔍 Analyzing truncation...")
        analysis = self.analyze_truncation(sqlite_conn, mariadb_conn)
        
        print(f"📊 SQLite: {analysis['sqlite']['with_images']} properties with images")
        print(f"📊 MariaDB: {analysis['mariadb']['exactly_191_chars']} properties truncated at 191 chars")
        print(f"🎯 Target: {analysis['sqlite']['truncated_in_mariadb']} properties need reconstruction")
        
        print("\n🔧 Extracting complete data from SQLite...")
        complete_data = self.extract_complete_data(sqlite_conn)
        print(f"✅ Found {len(complete_data)} properties with complete data")
        
        # Validate each reconstruction
        print("\n🔍 Validating reconstruction candidates...")
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
            print(f"\n🚀 Executing reconstruction for {len(valid_reconstructions)} properties...")
            
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
            print(f"✅ Reconstruction complete: {reconstruction_results['executed']} properties updated")
            
            if reconstruction_results['errors']:
                print(f"⚠️  {len(reconstruction_results['errors'])} errors occurred")
        
        elif dry_run:
            print("\n🔎 DRY RUN - No changes made to database")
            print("   Use reconstruct_data(dry_run=False) to execute reconstruction")
            
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
        
        return reconstruction_results
    
    def verify_reconstruction(self, mariadb_conn, sample_size: int = 10) -> Dict:
        """Verify the reconstruction was successful"""
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
            LIMIT %s
        ''', (sample_size,))
        
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
        
        return {
            'still_truncated': still_truncated,
            'now_complete': now_complete,
            'samples': samples
        }

def main():
    """Main reconstruction process"""
    reconstructor = ImageDataReconstructor()
    
    try:
        print("🔧 Glomart CRM Image Data Reconstruction")
        print("=" * 50)
        
        # Find databases
        sqlite_path = reconstructor.find_sqlite_database()
        print(f"✅ Found SQLite database: {sqlite_path}")
        
        # Connect to databases
        print("📡 Connecting to databases...")
        sqlite_conn = sqlite3.connect(sqlite_path)
        mariadb_conn = pymysql.connect(**reconstructor.mariadb_config)
        print("✅ Database connections established")
        
        # Run reconstruction (dry run first)
        print("\n" + "=" * 50)
        print("🔍 PHASE 1: DRY RUN ANALYSIS")
        print("=" * 50)
        dry_run_results = reconstructor.reconstruct_data(sqlite_conn, mariadb_conn, dry_run=True)
        
        # Ask for confirmation
        print("\n" + "=" * 50)
        if dry_run_results['valid_reconstructions'] > 0:
            response = input(f"🚀 Execute reconstruction for {dry_run_results['valid_reconstructions']} properties? (y/N): ").strip().lower()
            
            if response == 'y':
                print("🔄 PHASE 2: EXECUTING RECONSTRUCTION")
                print("=" * 50)
                results = reconstructor.reconstruct_data(sqlite_conn, mariadb_conn, dry_run=False)
                
                if results['executed'] > 0:
                    print("\n" + "=" * 50)
                    print("🔍 PHASE 3: VERIFICATION")
                    print("=" * 50)
                    verification = reconstructor.verify_reconstruction(mariadb_conn)
                    
                    print(f"📊 Verification Results:")
                    print(f"   Still truncated: {verification['still_truncated']} properties")
                    print(f"   Now complete: {verification['now_complete']} properties")
                    print(f"   Sample verification:")
                    for sample in verification['samples'][:5]:
                        status = "✅" if sample['valid_json'] else "❌"
                        print(f"      {status} {sample['property_id']}: {sample['image_count']} images ({sample['length']} chars)")
            else:
                print("❌ Reconstruction cancelled by user")
        else:
            print("ℹ️  No properties found for reconstruction")
        
        # Close connections
        sqlite_conn.close()
        mariadb_conn.close()
        print("\n✅ All operations completed successfully!")
        
    except FileNotFoundError as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == '__main__':
    main()