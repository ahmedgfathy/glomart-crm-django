#!/usr/bin/env python3
"""
Quick fix: Update settings.py with correct root password
"""
import os
import re

def update_settings_password():
    settings_path = '/var/www/glomart-crm/real_estate_crm/settings.py'
    
    if not os.path.exists(settings_path):
        settings_path = 'real_estate_crm/settings.py'  # Local development path
    
    try:
        with open(settings_path, 'r') as f:
            content = f.read()
        
        # Update the password in DATABASES configuration
        # Look for the password line and replace it
        updated_content = re.sub(
            r"'PASSWORD': '[^']*'",
            "'PASSWORD': 'ZeroCall20!@HH##1655&&'",
            content
        )
        
        with open(settings_path, 'w') as f:
            f.write(updated_content)
        
        print(f"✅ Updated password in {settings_path}")
        print("✅ Settings now use correct production password")
        
    except Exception as e:
        print(f"❌ Error updating settings: {e}")
        print("Please update manually:")
        print("Change 'PASSWORD': 'zerocall' to 'PASSWORD': 'ZeroCall20!@HH##1655&&'")

if __name__ == "__main__":
    update_settings_password()
