from django.contrib import admin
from .models import (
    Project, ProjectStatus, ProjectType, ProjectCategory, 
    ProjectPriority, Currency, ProjectHistory, ProjectAssignment
)


@admin.register(ProjectStatus)
class ProjectStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'color', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'display_name']
    ordering = ['order', 'name']


@admin.register(ProjectType)
class ProjectTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'icon', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'display_name']
    ordering = ['order', 'name']


@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'display_name']
    ordering = ['order', 'name']


@admin.register(ProjectPriority)
class ProjectPriorityAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'level', 'color', 'is_active']
    list_filter = ['level', 'is_active']
    search_fields = ['name', 'display_name']
    ordering = ['level', 'order']


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'symbol', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['code', 'name']
    ordering = ['order', 'code']


class ProjectHistoryInline(admin.TabularInline):
    model = ProjectHistory
    extra = 0
    readonly_fields = ['created_at']
    fields = ['action', 'field_name', 'old_value', 'new_value', 'user', 'created_at']


class ProjectAssignmentInline(admin.TabularInline):
    model = ProjectAssignment
    extra = 0
    readonly_fields = ['assigned_at']
    fields = ['user', 'role', 'assigned_by', 'is_active', 'assigned_at']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        'project_id', 'name', 'status', 'project_type', 'developer', 
        'total_units', 'available_units', 'assigned_to', 'created_at'
    ]
    list_filter = [
        'status', 'project_type', 'category', 'priority', 
        'is_active', 'is_featured', 'created_at'
    ]
    search_fields = ['project_id', 'name', 'description', 'location', 'developer']
    readonly_fields = ['project_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('project_id', 'name', 'description')
        }),
        ('Location & Details', {
            'fields': ('location', 'developer')
        }),
        ('Classification', {
            'fields': ('status', 'project_type', 'category', 'priority')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'completion_year')
        }),
        ('Units & Capacity', {
            'fields': ('total_units', 'available_units')
        }),
        ('Pricing', {
            'fields': ('price_range', 'currency', 'min_price', 'max_price')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'created_by')
        }),
        ('Additional Information', {
            'fields': ('notes', 'tags', 'is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ProjectAssignmentInline, ProjectHistoryInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new project
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ProjectHistory)
class ProjectHistoryAdmin(admin.ModelAdmin):
    list_display = ['project', 'action', 'field_name', 'user', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['project__name', 'project__project_id', 'field_name']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(ProjectAssignment)
class ProjectAssignmentAdmin(admin.ModelAdmin):
    list_display = ['project', 'user', 'role', 'assigned_by', 'is_active', 'assigned_at']
    list_filter = ['role', 'is_active', 'assigned_at']
    search_fields = ['project__name', 'user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['assigned_at']
    ordering = ['-assigned_at']
