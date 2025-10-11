#!/usr/bin/env python3
"""
MariaDB Connection Fix Script for Production
This script helps diagnose and fix database connection issues.
"""
import os

def create_mariadb_fix_commands():
    """Create commands to fix MariaDB connection issues"""
    
    commands = """
# ================================
# MariaDB Connection Fix Commands
# ================================

# 1. Check MariaDB service status
sudo systemctl status mariadb

# 2. Connect to MariaDB as root (test credentials)
mysql -u root -p

# Once connected, run these SQL commands:
# ================================
# Create dedicated Django user
CREATE USER IF NOT EXISTS 'django_user'@'localhost' IDENTIFIED BY 'Django2024!Secure';

# Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS django_db_glomart_rs CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Grant all privileges to Django user
GRANT ALL PRIVILEGES ON django_db_glomart_rs.* TO 'django_user'@'localhost';
FLUSH PRIVILEGES;

# Verify user exists
SELECT User, Host FROM mysql.user WHERE User = 'django_user';

# Show database
SHOW DATABASES LIKE 'django_db_glomart_rs';

# Exit MariaDB
EXIT;

# 3. Test new Django user connection
mysql -u django_user -p django_db_glomart_rs

# 4. If root password is wrong, reset it:
# sudo mysql_secure_installation
# OR
# sudo mysql
# ALTER USER 'root'@'localhost' IDENTIFIED BY 'your_new_password';
# FLUSH PRIVILEGES;
"""
    
    with open('mariadb_fix_commands.txt', 'w') as f:
        f.write(commands)
    
    print("✅ Created mariadb_fix_commands.txt with step-by-step instructions")

def create_django_settings_update():
    """Create updated Django settings for the new database user"""
    
    settings_update = '''
# Add this to your settings.py DATABASES configuration:

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_db_glomart_rs',
        'USER': 'django_user',  # Changed from 'root'
        'PASSWORD': 'Django2024!Secure',  # New secure password
        'HOST': 'localhost',
        'PORT': '',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
'''
    
    with open('new_database_settings.py', 'w') as f:
        f.write(settings_update)
    
    print("✅ Created new_database_settings.py with updated configuration")

def create_test_connection_script():
    """Create a script to test database connection"""
    
    test_script = '''#!/usr/bin/env python3
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
    print("\\n🔍 Running Django system checks...")
    execute_from_command_line(['manage.py', 'check'])
    
    print("\\n✅ All tests passed! Database is working correctly.")
    
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print(f"Error type: {type(e).__name__}")
    
    # Provide troubleshooting suggestions
    print("\\n🔧 Troubleshooting suggestions:")
    print("1. Verify MariaDB is running: sudo systemctl status mariadb")
    print("2. Check database credentials in settings.py")
    print("3. Ensure database 'django_db_glomart_rs' exists")
    print("4. Verify user 'django_user' has proper permissions")
'''
    
    with open('test_db_connection.py', 'w') as f:
        f.write(test_script)
    
    os.chmod('test_db_connection.py', 0o755)
    print("✅ Created test_db_connection.py script")

if __name__ == "__main__":
    print("🔧 MariaDB Connection Fix Generator")
    print("=" * 40)
    
    create_mariadb_fix_commands()
    create_django_settings_update()
    create_test_connection_script()
    
    print("\n📋 Next steps:")
    print("1. Review mariadb_fix_commands.txt and run the MariaDB commands")
    print("2. Update your settings.py with content from new_database_settings.py") 
    print("3. Run python test_db_connection.py to verify the connection")
    print("4. Restart your Django service: sudo systemctl restart glomart-crm")