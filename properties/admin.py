from django.contrib import admin
from .models import (
    Property, Region, FinishingType, UnitPurpose, PropertyType, 
    PropertyCategory, Compound, PropertyStatus, PropertyActivity, 
    Project, Currency, PropertyHistory
)


# Lookup table admins
@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code']
    ordering = ['name']


@admin.register(FinishingType)
class FinishingTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(UnitPurpose)
class UnitPurposeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(PropertyCategory)
class PropertyCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Compound)
class CompoundAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'location']
    ordering = ['name']


@admin.register(PropertyStatus)
class PropertyStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(PropertyActivity)
class PropertyActivityAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_active', 'created_at']
    list_filter = ['is_active', 'start_date', 'end_date', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'symbol', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name']
    ordering = ['code']


# Main Property admin
class PropertyHistoryInline(admin.TabularInline):
    model = PropertyHistory
    extra = 0
    readonly_fields = ['created_at']
    fields = ['change_type', 'changed_by', 'notes', 'created_at']


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = [
        'property_id', 'property_number', 'name', 'region', 'property_type', 
        'status', 'total_price', 'handler', 'created_at'
    ]
    list_filter = [
        'region', 'property_type', 'category', 'status', 'activity', 
        'compound', 'handler', 'created_at', 'is_liked'
    ]
    search_fields = [
        'property_id', 'property_number', 'name', 'description', 
        'mobile_number', 'notes'
    ]
    readonly_fields = ['created_at', 'updated_at', 'created_time', 'modified_time']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'property_id', 'property_number', 'name', 'description',
                'building', 'unit_number', 'apartment_number', 'plot_number'
            )
        }),
        ('Property Details', {
            'fields': (
                'region', 'property_type', 'category', 'compound', 'status',
                'activity', 'project', 'finishing_type', 'unit_purpose'
            )
        }),
        ('Physical Specifications', {
            'fields': (
                'rooms', 'living_rooms', 'sales_rooms', 'bathrooms',
                'floor_number', 'total_floors', 'year_built'
            )
        }),
        ('Area & Space', {
            'fields': (
                'land_area', 'land_garden_area', 'sales_area', 'total_space',
                'space_earth', 'space_unit', 'space_guard'
            )
        }),
        ('Pricing', {
            'fields': (
                'currency', 'base_price', 'asking_price', 'sold_price',
                'total_price', 'price_per_meter', 'transfer_fees', 'maintenance_fees'
            )
        }),
        ('Payment Terms', {
            'fields': (
                'down_payment', 'installment', 'monthly_payment', 'payment_frequency'
            )
        }),
        ('Features', {
            'fields': (
                'has_garage', 'garage_type', 'has_garden', 'garden_type',
                'has_pool', 'pool_type', 'has_terraces', 'terrace_type',
                'facilities', 'features', 'security_features'
            )
        }),
        ('Assignment & Management', {
            'fields': (
                'handler', 'sales_person', 'last_modified_by', 'assigned_users',
                'property_offered_by'
            )
        }),
        ('Contact Information', {
            'fields': (
                'mobile_number', 'secondary_phone', 'telephone'
            )
        }),
        ('Notes & Updates', {
            'fields': (
                'notes', 'sales_notes', 'general_notes', 'call_updates',
                'activity_notes', 'call_update', 'for_update'
            )
        }),
        ('Important Dates', {
            'fields': (
                'last_follow_up', 'sold_date', 'rental_start_date', 'rental_end_date',
                'rent_from', 'rent_to'
            )
        }),
        ('Media & Documents', {
            'fields': (
                'primary_image', 'thumbnail_path', 'images', 'property_images',
                'videos', 'documents', 'virtual_tour_url', 'brochure_url'
            )
        }),
        ('Status Flags', {
            'fields': (
                'is_liked', 'is_in_home', 'update_required'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_time', 'modified_time', 'created_at', 'updated_at'
            )
        }),
    )
    
    filter_horizontal = ['assigned_users']
    inlines = [PropertyHistoryInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # New property
            obj.last_modified_by = request.user
        else:  # Existing property
            obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PropertyHistory)
class PropertyHistoryAdmin(admin.ModelAdmin):
    list_display = ['property', 'change_type', 'changed_by', 'created_at']
    list_filter = ['change_type', 'changed_by', 'created_at']
    search_fields = ['property__property_id', 'property__name', 'notes']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
