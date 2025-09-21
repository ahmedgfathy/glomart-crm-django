#!/usr/bin/env python3
"""
Compare Local vs Production Environment
Identify differences between local (working) and production (not working) environments
"""

import paramiko
import pymysql
import os
import json
from datetime import datetime

# Configuration
LOCAL_CONFIG = {
    'django_path': '/Users/ahmedgomaa/Downloads/crm',
    'database': {
        'host': 'localhost',
        'user': 'root',
        'password': 'ZeroCall20!@HH##1655&&',
        'database': 'django_db_glomart_rs',
        'port': 3306
    }
}

PRODUCTION_CONFIG = {
    'host': '5.180.148.92',
    'username': 'root',
    'password': 'ZeroCall20!@HH##1655&&',
    'django_path': '/var/www/glomart-crm',
    'database': {
        'host': '5.180.148.92',
        'user': 'root',
        'password': 'ZeroCall20!@HH##1655&&',
        'database': 'django_db_glomart_rs',
        'port': 3306
    }
}

def connect_to_production():
    """Connect to production server"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=PRODUCTION_CONFIG['host'],
            username=PRODUCTION_CONFIG['username'],
            password=PRODUCTION_CONFIG['password'],
            timeout=10
        )
        print("✅ Connected to production server")
        return ssh
    except Exception as e:
        print(f"❌ Production SSH connection failed: {e}")
        return None

def compare_file_content(local_path, remote_path, ssh, description):
    """Compare a specific file between local and remote"""
    print(f"\n📋 Comparing {description}")
    print("=" * 60)
    
    # Read local file
    try:
        with open(local_path, 'r') as f:
            local_content = f.read()
        print(f"✅ Read local file: {local_path}")
    except Exception as e:
        print(f"❌ Failed to read local file: {e}")
        return
    
    # Read remote file
    try:
        stdin, stdout, stderr = ssh.exec_command(f"cat {remote_path}")
        remote_content = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        if error:
            print(f"❌ Failed to read remote file: {error}")
            return
        print(f"✅ Read remote file: {remote_path}")
    except Exception as e:
        print(f"❌ Failed to read remote file: {e}")
        return
    
    # Compare content
    if local_content == remote_content:
        print("✅ Files are identical")
    else:
        print("⚠️  Files are different!")
        
        # Check specific sections for models.py
        if 'models.py' in description:
            # Look for get_all_image_urls method
            local_method = extract_method(local_content, 'get_all_image_urls')
            remote_method = extract_method(remote_content, 'get_all_image_urls')
            
            if local_method != remote_method:
                print("🔍 get_all_image_urls method differences:")
                print(f"Local method length: {len(local_method) if local_method else 0} chars")
                print(f"Remote method length: {len(remote_method) if remote_method else 0} chars")
                
                if local_method and remote_method:
                    # Show first few lines of each
                    local_lines = local_method.split('\\n')[:5]
                    remote_lines = remote_method.split('\\n')[:5]
                    print("\\nLocal method (first 5 lines):")
                    for line in local_lines:
                        print(f"  {line}")
                    print("\\nRemote method (first 5 lines):")
                    for line in remote_lines:
                        print(f"  {line}")

def extract_method(content, method_name):
    """Extract a specific method from Python file content"""
    import re
    pattern = f'def {method_name}.*?(?=\\n    def |\\n    @property|\\nclass |\\Z)'
    match = re.search(pattern, content, re.DOTALL)
    return match.group(0) if match else None

def compare_database_samples():
    """Compare database content between local and production"""
    print(f"\\n📊 Comparing Database Content")
    print("=" * 60)
    
    # Connect to local database
    try:
        local_db = pymysql.connect(
            host=LOCAL_CONFIG['database']['host'],
            user=LOCAL_CONFIG['database']['user'],
            password=LOCAL_CONFIG['database']['password'],
            database=LOCAL_CONFIG['database']['database'],
            port=LOCAL_CONFIG['database']['port'],
            charset='utf8mb4'
        )
        print("✅ Connected to local database")
    except Exception as e:
        print(f"❌ Local database connection failed: {e}")
        return
    
    # Connect to production database
    try:
        prod_db = pymysql.connect(
            host=PRODUCTION_CONFIG['database']['host'],
            user=PRODUCTION_CONFIG['database']['user'],
            password=PRODUCTION_CONFIG['database']['password'],
            database=PRODUCTION_CONFIG['database']['database'],
            port=PRODUCTION_CONFIG['database']['port'],
            charset='utf8mb4'
        )
        print("✅ Connected to production database")
    except Exception as e:
        print(f"❌ Production database connection failed: {e}")
        local_db.close()
        return
    
    try:
        # Compare property counts
        with local_db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM properties_property")
            local_count = cursor.fetchone()[0]
        
        with prod_db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM properties_property")
            prod_count = cursor.fetchone()[0]
        
        print(f"📈 Property counts:")
        print(f"  Local: {local_count} properties")
        print(f"  Production: {prod_count} properties")
        
        # Compare sample property data
        sample_property_id = '679787d70031d79039eb'  # The one we tested locally
        
        print(f"\\n🔍 Comparing sample property: {sample_property_id}")
        
        # Local property data
        with local_db.cursor() as cursor:
            cursor.execute("SELECT property_id, title, primary_image FROM properties_property WHERE property_id = %s", (sample_property_id,))
            local_property = cursor.fetchone()
        
        # Production property data  
        with prod_db.cursor() as cursor:
            cursor.execute("SELECT property_id, title, primary_image FROM properties_property WHERE property_id = %s", (sample_property_id,))
            prod_property = cursor.fetchone()
        
        if local_property and prod_property:
            print("✅ Property exists in both databases")
            print(f"  Local title: {local_property[1][:50]}...")
            print(f"  Production title: {prod_property[1][:50]}...")
            
            # Compare primary_image data
            local_image_data = local_property[2]
            prod_image_data = prod_property[2]
            
            print(f"\\n📸 Image data comparison:")
            print(f"  Local image data length: {len(local_image_data) if local_image_data else 0} chars")
            print(f"  Production image data length: {len(prod_image_data) if prod_image_data else 0} chars")
            
            if local_image_data == prod_image_data:
                print("✅ Image data is identical")
            else:
                print("⚠️  Image data is different!")
                
                # Show first 200 chars of each
                print(f"\\nLocal image data (first 200 chars):")
                print(f"  {local_image_data[:200] if local_image_data else 'None'}...")
                print(f"\\nProduction image data (first 200 chars):")
                print(f"  {prod_image_data[:200] if prod_image_data else 'None'}...")
        else:
            print(f"❌ Property {sample_property_id} not found in one or both databases")
            print(f"  Local: {'Found' if local_property else 'Not found'}")
            print(f"  Production: {'Found' if prod_property else 'Not found'}")
        
    finally:
        local_db.close()
        prod_db.close()

def compare_static_and_media_structure(ssh):
    """Compare static and media file structure"""
    print(f"\\n📁 Comparing File Structure")
    print("=" * 60)
    
    # Local structure
    print("📂 Local media structure:")
    local_media_path = f"{LOCAL_CONFIG['django_path']}/public"
    if os.path.exists(local_media_path):
        for root, dirs, files in os.walk(local_media_path):
            level = root.replace(local_media_path, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            sub_indent = ' ' * 2 * (level + 1)
            for file in files[:5]:  # Limit to first 5 files per directory
                print(f"{sub_indent}{file}")
            if len(files) > 5:
                print(f"{sub_indent}... and {len(files) - 5} more files")
    else:
        print("❌ Local media directory not found")
    
    # Production structure
    print("\\n📂 Production media structure:")
    stdin, stdout, stderr = ssh.exec_command(f"find {PRODUCTION_CONFIG['django_path']}/public -type f | head -20")
    prod_files = stdout.read().decode('utf-8').strip()
    if prod_files:
        print("Sample files in production:")
        for file in prod_files.split('\\n'):
            print(f"  {file}")
    else:
        print("❌ No files found in production media directory")
    
    # Check nginx configuration
    print("\\n🔧 Production nginx configuration:")
    stdin, stdout, stderr = ssh.exec_command("grep -r 'public' /etc/nginx/sites-*/")
    nginx_config = stdout.read().decode('utf-8').strip()
    if nginx_config:
        print("Nginx static file configuration:")
        for line in nginx_config.split('\\n')[:10]:
            print(f"  {line}")
    else:
        print("⚠️  No nginx static file configuration found")

def test_production_urls(ssh):
    """Test various URLs on production"""
    print(f"\\n🌐 Testing Production URLs")
    print("=" * 60)
    
    test_urls = [
        "/static/images/property-placeholder.svg",
        "/public/properties/images/6797878e003c429d4583.jpg",
        "/properties/679787d70031d79039eb/images/"
    ]
    
    for url in test_urls:
        print(f"\\n🔗 Testing: {url}")
        # Test with curl
        stdin, stdout, stderr = ssh.exec_command(f"curl -I -s http://localhost{url}")
        response = stdout.read().decode('utf-8')
        if response:
            status_line = response.split('\\n')[0]
            print(f"  Response: {status_line}")
        else:
            print("  No response")

def main():
    """Main comparison function"""
    print("🔍 Local vs Production Environment Comparison")
    print("=" * 80)
    print(f"Local Django: {LOCAL_CONFIG['django_path']}")
    print(f"Production Django: {PRODUCTION_CONFIG['django_path']}")
    print(f"Production Server: {PRODUCTION_CONFIG['host']}")
    
    # Connect to production
    ssh = connect_to_production()
    if not ssh:
        return
    
    try:
        # 1. Compare critical files
        files_to_compare = [
            (f"{LOCAL_CONFIG['django_path']}/properties/models.py", 
             f"{PRODUCTION_CONFIG['django_path']}/properties/models.py", 
             "Properties Models"),
            (f"{LOCAL_CONFIG['django_path']}/local_settings.py",
             f"{PRODUCTION_CONFIG['django_path']}/real_estate_crm/settings.py",
             "Settings File"),
        ]
        
        for local_file, remote_file, description in files_to_compare:
            if os.path.exists(local_file):
                compare_file_content(local_file, remote_file, ssh, description)
            else:
                print(f"⚠️  Local file not found: {local_file}")
        
        # 2. Compare database content
        compare_database_samples()
        
        # 3. Compare file structure
        compare_static_and_media_structure(ssh)
        
        # 4. Test production URLs
        test_production_urls(ssh)
        
        print(f"\\n📝 Summary:")
        print("Check the differences above to identify why images work locally but not in production.")
        print("Key areas to focus on:")
        print("  1. Models.py get_all_image_urls method")
        print("  2. Database primary_image data")
        print("  3. File structure and nginx configuration")
        print("  4. URL response codes")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()