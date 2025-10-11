from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
import json
from datetime import datetime

from .models import OwnerDatabase, OwnerDatabaseAccess
from authentication.models import Module, Permission


def has_owner_permission(user, permission_level):
    """Check if user has specific permission level for owner module"""
    if user.is_superuser:
        return True
    
    try:
        user_profile = user.user_profile
        owner_module = Module.objects.get(name='owner')
        
        # Check if user has required permission level
        has_permission = user_profile.profile.rules.filter(
            module=owner_module,
            permission__level__gte=permission_level
        ).exists()
        
        return has_permission
    except (AttributeError, Module.DoesNotExist):
        return False


@login_required
def owner_dashboard(request):
    """Main dashboard for owner databases"""
    if not has_owner_permission(request.user, 1):  # View permission
        messages.error(request, "You don't have permission to access owner databases.")
        return redirect('authentication:dashboard')
    
    # Get available databases
    databases = OwnerDatabase.objects.filter(is_active=True).order_by('category', 'display_name')
    
    # Group databases by category
    categories = {}
    for db in databases:
        category = db.category or 'Uncategorized'
        if category not in categories:
            categories[category] = []
        categories[category].append(db)
    
    # Get user's recent database access
    recent_access = OwnerDatabaseAccess.objects.filter(
        user=request.user
    ).select_related('database').order_by('-last_accessed')[:10]
    
    # Statistics
    total_databases = databases.count()
    total_records = sum(db.total_records for db in databases)
    
    context = {
        'categories': categories,
        'recent_access': recent_access,
        'total_databases': total_databases,
        'total_records': total_records,
        'can_manage': has_owner_permission(request.user, 4),  # Delete/Manage permission
    }
    
    return render(request, 'owner/dashboard.html', context)


@login_required
def database_list(request):
    """List all available owner databases with filtering"""
    if not has_owner_permission(request.user, 1):  # View permission
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get filter parameters
    category_filter = request.GET.get('category')
    search_query = request.GET.get('search', '').strip()
    
    # Base queryset
    databases = OwnerDatabase.objects.filter(is_active=True)
    
    # Apply filters
    if category_filter:
        databases = databases.filter(category=category_filter)
    
    if search_query:
        databases = databases.filter(
            Q(name__icontains=search_query) |
            Q(display_name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(databases, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter dropdown
    categories = OwnerDatabase.objects.values_list('category', flat=True).distinct()
    categories = [cat for cat in categories if cat]  # Remove empty categories
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_filter,
        'search_query': search_query,
        'can_manage': has_owner_permission(request.user, 4),
    }
    
    return render(request, 'owner/database_list.html', context)


@login_required
def database_detail(request, database_id):
    """View specific database with data table"""
    if not has_owner_permission(request.user, 1):  # View permission
        messages.error(request, "You don't have permission to access owner databases.")
        return redirect('owner:dashboard')
    
    database = get_object_or_404(OwnerDatabase, id=database_id, is_active=True)
    
    # Record user access
    access, created = OwnerDatabaseAccess.objects.get_or_create(
        user=request.user,
        database=database,
        defaults={'access_count': 0}
    )
    access.access_count += 1
    access.save()
    
    # Get table information
    table_info = database.get_table_info()
    if not table_info:
        messages.error(request, f"Unable to connect to database: {database.name}")
        return redirect('owner:dashboard')
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    page_number = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 50))
    
    # Calculate offset
    offset = (page_number - 1) * per_page
    
    # Get data
    result = database.get_data(
        limit=per_page,
        offset=offset,
        search=search_query
    )
    
    # Get smart column mapping
    column_mapping = database.get_smart_column_mapping()
    
    # Calculate pagination info
    total_records = result['total']
    total_pages = (total_records + per_page - 1) // per_page
    
    # Calculate page range for pagination
    start_page = max(1, page_number - 2)
    end_page = min(total_pages, page_number + 2)
    page_range = list(range(start_page, end_page + 1))
    
    # Ensure we always show at least 5 pages if possible
    if len(page_range) < 5 and total_pages >= 5:
        if page_number <= 3:
            page_range = list(range(1, min(6, total_pages + 1)))
        elif page_number >= total_pages - 2:
            page_range = list(range(max(1, total_pages - 4), total_pages + 1))

    # Create enhanced columns info with smart names
    enhanced_columns = []
    for column in table_info['columns']:
        original_name = column['Field']
        smart_name = column_mapping.get(original_name, original_name)
        
        # Skip source_file fields from table display
        if 'source_file' in original_name.lower() or 'source_file' in smart_name.lower():
            continue
            
        enhanced_columns.append({
            'original': original_name,
            'display': smart_name,
            'type': column['Type'],
            'null': column['Null'],
            'key': column['Key'],
            'default': column['Default'],
            'extra': column['Extra']
        })

    context = {
        'database': database,
        'table_info': table_info,
        'data': result['data'],
        'columns': table_info['columns'],
        'enhanced_columns': enhanced_columns,
        'column_mapping': column_mapping,
        'total_records': total_records,
        'current_page': page_number,
        'total_pages': total_pages,
        'per_page': per_page,
        'search_query': search_query,
        'has_previous': page_number > 1,
        'has_next': page_number < total_pages,
        'previous_page': page_number - 1 if page_number > 1 else None,
        'next_page': page_number + 1 if page_number < total_pages else None,
        'page_range': page_range,
    }
    
    return render(request, 'owner/database_detail.html', context)


@login_required
def record_detail(request, database_id, record_id):
    """Get detailed information for a specific record"""
    if not has_owner_permission(request.user, 1):  # View permission
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    database = get_object_or_404(OwnerDatabase, id=database_id, is_active=True)
    record = database.get_record_by_id(record_id)
    
    if not record:
        return JsonResponse({'error': 'Record not found'}, status=404)
    
    # Get table info for column metadata
    table_info = database.get_table_info()
    columns = table_info['columns'] if table_info else []
    
    # Get smart column mapping
    column_mapping = database.get_smart_column_mapping()
    
    # Format the record data with smart column names
    formatted_record = []
    for column in columns:
        field_name = column['Field']
        field_type = column['Type']
        field_value = record.get(field_name, '')
        smart_name = column_mapping.get(field_name, field_name)
        
        # Skip source_file fields from popup display
        if 'source_file' in field_name.lower() or 'source_file' in smart_name.lower():
            continue
        
        # Format the value based on its type and content
        formatted_value = field_value
        if field_value:
            # Format dates
            if 'date' in smart_name.lower() and str(field_value):
                try:
                    from datetime import datetime
                    if isinstance(field_value, str) and len(str(field_value)) >= 10:
                        formatted_value = str(field_value)[:10]  # Show only date part
                except:
                    pass
            
            # Format phone numbers
            if 'phone' in smart_name.lower() or 'mobile' in smart_name.lower():
                phone_str = str(field_value)
                if len(phone_str) >= 10:
                    # Format as phone number if it looks like one
                    formatted_value = phone_str
            
            # Format large numbers with commas
            if 'price' in smart_name.lower() or 'budget' in smart_name.lower() or 'amount' in smart_name.lower():
                try:
                    if str(field_value).replace('.', '').replace(',', '').isdigit():
                        formatted_value = f"{float(field_value):,.0f}"
                except:
                    pass
        
        formatted_record.append({
            'field': field_name,
            'type': field_type,
            'value': field_value,
            'formatted_value': formatted_value,
            'display_name': smart_name,
            'original_name': field_name
        })
    
    return JsonResponse({
        'record': formatted_record,
        'database': {
            'name': database.name,
            'display_name': database.display_name,
            'description': database.description
        }
    })


@login_required
@require_http_methods(["POST"])
def sync_databases(request):
    """Sync available databases from MariaDB server"""
    if not has_owner_permission(request.user, 4):  # Manage permission
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Get available databases from MariaDB
        available_dbs = OwnerDatabase.get_available_databases()
        
        created_count = 0
        updated_count = 0
        
        # Database categories mapping
        db_categories = {
            'rehab': 'Real Estate - Major Developments',
            'marassi': 'Real Estate - Major Developments',
            'mivida': 'Real Estate - Major Developments',
            'palm': 'Real Estate - Major Developments',
            'uptown': 'Real Estate - Compound Projects',
            'amwaj': 'Real Estate - Compound Projects',
            'gouna': 'Real Estate - Regional Projects',
            'mangroovy': 'Real Estate - Regional Projects',
            'sahel': 'Real Estate - Regional Projects',
            'katameya': 'Real Estate - New Cairo/Tagamoa',
            'sabour': 'Real Estate - New Cairo/Tagamoa',
            'tagamoa': 'Real Estate - New Cairo/Tagamoa',
            'zayed': 'Real Estate - 6th October/Zayed',
            'october': 'Real Estate - 6th October/Zayed',
            'villas': 'Real Estate - 6th October/Zayed',
            'sodic': 'Real Estate - SODIC Projects',
            'jedar': 'Real Estate - Other Developments',
            'hadaeq': 'Real Estate - Other Developments',
            'alexandria': 'Real Estate - Other Developments',
            'emaar': 'Real Estate - Commercial/Corporate',
            'vip': 'Real Estate - Commercial/Corporate',
            'customer': 'Real Estate - Commercial/Corporate',
            'mawasem': 'Real Estate - Commercial/Corporate',
            'sea_shell': 'Real Estate - Commercial/Corporate',
            'jaguar': 'Automotive',
            'jeep': 'Automotive',
        }
        
        for db_name in available_dbs:
            # Determine category
            category = 'Uncategorized'
            for keyword, cat in db_categories.items():
                if keyword in db_name.lower():
                    category = cat
                    break
            
            # Create or update database record
            db_obj, created = OwnerDatabase.objects.get_or_create(
                name=db_name,
                defaults={
                    'display_name': '',  # Will be set below
                    'category': category,
                    'table_name': 'data',
                    'created_by': request.user,
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
            else:
                # Update category if changed
                if db_obj.category != category:
                    db_obj.category = category
                    db_obj.save()
                    updated_count += 1
            
            # Generate and set display name if not already set or needs update
            if not db_obj.display_name or db_obj.display_name == db_obj.name:
                db_obj.display_name = db_obj.generate_display_name()
                db_obj.save()
            
            # Update record count
            table_info = db_obj.get_table_info()
        
        return JsonResponse({
            'success': True,
            'message': f'Sync completed. Created: {created_count}, Updated: {updated_count}',
            'created': created_count,
            'updated': updated_count,
            'total_available': len(available_dbs)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error syncing databases: {str(e)}'
        }, status=500)
