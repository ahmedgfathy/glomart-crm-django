# Enhanced RBAC Models for Granular Permissions
# Add to authentication/models.py

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class FieldPermission(models.Model):
    """Field-level permissions for granular access control"""
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='field_permissions')
    module = models.ForeignKey('Module', on_delete=models.CASCADE)
    
    # Field identification
    model_name = models.CharField(max_length=100, help_text="Model name (e.g., 'Lead', 'Property')")
    field_name = models.CharField(max_length=100, help_text="Field name (e.g., 'budget_max', 'property_type')")
    
    # Permission levels for this specific field
    can_view = models.BooleanField(default=True)
    can_edit = models.BooleanField(default=False)
    can_filter = models.BooleanField(default=True, help_text="Can use this field for filtering data")
    
    # Field display settings
    is_visible_in_list = models.BooleanField(default=True, help_text="Show in list views")
    is_visible_in_detail = models.BooleanField(default=True, help_text="Show in detail views")
    is_visible_in_forms = models.BooleanField(default=True, help_text="Show in create/edit forms")
    
    # Conditional visibility
    show_condition = models.JSONField(default=dict, blank=True, help_text="JSON conditions for when to show field")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['profile', 'module', 'model_name', 'field_name']
        ordering = ['module', 'model_name', 'field_name']
    
    def __str__(self):
        return f"{self.profile.name} - {self.module.display_name}.{self.model_name}.{self.field_name}"


class DataFilter(models.Model):
    """Data filtering rules for profile-based data access"""
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='data_filters')
    module = models.ForeignKey('Module', on_delete=models.CASCADE)
    
    # Filter identification
    name = models.CharField(max_length=100, help_text="Filter name (e.g., 'Commercial Properties Only')")
    description = models.TextField(blank=True)
    model_name = models.CharField(max_length=100, help_text="Model to filter (e.g., 'Property', 'Lead')")
    
    # Filter configuration
    filter_type = models.CharField(max_length=50, choices=[
        ('include', 'Include Only'),
        ('exclude', 'Exclude'),
        ('conditional', 'Conditional'),
    ], default='include')
    
    # Filter conditions (JSON format for flexibility)
    filter_conditions = models.JSONField(default=dict, help_text="JSON filter conditions")
    
    # Examples of filter_conditions:
    # {"property_type__name__in": ["Commercial", "Office"]}
    # {"category__name": "Residential"}
    # {"budget_min__gte": 100000, "budget_max__lte": 500000}
    
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Application order (lower numbers first)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['module', 'order', 'name']
    
    def __str__(self):
        return f"{self.profile.name} - {self.name}"
    
    def apply_filter(self, queryset):
        """Apply this filter to a queryset"""
        if not self.is_active or not self.filter_conditions:
            return queryset
        
        try:
            if self.filter_type == 'include':
                return queryset.filter(**self.filter_conditions)
            elif self.filter_type == 'exclude':
                return queryset.exclude(**self.filter_conditions)
            elif self.filter_type == 'conditional':
                # More complex conditional logic can be implemented here
                return queryset.filter(**self.filter_conditions)
        except Exception as e:
            # Log error and return original queryset
            import logging
            logging.error(f"DataFilter {self.id} error: {e}")
            return queryset
        
        return queryset


class AttributeRule(models.Model):
    """Rules for attribute-level access and modification"""
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='attribute_rules')
    module = models.ForeignKey('Module', on_delete=models.CASCADE)
    
    # Rule identification
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Target specification
    model_name = models.CharField(max_length=100)
    attribute_name = models.CharField(max_length=100)
    
    # Rule type
    rule_type = models.CharField(max_length=50, choices=[
        ('read_only', 'Read Only'),
        ('hidden', 'Hidden'),
        ('required', 'Required'),
        ('computed', 'Computed'),
        ('dropdown_filter', 'Dropdown Filter'),
        ('value_restriction', 'Value Restriction'),
    ])
    
    # Rule configuration
    rule_config = models.JSONField(default=dict, help_text="JSON configuration for the rule")
    
    # Examples of rule_config:
    # For dropdown_filter: {"allowed_values": ["Commercial", "Office"], "source": "property_type"}
    # For value_restriction: {"min_value": 0, "max_value": 1000000}
    # For computed: {"formula": "budget_max - budget_min", "depends_on": ["budget_max", "budget_min"]}
    
    # Conditions for when rule applies
    apply_conditions = models.JSONField(default=dict, blank=True, help_text="When to apply this rule")
    
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['profile', 'module', 'model_name', 'attribute_name', 'rule_type']
        ordering = ['module', 'model_name', 'order']
    
    def __str__(self):
        return f"{self.profile.name} - {self.name} ({self.get_rule_type_display()})"


class DynamicDropdown(models.Model):
    """Dynamic dropdown configurations for profile-based filtering"""
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='dynamic_dropdowns')
    module = models.ForeignKey('Module', on_delete=models.CASCADE)
    
    # Dropdown identification
    name = models.CharField(max_length=100, help_text="Dropdown name (e.g., 'Property Types', 'Lead Sources')")
    field_name = models.CharField(max_length=100, help_text="Field this dropdown is for")
    
    # Data source configuration
    source_model = models.CharField(max_length=100, help_text="Source model for dropdown options")
    source_field = models.CharField(max_length=100, help_text="Field to use for option values")
    display_field = models.CharField(max_length=100, help_text="Field to use for option labels")
    
    # Filtering and restrictions
    allowed_values = models.JSONField(default=list, help_text="List of allowed values")
    restricted_values = models.JSONField(default=list, help_text="List of restricted values")
    
    # Additional filters
    filter_conditions = models.JSONField(default=dict, help_text="Additional filter conditions")
    
    # Presentation options
    is_multi_select = models.BooleanField(default=False)
    default_value = models.CharField(max_length=100, blank=True)
    placeholder_text = models.CharField(max_length=100, blank=True)
    
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['profile', 'module', 'field_name']
        ordering = ['module', 'order', 'name']
    
    def __str__(self):
        return f"{self.profile.name} - {self.name}"
    
    def get_options(self):
        """Get filtered dropdown options for this profile"""
        try:
            # Import the model dynamically
            from django.apps import apps
            model_class = apps.get_model(app_label=self.module.name, model_name=self.source_model)
            
            # Build queryset
            queryset = model_class.objects.all()
            
            # Apply filter conditions
            if self.filter_conditions:
                queryset = queryset.filter(**self.filter_conditions)
            
            # Apply allowed/restricted values
            if self.allowed_values:
                queryset = queryset.filter(**{f"{self.source_field}__in": self.allowed_values})
            
            if self.restricted_values:
                queryset = queryset.exclude(**{f"{self.source_field}__in": self.restricted_values})
            
            # Get options
            options = []
            for item in queryset:
                value = getattr(item, self.source_field)
                label = getattr(item, self.display_field)
                options.append({'value': value, 'label': label})
            
            return options
            
        except Exception as e:
            import logging
            logging.error(f"DynamicDropdown {self.id} error: {e}")
            return []


class ProfileDataScope(models.Model):
    """Define data scope for profiles (which data they can access)"""
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='data_scopes')
    module = models.ForeignKey('Module', on_delete=models.CASCADE)
    
    # Scope identification
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Scope type
    scope_type = models.CharField(max_length=50, choices=[
        ('all', 'All Data'),
        ('own', 'Own Data Only'),
        ('assigned', 'Assigned Data'),
        ('team', 'Team Data'),
        ('filtered', 'Filtered Data'),
        ('custom', 'Custom Query'),
    ])
    
    # Scope configuration
    scope_config = models.JSONField(default=dict, help_text="Configuration for data scope")
    
    # Examples of scope_config:
    # For 'own': {"user_field": "created_by"}
    # For 'assigned': {"user_field": "assigned_to"}
    # For 'team': {"team_field": "department", "user_attribute": "user_profile.department"}
    # For 'filtered': {"filters": {"status__name": "Active", "category": "Premium"}}
    
    # Query building
    custom_query = models.TextField(blank=True, help_text="Custom Django ORM query")
    
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['profile', 'module', 'scope_type']
        ordering = ['module', 'order']
    
    def __str__(self):
        return f"{self.profile.name} - {self.name} ({self.get_scope_type_display()})"
    
    def apply_scope(self, queryset, user):
        """Apply data scope to queryset for given user"""
        if not self.is_active:
            return queryset
        
        try:
            if self.scope_type == 'all':
                return queryset
            
            elif self.scope_type == 'own':
                user_field = self.scope_config.get('user_field', 'created_by')
                return queryset.filter(**{user_field: user})
            
            elif self.scope_type == 'assigned':
                user_field = self.scope_config.get('user_field', 'assigned_to')
                return queryset.filter(**{user_field: user})
            
            elif self.scope_type == 'team':
                team_field = self.scope_config.get('team_field')
                user_attribute = self.scope_config.get('user_attribute')
                if team_field and user_attribute:
                    # Get user's team value
                    user_value = user
                    for attr in user_attribute.split('.'):
                        user_value = getattr(user_value, attr, None)
                        if user_value is None:
                            break
                    
                    if user_value:
                        return queryset.filter(**{team_field: user_value})
            
            elif self.scope_type == 'filtered':
                filters = self.scope_config.get('filters', {})
                return queryset.filter(**filters)
            
            elif self.scope_type == 'custom':
                # Execute custom query logic here
                # This would need careful implementation for security
                pass
                
        except Exception as e:
            import logging
            logging.error(f"ProfileDataScope {self.id} error: {e}")
            return queryset
        
        return queryset


# Update the existing Profile model to include enhanced functionality
class ProfileEnhanced(models.Model):
    """Enhanced profile functionality - these methods would be added to existing Profile model"""
    
    def get_field_permissions(self, module_name, model_name):
        """Get field permissions for a specific module and model"""
        return self.field_permissions.filter(
            module__name=module_name,
            model_name=model_name,
            is_active=True
        )
    
    def can_view_field(self, module_name, model_name, field_name):
        """Check if profile can view a specific field"""
        try:
            field_perm = self.field_permissions.get(
                module__name=module_name,
                model_name=model_name,
                field_name=field_name,
                is_active=True
            )
            return field_perm.can_view
        except FieldPermission.DoesNotExist:
            return True  # Default to visible if no specific permission
    
    def can_edit_field(self, module_name, model_name, field_name):
        """Check if profile can edit a specific field"""
        try:
            field_perm = self.field_permissions.get(
                module__name=module_name,
                model_name=model_name,
                field_name=field_name,
                is_active=True
            )
            return field_perm.can_edit
        except FieldPermission.DoesNotExist:
            return True  # Default to editable if no specific permission
    
    def get_visible_fields(self, module_name, model_name, view_type='list'):
        """Get list of visible fields for a view type"""
        field_attr = f'is_visible_in_{view_type}'
        
        field_permissions = self.field_permissions.filter(
            module__name=module_name,
            model_name=model_name,
            is_active=True
        )
        
        visible_fields = []
        for field_perm in field_permissions:
            if getattr(field_perm, field_attr, True):
                visible_fields.append(field_perm.field_name)
        
        return visible_fields
    
    def apply_data_filters(self, queryset, module_name, model_name):
        """Apply all active data filters for this profile"""
        filters = self.data_filters.filter(
            module__name=module_name,
            model_name=model_name,
            is_active=True
        ).order_by('order')
        
        for data_filter in filters:
            queryset = data_filter.apply_filter(queryset)
        
        return queryset
    
    def apply_data_scope(self, queryset, module_name, user):
        """Apply data scope restrictions for this profile"""
        try:
            scope = self.data_scopes.get(
                module__name=module_name,
                is_active=True
            )
            return scope.apply_scope(queryset, user)
        except ProfileDataScope.DoesNotExist:
            return queryset  # No scope restrictions
    
    def get_dropdown_options(self, module_name, field_name):
        """Get dropdown options for a specific field"""
        try:
            dropdown = self.dynamic_dropdowns.get(
                module__name=module_name,
                field_name=field_name,
                is_active=True
            )
            return dropdown.get_options()
        except DynamicDropdown.DoesNotExist:
            return []