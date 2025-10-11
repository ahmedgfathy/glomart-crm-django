#!/usr/bin/env python3
"""
Database schema explorer for Django CRM
"""

import sys
from pathlib import Path

# Add the current directory to Python path  
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from dotenv import load_dotenv
from services.database import DatabaseService

load_dotenv()

def explore_schema():
    """Explore Django CRM database schema"""
    db = DatabaseService()
    
    print("=== Django CRM Database Schema ===")
    
    # Check leads table structure
    try:
        print("\n--- LEADS TABLE STRUCTURE ---")
        result = db.get_table_schema("leads_lead")
        print(result)
        
        print("\n--- PROPERTIES TABLE STRUCTURE ---") 
        result = db.get_table_schema("properties_property")
        print(result)
        
        print("\n--- PROJECTS TABLE STRUCTURE ---")
        result = db.get_table_schema("projects_project")
        print(result)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    explore_schema()