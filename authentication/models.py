from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


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
