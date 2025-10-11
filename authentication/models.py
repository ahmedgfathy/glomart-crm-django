from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class Module(models.Model):
    """Represents system modules like leads, property, project, etc."""
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, help_text="Bootstrap icon class")
    url_name = models.CharField(max_length=100, help_text="URL name for routing")
    order = models.IntegerField(default=0, help_text="Display order in navigation")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.display_name


class Permission(models.Model):
    """Represents permissions for each module with levels 1-4"""
    PERMISSION_LEVELS = [
        (1, 'View'),
        (2, 'Edit'),
        (3, 'Create'),
        (4, 'Delete'),
    ]
    
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='permissions')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, help_text="Permission code like 'view', 'edit', 'create', 'delete'")
    level = models.IntegerField(
        choices=PERMISSION_LEVELS,
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        help_text="Permission level: 1=View, 2=Edit, 3=Create, 4=Delete"
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['module', 'code']
        ordering = ['module', 'level']

    def __str__(self):
        return f"{self.module.display_name} - {self.get_level_display()}"


class Rule(models.Model):
    """Represents business rules that can be assigned to profiles"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    conditions = models.JSONField(default=dict, help_text="JSON field for rule conditions")
    actions = models.JSONField(default=dict, help_text="JSON field for rule actions")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    """User profiles with assigned rules and permissions"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    rules = models.ManyToManyField(Rule, blank=True, related_name='profiles')
    permissions = models.ManyToManyField(Permission, blank=True, related_name='profiles')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_module_permissions(self):
        """Get permissions grouped by module"""
        module_perms = {}
        for perm in self.permissions.filter(is_active=True).select_related('module'):
            module_name = perm.module.name
            if module_name not in module_perms:
                module_perms[module_name] = {
                    'module': perm.module,
                    'permissions': []
                }
            module_perms[module_name]['permissions'].append(perm)
        return module_perms

    def get_accessible_modules(self):
        """Get list of modules this profile can access"""
        return Module.objects.filter(
            permissions__profiles=self,
            is_active=True
        ).distinct().order_by('order', 'name')

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


class UserProfile(models.Model):
    """Extended user model with profile assignment"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    employee_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.profile.name if self.profile else 'No Profile'}"

    def has_permission(self, module_name, permission_code):
        """Check if user has specific permission for a module"""
        if not self.profile or not self.is_active:
            return False
        
        return self.profile.permissions.filter(
            module__name=module_name,
            code=permission_code,
            is_active=True
        ).exists()

    def get_max_permission_level(self, module_name):
        """Get the maximum permission level for a module (1-4)"""
        if not self.profile or not self.is_active:
            return 0
        
        max_level = self.profile.permissions.filter(
            module__name=module_name,
            is_active=True
        ).aggregate(max_level=models.Max('level'))['max_level']
        
        return max_level or 0

    def get_accessible_modules(self):
        """Get modules accessible by this user"""
        if not self.profile or not self.is_active:
            return Module.objects.none()
        
        return self.profile.get_accessible_modules()


class FieldPermission(models.Model):
    """Field-level permissions for granular access control"""
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='field_permissions')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    
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
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='data_filters')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    
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
                return queryset.filter(**self.filter_conditions)
        except Exception as e:
            import logging
            logging.error(f"DataFilter {self.id} error: {e}")
            return queryset
        
        return queryset


class DynamicDropdown(models.Model):
    """Dynamic dropdown configurations for profile-based filtering"""
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='dynamic_dropdowns')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    
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


class ProfileDataScope(models.Model):
    """Define data scope for profiles (which data they can access)"""
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='data_scopes')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    
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
            elif self.scope_type == 'filtered':
                filters = self.scope_config.get('filters', {})
                return queryset.filter(**filters)
        except Exception as e:
            import logging
            logging.error(f"ProfileDataScope {self.id} error: {e}")
            return queryset
        
        return queryset


class UserActivity(models.Model):
    """Track user activities and permissions usage"""
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('view', 'View'),
        ('create', 'Create'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('export', 'Export'),
        ('import', 'Import'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.timestamp}"
