#!/usr/bin/env python3
"""
Update Django settings for local development with production data
"""

import os
import re

def update_settings():
    settings_file = 'real_estate_crm/settings.py'
    
    if not os.path.exists(settings_file):
        print("❌ Settings file not found:", settings_file)
        return
    
    with open(settings_file, 'r') as f:
        content = f.read()
    
    # Database configuration for local development
    new_db_config = '''DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_db_glomart_rs',
        'HOST': 'localhost',
        'USER': 'root',
        'PASSWORD': 'zerocall',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    },
    # MariaDB connection for owner databases
    'mariadb_owner': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'localhost',
        'USER': 'root',
        'PASSWORD': 'zerocall',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}'''
    
    # Replace the DATABASES configuration
    pattern = r'DATABASES\s*=\s*\{[^}]*\}[^}]*\}'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_db_config, content, flags=re.DOTALL)
        
        with open(settings_file, 'w') as f:
            f.write(content)
        
        print("✅ Django settings updated for local development")
        print("✅ Database configured to use local MariaDB with production data")
    else:
        print("❌ Could not find DATABASES configuration in settings.py")
        print("💡 Please update manually with the provided configuration")

if __name__ == '__main__':
    update_settings()
