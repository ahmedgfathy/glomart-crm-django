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

print("🔍 TESTING FILTER DATA")
print("=" * 50)

# Test action choices
print(f"✅ ACTION_TYPES available: {hasattr(LeadAudit, 'ACTION_TYPES')}")
if hasattr(LeadAudit, 'ACTION_TYPES'):
    print(f"📋 Actions ({len(LeadAudit.ACTION_TYPES)}):")
    for value, label in LeadAudit.ACTION_TYPES:
        count = LeadAudit.objects.filter(action=value).count()
        print(f"   - {value}: {label} ({count} records)")

print()

# Test severity choices
print(f"✅ SEVERITY_CHOICES available: {hasattr(LeadAudit, 'SEVERITY_CHOICES')}")
if hasattr(LeadAudit, 'SEVERITY_CHOICES'):
    print(f"📊 Severities ({len(LeadAudit.SEVERITY_CHOICES)}):")
    for value, label in LeadAudit.SEVERITY_CHOICES:
        count = LeadAudit.objects.filter(severity=value).count()
        print(f"   - {value}: {label} ({count} records)")

print()

# Test users for filter
print("👥 USERS WITH AUDIT RECORDS:")
users_with_audits = User.objects.filter(lead_audits__isnull=False).distinct()
print(f"Found {users_with_audits.count()} users with audit records:")
for user in users_with_audits:
    audit_count = user.lead_audits.count()
    print(f"   - {user.get_full_name() or user.username} ({user.id}): {audit_count} audits")

print()

# Test sample audit record
print("🗂️ SAMPLE AUDIT RECORD:")
sample_audit = LeadAudit.objects.first()
if sample_audit:
    print(f"   ID: {sample_audit.id}")
    print(f"   Action: {sample_audit.action} ({sample_audit.get_action_display()})")
    print(f"   Severity: {sample_audit.severity} ({sample_audit.get_severity_display()})")
    print(f"   User: {sample_audit.user_identifier}")
    print(f"   Timestamp: {sample_audit.timestamp}")
    print(f"   Lead: {sample_audit.lead_identifier}")
else:
    print("   No audit records found!")