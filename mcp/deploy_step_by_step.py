#!/usr/bin/env python3
"""
Production Deployment - Step by Step
"""

import paramiko
from datetime import datetime

# Production server configuration
PRODUCTION_CONFIG = {
    'host': '5.180.148.92',
    'username': 'root',
    'password': 'ZeroCall20!@HH##1655&&',
}

def connect_to_production():
    """Connect to production server via SSH"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
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

def find_django_path(ssh):
    """Find the Django project path"""
    possible_paths = [
        '/var/www/real_estate_crm',
        '/var/www/html/real_estate_crm',
        '/home/real_estate_crm',
        '/opt/real_estate_crm',
        '/root/real_estate_crm'
    ]
    
    for path in possible_paths:
        stdin, stdout, stderr = ssh.exec_command(f"ls {path}/properties/models.py 2>/dev/null")
        if not stderr.read():
            print(f"✅ Found Django project at: {path}")
            return path
    
    # If not found in common locations, search for it
    print("Searching for Django project...")
    stdin, stdout, stderr = ssh.exec_command("find / -name 'models.py' -path '*/properties/*' 2>/dev/null | head -5")
    output = stdout.read().decode('utf-8').strip()
    
    if output:
        for line in output.split('\n'):
            if 'properties/models.py' in line:
                django_path = line.replace('/properties/models.py', '')
                print(f"✅ Found Django project at: {django_path}")
                return django_path
    
    print("❌ Could not find Django project")
    return None

def examine_current_models(ssh, django_path):
    """Examine the current models.py file"""
    models_path = f"{django_path}/properties/models.py"
    
    # Check if file exists
    stdin, stdout, stderr = ssh.exec_command(f"ls -la {models_path}")
    if stderr.read():
        print(f"❌ models.py not found at {models_path}")
        return False
    
    file_info = stdout.read().decode('utf-8').strip()
    print(f"📄 Current models.py: {file_info}")
    
    # Check current get_all_image_urls method
    stdin, stdout, stderr = ssh.exec_command(f"grep -A 5 'def get_all_image_urls' {models_path}")
    method_preview = stdout.read().decode('utf-8').strip()
    
    if method_preview:
        print("📋 Current get_all_image_urls method preview:")
        print(method_preview[:200] + "..." if len(method_preview) > 200 else method_preview)
    else:
        print("⚠️  get_all_image_urls method not found")
    
    return True

def create_backup(ssh, django_path):
    """Create backup of models.py"""
    models_path = f"{django_path}/properties/models.py"
    backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{models_path}.backup.{backup_timestamp}"
    
    stdin, stdout, stderr = ssh.exec_command(f"cp {models_path} {backup_path}")
    error = stderr.read().decode('utf-8')
    if error:
        print(f"❌ Backup failed: {error}")
        return False
    
    print(f"✅ Created backup: {backup_path}")
    return True

def deploy_fix(ssh, django_path):
    """Deploy the property image fix"""
    
    # The fixed method for production
    fixed_method = '''    def get_all_image_urls(self):
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
    
    # First, create a temporary file with the replacement
    temp_script = f"/tmp/fix_models_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    
    script_content = f'''#!/usr/bin/env python3
import re

# Read the current models.py
with open('{django_path}/properties/models.py', 'r') as f:
    content = f.read()

# Replace the get_all_image_urls method
# Pattern to find the method
pattern = r'(    def get_all_image_urls\\(self\\):.*?)(?=\\n    def |\\n    @property|\\nclass |\\Z)'

replacement = """{fixed_method}"""

updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write the updated content back
with open('{django_path}/properties/models.py', 'w') as f:
    f.write(updated_content)

print("✅ Updated get_all_image_urls method")
'''

    # Upload and run the script
    stdin, stdout, stderr = ssh.exec_command(f'cat > {temp_script} << "EOF"\n{script_content}\nEOF')
    if stderr.read():
        print("❌ Failed to create temp script")
        return False
    
    stdin, stdout, stderr = ssh.exec_command(f"python3 {temp_script}")
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    
    if error:
        print(f"❌ Script execution failed: {error}")
        return False
    
    print(f"✅ {output.strip()}")
    
    # Clean up temp script
    ssh.exec_command(f"rm {temp_script}")
    
    return True

def restart_services(ssh):
    """Restart Django services"""
    
    # Try common service restart commands
    services = ['gunicorn', 'uwsgi', 'nginx', 'apache2']
    
    for service in services:
        stdin, stdout, stderr = ssh.exec_command(f"systemctl is-active {service} 2>/dev/null")
        if stdout.read().decode('utf-8').strip() == 'active':
            print(f"🔄 Restarting {service}...")
            stdin, stdout, stderr = ssh.exec_command(f"systemctl reload {service}")
            error = stderr.read().decode('utf-8')
            if not error:
                print(f"✅ Restarted {service}")
            else:
                print(f"⚠️  {service} restart warning: {error}")

def main():
    """Main deployment process"""
    print("🚀 Production Deployment - Property Image Fix")
    print("=" * 60)
    
    # Connect to server
    ssh = connect_to_production()
    if not ssh:
        return False
    
    try:
        # Find Django project path
        django_path = find_django_path(ssh)
        if not django_path:
            return False
        
        # Examine current models
        if not examine_current_models(ssh, django_path):
            return False
        
        # Create backup
        if not create_backup(ssh, django_path):
            return False
        
        # Deploy fix
        if not deploy_fix(ssh, django_path):
            return False
        
        # Restart services
        restart_services(ssh)
        
        print("\n🎉 Production deployment completed!")
        print("✅ Property images should now display correctly")
        print(f"🔗 Test at: http://{PRODUCTION_CONFIG['host']}/properties/")
        
        return True
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()