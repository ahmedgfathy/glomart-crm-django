from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.forms.models import model_to_dict
from django.contrib.auth.models import User
import json
import csv
import io
from datetime import datetime

from .models import (
    Property, Region, FinishingType, UnitPurpose, PropertyType, 
    PropertyCategory, Compound, PropertyStatus, PropertyActivity, 
    PropertyHistory, UserPropertyPreferences
)
from .forms import PropertyCreateForm
from authentication.models import DataFilter, Module
from projects.models import Project, Currency


def apply_user_data_filters(user, queryset, model_name):
    """Apply user profile data filters to a queryset"""
    if not hasattr(user, 'user_profile') or not user.user_profile.profile:
        return queryset
    
    profile = user.user_profile.profile
    
    # Get data filters for this profile and model
    try:
        module = Module.objects.get(name='property')
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


@login_required
def property_list(request):
    """Display list of properties with search and filtering"""
    
    # Get all properties and apply user profile data filters
    properties = Property.objects.select_related(
        'region', 'property_type', 'category', 'status', 'activity',
        'compound', 'handler', 'sales_person'
    ).prefetch_related('assigned_users')
    
    # Apply user profile data filters first
    properties = apply_user_data_filters(request.user, properties, 'Property')
    
    # Apply search filters
    search_query = request.GET.get('search', '').strip()
    if search_query:
        properties = properties.filter(
            Q(property_id__icontains=search_query) |
            Q(property_number__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(region__name__icontains=search_query) |
            Q(compound__name__icontains=search_query) |
            Q(mobile_number__icontains=search_query)
        )
    
    # Apply filters
    region_id = request.GET.get('region')
    if region_id:
        properties = properties.filter(region_id=region_id)
    
    property_type_id = request.GET.get('property_type')
    if property_type_id:
        properties = properties.filter(property_type_id=property_type_id)
    
    status_id = request.GET.get('status')
    if status_id:
        properties = properties.filter(status_id=status_id)
    
    activity_id = request.GET.get('activity')
    if activity_id:
        properties = properties.filter(activity_id=activity_id)
    
    # Filter by price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        properties = properties.filter(total_price__gte=min_price)
    if max_price:
        properties = properties.filter(total_price__lte=max_price)
    
    # Filter by rooms
    rooms = request.GET.get('rooms')
    if rooms:
        properties = properties.filter(rooms=rooms)
    
    # TODO: Apply user-specific permissions (similar to leads)
    # For now, show all properties
    
    # Order by creation date (newest first)
    properties = properties.order_by('-created_at')
    
    # Pagination
    page_size = request.GET.get('page_size', 25)
    try:
        page_size = int(page_size)
        if page_size not in [10, 25, 50, 100]:
            page_size = 25
    except:
        page_size = 25
    
    paginator = Paginator(properties, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    regions = Region.objects.filter(is_active=True).order_by('name')
    property_types = PropertyType.objects.filter(is_active=True).order_by('name')
    statuses = PropertyStatus.objects.filter(is_active=True).order_by('name')
    activities = PropertyActivity.objects.filter(is_active=True).order_by('name')
    
    # Get user preferences
    user_preferences = UserPropertyPreferences.get_for_user(request.user)
    
    context = {
        'properties': page_obj,
        'total_properties': paginator.count,
        'search_query': search_query,
        'regions': regions,
        'property_types': property_types,
        'statuses': statuses,
        'activities': activities,
        'current_filters': {
            'region': region_id,
            'property_type': property_type_id,
            'status': status_id,
            'activity': activity_id,
            'min_price': min_price,
            'max_price': max_price,
            'rooms': rooms,
        },
        'page_size': page_size,
        'user_view_preference': user_preferences.view_mode,
    }
    
    return render(request, 'properties/property_list.html', context)


@login_required
def property_detail(request, property_id):
    """Display detailed view of a property"""
    property_obj = get_object_or_404(Property, property_id=property_id)
    
    # Get property history
    history = PropertyHistory.objects.filter(property=property_obj).order_by('-created_at')[:10]
    
    context = {
        'property': property_obj,
        'history': history,
    }
    
    return render(request, 'properties/property_detail.html', context)


@login_required
def property_search(request):
    """AJAX search for properties"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    properties = Property.objects.filter(
        Q(property_id__icontains=query) |
        Q(property_number__icontains=query) |
        Q(name__icontains=query)
    ).select_related('region', 'property_type', 'status')[:10]
    
    results = []
    for prop in properties:
        results.append({
            'id': prop.property_id,
            'text': f"{prop.property_number or prop.property_id} - {prop.name or 'Unnamed Property'}",
            'region': prop.region.name if prop.region else '',
            'type': prop.property_type.name if prop.property_type else '',
            'status': prop.status.name if prop.status else '',
            'price': str(prop.total_price) if prop.total_price else '',
        })
    
    return JsonResponse({'results': results})


@login_required
def property_create(request):
    """Create a new property"""
    if request.method == 'POST':
        form = PropertyCreateForm(request.POST)
        if form.is_valid():
            # Set the user before saving
            form.user = request.user
            property_obj = form.save()
            
            # Create history entry
            PropertyHistory.objects.create(
                property=property_obj,
                changed_by=request.user,
                change_type='created',
                new_values={'property_id': property_obj.property_id},
                notes=f'Property created by {request.user.username}'
            )
            
            messages.success(request, f'Property "{property_obj.name or property_obj.property_number}" created successfully!')
            return redirect('properties:property_detail', property_id=property_obj.property_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PropertyCreateForm()

    context = {
        'form': form,
    }
    
    return render(request, 'properties/property_create.html', context)


@login_required
def property_edit(request, property_id):
    """Edit an existing property"""
    property_obj = get_object_or_404(Property, property_id=property_id)
    
    if request.method == 'POST':
        form = PropertyCreateForm(request.POST, instance=property_obj)
        if form.is_valid():
            property_obj = form.save()
            messages.success(request, f'Property {property_obj.name} has been updated successfully!')
            return redirect('properties:property_detail', property_id=property_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PropertyCreateForm(instance=property_obj)
    
    # Get navigation properties (previous/next) with same filters as list view
    properties_queryset = Property.objects.select_related(
        'region', 'property_type', 'category', 'status', 'activity',
        'compound', 'handler', 'sales_person'
    ).prefetch_related('assigned_users')
    
    # Apply user profile data filters
    properties_queryset = apply_user_data_filters(request.user, properties_queryset, 'Property')
    
    # Order by creation date (same as list view)
    properties_queryset = properties_queryset.order_by('-created_at')
    
    # Get property IDs in order
    property_ids = list(properties_queryset.values_list('property_id', flat=True))
    
    # Find current property index
    try:
        current_index = property_ids.index(property_id)
        prev_property_id = property_ids[current_index + 1] if current_index + 1 < len(property_ids) else None
        next_property_id = property_ids[current_index - 1] if current_index > 0 else None
    except ValueError:
        # Property not found in filtered list
        prev_property_id = None
        next_property_id = None
    
    # Get all the context data needed for the form
    context = {
        'property': property_obj,
        'form': form,
        'prev_property_id': prev_property_id,
        'next_property_id': next_property_id,
        'current_index': property_ids.index(property_id) + 1 if property_id in property_ids else 0,
        'total_properties': len(property_ids),
        'regions': Region.objects.filter(is_active=True).order_by('name'),
        'finishing_types': FinishingType.objects.filter(is_active=True).order_by('name'),
        'unit_purposes': UnitPurpose.objects.filter(is_active=True).order_by('name'),
        'property_types': PropertyType.objects.filter(is_active=True).order_by('name'),
        'property_categories': PropertyCategory.objects.filter(is_active=True).order_by('name'),
        'compounds': Compound.objects.filter(is_active=True).order_by('name'),
        'property_statuses': PropertyStatus.objects.filter(is_active=True).order_by('name'),
        'activities': PropertyActivity.objects.filter(is_active=True).order_by('name'),
        'projects': Project.objects.filter(is_active=True).order_by('name'),
        'currencies': Currency.objects.filter(is_active=True).order_by('code'),
        'users': User.objects.filter(is_active=True).order_by('first_name', 'last_name'),
        'condition_choices': [
            ('excellent', 'Excellent'),
            ('very_good', 'Very Good'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('needs_renovation', 'Needs Renovation'),
        ],
        'furnishing_choices': [
            ('furnished', 'Fully Furnished'),
            ('semi_furnished', 'Semi Furnished'),
            ('unfurnished', 'Unfurnished'),
        ],
        'amenities': [
            ('parking', 'Parking'),
            ('pool', 'Swimming Pool'),
            ('gym', 'Gym'),
            ('garden', 'Garden'),
            ('elevator', 'Elevator'),
            ('security', '24/7 Security'),
            ('internet', 'High-Speed Internet'),
            ('ac', 'Air Conditioning'),
            ('heating', 'Central Heating'),
            ('balcony', 'Balcony'),
            ('terrace', 'Terrace'),
            ('garage', 'Private Garage'),
            ('storage', 'Storage Room'),
            ('concierge', 'Concierge Service'),
            ('laundry', 'Laundry Room'),
        ],
    }
    
    return render(request, 'properties/property_edit.html', context)


@login_required
def property_delete(request, property_id):
    """Delete a property"""
    property_obj = get_object_or_404(Property, property_id=property_id)
    
    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, f'Property {property_obj.property_number or property_obj.property_id} has been deleted.')
        return redirect('properties:property_list')
    
    context = {
        'property': property_obj,
    }
    
    return render(request, 'properties/property_delete.html', context)


@login_required
def property_like(request, property_id):
    """Toggle property like status"""
    property_obj = get_object_or_404(Property, property_id=property_id)
    
    property_obj.is_liked = not property_obj.is_liked
    property_obj.save()
    
    # Create history entry
    PropertyHistory.objects.create(
        property=property_obj,
        changed_by=request.user,
        change_type='liked' if property_obj.is_liked else 'unliked',
        notes=f'Property {"liked" if property_obj.is_liked else "unliked"} by {request.user.get_full_name() or request.user.username}'
    )
    
    return JsonResponse({
        'success': True,
        'liked': property_obj.is_liked,
        'message': f'Property {"liked" if property_obj.is_liked else "unliked"} successfully'
    })


@login_required
def property_assign(request, property_id):
    """Assign property to users"""
    property_obj = get_object_or_404(Property, property_id=property_id)
    
    if request.method == 'POST':
        user_ids = request.POST.getlist('user_ids')
        users = User.objects.filter(id__in=user_ids)
        
        property_obj.assigned_users.set(users)
        
        # Create history entry
        PropertyHistory.objects.create(
            property=property_obj,
            changed_by=request.user,
            change_type='assigned',
            notes=f'Property assigned to {", ".join([u.get_full_name() or u.username for u in users])}'
        )
        
        messages.success(request, 'Property assignment updated successfully.')
        return redirect('properties:property_detail', property_id=property_id)
    
    # Get all users for assignment
    users = User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username')
    
    context = {
        'property': property_obj,
        'users': users,
        'assigned_user_ids': list(property_obj.assigned_users.values_list('id', flat=True)),
    }
    
    return render(request, 'properties/property_assign.html', context)


@login_required
def property_export(request):
    """Export properties to CSV"""
    # Get filtered properties (same filters as list view)
    properties = Property.objects.select_related(
        'region', 'property_type', 'category', 'status', 'activity',
        'compound', 'handler', 'sales_person'
    )
    
    # Apply same filters as list view
    search_query = request.GET.get('search', '').strip()
    if search_query:
        properties = properties.filter(
            Q(property_id__icontains=search_query) |
            Q(property_number__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply other filters...
    region_id = request.GET.get('region')
    if region_id:
        properties = properties.filter(region_id=region_id)
    
    property_type_id = request.GET.get('property_type')
    if property_type_id:
        properties = properties.filter(property_type_id=property_type_id)
    
    status_id = request.GET.get('status')
    if status_id:
        properties = properties.filter(status_id=status_id)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="properties_export.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Property ID', 'Property Number', 'Name', 'Region', 'Type', 'Category',
        'Status', 'Activity', 'Compound', 'Total Price', 'Rooms', 'Bathrooms',
        'Total Space', 'Handler', 'Created At'
    ])
    
    # Write data
    for prop in properties:
        writer.writerow([
            prop.property_id,
            prop.property_number or '',
            prop.name or '',
            prop.region.name if prop.region else '',
            prop.property_type.name if prop.property_type else '',
            prop.category.name if prop.category else '',
            prop.status.name if prop.status else '',
            prop.activity.name if prop.activity else '',
            prop.compound.name if prop.compound else '',
            prop.total_price or '',
            prop.rooms or '',
            prop.bathrooms or '',
            prop.total_space or '',
            prop.handler.get_full_name() if prop.handler else '',
            prop.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    
    return response


# API endpoints for dynamic loading
@login_required
def api_regions(request):
    """Get regions as JSON"""
    regions = Region.objects.filter(is_active=True).order_by('name')
    data = [{'id': r.id, 'name': r.name} for r in regions]
    return JsonResponse({'regions': data})


@login_required
def api_compounds(request):
    """Get compounds as JSON"""
    compounds = Compound.objects.filter(is_active=True).order_by('name')
    data = [{'id': c.id, 'name': c.name, 'location': c.location} for c in compounds]
    return JsonResponse({'compounds': data})


@login_required
def property_images_api(request, property_id):
    """Get all images for a property as JSON"""
    try:
        property_obj = get_object_or_404(Property, property_id=property_id)
        images = property_obj.get_all_image_urls()
        return JsonResponse({'images': images})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def property_import(request):
    """Import properties from CSV file"""
    if request.method == 'POST':
        try:
            # Get uploaded file
            file = request.FILES.get('file')
            
            if not file:
                return JsonResponse({'success': False, 'error': 'Please select a file to upload.'})
            
            # Check file extension
            if not file.name.lower().endswith(('.csv', '.xlsx', '.xls')):
                return JsonResponse({'success': False, 'error': 'Please upload a valid CSV or Excel file.'})
            
            # Handle Excel files
            if file.name.lower().endswith(('.xlsx', '.xls')):
                try:
                    import pandas as pd
                    df = pd.read_excel(file)
                    # Convert to CSV format for processing
                    csv_string = df.to_csv(index=False)
                    file_data = csv_string
                except ImportError:
                    return JsonResponse({'success': False, 'error': 'Excel support not available. Please use CSV format.'})
            else:
                # Handle CSV files
                file_data = file.read().decode('utf-8')
            
            # Parse CSV data
            csv_data = csv.reader(io.StringIO(file_data))
            
            # Get headers
            headers = next(csv_data)
            headers = [h.strip().lower() for h in headers]
            
            # Get default values
            default_currency = Currency.objects.first()
            default_status = PropertyStatus.objects.filter(name__icontains='available').first() or PropertyStatus.objects.first()
            default_activity = PropertyActivity.objects.filter(name__icontains='sale').first() or PropertyActivity.objects.first()
            default_category = PropertyCategory.objects.filter(name__icontains='residential').first() or PropertyCategory.objects.first()
            
            imported_count = 0
            error_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_data, start=2):
                try:
                    if len(row) < 3:  # Minimum required fields
                        continue
                    
                    # Create dictionary from row data
                    row_data = {}
                    for i, value in enumerate(row):
                        if i < len(headers):
                            row_data[headers[i]] = value.strip() if value else ''
                    
                    # Extract required fields
                    title = row_data.get('title', '')
                    description = row_data.get('description', '')
                    price_str = row_data.get('price', '0')
                    
                    # Skip if missing essential data
                    if not title or not description:
                        errors.append(f"Row {row_num}: Missing required fields (title or description)")
                        error_count += 1
                        continue
                    
                    # Parse price
                    try:
                        price = float(price_str.replace(',', '').replace('$', '').strip()) if price_str else 0
                    except ValueError:
                        price = 0
                    
                    # Get or create lookup values
                    property_type = None
                    if row_data.get('property_type'):
                        property_type = PropertyType.objects.filter(name__icontains=row_data['property_type']).first()
                    
                    region = None
                    if row_data.get('region'):
                        region = Region.objects.filter(name__icontains=row_data['region']).first()
                    
                    # Generate unique property number if not provided
                    property_number = row_data.get('property_number', '')
                    if not property_number:
                        property_number = f"PROP{datetime.now().strftime('%Y%m%d')}{imported_count + 1:04d}"
                    
                    # Check if property already exists
                    if Property.objects.filter(property_number=property_number).exists():
                        errors.append(f"Row {row_num}: Property {property_number} already exists")
                        error_count += 1
                        continue
                    
                    # Create property
                    property_obj = Property.objects.create(
                        property_number=property_number,
                        title=title,
                        description=description,
                        price=price,
                        currency=default_currency,
                        property_type=property_type,
                        category=default_category,
                        status=default_status,
                        activity=default_activity,
                        region=region,
                        address=row_data.get('address', ''),
                        city=row_data.get('city', ''),
                        bedrooms=int(row_data.get('bedrooms', 0)) if row_data.get('bedrooms', '').isdigit() else None,
                        bathrooms=int(row_data.get('bathrooms', 0)) if row_data.get('bathrooms', '').isdigit() else None,
                        area_sqft=float(row_data.get('area_sqft', 0)) if row_data.get('area_sqft', '').replace('.', '').isdigit() else None,
                        features=row_data.get('features', ''),
                        amenities=row_data.get('amenities', ''),
                        created_by=request.user,
                        assigned_to=request.user
                    )
                    
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    error_count += 1
                    continue
            
            # Prepare response
            response_data = {
                'success': True,
                'imported_count': imported_count,
                'error_count': error_count
            }
            
            if errors:
                response_data['errors'] = errors[:10]  # Limit to first 10 errors
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Import failed: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def save_view_preference(request):
    """Save user's preferred view mode (grid/list)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            view_mode = data.get('view_mode')
            
            if view_mode not in ['grid', 'list']:
                return JsonResponse({'success': False, 'error': 'Invalid view mode'})
            
            # Get or create user preferences
            preferences = UserPropertyPreferences.get_for_user(request.user)
            preferences.view_mode = view_mode
            preferences.save()
            
            return JsonResponse({'success': True, 'view_mode': view_mode})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
