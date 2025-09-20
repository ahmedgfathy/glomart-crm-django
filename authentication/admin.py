from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Module, Permission, Rule, Profile, UserProfile, UserActivity,
    FieldPermission, DataFilter, DynamicDropdown, ProfileDataScope
)


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'icon', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name']
    ordering = ['order', 'name']
    list_editable = ['order', 'is_active']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['module', 'name', 'code', 'level', 'get_level_display', 'is_active']
    list_filter = ['module', 'level', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'module__name']
    ordering = ['module', 'level']
    list_editable = ['is_active']


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_editable = ['is_active']


class PermissionInline(admin.TabularInline):
    model = Profile.permissions.through
    extra = 0


class RuleInline(admin.TabularInline):
    model = Profile.rules.through
    extra = 0


class FieldPermissionInline(admin.TabularInline):
    model = FieldPermission
    extra = 0
    fields = ['module', 'model_name', 'field_name', 'can_view', 'can_edit', 'is_visible_in_list', 'is_active']


class DataFilterInline(admin.TabularInline):
    model = DataFilter
    extra = 0
    fields = ['module', 'name', 'model_name', 'filter_type', 'is_active']


class DynamicDropdownInline(admin.TabularInline):
    model = DynamicDropdown
    extra = 0
    fields = ['module', 'name', 'field_name', 'source_model', 'is_active']


class ProfileDataScopeInline(admin.TabularInline):
    model = ProfileDataScope
    extra = 0
    fields = ['module', 'name', 'scope_type', 'is_active']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_permissions_count', 'get_rules_count', 'get_users_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['permissions', 'rules']
    ordering = ['name']
    list_editable = ['is_active']
    inlines = [FieldPermissionInline, DataFilterInline, DynamicDropdownInline, ProfileDataScopeInline]
    
    def get_permissions_count(self, obj):
        return obj.permissions.count()
    get_permissions_count.short_description = 'Permissions'
    
    def get_rules_count(self, obj):
        return obj.rules.count()
    get_rules_count.short_description = 'Rules'
    
    def get_users_count(self, obj):
        return obj.users.count()
    get_users_count.short_description = 'Users'


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    fk_name = 'user'
    fields = ['profile', 'employee_id', 'department', 'position', 'phone', 'address', 'is_active']


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_profile', 'get_is_active', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined', 'user_profile__profile']
    
    def get_profile(self, obj):
        try:
            return obj.user_profile.profile.name if obj.user_profile.profile else 'No Profile'
        except UserProfile.DoesNotExist:
            return 'No Profile'
    get_profile.short_description = 'Profile'
    
    def get_is_active(self, obj):
        try:
            return obj.user_profile.is_active if hasattr(obj, 'user_profile') else obj.is_active
        except UserProfile.DoesNotExist:
            return obj.is_active
    get_is_active.short_description = 'Active'
    get_is_active.boolean = True


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'module', 'timestamp', 'ip_address']
    list_filter = ['activity_type', 'module', 'timestamp']
    search_fields = ['user__username', 'description']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']
    
    def has_add_permission(self, request):
        return False  # Activities are logged automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Activities are read-only


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(FieldPermission)
class FieldPermissionAdmin(admin.ModelAdmin):
    list_display = ['profile', 'module', 'model_name', 'field_name', 'can_view', 'can_edit', 'is_active']
    list_filter = ['profile', 'module', 'model_name', 'can_view', 'can_edit', 'is_active']
    search_fields = ['profile__name', 'module__name', 'model_name', 'field_name']
    ordering = ['profile', 'module', 'model_name', 'field_name']
    list_editable = ['can_view', 'can_edit', 'is_active']


@admin.register(DataFilter)
class DataFilterAdmin(admin.ModelAdmin):
    list_display = ['profile', 'module', 'name', 'model_name', 'filter_type', 'is_active']
    list_filter = ['profile', 'module', 'filter_type', 'is_active']
    search_fields = ['profile__name', 'module__name', 'name', 'model_name']
    ordering = ['profile', 'module', 'name']
    list_editable = ['is_active']


@admin.register(DynamicDropdown)
class DynamicDropdownAdmin(admin.ModelAdmin):
    list_display = ['profile', 'module', 'name', 'field_name', 'source_model', 'is_active']
    list_filter = ['profile', 'module', 'is_active']
    search_fields = ['profile__name', 'module__name', 'name', 'field_name']
    ordering = ['profile', 'module', 'name']
    list_editable = ['is_active']


@admin.register(ProfileDataScope)
class ProfileDataScopeAdmin(admin.ModelAdmin):
    list_display = ['profile', 'module', 'name', 'scope_type', 'is_active']
    list_filter = ['profile', 'module', 'scope_type', 'is_active']
    search_fields = ['profile__name', 'module__name', 'name']
    ordering = ['profile', 'module', 'scope_type']
    list_editable = ['is_active']
