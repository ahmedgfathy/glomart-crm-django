#!/usr/bin/env python3
"""
Production deployment script to fix property image display issues.
This updates the get_image_url method to include regex fallback for corrupted JSON.
"""

import paramiko
import sys
import re

def deploy_to_production():
    # Production server details
    hostname = '5.180.148.92'
    username = 'root'
    password = 'ZeroCall20!@HH##1655&&'
    
    # Path to the models.py file on production
    models_path = '/var/www/glomart-crm/properties/models.py'
    
    print("🚀 Starting production deployment to fix property images...")
    
    try:
        # Connect to production server
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, password=password)
        print("✅ Connected to production server")
        
        # Read the current models.py file
        sftp = ssh.open_sftp()
        with sftp.file(models_path, 'r') as f:
            content = f.read()
        
        # Convert bytes to string if needed
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        print("✅ Read current models.py file")
        
        # Define the new get_image_url method with regex fallback
        new_get_image_url_method = '''    def get_image_url(self):
        """Extract the primary image URL from the JSON data"""
        import json
        import re
        
        if not self.primary_image:
            return '/static/images/property-placeholder.jpg'
        
        try:
            # If it's a JSON array with image objects
            if self.primary_image.startswith('['):
                image_array = json.loads(self.primary_image)
                if image_array and len(image_array) > 0:
                    first_image = image_array[0]
                    # Return the original cloud URL if available and convert path
                    if 'originalUrl' in first_image:
                        original_url = first_image['originalUrl']
                        if original_url.startswith('/property-images/'):
                            return original_url.replace('/property-images/', '/public/properties/images/')
                        elif original_url.startswith('/properties/'):
                            return '/public' + original_url
                        return original_url
                    # Fallback to fileUrl if available - convert to /public/ path
                    elif 'fileUrl' in first_image:
                        file_url = first_image['fileUrl']
                        # Convert /properties/ or /property-images/ to /public/properties/images/ for nginx serving
                        if file_url.startswith('/properties/'):
                            return '/public' + file_url
                        elif file_url.startswith('/property-images/'):
                            return file_url.replace('/property-images/', '/public/properties/images/')
                        return file_url
            # If it's just a direct URL string
            elif self.primary_image.startswith('http'):
                return self.primary_image
        except (json.JSONDecodeError, KeyError, IndexError):
            # Regex fallback for corrupted JSON
            print(f"JSON parsing failed for primary_image, using regex fallback")
            # Look for image IDs in the corrupted JSON using regex
            id_matches = re.findall(r'"id":"([^"]+)"', self.primary_image)
            if id_matches:
                first_image_id = id_matches[0]
                return f'/public/properties/images/{first_image_id}.jpg'
        
        # Fallback to placeholder
        return '/static/images/property-placeholder.jpg'
'''
        
        # Pattern to find the existing get_image_url method
        pattern = r'    def get_image_url\(self\):.*?(?=    def|\Z)'
        
        # Replace the method
        new_content = re.sub(pattern, new_get_image_url_method, content, flags=re.DOTALL)
        
        if new_content == content:
            print("❌ Failed to find and replace get_image_url method")
            return False
        
        # Write the updated content back
        with sftp.open(models_path, 'w') as f:
            f.write(new_content)
        print("✅ Updated models.py with regex fallback for get_image_url")
        
        # Restart Django application
        stdin, stdout, stderr = ssh.exec_command('systemctl restart gunicorn')
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print("✅ Successfully restarted gunicorn service")
        else:
            print(f"⚠️  Gunicorn restart exit status: {exit_status}")
            error_output = stderr.read().decode()
            if error_output:
                print(f"Error: {error_output}")
        
        # Test the fix
        print("\n🧪 Testing the fix...")
        stdin, stdout, stderr = ssh.exec_command(
            'cd /var/www/glomart-crm && source venv/bin/activate && '
            'python manage.py shell -c "'
            'from properties.models import Property; '
            'p = Property.objects.first(); '
            'print(f\"Image URL: {p.get_image_url()}\"); '
            '"'
        )
        
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        if output:
            print(f"✅ Test output: {output}")
        if error and "48 objects imported" not in error:
            print(f"⚠️  Test stderr: {error}")
        
        # Clean up
        sftp.close()
        ssh.close()
        
        print("\n🎉 Production deployment completed successfully!")
        print("🌐 Check the website: https://sys.glomartrealestates.com/properties/")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = deploy_to_production()
    sys.exit(0 if success else 1)