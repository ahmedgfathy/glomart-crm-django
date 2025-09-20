from django.core.management.base import BaseCommand
from authentication.models import Module, Profile, FieldPermission, DataFilter, DynamicDropdown

class Command(BaseCommand):
    help = 'Initialize granular field permissions for every field in every module'
    
    # Complete field mapping for all modules
    MODULE_FIELDS = {
        'leads': {
            'Lead': {
                # Basic Information Fields
                'first_name': {'type': 'CharField', 'required': True, 'sensitive': False, 'category': 'basic'},
                'last_name': {'type': 'CharField', 'required': True, 'sensitive': False, 'category': 'basic'},
                'mobile': {'type': 'CharField', 'required': True, 'sensitive': True, 'category': 'contact'},
                
                # Contact Information
                'email': {'type': 'EmailField', 'required': False, 'sensitive': True, 'category': 'contact'},
                'phone': {'type': 'CharField', 'required': False, 'sensitive': True, 'category': 'contact'},
                'company': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'basic'},
                'title': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'basic'},
                
                # Lead Classification (Dropdowns)
                'lead_type': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'classification', 'dropdown': 'LeadType'},
                'source': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'classification', 'dropdown': 'LeadSource'},
                'status': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'classification', 'dropdown': 'LeadStatus'},
                'priority': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'classification', 'dropdown': 'LeadPriority'},
                'temperature': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'classification', 'dropdown': 'LeadTemperature'},
                
                # Property Interests (Sensitive)
                'budget_min': {'type': 'DecimalField', 'required': False, 'sensitive': True, 'category': 'financial'},
                'budget_max': {'type': 'DecimalField', 'required': False, 'sensitive': True, 'category': 'financial'},
                'preferred_locations': {'type': 'TextField', 'required': False, 'sensitive': False, 'category': 'preferences'},
                'property_type': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'preferences'},
                'requirements': {'type': 'TextField', 'required': False, 'sensitive': False, 'category': 'preferences'},
                
                # Lead Scoring
                'score': {'type': 'IntegerField', 'required': False, 'sensitive': False, 'category': 'scoring'},
                
                # Assignment
                'assigned_to': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'assignment', 'dropdown': 'User'},
                'created_by': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'assignment', 'dropdown': 'User'},
                
                # Communication Preferences
                'preferred_contact_method': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'preferences', 'choices': True},
                'best_contact_time': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'preferences'},
                
                # Timestamps
                'created_at': {'type': 'DateTimeField', 'required': False, 'sensitive': False, 'category': 'timestamps'},
                'updated_at': {'type': 'DateTimeField', 'required': False, 'sensitive': False, 'category': 'timestamps'},
                'last_contacted': {'type': 'DateTimeField', 'required': False, 'sensitive': False, 'category': 'timestamps'},
                'next_follow_up': {'type': 'DateTimeField', 'required': False, 'sensitive': False, 'category': 'timestamps'},
                
                # Conversion Tracking (Highly Sensitive)
                'converted_at': {'type': 'DateTimeField', 'required': False, 'sensitive': True, 'category': 'conversion'},
                'conversion_value': {'type': 'DecimalField', 'required': False, 'sensitive': True, 'category': 'conversion'},
                
                # Additional Fields
                'notes': {'type': 'TextField', 'required': False, 'sensitive': False, 'category': 'additional'},
                'tags': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'additional'},
                'is_qualified': {'type': 'BooleanField', 'required': False, 'sensitive': False, 'category': 'additional'},
            }
        },
        
        'property': {
            'Property': {
                # Primary Identification
                'property_id': {'type': 'CharField', 'required': True, 'sensitive': False, 'category': 'identification'},
                'property_number': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'identification'},
                'name': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'identification'},
                
                # Basic Property Information
                'building': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'basic'},
                'unit_number': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'basic'},
                'apartment_number': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'basic'},
                'plot_number': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'basic'},
                'floor_number': {'type': 'IntegerField', 'required': False, 'sensitive': False, 'category': 'basic'},
                'total_floors': {'type': 'IntegerField', 'required': False, 'sensitive': False, 'category': 'basic'},
                
                # Related Lookups (Dropdowns)
                'region': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'location', 'dropdown': 'Region'},
                'finishing_type': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'specifications', 'dropdown': 'FinishingType'},
                'unit_purpose': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'specifications', 'dropdown': 'UnitPurpose'},
                'property_type': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'classification', 'dropdown': 'PropertyType'},
                'category': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'classification', 'dropdown': 'PropertyCategory'},
                'compound': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'location', 'dropdown': 'Compound'},
                'status': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'status', 'dropdown': 'PropertyStatus'},
                'activity': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'status', 'dropdown': 'PropertyActivity'},
                'project': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'classification', 'dropdown': 'Project'},
                'currency': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'financial', 'dropdown': 'Currency'},
                
                # Descriptive Fields
                'description': {'type': 'TextField', 'required': False, 'sensitive': False, 'category': 'description'},
                'unit_features': {'type': 'TextField', 'required': False, 'sensitive': False, 'category': 'description'},
                'phase': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'description'},
                'the_floors': {'type': 'TextField', 'required': False, 'sensitive': False, 'category': 'description'},
                'in_or_outside_compound': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'location'},
                'year_built': {'type': 'IntegerField', 'required': False, 'sensitive': False, 'category': 'specifications'},
                
                # Room Information
                'rooms': {'type': 'IntegerField', 'required': False, 'sensitive': False, 'category': 'specifications'},
                'living_rooms': {'type': 'IntegerField', 'required': False, 'sensitive': False, 'category': 'specifications'},
                'sales_rooms': {'type': 'IntegerField', 'required': False, 'sensitive': False, 'category': 'specifications'},
                'bathrooms': {'type': 'IntegerField', 'required': False, 'sensitive': False, 'category': 'specifications'},
                
                # Area Measurements
                'land_area': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'measurements'},
                'land_garden_area': {'type': 'DecimalField', 'required': False, 'sensitive': False, 'category': 'measurements'},
                'sales_area': {'type': 'DecimalField', 'required': False, 'sensitive': False, 'category': 'measurements'},
                'total_space': {'type': 'DecimalField', 'required': False, 'sensitive': False, 'category': 'measurements'},
                'space_earth': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'measurements'},
                'space_unit': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'measurements'},
                'space_guard': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'measurements'},
                
                # Pricing Information (HIGHLY SENSITIVE)
                'base_price': {'type': 'DecimalField', 'required': False, 'sensitive': True, 'category': 'financial'},
                'asking_price': {'type': 'DecimalField', 'required': False, 'sensitive': True, 'category': 'financial'},
                'sold_price': {'type': 'DecimalField', 'required': False, 'sensitive': True, 'category': 'financial'},
                'total_price': {'type': 'DecimalField', 'required': False, 'sensitive': True, 'category': 'financial'},
                'price_per_meter': {'type': 'DecimalField', 'required': False, 'sensitive': True, 'category': 'financial'},
                'transfer_fees': {'type': 'DecimalField', 'required': False, 'sensitive': True, 'category': 'financial'},
                'maintenance_fees': {'type': 'DecimalField', 'required': False, 'sensitive': True, 'category': 'financial'},
                
                # Payment Information (SENSITIVE)
                'down_payment': {'type': 'DecimalField', 'required': False, 'sensitive': True, 'category': 'payment'},
                'installment': {'type': 'DecimalField', 'required': False, 'sensitive': True, 'category': 'payment'},
                'monthly_payment': {'type': 'DecimalField', 'required': False, 'sensitive': True, 'category': 'payment'},
                'payment_frequency': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'payment'},
                
                # Features (JSON Fields)
                'facilities': {'type': 'JSONField', 'required': False, 'sensitive': False, 'category': 'features'},
                'features': {'type': 'JSONField', 'required': False, 'sensitive': False, 'category': 'features'},
                'security_features': {'type': 'JSONField', 'required': False, 'sensitive': False, 'category': 'features'},
                
                # Boolean Features
                'has_garage': {'type': 'BooleanField', 'required': False, 'sensitive': False, 'category': 'features'},
                'garage_type': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'features'},
                'has_garden': {'type': 'BooleanField', 'required': False, 'sensitive': False, 'category': 'features'},
                'garden_type': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'features'},
                'has_pool': {'type': 'BooleanField', 'required': False, 'sensitive': False, 'category': 'features'},
                'pool_type': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'features'},
                'has_terraces': {'type': 'BooleanField', 'required': False, 'sensitive': False, 'category': 'features'},
                'terrace_type': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'features'},
                
                # Status Flags
                'is_liked': {'type': 'BooleanField', 'required': False, 'sensitive': False, 'category': 'status'},
                'is_in_home': {'type': 'BooleanField', 'required': False, 'sensitive': False, 'category': 'status'},
                'update_required': {'type': 'BooleanField', 'required': False, 'sensitive': False, 'category': 'status'},
                
                # Assignment and Management
                'property_offered_by': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'assignment'},
                'handler': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'assignment', 'dropdown': 'User'},
                'sales_person': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'assignment', 'dropdown': 'User'},
                'last_modified_by': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'assignment', 'dropdown': 'User'},
                
                # Contact Information (SENSITIVE)
                'mobile_number': {'type': 'CharField', 'required': False, 'sensitive': True, 'category': 'contact'},
                'secondary_phone': {'type': 'CharField', 'required': False, 'sensitive': True, 'category': 'contact'},
                'telephone': {'type': 'CharField', 'required': False, 'sensitive': True, 'category': 'contact'},
                
                # Owner Information (HIGHLY SENSITIVE)
                'owner_name': {'type': 'CharField', 'required': False, 'sensitive': True, 'category': 'owner'},
                'owner_phone': {'type': 'CharField', 'required': False, 'sensitive': True, 'category': 'owner'},
                'owner_email': {'type': 'EmailField', 'required': False, 'sensitive': True, 'category': 'owner'},
                'owner_notes': {'type': 'TextField', 'required': False, 'sensitive': True, 'category': 'owner'},
                
                # Notes and Updates
                'notes': {'type': 'TextField', 'required': False, 'sensitive': False, 'category': 'notes'},
                'sales_notes': {'type': 'TextField', 'required': False, 'sensitive': False, 'category': 'notes'},
                'general_notes': {'type': 'TextField', 'required': False, 'sensitive': False, 'category': 'notes'},
                'call_updates': {'type': 'TextField', 'required': False, 'sensitive': False, 'category': 'notes'},
                'activity_notes': {'type': 'TextField', 'required': False, 'sensitive': False, 'category': 'notes'},
                
                # Important Dates
                'last_follow_up': {'type': 'DateTimeField', 'required': False, 'sensitive': False, 'category': 'timestamps'},
                'sold_date': {'type': 'DateField', 'required': False, 'sensitive': False, 'category': 'timestamps'},
                'rental_start_date': {'type': 'DateField', 'required': False, 'sensitive': False, 'category': 'timestamps'},
                'rental_end_date': {'type': 'DateField', 'required': False, 'sensitive': False, 'category': 'timestamps'},
                
                # Media Files
                'primary_image': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'media'},
                'images': {'type': 'JSONField', 'required': False, 'sensitive': False, 'category': 'media'},
                'videos': {'type': 'JSONField', 'required': False, 'sensitive': False, 'category': 'media'},
                'documents': {'type': 'JSONField', 'required': False, 'sensitive': False, 'category': 'media'},
                'virtual_tour_url': {'type': 'URLField', 'required': False, 'sensitive': False, 'category': 'media'},
            }
        },
        
        'projects': {
            'Project': {
                # Primary Identification
                'project_id': {'type': 'CharField', 'required': True, 'sensitive': False, 'category': 'identification'},
                'name': {'type': 'CharField', 'required': True, 'sensitive': False, 'category': 'identification'},
                'description': {'type': 'TextField', 'required': False, 'sensitive': False, 'category': 'description'},
                
                # Location and Basic Info
                'location': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'location'},
                'developer': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'basic'},
                
                # Status and Categorization
                'status': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'classification', 'dropdown': 'ProjectStatus'},
                'project_type': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'classification', 'dropdown': 'ProjectType'},
                'category': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'classification', 'dropdown': 'ProjectCategory'},
                'priority': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'classification', 'dropdown': 'ProjectPriority'},
                
                # Dates and Timeline
                'start_date': {'type': 'DateTimeField', 'required': False, 'sensitive': False, 'category': 'timeline'},
                'end_date': {'type': 'DateTimeField', 'required': False, 'sensitive': False, 'category': 'timeline'},
                'completion_year': {'type': 'IntegerField', 'required': False, 'sensitive': False, 'category': 'timeline'},
                
                # Units and Capacity
                'total_units': {'type': 'IntegerField', 'required': False, 'sensitive': False, 'category': 'capacity'},
                'available_units': {'type': 'IntegerField', 'required': False, 'sensitive': False, 'category': 'capacity'},
                
                # Pricing (SENSITIVE)
                'price_range': {'type': 'CharField', 'required': False, 'sensitive': True, 'category': 'financial'},
                'currency': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'financial', 'dropdown': 'Currency'},
                'min_price': {'type': 'DecimalField', 'required': False, 'sensitive': True, 'category': 'financial'},
                'max_price': {'type': 'DecimalField', 'required': False, 'sensitive': True, 'category': 'financial'},
                
                # Assignment and Ownership
                'assigned_to': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'assignment', 'dropdown': 'User'},
                'created_by': {'type': 'ForeignKey', 'required': False, 'sensitive': False, 'category': 'assignment', 'dropdown': 'User'},
                
                # Additional Fields
                'notes': {'type': 'TextField', 'required': False, 'sensitive': False, 'category': 'additional'},
                'tags': {'type': 'CharField', 'required': False, 'sensitive': False, 'category': 'additional'},
                'is_active': {'type': 'BooleanField', 'required': False, 'sensitive': False, 'category': 'status'},
                'is_featured': {'type': 'BooleanField', 'required': False, 'sensitive': False, 'category': 'status'},
            }
        }
    }
    
    # Profile-specific field permission templates
    PROFILE_TEMPLATES = {
        'Commercial Property Specialist': {
            'allowed_categories': ['basic', 'identification', 'location', 'specifications', 'features', 'notes', 'timeline'],
            'restricted_categories': ['owner', 'financial'],
            'restricted_sensitive_fields': True,
            'data_filters': {
                'property': {'property_type__name__in': ['Commercial', 'Mixed Use', 'Office']},
                'leads': {'property_type__icontains': 'commercial'},
            }
        },
        'Residential Property Specialist': {
            'allowed_categories': ['basic', 'identification', 'location', 'specifications', 'features', 'notes', 'timeline'],
            'restricted_categories': ['owner', 'financial'],
            'restricted_sensitive_fields': True,
            'data_filters': {
                'property': {'property_type__name__in': ['Residential', 'Apartment', 'Villa']},
                'leads': {'property_type__icontains': 'residential'},
            }
        },
        'Lead Manager': {
            'allowed_categories': ['basic', 'contact', 'classification', 'financial', 'conversion', 'assignment'],
            'restricted_categories': ['owner'],
            'restricted_sensitive_fields': False,
            'data_filters': {},
        },
        'Sales Representative': {
            'allowed_categories': ['basic', 'contact', 'classification', 'assignment'],
            'restricted_categories': ['financial', 'conversion', 'owner'],
            'restricted_sensitive_fields': True,
            'data_filters': {
                'property': {'assigned_users': 'current_user'},
                'leads': {'assigned_to': 'current_user'},
                'projects': {'assigned_to': 'current_user'},
            }
        }
    }
    
    def handle(self, *args, **options):
        self.stdout.write('Creating granular field permissions for all modules...')
        
        created_permissions = 0
        updated_permissions = 0
        
        # Process each module
        for module_name, models in self.MODULE_FIELDS.items():
            try:
                module = Module.objects.get(name=module_name)
                self.stdout.write(f'\n📦 Processing module: {module.display_name}')
                
                # Process each model in the module
                for model_name, fields in models.items():
                    self.stdout.write(f'  📋 Processing model: {model_name}')
                    
                    # Process each field in the model
                    for field_name, field_config in fields.items():
                        self.stdout.write(f'    🔧 Processing field: {field_name}')
                        
                        # Create field permissions for each profile
                        for profile_name, template in self.PROFILE_TEMPLATES.items():
                            try:
                                profile = Profile.objects.get(name=profile_name)
                                
                                # Determine if this field should be visible for this profile
                                field_category = field_config.get('category', 'basic')
                                is_sensitive = field_config.get('sensitive', False)
                                
                                # Check if field is allowed based on category
                                category_allowed = field_category in template.get('allowed_categories', [])
                                category_restricted = field_category in template.get('restricted_categories', [])
                                sensitive_restricted = is_sensitive and template.get('restricted_sensitive_fields', False)
                                
                                # Determine permissions
                                can_view = category_allowed and not category_restricted and not sensitive_restricted
                                can_edit = can_view and field_category not in ['timestamps', 'identification']
                                
                                # Create or update field permission
                                field_permission, created = FieldPermission.objects.get_or_create(
                                    profile=profile,
                                    module=module,
                                    model_name=model_name,
                                    field_name=field_name,
                                    defaults={
                                        'can_view': can_view,
                                        'can_edit': can_edit,
                                        'can_filter': can_view,
                                        'is_visible_in_list': can_view and field_category in ['basic', 'identification', 'classification'],
                                        'is_visible_in_detail': can_view,
                                        'is_visible_in_forms': can_edit,
                                        'is_active': True,
                                    }
                                )
                                
                                if created:
                                    created_permissions += 1
                                    self.stdout.write(f'      ✅ Created permission for {profile_name}')
                                else:
                                    # Update existing permission
                                    field_permission.can_view = can_view
                                    field_permission.can_edit = can_edit
                                    field_permission.can_filter = can_view
                                    field_permission.is_visible_in_list = can_view and field_category in ['basic', 'identification', 'classification']
                                    field_permission.is_visible_in_detail = can_view
                                    field_permission.is_visible_in_forms = can_edit
                                    field_permission.save()
                                    updated_permissions += 1
                                    self.stdout.write(f'      🔄 Updated permission for {profile_name}')
                                
                                # Create dropdown restrictions if field has dropdown
                                if field_config.get('dropdown'):
                                    self.create_dropdown_restrictions(
                                        profile, module, model_name, field_name, 
                                        field_config['dropdown'], template
                                    )
                                
                            except Profile.DoesNotExist:
                                self.stdout.write(
                                    self.style.WARNING(f'      ⚠️  Profile "{profile_name}" not found')
                                )
                                continue
                
            except Module.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Module "{module_name}" not found')
                )
                continue
        
        # Create data filters for each profile
        self.create_data_filters()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Completed! Created {created_permissions} new field permissions, '
                f'updated {updated_permissions} existing permissions.'
            )
        )
    
    def create_dropdown_restrictions(self, profile, module, model_name, field_name, dropdown_model, template):
        """Create dropdown value restrictions based on profile"""
        
        # Define dropdown restrictions for different profiles
        dropdown_restrictions = {
            'Commercial Property Specialist': {
                'PropertyType': ['Commercial', 'Mixed Use', 'Office', 'Retail'],
                'PropertyCategory': ['Commercial', 'Office Building', 'Retail Space'],
                'LeadType': ['Commercial Buyer', 'Commercial Investor'],
            },
            'Residential Property Specialist': {
                'PropertyType': ['Residential', 'Apartment', 'Villa', 'Townhouse'],
                'PropertyCategory': ['Residential', 'Apartment Complex', 'Single Family'],
                'LeadType': ['Residential Buyer', 'Residential Seller'],
            },
            'Lead Manager': {
                # No restrictions - can see all options
            },
            'Sales Representative': {
                # Limited options but can see most types
                'LeadStatus': ['New', 'Contacted', 'Follow-up'],  # Cannot change to Closed Won/Lost
            }
        }
        
        profile_restrictions = dropdown_restrictions.get(profile.name, {})
        if dropdown_model in profile_restrictions:
            allowed_values = profile_restrictions[dropdown_model]
            
            # Create dynamic dropdown restriction
            DynamicDropdown.objects.get_or_create(
                profile=profile,
                module=module,
                field_name=field_name,
                defaults={
                    'name': f'{field_name.title()} for {profile.name}',
                    'source_model': dropdown_model,
                    'source_field': 'name',
                    'display_field': 'name',
                    'allowed_values': allowed_values,
                    'is_active': True,
                }
            )
            self.stdout.write(f'        🎯 Created dropdown restriction for {dropdown_model}')
    
    def create_data_filters(self):
        """Create data filters for each profile"""
        self.stdout.write('\n🔍 Creating data filters...')
        
        for profile_name, template in self.PROFILE_TEMPLATES.items():
            try:
                profile = Profile.objects.get(name=profile_name)
                data_filters = template.get('data_filters', {})
                
                for module_name, filter_conditions in data_filters.items():
                    try:
                        module = Module.objects.get(name=module_name)
                        
                        # Determine model name based on module
                        model_map = {
                            'property': 'Property',
                            'leads': 'Lead',
                            'projects': 'Project'
                        }
                        model_name = model_map.get(module_name, 'Unknown')
                        
                        DataFilter.objects.get_or_create(
                            profile=profile,
                            module=module,
                            name=f'{profile_name} - {model_name} Filter',
                            defaults={
                                'description': f'Automatic data filtering for {profile_name}',
                                'model_name': model_name,
                                'filter_type': 'include',
                                'filter_conditions': filter_conditions,
                                'is_active': True,
                                'order': 1,
                            }
                        )
                        self.stdout.write(f'  ✅ Created data filter for {profile_name} - {model_name}')
                        
                    except Module.DoesNotExist:
                        continue
                        
            except Profile.DoesNotExist:
                continue
        
        self.stdout.write('🎯 Data filters creation completed!')