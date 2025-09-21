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

# File System Tools
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