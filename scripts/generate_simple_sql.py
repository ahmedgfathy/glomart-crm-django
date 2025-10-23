#!/usr/bin/env python3
"""
Generate simplified SQL file for production image data reconstruction (without transactions)
"""

import sqlite3
import json
import os

def generate_simple_reconstruction_sql():
    """Generate simple SQL file for production reconstruction"""
    
    local_sqlite_path = '/Users/ahmedgomaa/Downloads/crm/db.sqlite3'
    output_sql_file = '/Users/ahmedgomaa/Downloads/crm/production_simple_reconstruction.sql'
    
    # Connect to local SQLite
    sqlite_conn = sqlite3.connect(local_sqlite_path)
    cursor = sqlite_conn.cursor()
    
    # Extract complete image data
    cursor.execute('''
        SELECT property_id, primary_image 
        FROM properties_property 
        WHERE primary_image IS NOT NULL 
        AND primary_image != "" 
        AND primary_image != "[]"
        AND LENGTH(primary_image) > 191
        ORDER BY property_id
    ''')
    
    complete_data = {}
    for property_id, primary_image in cursor.fetchall():
        try:
            images = json.loads(primary_image)
            if isinstance(images, list) and images:
                complete_data[property_id] = primary_image
        except json.JSONDecodeError:
            continue
    
    sqlite_conn.close()
    
    # Generate simple SQL file
    with open(output_sql_file, 'w', encoding='utf-8') as f:
        f.write("-- Simple Production Image Data Reconstruction SQL\n")
        f.write("USE django_db_glomart_rs;\n")
        f.write("SET autocommit = 1;\n\n")
        
        for property_id, complete_json in complete_data.items():
            # Escape single quotes in JSON
            escaped_json = complete_json.replace("'", "''")
            f.write(f"UPDATE properties_property SET primary_image = '{escaped_json}' WHERE property_id = '{property_id}' AND CHAR_LENGTH(primary_image) = 191;\n")
    
    print(f"✅ Simple SQL file generated: {output_sql_file}")
    print(f"📊 Generated {len(complete_data)} UPDATE statements")
    
    return output_sql_file

if __name__ == '__main__':
    generate_simple_reconstruction_sql()