from django.core.management.base import BaseCommand
from authentication.models import (
    Module, Permission, Profile, FieldPermission, DataFilter, 
    DynamicDropdown, ProfileDataScope
)


class Command(BaseCommand):
    help = 'Initialize enhanced RBAC system with example field permissions and data filters'

    def handle(self, *args, **options):
        self.stdout.write("Setting up enhanced RBAC system...")
        
        # Ensure basic modules exist
        leads_module, _ = Module.objects.get_or_create(
            name='leads',
            defaults={
                'display_name': 'Leads',
                'icon': 'bi-person-lines-fill',
                'url_name': 'leads:leads_list',
                'order': 1
            }
        )
        
        properties_module, _ = Module.objects.get_or_create(
            name='property',
            defaults={
                'display_name': 'Properties',
                'icon': 'bi-building',
                'url_name': 'properties:property_list',
                'order': 2
            }
        )
        
        projects_module, _ = Module.objects.get_or_create(
            name='projects',
            defaults={
                'display_name': 'Projects',
                'icon': 'bi-diagram-3',
                'url_name': 'projects:project_list',
                'order': 3
            }
        )
        
        # Create example profiles with enhanced permissions
        self.create_commercial_specialist_profile(properties_module)
        self.create_residential_specialist_profile(properties_module)
        self.create_lead_manager_profile(leads_module)
        self.create_sales_representative_profile(leads_module, properties_module)
        
        self.stdout.write(self.style.SUCCESS('Enhanced RBAC system initialized successfully!'))
    
    def create_commercial_specialist_profile(self, properties_module):
        """Create a profile for commercial property specialists"""
        self.stdout.write("Creating Commercial Property Specialist profile...")
        
        # Create profile
        profile, created = Profile.objects.get_or_create(
            name='Commercial Property Specialist',
            defaults={
                'description': 'Can only view and manage commercial properties and related data'
            }
        )
        
        if created:
            # Add basic permissions
            view_perm = Permission.objects.get(module=properties_module, code='view')
            edit_perm = Permission.objects.get(module=properties_module, code='edit')
            create_perm = Permission.objects.get(module=properties_module, code='create')
            
            profile.permissions.add(view_perm, edit_perm, create_perm)
            
            # Add data filter to show only commercial properties
            DataFilter.objects.create(
                profile=profile,
                module=properties_module,
                name='Commercial Properties Only',
                description='Show only commercial, office, retail, and warehouse properties',
                model_name='Property',
                filter_type='include',
                filter_conditions={
                    'property_type__name__in': [
                        'Commercial', 'Office', 'Retail', 'Warehouse', 
                        'Shop', 'Business Center', 'Industrial'
                    ]
                }
            )
            
            # Hide residential-specific fields
            residential_fields = [
                'bedrooms', 'living_rooms', 'has_garden', 'garden_type',
                'family_area', 'children_area'
            ]
            
            for field_name in residential_fields:
                FieldPermission.objects.create(
                    profile=profile,
                    module=properties_module,
                    model_name='Property',
                    field_name=field_name,
                    can_view=False,
                    can_edit=False,
                    is_visible_in_list=False,
                    is_visible_in_detail=False,
                    is_visible_in_forms=False
                )
            
            # Create dynamic dropdown for property types (commercial only)
            DynamicDropdown.objects.create(
                profile=profile,
                module=properties_module,
                name='Commercial Property Types',
                field_name='property_type',
                source_model='PropertyType',
                source_field='name',
                display_field='name',
                allowed_values=[
                    'Commercial', 'Office', 'Retail', 'Warehouse',
                    'Shop', 'Business Center', 'Industrial'
                ]
            )
            
            self.stdout.write("✓ Commercial Property Specialist profile created")
        else:
            self.stdout.write("✓ Commercial Property Specialist profile already exists")
    
    def create_residential_specialist_profile(self, properties_module):
        """Create a profile for residential property specialists"""
        self.stdout.write("Creating Residential Property Specialist profile...")
        
        # Create profile
        profile, created = Profile.objects.get_or_create(
            name='Residential Property Specialist',
            defaults={
                'description': 'Can only view and manage residential properties'
            }
        )
        
        if created:
            # Add basic permissions
            view_perm = Permission.objects.get(module=properties_module, code='view')
            edit_perm = Permission.objects.get(module=properties_module, code='edit')
            create_perm = Permission.objects.get(module=properties_module, code='create')
            
            profile.permissions.add(view_perm, edit_perm, create_perm)
            
            # Add data filter to show only residential properties
            DataFilter.objects.create(
                profile=profile,
                module=properties_module,
                name='Residential Properties Only',
                description='Show only residential properties like apartments, villas, houses',
                model_name='Property',
                filter_type='include',
                filter_conditions={
                    'property_type__name__in': [
                        'Residential', 'Apartment', 'Villa', 'House',
                        'Flat', 'Duplex', 'Townhouse', 'Penthouse'
                    ]
                }
            )
            
            # Hide commercial-specific fields
            commercial_fields = [
                'office_area', 'conference_rooms', 'parking_spaces_commercial',
                'loading_dock', 'warehouse_area', 'retail_frontage'
            ]
            
            for field_name in commercial_fields:
                FieldPermission.objects.create(
                    profile=profile,
                    module=properties_module,
                    model_name='Property',
                    field_name=field_name,
                    can_view=False,
                    can_edit=False,
                    is_visible_in_list=False,
                    is_visible_in_detail=False,
                    is_visible_in_forms=False
                )
            
            # Create dynamic dropdown for property types (residential only)
            DynamicDropdown.objects.create(
                profile=profile,
                module=properties_module,
                name='Residential Property Types',
                field_name='property_type',
                source_model='PropertyType',
                source_field='name',
                display_field='name',
                allowed_values=[
                    'Residential', 'Apartment', 'Villa', 'House',
                    'Flat', 'Duplex', 'Townhouse', 'Penthouse'
                ]
            )
            
            self.stdout.write("✓ Residential Property Specialist profile created")
        else:
            self.stdout.write("✓ Residential Property Specialist profile already exists")
    
    def create_lead_manager_profile(self, leads_module):
        """Create a profile for lead managers with full lead access"""
        self.stdout.write("Creating Lead Manager profile...")
        
        profile, created = Profile.objects.get_or_create(
            name='Lead Manager',
            defaults={
                'description': 'Can manage all leads with full access to all lead data'
            }
        )
        
        if created:
            # Add all lead permissions
            permissions = Permission.objects.filter(module=leads_module)
            profile.permissions.add(*permissions)
            
            # Data scope: all leads
            ProfileDataScope.objects.create(
                profile=profile,
                module=leads_module,
                name='All Leads Access',
                description='Access to all leads in the system',
                scope_type='all'
            )
            
            # Show all fields
            lead_fields = [
                'first_name', 'last_name', 'mobile', 'email', 'company',
                'budget_min', 'budget_max', 'property_type', 'requirements',
                'source', 'status', 'priority', 'temperature', 'score',
                'assigned_to', 'created_by', 'notes'
            ]
            
            for field_name in lead_fields:
                FieldPermission.objects.create(
                    profile=profile,
                    module=leads_module,
                    model_name='Lead',
                    field_name=field_name,
                    can_view=True,
                    can_edit=True,
                    is_visible_in_list=True,
                    is_visible_in_detail=True,
                    is_visible_in_forms=True
                )
            
            self.stdout.write("✓ Lead Manager profile created")
        else:
            self.stdout.write("✓ Lead Manager profile already exists")
    
    def create_sales_representative_profile(self, leads_module, properties_module):
        """Create a profile for sales representatives with limited access"""
        self.stdout.write("Creating Sales Representative profile...")
        
        profile, created = Profile.objects.get_or_create(
            name='Sales Representative',
            defaults={
                'description': 'Can view assigned leads and properties, limited editing capabilities'
            }
        )
        
        if created:
            # Add limited permissions for leads
            view_leads = Permission.objects.get(module=leads_module, code='view')
            edit_leads = Permission.objects.get(module=leads_module, code='edit')
            profile.permissions.add(view_leads, edit_leads)
            
            # Add limited permissions for properties  
            view_properties = Permission.objects.get(module=properties_module, code='view')
            profile.permissions.add(view_properties)
            
            # Data scope: only assigned leads
            ProfileDataScope.objects.create(
                profile=profile,
                module=leads_module,
                name='Assigned Leads Only',
                description='Can only access leads assigned to them',
                scope_type='assigned',
                scope_config={'user_field': 'assigned_to'}
            )
            
            # Hide sensitive fields in leads
            sensitive_fields = ['score', 'budget_min', 'budget_max', 'conversion_value']
            
            for field_name in sensitive_fields:
                FieldPermission.objects.create(
                    profile=profile,
                    module=leads_module,
                    model_name='Lead',
                    field_name=field_name,
                    can_view=False,
                    can_edit=False,
                    is_visible_in_list=False,
                    is_visible_in_detail=False,
                    is_visible_in_forms=False
                )
            
            # Hide property pricing fields
            pricing_fields = ['total_price', 'sold_price', 'base_price', 'transfer_fees']
            
            for field_name in pricing_fields:
                FieldPermission.objects.create(
                    profile=profile,
                    module=properties_module,
                    model_name='Property',
                    field_name=field_name,
                    can_view=False,
                    can_edit=False,
                    is_visible_in_list=False,
                    is_visible_in_detail=False,
                    is_visible_in_forms=False
                )
            
            self.stdout.write("✓ Sales Representative profile created")
        else:
            self.stdout.write("✓ Sales Representative profile already exists")