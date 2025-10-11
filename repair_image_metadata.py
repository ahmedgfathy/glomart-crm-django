#!/usr/bin/env python3
"""
Database Image Metadata Repair Script

This script analyzes and fixes the JSON truncation issue where property images
are cut off at 191 characters, preventing display of multiple images per property.

The script will:
1. Analyze the current state of image metadata
2. Scan actual image files on disk 
3. Rebuild the property-to-image relationships
4. Update the database with complete image metadata
"""

import os
import sys
import json
import re
import pymysql
import paramiko
from pathlib import Path
from datetime import datetime

# Configuration for both local and production
CONFIG = {
    'local': {
        'database': {
            'host': 'localhost',
            'user': 'root',
            'password': 'zerocall',
            'database': 'django_db_glomart_rs',
            'port': 3306
        },
        'image_path': '/Users/ahmedgomaa/Downloads/crm/public/properties/images',
        'django_path': '/Users/ahmedgomaa/Downloads/crm'
    },
    'production': {
        'database': {
            'host': '5.180.148.92',
            'user': 'root',
            'password': 'ZeroCall20!@HH##1655&&',
            'database': 'django_db_glomart_rs',
            'port': 3306
        },
        'image_path': '/var/www/glomart-crm/public/properties/images',
        'django_path': '/var/www/glomart-crm',
        'ssh': {
            'host': '5.180.148.92',
            'username': 'root',
            'password': 'ZeroCall20!@HH##1655&&'
        }
    }
}

def connect_to_database(config):
    """Connect to MariaDB database"""
    try:
        connection = pymysql.connect(
            host=config['database']['host'],
            user=config['database']['user'],
            password=config['database']['password'],
            database=config['database']['database'],
            port=config['database']['port'],
            charset='utf8mb4'
        )
        print(f"✅ Connected to database: {config['database']['host']}")
        return connection
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def analyze_current_state(connection):
    """Analyze the current state of image metadata in the database"""
    print("\n🔍 ANALYZING CURRENT DATABASE STATE")
    print("=" * 60)
    
    cursor = connection.cursor()
    
    # Get total properties
    cursor.execute("SELECT COUNT(*) FROM properties_property")
    total_properties = cursor.fetchone()[0]
    
    # Get properties with image data
    cursor.execute("SELECT COUNT(*) FROM properties_property WHERE primary_image IS NOT NULL AND primary_image != '' AND primary_image != '[]'")
    properties_with_images = cursor.fetchone()[0]
    
    # Get properties with truncated JSON (common length = 191)
    cursor.execute("SELECT COUNT(*) FROM properties_property WHERE LENGTH(primary_image) = 191")
    truncated_properties = cursor.fetchone()[0]
    
    # Get properties with complete JSON (multiple images)
    cursor.execute("SELECT COUNT(*) FROM properties_property WHERE primary_image LIKE '%},{%'")
    multi_image_properties = cursor.fetchone()[0]
    
    # Sample of truncated data
    cursor.execute("SELECT property_id, LENGTH(primary_image), primary_image FROM properties_property WHERE LENGTH(primary_image) = 191 LIMIT 3")
    truncated_samples = cursor.fetchall()
    
    print(f"📊 Database Statistics:")
    print(f"   Total Properties: {total_properties}")
    print(f"   Properties with image data: {properties_with_images}")
    print(f"   Properties with truncated JSON (191 chars): {truncated_properties}")
    print(f"   Properties with multiple images: {multi_image_properties}")
    print(f"   Truncation rate: {(truncated_properties/properties_with_images*100):.1f}%")
    
    print(f"\n📝 Sample Truncated Data:")
    for prop_id, length, json_data in truncated_samples:
        print(f"   {prop_id}: {length} chars - {json_data[:100]}...")
    
    return {
        'total_properties': total_properties,
        'properties_with_images': properties_with_images,
        'truncated_properties': truncated_properties,
        'multi_image_properties': multi_image_properties
    }

def scan_image_files(image_path, is_remote=False, ssh=None):
    """Scan actual image files on disk"""
    print(f"\n📁 SCANNING IMAGE FILES: {image_path}")
    print("=" * 60)
    
    if is_remote and ssh:
        # Remote scanning via SSH
        stdin, stdout, stderr = ssh.exec_command(f'find {image_path} -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | head -20')
        sample_files = stdout.read().decode().strip().split('\n')
        
        stdin, stdout, stderr = ssh.exec_command(f'find {image_path} -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | wc -l')
        total_files = int(stdout.read().decode().strip())
        
    else:
        # Local scanning
        if not os.path.exists(image_path):
            print(f"❌ Image directory does not exist: {image_path}")
            return []
        
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            image_files.extend(Path(image_path).glob(ext))
            image_files.extend(Path(image_path).glob(ext.upper()))
        
        total_files = len(image_files)
        sample_files = [str(f.name) for f in image_files[:20]]
    
    print(f"📷 Found {total_files} image files")
    print(f"🔍 Sample files:")
    for file in sample_files[:10]:
        print(f"   {file}")
    
    return sample_files

def analyze_image_naming_pattern(image_files):
    """Analyze the naming pattern of image files to understand the relationship"""
    print(f"\n🔍 ANALYZING IMAGE NAMING PATTERNS")
    print("=" * 60)
    
    patterns = {}
    
    for file in image_files:
        if isinstance(file, str):
            filename = os.path.basename(file)
        else:
            filename = str(file)
            
        # Extract potential ID patterns
        if len(filename) >= 20:  # Appwrite style IDs
            potential_id = filename.replace('.jpg', '').replace('.jpeg', '').replace('.png', '')
            prefix = potential_id[:8] if len(potential_id) >= 8 else potential_id
            patterns[prefix] = patterns.get(prefix, 0) + 1
    
    print(f"📊 ID Prefix Analysis (top 10):")
    sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
    for prefix, count in sorted_patterns[:10]:
        print(f"   {prefix}*: {count} files")
    
    return patterns

def extract_image_ids_from_json(json_data):
    """Extract image IDs from corrupted JSON using regex"""
    if not json_data:
        return []
    
    # Try JSON parsing first
    try:
        if json_data.startswith('['):
            images = json.loads(json_data)
            return [img.get('id') for img in images if img.get('id')]
    except json.JSONDecodeError:
        pass
    
    # Regex fallback for corrupted JSON
    id_matches = re.findall(r'"id":"([^"]+)"', json_data)
    return id_matches

def create_image_property_mapping(connection, image_files):
    """Create a mapping between images and properties based on existing metadata"""
    print(f"\n🔗 CREATING IMAGE-PROPERTY MAPPING")
    print("=" * 60)
    
    cursor = connection.cursor()
    cursor.execute("SELECT property_id, primary_image FROM properties_property WHERE primary_image IS NOT NULL AND primary_image != '' AND primary_image != '[]'")
    
    property_images = {}
    available_images = set()
    
    # Build set of available image files
    for file in image_files:
        if isinstance(file, str):
            filename = os.path.basename(file).replace('.jpg', '').replace('.jpeg', '').replace('.png', '')
            available_images.add(filename)
    
    mapped_count = 0
    
    for property_id, json_data in cursor.fetchall():
        image_ids = extract_image_ids_from_json(json_data)
        
        # Find which IDs have corresponding files
        existing_images = []
        for image_id in image_ids:
            if image_id in available_images:
                existing_images.append(image_id)
        
        if existing_images:
            property_images[property_id] = existing_images
            mapped_count += 1
    
    print(f"📊 Mapping Results:")
    print(f"   Properties with mappable images: {mapped_count}")
    print(f"   Total available image files: {len(available_images)}")
    
    # Show sample mappings
    print(f"\n📝 Sample Mappings:")
    for prop_id, images in list(property_images.items())[:5]:
        print(f"   {prop_id}: {len(images)} images -> {images[:3]}{'...' if len(images) > 3 else ''}")
    
    return property_images

def rebuild_complete_json(property_images):
    """Rebuild complete JSON metadata for properties"""
    print(f"\n🔧 REBUILDING COMPLETE JSON METADATA")
    print("=" * 60)
    
    rebuilt_metadata = {}
    
    for property_id, image_ids in property_images.items():
        complete_images = []
        
        for image_id in image_ids:
            image_obj = {
                "id": image_id,
                "fileUrl": f"/property-images/{image_id}.jpg",
                "originalUrl": f"/property-images/{image_id}.jpg"
            }
            complete_images.append(image_obj)
        
        # Create complete JSON
        complete_json = json.dumps(complete_images)
        rebuilt_metadata[property_id] = complete_json
    
    print(f"✅ Rebuilt metadata for {len(rebuilt_metadata)} properties")
    
    # Show sample rebuilt JSON
    sample_property = list(rebuilt_metadata.keys())[0]
    sample_json = rebuilt_metadata[sample_property]
    print(f"\n📝 Sample Rebuilt JSON:")
    print(f"   Property: {sample_property}")
    print(f"   Length: {len(sample_json)} chars (vs original 191)")
    print(f"   JSON: {sample_json[:200]}...")
    
    return rebuilt_metadata

def update_database(connection, rebuilt_metadata, dry_run=True):
    """Update the database with rebuilt metadata"""
    action = "DRY RUN" if dry_run else "UPDATING"
    print(f"\n💾 {action}: DATABASE UPDATE")
    print("=" * 60)
    
    cursor = connection.cursor()
    updated_count = 0
    
    for property_id, complete_json in rebuilt_metadata.items():
        if dry_run:
            print(f"   Would update {property_id}: {len(complete_json)} chars")
        else:
            try:
                cursor.execute(
                    "UPDATE properties_property SET primary_image = %s WHERE property_id = %s",
                    (complete_json, property_id)
                )
                updated_count += 1
            except Exception as e:
                print(f"   ❌ Failed to update {property_id}: {e}")
    
    if not dry_run:
        connection.commit()
        print(f"✅ Updated {updated_count} properties in database")
    else:
        print(f"📝 Would update {len(rebuilt_metadata)} properties")
    
    return updated_count

def main():
    """Main repair function"""
    print("🔧 DATABASE IMAGE METADATA REPAIR TOOL")
    print("=" * 60)
    
    # Ask user which environment to fix
    env = input("Select environment (local/production/both): ").lower().strip()
    if env not in ['local', 'production', 'both']:
        print("❌ Invalid environment. Choose: local, production, or both")
        return
    
    dry_run = input("Dry run? (y/n): ").lower().strip() == 'y'
    
    environments = [env] if env != 'both' else ['local', 'production']
    
    for current_env in environments:
        print(f"\n🌍 PROCESSING ENVIRONMENT: {current_env.upper()}")
        print("=" * 60)
        
        config = CONFIG[current_env]
        
        # Connect to database
        connection = connect_to_database(config)
        if not connection:
            continue
        
        try:
            # Step 1: Analyze current state
            stats = analyze_current_state(connection)
            
            # Step 2: Scan image files
            if current_env == 'production':
                # SSH connection for production
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    hostname=config['ssh']['host'],
                    username=config['ssh']['username'],
                    password=config['ssh']['password']
                )
                image_files = scan_image_files(config['image_path'], is_remote=True, ssh=ssh)
                ssh.close()
            else:
                image_files = scan_image_files(config['image_path'])
            
            if not image_files:
                print(f"❌ No image files found for {current_env}")
                continue
            
            # Step 3: Analyze naming patterns
            patterns = analyze_image_naming_pattern(image_files)
            
            # Step 4: Create property-image mapping
            property_images = create_image_property_mapping(connection, image_files)
            
            # Step 5: Rebuild complete JSON
            rebuilt_metadata = rebuild_complete_json(property_images)
            
            # Step 6: Update database
            update_database(connection, rebuilt_metadata, dry_run=dry_run)
            
        finally:
            connection.close()
    
    print(f"\n🎉 REPAIR PROCESS COMPLETED!")
    if dry_run:
        print("📝 This was a dry run. Re-run with dry_run=False to apply changes.")
    else:
        print("✅ Database has been updated. Check your application!")

if __name__ == "__main__":
    main()