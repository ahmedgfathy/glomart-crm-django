#!/usr/bin/env python
import os
import django
import sys

# Add the project directory to the Python path
sys.path.append('/Users/ahmedgomaa/Downloads/crm')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
django.setup()

from leads.models import LeadAudit
from authentication.models import Module, Permission, Profile

print("=== AUDIT DEBUG ===")
print(f"Total audit logs: {LeadAudit.objects.count()}")

# Check first audit log
audit = LeadAudit.objects.first()
if audit:
    print(f"\nFirst audit log:")
    print(f"  ID: {audit.id}")
    print(f"  Action: {audit.action}")
    print(f"  User: {audit.user}")
    print(f"  User identifier: {audit.user_identifier}")
    print(f"  Timestamp: {audit.timestamp}")
    print(f"  Description: {audit.description}")
    print(f"  Lead: {audit.lead}")
    print(f"  Lead name backup: {audit.lead_name_backup}")
    print(f"  Severity: {audit.severity}")
    
    # Check if methods exist
    print(f"  get_action_display: {audit.get_action_display()}")
    print(f"  get_severity_display: {audit.get_severity_display()}")

print("\n=== PERMISSION RULES DEBUG ===")
print(f"Total modules: {Module.objects.count()}")
print(f"Total permissions: {Permission.objects.count()}")
print(f"Total profiles: {Profile.objects.count()}")

# Check audit module permissions
audit_module = Module.objects.filter(name='audit').first()
if audit_module:
    print(f"\nAudit module found: {audit_module.display_name}")
    audit_permissions = Permission.objects.filter(module=audit_module)
    print(f"Audit permissions: {audit_permissions.count()}")
    for perm in audit_permissions:
        print(f"  - {perm.code}: {perm.name} (level {perm.level})")
else:
    print("❌ No audit module found!")

# Check Administrator profile
admin_profile = Profile.objects.filter(name='Administrator').first()
if admin_profile:
    print(f"\nAdministrator profile found: {admin_profile.name}")
    admin_permissions = admin_profile.permissions.all()
    print(f"Administrator permissions: {admin_permissions.count()}")
    
    # Show audit permissions for admin
    admin_audit_perms = admin_profile.permissions.filter(module__name='audit')
    print(f"Admin audit permissions: {admin_audit_perms.count()}")
    for perm in admin_audit_perms:
        print(f"  - {perm.module.name}.{perm.code}: level {perm.level}")
else:
    print("❌ No Administrator profile found!")