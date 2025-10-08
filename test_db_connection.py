#!/usr/bin/env python3
import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')

try:
    django.setup()
    
    from django.db import connection
    from django.core.management import execute_from_command_line
    
    print("Testing database connection...")
    
    # Test connection
    cursor = connection.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    
    print("✅ Database connection successful!")
    print(f"✅ Test query result: {result}")
    
    # Test Django models
    from authentication.models import User
    user_count = User.objects.count()
    print(f"✅ Can query User model: {user_count} users found")
    
    # Run Django check
    print("\n🔍 Running Django system checks...")
    execute_from_command_line(['manage.py', 'check'])
    
    print("\n✅ All tests passed! Database is working correctly.")
    
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print(f"Error type: {type(e).__name__}")
    
    # Provide troubleshooting suggestions
    print("\n🔧 Troubleshooting suggestions:")
    print("1. Verify MariaDB is running: sudo systemctl status mariadb")
    print("2. Check database credentials in settings.py")
    print("3. Ensure database 'django_db_glomart_rs' exists")
    print("4. Verify user 'django_user' has proper permissions")
