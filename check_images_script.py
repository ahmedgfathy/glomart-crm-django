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
import json
import re

def check_multiple_images():
    """Check which properties have multiple images"""
    print("Checking properties for multiple images...")
    
    properties = Property.objects.all()[:30]
    multi_count = 0
    total_with_images = 0
    
    for p in properties:
        if not p.primary_image or len(p.primary_image.strip()) <= 2:
            continue
        
        total_with_images += 1
        
        try:
            count = 0
            if p.primary_image.startswith('['):
                try:
                    images = json.loads(p.primary_image)
                    count = len(images) if images else 0
                    status = "Complete JSON"
                except json.JSONDecodeError:
                    id_matches = re.findall(r'"id":"([^"]+)"', p.primary_image)
                    count = len(id_matches)
                    status = "Regex fallback"
                
                if count > 1:
                    multi_count += 1
                    print(f"Property {p.pk}: {count} images ({status})")
                    urls = p.get_all_image_urls()
                    print(f"  Generated {len(urls)} URLs:")
                    for i, url in enumerate(urls[:3]):
                        print(f"    {i+1}: {url}")
                    if len(urls) > 3:
                        print(f"    ... and {len(urls)-3} more")
                    print("---")
                elif count == 1:
                    print(f"Property {p.pk}: 1 image ({status})")
                    
        except Exception as e:
            print(f"Error with {p.pk}: {e}")
    
    print(f"\nSUMMARY:")
    print(f"Properties checked: {total_with_images}")
    print(f"Properties with multiple images: {multi_count}")
    if total_with_images > 0:
        print(f"Percentage with multiple images: {(multi_count/total_with_images*100):.1f}%")

if __name__ == "__main__":
    check_multiple_images()