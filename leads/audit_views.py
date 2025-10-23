from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import csv
import json

from leads.models import Lead, LeadAudit
from authentication.models import UserProfile


def has_audit_permission(user, permission_code):
    """Check if user has specific audit permission"""
    print(f"🔍 PERMISSION DEBUG: Checking {user.username} for audit.{permission_code}")
    try:
        user_profile = user.user_profile
        print(f"🔍 PERMISSION DEBUG: User profile found: {user_profile.id}")
        
        result = user_profile.has_permission('audit', permission_code)
        print(f"🔍 PERMISSION DEBUG: Permission result: {result}")
        return result
    except (UserProfile.DoesNotExist, AttributeError) as e:
        print(f"❌ PERMISSION DEBUG: Error: {e}")
        return False


@login_required
def audit_list(request):
    """Main audit list view with filtering and search"""
    print(f"🔍 AUDIT DEBUG: User: {request.user.username}, is_authenticated: {request.user.is_authenticated}")
    
    # Check permissions
    has_view_perm = has_audit_permission(request.user, 'view')
    print(f"🔍 AUDIT DEBUG: has_audit_permission('view'): {has_view_perm}")
    
    if not has_view_perm:
        print(f"❌ AUDIT DEBUG: No permission, rendering no_permission template")
        return render(request, 'audit/no_permission.html', {
            'message': 'You do not have permission to view audit logs.'
        })
    
    can_view_all = has_audit_permission(request.user, 'view_all')
    can_export = has_audit_permission(request.user, 'export')
    can_manage = has_audit_permission(request.user, 'manage')
    
    print(f"🔍 AUDIT DEBUG: can_view_all: {can_view_all}, can_export: {can_export}, can_manage: {can_manage}")
    
    # Base queryset
    if can_view_all:
        audits = LeadAudit.objects.all()
    else:
        # Users can only see their own actions
        audits = LeadAudit.objects.filter(user=request.user)
    
    print(f"🔍 AUDIT DEBUG: Total audits before filtering: {audits.count()}")
    
    # Apply filters
    filters = {}
    
    # Date range filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            audits = audits.filter(timestamp__date__gte=date_from)
            filters['date_from'] = date_from.strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            audits = audits.filter(timestamp__date__lte=date_to)
            filters['date_to'] = date_to.strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    # Action filter
    action_filter = request.GET.get('action')
    if action_filter:
        audits = audits.filter(action=action_filter)
        filters['action'] = action_filter
    
    # User filter (only if can view all)
    user_filter = request.GET.get('user')
    if user_filter and can_view_all:
        try:
            user_id = int(user_filter)
            audits = audits.filter(user_id=user_id)
            filters['user'] = user_id
        except (ValueError, TypeError):
            pass
    
    # Severity filter
    severity_filter = request.GET.get('severity')
    if severity_filter:
        audits = audits.filter(severity=severity_filter)
        filters['severity'] = severity_filter
    
    # Search filter
    search_query = request.GET.get('search')
    if search_query:
        audits = audits.filter(
            Q(description__icontains=search_query) |
            Q(lead_name_backup__icontains=search_query) |
            Q(user_name_backup__icontains=search_query) |
            Q(field_name__icontains=search_query) |
            Q(old_value__icontains=search_query) |
            Q(new_value__icontains=search_query)
        )
        filters['search'] = search_query
    
    # Order by timestamp (newest first)
    audits = audits.select_related('user', 'lead').order_by('-timestamp')
    
    print(f"🔍 AUDIT DEBUG: Audits after ordering: {audits.count()}")
    
    # Pagination
    page_size = int(request.GET.get('page_size', 25))
    paginator = Paginator(audits, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    print(f"🔍 AUDIT DEBUG: Page size: {page_size}, Current page: {page_number or 1}")
    print(f"🔍 AUDIT DEBUG: Page object has {len(page_obj)} items")
    print(f"🔍 AUDIT DEBUG: Sample audit items:")
    for i, audit in enumerate(page_obj[:3]):  # Show first 3
        print(f"  {i+1}. ID: {audit.id}, Action: {audit.action}, User: {audit.user_identifier}, Time: {audit.timestamp}")
    
    # Get filter options for dropdowns
    action_choices = LeadAudit.ACTION_TYPES
    severity_choices = LeadAudit.SEVERITY_CHOICES
    
    # Get users for filter (only if can view all)
    users_for_filter = []
    if can_view_all:
        users_for_filter = User.objects.filter(
            lead_audits__isnull=False
        ).distinct().order_by('first_name', 'last_name', 'username')
    
    # Get statistics
    total_audits = audits.count()
    today_audits = audits.filter(timestamp__date=timezone.now().date()).count()
    
    # Recent activities (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_stats = audits.filter(timestamp__gte=week_ago).values('action').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    context = {
        'page_obj': page_obj,
        'filters': filters,
        'action_choices': action_choices,
        'severity_choices': severity_choices,
        'users_for_filter': users_for_filter,
        'can_view_all': can_view_all,
        'can_export': can_export,
        'can_manage': can_manage,
        'total_audits': total_audits,
        'today_audits': today_audits,
        'recent_stats': recent_stats,
        'page_size': page_size,
    }
    
    return render(request, 'audit/audit_list.html', context)


@login_required
def audit_detail(request, audit_id):
    """Detailed view of a specific audit log"""
    audit = get_object_or_404(LeadAudit, id=audit_id)
    
    # Check permissions
    can_view_all = has_audit_permission(request.user, 'view_all')
    
    if not can_view_all and audit.user != request.user:
        return render(request, 'audit/no_permission.html', {
            'message': 'You do not have permission to view this audit log.'
        })
    
    # Get related audits for the same lead
    related_audits = []
    try:
        if audit.lead:
            related_audits = LeadAudit.objects.filter(
                lead=audit.lead
            ).exclude(id=audit.id).order_by('-timestamp')[:10]
    except Lead.DoesNotExist:
        # Lead has been deleted, no related audits to show
        related_audits = []
    
    context = {
        'audit': audit,
        'related_audits': related_audits,
        'can_view_all': can_view_all,
    }
    
    return render(request, 'audit/audit_detail.html', context)


@login_required
def audit_export(request):
    """Export audit logs to CSV"""
    if not has_audit_permission(request.user, 'export'):
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to export audit logs.'
        }, status=403)
    
    can_view_all = has_audit_permission(request.user, 'view_all')
    
    # Get the same filtered queryset as the list view
    if can_view_all:
        audits = LeadAudit.objects.all()
    else:
        audits = LeadAudit.objects.filter(user=request.user)
    
    # Apply the same filters as in audit_list
    # (This is a simplified version - you could extract the filtering logic to a separate function)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="audit_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Timestamp',
        'Action',
        'Lead Name',
        'User',
        'Description',
        'Field Changed',
        'Old Value',
        'New Value',
        'Severity',
        'IP Address'
    ])
    
    # Write data
    for audit in audits.select_related('user', 'lead').order_by('-timestamp'):
        writer.writerow([
            audit.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            audit.get_action_display(),
            audit.lead_identifier,
            audit.user_identifier,
            audit.description,
            audit.field_name,
            audit.old_value,
            audit.new_value,
            audit.get_severity_display(),
            audit.ip_address or ''
        ])
    
    return response


@login_required
def audit_stats_api(request):
    """API endpoint for audit statistics"""
    if not has_audit_permission(request.user, 'view'):
        return JsonResponse({
            'success': False,
            'message': 'No permission'
        }, status=403)
    
    can_view_all = has_audit_permission(request.user, 'view_all')
    
    # Base queryset
    if can_view_all:
        audits = LeadAudit.objects.all()
    else:
        audits = LeadAudit.objects.filter(user=request.user)
    
    # Get date range (last 30 days by default)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    audits = audits.filter(timestamp__gte=start_date)
    
    # Daily activity counts
    daily_stats = audits.extra(
        select={'day': 'date(timestamp)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Action type distribution
    action_stats = audits.values('action').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # User activity (only if can view all)
    user_stats = []
    if can_view_all:
        user_stats = audits.values(
            'user__first_name', 'user__last_name', 'user__username'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]
    
    return JsonResponse({
        'success': True,
        'daily_stats': list(daily_stats),
        'action_stats': list(action_stats),
        'user_stats': list(user_stats),
        'total_audits': audits.count()
    })


@login_required
def audit_settings(request):
    """Audit settings and management"""
    if not has_audit_permission(request.user, 'manage'):
        return render(request, 'audit/no_permission.html', {
            'message': 'You do not have permission to manage audit settings.'
        })
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'purge_old':
            # Purge audit logs older than specified days
            days = int(request.POST.get('days', 90))
            cutoff_date = timezone.now() - timedelta(days=days)
            
            deleted_count = LeadAudit.objects.filter(
                timestamp__lt=cutoff_date
            ).delete()[0]
            
            # Log this action
            LeadAudit.log_action(
                lead=None,
                action='delete',
                user=request.user,
                description=f"Purged {deleted_count} audit logs older than {days} days",
                severity='critical'
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Purged {deleted_count} old audit logs.'
            })
    
    # Get statistics for settings page
    total_audits = LeadAudit.objects.count()
    oldest_audit = LeadAudit.objects.order_by('timestamp').first()
    newest_audit = LeadAudit.objects.order_by('-timestamp').first()
    
    # Storage usage estimation (rough)
    avg_size_per_audit = 500  # bytes
    estimated_storage_mb = (total_audits * avg_size_per_audit) / 1024 / 1024
    
    context = {
        'total_audits': total_audits,
        'oldest_audit': oldest_audit,
        'newest_audit': newest_audit,
        'estimated_storage_mb': round(estimated_storage_mb, 2)
    }
    
    return render(request, 'audit/audit_settings.html', context)