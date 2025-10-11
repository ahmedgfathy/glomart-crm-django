#!/usr/bin/env python3
"""
Test script to verify local data is properly loaded
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
django.setup()

from django.contrib.auth.models import User
from properties.models import Property
from leads.models import Lead

def test_data():
    print("🔍 Testing local data access...")
    
    try:
        # Test users
        user_count = User.objects.count()
        print(f"👤 Users: {user_count}")
        
        if user_count > 0:
            sample_user = User.objects.first()
            print(f"   Sample user: {sample_user.username} ({sample_user.email})")
        
        # Test properties  
        property_count = Property.objects.count()
        print(f"🏠 Properties: {property_count}")
        
        if property_count > 0:
            sample_property = Property.objects.first()
            print(f"   Sample property: {sample_property.property_id}")
        
        # Test leads
        lead_count = Lead.objects.count() 
        print(f"👥 Leads: {lead_count}")
        
        if lead_count > 0:
            sample_lead = Lead.objects.first()
            print(f"   Sample lead: {sample_lead.first_name} {sample_lead.last_name}")
        
        print(f"\n🎉 SUCCESS! Local database has {user_count + property_count + lead_count} total records")
        return True
        
    except Exception as e:
        print(f"❌ Error testing data: {e}")
        return False

if __name__ == '__main__':
    test_data()
