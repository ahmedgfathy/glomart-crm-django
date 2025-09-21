#!/usr/bin/env python3

import os
import sys
import django

# Add the current directory to the Python path
sys.path.append('/var/www/glomart-crm')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')

# Setup Django
django.setup()

from properties.models import Property

def test_property_images():
    """Test property image URLs"""
    properties = Property.objects.all()[:10]
    
    print("=== Property Image URL Test ===")
    for prop in properties:
        print(f"\nProperty ID: {prop.pk}")
        print(f"Primary Image Raw: {repr(prop.primary_image)}")
        
        try:
            urls = prop.get_all_image_urls()
            print(f"Generated URLs: {urls}")
            
            # Check if it's using placeholder
            if any('placeholder' in url for url in urls):
                print("⚠️  Using placeholder - image parsing failed")
            else:
                print("✅ Generated actual image URLs")
                
        except Exception as e:
            print(f"❌ Error generating URLs: {e}")
            
        print("-" * 50)

if __name__ == "__main__":
    test_property_images()