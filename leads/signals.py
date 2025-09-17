import json
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from threading import local
from .models import Lead, LeadAudit, LeadNote, LeadActivity, LeadDocument

# Thread-local storage for request context
_thread_locals = local()


def get_current_request():
    """Get current request from thread-local storage"""
    return getattr(_thread_locals, 'request', None)


def set_current_request(request):
    """Set current request in thread-local storage"""
    _thread_locals.request = request


def clear_current_request():
    """Clear current request from thread-local storage"""
    if hasattr(_thread_locals, 'request'):
        delattr(_thread_locals, 'request')


def get_request_info():
    """Extract useful info from current request"""
    request = get_current_request()
    if request:
        return {
            'user': getattr(request, 'user', None),
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'session_key': request.session.session_key if hasattr(request, 'session') else '',
        }
    return {
        'user': None,
        'ip_address': None,
        'user_agent': '',
        'session_key': '',
    }


@receiver(pre_save, sender=Lead)
def capture_lead_changes(sender, instance, **kwargs):
    """Capture changes before saving lead"""
    if instance.pk:  # Only for updates, not creates
        try:
            # Get the old instance
            old_instance = Lead.objects.get(pk=instance.pk)
            
            # Store old values for comparison
            instance._old_values = {
                'first_name': old_instance.first_name,
                'last_name': old_instance.last_name,
                'mobile': old_instance.mobile,
                'email': old_instance.email,
                'status': old_instance.status,
                'priority': old_instance.priority,
                'temperature': old_instance.temperature,
                'assigned_to': old_instance.assigned_to,
                'score': old_instance.score,
                'budget_min': old_instance.budget_min,
                'budget_max': old_instance.budget_max,
                'lead_type': old_instance.lead_type,
                'source': old_instance.source,
                'company': old_instance.company,
                'title': old_instance.title,
                'preferred_contact_method': old_instance.preferred_contact_method,
                'is_qualified': old_instance.is_qualified,
                'notes': old_instance.notes,
                'tags': old_instance.tags,
            }
        except Lead.DoesNotExist:
            # Lead doesn't exist yet (creation)
            instance._old_values = {}
    else:
        instance._old_values = {}


@receiver(post_save, sender=Lead)
def log_lead_changes(sender, instance, created, **kwargs):
    """Log lead creation and updates"""
    request_info = get_request_info()
    
    if created:
        # Log lead creation
        LeadAudit.log_action(
            lead=instance,
            action='create',
            user=request_info['user'],
            description=f"Lead created: {instance.full_name} ({instance.mobile})",
            ip_address=request_info['ip_address'],
            user_agent=request_info['user_agent'],
            severity='medium'
        )
    else:
        # Log field changes
        old_values = getattr(instance, '_old_values', {})
        if old_values:
            changes = []
            
            # Check each field for changes
            fields_to_check = {
                'first_name': 'First Name',
                'last_name': 'Last Name',
                'mobile': 'Mobile',
                'email': 'Email',
                'status': 'Status',
                'priority': 'Priority',
                'temperature': 'Temperature',
                'assigned_to': 'Assigned To',
                'score': 'Score',
                'budget_min': 'Minimum Budget',
                'budget_max': 'Maximum Budget',
                'lead_type': 'Lead Type',
                'source': 'Source',
                'company': 'Company',
                'title': 'Title',
                'preferred_contact_method': 'Preferred Contact Method',
                'is_qualified': 'Qualified Status',
                'notes': 'Notes',
                'tags': 'Tags',
            }
            
            for field_name, display_name in fields_to_check.items():
                old_value = old_values.get(field_name)
                new_value = getattr(instance, field_name)
                
                if old_value != new_value:
                    # Format values for display
                    old_display = str(old_value) if old_value is not None else "None"
                    new_display = str(new_value) if new_value is not None else "None"
                    
                    changes.append(f"{display_name}: {old_display} → {new_display}")
                    
                    # Log specific action types for important changes
                    action_type = 'update'
                    severity = 'medium'
                    
                    if field_name == 'status':
                        action_type = 'status_change'
                        severity = 'high'
                    elif field_name == 'assigned_to':
                        action_type = 'assignment_change'
                        severity = 'high'
                    elif field_name == 'priority':
                        action_type = 'priority_change'
                        severity = 'medium'
                    elif field_name == 'temperature':
                        action_type = 'temperature_change'
                        severity = 'medium'
                    elif field_name == 'score':
                        action_type = 'score_change'
                        severity = 'medium'
                    
                    LeadAudit.log_action(
                        lead=instance,
                        action=action_type,
                        user=request_info['user'],
                        description=f"{display_name} changed: {old_display} → {new_display}",
                        field_name=field_name,
                        old_value=old_display,
                        new_value=new_display,
                        ip_address=request_info['ip_address'],
                        user_agent=request_info['user_agent'],
                        severity=severity
                    )
            
            # Log general update if there were changes
            if changes:
                LeadAudit.log_action(
                    lead=instance,
                    action='update',
                    user=request_info['user'],
                    description=f"Lead updated: {'; '.join(changes)}",
                    ip_address=request_info['ip_address'],
                    user_agent=request_info['user_agent'],
                    severity='medium'
                )


@receiver(post_delete, sender=Lead)
def log_lead_deletion(sender, instance, **kwargs):
    """Log lead deletion"""
    request_info = get_request_info()
    
    LeadAudit.log_action(
        lead=None,  # Lead is deleted
        action='delete',
        user=request_info['user'],
        description=f"Lead deleted: {instance.full_name} ({instance.mobile})",
        lead_id_backup=str(instance.id),
        lead_name_backup=instance.full_name,
        ip_address=request_info['ip_address'],
        user_agent=request_info['user_agent'],
        severity='critical'
    )


@receiver(post_save, sender=LeadNote)
def log_note_addition(sender, instance, created, **kwargs):
    """Log when notes are added to leads"""
    if created:
        request_info = get_request_info()
        
        LeadAudit.log_action(
            lead=instance.lead,
            action='note_added',
            user=request_info['user'] or instance.user,
            description=f"Note added: {instance.note[:100]}{'...' if len(instance.note) > 100 else ''}",
            related_object_type='LeadNote',
            related_object_id=str(instance.id),
            ip_address=request_info['ip_address'],
            user_agent=request_info['user_agent'],
            severity='low' if not instance.is_important else 'medium'
        )


@receiver(post_save, sender=LeadActivity)
def log_activity_addition(sender, instance, created, **kwargs):
    """Log when activities are added to leads"""
    if created:
        request_info = get_request_info()
        
        severity = 'medium'
        if instance.activity_type in ['call', 'meeting', 'email']:
            severity = 'high'
        elif instance.activity_type == 'status_change':
            severity = 'high'
        
        LeadAudit.log_action(
            lead=instance.lead,
            action='activity_added',
            user=request_info['user'] or instance.user,
            description=f"{instance.get_activity_type_display()}: {instance.title}",
            related_object_type='LeadActivity',
            related_object_id=str(instance.id),
            ip_address=request_info['ip_address'],
            user_agent=request_info['user_agent'],
            severity=severity
        )


@receiver(post_save, sender=LeadDocument)
def log_document_addition(sender, instance, created, **kwargs):
    """Log when documents are added to leads"""
    if created:
        request_info = get_request_info()
        
        LeadAudit.log_action(
            lead=instance.lead,
            action='document_added',
            user=request_info['user'] or instance.uploaded_by,
            description=f"Document added: {instance.title} ({instance.file_type})",
            related_object_type='LeadDocument',
            related_object_id=str(instance.id),
            ip_address=request_info['ip_address'],
            user_agent=request_info['user_agent'],
            severity='medium'
        )


# Utility functions for manual logging
def log_lead_contact(lead, contact_method, user=None, notes=""):
    """Manually log contact with a lead"""
    request_info = get_request_info()
    
    LeadAudit.log_action(
        lead=lead,
        action='contact',
        user=user or request_info['user'],
        description=f"Contact made via {contact_method}. {notes}",
        field_name='last_contacted',
        new_value=timezone.now().isoformat(),
        ip_address=request_info['ip_address'],
        user_agent=request_info['user_agent'],
        severity='high'
    )
    
    # Update the lead's last_contacted field
    lead.mark_as_contacted()


def log_lead_conversion(lead, conversion_value=None, user=None, notes=""):
    """Manually log lead conversion"""
    request_info = get_request_info()
    
    description = f"Lead converted to customer"
    if conversion_value:
        description += f" (Value: ${conversion_value:,.2f})"
    if notes:
        description += f". {notes}"
    
    LeadAudit.log_action(
        lead=lead,
        action='conversion',
        user=user or request_info['user'],
        description=description,
        field_name='converted_at',
        new_value=timezone.now().isoformat(),
        ip_address=request_info['ip_address'],
        user_agent=request_info['user_agent'],
        severity='critical'
    )


def log_bulk_action(leads, action, user=None, description=""):
    """Log bulk actions on multiple leads"""
    request_info = get_request_info()
    
    for lead in leads:
        LeadAudit.log_action(
            lead=lead,
            action=action,
            user=user or request_info['user'],
            description=f"Bulk action: {description}",
            ip_address=request_info['ip_address'],
            user_agent=request_info['user_agent'],
            severity='medium',
            source='bulk_action'
        )