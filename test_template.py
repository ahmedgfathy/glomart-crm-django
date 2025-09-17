#!/usr/bin/env python

import os
import sys
import django
from django.template import Template, Context
from django.template.loader import get_template

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
sys.path.append('/Users/ahmedgomaa/Downloads/crm')

django.setup()

try:
    # Try to load the audit template
    template = get_template('audit/audit_list.html')
    print("✅ Template loads successfully without syntax errors!")
    
    # Create a minimal context to test rendering
    from django.contrib.auth.models import User
    from django.core.paginator import Paginator
    from leads.models import LeadAudit
    
    # Get some audit data
    audits = LeadAudit.objects.all()[:5]  # Get first 5 audits
    paginator = Paginator(audits, 10)
    page_obj = paginator.get_page(1)
    
    context = {
        'page_obj': page_obj,
        'total_audits': LeadAudit.objects.count(),
        'user': User.objects.first() if User.objects.exists() else None,
        'can_view_all': True,
    }
    
    # Try to render the template
    rendered = template.render(context)
    print(f"✅ Template renders successfully! ({len(rendered)} characters)")
    print(f"🗂️  Found {len(audits)} audit logs")
    
except Exception as e:
    print(f"❌ Template error: {e}")
    import traceback
    traceback.print_exc()