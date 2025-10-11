#!/usr/bin/env python3
"""
Production Update Script for Property Image Fix
This script updates the production server with the same fixes applied locally
"""

import os
import sys
import subprocess

def update_production_models():
    """Update the Property model methods in production"""
    
    # The fixed get_all_image_urls method for production
    fixed_get_all_image_urls = '''    def get_all_image_urls(self):
        """Extract all image URLs from the JSON data"""
        import json
        import re
        from django.conf import settings
        
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

    # The fixed get_image_url method for production
    fixed_get_image_url = '''    def get_image_url(self):
        """Extract the primary image URL from the JSON data"""
        import json
        import re
        
        if not self.primary_image:
            return '/static/images/property-placeholder.svg'
        
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
                        if file_url.startswith('/properties/'):
                            return '/public' + file_url
                        elif file_url.startswith('/property-images/'):
                            return file_url.replace('/property-images/', '/public/properties/images/')
                        return file_url
            # If it's just a direct URL string
            elif self.primary_image.startswith('http'):
                return self.primary_image
        except (json.JSONDecodeError, KeyError, IndexError):
            # If JSON parsing fails, try to extract fileUrl using regex
            file_url_matches = re.findall(r'"fileUrl":"([^"]+)"', self.primary_image)
            if file_url_matches:
                file_url = file_url_matches[0]
                if file_url.startswith('/property-images/'):
                    return file_url.replace('/property-images/', '/public/properties/images/')
                elif file_url.startswith('/properties/'):
                    return '/public' + file_url
                return file_url
        
        # Fallback to placeholder
        return '/static/images/property-placeholder.svg' '''

    return fixed_get_all_image_urls, fixed_get_image_url

def create_production_patch():
    """Create a patch file for production deployment"""
    
    print("Creating production patch file...")
    
    fixed_get_all_image_urls, fixed_get_image_url = update_production_models()
    
    patch_content = f'''#!/bin/bash
# Production deployment script for property image fix
# Run this script on your production server

echo "Updating Property model methods..."

# Backup the current models.py file
cp properties/models.py properties/models.py.backup.$(date +%Y%m%d_%H%M%S)

# Apply the fixes to properties/models.py
# Note: This needs to be done manually or with a proper deployment script

echo "Manual steps required:"
echo "1. Update the get_all_image_urls method in properties/models.py"
echo "2. Update the get_image_url method in properties/models.py" 
echo "3. Restart your Django application server"
echo "4. Test property image display"

echo ""
echo "The fixed methods are saved in production_model_fixes.py"
echo "Copy and replace the corresponding methods in your production properties/models.py"
'''

    # Save the patch script
    with open('/Users/ahmedgomaa/Downloads/crm/mcp/production_patch.sh', 'w') as f:
        f.write(patch_content)
    
    # Save the model fixes
    model_fixes = f'''"""
Production fixes for properties/models.py
Replace the existing get_all_image_urls and get_image_url methods with these versions
"""

{fixed_get_all_image_urls}

{fixed_get_image_url}
'''
    
    with open('/Users/ahmedgomaa/Downloads/crm/mcp/production_model_fixes.py', 'w') as f:
        f.write(model_fixes)
    
    print("✅ Created production_patch.sh")
    print("✅ Created production_model_fixes.py")
    print("")
    print("Next steps:")
    print("1. Copy production_model_fixes.py to your production server")
    print("2. Update properties/models.py with the fixed methods")
    print("3. Restart Django application server")
    
    return True

if __name__ == "__main__":
    create_production_patch()