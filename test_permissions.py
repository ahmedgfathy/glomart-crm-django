#!/usr/bin/env python3
"""
Test script to verify permission slider auto-save functionality
"""
import os
import sys

# Setup Django environment BEFORE importing anything else
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
sys.path.append('/Users/ahmedgomaa/Downloads/crm')

import django
django.setup()

import json
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.http import JsonResponse

from authentication.models import Profile, Module, Permission
from authentication.views import update_profile_permissions

def test_permission_update():
    """Test permission update for all levels including level 4"""
    
    # Create a test superuser if not exists
    try:
        admin_user = User.objects.get(username='admin')
    except User.DoesNotExist:
        admin_user = User.objects.create_superuser('admin', 'admin@test.com', 'admin')
    
    # Get or create a test profile
    try:
        profile = Profile.objects.first()
        if not profile:
            print("No profiles found in database")
            return
    except Exception as e:
        print(f"Error getting profile: {e}")
        return
    
    # Get a test module
    try:
        module = Module.objects.first()
        if not module:
            print("No modules found in database")
            return
    except Exception as e:
        print(f"Error getting module: {e}")
        return
    
    print(f"Testing permission updates for profile: {profile.name}")
    print(f"Using module: {module.name}")
    print("-" * 50)
    
    # Test all permission levels
    factory = RequestFactory()
    
    for level in range(1, 5):  # Test levels 1-4
        print(f"\nTesting Level {level}:")
        
        # Create a mock AJAX request
        data = json.dumps({
            'module': module.name,
            'level': level
        })
        
        request = factory.post(
            f'/authentication/update-permissions/{profile.id}/',
            data=data,
            content_type='application/json'
        )
        request.user = admin_user
        
        # Call the update function
        try:
            response = update_profile_permissions(request, profile.id)
            
            if isinstance(response, JsonResponse):
                response_data = json.loads(response.content.decode())
                if response_data.get('success'):
                    print(f"  ✅ Level {level}: SUCCESS")
                    
                    # Check what permissions were actually added
                    current_perms = profile.permissions.filter(module=module)
                    print(f"     Added {current_perms.count()} permissions:")
                    for perm in current_perms:
                        print(f"       - {perm.name} (level {perm.level})")
                else:
                    print(f"  ❌ Level {level}: FAILED - {response_data.get('error', 'Unknown error')}")
            else:
                print(f"  ❌ Level {level}: FAILED - Invalid response type")
                
        except Exception as e:
            print(f"  ❌ Level {level}: EXCEPTION - {str(e)}")
    
    print("\n" + "=" * 50)
    print("Test completed. Check debug output above for any issues.")

if __name__ == "__main__":
    test_permission_update()