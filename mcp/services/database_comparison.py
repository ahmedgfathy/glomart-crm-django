#!/usr/bin/env python3
"""
Database Comparison Service for MCP Server
Compares old SQLite database with current MariaDB to understand data truncation
"""

import sqlite3
import pymysql
import json
import os
from typing import Dict, List, Tuple, Any
from pathlib import Path

class DatabaseComparisonService:
    def __init__(self):
        self.crm_path = Path(__file__).parent.parent
        self.sqlite_paths = [
            self.crm_path / "db.sqlite3",
            self.crm_path / "local_db.sqlite3"
        ]
        self.mariadb_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'zerocall',
            'database': 'django_db_glomart_rs',
            'port': 3306,
            'charset': 'utf8mb4'
        }
    
    def connect_sqlite(self, db_path: str) -> sqlite3.Connection:
        """Connect to SQLite database"""
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"SQLite database not found: {db_path}")
        return sqlite3.connect(db_path)
    
    def connect_mariadb(self) -> pymysql.Connection:
        """Connect to MariaDB database"""
        return pymysql.connect(**self.mariadb_config)
    
    def get_table_structure(self, connection, db_type: str) -> Dict[str, List[Dict]]:
        """Get table structure for comparison"""
        tables = {}
        
        if db_type == 'sqlite':
            cursor = connection.cursor()
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            table_names = [row[0] for row in cursor.fetchall()]
            
            for table_name in table_names:
                # Get column info
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        'name': row[1],
                        'type': row[2],
                        'nullable': not row[3],
                        'default': row[4],
                        'primary_key': bool(row[5])
                    })
                tables[table_name] = columns
        
        elif db_type == 'mariadb':
            cursor = connection.cursor()
            # Get all tables
            cursor.execute("SHOW TABLES")
            table_names = [row[0] for row in cursor.fetchall()]
            
            for table_name in table_names:
                # Get column info
                cursor.execute(f"""
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        IS_NULLABLE,
                        COLUMN_DEFAULT,
                        COLUMN_KEY,
                        CHARACTER_MAXIMUM_LENGTH
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = '{self.mariadb_config['database']}' 
                    AND TABLE_NAME = '{table_name}'
                    ORDER BY ORDINAL_POSITION
                """)
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        'name': row[0],
                        'type': row[1],
                        'nullable': row[2] == 'YES',
                        'default': row[3],
                        'primary_key': row[4] == 'PRI',
                        'max_length': row[5]
                    })
                tables[table_name] = columns
        
        return tables
    
    def compare_table_structures(self, sqlite_tables: Dict, mariadb_tables: Dict) -> Dict:
        """Compare table structures between SQLite and MariaDB"""
        comparison = {
            'sqlite_only': [],
            'mariadb_only': [],
            'common_tables': {},
            'differences': []
        }
        
        sqlite_names = set(sqlite_tables.keys())
        mariadb_names = set(mariadb_tables.keys())
        
        comparison['sqlite_only'] = list(sqlite_names - mariadb_names)
        comparison['mariadb_only'] = list(mariadb_names - sqlite_names)
        
        # Compare common tables
        common_tables = sqlite_names & mariadb_names
        for table_name in common_tables:
            sqlite_cols = {col['name']: col for col in sqlite_tables[table_name]}
            mariadb_cols = {col['name']: col for col in mariadb_tables[table_name]}
            
            table_diff = {
                'sqlite_only_columns': list(set(sqlite_cols.keys()) - set(mariadb_cols.keys())),
                'mariadb_only_columns': list(set(mariadb_cols.keys()) - set(sqlite_cols.keys())),
                'column_differences': []
            }
            
            # Compare common columns
            common_cols = set(sqlite_cols.keys()) & set(mariadb_cols.keys())
            for col_name in common_cols:
                sqlite_col = sqlite_cols[col_name]
                mariadb_col = mariadb_cols[col_name]
                
                if sqlite_col['type'] != mariadb_col['type']:
                    table_diff['column_differences'].append({
                        'column': col_name,
                        'sqlite_type': sqlite_col['type'],
                        'mariadb_type': mariadb_col['type'],
                        'mariadb_max_length': mariadb_col.get('max_length')
                    })
            
            comparison['common_tables'][table_name] = table_diff
        
        return comparison
    
    def analyze_properties_table(self, sqlite_conn, mariadb_conn) -> Dict:
        """Detailed analysis of properties_property table"""
        analysis = {}
        
        # Check if both databases have the properties_property table
        sqlite_cursor = sqlite_conn.cursor()
        mariadb_cursor = mariadb_conn.cursor()
        
        # SQLite analysis
        try:
            sqlite_cursor.execute("SELECT COUNT(*) FROM properties_property")
            sqlite_count = sqlite_cursor.fetchone()[0]
            
            # Check primary_image field
            sqlite_cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN primary_image IS NOT NULL AND primary_image != '' AND primary_image != '[]' THEN 1 END) as with_images,
                    AVG(LENGTH(primary_image)) as avg_length,
                    MAX(LENGTH(primary_image)) as max_length,
                    MIN(LENGTH(primary_image)) as min_length
                FROM properties_property
            """)
            sqlite_image_stats = sqlite_cursor.fetchone()
            
            # Sample of complete image data
            sqlite_cursor.execute("""
                SELECT property_id, LENGTH(primary_image) as img_length, primary_image 
                FROM properties_property 
                WHERE primary_image IS NOT NULL AND primary_image != '' AND primary_image != '[]'
                ORDER BY LENGTH(primary_image) DESC 
                LIMIT 5
            """)
            sqlite_samples = sqlite_cursor.fetchall()
            
        except sqlite3.OperationalError as e:
            sqlite_count = 0
            sqlite_image_stats = None
            sqlite_samples = []
            analysis['sqlite_error'] = str(e)
        
        # MariaDB analysis
        try:
            mariadb_cursor.execute("SELECT COUNT(*) FROM properties_property")
            mariadb_count = mariadb_cursor.fetchone()[0]
            
            mariadb_cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN primary_image IS NOT NULL AND primary_image != '' AND primary_image != '[]' THEN 1 END) as with_images,
                    AVG(CHAR_LENGTH(primary_image)) as avg_length,
                    MAX(CHAR_LENGTH(primary_image)) as max_length,
                    MIN(CHAR_LENGTH(primary_image)) as min_length
                FROM properties_property
            """)
            mariadb_image_stats = mariadb_cursor.fetchone()
            
            # Sample of truncated data
            mariadb_cursor.execute("""
                SELECT property_id, CHAR_LENGTH(primary_image) as img_length, primary_image 
                FROM properties_property 
                WHERE primary_image IS NOT NULL AND primary_image != '' AND primary_image != '[]'
                ORDER BY CHAR_LENGTH(primary_image) DESC 
                LIMIT 5
            """)
            mariadb_samples = mariadb_cursor.fetchall()
            
        except pymysql.Error as e:
            mariadb_count = 0
            mariadb_image_stats = None
            mariadb_samples = []
            analysis['mariadb_error'] = str(e)
        
        analysis.update({
            'sqlite': {
                'total_properties': sqlite_count,
                'image_stats': sqlite_image_stats,
                'samples': sqlite_samples
            },
            'mariadb': {
                'total_properties': mariadb_count,
                'image_stats': mariadb_image_stats,
                'samples': mariadb_samples
            }
        })
        
        return analysis
    
    def compare_specific_properties(self, sqlite_conn, mariadb_conn, property_ids: List[str]) -> Dict:
        """Compare specific properties between databases"""
        comparison = {}
        
        sqlite_cursor = sqlite_conn.cursor()
        mariadb_cursor = mariadb_conn.cursor()
        
        for prop_id in property_ids:
            prop_comparison = {}
            
            # SQLite data
            try:
                sqlite_cursor.execute(
                    "SELECT property_id, primary_image, images, property_images FROM properties_property WHERE property_id = ?",
                    (prop_id,)
                )
                sqlite_data = sqlite_cursor.fetchone()
                if sqlite_data:
                    prop_comparison['sqlite'] = {
                        'property_id': sqlite_data[0],
                        'primary_image': sqlite_data[1],
                        'primary_image_length': len(sqlite_data[1]) if sqlite_data[1] else 0,
                        'images': sqlite_data[2] if len(sqlite_data) > 2 else None,
                        'property_images': sqlite_data[3] if len(sqlite_data) > 3 else None
                    }
                else:
                    prop_comparison['sqlite'] = None
            except Exception as e:
                prop_comparison['sqlite_error'] = str(e)
            
            # MariaDB data
            try:
                mariadb_cursor.execute(
                    "SELECT property_id, primary_image, images, property_images FROM properties_property WHERE property_id = %s",
                    (prop_id,)
                )
                mariadb_data = mariadb_cursor.fetchone()
                if mariadb_data:
                    prop_comparison['mariadb'] = {
                        'property_id': mariadb_data[0],
                        'primary_image': mariadb_data[1],
                        'primary_image_length': len(mariadb_data[1]) if mariadb_data[1] else 0,
                        'images': mariadb_data[2] if len(mariadb_data) > 2 else None,
                        'property_images': mariadb_data[3] if len(mariadb_data) > 3 else None
                    }
                else:
                    prop_comparison['mariadb'] = None
            except Exception as e:
                prop_comparison['mariadb_error'] = str(e)
            
            comparison[prop_id] = prop_comparison
        
        return comparison
    
    def extract_complete_image_data(self, sqlite_conn) -> Dict[str, List[Dict]]:
        """Extract complete image data from SQLite for reconstruction"""
        image_data = {}
        
        cursor = sqlite_conn.cursor()
        try:
            cursor.execute("""
                SELECT property_id, primary_image, images, property_images
                FROM properties_property 
                WHERE primary_image IS NOT NULL AND primary_image != '' AND primary_image != '[]'
            """)
            
            for row in cursor.fetchall():
                property_id, primary_image, images, property_images = row
                
                all_images = []
                
                # Parse primary_image
                if primary_image:
                    try:
                        primary_images_list = json.loads(primary_image)
                        if isinstance(primary_images_list, list):
                            all_images.extend(primary_images_list)
                    except json.JSONDecodeError:
                        pass
                
                # Parse images field
                if images:
                    try:
                        images_list = json.loads(images)
                        if isinstance(images_list, list):
                            all_images.extend(images_list)
                    except json.JSONDecodeError:
                        pass
                
                # Parse property_images field
                if property_images:
                    try:
                        prop_images_list = json.loads(property_images)
                        if isinstance(prop_images_list, list):
                            all_images.extend(prop_images_list)
                    except json.JSONDecodeError:
                        pass
                
                if all_images:
                    image_data[property_id] = all_images
        
        except Exception as e:
            print(f"Error extracting image data: {e}")
        
        return image_data
    
    def generate_reconstruction_sql(self, complete_image_data: Dict[str, List[Dict]]) -> str:
        """Generate SQL statements to reconstruct the complete image data in MariaDB"""
        sql_statements = []
        
        for property_id, images in complete_image_data.items():
            complete_json = json.dumps(images)
            sql_statements.append(
                f"UPDATE properties_property SET primary_image = '{complete_json.replace("'", "''")}' WHERE property_id = '{property_id}';"
            )
        
        return '\n'.join(sql_statements)