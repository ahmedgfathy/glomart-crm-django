import os
import logging
import json
from typing import List, Dict, Any, Optional
import pymysql

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for handling MariaDB database operations."""
    
    def __init__(self):
        self.connection_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'glomart_crm'),
            'charset': 'utf8mb4',
            'autocommit': True
        }
        self.connection = None
        logger.info(f"DatabaseService initialized for database: {self.connection_config['database']}")
    
    def _get_connection(self):
        """Get a database connection, creating one if needed."""
        if self.connection is None or not self.connection.open:
            try:
                self.connection = pymysql.connect(**self.connection_config)
                logger.info("Database connection established")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise ConnectionError(f"Database connection failed: {str(e)}")
        return self.connection
    
    def execute_query(self, query: str, params: List[Any] = None) -> str:
        """Execute a SQL query and return formatted results."""
        if params is None:
            params = []
        
        try:
            connection = self._get_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # Log the query (without sensitive data)
                safe_query = query.replace('\n', ' ').strip()
                logger.info(f"Executing query: {safe_query[:100]}...")
                
                cursor.execute(query, params)
                
                # Check if it's a SELECT query
                if query.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    if not results:
                        return "Query executed successfully. No rows returned."
                    
                    # Format results as a readable table
                    return self._format_query_results(results, query)
                else:
                    # For INSERT, UPDATE, DELETE, etc.
                    affected_rows = cursor.rowcount
                    return f"Query executed successfully. Affected rows: {affected_rows}"
                    
        except Exception as e:
            logger.error(f"Database query error: {e}")
            raise RuntimeError(f"Database query failed: {str(e)}")
    
    def _format_query_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """Format query results in a readable format."""
        if not results:
            return "No results found."
        
        # Get column names
        columns = list(results[0].keys())
        
        # Create header
        output = f"Query Results ({len(results)} rows):\n"
        output += f"Query: {query.strip()}\n\n"
        
        # If there are many columns, use JSON format
        if len(columns) > 5:
            output += "Results (JSON format due to many columns):\n"
            for i, row in enumerate(results[:50]):  # Limit to 50 rows
                output += f"\nRow {i+1}:\n"
                output += json.dumps(row, indent=2, default=str)
            
            if len(results) > 50:
                output += f"\n... and {len(results) - 50} more rows"
        else:
            # Create table format for fewer columns
            # Calculate column widths
            col_widths = {}
            for col in columns:
                col_widths[col] = max(len(str(col)), 
                                    max(len(str(row.get(col, ''))) for row in results[:20]))
                # Limit column width to 50 characters
                col_widths[col] = min(col_widths[col], 50)
            
            # Header row
            header = " | ".join(str(col).ljust(col_widths[col]) for col in columns)
            separator = "-+-".join("-" * col_widths[col] for col in columns)
            
            output += header + "\n"
            output += separator + "\n"
            
            # Data rows (limit to 20 for readability)
            for row in results[:20]:
                row_data = []
                for col in columns:
                    value = str(row.get(col, ''))
                    if len(value) > col_widths[col]:
                        value = value[:col_widths[col]-3] + "..."
                    row_data.append(value.ljust(col_widths[col]))
                output += " | ".join(row_data) + "\n"
            
            if len(results) > 20:
                output += f"\n... and {len(results) - 20} more rows"
        
        return output
    
    def get_tables(self) -> str:
        """Get a list of all tables in the database."""
        try:
            query = "SHOW TABLES"
            connection = self._get_connection()
            with connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                
                if not results:
                    return "No tables found in the database."
                
                tables = [row[0] for row in results]
                output = f"Tables in database '{self.connection_config['database']}':\n\n"
                
                # Get table info
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                    count = cursor.fetchone()[0]
                    output += f"📋 {table} ({count} rows)\n"
                
                return output
                
        except Exception as e:
            logger.error(f"Error getting tables: {e}")
            raise RuntimeError(f"Failed to get tables: {str(e)}")
    
    def get_table_schema(self, table: str) -> str:
        """Get schema information for a specific table."""
        try:
            # Validate table name to prevent SQL injection
            if not table.replace('_', '').replace('-', '').isalnum():
                raise ValueError("Invalid table name")
            
            query = f"DESCRIBE `{table}`"
            connection = self._get_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                
                if not results:
                    return f"Table '{table}' not found or has no columns."
                
                output = f"Schema for table '{table}':\n\n"
                
                # Format schema information
                for col in results:
                    field = col['Field']
                    type_info = col['Type']
                    null_info = "NULL" if col['Null'] == 'YES' else "NOT NULL"
                    key_info = col['Key'] or ""
                    default = col['Default'] if col['Default'] is not None else ""
                    extra = col['Extra'] or ""
                    
                    output += f"📋 {field}\n"
                    output += f"   Type: {type_info}\n"
                    output += f"   Null: {null_info}\n"
                    if key_info:
                        output += f"   Key: {key_info}\n"
                    if default:
                        output += f"   Default: {default}\n"
                    if extra:
                        output += f"   Extra: {extra}\n"
                    output += "\n"
                
                return output
                
        except Exception as e:
            logger.error(f"Error getting schema for table {table}: {e}")
            raise RuntimeError(f"Failed to get schema for table '{table}': {str(e)}")
    
    def backup_database(self, backup_path: str) -> str:
        """Create a backup of the database using mysqldump."""
        try:
            import subprocess
            from pathlib import Path
            
            # Validate backup path
            backup_file = Path(backup_path).resolve()
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Build mysqldump command
            cmd = [
                'mysqldump',
                '-h', self.connection_config['host'],
                '-P', str(self.connection_config['port']),
                '-u', self.connection_config['user'],
                f"-p{self.connection_config['password']}",
                '--single-transaction',
                '--routines',
                '--triggers',
                self.connection_config['database']
            ]
            
            # Execute mysqldump
            with open(backup_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                size = backup_file.stat().st_size
                return f"Database backup created successfully at {backup_path} ({size} bytes)"
            else:
                error_msg = result.stderr.decode() if result.stderr else "Unknown error"
                raise RuntimeError(f"mysqldump failed: {error_msg}")
                
        except FileNotFoundError:
            raise RuntimeError("mysqldump command not found. Please install MySQL client tools.")
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            raise RuntimeError(f"Failed to create database backup: {str(e)}")
    
    async def close(self):
        """Close the database connection."""
        if self.connection and self.connection.open:
            self.connection.close()
            logger.info("Database connection closed")