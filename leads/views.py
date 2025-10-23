from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime, timedelta

from .models import (
    Lead, LeadSource, LeadStatus, LeadNote, 
    LeadActivity, LeadDocument, LeadTag,
    LeadType, LeadPriority, LeadTemperature,
    UserLeadPreferences, LeadEvent
)
from authentication.models import Module, Permission, DataFilter


def apply_user_data_filters(user, queryset, model_name):
    """Apply user profile data filters to a queryset"""
    if not hasattr(user, 'user_profile') or not user.user_profile.profile:
        return queryset
    
    profile = user.user_profile.profile
    
    # Get data filters for this profile and model
    try:
        module = Module.objects.get(name='leads')
        filters = DataFilter.objects.filter(
            profile=profile,
            module=module,
            model_name=model_name,
            is_active=True
        )
        
        if filters.exists():
            # If there are multiple filters, we need to combine them properly
            # For data access filters, we typically want to show records that match ANY of the filters (OR logic)
            from django.db.models import Q
            combined_filter = Q()
            
            for data_filter in filters:
                if data_filter.filter_conditions:
                    try:
                        # Add each filter with OR logic
                        combined_filter |= Q(**data_filter.filter_conditions)
                    except Exception as e:
                        # Log the error but don't break the view
                        print(f"Error processing filter {data_filter.name}: {e}")
                        continue
            
            # Apply the combined filter
            if combined_filter:
                queryset = queryset.filter(combined_filter)
                    
    except Module.DoesNotExist:
        pass
    
    return queryset


def has_lead_permission(user, permission_level):
    """Check if user has specific permission level for leads module"""
    if user.is_superuser:
        return True
    
    try:
        user_profile = user.user_profile
        leads_module = Module.objects.get(name='leads')
        
        # Get user permissions for leads module
        permissions = user_profile.profile.permissions.filter(
            module=leads_module,
            level__gte=permission_level,
            is_active=True
        )
        return permissions.exists()
    except:
        return False


def permission_required(level):
    """Decorator to check lead permissions"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('authentication:login')
            
            if not has_lead_permission(request.user, level):
                messages.error(request, 'Access denied. Insufficient permissions.')
                return redirect('authentication:dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


@login_required
@permission_required(1)  # View permission
def leads_list_view(request):
    """Display paginated list of leads with filtering and search"""
    # Get base leads queryset
    leads = Lead.objects.select_related('status', 'source', 'assigned_to', 'lead_type', 'priority', 'temperature').all()
    
    # Apply user profile data filters first
    leads = apply_user_data_filters(request.user, leads, 'Lead')
    
    # Restrict leads based on user permissions (if not superuser)
    if not request.user.is_superuser:
        # Check if user has manager-level access through profile
        if hasattr(request.user, 'user_profile') and request.user.user_profile.profile:
            profile = request.user.user_profile.profile
            # If profile name contains 'manager' or 'supervisor', allow seeing all filtered leads
            if 'manager' not in profile.name.lower() and 'supervisor' not in profile.name.lower():
                # Regular users can only see leads assigned to them
                leads = leads.filter(assigned_to=request.user)
        else:
            # No profile - restrict to assigned leads only
            leads = leads.filter(assigned_to=request.user)
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        leads = leads.filter(status_id=status_filter)
    
    source_filter = request.GET.get('source')
    if source_filter:
        leads = leads.filter(source_id=source_filter)
    
    assigned_filter = request.GET.get('assigned')
    if assigned_filter == 'me':
        leads = leads.filter(assigned_to=request.user)
    elif assigned_filter == 'unassigned':
        leads = leads.filter(assigned_to__isnull=True)
    elif assigned_filter and assigned_filter.isdigit():
        leads = leads.filter(assigned_to_id=assigned_filter)
    
    priority_filter = request.GET.get('priority')
    if priority_filter:
        leads = leads.filter(priority_id=priority_filter)
    
    lead_type_filter = request.GET.get('lead_type')
    if lead_type_filter:
        leads = leads.filter(lead_type_id=lead_type_filter)
    
    temperature_filter = request.GET.get('temperature')
    if temperature_filter:
        leads = leads.filter(temperature_id=temperature_filter)
    
    # Search functionality - Enhanced for better partial matching
    search_query = request.GET.get('search', '').strip()
    if search_query:
        # Split search query into words for better matching
        search_words = search_query.split()
        search_filter = Q()
        
        for word in search_words:
            word_filter = (
                Q(first_name__icontains=word) |
                Q(last_name__icontains=word) |
                Q(email__icontains=word) |
                Q(phone__icontains=word) |
                Q(mobile__icontains=word) |
                Q(company__icontains=word) |
                Q(title__icontains=word) |
                Q(preferred_locations__icontains=word) |
                Q(property_type__icontains=word) |
                Q(requirements__icontains=word) |
                Q(notes__icontains=word)
            )
            search_filter &= word_filter
        
        # Also search for the complete query
        complete_filter = (
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(mobile__icontains=search_query) |
            Q(company__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(preferred_locations__icontains=search_query) |
            Q(property_type__icontains=search_query) |
            Q(requirements__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
        
        # Combine both filters with OR
        leads = leads.filter(search_filter | complete_filter)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    leads = leads.order_by(sort_by)
    
    # Pagination - handle per_page parameter
    per_page = request.GET.get('per_page', 25)
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 25
    except (ValueError, TypeError):
        per_page = 25
    
    paginator = Paginator(leads, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    statuses = LeadStatus.objects.filter(is_active=True)
    sources = LeadSource.objects.filter(is_active=True)
    
    # Users dropdown - superusers see all, regular users only see themselves
    if request.user.is_superuser:
        users = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    else:
        users = User.objects.filter(id=request.user.id)  # Only current user
    
    lead_types = LeadType.objects.filter(is_active=True)
    priorities = LeadPriority.objects.filter(is_active=True).order_by('order')
    temperatures = LeadTemperature.objects.filter(is_active=True).order_by('order')
    
    # Statistics - User-specific for non-superusers
    if request.user.is_superuser:
        total_leads = Lead.objects.count()
        qualified_leads = Lead.objects.filter(is_qualified=True).count()
        unassigned_leads = Lead.objects.filter(assigned_to__isnull=True).count()
    else:
        # Regular users see only their assigned leads statistics
        user_leads = Lead.objects.filter(assigned_to=request.user)
        total_leads = user_leads.count()
        qualified_leads = user_leads.filter(is_qualified=True).count()
        unassigned_leads = 0  # User can't see unassigned leads
    
    # Get user column preferences
    user_preferences = UserLeadPreferences.get_for_user(request.user)
    
    context = {
        'page_obj': page_obj,
        'leads': page_obj.object_list,
        'statuses': statuses,
        'sources': sources,
        'users': users,
        'lead_types': lead_types,
        'priorities': priorities,
        'temperatures': temperatures,
        'total_leads': total_leads,
        'qualified_leads': qualified_leads,
        'unassigned_leads': unassigned_leads,
        'user_preferences': user_preferences,
        'visible_columns': user_preferences.get_visible_columns(),
        'filters': {
            'status': status_filter,
            'source': source_filter,
            'assigned': assigned_filter,
            'priority': priority_filter,
            'lead_type': lead_type_filter,
            'temperature': temperature_filter,
            'search': search_query,
            'sort': sort_by,
        },
        'can_create': has_lead_permission(request.user, 3),
        'can_edit': has_lead_permission(request.user, 2),
        'can_delete': has_lead_permission(request.user, 4),
    }
    
    return render(request, 'leads/leads_list.html', context)


@login_required
@permission_required(1)  # View permission
def leads_dashboard_view(request):
    """Lead analytics dashboard"""
    # Time periods
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Basic stats
    total_leads = Lead.objects.count()
    new_leads_week = Lead.objects.filter(created_at__date__gte=week_ago).count()
    qualified_leads = Lead.objects.filter(is_qualified=True).count()
    converted_leads = Lead.objects.filter(converted_at__isnull=False).count()
    pending_leads = total_leads - converted_leads
    
    # Conversion rate
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
    
    # Pipeline stages (statuses)
    pipeline_stages = LeadStatus.objects.annotate(
        count=Count('lead')
    ).filter(is_active=True).order_by('order')
    
    # Lead sources with counts
    lead_sources = LeadSource.objects.annotate(
        count=Count('lead')
    ).filter(is_active=True, count__gt=0).order_by('-count')[:6]
    
    # Add colors for chart
    colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']
    for i, source in enumerate(lead_sources):
        source.color = colors[i % len(colors)]
    
    # Recent activities
    recent_activities = LeadActivity.objects.select_related(
        'lead', 'user'
    ).order_by('-created_at')[:10]
    
    # Hot leads
    hot_leads = Lead.objects.filter(
        temperature='hot'
    ).select_related('status').order_by('-score', '-created_at')[:5]
    
    # Performance metrics (mock data for now)
    avg_response_time = 4.2
    avg_deal_size = "125K"
    follow_up_rate = 85
    lead_velocity = 12
    
    # Goals (mock data for now)
    new_leads_goal = {
        'current': new_leads_week * 4,  # Estimate monthly from weekly
        'target': 100,
        'percentage': min(100, (new_leads_week * 4 / 100) * 100)
    }
    
    conversions_goal = {
        'current': converted_leads,
        'target': 25,
        'percentage': min(100, (converted_leads / 25) * 100)
    }
    
    revenue_goal = {
        'current': 180,
        'target': 500,
        'percentage': 36
    }
    
    # Temperature counts
    hot_count = Lead.objects.filter(temperature='hot').count()
    warm_count = Lead.objects.filter(temperature='warm').count()
    cold_count = Lead.objects.filter(temperature='cold').count()
    
    # Priority counts
    high_priority_count = Lead.objects.filter(priority='high').count()
    medium_priority_count = Lead.objects.filter(priority='medium').count()
    low_priority_count = Lead.objects.filter(priority='low').count()
    
    # Status counts for quick filters
    statuses_with_counts = LeadStatus.objects.annotate(
        count=Count('lead')
    ).filter(is_active=True)
    
    context = {
        'total_leads': total_leads,
        'new_leads_week': new_leads_week,
        'qualified_leads': qualified_leads,
        'converted_leads': converted_leads,
        'pending_leads': pending_leads,
        'conversion_rate': round(conversion_rate, 1),
        'pipeline_stages': pipeline_stages,
        'lead_sources': lead_sources,
        'recent_activities': recent_activities,
        'hot_leads': hot_leads,
        'avg_response_time': avg_response_time,
        'avg_deal_size': avg_deal_size,
        'follow_up_rate': follow_up_rate,
        'lead_velocity': lead_velocity,
        'new_leads_goal': new_leads_goal,
        'conversions_goal': conversions_goal,
        'revenue_goal': revenue_goal,
        'hot_count': hot_count,
        'warm_count': warm_count,
        'cold_count': cold_count,
        'high_priority_count': high_priority_count,
        'medium_priority_count': medium_priority_count,
        'low_priority_count': low_priority_count,
        'statuses': statuses_with_counts,
    }
    
    return render(request, 'leads/dashboard.html', context)


@login_required
@permission_required(3)  # Create permission
def lead_create_view(request):
    """Create new lead"""
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            mobile = request.POST.get('mobile', '')
            email = request.POST.get('email', '')
            phone = request.POST.get('phone', '')
            company = request.POST.get('company', '')
            title = request.POST.get('title', '')
            
            # Lead details
            lead_type_id = request.POST.get('lead_type')
            source_id = request.POST.get('source')
            status_id = request.POST.get('status')
            priority_id = request.POST.get('priority')
            temperature_id = request.POST.get('temperature')
            
            # Property interests
            budget_min = request.POST.get('budget_min') or None
            budget_max = request.POST.get('budget_max') or None
            preferred_locations = request.POST.get('preferred_locations', '')
            property_type = request.POST.get('property_type', '')
            requirements = request.POST.get('requirements', '')
            
            # Communication
            preferred_contact_method = request.POST.get('preferred_contact_method', 'email')
            best_contact_time = request.POST.get('best_contact_time', '')
            
            # Assignment
            assigned_to_id = request.POST.get('assigned_to')
            
            # Create lead
            lead = Lead.objects.create(
                first_name=first_name,
                last_name=last_name,
                mobile=mobile,
                email=email,
                phone=phone,
                company=company,
                title=title,
                lead_type_id=lead_type_id if lead_type_id else None,
                source_id=source_id if source_id else None,
                status_id=status_id,
                priority_id=priority_id if priority_id else None,
                temperature_id=temperature_id if temperature_id else None,
                budget_min=budget_min,
                budget_max=budget_max,
                preferred_locations=preferred_locations,
                property_type=property_type,
                requirements=requirements,
                preferred_contact_method=preferred_contact_method,
                best_contact_time=best_contact_time,
                created_by=request.user,
                assigned_to_id=assigned_to_id if assigned_to_id else None,
            )
            
            # Create initial activity
            LeadActivity.objects.create(
                lead=lead,
                user=request.user,
                activity_type='note',
                title='Lead Created',
                description=f'Lead created by {request.user.get_full_name() or request.user.username}',
                is_completed=True,
                completed_at=timezone.now()
            )
            
            messages.success(request, f'Lead "{lead.full_name}" created successfully!')
            return redirect('leads:lead_detail', lead_id=lead.id)
            
        except Exception as e:
            messages.error(request, f'Error creating lead: {str(e)}')
    
    # Get form options
    sources = LeadSource.objects.filter(is_active=True)
    statuses = LeadStatus.objects.filter(is_active=True).order_by('order')
    lead_types = LeadType.objects.filter(is_active=True)
    priorities = LeadPriority.objects.filter(is_active=True).order_by('order')
    temperatures = LeadTemperature.objects.filter(is_active=True).order_by('order')
    users = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    
    context = {
        'sources': sources,
        'statuses': statuses,
        'lead_types': lead_types,
        'priorities': priorities,
        'temperatures': temperatures,
        'users': users,
        'contact_methods': [
            ('email', 'Email'),
            ('phone', 'Phone'),
            ('sms', 'SMS'),
            ('whatsapp', 'WhatsApp'),
        ]
    }
    
    return render(request, 'leads/create_lead.html', context)


@login_required
@permission_required(1)  # View permission
def lead_detail_view(request, lead_id):
    """Detailed view of a single lead"""
    lead = get_object_or_404(Lead, id=lead_id)
    
    # Get related data
    notes = lead.lead_notes.select_related('user').order_by('-created_at')[:10]
    activities = lead.activities.select_related('user').order_by('-created_at')[:10]
    documents = lead.documents.select_related('uploaded_by').order_by('-created_at')
    
    # Activity summary
    activity_summary = lead.activities.values('activity_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'lead': lead,
        'notes': notes,
        'activities': activities,
        'documents': documents,
        'activity_summary': activity_summary,
        'can_edit': has_lead_permission(request.user, 2),
        'can_delete': has_lead_permission(request.user, 4),
        'can_add_notes': has_lead_permission(request.user, 2),
    }
    
    return render(request, 'leads/lead_detail.html', context)


@login_required
@permission_required(2)  # Edit permission
def lead_edit_view(request, lead_id):
    """Edit existing lead"""
    lead = get_object_or_404(Lead, id=lead_id)
    
    if request.method == 'POST':
        try:
            # Update basic information
            lead.first_name = request.POST['first_name']
            lead.last_name = request.POST['last_name']
            lead.mobile = request.POST.get('mobile', lead.mobile)
            lead.email = request.POST.get('email', '')
            lead.phone = request.POST.get('phone', '')
            lead.company = request.POST.get('company', '')
            lead.title = request.POST.get('title', '')
            
            # Update lead details
            lead_type_id = request.POST.get('lead_type')
            lead.lead_type_id = lead_type_id if lead_type_id else None
            source_id = request.POST.get('source')
            lead.source_id = source_id if source_id else None
            lead.status_id = request.POST.get('status')
            priority_id = request.POST.get('priority')
            lead.priority_id = priority_id if priority_id else None
            temperature_id = request.POST.get('temperature')
            lead.temperature_id = temperature_id if temperature_id else None
            
            # Update property interests
            budget_min = request.POST.get('budget_min')
            budget_max = request.POST.get('budget_max')
            lead.budget_min = budget_min if budget_min else None
            lead.budget_max = budget_max if budget_max else None
            lead.preferred_locations = request.POST.get('preferred_locations', '')
            lead.property_type = request.POST.get('property_type', '')
            lead.requirements = request.POST.get('requirements', '')
            
            # Update communication preferences
            lead.preferred_contact_method = request.POST.get('preferred_contact_method', 'email')
            lead.best_contact_time = request.POST.get('best_contact_time', '')
            
            # Update assignment
            assigned_to_id = request.POST.get('assigned_to')
            if assigned_to_id:
                lead.assigned_to_id = assigned_to_id
            
            # Update notes and tags
            lead.notes = request.POST.get('notes', '')
            lead.tags = request.POST.get('tags', '')
            
            lead.save()
            
            # Create activity for the update
            LeadActivity.objects.create(
                lead=lead,
                user=request.user,
                activity_type='note',
                title='Lead Updated',
                description=f'Lead information updated by {request.user.get_full_name() or request.user.username}',
                is_completed=True,
                completed_at=timezone.now()
            )
            
            messages.success(request, f'Lead "{lead.full_name}" updated successfully!')
            return redirect('leads:lead_detail', lead_id=lead.id)
            
        except Exception as e:
            messages.error(request, f'Error updating lead: {str(e)}')
    
    # Get navigation leads (previous/next) with same filters as list view
    leads_queryset = Lead.objects.select_related('status', 'source', 'assigned_to', 'lead_type', 'priority', 'temperature').all()
    
    # Apply user profile data filters
    leads_queryset = apply_user_data_filters(request.user, leads_queryset, 'Lead')
    
    # Restrict leads based on user permissions (if not superuser)
    if not request.user.is_superuser:
        # Check if user has manager-level access through profile
        if hasattr(request.user, 'user_profile') and request.user.user_profile.profile:
            profile = request.user.user_profile.profile
            # If profile name contains 'manager' or 'supervisor', allow seeing all filtered leads
            if 'manager' not in profile.name.lower() and 'supervisor' not in profile.name.lower():
                # Regular users can only see leads assigned to them
                leads_queryset = leads_queryset.filter(assigned_to=request.user)
        else:
            # No profile - restrict to assigned leads only
            leads_queryset = leads_queryset.filter(assigned_to=request.user)
    
    # Order by creation date (same as list view)
    leads_queryset = leads_queryset.order_by('-created_at')
    
    # Get lead IDs in order
    lead_ids = list(leads_queryset.values_list('id', flat=True))
    
    # Find current lead index
    try:
        current_index = lead_ids.index(lead_id)
        prev_lead_id = lead_ids[current_index + 1] if current_index + 1 < len(lead_ids) else None
        next_lead_id = lead_ids[current_index - 1] if current_index > 0 else None
    except ValueError:
        # Lead not found in filtered list
        prev_lead_id = None
        next_lead_id = None
    
    # Get form options
    sources = LeadSource.objects.filter(is_active=True)
    statuses = LeadStatus.objects.filter(is_active=True).order_by('order')
    users = User.objects.filter(is_active=True)
    lead_types = LeadType.objects.filter(is_active=True)
    priorities = LeadPriority.objects.filter(is_active=True).order_by('order')
    temperatures = LeadTemperature.objects.filter(is_active=True).order_by('order')
    
    context = {
        'lead': lead,
        'prev_lead_id': prev_lead_id,
        'next_lead_id': next_lead_id,
        'current_index': lead_ids.index(lead_id) + 1 if lead_id in lead_ids else 0,
        'total_leads': len(lead_ids),
        'sources': sources,
        'statuses': statuses,
        'users': users,
        'lead_types': lead_types,
        'priorities': priorities,
        'temperatures': temperatures,
        'contact_methods': [
            ('email', 'Email'),
            ('phone', 'Phone'),
            ('sms', 'SMS'),
            ('whatsapp', 'WhatsApp'),
        ]
    }
    
    return render(request, 'leads/edit_lead.html', context)


@login_required
@permission_required(4)  # Delete permission
def lead_delete_view(request, lead_id):
    """Delete lead"""
    lead = get_object_or_404(Lead, id=lead_id)
    
    if request.method == 'POST':
        lead_name = lead.full_name
        lead.delete()
        messages.success(request, f'Lead "{lead_name}" deleted successfully!')
        return redirect('leads:leads_list')
    
    return render(request, 'leads/delete_lead.html', {'lead': lead})


@login_required
@permission_required(2)  # Edit permission
def add_lead_note_view(request, lead_id):
    """Add note to lead"""
    lead = get_object_or_404(Lead, id=lead_id)
    
    if request.method == 'POST':
        note_text = request.POST.get('note')
        is_important = request.POST.get('is_important') == 'on'
        
        if note_text:
            LeadNote.objects.create(
                lead=lead,
                user=request.user,
                note=note_text,
                is_important=is_important
            )
            
            # Create activity
            LeadActivity.objects.create(
                lead=lead,
                user=request.user,
                activity_type='note',
                title='Note Added',
                description=f'Note added: {note_text[:50]}...' if len(note_text) > 50 else note_text,
                is_completed=True,
                completed_at=timezone.now()
            )
            
            messages.success(request, 'Note added successfully!')
        else:
            messages.error(request, 'Note content is required.')
    
    return redirect('leads:lead_detail', lead_id=lead_id)


@login_required
@permission_required(2)  # Edit permission  
def add_lead_activity_view(request, lead_id):
    """Add activity to lead"""
    lead = get_object_or_404(Lead, id=lead_id)
    
    if request.method == 'POST':
        try:
            activity_type = request.POST.get('activity_type')
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            outcome = request.POST.get('outcome', '')
            duration = request.POST.get('duration_minutes')
            scheduled_at = request.POST.get('scheduled_at')
            
            activity = LeadActivity.objects.create(
                lead=lead,
                user=request.user,
                activity_type=activity_type,
                title=title,
                description=description,
                outcome=outcome,
                duration_minutes=int(duration) if duration else None,
                scheduled_at=datetime.fromisoformat(scheduled_at) if scheduled_at else None,
                is_completed=request.POST.get('is_completed') == 'on',
                completed_at=timezone.now() if request.POST.get('is_completed') == 'on' else None
            )
            
            # Update lead's last contacted if it's a communication activity
            if activity_type in ['call', 'email', 'meeting', 'sms']:
                lead.mark_as_contacted()
            
            messages.success(request, 'Activity added successfully!')
            return redirect('leads:lead_detail', lead_id=lead_id)
            
        except Exception as e:
            messages.error(request, f'Error adding activity: {str(e)}')
    
    context = {
        'lead': lead,
        'activity_types': LeadActivity.ACTIVITY_TYPES,
    }
    
    return render(request, 'leads/add_activity.html', context)


@csrf_exempt
@login_required
@permission_required(2)  # Edit permission
def update_lead_status_api(request):
    """Update lead status via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            status_id = data.get('status_id')
            is_bulk = data.get('bulk', False)
            
            if is_bulk:
                # Handle bulk status update
                lead_ids = data.get('lead_ids', [])
                if not lead_ids:
                    return JsonResponse({'success': False, 'error': 'No leads selected'})
                
                leads = Lead.objects.filter(id__in=lead_ids)
                status = get_object_or_404(LeadStatus, id=status_id)
                
                updated_count = 0
                for lead in leads:
                    old_status = lead.status.name if lead.status else 'None'
                    lead.status = status
                    lead.save()
                    updated_count += 1
                    
                    # Create activity for status change
                    LeadActivity.objects.create(
                        lead=lead,
                        user=request.user,
                        activity_type='status_change',
                        title='Bulk Status Change',
                        description=f'Status changed from "{old_status}" to "{status.name}" via bulk operation',
                        is_completed=True,
                        completed_at=timezone.now()
                    )
                
                return JsonResponse({
                    'success': True,
                    'message': f'{updated_count} leads updated to {status.name}',
                    'updated_count': updated_count
                })
            else:
                # Handle single lead status update
                lead_id = data.get('lead_id')
                lead = get_object_or_404(Lead, id=lead_id)
                old_status = lead.status.name if lead.status else 'None'
                
                status = get_object_or_404(LeadStatus, id=status_id)
                lead.status = status
                lead.save()
                
                # Create activity for status change
                LeadActivity.objects.create(
                    lead=lead,
                    user=request.user,
                    activity_type='status_change',
                    title='Status Changed',
                    description=f'Status changed from "{old_status}" to "{status.name}"',
                    is_completed=True,
                    completed_at=timezone.now()
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Status updated to {status.name}',
                    'new_status': status.name,
                    'new_color': status.color
                })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
@login_required
@permission_required(2)  # Edit permission
def add_quick_note_api(request):
    """Add quick note via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lead_id = data.get('lead_id')
            note_text = data.get('note')
            
            lead = get_object_or_404(Lead, id=lead_id)
            
            note = LeadNote.objects.create(
                lead=lead,
                user=request.user,
                note=note_text,
                is_important=False
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Note added successfully',
                'note_id': note.id,
                'created_at': note.created_at.strftime('%Y-%m-%d %H:%M')
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
@login_required
@permission_required(2)  # Edit permission
def archive_lead_api(request):
    """Archive lead via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lead_id = data.get('lead_id')
            
            lead = get_object_or_404(Lead, id=lead_id)
            
            # Try to find an "Archived" status, or create one if it doesn't exist
            archived_status, created = LeadStatus.objects.get_or_create(
                name='Archived',
                defaults={
                    'description': 'Archived leads',
                    'color': '#6b7280',
                    'order': 999,
                    'is_active': True,
                    'is_final': True
                }
            )
            
            old_status = lead.status.name
            lead.status = archived_status
            lead.save()
            
            # Create activity for archiving
            LeadActivity.objects.create(
                lead=lead,
                user=request.user,
                activity_type='status_change',
                title='Lead Archived',
                description=f'Lead archived by {request.user.get_full_name() or request.user.username}. Status changed from "{old_status}" to "Archived"',
                is_completed=True,
                completed_at=timezone.now()
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Lead archived successfully'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@permission_required(1)  # View permission
def leads_search_api(request):
    """Search leads via AJAX"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    leads = Lead.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query) |
        Q(phone__icontains=query) |
        Q(company__icontains=query)
    ).select_related('status')[:10]
    
    results = []
    for lead in leads:
        results.append({
            'id': str(lead.id),
            'name': lead.full_name,
            'email': lead.email,
            'phone': lead.phone,
            'status': lead.status.name,
            'status_color': lead.status.color,
        })
    
    return JsonResponse({'results': results})


# Lead management actions
@login_required
@permission_required(2)
def update_lead_score_view(request, lead_id):
    """Update lead score"""
    lead = get_object_or_404(Lead, id=lead_id)
    
    if request.method == 'POST':
        try:
            score = int(request.POST.get('score', 0))
            if 0 <= score <= 100:
                old_score = lead.score
                lead.score = score
                lead.save()
                
                # Create activity for score change
                LeadActivity.objects.create(
                    lead=lead,
                    user=request.user,
                    activity_type='score_update',
                    title='Score Updated',
                    description=f'Score changed from {old_score} to {score}',
                    is_completed=True,
                    completed_at=timezone.now()
                )
                
                messages.success(request, f'Lead score updated to {score}')
            else:
                messages.error(request, 'Score must be between 0 and 100')
        except ValueError:
            messages.error(request, 'Invalid score value')
    
    return redirect('leads:lead_detail', lead_id=lead_id)


@login_required
@permission_required(2) 
def lead_convert_view(request, lead_id):
    """Convert lead to customer/opportunity"""
    lead = get_object_or_404(Lead, id=lead_id)
    
    if request.method == 'POST':
        try:
            # Mark lead as converted
            lead.converted_at = timezone.now()
            lead.save()
            
            # Create conversion activity
            LeadActivity.objects.create(
                lead=lead,
                user=request.user,
                activity_type='conversion',
                title='Lead Converted',
                description=f'Lead converted to customer by {request.user.get_full_name() or request.user.username}',
                is_completed=True,
                completed_at=timezone.now()
            )
            
            messages.success(request, f'Lead "{lead.full_name}" converted successfully!')
            return redirect('leads:lead_detail', lead_id=lead_id)
            
        except Exception as e:
            messages.error(request, f'Error converting lead: {str(e)}')
    
    return redirect('leads:lead_detail', lead_id=lead_id)


@login_required
@permission_required(2)
def lead_assign_view(request, lead_id):
    """Assign lead to user"""
    lead = get_object_or_404(Lead, id=lead_id)
    
    if request.method == 'POST':
        try:
            user_id = request.POST.get('assigned_to')
            old_user = lead.assigned_to
            
            if user_id:
                new_user = get_object_or_404(User, id=user_id)
                lead.assigned_to = new_user
            else:
                lead.assigned_to = None
                new_user = None
            
            lead.save()
            
            # Create activity for assignment change
            description = f'Lead reassigned from {old_user.get_full_name() if old_user else "Unassigned"} to {new_user.get_full_name() if new_user else "Unassigned"}'
            LeadActivity.objects.create(
                lead=lead,
                user=request.user,
                activity_type='assignment',
                title='Lead Reassigned',
                description=description,
                is_completed=True,
                completed_at=timezone.now()
            )
            
            messages.success(request, 'Lead assignment updated successfully!')
            
        except Exception as e:
            messages.error(request, f'Error updating assignment: {str(e)}')
    
    return redirect('leads:lead_detail', lead_id=lead_id)


# Notes management
@login_required
@permission_required(1)
def lead_notes_view(request, lead_id):
    """View all notes for a lead"""
    lead = get_object_or_404(Lead, id=lead_id)
    notes = lead.lead_notes.select_related('user').order_by('-created_at')
    
    context = {
        'lead': lead,
        'notes': notes,
        'can_add_notes': has_lead_permission(request.user, 2),
        'can_delete_notes': has_lead_permission(request.user, 4),
    }
    
    return render(request, 'leads/lead_notes.html', context)


@login_required
@permission_required(4)
def delete_lead_note_view(request, note_id):
    """Delete a lead note"""
    note = get_object_or_404(LeadNote, id=note_id)
    lead_id = note.lead.id
    
    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Note deleted successfully!')
    
    return redirect('leads:lead_detail', lead_id=lead_id)


# Activities management  
@login_required  
@permission_required(1)
def lead_activities_view(request, lead_id):
    """View all activities for a lead"""
    lead = get_object_or_404(Lead, id=lead_id)
    activities = lead.activities.select_related('user').order_by('-created_at')
    
    context = {
        'lead': lead,
        'activities': activities,
        'can_add_activities': has_lead_permission(request.user, 2),
        'can_delete_activities': has_lead_permission(request.user, 4),
    }
    
    return render(request, 'leads/lead_activities.html', context)


@login_required
@permission_required(2)
def complete_activity_view(request, activity_id):
    """Mark activity as completed"""
    activity = get_object_or_404(LeadActivity, id=activity_id)
    
    if request.method == 'POST':
        activity.is_completed = True
        activity.completed_at = timezone.now()
        activity.save()
        
        messages.success(request, 'Activity marked as completed!')
    
    return redirect('leads:lead_detail', lead_id=activity.lead.id)


@login_required
@permission_required(4)
def delete_activity_view(request, activity_id):
    """Delete an activity"""
    activity = get_object_or_404(LeadActivity, id=activity_id)
    lead_id = activity.lead.id
    
    if request.method == 'POST':
        activity.delete()
        messages.success(request, 'Activity deleted successfully!')
    
    return redirect('leads:lead_detail', lead_id=lead_id)


# Bulk operations
@login_required
@permission_required(2)
def bulk_assign_leads_view(request):
    """Bulk assign leads to users"""
    if request.method == 'POST':
        try:
            lead_ids = request.POST.getlist('lead_ids')
            user_id = request.POST.get('assigned_to')
            
            if lead_ids and user_id:
                user = get_object_or_404(User, id=user_id)
                leads = Lead.objects.filter(id__in=lead_ids)
                
                for lead in leads:
                    lead.assigned_to = user
                    lead.save()
                    
                    # Create activity for bulk assignment
                    LeadActivity.objects.create(
                        lead=lead,
                        user=request.user,
                        activity_type='assignment',
                        title='Bulk Assignment',
                        description=f'Lead assigned to {user.get_full_name() or user.username} via bulk operation',
                        is_completed=True,
                        completed_at=timezone.now()
                    )
                
                messages.success(request, f'{len(lead_ids)} leads assigned to {user.get_full_name() or user.username}')
            
        except Exception as e:
            messages.error(request, f'Error in bulk assignment: {str(e)}')
    
    return redirect('leads:leads_list')


@login_required
@permission_required(4)
def bulk_delete_leads_view(request):
    """Bulk delete leads"""
    if request.method == 'POST':
        try:
            lead_ids = request.POST.getlist('lead_ids')
            
            if lead_ids:
                leads = Lead.objects.filter(id__in=lead_ids)
                count = leads.count()
                leads.delete()
                
                messages.success(request, f'{count} leads deleted successfully!')
            
        except Exception as e:
            messages.error(request, f'Error in bulk deletion: {str(e)}')
    
    return redirect('leads:leads_list')


@login_required
@permission_required(1)
def export_leads_view(request):
    """Export leads to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="leads_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Name', 'Email', 'Phone', 'Company', 'Status', 'Source', 
        'Priority', 'Score', 'Created', 'Assigned To'
    ])
    
    # Check if specific leads are selected for export
    if request.method == 'POST':
        lead_ids = request.POST.getlist('lead_ids')
        if lead_ids:
            leads = Lead.objects.select_related('status', 'source', 'assigned_to').filter(id__in=lead_ids)
        else:
            # Fallback to all accessible leads
            if request.user.is_superuser:
                leads = Lead.objects.select_related('status', 'source', 'assigned_to').all()
            else:
                leads = Lead.objects.select_related('status', 'source', 'assigned_to').filter(assigned_to=request.user)
    else:
        # GET request - export all accessible leads
        if request.user.is_superuser:
            leads = Lead.objects.select_related('status', 'source', 'assigned_to').all()
        else:
            leads = Lead.objects.select_related('status', 'source', 'assigned_to').filter(assigned_to=request.user)
    
    for lead in leads:
        writer.writerow([
            lead.full_name,
            lead.email,
            lead.phone,
            lead.company,
            lead.status.name if lead.status else '',
            lead.source.name if lead.source else '',
            lead.priority.name if lead.priority else '',
            lead.score,
            lead.created_at.strftime('%Y-%m-%d'),
            lead.assigned_to.get_full_name() if lead.assigned_to else 'Unassigned'
        ])
    
    return response


# Source and status management
@login_required
@permission_required(1)
def lead_sources_view(request):
    """Manage lead sources"""
    sources = LeadSource.objects.all().order_by('name')
    
    context = {
        'sources': sources,
        'can_create': has_lead_permission(request.user, 3),
        'can_edit': has_lead_permission(request.user, 2),
        'can_delete': has_lead_permission(request.user, 4),
    }
    
    return render(request, 'leads/sources.html', context)


@login_required
@permission_required(3)
def create_lead_source_view(request):
    """Create new lead source"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            
            if name:
                LeadSource.objects.create(
                    name=name,
                    description=description,
                    created_by=request.user
                )
                messages.success(request, f'Lead source "{name}" created successfully!')
                return redirect('leads:sources')
            else:
                messages.error(request, 'Source name is required.')
                
        except Exception as e:
            messages.error(request, f'Error creating source: {str(e)}')
    
    return render(request, 'leads/create_source.html')


@login_required
@permission_required(1)
def lead_statuses_view(request):
    """Manage lead statuses"""
    statuses = LeadStatus.objects.all().order_by('order')
    
    context = {
        'statuses': statuses,
        'can_create': has_lead_permission(request.user, 3),
        'can_edit': has_lead_permission(request.user, 2),
        'can_delete': has_lead_permission(request.user, 4),
    }
    
    return render(request, 'leads/statuses.html', context)


@login_required
@permission_required(3)
def create_lead_status_view(request):
    """Create new lead status"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            color = request.POST.get('color', '#3b82f6')
            description = request.POST.get('description', '')
            order = request.POST.get('order', 0)
            
            if name:
                LeadStatus.objects.create(
                    name=name,
                    color=color,
                    description=description,
                    order=int(order),
                    created_by=request.user
                )
                messages.success(request, f'Lead status "{name}" created successfully!')
                return redirect('leads:statuses')
            else:
                messages.error(request, 'Status name is required.')
                
        except Exception as e:
            messages.error(request, f'Error creating status: {str(e)}')
    
    return render(request, 'leads/create_status.html')


@login_required
@permission_required(3)
def import_leads_view(request):
    """Import leads from CSV file"""
    if request.method == 'POST':
        try:
            import csv
            import io
            
            csv_file = request.FILES.get('csv_file')
            
            if not csv_file:
                messages.error(request, 'Please select a CSV file to upload.')
                return redirect('leads:leads_list')
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a valid CSV file.')
                return redirect('leads:leads_list')
            
            # Read and parse CSV
            file_data = csv_file.read().decode('utf-8')
            csv_data = csv.reader(io.StringIO(file_data))
            
            # Skip header row
            headers = next(csv_data)
            
            # Get default values
            default_source = LeadSource.objects.first()
            default_status = LeadStatus.objects.first()
            
            imported_count = 0
            error_count = 0
            
            for row_num, row in enumerate(csv_data, start=2):
                try:
                    if len(row) < 4:  # Minimum required fields
                        continue
                    
                    # Extract data from CSV row
                    first_name = row[0].strip() if len(row) > 0 else ''
                    last_name = row[1].strip() if len(row) > 1 else ''
                    email = row[2].strip() if len(row) > 2 else ''
                    phone = row[3].strip() if len(row) > 3 else ''
                    company = row[4].strip() if len(row) > 4 else ''
                    
                    # Skip if no name or email
                    if not first_name and not email:
                        continue
                    
                    # Check if lead already exists
                    if email and Lead.objects.filter(email=email).exists():
                        continue
                    
                    # Create new lead
                    lead = Lead.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        phone=phone,
                        company=company,
                        source=default_source,
                        status=default_status,
                        assigned_to=request.user,
                        created_by=request.user
                    )
                    
                    imported_count += 1
                    
                except Exception as e:
                    error_count += 1
                    continue
            
            if imported_count > 0:
                messages.success(request, f'Successfully imported {imported_count} leads.')
            
            if error_count > 0:
                messages.warning(request, f'{error_count} rows had errors and were skipped.')
            
            if imported_count == 0 and error_count == 0:
                messages.info(request, 'No new leads were imported. All leads may already exist.')
            
        except Exception as e:
            messages.error(request, f'Error importing leads: {str(e)}')
    
    return redirect('leads:leads_list')


@csrf_exempt
@login_required
def save_column_preferences(request):
    """Save user's column display preferences via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            preferences = UserLeadPreferences.get_for_user(request.user)
            
            # Update column visibility preferences
            preferences.show_checkbox = data.get('show_checkbox', True)
            preferences.show_name = data.get('show_name', True)  # Always show name
            preferences.show_mobile = data.get('show_mobile', True)
            preferences.show_email = data.get('show_email', True)
            preferences.show_company = data.get('show_company', True)
            preferences.show_status = data.get('show_status', True)
            preferences.show_source = data.get('show_source', False)
            preferences.show_priority = data.get('show_priority', False)
            preferences.show_temperature = data.get('show_temperature', False)
            preferences.show_score = data.get('show_score', False)
            preferences.show_assigned_to = data.get('show_assigned_to', True)
            preferences.show_created_at = data.get('show_created_at', False)
            preferences.show_last_contacted = data.get('show_last_contacted', False)
            preferences.show_budget = data.get('show_budget', False)
            preferences.show_property_type = data.get('show_property_type', False)
            preferences.show_actions = data.get('show_actions', True)  # Always show actions
            
            preferences.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Column preferences saved successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# ==================== EVENTS API ====================

@login_required
def get_lead_events_api(request, lead_id):
    """Get all events for a specific lead"""
    try:
        lead = get_object_or_404(Lead, id=lead_id)
        
        # Check permissions
        if not request.user.is_superuser:
            user_profile = request.user.user_profile
            if lead.assigned_to != request.user and not user_profile.profile.permissions.filter(
                module__name='leads', code='view'
            ).exists():
                return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        # Get events
        events = LeadEvent.objects.filter(lead_id=lead_id).order_by('-start_datetime')
        
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'title': event.title,
                'event_type': event.event_type,
                'description': event.description,
                'start_datetime': event.start_datetime.isoformat(),
                'end_datetime': event.end_datetime.isoformat(),
                'location': event.location,
                'status': event.status,
                'duration_minutes': event.duration_minutes,
                'assigned_to': event.assigned_to.get_full_name() if event.assigned_to else None,
                'created_by': event.created_by.get_full_name() if event.created_by else None,
            })
        
        return JsonResponse({
            'success': True,
            'events': events_data
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@login_required
def create_event_api(request):
    """Create a new event"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lead_id = data.get('lead_id')
            
            lead = get_object_or_404(Lead, id=lead_id)
            
            # Check permissions
            if not request.user.is_superuser:
                user_profile = request.user.user_profile
                if lead.assigned_to != request.user and not user_profile.profile.permissions.filter(
                    module__name='leads', code='edit'
                ).exists():
                    return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
            
            from django.utils.dateparse import parse_datetime
            
            # Create event
            event = LeadEvent.objects.create(
                lead_id=lead_id,
                title=data.get('title'),
                event_type=data.get('event_type', 'meeting'),
                description=data.get('description', ''),
                start_datetime=parse_datetime(data.get('start_datetime')),
                end_datetime=parse_datetime(data.get('end_datetime')),
                location=data.get('location', ''),
                reminder_minutes_before=data.get('reminder_minutes_before', 30),
                assigned_to=request.user,
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Event created successfully!',
                'event_id': event.id
            })
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


@csrf_exempt
@login_required
def update_event_status_api(request, event_id):
    """Update event status"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            event = get_object_or_404(LeadEvent, id=event_id)
            
            # Check permissions
            if not request.user.is_superuser:
                if event.assigned_to != request.user and event.created_by != request.user:
                    return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
            
            event.status = data.get('status')
            event.save(update_fields=['status'])
            
            return JsonResponse({
                'success': True,
                'message': f'Event {event.status} successfully!'
            })
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


@login_required
def get_user_upcoming_events_api(request):
    """Get upcoming events for the logged-in user (for calendar in navbar)"""
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        # Get events for next 30 days
        today = timezone.now()
        next_month = today + timedelta(days=30)
        
        events = LeadEvent.objects.filter(
            assigned_to=request.user,
            start_datetime__gte=today,
            start_datetime__lte=next_month,
            status='scheduled'
        ).order_by('start_datetime')[:20]  # Limit to 20 events
        
        events_data = []
        for event in events:
            try:
                lead = Lead.objects.get(id=event.lead_id)
                lead_name = lead.full_name
            except Lead.DoesNotExist:
                lead_name = "Unknown Lead"
            
            events_data.append({
                'id': event.id,
                'title': event.title,
                'event_type': event.event_type,
                'start_datetime': event.start_datetime.isoformat(),
                'end_datetime': event.end_datetime.isoformat(),
                'location': event.location,
                'lead_id': event.lead_id,
                'lead_name': lead_name,
                'duration_minutes': event.duration_minutes,
            })
        
        return JsonResponse({
            'success': True,
            'events': events_data,
            'count': len(events_data)
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

