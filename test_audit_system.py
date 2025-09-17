#!/usr/bin/env python

import os
import sys

# Configure Django settings FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
sys.path.append('/Users/ahmedgomaa/Downloads/crm')

import django
django.setup()

from django.test import Client
from django.contrib.auth.models import User

# Create a test client
client = Client()

print("🧪 Testing Complete Audit System...")
print("=" * 50)

try:
    # Test 1: Access audit list page
    print("1. Testing audit list page...")
    response = client.get('/audit/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Audit list page loads successfully!")
        print(f"   📄 Content length: {len(response.content)} bytes")
    else:
        print(f"   ❌ Failed to load audit list (status: {response.status_code})")
    
    # Test 2: Check for authentication requirement
    print("\n2. Testing authentication...")
    if response.status_code == 302:
        print("   ✅ Authentication required (redirected to login)")
    elif response.status_code == 200:
        print("   ⚠️  No authentication required")
    
    # Test 3: Test with logged-in user
    print("\n3. Testing with authenticated user...")
    user = User.objects.first()
    if user:
        client.force_login(user)
        response = client.get('/audit/')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Authenticated access works!")
            
            # Check if audit data is present
            content = response.content.decode('utf-8')
            if 'No audit logs found' in content:
                print("   📋 No audit logs displayed")
            elif 'audit-row' in content:
                print("   📋 Audit logs are displayed!")
            else:
                print("   ⚠️  Unclear audit display status")
        else:
            print(f"   ❌ Authentication failed (status: {response.status_code})")
    else:
        print("   ❌ No users found in database")
    
    # Test 4: Check profile/permissions page
    print("\n4. Testing profile/permissions page...")
    response = client.get('/authentication/profile/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Profile page loads successfully!")
        content = response.content.decode('utf-8')
        if 'permission-slider' in content:
            print("   🎛️  Permission sliders are present!")
        else:
            print("   ⚠️  Permission sliders not found")
    else:
        print(f"   ❌ Profile page failed (status: {response.status_code})")

    # Test 5: Count audit logs
    from leads.models import LeadAudit
    audit_count = LeadAudit.objects.count()
    print(f"\n5. Database verification:")
    print(f"   📊 Total audit logs in database: {audit_count}")
    
    if audit_count > 0:
        latest_audit = LeadAudit.objects.latest('timestamp')
        print(f"   🕒 Latest audit: {latest_audit.action} on {latest_audit.timestamp}")
        print("   ✅ Audit system has data!")
    else:
        print("   ⚠️  No audit logs in database")

except Exception as e:
    print(f"❌ Test failed with error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("🏁 Audit System Test Complete!")