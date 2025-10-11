#!/usr/bin/env python3
"""
Generate SQL file for production image data reconstruction
Creates SQL statements that can be executed on production server
"""

import sqlite3
import json
import os
from pathlib import Path

def generate_reconstruction_sql():
    """Generate SQL file for production reconstruction"""
    
    local_sqlite_path = '/Users/ahmedgomaa/Downloads/crm/db.sqlite3'
    output_sql_file = '/Users/ahmedgomaa/Downloads/crm/production_image_reconstruction.sql'
    
    if not os.path.exists(local_sqlite_path):
        print(f"❌ Local SQLite database not found: {local_sqlite_path}")
        return
    
    print("🔧 Generating Production Image Data Reconstruction SQL")
    print("=" * 60)
    
    # Connect to local SQLite
    print("📡 Connecting to local SQLite database...")
    sqlite_conn = sqlite3.connect(local_sqlite_path)
    cursor = sqlite_conn.cursor()
    
    # Extract complete image data
    print("🔍 Extracting complete image data...")
    cursor.execute('''
        SELECT property_id, primary_image 
        FROM properties_property 
        WHERE primary_image IS NOT NULL 
        AND primary_image != "" 
        AND primary_image != "[]"
        AND LENGTH(primary_image) > 191
    ''')
    
    complete_data = {}
    for property_id, primary_image in cursor.fetchall():
        # Validate JSON
        try:
            images = json.loads(primary_image)
            if isinstance(images, list) and images:
                complete_data[property_id] = primary_image
        except json.JSONDecodeError:
            print(f"⚠️  Skipping {property_id}: Invalid JSON")
    
    sqlite_conn.close()
    print(f"✅ Found {len(complete_data)} properties with complete data")
    
    # Generate SQL file
    print("📝 Generating SQL statements...")
    
    with open(output_sql_file, 'w', encoding='utf-8') as f:
        f.write("-- Production Image Data Reconstruction SQL\n")
        f.write("-- Generated from local SQLite database\n")
        f.write(f"-- Total properties to reconstruct: {len(complete_data)}\n")
        f.write("-- Execute this on production MariaDB server\n\n")
        
        f.write("USE django_db_glomart_rs;\n\n")
        
        f.write("-- Start transaction\n")
        f.write("START TRANSACTION;\n\n")
        
        f.write("-- Backup current state (optional)\n")
        f.write("-- CREATE TABLE properties_property_backup AS SELECT * FROM properties_property WHERE CHAR_LENGTH(primary_image) = 191;\n\n")
        
        f.write("-- Image data reconstruction statements\n")
        
        count = 0
        for property_id, complete_json in complete_data.items():
            # Escape single quotes in JSON
            escaped_json = complete_json.replace("'", "''")
            
            f.write(f"UPDATE properties_property SET primary_image = '{escaped_json}' WHERE property_id = '{property_id}' AND CHAR_LENGTH(primary_image) = 191;\n")
            
            count += 1
            if count % 100 == 0:
                f.write(f"-- Progress: {count}/{len(complete_data)} properties\n")
        
        f.write("\n-- Verify reconstruction\n")
        f.write("SELECT \n")
        f.write("    COUNT(*) as total_properties,\n")
        f.write("    COUNT(CASE WHEN CHAR_LENGTH(primary_image) = 191 THEN 1 END) as still_truncated,\n")
        f.write("    COUNT(CASE WHEN CHAR_LENGTH(primary_image) > 191 THEN 1 END) as now_complete,\n")
        f.write("    AVG(CHAR_LENGTH(primary_image)) as avg_length,\n")
        f.write("    MAX(CHAR_LENGTH(primary_image)) as max_length\n")
        f.write("FROM properties_property \n")
        f.write("WHERE primary_image IS NOT NULL AND primary_image != '' AND primary_image != '[]';\n\n")
        
        f.write("-- Sample verification\n")
        f.write("SELECT property_id, CHAR_LENGTH(primary_image) as length, \n")
        f.write("       CASE WHEN primary_image LIKE '[%' AND primary_image LIKE '%]' THEN 'Valid JSON' ELSE 'Invalid JSON' END as json_status\n")
        f.write("FROM properties_property \n")
        f.write("WHERE CHAR_LENGTH(primary_image) > 191 \n")
        f.write("ORDER BY CHAR_LENGTH(primary_image) DESC \n")
        f.write("LIMIT 10;\n\n")
        
        f.write("-- Commit transaction (uncomment when ready)\n")
        f.write("-- COMMIT;\n\n")
        f.write("-- Rollback transaction (if needed)\n")
        f.write("-- ROLLBACK;\n")
    
    print(f"✅ SQL file generated: {output_sql_file}")
    print(f"📊 Generated {len(complete_data)} UPDATE statements")
    
    # Generate summary statistics
    print("\n📈 Summary Statistics:")
    total_chars = sum(len(data) for data in complete_data.values())
    avg_chars = total_chars / len(complete_data) if complete_data else 0
    max_chars = max(len(data) for data in complete_data.values()) if complete_data else 0
    
    print(f"   Total characters to restore: {total_chars:,}")
    print(f"   Average length per property: {avg_chars:.1f} chars")
    print(f"   Maximum length: {max_chars:,} chars")
    
    # Sample verification
    print("\n📝 Sample properties to be reconstructed:")
    sample_count = 0
    for property_id, complete_json in complete_data.items():
        if sample_count >= 5:
            break
        try:
            images = json.loads(complete_json)
            print(f"   🏠 {property_id}: {len(images)} images ({len(complete_json)} chars)")
        except json.JSONDecodeError:
            print(f"   ❌ {property_id}: Invalid JSON ({len(complete_json)} chars)")
        sample_count += 1
    
    print("\n🚀 Next steps:")
    print("1. Copy the SQL file to production server")
    print("2. Execute the SQL statements on production MariaDB")
    print("3. Verify the reconstruction results")
    print(f"\nSQL file location: {output_sql_file}")

if __name__ == '__main__':
    generate_reconstruction_sql()