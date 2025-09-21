#!/usr/bin/env python3
"""
Fix Property Images in Production - Diagnostic and Fix Script
"""

import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from services.filesystem import FileSystemService

def diagnose_image_issue():
    """Diagnose property image serving issues"""
    fs = FileSystemService()
    
    print("🔍 === PROPERTY IMAGES DIAGNOSTIC ===")
    
    # Check current image structure
    print("\n📁 LOCAL IMAGE STRUCTURE:")
    try:
        public_props = fs.list_directory('/Users/ahmedgomaa/Downloads/crm/public/properties/images')
        print("✅ Public properties images found")
        print(f"   Sample: {public_props[:200]}...")
    except Exception as e:
        print(f"❌ Public properties images: {e}")
    
    # Check static directory
    print("\n📁 STATIC DIRECTORY:")
    try:
        static_dir = fs.list_directory('/Users/ahmedgomaa/Downloads/crm/static')
        print("✅ Static directory found")
        print(f"   Contents: {static_dir[:200]}...")
    except Exception as e:
        print(f"❌ Static directory: {e}")
    
    # Check Django settings
    print("\n⚙️ DJANGO SETTINGS ANALYSIS:")
    try:
        settings = fs.read_file('/Users/ahmedgomaa/Downloads/crm/real_estate_crm/settings.py')
        
        print("Current settings:")
        lines = settings.split('\n')
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in ['STATIC_URL', 'MEDIA_URL', 'STATIC_ROOT', 'MEDIA_ROOT']):
                print(f"   Line {i+1}: {line.strip()}")
                
    except Exception as e:
        print(f"❌ Settings analysis: {e}")
    
    print("\n🔧 === PRODUCTION FIXES NEEDED ===")
    print("1. ✅ Nginx/Apache static file serving configuration")
    print("2. ✅ Correct STATIC_ROOT and MEDIA_ROOT paths") 
    print("3. ✅ Property image URL generation in templates")
    print("4. ✅ Proper image path mapping")

def generate_nginx_config():
    """Generate nginx configuration for static files"""
    
    nginx_config = """
# Add this to your nginx server block for production

server {
    listen 80;
    server_name your-domain.com;

    # Static files
    location /static/ {
        alias /var/www/glomart-crm/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/glomart-crm/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Property images from public directory
    location /public/ {
        alias /var/www/glomart-crm/public/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Django application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""
    
    return nginx_config

def generate_production_settings():
    """Generate production settings additions"""
    
    settings_additions = """
# Add these to your production settings.py

import os

# Production static files
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/glomart-crm/staticfiles/'

# Production media files  
MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/glomart-crm/media/'

# Public files (for property images)
PUBLIC_URL = '/public/'
PUBLIC_ROOT = '/var/www/glomart-crm/public/'

# Allow serving static files in production (if not using nginx)
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
"""
    
    return settings_additions

if __name__ == "__main__":
    diagnose_image_issue()
    
    print("\n📝 === NGINX CONFIGURATION ===")
    nginx_config = generate_nginx_config()
    print(nginx_config)
    
    print("\n📝 === PRODUCTION SETTINGS ===")
    prod_settings = generate_production_settings()
    print(prod_settings)