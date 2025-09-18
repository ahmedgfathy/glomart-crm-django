from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
import uuid
from datetime import datetime


class ProjectStatus(models.Model):
    """Project status lookup table"""
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#28a745')  # Bootstrap colors
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Project Status'
        verbose_name_plural = 'Project Statuses'

    def __str__(self):
        return self.display_name


class ProjectType(models.Model):
    """Project type lookup table"""
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-diagram-3')
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Project Type'
        verbose_name_plural = 'Project Types'

    def __str__(self):
        return self.display_name


class ProjectCategory(models.Model):
    """Project category lookup table"""
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Project Category'
        verbose_name_plural = 'Project Categories'

    def __str__(self):
        return self.display_name


class ProjectPriority(models.Model):
    """Project priority lookup table"""
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#ffc107')
    level = models.IntegerField(default=3)  # 1=Low, 2=Medium, 3=Normal, 4=High, 5=Critical
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['level', 'order']
        verbose_name = 'Project Priority'
        verbose_name_plural = 'Project Priorities'

    def __str__(self):
        return self.display_name


class Currency(models.Model):
    """Currency lookup table for project pricing"""
    code = models.CharField(max_length=3, unique=True)  # USD, AED, etc.
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'code']
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'

    def __str__(self):
        return f"{self.code} - {self.name}"


class Project(models.Model):
    """Main project model"""
    # Primary identification
    project_id = models.CharField(max_length=191, primary_key=True, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Location and basic info
    location = models.CharField(max_length=255, blank=True, null=True)
    developer = models.CharField(max_length=255, blank=True, null=True)
    
    # Status and categorization
    status = models.ForeignKey(ProjectStatus, on_delete=models.SET_NULL, null=True, blank=True)
    project_type = models.ForeignKey(ProjectType, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(ProjectCategory, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.ForeignKey(ProjectPriority, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Dates and timeline
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    completion_year = models.IntegerField(null=True, blank=True)
    
    # Units and capacity
    total_units = models.IntegerField(default=0, null=True, blank=True)
    available_units = models.IntegerField(default=0, null=True, blank=True)
    
    # Pricing
    price_range = models.CharField(max_length=255, blank=True, null=True)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, blank=True)
    min_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    max_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Assignment and ownership
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_projects')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')
    
    # Additional fields
    notes = models.TextField(blank=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Timestamps (matching MariaDB structure)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['project_type']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['created_by']),
            models.Index(fields=['is_active']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.name or f"Project {self.project_id[:8]}"

    def save(self, *args, **kwargs):
        if not self.project_id:
            # Generate unique project ID similar to MariaDB format
            self.project_id = f"{uuid.uuid4().hex[:12]}{datetime.now().strftime('%Y%m%d')}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('projects:project_detail', kwargs={'project_id': self.project_id})

    @property
    def units_sold(self):
        """Calculate units sold"""
        if self.total_units and self.available_units:
            return self.total_units - self.available_units
        return 0

    @property
    def completion_percentage(self):
        """Calculate completion percentage based on units sold"""
        if self.total_units and self.total_units > 0:
            return (self.units_sold / self.total_units) * 100
        return 0

    @property
    def status_color(self):
        """Get status color for display"""
        if self.status:
            return self.status.color
        return '#6c757d'  # Default gray

    @property
    def priority_color(self):
        """Get priority color for display"""
        if self.priority:
            return self.priority.color
        return '#ffc107'  # Default yellow

    @property
    def is_overdue(self):
        """Check if project is overdue"""
        if self.end_date:
            return datetime.now().date() > self.end_date.date()
        return False

    @property
    def days_remaining(self):
        """Calculate days remaining until end date"""
        if self.end_date:
            delta = self.end_date.date() - datetime.now().date()
            return delta.days
        return None

    @property
    def formatted_price_range(self):
        """Format price range for display"""
        if self.min_price and self.max_price and self.currency:
            return f"{self.currency.symbol}{self.min_price:,.0f} - {self.currency.symbol}{self.max_price:,.0f}"
        elif self.price_range:
            return self.price_range
        return "Price on request"


class ProjectHistory(models.Model):
    """Track changes to projects"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)  # created, updated, deleted, status_changed
    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Project History'
        verbose_name_plural = 'Project Histories'

    def __str__(self):
        return f"{self.project} - {self.action} by {self.user}"


class ProjectAssignment(models.Model):
    """Track project assignments to multiple users"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_assignments')
    role = models.CharField(max_length=100, default='Member')  # Project Manager, Developer, etc.
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_assignments_made')
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['project', 'user']
        ordering = ['-assigned_at']
        verbose_name = 'Project Assignment'
        verbose_name_plural = 'Project Assignments'

    def __str__(self):
        return f"{self.user} assigned to {self.project} as {self.role}"
