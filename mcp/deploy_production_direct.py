#!/usr/bin/env python3
"""
Direct Production Deployment Script
This script connects to your production server and applies the property image fixes
"""

import os
import sys
import pymysql
import paramiko
from datetime import datetime

# Production server configuration
PRODUCTION_CONFIG = {
    'host': '5.180.148.92',
    'username': 'root',
    'password': 'ZeroCall20!@HH##1655&&',
    'ssh_key_path': None,  # Will use password authentication
    'django_path': '/var/www/glomart-crm',
    'systemd_service': 'gunicorn',
    'database': {
        'host': '5.180.148.92',
        'user': 'root', 
        'password': 'ZeroCall20!@HH##1655&&',
        'database': 'django_db_glomart_rs',
        'port': 3306
    }
}

def connect_to_production_db():
    """Connect to production MariaDB database"""
    try:
        connection = pymysql.connect(
            host=PRODUCTION_CONFIG['database']['host'],
            user=PRODUCTION_CONFIG['database']['user'],
            password=PRODUCTION_CONFIG['database']['password'],
            database=PRODUCTION_CONFIG['database']['database'],
            port=PRODUCTION_CONFIG['database']['port'],
            charset='utf8mb4'
        )
        print("✅ Connected to production database")
        return connection
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def connect_to_production_server():
    """Connect to production server via SSH"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Try to connect with password (you'll need to provide it)
        print(f"Connecting to {PRODUCTION_CONFIG['host']}...")
        ssh.connect(
            hostname=PRODUCTION_CONFIG['host'],
            username=PRODUCTION_CONFIG['username'],
            password=PRODUCTION_CONFIG['password'],
            timeout=10
        )
        print("✅ Connected to production server")
        return ssh
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return None

def backup_production_models(ssh):
    """Create backup of current models.py file"""
    backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_command = f"cp {PRODUCTION_CONFIG['django_path']}/properties/models.py {PRODUCTION_CONFIG['django_path']}/properties/models.py.backup.{backup_timestamp}"
    
    stdin, stdout, stderr = ssh.exec_command(backup_command)
    if stderr.read():
        print("❌ Failed to create backup")
        return False
    print("✅ Created backup of models.py")
    return True

def read_production_models(ssh):
    """Read current production models.py"""
    read_command = f"cat {PRODUCTION_CONFIG['django_path']}/properties/models.py"
    stdin, stdout, stderr = ssh.exec_command(read_command)
    
    if stderr.read():
        print("❌ Failed to read models.py")
        return None
    
    content = stdout.read().decode('utf-8')
    print("✅ Read current models.py content")
    return content

def create_fixed_models_content(original_content):
    """Create the updated models.py content with fixes"""
    
    # The production-ready get_all_image_urls method
    fixed_get_all_image_urls = '''    def get_all_image_urls(self):
        """Extract all image URLs from the JSON data"""
        import json
        import re
        
        if not self.primary_image:
            return ['/static/images/property-placeholder.svg']
        
        try:
            # If it's a JSON array with image objects
            if self.primary_image.startswith('['):
                image_array = json.loads(self.primary_image)
                if image_array and len(image_array) > 0:
                    urls = []
                    for img in image_array:
                        # Return the original cloud URL if available and convert path
                        if 'originalUrl' in img:
                            original_url = img['originalUrl']
                            if original_url.startswith('/property-images/'):
                                # For production, use /public/ path for nginx serving
                                urls.append(original_url.replace('/property-images/', '/public/properties/images/'))
                            elif original_url.startswith('/properties/'):
                                # For production, use /public/ path
                                urls.append('/public' + original_url)
                            else:
                                urls.append(original_url)
                        # Fallback to fileUrl if available - convert to /public/ path for production
                        elif 'fileUrl' in img:
                            file_url = img['fileUrl']
                            # Convert /properties/ or /property-images/ to /public/properties/images/ for nginx serving
                            if file_url.startswith('/properties/'):
                                urls.append('/public' + file_url)
                            elif file_url.startswith('/property-images/'):
                                urls.append(file_url.replace('/property-images/', '/public/properties/images/'))
                            else:
                                urls.append(file_url)
                    return urls if urls else ['/static/images/property-placeholder.svg']
            # If it's just a direct URL string
            elif self.primary_image.startswith('http'):
                return [self.primary_image]
        except (json.JSONDecodeError, KeyError, IndexError):
            # If JSON parsing fails, try to extract fileUrl using regex
            file_url_matches = re.findall(r'"fileUrl":"([^"]+)"', self.primary_image)
            if file_url_matches:
                urls = []
                for file_url in file_url_matches:
                    if file_url.startswith('/property-images/'):
                        urls.append(file_url.replace('/property-images/', '/public/properties/images/'))
                    elif file_url.startswith('/properties/'):
                        urls.append('/public' + file_url)
                    else:
                        urls.append(file_url)
                return urls if urls else ['/static/images/property-placeholder.svg']
        
        # Fallback to placeholder
        return ['/static/images/property-placeholder.svg']'''

    # Find and replace the get_all_image_urls method
    import re
    
    # Pattern to match the entire get_all_image_urls method
    pattern = r'(    def get_all_image_urls\(self\):.*?)(\n    def |\n    @property|\nclass |\Z)'
    
    def replacement(match):
        return fixed_get_all_image_urls + match.group(2)
    
    updated_content = re.sub(pattern, replacement, original_content, flags=re.DOTALL)
    
    if updated_content == original_content:
        print("⚠️  Warning: get_all_image_urls method not found or not replaced")
    else:
        print("✅ Updated get_all_image_urls method")
    
    return updated_content

def deploy_fixed_models(ssh, fixed_content):
    """Deploy the fixed models.py to production"""
    
    # Write the fixed content to a temporary file
    temp_file = f"/tmp/models_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    
    # Use cat with heredoc to write the file
    write_command = f'cat > {temp_file} << "EOF"\n{fixed_content}\nEOF'
    
    stdin, stdout, stderr = ssh.exec_command(write_command)
    error = stderr.read().decode('utf-8')
    if error:
        print(f"❌ Failed to write temp file: {error}")
        return False
    
    # Move the temp file to replace the original
    move_command = f"mv {temp_file} {PRODUCTION_CONFIG['django_path']}/properties/models.py"
    stdin, stdout, stderr = ssh.exec_command(move_command)
    error = stderr.read().decode('utf-8')
    if error:
        print(f"❌ Failed to move file: {error}")
        return False
    
    print("✅ Deployed fixed models.py")
    return True

def restart_django_service(ssh):
    """Restart the Django application service"""
    restart_command = f"systemctl reload {PRODUCTION_CONFIG['systemd_service']}"
    
    stdin, stdout, stderr = ssh.exec_command(restart_command)
    error = stderr.read().decode('utf-8')
    if error:
        print(f"⚠️  Service restart warning: {error}")
    
    print("✅ Restarted Django service")
    return True

def main():
    """Main deployment function"""
    print("🚀 Starting Production Deployment")
    print("=" * 50)
    
    # Connect to production server
    ssh = connect_to_production_server()
    if not ssh:
        return False
    
    try:
        # Step 1: Backup current models.py
        if not backup_production_models(ssh):
            return False
        
        # Step 2: Read current models.py
        original_content = read_production_models(ssh)
        if not original_content:
            return False
        
        # Step 3: Create fixed content
        fixed_content = create_fixed_models_content(original_content)
        
        # Step 4: Deploy fixed models
        if not deploy_fixed_models(ssh, fixed_content):
            return False
        
        # Step 5: Restart Django service
        restart_django_service(ssh)
        
        print("\n🎉 Production deployment completed successfully!")
        print("✅ Property images should now display correctly")
        print(f"🔗 Test at: http://{PRODUCTION_CONFIG['host']}/properties/")
        
        return True
        
    finally:
        ssh.close()

if __name__ == "__main__":
    # Check if required modules are available
    try:
        import paramiko
        import pymysql
    except ImportError as e:
        print(f"❌ Missing required module: {e}")
        print("Install with: pip install paramiko pymysql")
        sys.exit(1)
    
    success = main()
    sys.exit(0 if success else 1)