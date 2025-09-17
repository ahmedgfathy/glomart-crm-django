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
    LeadType, LeadPriority, LeadTemperature
)
from authentication.models import Module, Permission


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
    leads = Lead.objects.select_related('status', 'source', 'assigned_to', 'lead_type', 'priority', 'temperature').all()
    
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
                Q(address__icontains=word) |
                Q(city__icontains=word) |
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
            Q(address__icontains=search_query) |
            Q(city__icontains=search_query) |
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
    users = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    lead_types = LeadType.objects.filter(is_active=True)
    priorities = LeadPriority.objects.filter(is_active=True).order_by('order')
    temperatures = LeadTemperature.objects.filter(is_active=True).order_by('order')
    
    # Statistics
    total_leads = Lead.objects.count()
    qualified_leads = Lead.objects.filter(is_qualified=True).count()
    unassigned_leads = Lead.objects.filter(assigned_to__isnull=True).count()
    
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
    
    # Get form options
    sources = LeadSource.objects.filter(is_active=True)
    statuses = LeadStatus.objects.filter(is_active=True).order_by('order')
    users = User.objects.filter(is_active=True)
    lead_types = LeadType.objects.filter(is_active=True)
    priorities = LeadPriority.objects.filter(is_active=True).order_by('order')
    temperatures = LeadTemperature.objects.filter(is_active=True).order_by('order')
    
    context = {
        'lead': lead,
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
            lead_id = data.get('lead_id')
            status_id = data.get('status_id')
            
            lead = get_object_or_404(Lead, id=lead_id)
            old_status = lead.status.name
            lead.status_id = status_id
            lead.save()
            
            new_status = lead.status.name
            
            # Create activity for status change
            LeadActivity.objects.create(
                lead=lead,
                user=request.user,
                activity_type='status_change',
                title='Status Changed',
                description=f'Status changed from "{old_status}" to "{new_status}"',
                is_completed=True,
                completed_at=timezone.now()
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Status updated to {new_status}',
                'new_status': new_status,
                'new_color': lead.status.color
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
    
    leads = Lead.objects.select_related('status', 'source', 'assigned_to').all()
    
    for lead in leads:
        writer.writerow([
            lead.full_name,
            lead.email,
            lead.phone,
            lead.company,
            lead.status.name if lead.status else '',
            lead.source.name if lead.source else '',
            lead.get_priority_display(),
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
