#!/usr/bin/env python3
"""
Test Django database connection on production server
Run this on your production server: /var/www/glomart-crm/
"""
import os
import sys
import django
from pathlib import Path

def test_django_db():
    # Set up Django environment
    project_root = Path('/var/www/glomart-crm')
    if not project_root.exists():
        project_root = Path('.')  # Local development
    
    sys.path.insert(0, str(project_root))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
    
    try:
        print("🔧 Setting up Django...")
        django.setup()
        
        from django.db import connection
        
        print("🔗 Testing database connection...")
        
        # Test basic connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"✅ Basic connection test: {result}")
        
        # Test Django models
        from django.contrib.auth.models import User
        user_count = User.objects.count()
        print(f"✅ User model test: {user_count} users found")
        
        # Test database info
        db_info = connection.get_connection_params()
        print(f"✅ Database: {db_info.get('db', 'N/A')}")
        print(f"✅ User: {db_info.get('user', 'N/A')}")
        print(f"✅ Host: {db_info.get('host', 'N/A')}")
        
        print("\n🎉 All database tests passed!")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        
        print("\n🔧 Debug information:")
        print("1. Check MariaDB is running: sudo systemctl status mariadb")
        print("2. Verify database exists: mysql -u root -p -e 'SHOW DATABASES;'")
        print("3. Check user permissions: mysql -u root -p -e 'SHOW GRANTS FOR \'root\'@\'localhost\';'")
        
        sys.exit(1)

if __name__ == "__main__":
    test_django_db()
