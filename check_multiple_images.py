#!/usr/bin/env python3
"""
Script to check which properties have multiple images in production
"""

import paramiko
import sys

def check_multiple_images():
    # Production server details
    hostname = '5.180.148.92'
    username = 'root'
    password = 'ZeroCall20!@HH##1655&&'
    
    print("🔍 Checking properties with multiple images...")
    
    try:
        # Connect to production server
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, password=password)
        print("✅ Connected to production server")
        
        # Python script to run on the server
        check_script = '''
from properties.models import Property
import json
import re

print("Checking image counts for all properties...")
print("=" * 60)

properties = Property.objects.filter(primary_image__isnull=False).exclude(primary_image="").exclude(primary_image="[]")
total_checked = 0
multiple_image_count = 0

for p in properties:
    total_checked += 1
    try:
        if p.primary_image.startswith("["):
            # Try parsing JSON first
            try:
                images = json.loads(p.primary_image)
                count = len(images) if images else 0
                status = "Complete JSON"
                
                if count > 1:
                    print(f"✅ Property {p.pk}: {count} images ({status})")
                    urls = p.get_all_image_urls()
                    for i, url in enumerate(urls[:3]):  # Show first 3 URLs
                        print(f"   Image {i+1}: {url}")
                    if len(urls) > 3:
                        print(f"   ... and {len(urls)-3} more images")
                    multiple_image_count += 1
                    print("-" * 40)
                    
            except json.JSONDecodeError:
                # Use regex fallback
                id_matches = re.findall(r\'"id":"([^"]+)"\', p.primary_image)
                count = len(id_matches)
                status = "Truncated JSON (regex)"
                
                if count > 1:
                    print(f"⚠️  Property {p.pk}: {count} images ({status})")
                    urls = p.get_all_image_urls()
                    for i, url in enumerate(urls[:3]):
                        print(f"   Image {i+1}: {url}")
                    if len(urls) > 3:
                        print(f"   ... and {len(urls)-3} more images")
                    multiple_image_count += 1
                    print("-" * 40)
                    
    except Exception as e:
        print(f"❌ Property {p.pk}: Error - {e}")

print("=" * 60)
print(f"SUMMARY:")
print(f"📊 Total properties checked: {total_checked}")
print(f"🖼️  Properties with multiple images: {multiple_image_count}")
print(f"📈 Percentage with multiple images: {(multiple_image_count/total_checked*100):.1f}%")

# Check a few single-image properties for reference
print("\\nSample single-image properties:")
single_image_props = Property.objects.filter(primary_image__isnull=False).exclude(primary_image="").exclude(primary_image="[]")[:5]
for p in single_image_props:
    try:
        urls = p.get_all_image_urls()
        if len(urls) == 1 and "placeholder" not in urls[0]:
            print(f"📷 Property {p.pk}: 1 image - {urls[0]}")
    except:
        pass
'''
        
        # Execute the script on the server
        command = f'cd /var/www/glomart-crm && source venv/bin/activate && python manage.py shell -c "{check_script}"'
        stdin, stdout, stderr = ssh.exec_command(command)
        
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        if output:
            print(output)
        if error and "48 objects imported" not in error:
            print(f"⚠️  Error output: {error}")
        
        ssh.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to check images: {str(e)}")
        return False

if __name__ == "__main__":
    success = check_multiple_images()
    sys.exit(0 if success else 1)