#!/usr/bin/env python3
"""
Test script for Glomart CRM MCP Server tools
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from dotenv import load_dotenv
from services.filesystem import FileSystemService
from services.database import DatabaseService

# Load environment variables
load_dotenv()

def test_filesystem():
    """Test filesystem service"""
    print("=== Testing Filesystem Service ===")
    fs = FileSystemService()
    
    try:
        # Test list directory
        print("Listing CRM directory:")
        result = fs.list_directory("/Users/ahmedgomaa/Downloads/crm")
        print(result[:200] + "..." if len(result) > 200 else result)
        
        # Test read a file
        print("\nReading manage.py:")
        result = fs.read_file("/Users/ahmedgomaa/Downloads/crm/manage.py")
        print(result[:200] + "..." if len(result) > 200 else result)
        
        print("✅ Filesystem service working!")
        
    except Exception as e:
        print(f"❌ Filesystem service error: {e}")

def test_database():
    """Test database service"""
    print("\n=== Testing Database Service ===")
    db = DatabaseService()
    
    try:
        # Test basic connection
        print("Testing database connection...")
        tables = db.get_tables()
        print(f"Found {len(tables)} tables")
        
        # Test a simple query
        result = db.execute_query("SELECT 1 as test")
        print(f"Simple query result: {result}")
        
        print("✅ Database service working!")
        
    except Exception as e:
        print(f"❌ Database service error: {e}")
        print("Make sure MariaDB is running and credentials in .env are correct")

if __name__ == "__main__":
    test_filesystem()
    test_database()
    print("\n=== MCP Server Tools Test Complete ===")