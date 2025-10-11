from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q
from .models import (
    Lead, LeadSource, LeadType, LeadPriority, LeadTemperature, 
    LeadStatus, LeadNote, LeadActivity, LeadDocument, LeadTag, LeadAudit
)


@admin.register(LeadSource)
class LeadSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(LeadType)
class LeadTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(LeadPriority)
class LeadPriorityAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'order', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['order', 'name']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(LeadTemperature)
class LeadTemperatureAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'order', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['order', 'name']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(LeadStatus)
class LeadStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'order', 'is_active', 'is_final', 'created_by', 'created_at']
    list_filter = ['is_active', 'is_final', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['order', 'name']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class LeadNoteInline(admin.TabularInline):
    model = LeadNote
    extra = 0
    readonly_fields = ['created_at']


class LeadActivityInline(admin.TabularInline):
    model = LeadActivity
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'mobile', 'email', 'lead_type', 'status', 
        'priority', 'temperature', 'assigned_to', 'score', 'created_at'
    ]
    list_filter = [
        'lead_type', 'status', 'priority', 'temperature', 'source', 
        'assigned_to', 'is_qualified', 'created_at'
    ]
    search_fields = [
        'first_name', 'last_name', 'mobile', 'email', 'company'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at', 'days_since_created']
    
    fieldsets = (
        ('Basic Information (Required)', {
            'fields': ('first_name', 'last_name', 'mobile'),
            'description': 'Only these fields are mandatory'
        }),
        ('Contact Information (Optional)', {
            'fields': ('email', 'phone'),
            'classes': ('collapse',)
        }),
        ('Company Information (Optional)', {
            'fields': ('company', 'title'),
            'classes': ('collapse',)
        }),
        ('Lead Classification (Optional)', {
            'fields': ('lead_type', 'source', 'status', 'priority', 'temperature')
        }),
        ('Assignment & Scoring', {
            'fields': ('assigned_to', 'score', 'is_qualified')
        }),
        ('Property Interests (Optional)', {
            'fields': (
                'budget_min', 'budget_max', 'preferred_locations', 
                'property_type', 'requirements'
            ),
            'classes': ('collapse',)
        }),
        ('Communication (Optional)', {
            'fields': (
                'preferred_contact_method', 'best_contact_time', 
                'last_contacted', 'next_follow_up'
            ),
            'classes': ('collapse',)
        }),
        ('Additional Information (Optional)', {
            'fields': ('notes', 'tags'),
            'classes': ('collapse',)
        }),
        ('Conversion Tracking (Optional)', {
            'fields': ('converted_at', 'conversion_value'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [LeadNoteInline, LeadActivityInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(LeadNote)
class LeadNoteAdmin(admin.ModelAdmin):
    list_display = ['lead', 'user', 'is_important', 'created_at']
    list_filter = ['is_important', 'created_at', 'user']
    search_fields = ['lead__first_name', 'lead__last_name', 'note']


@admin.register(LeadActivity)
class LeadActivityAdmin(admin.ModelAdmin):
    list_display = ['lead', 'activity_type', 'title', 'user', 'is_completed', 'created_at']
    list_filter = ['activity_type', 'is_completed', 'created_at', 'user']
    search_fields = ['lead__first_name', 'lead__last_name', 'title', 'description']


@admin.register(LeadDocument)
class LeadDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'lead', 'file_type', 'uploaded_by', 'created_at']
    list_filter = ['file_type', 'created_at', 'uploaded_by']
    search_fields = ['title', 'lead__first_name', 'lead__last_name']


@admin.register(LeadTag)
class LeadTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'created_at']
    search_fields = ['name']


@admin.register(LeadAudit)
class LeadAuditAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'action_display', 'lead_link', 'user_display', 
        'description_short', 'severity_display', 'field_name'
    ]
    list_filter = [
        'action', 'severity', 'timestamp', 'user', 'is_sensitive', 
        'is_system_generated', 'source'
    ]
    search_fields = [
        'description', 'lead_name_backup', 'user_name_backup', 
        'field_name', 'old_value', 'new_value', 'ip_address'
    ]
    readonly_fields = [
        'id', 'lead', 'lead_id_backup', 'lead_name_backup', 'action',
        'description', 'field_name', 'old_value', 'new_value',
        'user', 'user_name_backup', 'ip_address', 'user_agent',
        'request_id', 'session_key', 'source', 'related_object_type',
        'related_object_id', 'timestamp', 'severity', 'is_sensitive',
        'is_system_generated'
    ]
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    # Custom display methods
    def action_display(self, obj):
        colors = {
            'create': 'success',
            'update': 'primary', 
            'delete': 'danger',
            'status_change': 'warning',
            'assignment_change': 'info',
            'contact': 'success',
            'conversion': 'warning'
        }
        color = colors.get(obj.action, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_action_display()
        )
    action_display.short_description = 'Action'
    
    def lead_link(self, obj):
        if obj.lead:
            url = reverse('admin:leads_lead_change', args=[obj.lead.pk])
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                url,
                obj.lead.full_name
            )
        else:
            return format_html(
                '<span class="text-muted">{} (Deleted)</span>',
                obj.lead_name_backup
            )
    lead_link.short_description = 'Lead'
    
    def user_display(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.pk])
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                url,
                obj.user.get_full_name() or obj.user.username
            )
        else:
            return format_html(
                '<span class="text-muted">{}</span>',
                obj.user_name_backup or 'Unknown'
            )
    user_display.short_description = 'User'
    
    def description_short(self, obj):
        return obj.description[:80] + '...' if len(obj.description) > 80 else obj.description
    description_short.short_description = 'Description'
    
    def severity_display(self, obj):
        colors = {
            'low': 'success',
            'medium': 'warning',
            'high': 'warning',
            'critical': 'danger'
        }
        color = colors.get(obj.severity, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_severity_display()
        )
    severity_display.short_description = 'Severity'
    
    # Custom fieldsets for better organization
    fieldsets = (
        ('Basic Information', {
            'fields': ('timestamp', 'action', 'severity', 'description')
        }),
        ('Lead Information', {
            'fields': ('lead', 'lead_id_backup', 'lead_name_backup'),
            'classes': ('collapse',)
        }),
        ('User Information', {
            'fields': ('user', 'user_name_backup', 'ip_address'),
            'classes': ('collapse',)
        }),
        ('Change Details', {
            'fields': ('field_name', 'old_value', 'new_value'),
            'classes': ('collapse',)
        }),
        ('Technical Details', {
            'fields': (
                'user_agent', 'request_id', 'session_key', 'source',
                'related_object_type', 'related_object_id'
            ),
            'classes': ('collapse',)
        }),
        ('Flags', {
            'fields': ('is_sensitive', 'is_system_generated'),
            'classes': ('collapse',)
        }),
    )
    
    # Disable add and change permissions (audit logs should be read-only)
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete audit logs
        return request.user.is_superuser
    
    # Custom actions
    actions = ['export_selected_audits', 'mark_as_sensitive']
    
    def export_selected_audits(self, request, queryset):
        # This would export selected audit logs
        self.message_user(request, f"{queryset.count()} audit logs selected for export.")
    export_selected_audits.short_description = "Export selected audit logs"
    
    def mark_as_sensitive(self, request, queryset):
        updated = queryset.update(is_sensitive=True)
        self.message_user(request, f"{updated} audit logs marked as sensitive.")
    mark_as_sensitive.short_description = "Mark as sensitive"
    
    # Custom get_queryset to optimize for performance
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'lead')
    
    # Custom filters based on user permissions
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        
        # If not superuser, only show their own audit logs
        if not request.user.is_superuser:
            queryset = queryset.filter(user=request.user)
        
        return queryset, use_distinct
