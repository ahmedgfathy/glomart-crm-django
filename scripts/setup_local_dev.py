#!/usr/bin/env python3
"""
Local Development Database Setup Script
Creates a local MariaDB database with simple credentials for development
"""
import subprocess
import sys
import os

def run_mysql_command(command, password=""):
    """Run MySQL command safely"""
    try:
        if password:
            result = subprocess.run(
                ['mysql', '-u', 'root', f'-p{password}', '-e', command],
                capture_output=True, text=True, check=True
            )
        else:
            result = subprocess.run(
                ['mysql', '-u', 'root', '-e', command],
                capture_output=True, text=True, check=True
            )
        return result.stdout, True
    except subprocess.CalledProcessError as e:
        return e.stderr, False

def setup_local_database():
    """Setup local MariaDB for development"""
    
    print("🔧 Setting up local MariaDB for Glomart CRM development...")
    
    # Try connecting without password first
    print("Testing MariaDB connection without password...")
    output, success = run_mysql_command("SHOW DATABASES;")
    
    if success:
        print("✅ Connected to MariaDB without password")
        password = ""
    else:
        print("❌ Cannot connect without password")
        # Try common default passwords
        for pwd in ["", "root", "password"]:
            print(f"Trying password: '{pwd}'")
            output, success = run_mysql_command("SHOW DATABASES;", pwd)
            if success:
                print(f"✅ Connected with password: '{pwd}'")
                password = pwd
                break
        else:
            print("❌ Could not connect to MariaDB")
            print("Please ensure MariaDB is running and you know the root password")
            print("You can reset MariaDB root password with:")
            print("  sudo mysql_secure_installation")
            return False
    
    # Create local database and user
    db_commands = [
        "CREATE DATABASE IF NOT EXISTS glomart_crm_local CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
        "CREATE USER IF NOT EXISTS 'glomart_local'@'localhost' IDENTIFIED BY 'local123';",
        "GRANT ALL PRIVILEGES ON glomart_crm_local.* TO 'glomart_local'@'localhost';",
        "FLUSH PRIVILEGES;"
    ]
    
    print("\n🗄️ Creating local database and user...")
    for cmd in db_commands:
        output, success = run_mysql_command(cmd, password)
        if not success:
            print(f"❌ Failed to execute: {cmd}")
            print(f"Error: {output}")
            return False
    
    print("✅ Local database setup completed!")
    
    # Test the new connection
    print("\n🔍 Testing new database connection...")
    output, success = run_mysql_command("USE glomart_crm_local; SHOW TABLES;", "local123")
    if success:
        print("✅ Can connect to new database")
        return True
    else:
        print(f"❌ Cannot connect to new database: {output}")
        return False

def create_local_settings():
    """Create local settings file"""
    
    settings_content = '''"""
Local Django settings for Glomart CRM
This file overrides settings.py for local development
"""

from .settings import *

# Override database settings for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'glomart_crm_local',
        'USER': 'glomart_local',
        'PASSWORD': 'local123',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Local development settings
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Disable HTTPS redirect for local development
SECURE_SSL_REDIRECT = False

# Email backend for development (console output)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

print("🏠 Using LOCAL development settings")
print(f"🗄️ Database: {DATABASES['default']['NAME']}")
print(f"👤 User: {DATABASES['default']['USER']}")
'''
    
    with open('real_estate_crm/settings_local.py', 'w') as f:
        f.write(settings_content)
    
    print("✅ Created local settings file: real_estate_crm/settings_local.py")

def main():
    print("🏠 Glomart CRM Local Development Setup")
    print("=" * 50)
    
    # Setup database
    if not setup_local_database():
        sys.exit(1)
    
    # Create local settings
    create_local_settings()
    
    print("\n🎉 Local setup completed!")
    print("\n📋 Next steps:")
    print("1. Set environment variable: export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_local")
    print("2. Run migrations: python manage.py migrate")
    print("3. Create superuser: python manage.py createsuperuser")
    print("4. Start server: python manage.py runserver")
    print("\n🌐 Access your app at: http://localhost:8000")

if __name__ == "__main__":
    main()