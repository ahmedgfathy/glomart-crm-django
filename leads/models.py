from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class LeadSource(models.Model):
    """Lead source tracking (Website, Referral, Advertisement, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        permissions = [
            ("can_manage_lead_sources", "Can manage lead sources"),
        ]
    
    def __str__(self):
        return self.name


class LeadType(models.Model):
    """Lead types (Buyer, Seller, Investor, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        permissions = [
            ("can_manage_lead_types", "Can manage lead types"),
        ]
    
    def __str__(self):
        return self.name


class LeadPriority(models.Model):
    """Lead priority levels"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3b82f6')  # Hex color code
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Lead Priorities"
        permissions = [
            ("can_manage_lead_priorities", "Can manage lead priorities"),
        ]
    
    def __str__(self):
        return self.name


class LeadTemperature(models.Model):
    """Lead temperature levels (Hot, Warm, Cold)"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3b82f6')  # Hex color code
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
        permissions = [
            ("can_manage_lead_temperatures", "Can manage lead temperatures"),
        ]
    
    def __str__(self):
        return self.name


class LeadStatus(models.Model):
    """Lead status tracking (New, Contacted, Qualified, etc.)"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3b82f6')  # Hex color code
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_final = models.BooleanField(default=False)  # For Won/Lost status
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Lead Statuses"
        permissions = [
            ("can_manage_lead_statuses", "Can manage lead statuses"),
        ]
    
    def __str__(self):
        return self.name


class Lead(models.Model):
    """Main Lead model for real estate CRM - Only essential fields mandatory"""
    
    # Basic Information (MANDATORY)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)  # MANDATORY
    last_name = models.CharField(max_length=100)   # MANDATORY
    mobile = models.CharField(max_length=20)       # MANDATORY
    
    # Contact Information (OPTIONAL)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)  # Additional phone
    company = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=100, blank=True)
    
    # Lead Classification (OPTIONAL - Foreign Keys to separate tables)
    lead_type = models.ForeignKey(LeadType, on_delete=models.SET_NULL, null=True, blank=True)
    source = models.ForeignKey(LeadSource, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.ForeignKey(LeadStatus, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.ForeignKey(LeadPriority, on_delete=models.SET_NULL, null=True, blank=True)
    temperature = models.ForeignKey(LeadTemperature, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Property Interests (OPTIONAL)
    budget_min = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    preferred_locations = models.TextField(blank=True, help_text="Comma-separated list of preferred locations")
    property_type = models.CharField(max_length=100, blank=True)
    requirements = models.TextField(blank=True)
    
    # Lead Scoring and Tracking (OPTIONAL)
    score = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Lead score from 0-100"
    )
    
    # Assignment and Ownership (OPTIONAL)
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_leads'
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_leads'
    )
    
    # Communication Preferences (OPTIONAL)
    preferred_contact_method = models.CharField(
        max_length=20, 
        choices=[
            ('email', 'Email'),
            ('mobile', 'Mobile'),
            ('phone', 'Phone'),
            ('sms', 'SMS'),
            ('whatsapp', 'WhatsApp'),
        ], 
        default='mobile',
        blank=True
    )
    best_contact_time = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_contacted = models.DateTimeField(null=True, blank=True)
    next_follow_up = models.DateTimeField(null=True, blank=True)
    
    # Conversion Tracking (OPTIONAL)
    converted_at = models.DateTimeField(null=True, blank=True)
    conversion_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Additional Fields (OPTIONAL)
    notes = models.TextField(blank=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    is_qualified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['mobile']),
            models.Index(fields=['email']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['created_at']),
            models.Index(fields=['score']),
        ]
        permissions = [
            ("can_view_leads", "Can view leads"),
            ("can_add_leads", "Can add leads"),
            ("can_change_leads", "Can change leads"),
            ("can_delete_leads", "Can delete leads"),
            ("can_assign_leads", "Can assign leads"),
            ("can_convert_leads", "Can convert leads"),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.mobile})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def primary_contact(self):
        """Return the primary contact method - mobile is always available"""
        return self.mobile
    
    @property
    def budget_range(self):
        if self.budget_min and self.budget_max:
            return f"${self.budget_min:,.0f} - ${self.budget_max:,.0f}"
        elif self.budget_min:
            return f"${self.budget_min:,.0f}+"
        elif self.budget_max:
            return f"Up to ${self.budget_max:,.0f}"
        return "Not specified"
    
    @property
    def days_since_created(self):
        return (timezone.now() - self.created_at).days
    
    @property
    def days_since_last_contact(self):
        if self.last_contacted:
            return (timezone.now() - self.last_contacted).days
        return None
    
    def mark_as_contacted(self):
        """Mark lead as contacted and update timestamp"""
        self.last_contacted = timezone.now()
        self.save(update_fields=['last_contacted'])
    
    def update_score(self, new_score):
        """Update lead score with validation"""
        if 0 <= new_score <= 100:
            self.score = new_score
            self.save(update_fields=['score'])
            return True
        return False
    
    @property
    def notes_count(self):
        """Count of notes for this lead"""
        return self.lead_notes.count()
    
    @property
    def activities_count(self):
        """Count of activities for this lead"""
        return self.activities.count()
    
    @property
    def documents_count(self):
        """Count of documents for this lead"""
        return self.documents.count()


class LeadNote(models.Model):
    """Notes and comments for leads"""
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='lead_notes')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    note = models.TextField()
    is_important = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Note for {self.lead.full_name} by {self.user}"


class LeadActivity(models.Model):
    """Track all activities related to leads"""
    ACTIVITY_TYPES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('sms', 'SMS'),
        ('note', 'Note Added'),
        ('status_change', 'Status Changed'),
        ('assignment', 'Assignment Changed'),
        ('property_viewed', 'Property Viewed'),
        ('document_sent', 'Document Sent'),
        ('follow_up', 'Follow-up'),
        ('other', 'Other'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    outcome = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    
    # Related objects (optional)
    related_property_id = models.CharField(max_length=100, blank=True)
    related_document = models.CharField(max_length=500, blank=True)
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.lead.full_name}"
    
    def mark_completed(self):
        """Mark activity as completed"""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save(update_fields=['is_completed', 'completed_at'])


class LeadDocument(models.Model):
    """Documents associated with leads"""
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file_path = models.CharField(max_length=500)  # For future file upload integration
    file_type = models.CharField(max_length=50)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.lead.full_name}"


class LeadTag(models.Model):
    """Tags for lead categorization"""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#3b82f6')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class LeadAudit(models.Model):
    """Comprehensive audit trail for all lead changes"""
    
    ACTION_TYPES = [
        ('create', 'Lead Created'),
        ('update', 'Lead Updated'),
        ('delete', 'Lead Deleted'),
        ('status_change', 'Status Changed'),
        ('assignment_change', 'Assignment Changed'),
        ('priority_change', 'Priority Changed'),
        ('temperature_change', 'Temperature Changed'),
        ('contact', 'Contact Made'),
        ('note_added', 'Note Added'),
        ('document_added', 'Document Added'),
        ('activity_added', 'Activity Added'),
        ('score_change', 'Score Changed'),
        ('conversion', 'Lead Converted'),
        ('restore', 'Lead Restored'),
    ]
    
    # Core audit fields
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='audit_logs', null=True, blank=True)
    lead_id_backup = models.UUIDField(null=True, blank=True, help_text="Backup of lead ID for deleted leads")
    lead_name_backup = models.CharField(max_length=200, blank=True, help_text="Backup of lead name for deleted leads")
    
    # Action details
    action = models.CharField(max_length=30, choices=ACTION_TYPES)
    description = models.TextField(help_text="Detailed description of the change")
    
    # Field change tracking
    field_name = models.CharField(max_length=100, blank=True, help_text="Name of changed field")
    old_value = models.TextField(blank=True, help_text="Previous value (JSON format)")
    new_value = models.TextField(blank=True, help_text="New value (JSON format)")
    
    # User and system tracking
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lead_audits')
    user_name_backup = models.CharField(max_length=200, blank=True, help_text="Backup of username")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Context and metadata
    request_id = models.CharField(max_length=100, blank=True, help_text="Request tracking ID")
    session_key = models.CharField(max_length=100, blank=True)
    source = models.CharField(max_length=50, default='web', help_text="Source of change (web, api, import, etc.)")
    
    # Additional tracking
    related_object_type = models.CharField(max_length=50, blank=True, help_text="Type of related object")
    related_object_id = models.CharField(max_length=100, blank=True, help_text="ID of related object")
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Severity and categorization
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    
    # Flags
    is_sensitive = models.BooleanField(default=False, help_text="Contains sensitive information")
    is_system_generated = models.BooleanField(default=False, help_text="Generated by system automation")
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['lead', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['field_name', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['severity', 'timestamp']),
        ]
        permissions = [
            ("can_view_lead_audits", "Can view lead audit logs"),
            ("can_view_all_audits", "Can view all audit logs"),
            ("can_export_audits", "Can export audit logs"),
            ("can_manage_audits", "Can manage audit settings"),
            ("can_delete_audits", "Can delete audit logs"),
        ]
    
    def __str__(self):
        lead_name = self.lead.full_name if self.lead else self.lead_name_backup
        user_name = self.user.get_full_name() if self.user else self.user_name_backup
        return f"{self.get_action_display()} - {lead_name} by {user_name}"
    
    @property
    def lead_identifier(self):
        """Get lead identifier for display, handling deleted leads"""
        if self.lead:
            return f"{self.lead.full_name} ({self.lead.mobile})"
        return f"{self.lead_name_backup} (ID: {self.lead_id_backup})"
    
    @property
    def user_identifier(self):
        """Get user identifier for display, handling deleted users"""
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.user_name_backup or "Unknown User"
    
    @property
    def formatted_timestamp(self):
        """Human-readable timestamp"""
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    @property
    def time_since(self):
        """Time since the audit log was created"""
        delta = timezone.now() - self.timestamp
        if delta.days > 0:
            return f"{delta.days} days ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hours ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"
    
    @classmethod
    def log_action(cls, lead, action, user=None, description="", field_name="", 
                   old_value="", new_value="", ip_address=None, user_agent="", 
                   severity="medium", **kwargs):
        """
        Convenience method to log an audit action
        """
        # Backup lead info in case lead gets deleted
        lead_id_backup = str(lead.id) if lead else None
        lead_name_backup = lead.full_name if lead else ""
        
        # Backup user info in case user gets deleted
        user_name_backup = user.get_full_name() if user else ""
        
        return cls.objects.create(
            lead=lead,
            lead_id_backup=lead_id_backup,
            lead_name_backup=lead_name_backup,
            action=action,
            description=description,
            field_name=field_name,
            old_value=str(old_value) if old_value else "",
            new_value=str(new_value) if new_value else "",
            user=user,
            user_name_backup=user_name_backup,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity,
            **kwargs
        )


class UserLeadPreferences(models.Model):
    """Store user preferences for lead list column display"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lead_preferences')
    
    # Column visibility preferences (default to True for essential columns)
    show_checkbox = models.BooleanField(default=True)
    show_name = models.BooleanField(default=True)  # Always show name
    show_mobile = models.BooleanField(default=True)
    show_email = models.BooleanField(default=True)
    show_company = models.BooleanField(default=True)
    show_status = models.BooleanField(default=True)
    show_source = models.BooleanField(default=False)
    show_priority = models.BooleanField(default=False)
    show_temperature = models.BooleanField(default=False)
    show_score = models.BooleanField(default=False)
    show_assigned_to = models.BooleanField(default=True)
    show_created_at = models.BooleanField(default=False)
    show_last_contacted = models.BooleanField(default=False)
    show_budget = models.BooleanField(default=False)
    show_property_type = models.BooleanField(default=False)
    show_actions = models.BooleanField(default=True)  # Always show actions
    
    # Column order preferences (JSON field to store column order)
    column_order = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Lead Preference"
        verbose_name_plural = "User Lead Preferences"
    
    def __str__(self):
        return f"{self.user.username} - Lead Preferences"
    
    @classmethod
    def get_for_user(cls, user):
        """Get or create preferences for a user"""
        preferences, created = cls.objects.get_or_create(
            user=user,
            defaults={
                'show_name': True,
                'show_mobile': True,
                'show_email': True,
                'show_status': True,
                'show_assigned_to': True,
                'show_actions': True,
            }
        )
        return preferences
    
    def get_visible_columns(self):
        """Return list of visible column names"""
        visible_columns = []
        if self.show_checkbox:
            visible_columns.append('checkbox')
        if self.show_name:
            visible_columns.append('name')
        if self.show_mobile:
            visible_columns.append('mobile')
        if self.show_email:
            visible_columns.append('email')
        if self.show_company:
            visible_columns.append('company')
        if self.show_status:
            visible_columns.append('status')
        if self.show_source:
            visible_columns.append('source')
        if self.show_priority:
            visible_columns.append('priority')
        if self.show_temperature:
            visible_columns.append('temperature')
        if self.show_score:
            visible_columns.append('score')
        if self.show_assigned_to:
            visible_columns.append('assigned_to')
        if self.show_created_at:
            visible_columns.append('created_at')
        if self.show_last_contacted:
            visible_columns.append('last_contacted')
        if self.show_budget:
            visible_columns.append('budget')
        if self.show_property_type:
            visible_columns.append('property_type')
        if self.show_actions:
            visible_columns.append('actions')
        return visible_columns


class LeadEvent(models.Model):
    """Events/Appointments associated with leads"""
    EVENT_TYPES = [
        ('meeting', 'Meeting'),
        ('call', 'Phone Call'),
        ('site_visit', 'Site Visit'),
        ('follow_up', 'Follow Up'),
        ('presentation', 'Presentation'),
        ('negotiation', 'Negotiation'),
        ('closing', 'Closing'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
        ('no_show', 'No Show'),
    ]
    
    lead_id = models.CharField(max_length=36, db_index=True)  # UUID string to match Lead.id
    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, default='meeting')
    description = models.TextField(blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    location = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Attendees
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_events')
    attendees = models.ManyToManyField(User, blank=True, related_name='lead_events')
    
    # Reminders
    send_reminder = models.BooleanField(default=True)
    reminder_minutes_before = models.PositiveIntegerField(default=30, help_text="Minutes before event to send reminder")
    reminder_sent = models.BooleanField(default=False)
    
    # Meeting outcome (filled after completion)
    outcome_notes = models.TextField(blank=True)
    next_action = models.TextField(blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_datetime']
        permissions = [
            ("can_view_all_events", "Can view all events"),
            ("can_manage_all_events", "Can manage all events"),
        ]
        indexes = [
            models.Index(fields=['start_datetime', 'status']),
            models.Index(fields=['assigned_to', 'start_datetime']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.start_datetime.strftime('%Y-%m-%d %H:%M')})"
    
    @property
    def lead(self):
        """Get the related lead object"""
        try:
            return Lead.objects.get(id=self.lead_id)
        except Lead.DoesNotExist:
            return None
    
    @property
    def is_upcoming(self):
        return self.start_datetime > timezone.now() and self.status == 'scheduled'
    
    @property
    def is_past(self):
        return self.end_datetime < timezone.now()
    
    @property
    def duration_minutes(self):
        return int((self.end_datetime - self.start_datetime).total_seconds() / 60)

