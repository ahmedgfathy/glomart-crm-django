#!/usr/bin/env python3
"""
Advanced test script for Glomart CRM MCP Server
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from dotenv import load_dotenv
from services.database import DatabaseService

# Load environment variables
load_dotenv()

def test_django_tables():
    """Test Django CRM database tables"""
    print("=== Testing Django CRM Database ===")
    db = DatabaseService()
    
    try:
        # Get Django tables
        print("Getting Django tables...")
        tables = db.get_tables()
        django_tables = [t for t in tables if any(app in t for app in ['auth_', 'leads_', 'properties_', 'projects_', 'authentication_'])]
        
        print(f"Found {len(django_tables)} Django tables:")
        for table in django_tables[:10]:  # Show first 10
            print(f"  • {table}")
        
        if len(django_tables) > 10:
            print(f"  ... and {len(django_tables) - 10} more")
        
        # Test specific CRM queries
        print("\n=== Testing CRM Data Queries ===")
        
        # Test leads
        if 'leads_lead' in tables:
            result = db.execute_query("SELECT COUNT(*) as lead_count FROM leads_lead LIMIT 1")
            print(f"Total leads: {result}")
        
        # Test properties  
        if 'properties_property' in tables:
            result = db.execute_query("SELECT COUNT(*) as property_count FROM properties_property LIMIT 1")
            print(f"Total properties: {result}")
        
        # Test projects
        if 'projects_project' in tables:
            result = db.execute_query("SELECT COUNT(*) as project_count FROM projects_project LIMIT 1")
            print(f"Total projects: {result}")
            
        # Show some sample data
        print("\n=== Sample Data ===")
        if 'leads_lead' in tables:
            result = db.execute_query("SELECT id, name, email, phone FROM leads_lead LIMIT 3")
            print(f"Sample leads:\n{result}")
        
        print("✅ Django CRM database access working!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_django_tables()