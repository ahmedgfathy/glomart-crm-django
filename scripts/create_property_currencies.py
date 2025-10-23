#!/usr/bin/env python3
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings_local')
django.setup()

from properties.models import Currency

# Create property currencies
currencies = [
    {'code': 'EGP', 'name': 'Egyptian Pound', 'symbol': 'LE'},
    {'code': 'USD', 'name': 'US Dollar', 'symbol': '$'},
    {'code': 'EUR', 'name': 'Euro', 'symbol': '€'},
]

for curr_data in currencies:
    currency, created = Currency.objects.get_or_create(
        code=curr_data['code'],
        defaults=curr_data
    )
    if created:
        print(f'Created property currency: {currency}')
    else:
        print(f'Currency already exists: {currency}')

print("✅ Property currencies setup complete!")