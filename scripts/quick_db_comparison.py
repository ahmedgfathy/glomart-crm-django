#!/usr/bin/env python3
"""
Quick database comparison to analyze truncation issue
"""

import sqlite3
import pymysql
import json
import os
from pathlib import Path

def main():
    # Database configuration
    crm_path = Path('.')
    sqlite_paths = [crm_path / 'db.sqlite3', crm_path / 'local_db.sqlite3']
    mariadb_config = {
        'host': 'localhost',
        'user': 'root', 
        'password': 'zerocall',
        'database': 'django_db_glomart_rs',
        'port': 3306,
        'charset': 'utf8mb4'
    }

    # Find SQLite database
    sqlite_path = None
    for path in sqlite_paths:
        if path.exists():
            sqlite_path = str(path)
            break

    if not sqlite_path:
        print('❌ No SQLite database found')
        return

    print(f'✅ Found SQLite database: {sqlite_path}')

    try:
        # Connect to both databases
        sqlite_conn = sqlite3.connect(sqlite_path)
        mariadb_conn = pymysql.connect(**mariadb_config)

        print('\n=== PROPERTIES TABLE ANALYSIS ===')

        # SQLite analysis
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute('SELECT COUNT(*) FROM properties_property')
        sqlite_count = sqlite_cursor.fetchone()[0]

        sqlite_cursor.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN primary_image IS NOT NULL AND primary_image != "" AND primary_image != "[]" THEN 1 END) as with_images,
                AVG(LENGTH(primary_image)) as avg_length,
                MAX(LENGTH(primary_image)) as max_length,
                MIN(LENGTH(primary_image)) as min_length
            FROM properties_property
            WHERE primary_image IS NOT NULL AND primary_image != ""
        ''')
        sqlite_stats = sqlite_cursor.fetchone()

        print(f'📊 SQLite: {sqlite_count} total properties')
        if sqlite_stats and sqlite_stats[0] > 0:
            print(f'   📸 {sqlite_stats[1]} properties with images')
            print(f'   📏 Avg length: {sqlite_stats[2]:.1f} chars')
            print(f'   📏 Max length: {sqlite_stats[3]} chars')
            print(f'   📏 Min length: {sqlite_stats[4]} chars')

        # MariaDB analysis  
        mariadb_cursor = mariadb_conn.cursor()
        mariadb_cursor.execute('SELECT COUNT(*) FROM properties_property')
        mariadb_count = mariadb_cursor.fetchone()[0]

        mariadb_cursor.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN primary_image IS NOT NULL AND primary_image != "" AND primary_image != "[]" THEN 1 END) as with_images,
                AVG(CHAR_LENGTH(primary_image)) as avg_length,
                MAX(CHAR_LENGTH(primary_image)) as max_length,
                MIN(CHAR_LENGTH(primary_image)) as min_length
            FROM properties_property
            WHERE primary_image IS NOT NULL AND primary_image != ""
        ''')
        mariadb_stats = mariadb_cursor.fetchone()

        print(f'\n📊 MariaDB: {mariadb_count} total properties')
        if mariadb_stats and mariadb_stats[0] > 0:
            print(f'   📸 {mariadb_stats[1]} properties with images')
            print(f'   📏 Avg length: {mariadb_stats[2]:.1f} chars')
            print(f'   📏 Max length: {mariadb_stats[3]} chars')  
            print(f'   📏 Min length: {mariadb_stats[4]} chars')

        # Show truncation comparison
        if sqlite_stats and mariadb_stats and sqlite_stats[3] and mariadb_stats[3]:
            data_loss = (sqlite_stats[3] - mariadb_stats[3]) / sqlite_stats[3] * 100
            print(f'\n⚠️  TRUNCATION ANALYSIS:')
            print(f'   💔 Data loss: {data_loss:.1f}% ({sqlite_stats[3] - mariadb_stats[3]} chars lost)')
            print(f'   📉 SQLite max: {sqlite_stats[3]} → MariaDB max: {mariadb_stats[3]}')
            
            if mariadb_stats[3] == 191:
                print('   🔍 MariaDB exactly 191 chars - VARCHAR(191) truncation confirmed!')

        # Sample comparison
        print('\n=== SAMPLE PROPERTY COMPARISON ===')
        sqlite_cursor.execute('''
            SELECT property_id, LENGTH(primary_image), primary_image 
            FROM properties_property 
            WHERE primary_image IS NOT NULL AND primary_image != "" AND primary_image != "[]"
            ORDER BY LENGTH(primary_image) DESC 
            LIMIT 5
        ''')
        sqlite_samples = sqlite_cursor.fetchall()

        for i, sample in enumerate(sqlite_samples, 1):
            prop_id = sample[0]
            sqlite_len = sample[1]
            sqlite_data = sample[2]
            
            print(f'\n🏠 Property {prop_id} (Sample {i}):')
            print(f'   SQLite: {sqlite_len} chars')
            
            mariadb_cursor.execute('SELECT CHAR_LENGTH(primary_image), primary_image FROM properties_property WHERE property_id = %s', (prop_id,))
            mariadb_result = mariadb_cursor.fetchone()
            
            if mariadb_result:
                mariadb_len = mariadb_result[0]
                mariadb_data = mariadb_result[1]
                lost = sqlite_len - mariadb_len
                
                print(f'   MariaDB: {mariadb_len} chars')
                print(f'   💔 Lost: {lost} chars ({(lost/sqlite_len)*100:.1f}%)')
                
                if len(sqlite_data) > 300:
                    print(f'   📄 SQLite preview: {sqlite_data[:300]}...')
                else:
                    print(f'   📄 SQLite data: {sqlite_data}')
                print(f'   📄 MariaDB data: {mariadb_data}')
                
                # Check if it's valid JSON
                try:
                    sqlite_json = json.loads(sqlite_data)
                    mariadb_json = json.loads(mariadb_data) if mariadb_data else []
                    print(f'   🔢 SQLite images: {len(sqlite_json)} items')
                    print(f'   🔢 MariaDB images: {len(mariadb_json)} items')
                except json.JSONDecodeError:
                    print('   ❌ Invalid JSON detected')

        # Extract sample of complete data for reconstruction
        print('\n=== RECONSTRUCTION POTENTIAL ===')
        sqlite_cursor.execute('''
            SELECT property_id, primary_image 
            FROM properties_property 
            WHERE primary_image IS NOT NULL 
            AND primary_image != "" 
            AND primary_image != "[]"
            AND LENGTH(primary_image) > 191
            LIMIT 10
        ''')
        reconstruction_candidates = sqlite_cursor.fetchall()
        
        print(f'🔧 Found {len(reconstruction_candidates)} properties with complete data for reconstruction')
        
        if reconstruction_candidates:
            print('   Sample reconstruction candidates:')
            for prop_id, complete_data in reconstruction_candidates[:3]:
                try:
                    images = json.loads(complete_data)
                    print(f'   🏠 {prop_id}: {len(images)} images ({len(complete_data)} chars)')
                except:
                    print(f'   🏠 {prop_id}: Invalid JSON ({len(complete_data)} chars)')

        sqlite_conn.close()
        mariadb_conn.close()
        print('\n✅ Analysis complete!')

    except sqlite3.Error as e:
        print(f'❌ SQLite error: {e}')
    except pymysql.Error as e:
        print(f'❌ MariaDB error: {e}')
    except Exception as e:
        print(f'❌ General error: {e}')

if __name__ == '__main__':
    main()