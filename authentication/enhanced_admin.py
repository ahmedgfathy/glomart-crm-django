from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from authentication.models import FieldPermission, DataFilter, DynamicDropdown

class ModuleFilter(SimpleListFilter):
    title = 'Module'
    parameter_name = 'module'

    def lookups(self, request, model_admin):
        from authentication.models import Module
        return [(module.id, module.display_name) for module in Module.objects.filter(is_active=True)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(module_id=self.value())
        return queryset

class ProfileFilter(SimpleListFilter):
    title = 'Profile'
    parameter_name = 'profile'

    def lookups(self, request, model_admin):
        from authentication.models import Profile
        return [(profile.id, profile.name) for profile in Profile.objects.filter(is_active=True)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(profile_id=self.value())
        return queryset

class SensitiveFieldFilter(SimpleListFilter):
    title = 'Field Sensitivity'
    parameter_name = 'sensitivity'

    def lookups(self, request, model_admin):
        return [
            ('financial', 'Financial Fields'),
            ('contact', 'Contact Information'),
            ('basic', 'Basic Fields'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            # This is a simplified filter - in production you'd map field names to categories
            sensitive_fields = {
                'financial': ['budget_min', 'budget_max', 'base_price', 'asking_price', 'sold_price', 'total_price'],
                'contact': ['mobile', 'email', 'phone', 'mobile_number', 'secondary_phone'],
                'basic': ['first_name', 'last_name', 'name', 'property_id'],
            }
            if self.value() in sensitive_fields:
                return queryset.filter(field_name__in=sensitive_fields[self.value()])
        return queryset

@admin.register(FieldPermission)
class EnhancedFieldPermissionAdmin(admin.ModelAdmin):
    list_display = [
        'get_field_display', 'profile', 'module', 'model_name', 
        'get_permissions_summary', 'get_visibility_summary', 'is_active'
    ]
    list_filter = [ModuleFilter, ProfileFilter, SensitiveFieldFilter, 'is_active', 'can_view', 'can_edit']
    search_fields = ['field_name', 'profile__name', 'module__name', 'model_name']
    ordering = ['profile', 'module', 'model_name', 'field_name']
    list_editable = ['is_active']
    list_per_page = 50
    
    # Organize fieldsets for better UX
    fieldsets = (
        ('Field Information', {
            'fields': ('profile', 'module', 'model_name', 'field_name'),
            'classes': ('wide',)
        }),
        ('Permissions', {
            'fields': ('can_view', 'can_edit', 'can_filter'),
            'classes': ('wide',)
        }),
        ('Visibility Settings', {
            'fields': ('is_visible_in_list', 'is_visible_in_detail', 'is_visible_in_forms'),
            'classes': ('wide',)
        }),
        ('Advanced', {
            'fields': ('show_condition', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def get_field_display(self, obj):
        """Display field name with module and model context"""
        return format_html(
            '<strong>{}</strong><br><small>{}.{}</small>',
            obj.field_name.replace('_', ' ').title(),
            obj.module.display_name,
            obj.model_name
        )
    get_field_display.short_description = 'Field'
    get_field_display.admin_order_field = 'field_name'
    
    def get_permissions_summary(self, obj):
        """Visual summary of permissions"""
        permissions = []
        if obj.can_view:
            permissions.append('<span style="color: green;">👁️ View</span>')
        if obj.can_edit:
            permissions.append('<span style="color: blue;">✏️ Edit</span>')
        if obj.can_filter:
            permissions.append('<span style="color: orange;">🔍 Filter</span>')
        
        return mark_safe(' '.join(permissions) if permissions else '<span style="color: red;">🚫 No Access</span>')
    get_permissions_summary.short_description = 'Permissions'
    
    def get_visibility_summary(self, obj):
        """Visual summary of visibility settings"""
        visibility = []
        if obj.is_visible_in_list:
            visibility.append('<span style="color: green;">📋 List</span>')
        if obj.is_visible_in_detail:
            visibility.append('<span style="color: blue;">📄 Detail</span>')
        if obj.is_visible_in_forms:
            visibility.append('<span style="color: purple;">📝 Forms</span>')
        
        return mark_safe(' '.join(visibility) if visibility else '<span style="color: red;">👻 Hidden</span>')
    get_visibility_summary.short_description = 'Visibility'
    
    # Custom actions for bulk operations
    actions = ['enable_view_permissions', 'disable_view_permissions', 'enable_edit_permissions', 'disable_edit_permissions']
    
    def enable_view_permissions(self, request, queryset):
        queryset.update(can_view=True, is_visible_in_list=True, is_visible_in_detail=True)
        self.message_user(request, f'Enabled view permissions for {queryset.count()} field permissions.')
    enable_view_permissions.short_description = 'Enable view permissions for selected fields'
    
    def disable_view_permissions(self, request, queryset):
        queryset.update(can_view=False, is_visible_in_list=False, is_visible_in_detail=False, is_visible_in_forms=False)
        self.message_user(request, f'Disabled view permissions for {queryset.count()} field permissions.')
    disable_view_permissions.short_description = 'Disable view permissions for selected fields'
    
    def enable_edit_permissions(self, request, queryset):
        queryset.update(can_edit=True, is_visible_in_forms=True)
        self.message_user(request, f'Enabled edit permissions for {queryset.count()} field permissions.')
    enable_edit_permissions.short_description = 'Enable edit permissions for selected fields'
    
    def disable_edit_permissions(self, request, queryset):
        queryset.update(can_edit=False)
        self.message_user(request, f'Disabled edit permissions for {queryset.count()} field permissions.')
    disable_edit_permissions.short_description = 'Disable edit permissions for selected fields'

@admin.register(DataFilter)
class EnhancedDataFilterAdmin(admin.ModelAdmin):
    list_display = [
        'get_filter_display', 'profile', 'module', 'model_name', 
        'filter_type', 'get_conditions_summary', 'is_active', 'order'
    ]
    list_filter = [ModuleFilter, ProfileFilter, 'filter_type', 'is_active']
    search_fields = ['name', 'profile__name', 'module__name', 'model_name']
    ordering = ['profile', 'module', 'order', 'name']
    list_editable = ['is_active', 'order']
    
    fieldsets = (
        ('Filter Information', {
            'fields': ('profile', 'module', 'name', 'description'),
            'classes': ('wide',)
        }),
        ('Filter Configuration', {
            'fields': ('model_name', 'filter_type', 'filter_conditions'),
            'classes': ('wide',)
        }),
        ('Settings', {
            'fields': ('order', 'is_active'),
            'classes': ('wide',)
        }),
    )
    
    def get_filter_display(self, obj):
        """Display filter name with description"""
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.name,
            obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        )
    get_filter_display.short_description = 'Filter'
    get_filter_display.admin_order_field = 'name'
    
    def get_conditions_summary(self, obj):
        """Display filter conditions in a readable format"""
        if not obj.filter_conditions:
            return mark_safe('<em>No conditions</em>')
        
        conditions = []
        for key, value in obj.filter_conditions.items():
            conditions.append(f'<code>{key}: {value}</code>')
        
        return mark_safe('<br>'.join(conditions[:3]) + ('...' if len(conditions) > 3 else ''))
    get_conditions_summary.short_description = 'Conditions'

@admin.register(DynamicDropdown)
class EnhancedDynamicDropdownAdmin(admin.ModelAdmin):
    list_display = [
        'get_dropdown_display', 'profile', 'module', 'field_name', 
        'source_model', 'get_values_summary', 'is_active'
    ]
    list_filter = [ModuleFilter, ProfileFilter, 'is_active']
    search_fields = ['name', 'field_name', 'profile__name', 'module__name']
    ordering = ['profile', 'module', 'field_name']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Dropdown Information', {
            'fields': ('profile', 'module', 'name', 'field_name'),
            'classes': ('wide',)
        }),
        ('Data Source', {
            'fields': ('source_model', 'source_field', 'display_field'),
            'classes': ('wide',)
        }),
        ('Value Restrictions', {
            'fields': ('allowed_values', 'restricted_values', 'filter_conditions'),
            'classes': ('wide',)
        }),
        ('Presentation', {
            'fields': ('is_multi_select', 'default_value', 'placeholder_text'),
            'classes': ('wide',)
        }),
        ('Settings', {
            'fields': ('order', 'is_active'),
            'classes': ('wide',)
        }),
    )
    
    def get_dropdown_display(self, obj):
        """Display dropdown name with field context"""
        return format_html(
            '<strong>{}</strong><br><small>Field: {}</small>',
            obj.name,
            obj.field_name
        )
    get_dropdown_display.short_description = 'Dropdown'
    get_dropdown_display.admin_order_field = 'name'
    
    def get_values_summary(self, obj):
        """Display allowed values summary"""
        if obj.allowed_values:
            values = obj.allowed_values[:3] if isinstance(obj.allowed_values, list) else []
            if values:
                display = ', '.join(str(v) for v in values)
                if len(obj.allowed_values) > 3:
                    display += f' (+{len(obj.allowed_values) - 3} more)'
                return format_html('<code>{}</code>', display)
        return mark_safe('<em>No restrictions</em>')
    get_values_summary.short_description = 'Allowed Values'

# Custom admin site title
admin.site.site_header = 'CRM Field Permissions Management'
admin.site.site_title = 'CRM Permissions'
admin.site.index_title = 'Granular RBAC Administration'