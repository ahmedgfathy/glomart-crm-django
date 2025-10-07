#!/usr/bin/env python3
"""
Initialize Owner Database records in Django for all cloned rs_ databases
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
django.setup()

from owner.models import OwnerDatabase
import pymysql

def initialize_owner_databases():
    print("🏠 Initializing Owner Database records...")
    
    try:
        # Get all rs_ databases from local MariaDB
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='zerocall',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SHOW DATABASES LIKE 'rs_%'")
            databases = cursor.fetchall()
            
        connection.close()
        
        if not databases:
            print("⚠️  No rs_ databases found in local MariaDB")
            return
        
        created_count = 0
        updated_count = 0
        
        # Database categories mapping
        db_categories = {
            'rehab': 'Real Estate - Major Developments',
            'marassi': 'Real Estate - Major Developments', 
            'mivida': 'Real Estate - Major Developments',
            'palm': 'Real Estate - Major Developments',
            'uptown': 'Real Estate - Compound Projects',
            'amwaj': 'Real Estate - Compound Projects',
            'gouna': 'Real Estate - Regional Projects',
            'mangroovy': 'Real Estate - Regional Projects',
            'sahel': 'Real Estate - Regional Projects',
            'katameya': 'Real Estate - New Cairo/Tagamoa',
            'sabour': 'Real Estate - New Cairo/Tagamoa',
            'tagamoa': 'Real Estate - New Cairo/Tagamoa',
            'zayed': 'Real Estate - 6th October/Zayed',
            'october': 'Real Estate - 6th October/Zayed',
            'villas': 'Real Estate - 6th October/Zayed',
            'sodic': 'Real Estate - SODIC Projects',
            'jedar': 'Real Estate - Other Developments',
            'hadaeq': 'Real Estate - Other Developments',
            'alexandria': 'Real Estate - Other Developments',
            'emaar': 'Real Estate - Commercial/Corporate',
            'vip': 'Real Estate - Commercial/Corporate',
            'customer': 'Real Estate - Commercial/Corporate',
            'mawasem': 'Real Estate - Commercial/Corporate',
            'sea_shell': 'Real Estate - Commercial/Corporate',
            'jaguar': 'Automotive',
            'jeep': 'Automotive',
        }
        
        for db_info in databases:
            db_name = db_info['Database (rs_%)']
            
            # Determine category
            category = 'Uncategorized'
            for keyword, cat in db_categories.items():
                if keyword in db_name.lower():
                    category = cat
                    break
            
            # Create or update database record
            db_obj, created = OwnerDatabase.objects.get_or_create(
                name=db_name,
                defaults={
                    'category': category,
                    'table_name': 'data',
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                print(f"  ✅ Created: {db_name} ({category})")
            else:
                # Update category if changed
                if db_obj.category != category:
                    db_obj.category = category
                    db_obj.save()
                    updated_count += 1
                    print(f"  📝 Updated: {db_name} ({category})")
            
            # Generate and set display name
            if not db_obj.display_name or db_obj.display_name == db_obj.name:
                db_obj.display_name = db_obj.generate_display_name()
                db_obj.save()
            
            # Update record count
            table_info = db_obj.get_table_info()
            if table_info:
                print(f"     📊 Records: {table_info['record_count']:,}")
        
        print(f"\n🎉 Owner Database initialization complete!")
        print(f"  ✅ Created: {created_count}")
        print(f"  📝 Updated: {updated_count}")
        print(f"  📊 Total Owner Databases: {len(databases)}")
        
    except Exception as e:
        print(f"❌ Error initializing owner databases: {e}")

if __name__ == '__main__':
    initialize_owner_databases()
