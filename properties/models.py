from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# Lookup Tables (Normalized)

class Region(models.Model):
    """Areas/Regions lookup table"""
    name = models.CharField(max_length=191, unique=True)
    code = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class FinishingType(models.Model):
    """Finishing types lookup table"""
    name = models.CharField(max_length=191, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class UnitPurpose(models.Model):
    """Unit purposes (unitFor) lookup table"""
    name = models.CharField(max_length=191, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class PropertyType(models.Model):
    """Property types lookup table"""
    name = models.CharField(max_length=191, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class PropertyCategory(models.Model):
    """Property categories lookup table"""
    name = models.CharField(max_length=191, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Compound(models.Model):
    """Compounds lookup table"""
    name = models.CharField(max_length=191, unique=True)
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class PropertyStatus(models.Model):
    """Property status lookup table"""
    name = models.CharField(max_length=191, unique=True)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class PropertyActivity(models.Model):
    """Property activities lookup table"""
    name = models.CharField(max_length=191, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Project(models.Model):
    """Projects lookup table"""
    name = models.CharField(max_length=191, unique=True)
    description = models.TextField(blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Currency(models.Model):
    """Currency lookup table"""
    code = models.CharField(max_length=3, unique=True)  # USD, EUR, AED
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.code} ({self.symbol})"
    
    class Meta:
        ordering = ['code']


# Main Property Model

class Property(models.Model):
    """Main Property model with all normalized relationships"""
    
    # Primary identification
    property_id = models.CharField(max_length=191, unique=True, primary_key=True)
    property_number = models.CharField(max_length=191, blank=True, null=True)
    name = models.CharField(max_length=191, blank=True, null=True)
    
    # Basic property information
    building = models.CharField(max_length=191, blank=True, null=True)
    unit_number = models.CharField(max_length=191, blank=True, null=True)
    apartment_number = models.CharField(max_length=191, blank=True, null=True)
    plot_number = models.CharField(max_length=191, blank=True, null=True)
    floor_number = models.IntegerField(blank=True, null=True)
    total_floors = models.IntegerField(blank=True, null=True)
    
    # Related lookups
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    finishing_type = models.ForeignKey(FinishingType, on_delete=models.SET_NULL, null=True, blank=True)
    unit_purpose = models.ForeignKey(UnitPurpose, on_delete=models.SET_NULL, null=True, blank=True)
    property_type = models.ForeignKey(PropertyType, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(PropertyCategory, on_delete=models.SET_NULL, null=True, blank=True)
    compound = models.ForeignKey(Compound, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.ForeignKey(PropertyStatus, on_delete=models.SET_NULL, null=True, blank=True)
    activity = models.ForeignKey(PropertyActivity, on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, blank=True, default=1)
    
    # Descriptive fields
    description = models.TextField(blank=True, null=True)
    unit_features = models.TextField(blank=True, null=True)
    phase = models.CharField(max_length=191, blank=True, null=True)
    the_floors = models.TextField(blank=True, null=True)
    in_or_outside_compound = models.CharField(max_length=191, blank=True, null=True)
    year_built = models.IntegerField(blank=True, null=True)
    
    # Room information
    rooms = models.IntegerField(blank=True, null=True)
    living_rooms = models.IntegerField(default=0)
    sales_rooms = models.IntegerField(default=0)
    bathrooms = models.IntegerField(default=0)
    
    # Area measurements
    land_area = models.CharField(max_length=191, blank=True, null=True)
    land_garden_area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sales_area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_space = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    space_earth = models.CharField(max_length=191, blank=True, null=True)
    space_unit = models.CharField(max_length=191, blank=True, null=True)
    space_guard = models.CharField(max_length=191, blank=True, null=True)
    
    # Pricing information
    base_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    asking_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    sold_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    total_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    price_per_meter = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    transfer_fees = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    maintenance_fees = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    
    # Payment information
    down_payment = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    installment = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    monthly_payment = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    payment_frequency = models.CharField(max_length=191, blank=True, null=True)  # payedEvery
    
    # Features (JSON fields for flexibility)
    facilities = models.JSONField(default=list, blank=True)
    features = models.JSONField(default=list, blank=True)
    security_features = models.JSONField(default=list, blank=True)
    
    # Boolean features
    has_garage = models.BooleanField(default=False)
    garage_type = models.CharField(max_length=191, blank=True, null=True)
    has_garden = models.BooleanField(default=False)
    garden_type = models.CharField(max_length=191, blank=True, null=True)
    has_pool = models.BooleanField(default=False)
    pool_type = models.CharField(max_length=191, blank=True, null=True)
    has_terraces = models.BooleanField(default=False)
    terrace_type = models.CharField(max_length=191, blank=True, null=True)
    
    # Status flags
    is_liked = models.BooleanField(default=False)
    is_in_home = models.BooleanField(default=False)
    update_required = models.BooleanField(default=False)
    
    # Assignment and management
    property_offered_by = models.CharField(max_length=191, blank=True, null=True)
    handler = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_properties')
    sales_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_properties')
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_users = models.ManyToManyField(User, blank=True, related_name='assigned_properties')
    
    # Contact information
    mobile_number = models.CharField(max_length=191, blank=True, null=True)
    secondary_phone = models.CharField(max_length=191, blank=True, null=True)
    telephone = models.CharField(max_length=191, blank=True, null=True)
    
    # Owner information
    owner_name = models.CharField(max_length=191, blank=True, null=True)
    owner_phone = models.CharField(max_length=191, blank=True, null=True)
    owner_email = models.EmailField(blank=True, null=True)
    owner_notes = models.TextField(blank=True, null=True)
    
    # Notes and updates
    notes = models.TextField(blank=True, null=True)
    sales_notes = models.TextField(blank=True, null=True)
    general_notes = models.TextField(blank=True, null=True)
    call_updates = models.TextField(blank=True, null=True)
    activity_notes = models.TextField(blank=True, null=True)
    call_update = models.TextField(blank=True, null=True)
    for_update = models.TextField(blank=True, null=True)
    
    # Important dates
    last_follow_up = models.DateTimeField(blank=True, null=True)
    sold_date = models.DateField(blank=True, null=True)
    rental_start_date = models.DateField(blank=True, null=True)
    rental_end_date = models.DateField(blank=True, null=True)
    rent_from = models.DateTimeField(blank=True, null=True)
    rent_to = models.DateTimeField(blank=True, null=True)
    
    # Media files (store paths as JSON for multiple files)
    primary_image = models.CharField(max_length=191, blank=True, null=True)
    thumbnail_path = models.CharField(max_length=191, blank=True, null=True)
    images = models.JSONField(default=list, blank=True)
    property_images = models.JSONField(default=list, blank=True)
    videos = models.JSONField(default=list, blank=True)
    documents = models.JSONField(default=list, blank=True)
    virtual_tour_url = models.URLField(blank=True, null=True)
    brochure_url = models.URLField(blank=True, null=True)
    
    # Foreign key IDs (for migration reference)
    property_division_id = models.CharField(max_length=191, blank=True, null=True)
    compound_location_id = models.CharField(max_length=191, blank=True, null=True)
    parcel_id = models.CharField(max_length=191, blank=True, null=True)
    finishing_level_id = models.CharField(max_length=191, blank=True, null=True)
    
    # Timestamps
    created_time = models.DateTimeField(blank=True, null=True)
    modified_time = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.property_number or self.property_id} - {self.name or 'Unnamed Property'}"
    
    @property
    def display_price(self):
        """Format price with currency"""
        if self.total_price and self.currency:
            return f"{self.currency.symbol} {self.total_price:,.0f}"
        return "Price not set"
    
    def get_image_url(self):
        """Extract the primary image URL from the JSON data"""
        import json
        
        if not self.primary_image:
            return '/static/images/property-placeholder.jpg'
        
        try:
            # If it's a JSON array with image objects
            if self.primary_image.startswith('['):
                image_array = json.loads(self.primary_image)
                if image_array and len(image_array) > 0:
                    first_image = image_array[0]
                    # Return the original cloud URL if available
                    if 'originalUrl' in first_image:
                        return first_image['originalUrl']
                    # Fallback to fileUrl if available
                    elif 'fileUrl' in first_image:
                        return first_image['fileUrl']
            # If it's just a direct URL string
            elif self.primary_image.startswith('http'):
                return self.primary_image
        except (json.JSONDecodeError, KeyError, IndexError):
            pass
        
        # Fallback to placeholder
        return '/static/images/property-placeholder.jpg'
    
    def get_all_image_urls(self):
        """Extract all image URLs from the JSON data"""
        import json
        
        if not self.primary_image:
            return ['/static/images/property-placeholder.jpg']
        
        try:
            # If it's a JSON array with image objects
            if self.primary_image.startswith('['):
                image_array = json.loads(self.primary_image)
                if image_array and len(image_array) > 0:
                    urls = []
                    for img in image_array:
                        # Return the original cloud URL if available
                        if 'originalUrl' in img:
                            urls.append(img['originalUrl'])
                        # Fallback to fileUrl if available
                        elif 'fileUrl' in img:
                            urls.append(img['fileUrl'])
                    return urls if urls else ['/static/images/property-placeholder.jpg']
            # If it's just a direct URL string
            elif self.primary_image.startswith('http'):
                return [self.primary_image]
        except (json.JSONDecodeError, KeyError, IndexError):
            pass
        
        # Fallback to placeholder
        return ['/static/images/property-placeholder.jpg']

    @property
    def total_area(self):
        """Calculate total area"""
        return self.total_space or self.sales_area or 0
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'


# Property History for tracking changes
class PropertyHistory(models.Model):
    """Track property changes"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='history')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    change_type = models.CharField(max_length=50)  # created, updated, status_changed, etc.
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.property} - {self.change_type} by {self.changed_by}"
    
    class Meta:
        ordering = ['-created_at']


class UserPropertyPreferences(models.Model):
    """Store user preferences for property list view"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='property_preferences')
    view_mode = models.CharField(
        max_length=10, 
        choices=[('grid', 'Grid View'), ('list', 'List View')], 
        default='grid'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @classmethod
    def get_for_user(cls, user):
        """Get or create preferences for user"""
        preferences, created = cls.objects.get_or_create(user=user)
        return preferences
    
    def __str__(self):
        return f"{self.user.username} - {self.view_mode} view"
    
    class Meta:
        verbose_name = 'User Property Preference'
        verbose_name_plural = 'User Property Preferences'
