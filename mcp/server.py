#!/usr/bin/env python3

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the current directory to Python path to import our modules
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from services.filesystem import FileSystemService
from services.database import DatabaseService
from services.django_manager import DjangoService
from services.database_comparison import DatabaseComparisonService

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO if os.getenv('DEBUG', 'false').lower() == 'true' else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Important: Use stderr for MCP servers, not stdout
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Glomart CRM MCP Server")

    # Initialize services
    fs_service = FileSystemService()
    db_service = DatabaseService()
    django_service = DjangoService()
    db_comparison_service = DatabaseComparisonService()# File System Tools
@mcp.tool()
def read_file(path: str) -> str:
    """Read the contents of a file.
    
    Args:
        path: Path to the file to read
        
    Returns:
        The file contents as a string
    """
    try:
        return fs_service.read_file(path)
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        raise

@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write content to a file.
    
    Args:
        path: Path to the file to write
        content: Content to write to the file
        
    Returns:
        Success message
    """
    try:
        return fs_service.write_file(path, content)
    except Exception as e:
        logger.error(f"Error writing file {path}: {e}")
        raise

@mcp.tool()
def list_directory(path: str = ".") -> str:
    """List the contents of a directory.
    
    Args:
        path: Path to the directory to list (default: current directory)
        
    Returns:
        Directory listing as a formatted string
    """
    try:
        return fs_service.list_directory(path)
    except Exception as e:
        logger.error(f"Error listing directory {path}: {e}")
        raise

@mcp.tool()
def create_directory(path: str) -> str:
    """Create a new directory.
    
    Args:
        path: Path to the directory to create
        
    Returns:
        Success message
    """
    try:
        return fs_service.create_directory(path)
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        raise

@mcp.tool()
def delete_file(path: str) -> str:
    """Delete a file or directory.
    
    Args:
        path: Path to the file or directory to delete
        
    Returns:
        Success message
    """
    try:
        return fs_service.delete_file(path)
    except Exception as e:
        logger.error(f"Error deleting {path}: {e}")
        raise

@mcp.tool()
def search_files(pattern: str, directory: str = ".") -> str:
    """Search for files matching a pattern.
    
    Args:
        pattern: Glob pattern to search for
        directory: Directory to search in (default: current directory)
        
    Returns:
        List of matching files
    """
    try:
        return fs_service.search_files(pattern, directory)
    except Exception as e:
        logger.error(f"Error searching files with pattern {pattern}: {e}")
        raise

# Database Tools
@mcp.tool()
def db_query(query: str, params: list = None) -> str:
    """Execute a SQL query on the MariaDB database.
    
    Args:
        query: SQL query to execute
        params: Parameters for the query (optional)
        
    Returns:
        Query results as formatted text
    """
    try:
        return db_service.execute_query(query, params or [])
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise

@mcp.tool()
def db_get_tables() -> str:
    """Get a list of all tables in the database.
    
    Returns:
        List of database tables
    """
    try:
        return db_service.get_tables()
    except Exception as e:
        logger.error(f"Error getting tables: {e}")
        raise

@mcp.tool()
def db_get_schema(table: str) -> str:
    """Get schema information for a specific table.
    
    Args:
        table: Name of the table to get schema for
        
    Returns:
        Table schema information
    """
    try:
        return db_service.get_table_schema(table)
    except Exception as e:
        logger.error(f"Error getting schema for table {table}: {e}")
        raise

@mcp.tool()
def db_backup(path: str) -> str:
    """Create a backup of the database.
    
    Args:
        path: Path where to save the backup file
        
    Returns:
        Success message
    """
    try:
        return db_service.backup_database(path)
    except Exception as e:
        logger.error(f"Error backing up database: {e}")
        raise

# Django Management Tools
@mcp.tool()
def django_migrate() -> str:
    """Run Django database migrations.
    
    Returns:
        Migration output
    """
    try:
        return django_service.run_migrations()
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        raise

@mcp.tool()
def django_collectstatic() -> str:
    """Collect static files for Django.
    
    Returns:
        Collection output
    """
    try:
        return django_service.collect_static()
    except Exception as e:
        logger.error(f"Error collecting static files: {e}")
        raise

@mcp.tool()
def django_shell(command: str) -> str:
    """Execute a command in Django shell.
    
    Args:
        command: Python command to execute in Django shell
        
    Returns:
        Command output
    """
    try:
        return django_service.run_shell_command(command)
    except Exception as e:
        logger.error(f"Error running Django shell command: {e}")
        raise

@mcp.tool()
def django_test(app: str = None) -> str:
    """Run Django tests.
    
    Args:
        app: Specific app to test (optional)
        
    Returns:
        Test results
    """
    try:
        return django_service.run_tests(app)
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        raise

@mcp.tool()
def django_makemigrations(app: str = None) -> str:
    """Create new Django migrations.
    
    Args:
        app: Specific app to create migrations for (optional)
        
    Returns:
        Migration creation output
    """
    try:
        return django_service.make_migrations(app)
    except Exception as e:
        logger.error(f"Error making migrations: {e}")
        raise

# Database Comparison Tools
@mcp.tool()
def compare_database_structures() -> str:
    """Compare table structures between old SQLite and current MariaDB"""
    try:
        # Find and connect to SQLite database
        sqlite_conn = None
        sqlite_path = None
        for path in db_comparison_service.sqlite_paths:
            if path.exists():
                sqlite_path = str(path)
                sqlite_conn = db_comparison_service.connect_sqlite(sqlite_path)
                break
        
        if not sqlite_conn:
            return "Error: No SQLite database found in project directory"
        
        # Connect to MariaDB
        mariadb_conn = db_comparison_service.connect_mariadb()
        
        # Get table structures
        sqlite_tables = db_comparison_service.get_table_structure(sqlite_conn, 'sqlite')
        mariadb_tables = db_comparison_service.get_table_structure(mariadb_conn, 'mariadb')
        
        # Compare structures
        comparison = db_comparison_service.compare_table_structures(sqlite_tables, mariadb_tables)
        
        # Close connections
        sqlite_conn.close()
        mariadb_conn.close()
        
        result = f"Database Structure Comparison (SQLite: {sqlite_path})\n"
        result += "=" * 60 + "\n\n"
        
        if comparison['sqlite_only']:
            result += f"Tables only in SQLite ({len(comparison['sqlite_only'])}):\n"
            for table in comparison['sqlite_only']:
                result += f"  - {table}\n"
            result += "\n"
        
        if comparison['mariadb_only']:
            result += f"Tables only in MariaDB ({len(comparison['mariadb_only'])}):\n"
            for table in comparison['mariadb_only']:
                result += f"  - {table}\n"
            result += "\n"
        
        result += f"Common tables with differences ({len(comparison['common_tables'])}):\n"
        for table_name, diff in comparison['common_tables'].items():
            if diff['sqlite_only_columns'] or diff['mariadb_only_columns'] or diff['column_differences']:
                result += f"\n{table_name}:\n"
                
                if diff['sqlite_only_columns']:
                    result += f"  SQLite only columns: {', '.join(diff['sqlite_only_columns'])}\n"
                
                if diff['mariadb_only_columns']:
                    result += f"  MariaDB only columns: {', '.join(diff['mariadb_only_columns'])}\n"
                
                if diff['column_differences']:
                    result += "  Type differences:\n"
                    for col_diff in diff['column_differences']:
                        result += f"    {col_diff['column']}: SQLite({col_diff['sqlite_type']}) -> MariaDB({col_diff['mariadb_type']}"
                        if col_diff['mariadb_max_length']:
                            result += f", max_length={col_diff['mariadb_max_length']}"
                        result += ")\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error comparing database structures: {e}")
        return f"Error comparing database structures: {str(e)}"

@mcp.tool()
def analyze_properties_image_data() -> str:
    """Analyze properties table image data between SQLite and MariaDB"""
    try:
        # Find and connect to SQLite database
        sqlite_conn = None
        sqlite_path = None
        for path in db_comparison_service.sqlite_paths:
            if path.exists():
                sqlite_path = str(path)
                sqlite_conn = db_comparison_service.connect_sqlite(sqlite_path)
                break
        
        if not sqlite_conn:
            return "Error: No SQLite database found in project directory"
        
        # Connect to MariaDB
        mariadb_conn = db_comparison_service.connect_mariadb()
        
        # Analyze properties table
        analysis = db_comparison_service.analyze_properties_table(sqlite_conn, mariadb_conn)
        
        # Close connections
        sqlite_conn.close()
        mariadb_conn.close()
        
        result = f"Properties Table Image Data Analysis (SQLite: {sqlite_path})\n"
        result += "=" * 70 + "\n\n"
        
        if 'sqlite_error' in analysis:
            result += f"SQLite Error: {analysis['sqlite_error']}\n\n"
        else:
            sqlite_stats = analysis['sqlite']
            result += "SQLite Database:\n"
            result += f"  Total properties: {sqlite_stats['total_properties']}\n"
            if sqlite_stats['image_stats']:
                result += f"  Properties with images: {sqlite_stats['image_stats'][1]}\n"
                result += f"  Average image data length: {sqlite_stats['image_stats'][2]:.1f} chars\n"
                result += f"  Max image data length: {sqlite_stats['image_stats'][3]} chars\n"
                result += f"  Min image data length: {sqlite_stats['image_stats'][4]} chars\n"
            
            if sqlite_stats['samples']:
                result += "\n  Sample complete image data:\n"
                for sample in sqlite_stats['samples'][:3]:
                    result += f"    Property {sample[0]}: {sample[1]} chars\n"
                    if len(sample[2]) > 200:
                        result += f"      Data: {sample[2][:200]}...\n"
                    else:
                        result += f"      Data: {sample[2]}\n"
            result += "\n"
        
        if 'mariadb_error' in analysis:
            result += f"MariaDB Error: {analysis['mariadb_error']}\n\n"
        else:
            mariadb_stats = analysis['mariadb']
            result += "MariaDB Database:\n"
            result += f"  Total properties: {mariadb_stats['total_properties']}\n"
            if mariadb_stats['image_stats']:
                result += f"  Properties with images: {mariadb_stats['image_stats'][1]}\n"
                result += f"  Average image data length: {mariadb_stats['image_stats'][2]:.1f} chars\n"
                result += f"  Max image data length: {mariadb_stats['image_stats'][3]} chars\n"
                result += f"  Min image data length: {mariadb_stats['image_stats'][4]} chars\n"
            
            if mariadb_stats['samples']:
                result += "\n  Sample truncated image data:\n"
                for sample in mariadb_stats['samples'][:3]:
                    result += f"    Property {sample[0]}: {sample[1]} chars\n"
                    result += f"      Data: {sample[2]}\n"
            result += "\n"
        
        # Compare the stats
        if 'sqlite_error' not in analysis and 'mariadb_error' not in analysis:
            result += "Comparison:\n"
            sqlite_stats = analysis['sqlite']['image_stats']
            mariadb_stats = analysis['mariadb']['image_stats']
            
            if sqlite_stats and mariadb_stats:
                result += f"  Data loss ratio: {(sqlite_stats[3] - mariadb_stats[3]) / sqlite_stats[3] * 100:.1f}%\n"
                result += f"  Average length difference: {sqlite_stats[2] - mariadb_stats[2]:.1f} chars\n"
                
                if mariadb_stats[3] == 191:
                    result += "  ⚠️  MariaDB shows exactly 191 char limit - likely VARCHAR(191) truncation!\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing properties image data: {e}")
        return f"Error analyzing properties image data: {str(e)}"

@mcp.tool()
def extract_complete_image_data_from_sqlite() -> str:
    """Extract complete image data from SQLite for reconstruction"""
    try:
        # Find and connect to SQLite database
        sqlite_conn = None
        sqlite_path = None
        for path in db_comparison_service.sqlite_paths:
            if path.exists():
                sqlite_path = str(path)
                sqlite_conn = db_comparison_service.connect_sqlite(sqlite_path)
                break
        
        if not sqlite_conn:
            return "Error: No SQLite database found in project directory"
        
        # Extract complete image data
        complete_data = db_comparison_service.extract_complete_image_data(sqlite_conn)
        
        # Generate reconstruction SQL
        reconstruction_sql = db_comparison_service.generate_reconstruction_sql(complete_data)
        
        # Close connection
        sqlite_conn.close()
        
        result = f"Complete Image Data Extraction (SQLite: {sqlite_path})\n"
        result += "=" * 60 + "\n\n"
        result += f"Properties with complete image data: {len(complete_data)}\n\n"
        
        # Show sample data
        result += "Sample complete image data:\n"
        count = 0
        for prop_id, images in complete_data.items():
            if count >= 5:
                break
            result += f"\nProperty {prop_id} ({len(images)} images):\n"
            for i, img in enumerate(images[:2]):  # Show first 2 images
                result += f"  Image {i+1}: {img.get('filename', 'unknown')} ({img.get('size', 'unknown')} bytes)\n"
            if len(images) > 2:
                result += f"  ... and {len(images) - 2} more images\n"
            count += 1
        
        # Save reconstruction SQL to file
        sql_file = db_comparison_service.crm_path / "reconstruct_image_data.sql"
        with open(sql_file, 'w') as f:
            f.write("-- SQL to reconstruct complete image data from SQLite to MariaDB\n")
            f.write("-- Generated by MCP Database Comparison Service\n\n")
            f.write(reconstruction_sql)
        
        result += f"\n\nReconstructed SQL saved to: {sql_file}\n"
        result += f"Total SQL statements: {len(complete_data)}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error extracting complete image data: {e}")
        return f"Error extracting complete image data: {str(e)}"

@mcp.tool()
def compare_specific_properties(property_ids: str) -> str:
    """Compare specific properties between SQLite and MariaDB (comma-separated property IDs)"""
    try:
        # Parse property IDs
        prop_list = [pid.strip() for pid in property_ids.split(',') if pid.strip()]
        if not prop_list:
            return "Error: No valid property IDs provided"
        
        # Find and connect to SQLite database
        sqlite_conn = None
        sqlite_path = None
        for path in db_comparison_service.sqlite_paths:
            if path.exists():
                sqlite_path = str(path)
                sqlite_conn = db_comparison_service.connect_sqlite(sqlite_path)
                break
        
        if not sqlite_conn:
            return "Error: No SQLite database found in project directory"
        
        # Connect to MariaDB
        mariadb_conn = db_comparison_service.connect_mariadb()
        
        # Compare specific properties
        comparison = db_comparison_service.compare_specific_properties(sqlite_conn, mariadb_conn, prop_list)
        
        # Close connections
        sqlite_conn.close()
        mariadb_conn.close()
        
        result = f"Property Comparison (SQLite: {sqlite_path})\n"
        result += "=" * 50 + "\n\n"
        
        for prop_id, comp in comparison.items():
            result += f"Property ID: {prop_id}\n"
            result += "-" * 30 + "\n"
            
            if 'sqlite_error' in comp:
                result += f"SQLite Error: {comp['sqlite_error']}\n"
            elif comp['sqlite']:
                result += f"SQLite: {comp['sqlite']['primary_image_length']} chars\n"
                if comp['sqlite']['primary_image']:
                    data = comp['sqlite']['primary_image']
                    if len(data) > 300:
                        result += f"  Data: {data[:300]}...\n"
                    else:
                        result += f"  Data: {data}\n"
            else:
                result += "SQLite: Property not found\n"
            
            if 'mariadb_error' in comp:
                result += f"MariaDB Error: {comp['mariadb_error']}\n"
            elif comp['mariadb']:
                result += f"MariaDB: {comp['mariadb']['primary_image_length']} chars\n"
                if comp['mariadb']['primary_image']:
                    result += f"  Data: {comp['mariadb']['primary_image']}\n"
            else:
                result += "MariaDB: Property not found\n"
            
            # Show comparison
            if comp.get('sqlite') and comp.get('mariadb'):
                sqlite_len = comp['sqlite']['primary_image_length']
                mariadb_len = comp['mariadb']['primary_image_length']
                if sqlite_len != mariadb_len:
                    result += f"⚠️  Length difference: {sqlite_len - mariadb_len} chars lost\n"
                    if mariadb_len == 191:
                        result += "📏 MariaDB exactly 191 chars - VARCHAR(191) truncation confirmed!\n"
            
            result += "\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error comparing properties: {e}")
        return f"Error comparing properties: {str(e)}"

async def main():
    """Main function to run the MCP server."""
    try:
        logger.info("Starting Glomart CRM MCP Server...")
        await mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        await db_service.close()
        logger.info("Server shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())