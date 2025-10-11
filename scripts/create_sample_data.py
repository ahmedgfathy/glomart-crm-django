#!/usr/bin/env python3
"""
Create sample data for local development
"""
import os
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models.signals import post_save, post_delete, pre_save

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings_local')
django.setup()

from django.contrib.auth.models import User
from properties.models import (
    Property, Region, PropertyType, PropertyCategory, 
    PropertyStatus, Compound, UnitPurpose, FinishingType,
    PropertyActivity, Project as PropertyProject
)
from leads.models import Lead, LeadSource, LeadStatus, LeadPriority
from projects.models import (
    Project, ProjectStatus, ProjectType, ProjectCategory,
    ProjectPriority
)
from properties.models import Currency as PropertyCurrency
from projects.models import Currency as ProjectCurrency
from authentication.models import Profile, Module, FieldPermission

def create_property_lookup_data():
    """Create property lookup data"""
    print("Creating property lookup data...")
    
    # Regions
    regions_data = [
        "Cairo", "Giza", "Alexandria", "New Capital", "6th October",
        "Sheikh Zayed", "New Cairo", "Maadi", "Zamalek", "Heliopolis"
    ]
    for region_name in regions_data:
        Region.objects.get_or_create(name=region_name)
    
    # Property Types
    types_data = [
        "Apartment", "Villa", "Townhouse", "Duplex", "Penthouse",
        "Studio", "Office", "Shop", "Warehouse", "Land"
    ]
    for type_name in types_data:
        PropertyType.objects.get_or_create(name=type_name)
    
    # Property Categories
    categories_data = [
        "Residential", "Commercial", "Administrative", "Medical",
        "Industrial", "Retail", "Mixed Use"
    ]
    for category_name in categories_data:
        PropertyCategory.objects.get_or_create(name=category_name)
    
    # Property Status
    statuses_data = [
        ("Available", "#28a745"),
        ("Sold", "#dc3545"),
        ("Reserved", "#ffc107"),
        ("Under Construction", "#17a2b8"),
        ("Rented", "#6f42c1")
    ]
    for status_name, color in statuses_data:
        PropertyStatus.objects.get_or_create(
            name=status_name,
            defaults={'color': color}
        )
    
    # Compounds
    compounds_data = [
        "Palm Hills October", "Al Rehab City", "Madinaty", "Hyde Park",
        "Taj City", "Mountain View", "Sodic West", "New Giza"
    ]
    for compound_name in compounds_data:
        Compound.objects.get_or_create(name=compound_name)
    
    # Unit Purposes
    purposes_data = ["Sale", "Rent", "Investment"]
    for purpose_name in purposes_data:
        UnitPurpose.objects.get_or_create(name=purpose_name)
    
    # Finishing Types
    finishing_data = [
        "Fully Finished", "Semi Finished", "Core & Shell", "Lux Finished"
    ]
    for finishing_name in finishing_data:
        FinishingType.objects.get_or_create(name=finishing_name)
    
    # Activities
    activities_data = [
        "Hot Lead", "Follow Up", "Site Visit", "Negotiation", "Closed"
    ]
    for activity_name in activities_data:
        PropertyActivity.objects.get_or_create(name=activity_name)
    
    # Property Projects
    projects_data = [
        "New Capital Phase 1", "6th October Gardens", "Zamalek Tower",
        "Maadi Residence", "Heliopolis Plaza"
    ]
    for project_name in projects_data:
        PropertyProject.objects.get_or_create(name=project_name)

def create_lead_lookup_data():
    """Create lead lookup data"""
    print("Creating lead lookup data...")
    
    # Lead Sources
    sources_data = [
        "Website", "Facebook", "Instagram", "Referral", "Cold Call",
        "Walk-in", "Exhibition", "WhatsApp", "Email Campaign"
    ]
    for source_name in sources_data:
        LeadSource.objects.get_or_create(name=source_name)
    
    # Lead Status
    statuses_data = [
        ("New", "#17a2b8"),
        ("Contacted", "#ffc107"),
        ("Qualified", "#28a745"),
        ("Converted", "#6f42c1"),
        ("Lost", "#dc3545")
    ]
    for status_name, color in statuses_data:
        LeadStatus.objects.get_or_create(
            name=status_name,
            defaults={'color': color}
        )
    
    # Lead Priorities - check if model exists and what fields it has
    try:
        priorities_data = [
            ("Low", "#6c757d"),
            ("Normal", "#17a2b8"),
            ("High", "#ffc107"),
            ("Urgent", "#dc3545")
        ]
        for priority_name, color in priorities_data:
            LeadPriority.objects.get_or_create(
                name=priority_name,
                defaults={'color': color}
            )
    except Exception as e:
        print(f"Note: Could not create lead priorities: {e}")

def create_sample_properties():
    """Create sample properties"""
    print("Creating sample properties...")
    
    # Clear existing sample properties to avoid duplicates
    Property.objects.filter(property_id__startswith='PROP-').delete()
    
    # Get lookup data
    regions = list(Region.objects.all())
    property_types = list(PropertyType.objects.all())
    categories = list(PropertyCategory.objects.all())
    statuses = list(PropertyStatus.objects.all())
    compounds = list(Compound.objects.all())
    purposes = list(UnitPurpose.objects.all())
    finishing_types = list(FinishingType.objects.all())
    currencies = list(PropertyCurrency.objects.all())
    
    if not all([regions, property_types, categories, statuses, currencies]):
        print("❌ Missing lookup data for properties")
        return
    
    sample_properties = [
        {
            'name': 'Luxury Villa in Palm Hills',
            'bedrooms': 4,
            'bathrooms': 3,
            'asking_price': Decimal('5500000'),
            'total_space': Decimal('350.0'),
            'description': 'Beautiful villa with garden and private pool'
        },
        {
            'name': 'Modern Apartment in Madinaty',
            'bedrooms': 3,
            'bathrooms': 2,
            'asking_price': Decimal('2800000'),
            'total_space': Decimal('180.0'),
            'description': 'Fully furnished apartment with city view'
        },
        {
            'name': 'Commercial Office in New Capital',
            'bedrooms': 0,
            'bathrooms': 2,
            'asking_price': Decimal('4200000'),
            'total_space': Decimal('250.0'),
            'description': 'Premium office space in business district'
        },
        {
            'name': 'Studio in Zamalek',
            'bedrooms': 1,
            'bathrooms': 1,
            'asking_price': Decimal('1500000'),
            'total_space': Decimal('75.0'),
            'description': 'Cozy studio in prime location'
        },
        {
            'name': 'Penthouse in Hyde Park',
            'bedrooms': 5,
            'bathrooms': 4,
            'asking_price': Decimal('12000000'),
            'total_space': Decimal('450.0'),
            'description': 'Exclusive penthouse with panoramic views'
        }
    ]
    
    for i, prop_data in enumerate(sample_properties, 1):
        property_obj = Property.objects.create(
            property_id=f'PROP-{i:04d}',
            property_number=f'P{i:03d}',
            name=prop_data['name'],
            region=random.choice(regions),
            property_type=random.choice(property_types),
            category=random.choice(categories),
            status=random.choice(statuses),
            compound=random.choice(compounds) if compounds else None,
            unit_purpose=random.choice(purposes) if purposes else None,
            finishing_type=random.choice(finishing_types) if finishing_types else None,
            rooms=prop_data['bedrooms'],  # Map bedrooms to rooms field
            bathrooms=prop_data['bathrooms'],
            asking_price=prop_data['asking_price'],
            total_space=prop_data['total_space'],
            description=prop_data['description'],
            currency=currencies[0] if currencies else None,  # EGP
            handler_id=1,  # Admin user as handler
            sales_person_id=1  # Admin user as sales person
        )
        print(f"Created property: {property_obj.name}")

def create_sample_leads():
    """Create sample leads"""
    print("Creating sample leads...")
    
    # Temporarily disable signals to avoid audit conflicts
    from leads.signals import log_lead_changes, log_lead_deletion, capture_lead_changes
    post_save.disconnect(log_lead_changes, sender=Lead)
    post_delete.disconnect(log_lead_deletion, sender=Lead)
    pre_save.disconnect(capture_lead_changes, sender=Lead)
    
    # Clear existing sample leads to avoid duplicates
    Lead.objects.filter(mobile__startswith='+20123456789').delete()
    
    # Get lookup data
    sources = list(LeadSource.objects.all())
    statuses = list(LeadStatus.objects.all())
    priorities = list(LeadPriority.objects.all())
    
    if not all([sources, statuses, priorities]):
        print("❌ Missing lookup data for leads")
        return
    
    sample_leads = [
        {
            'name': 'Ahmed Mohamed',
            'email': 'ahmed.mohamed@email.com',
            'phone': '+201234567890',
            'budget_min': 2000000,
            'budget_max': 3000000,
            'property_preference': 'Apartment in New Cairo'
        },
        {
            'name': 'Sara Ali',
            'email': 'sara.ali@email.com',
            'phone': '+201234567891',
            'budget_min': 5000000,
            'budget_max': 8000000,
            'property_preference': 'Villa with garden'
        },
        {
            'name': 'Omar Hassan',
            'email': 'omar.hassan@email.com',
            'phone': '+201234567892',
            'budget_min': 1000000,
            'budget_max': 1500000,
            'property_preference': 'Studio or small apartment'
        },
        {
            'name': 'Fatima Nour',
            'email': 'fatima.nour@email.com',
            'phone': '+201234567893',
            'budget_min': 3000000,
            'budget_max': 5000000,
            'property_preference': 'Commercial office space'
        },
        {
            'name': 'Karim Farouk',
            'email': 'karim.farouk@email.com',
            'phone': '+201234567894',
            'budget_min': 10000000,
            'budget_max': 15000000,
            'property_preference': 'Luxury penthouse'
        }
    ]
    
    for lead_data in sample_leads:
        # Split name into first and last name
        name_parts = lead_data['name'].split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        try:
            lead_obj = Lead.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=lead_data['email'],
                mobile=lead_data['phone'],  # Use mobile instead of phone
                budget_min=lead_data['budget_min'],
                budget_max=lead_data['budget_max'],
                requirements=lead_data['property_preference'],  # Use requirements field
                source=random.choice(sources) if sources else None,  # Use source instead of lead_source
                status=random.choice(statuses) if statuses else None,
                priority=random.choice(priorities) if priorities else None,
                notes=f"Interested in {lead_data['property_preference']}",
                created_by_id=1,  # Admin user
                assigned_to_id=1  # Admin user
            )
            print(f"Created lead: {lead_obj.full_name}")
        except Exception as e:
            print(f"❌ Error creating lead {first_name} {last_name}: {e}")
            continue
    
    # Re-enable signals
    post_save.connect(log_lead_changes, sender=Lead)
    post_delete.connect(log_lead_deletion, sender=Lead)  
    pre_save.connect(capture_lead_changes, sender=Lead)

def create_sample_projects():
    """Create sample projects"""
    print("Creating sample projects...")
    
    # Clear existing sample projects to avoid duplicates
    Project.objects.filter(project_id__startswith='PROJ-').delete()
    
    # Get lookup data
    statuses = list(ProjectStatus.objects.all())
    types = list(ProjectType.objects.all())
    categories = list(ProjectCategory.objects.all())
    priorities = list(ProjectPriority.objects.all())
    currencies = list(ProjectCurrency.objects.all())
    
    if not all([statuses, types, categories, currencies]):
        print("❌ Missing lookup data for projects")
        return
    
    sample_projects = [
        {
            'name': 'Golden Tower New Capital',
            'description': 'Luxury residential tower in the New Administrative Capital',
            'total_units': 200,
            'min_price': Decimal('1800000'),
            'max_price': Decimal('6000000'),
            'start_date': datetime.now().date() - timedelta(days=180),
            'end_date': datetime.now().date() + timedelta(days=365),
            'budget': Decimal('150000000')
        },
        {
            'name': 'Marina Walk Alexandria',
            'description': 'Waterfront commercial and residential complex',
            'total_units': 350,
            'min_price': Decimal('2500000'),
            'max_price': Decimal('12000000'),
            'start_date': datetime.now().date() - timedelta(days=90),
            'end_date': datetime.now().date() + timedelta(days=545),
            'budget': Decimal('280000000')
        },
        {
            'name': 'Smart Office Park 6th October',
            'description': 'Modern office complex with smart building technology',
            'total_units': 150,
            'min_price': Decimal('3200000'),
            'max_price': Decimal('8500000'),
            'start_date': datetime.now().date() - timedelta(days=30),
            'end_date': datetime.now().date() + timedelta(days=730),
            'budget': Decimal('95000000')
        }
    ]
    
    for i, proj_data in enumerate(sample_projects, 1):
        project_obj = Project.objects.create(
            project_id=f'PROJ-{i:04d}',
            name=proj_data['name'],
            description=proj_data['description'],
            status=random.choice(statuses),
            project_type=random.choice(types),
            category=random.choice(categories),
            priority=random.choice(priorities) if priorities else None,
            total_units=proj_data['total_units'],
            min_price=proj_data['min_price'],
            max_price=proj_data['max_price'],
            start_date=proj_data['start_date'],
            end_date=proj_data['end_date'],
            price_range=f"{proj_data['min_price']:,.0f} - {proj_data['max_price']:,.0f}",
            currency=currencies[0] if currencies else None,  # EGP
            created_by_id=1,  # Admin user
            assigned_to_id=1  # Admin user
        )
        print(f"Created project: {project_obj.name}")

def setup_admin_field_permissions():
    """Setup field permissions for admin user"""
    print("Setting up admin field permissions...")
    
    admin_user = User.objects.filter(username='admin').first()
    if not admin_user:
        print("❌ Admin user not found")
        return
    
    # Get or create admin profile
    profile, created = Profile.objects.get_or_create(
        user=admin_user,
        defaults={
            'name': 'Administrator',
            'role': 'admin',
            'department': 'Management'
        }
    )
    
    # Field definitions for different modules
    field_definitions = {
        'property': {
            'Property': [
                'name', 'region', 'property_type', 'category', 'status',
                'bedrooms', 'bathrooms', 'asking_price', 'total_space',
                'description', 'compound', 'unit_purpose', 'finishing_type'
            ]
        },
        'leads': {
            'Lead': [
                'name', 'email', 'phone', 'budget_min', 'budget_max', 
                'property_preference', 'lead_source', 'status', 'priority', 'notes'
            ]
        },
        'projects': {
            'Project': [
                'name', 'description', 'status', 'project_type', 'category',
                'total_units', 'min_price', 'max_price', 'budget', 'start_date', 'end_date'
            ]
        }
    }
    
    created_count = 0
    for module in Module.objects.filter(is_active=True):
        module_name = module.name.lower()
        if module_name in field_definitions:
            for model_name, fields in field_definitions[module_name].items():
                for field_name in fields:
                    field_perm, created = FieldPermission.objects.get_or_create(
                        profile=profile,
                        module=module,
                        model_name=model_name,
                        field_name=field_name,
                        defaults={
                            'can_view': True,
                            'can_edit': True,  # Admin can edit everything
                            'is_visible_in_list': True,
                            'is_visible_in_detail': True,
                            'is_visible_in_forms': True,
                            'is_active': True
                        }
                    )
                    if created:
                        created_count += 1
    
    print(f"Created {created_count} field permissions for admin user")

def main():
    print("🎯 Creating sample data for Glomart CRM...")
    print("=" * 50)
    
    try:
        # Create lookup data
        create_property_lookup_data()
        create_lead_lookup_data()
        
        # Create sample data
        create_sample_properties()
        create_sample_leads()
        create_sample_projects()
        
        # Setup permissions
        setup_admin_field_permissions()
        
        print("\n✅ Sample data creation completed!")
        print(f"✅ Created properties, leads, and projects")
        print(f"✅ Set up admin field permissions")
        print("\n🌐 You can now access your app with data at: http://localhost:8000")
        print("🔑 Login: admin / admin123")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")

if __name__ == "__main__":
    main()