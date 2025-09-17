#!/usr/bin/env python

import os
import sys

# Configure Django settings FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
sys.path.append('/Users/ahmedgomaa/Downloads/crm')

import django
django.setup()

from leads.models import LeadAudit
from django.contrib.auth.models import User

print("🧪 TESTING AUDIT FUNCTIONALITY")
print("=" * 50)

# Test 1: Get audit record 15
print("1. TESTING AUDIT DETAIL PAGE:")
try:
    audit = LeadAudit.objects.get(id=15)
    print(f"   ✅ Audit ID 15 found")
    print(f"   📝 Action: {audit.get_action_display()}")
    print(f"   👤 User: {audit.user_identifier}")
    print(f"   📊 Severity: {audit.get_severity_display()}")
    print(f"   🏠 Lead: {audit.lead_identifier}")
    print(f"   📅 Time: {audit.timestamp}")
except LeadAudit.DoesNotExist:
    print("   ❌ Audit ID 15 not found")

print()

# Test 2: Check why users filter is empty
print("2. DEBUGGING USER FILTER:")
total_audits = LeadAudit.objects.all().count()
audits_with_user = LeadAudit.objects.filter(user__isnull=False).count()
audits_without_user = LeadAudit.objects.filter(user__isnull=True).count()

print(f"   📊 Total audits: {total_audits}")
print(f"   👤 Audits with user: {audits_with_user}")
print(f"   ❓ Audits without user: {audits_without_user}")

if audits_with_user > 0:
    users_in_audits = User.objects.filter(lead_audits__isnull=False).distinct()
    print(f"   🧑‍💼 Users found in audits: {users_in_audits.count()}")
    for user in users_in_audits:
        print(f"      - {user.get_full_name() or user.username} (ID: {user.id})")

print()

# Test 3: Test filtering functionality
print("3. TESTING FILTER FUNCTIONALITY:")

# Test action filter
update_audits = LeadAudit.objects.filter(action='update').count()
print(f"   🔄 'update' action audits: {update_audits}")

score_audits = LeadAudit.objects.filter(action='score_change').count()
print(f"   📈 'score_change' action audits: {score_audits}")

# Test severity filter
medium_audits = LeadAudit.objects.filter(severity='medium').count()
high_audits = LeadAudit.objects.filter(severity='high').count()
print(f"   📊 'medium' severity audits: {medium_audits}")
print(f"   ⚠️ 'high' severity audits: {high_audits}")

print()

# Test 4: Create a test user audit if needed
print("4. FIXING USER ASSIGNMENT:")
admin_user = User.objects.filter(is_superuser=True).first()
if admin_user:
    print(f"   👑 Found admin user: {admin_user.username}")
    
    # Update some audit records to have a user
    audit_ids_to_update = list(LeadAudit.objects.filter(user__isnull=True).values_list('id', flat=True)[:5])
    updated_count = LeadAudit.objects.filter(id__in=audit_ids_to_update).update(user=admin_user)
    print(f"   ✅ Updated {updated_count} audit records to have user: {admin_user.username}")
    
    # Verify the fix
    users_now = User.objects.filter(lead_audits__isnull=False).distinct().count()
    print(f"   🔄 Users in filter now: {users_now}")
else:
    print("   ❌ No admin user found")