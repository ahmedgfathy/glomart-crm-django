from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserCreationForm
from django import forms
import json

from .models import Module, Permission, Rule, Profile, UserProfile, UserActivity, FieldPermission, DataFilter, DynamicDropdown


def login_view(request):
    """Login view for users"""
    if request.user.is_authenticated:
        return redirect('authentication:dashboard')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Log user activity
            UserActivity.objects.create(
                user=user,
                activity_type='login',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            return redirect('authentication:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'authentication/login.html')


def logout_view(request):
    """Logout view for users"""
    if request.user.is_authenticated:
        UserActivity.objects.create(
            user=request.user,
            activity_type='logout',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    logout(request)
    
    # Clear ALL existing messages to prevent clutter on login page
    storage = messages.get_messages(request)
    storage.used = True  # Mark all messages as used/consumed
    
    # Add only a clean logout message
    messages.success(request, 'You have been successfully logged out.')
    return redirect('authentication:login')


@login_required
def dashboard_view(request):
    """Dashboard view after successful login"""
    try:
        user_profile = request.user.user_profile
        accessible_modules = user_profile.get_accessible_modules()
    except UserProfile.DoesNotExist:
        accessible_modules = Module.objects.none()
        messages.warning(request, 'No profile assigned. Contact administrator.')
    
    # Get real statistics from database
    from properties.models import Property
    from leads.models import Lead
    from projects.models import Project
    
    # Property statistics
    total_properties = Property.objects.count()
    
    # Count residential and commercial properties
    residential_count = Property.objects.filter(
        Q(property_type__name__icontains='residential') |
        Q(property_type__name__icontains='apartment') |
        Q(property_type__name__icontains='villa') |
        Q(property_type__name__icontains='house') |
        Q(property_type__name__icontains='flat')
    ).count()
    
    commercial_count = Property.objects.filter(
        Q(property_type__name__icontains='commercial') |
        Q(property_type__name__icontains='office') |
        Q(property_type__name__icontains='retail') |
        Q(property_type__name__icontains='warehouse') |
        Q(property_type__name__icontains='shop')
    ).count()
    
    # Count medical and office properties specifically
    medical_count = Property.objects.filter(
        Q(property_type__name__icontains='medical') |
        Q(property_type__name__icontains='clinic') |
        Q(property_type__name__icontains='hospital') |
        Q(property_type__name__icontains='pharmacy') |
        Q(property_type__name__icontains='healthcare')
    ).count()
    
    office_count = Property.objects.filter(
        Q(property_type__name__icontains='office') |
        Q(property_type__name__icontains='workspace') |
        Q(property_type__name__icontains='coworking') |
        Q(property_type__name__icontains='business center')
    ).count()
    
    # Lead statistics (as active clients)
    # Count leads that are not in final status (Won/Lost) - these are "active" leads
    from leads.models import LeadStatus
    active_leads = Lead.objects.filter(
        status__is_final=False,
        status__is_active=True
    ).count()
    
    # If no leads have status set, count total leads
    if active_leads == 0:
        active_leads = Lead.objects.count()    # Project statistics
    total_projects = Project.objects.filter(is_active=True).count()
    active_projects = Project.objects.filter(is_active=True, status__name='active').count()
    
    # Pending deals (leads in negotiation or similar status)
    pending_deals = Lead.objects.filter(
        Q(status__name__icontains='negotiation') | 
        Q(status__name__icontains='pending') |
        Q(status__name__icontains='follow')
    ).count()
    
    # Calculate total property value (portfolio value)
    total_property_value = Property.objects.aggregate(
        total=Sum('total_price')
    )['total'] or 0
    
    # Also calculate average property value
    avg_property_value = 0
    if total_properties > 0 and total_property_value > 0:
        avg_property_value = total_property_value / total_properties
    else:
        avg_property_value = 0
    
    # Format the total value for display
    if total_property_value > 1000000:
        monthly_revenue = f"{total_property_value/1000000:.1f}M"
    elif total_property_value > 1000:
        monthly_revenue = f"{total_property_value/1000:.0f}K"
    else:
        monthly_revenue = f"{total_property_value:.0f}"
    
    # Recent activities from UserActivity
    recent_activities = UserActivity.objects.select_related('user').order_by('-timestamp')[:5]
    
    # Field permissions statistics
    from .models import FieldPermission, Profile
    total_field_permissions = FieldPermission.objects.count()
    profiles_count = Profile.objects.count()
    active_field_permissions = FieldPermission.objects.filter(can_view=True).count()
    
    # User statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    residential_users = UserProfile.objects.filter(
        profile__name='Residential Users Profile'
    ).count()
    
    # Owner database functionality has been removed
    
    context = {
        'user': request.user,
        'accessible_modules': accessible_modules,
        'total_properties': total_properties,
        'total_projects': total_projects,
        'active_leads': active_leads,
        'active_projects': active_projects,
        'pending_deals': pending_deals,
        'monthly_revenue': monthly_revenue,
        'residential_count': residential_count,
        'commercial_count': commercial_count,
        'medical_count': medical_count,
        'office_count': office_count,
        'recent_activities': recent_activities,
        # Field permissions stats
        'total_field_permissions': total_field_permissions,
        'profiles_count': profiles_count,
        'active_field_permissions': active_field_permissions,
        # User stats
        'total_users': total_users,
        'active_users': active_users,
        'residential_users': residential_users,
        'active_field_permissions': active_field_permissions,
        # Additional analytics
        'total_property_value': total_property_value,
        'avg_property_value': avg_property_value,
        'conversion_rate': round((active_leads / max(total_properties, 1)) * 100, 1) if total_properties > 0 and active_leads >= 0 else 0,
        'properties_per_user': round(total_properties / max(total_users, 1), 1) if total_users > 0 and total_properties >= 0 else 0,
        # Owner database stats
    }
    
    return render(request, 'authentication/dashboard.html', context)


@login_required
def user_management_view(request):
    """User management interface"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('authentication:dashboard')
    
    search_query = request.GET.get('search', '').strip()
    profile_filter = request.GET.get('profile', '').strip()
    users = User.objects.select_related('user_profile__profile').all()
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    if profile_filter:
        try:
            users = users.filter(user_profile__profile_id=int(profile_filter))
        except (ValueError, TypeError):
            profile_filter = ''
    
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    profiles = Profile.objects.filter(is_active=True)
    
    return render(request, 'authentication/user_management.html', {
        'users': users_page,
        'profiles': profiles,
        'search_query': search_query,
        'selected_profile': profile_filter
    })

@login_required
def profile_detail_view(request, profile_id):
    """Profile detail with permission management"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('authentication:dashboard')
    
    profile = get_object_or_404(Profile, id=profile_id)
    
    # Filter out modules where Django app doesn't exist
    # This prevents errors when modules are deleted from codebase but still in DB
    from django.apps import apps
    all_modules = Module.objects.filter(is_active=True).prefetch_related('permissions')
    
    # Whitelist of known good modules (even if Django app name differs slightly)
    valid_modules = []
    installed_apps = [app.label for app in apps.get_app_configs()]
    
    for module in all_modules:
        module_name = module.name.lower()
        
        # Try exact match first
        if module_name in installed_apps:
            valid_modules.append(module)
            continue
        
        # Try adding 's' for plural (lead -> leads)
        if module_name + 's' in installed_apps:
            valid_modules.append(module)
            continue
        
        # Try removing 's' for singular (leads -> lead)
        if module_name.endswith('s') and module_name[:-1] in installed_apps:
            valid_modules.append(module)
            continue
        
        # Try y -> ies transformation (property -> properties)
        if module_name.endswith('y') and module_name[:-1] + 'ies' in installed_apps:
            valid_modules.append(module)
            continue
        
        # Try ies -> y transformation (properties -> property)
        if module_name.endswith('ies') and module_name[:-3] + 'y' in installed_apps:
            valid_modules.append(module)
            continue
        
        # Check if any installed app name contains this module name
        if any(module_name in app or app in module_name for app in installed_apps if not app.startswith('django')):
            valid_modules.append(module)
            continue
        
        print(f"⚠️ Skipping module '{module.name}' ({module.display_name}) - no matching Django app found")
    
    modules = valid_modules
    
    # Get current permissions for this profile
    current_permissions = {}
    for perm in profile.permissions.all():
        module_name = perm.module.name
        if module_name not in current_permissions:
            current_permissions[module_name] = 0
        current_permissions[module_name] = max(current_permissions[module_name], perm.level)
    
    # Convert to JSON for JavaScript
    import json
    current_permissions_json = json.dumps(current_permissions)
    
    # Get Data Filters for this profile
    data_filters = DataFilter.objects.filter(profile=profile).select_related('module').order_by('module__name', 'order')
    
    # Get Dynamic Dropdowns for this profile
    dropdown_restrictions = DynamicDropdown.objects.filter(profile=profile).select_related('module').order_by('module__name', 'order')
    
    return render(request, 'authentication/profile_detail.html', {
        'profile': profile,
        'modules': modules,
        'current_permissions': current_permissions,
        'current_permissions_json': current_permissions_json,
        'data_filters': data_filters,
        'dropdown_restrictions': dropdown_restrictions,
    })


@csrf_exempt
@login_required
def update_profile_permissions(request, profile_id):
    """Update profile permissions via AJAX"""
    print(f"🔍 Permission update request received: method={request.method}, user={request.user.username}, is_superuser={request.user.is_superuser}")
    print(f"🔍 Request headers: {dict(request.headers)}")
    print(f"🔍 Request body: {request.body}")
    
    if not request.user.is_superuser:
        print(f"❌ Access denied: User {request.user.username} is not a superuser")
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method != 'POST':
        print(f"❌ Invalid method: {request.method}")
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        import json
        profile = get_object_or_404(Profile, id=profile_id)
        data = json.loads(request.body)
        
        # Check if this is a field permissions save request
        action = data.get('action')
        
        if action == 'save_field_permissions':
            # Handle field permissions
            field_permissions = data.get('field_permissions', [])
            
            print(f"📋 Saving field permissions: profile_id={profile_id}, count={len(field_permissions)}")
            
            for field_perm in field_permissions:
                module_name = field_perm.get('module')
                model_name = field_perm.get('model')
                field_name = field_perm.get('field')
                can_view = field_perm.get('can_view', False)
                can_edit = field_perm.get('can_edit', False)
                
                try:
                    module = Module.objects.get(name=module_name)
                    
                    # Update or create field permission
                    FieldPermission.objects.update_or_create(
                        profile=profile,
                        module=module,
                        model_name=model_name,
                        field_name=field_name,
                        defaults={
                            'can_view': can_view,
                            'can_edit': can_edit,
                            'can_filter': can_view,  # If can view, can filter
                            'is_visible_in_list': can_view,
                            'is_visible_in_detail': can_view,
                            'is_visible_in_forms': can_edit,
                            'is_active': True
                        }
                    )
                except Module.DoesNotExist:
                    print(f"⚠️ Module not found: {module_name}")
                    continue
            
            print(f"✅ Successfully saved {len(field_permissions)} field permissions")
            return JsonResponse({
                'success': True, 
                'message': f'Saved {len(field_permissions)} field permissions'
            })
        
        # Handle module permissions (existing logic)
        module_name = data.get('module')
        permission_level = int(data.get('level', 0))
        
        print(f"📋 Processing: profile_id={profile_id}, module={module_name}, level={permission_level}")
        
        module = get_object_or_404(Module, name=module_name)
        
        # Remove existing permissions for this module
        existing_permissions = profile.permissions.filter(module=module)
        print(f"🗑️ Removing {existing_permissions.count()} existing permissions")
        profile.permissions.remove(*existing_permissions)
        
        # Add new permissions up to the specified level
        if permission_level > 0:
            permissions_to_add = Permission.objects.filter(
                module=module,
                level__lte=permission_level,
                is_active=True
            )
            print(f"➕ Adding {permissions_to_add.count()} permissions")
            profile.permissions.add(*permissions_to_add)
        
        print(f"✅ Successfully updated permissions for {module_name} to level {permission_level}")
        return JsonResponse({'success': True, 'message': 'Permissions updated successfully'})
        
    except Exception as e:
        import traceback
        print(f"❌ ERROR: Error updating permissions: {str(e)}")
        print(f"❌ ERROR: Traceback: {traceback.format_exc()}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
def get_module_fields(request, profile_id, module_name):
    """Get all model fields for a specific module to display field permissions"""
    print(f"🔍 get_module_fields called: profile_id={profile_id}, module_name={module_name}")
    
    if not request.user.is_superuser:
        print(f"❌ Access denied: user {request.user.username} is not superuser")
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        from django.apps import apps
        profile = get_object_or_404(Profile, id=profile_id)
        print(f"✅ Profile found: {profile.name}")
        
        module = get_object_or_404(Module, name=module_name)
        print(f"✅ Module found: {module.display_name}")
        
        # Get all models for this module
        # Try to find the Django app with name variations
        app_config = None
        app_name_to_use = module_name
        
        # Try exact match first
        try:
            app_config = apps.get_app_config(module_name)
            print(f"✅ App config found for {module_name} (exact match)")
        except LookupError:
            # Try with 's' added (property -> properties)
            try:
                app_config = apps.get_app_config(module_name + 's')
                app_name_to_use = module_name + 's'
                print(f"✅ App config found for {app_name_to_use} (plural)")
            except LookupError:
                # Try without 's' (leads -> lead)
                if module_name.endswith('s'):
                    try:
                        app_config = apps.get_app_config(module_name[:-1])
                        app_name_to_use = module_name[:-1]
                        print(f"✅ App config found for {app_name_to_use} (singular)")
                    except LookupError:
                        pass
                
                # Try y -> ies (property -> properties)
                if not app_config and module_name.endswith('y'):
                    try:
                        app_config = apps.get_app_config(module_name[:-1] + 'ies')
                        app_name_to_use = module_name[:-1] + 'ies'
                        print(f"✅ App config found for {app_name_to_use} (y->ies)")
                    except LookupError:
                        pass
        
        if not app_config:
            error_msg = f'Django app not found for module "{module_name}". This module may have been deleted from the codebase.'
            print(f"❌ {error_msg}")
            return JsonResponse({'error': error_msg}, status=404)
        
        models_data = []
        
        for model in app_config.get_models():
            # Skip through models, history models, and preference models
            model_name = model._meta.model_name
            if model_name and ('through' in model_name or 'history' in model_name or 'preferences' in model_name or 'audit' in model_name):
                continue
            
            fields_data = []
            
            # Get all fields except many-to-many and reverse relations
            for field in model._meta.get_fields():
                if field.many_to_many or field.one_to_many:
                    continue
                
                # Get existing field permission if any
                try:
                    field_perm = FieldPermission.objects.get(
                        profile=profile,
                        module=module,
                        model_name=model.__name__,
                        field_name=field.name
                    )
                    can_view = field_perm.can_view
                    can_edit = field_perm.can_edit
                except FieldPermission.DoesNotExist:
                    # Default: all fields visible and editable
                    can_view = True
                    can_edit = True
                
                field_info = {
                    'name': field.name,
                    'verbose_name': getattr(field, 'verbose_name', field.name).title(),
                    'field_type': field.get_internal_type() if hasattr(field, 'get_internal_type') else 'Unknown',
                    'can_view': can_view,
                    'can_edit': can_edit,
                    'is_required': not getattr(field, 'blank', True) if hasattr(field, 'blank') else False,
                }
                
                fields_data.append(field_info)
            
            if fields_data:  # Only include models that have fields
                verbose_name = model._meta.verbose_name
                model_verbose_name = verbose_name.title() if verbose_name else model.__name__
                models_data.append({
                    'model_name': model.__name__,
                    'model_verbose_name': model_verbose_name,
                    'fields': fields_data
                })
        
        print(f"✅ Found {len(models_data)} models with fields for {module_name}")
        
        return JsonResponse({
            'success': True,
            'module': module_name,
            'models': models_data
        })
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"❌ Error getting module fields: {error_msg}")
        print(f"❌ Traceback: {traceback_str}")
        return JsonResponse({
            'success': False,
            'error': error_msg,
            'traceback': traceback_str if request.user.is_superuser else None
        }, status=500)


@login_required
def assign_user_profile_view(request, user_id):
    """Assign profile to user"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('authentication:dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        profile_id = request.POST.get('profile')
        
        # Get or create user profile
        user_profile, created = UserProfile.objects.get_or_create(user=user)
        
        if profile_id:
            profile = get_object_or_404(Profile, id=profile_id)
            user_profile.profile = profile
            user_profile.created_by = request.user
            user_profile.save()
            messages.success(request, f'Profile "{profile.name}" assigned to {user.username}')
        else:
            user_profile.profile = None
            user_profile.save()
            messages.success(request, f'Profile removed from {user.username}')
        
        return redirect('authentication:users')
    
    profiles = Profile.objects.filter(is_active=True)
    try:
        current_profile = user.user_profile.profile
    except UserProfile.DoesNotExist:
        current_profile = None
    
    return render(request, 'authentication/assign_profile.html', {
        'user': user,
        'profiles': profiles,
        'current_profile': current_profile
    })


# Custom User Creation Form
class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    profile = forms.ModelChoiceField(
        queryset=Profile.objects.filter(is_active=True),
        required=False,
        empty_label="No Profile",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Sales, Marketing, Finance'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            # Create user profile
            profile = self.cleaned_data.get('profile')
            department = self.cleaned_data.get('department', '')
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            user_profile.profile = profile
            user_profile.department = department
            user_profile.save()
        return user


@login_required
def create_user_view(request):
    """Create new user with profile assignment"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('authentication:dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserActivity.objects.create(
                user=request.user,
                activity_type='user_created',
                description=f'Created user: {user.username}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            messages.success(request, f'User "{user.username}" created successfully!')
            return redirect('authentication:users')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'authentication/create_user.html', {'form': form})


@login_required
def edit_user_view(request, user_id):
    """Edit existing user"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('authentication:dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.is_active = 'is_active' in request.POST
        
        # Handle profile assignment
        profile_id = request.POST.get('profile')
        department = request.POST.get('department', '')
        user_profile, created = UserProfile.objects.get_or_create(user=user)
        
        if profile_id:
            profile = get_object_or_404(Profile, id=profile_id)
            user_profile.profile = profile
        else:
            user_profile.profile = None
        
        user_profile.department = department
        user_profile.save()
        
        user.save()
        
        UserActivity.objects.create(
            user=request.user,
            activity_type='user_updated',
            description=f'Updated user: {user.username}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(request, f'User "{user.username}" updated successfully!')
        return redirect('authentication:users')
    
    profiles = Profile.objects.filter(is_active=True)
    try:
        current_profile = user.user_profile.profile
    except UserProfile.DoesNotExist:
        current_profile = None
    
    return render(request, 'authentication/edit_user.html', {
        'user': user,
        'profiles': profiles,
        'current_profile': current_profile
    })


@login_required
@require_POST
def toggle_user_status(request, user_id):
    """Toggle user active/inactive status"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    user = get_object_or_404(User, id=user_id)
    
    # Prevent self-deactivation
    if user == request.user and user.is_active:
        return JsonResponse({
            'success': False, 
            'message': 'You cannot deactivate your own account'
        })
    
    # Prevent deactivating the last admin
    if user.is_superuser and user.is_active:
        active_admin_count = User.objects.filter(is_superuser=True, is_active=True).count()
        if active_admin_count <= 1:
            return JsonResponse({
                'success': False,
                'message': 'Cannot deactivate the last active administrator'
            })
    
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    
    try:
        user_profile = user.user_profile
    except UserProfile.DoesNotExist:
        user_profile = None
    
    if user_profile:
        user_profile.is_active = user.is_active
        user_profile.save(update_fields=['is_active'])
    
    UserActivity.objects.create(
        user=request.user,
        activity_type='user_status_changed',
        description=f'{"Activated" if user.is_active else "Deactivated"} user: {user.username}',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return JsonResponse({
        'success': True,
        'is_active': user.is_active,
        'profile_is_active': user_profile.is_active if user_profile else None,
        'message': f'User {"activated" if user.is_active else "deactivated"} successfully'
    })


@login_required  
def delete_user_view(request, user_id):
    """Delete user (admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('authentication:dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    # Prevent self-deletion
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('authentication:users')
    
    # Prevent deletion of the last admin account
    if user.is_superuser:
        admin_count = User.objects.filter(is_superuser=True, is_active=True).count()
        if admin_count <= 1:
            messages.error(request, 'Cannot delete the last administrator account. System must have at least one active admin.')
            return redirect('authentication:users')
    
    if request.method == 'POST':
        # Double-check admin count before deletion
        if user.is_superuser:
            admin_count = User.objects.filter(is_superuser=True, is_active=True).count()
            if admin_count <= 1:
                messages.error(request, 'Cannot delete the last administrator account. System must have at least one active admin.')
                return redirect('authentication:users')
        
        username = user.username
        UserActivity.objects.create(
            user=request.user,
            activity_type='user_deleted',
            description=f'Deleted user: {username}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        user.delete()
        messages.success(request, f'User "{username}" deleted successfully!')
        return redirect('authentication:users')
    
    # Check if this user is the last admin for template context
    is_last_admin = False
    if user.is_superuser:
        admin_count = User.objects.filter(is_superuser=True, is_active=True).count()
        is_last_admin = admin_count <= 1
    
    return render(request, 'authentication/delete_user.html', {
        'user': user,
        'is_last_admin': is_last_admin
    })


@login_required
def profiles_view(request):
    """Profile management view"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('authentication:dashboard')
    
    profiles = Profile.objects.all().order_by('name')
    
    return render(request, 'authentication/profiles.html', {
        'profiles': profiles
    })


@login_required
def create_profile_view(request):
    """Create new profile"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('authentication:dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        
        if not name:
            messages.error(request, 'Profile name is required.')
            return render(request, 'authentication/create_profile.html')
        
        if Profile.objects.filter(name=name).exists():
            messages.error(request, 'A profile with this name already exists.')
            return render(request, 'authentication/create_profile.html')
        
        profile = Profile.objects.create(
            name=name,
            description=description,
            is_active=is_active
        )
        
        UserActivity.objects.create(
            user=request.user,
            activity_type='profile_created',
            description=f'Created profile: {name}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(request, f'Profile "{name}" created successfully!')
        return redirect('authentication:profile_detail', profile_id=profile.id)
    
    return render(request, 'authentication/create_profile.html')


@login_required
def edit_profile_view(request, profile_id):
    """Edit profile details"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('authentication:dashboard')
    
    profile = get_object_or_404(Profile, id=profile_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        
        if not name:
            messages.error(request, 'Profile name is required.')
            return render(request, 'authentication/edit_profile.html', {'profile': profile})
        
        if Profile.objects.filter(name=name).exclude(id=profile.id).exists():
            messages.error(request, 'A profile with this name already exists.')
            return render(request, 'authentication/edit_profile.html', {'profile': profile})
        
        profile.name = name
        profile.description = description
        profile.is_active = is_active
        profile.save()
        
        UserActivity.objects.create(
            user=request.user,
            activity_type='profile_updated',
            description=f'Updated profile: {name}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(request, f'Profile "{name}" updated successfully!')
        return redirect('authentication:profile_detail', profile_id=profile.id)
    
    return render(request, 'authentication/edit_profile.html', {'profile': profile})


@login_required
def delete_profile_view(request, profile_id):
    """Delete profile"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('authentication:dashboard')
    
    profile = get_object_or_404(Profile, id=profile_id)
    
    # Check if profile is in use
    users_count = profile.userprofile_set.count()
    
    if request.method == 'POST':
        if users_count > 0:
            messages.error(request, f'Cannot delete profile "{profile.name}". It is assigned to {users_count} user(s). Please reassign these users first.')
            return redirect('authentication:profiles')
        
        profile_name = profile.name
        UserActivity.objects.create(
            user=request.user,
            activity_type='profile_deleted',
            description=f'Deleted profile: {profile_name}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        profile.delete()
        messages.success(request, f'Profile "{profile_name}" deleted successfully!')
        return redirect('authentication:profiles')
    
    return render(request, 'authentication/delete_profile.html', {
        'profile': profile,
        'users_count': users_count
    })


@login_required
def view_user_profile(request, user_id):
    """View user profile details"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('authentication:dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    # Get user activity (recent 10 activities)
    recent_activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:10]
    
    return render(request, 'authentication/view_user_profile.html', {
        'user': user,
        'recent_activities': recent_activities
    })


def auth_check_view(request):
    """Check authentication status"""
    return render(request, 'authentication/auth_check.html')


@csrf_exempt
@login_required
def get_model_fields_for_filter(request, module_name):
    """Get all fields for a model to use in filter builder"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        from django.apps import apps
        
        # Map module names to app names and model names
        model_map = {
            'leads': ('leads', 'Lead'),
            'properties': ('properties', 'Property'),
            'projects': ('projects', 'Project'),
            'authentication': ('authentication', 'User'),
        }
        
        module_lower = module_name.lower()
        if module_lower not in model_map:
            return JsonResponse({'error': f'Unknown module: {module_name}'}, status=400)
        
        app_label, model_name = model_map[module_lower]
        
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            return JsonResponse({'error': f'Model not found: {app_label}.{model_name}'}, status=404)
        
        # Get all fields from the model
        fields_list = []
        
        # Get regular fields
        for field in model._meta.get_fields():
            field_name = field.name
            field_type = field.get_internal_type() if hasattr(field, 'get_internal_type') else 'Unknown'
            
            # Skip reverse relations
            if field.auto_created and not field.concrete:
                continue
            
            # Determine field category and suggested operators
            if field_type in ['CharField', 'TextField', 'EmailField', 'URLField', 'SlugField']:
                category = 'text'
                operators = ['__icontains', '__exact', '__startswith', '__endswith', '__in']
            elif field_type in ['IntegerField', 'BigIntegerField', 'SmallIntegerField', 'PositiveIntegerField', 
                               'FloatField', 'DecimalField']:
                category = 'number'
                operators = ['__exact', '__gt', '__gte', '__lt', '__lte', '__in']
            elif field_type in ['BooleanField', 'NullBooleanField']:
                category = 'boolean'
                operators = ['__exact']
            elif field_type in ['DateField', 'DateTimeField']:
                category = 'date'
                operators = ['__exact', '__gt', '__gte', '__lt', '__lte', '__year', '__month', '__day']
            elif field_type in ['ForeignKey', 'OneToOneField']:
                category = 'relation'
                operators = ['__exact', '__in']
                # Add related field lookups
                related_model = field.related_model
                field_name = field.name
                # Add base relation
                fields_list.append({
                    'value': f'{field_name}',
                    'label': f'{field.verbose_name.title()} (ID)',
                    'type': category,
                    'operators': operators
                })
                # Add common related field lookups
                if hasattr(related_model, 'name'):
                    fields_list.append({
                        'value': f'{field_name}__name',
                        'label': f'{field.verbose_name.title()} → Name',
                        'type': 'text',
                        'operators': ['__icontains', '__exact', '__in'],
                        'has_choices': True  # Flag for frontend to show dropdown
                    })
                if hasattr(related_model, 'username'):
                    fields_list.append({
                        'value': f'{field_name}__username',
                        'label': f'{field.verbose_name.title()} → Username',
                        'type': 'text',
                        'operators': ['__icontains', '__exact'],
                        'has_choices': True  # Flag for frontend to show dropdown
                    })
                continue
            elif field_type == 'ManyToManyField':
                category = 'relation_many'
                operators = ['__in']
            else:
                category = 'other'
                operators = ['__exact', '__icontains']
            
            # Get verbose name or use field name
            verbose_name = getattr(field, 'verbose_name', field_name)
            label = verbose_name.title() if verbose_name else field_name.replace('_', ' ').title()
            
            fields_list.append({
                'value': field_name,
                'label': label,
                'type': category,
                'operators': operators
            })
        
        return JsonResponse({
            'success': True,
            'model': model_name,
            'fields': fields_list
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
def get_field_choices(request, module_name, field_name):
    """Get available choices/values for a specific field (especially ForeignKey fields)"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        from django.apps import apps
        
        # Map module names to app names and model names
        model_map = {
            'leads': ('leads', 'Lead'),
            'properties': ('properties', 'Property'),
            'projects': ('projects', 'Project'),
            'authentication': ('authentication', 'User'),
        }
        
        module_lower = module_name.lower()
        if module_lower not in model_map:
            return JsonResponse({'error': f'Unknown module: {module_name}'}, status=400)
        
        app_label, model_name = model_map[module_lower]
        
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            return JsonResponse({'error': f'Model not found: {app_label}.{model_name}'}, status=404)
        
        # Parse field name (may include lookup like "property_type__name")
        field_parts = field_name.split('__')
        base_field_name = field_parts[0]
        
        # Get the field from the model
        try:
            field = model._meta.get_field(base_field_name)
        except Exception as e:
            return JsonResponse({'error': f'Field not found: {field_name}'}, status=404)
        
        choices = []
        
        # Check if it's a ForeignKey
        if hasattr(field, 'related_model'):
            related_model = field.related_model
            
            # Determine which field to display
            if len(field_parts) > 1:
                display_field = field_parts[1]  # e.g., "name" from "property_type__name"
            else:
                # Try to find a suitable display field
                if hasattr(related_model, 'name'):
                    display_field = 'name'
                elif hasattr(related_model, 'display_name'):
                    display_field = 'display_name'
                elif hasattr(related_model, 'title'):
                    display_field = 'title'
                else:
                    display_field = 'id'
            
            # Fetch all records from the related model
            try:
                records = related_model.objects.all()[:100]  # Limit to 100 for performance
                
                for record in records:
                    if hasattr(record, display_field):
                        value = getattr(record, display_field)
                        choices.append({
                            'id': record.pk,
                            'value': str(value),
                            'display': str(value)
                        })
                    else:
                        choices.append({
                            'id': record.pk,
                            'value': str(record.pk),
                            'display': str(record)
                        })
            except Exception as e:
                return JsonResponse({'error': f'Error fetching records: {str(e)}'}, status=500)
        
        # Check if field has choices defined
        elif hasattr(field, 'choices') and field.choices:
            for choice_value, choice_display in field.choices:
                choices.append({
                    'value': choice_value,
                    'display': choice_display
                })
        
        return JsonResponse({
            'success': True,
            'field': field_name,
            'choices': choices,
            'has_choices': len(choices) > 0
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ==================== DATA FILTERS & DROPDOWN RESTRICTIONS CRUD ====================

@csrf_exempt
@login_required
def manage_data_filter(request, profile_id):
    """Create, update, or delete data filters for a profile"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    profile = get_object_or_404(Profile, id=profile_id)
    
    if request.method == 'GET':
        # Get all data filters for this profile
        filters = DataFilter.objects.filter(profile=profile).select_related('module')
        filters_data = [{
            'id': f.id,
            'name': f.name,
            'description': f.description,
            'module_id': f.module.id,
            'module_name': f.module.name,
            'module_display': f.module.display_name,
            'model_name': f.model_name,
            'filter_type': f.filter_type,
            'filter_conditions': f.filter_conditions,
            'is_active': f.is_active,
            'order': f.order,
        } for f in filters]
        return JsonResponse({'success': True, 'filters': filters_data})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'create':
                module = get_object_or_404(Module, id=data.get('module_id'))
                data_filter = DataFilter.objects.create(
                    profile=profile,
                    module=module,
                    name=data.get('name'),
                    description=data.get('description', ''),
                    model_name=data.get('model_name'),
                    filter_type=data.get('filter_type', 'include'),
                    filter_conditions=data.get('filter_conditions', {}),
                    is_active=data.get('is_active', True),
                    order=data.get('order', 0)
                )
                return JsonResponse({
                    'success': True,
                    'message': 'Data filter created successfully',
                    'filter_id': data_filter.id
                })
            
            elif action == 'update':
                data_filter = get_object_or_404(DataFilter, id=data.get('filter_id'), profile=profile)
                data_filter.name = data.get('name', data_filter.name)
                data_filter.description = data.get('description', data_filter.description)
                data_filter.model_name = data.get('model_name', data_filter.model_name)
                data_filter.filter_type = data.get('filter_type', data_filter.filter_type)
                data_filter.filter_conditions = data.get('filter_conditions', data_filter.filter_conditions)
                data_filter.is_active = data.get('is_active', data_filter.is_active)
                data_filter.order = data.get('order', data_filter.order)
                data_filter.save()
                return JsonResponse({'success': True, 'message': 'Data filter updated successfully'})
            
            elif action == 'delete':
                data_filter = get_object_or_404(DataFilter, id=data.get('filter_id'), profile=profile)
                data_filter.delete()
                return JsonResponse({'success': True, 'message': 'Data filter deleted successfully'})
            
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
@login_required
def manage_dropdown_restriction(request, profile_id):
    """Create, update, or delete dropdown restrictions for a profile"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    profile = get_object_or_404(Profile, id=profile_id)
    
    if request.method == 'GET':
        # Get all dropdown restrictions for this profile
        restrictions = DynamicDropdown.objects.filter(profile=profile).select_related('module')
        restrictions_data = [{
            'id': r.id,
            'name': r.name,
            'module_id': r.module.id,
            'module_name': r.module.name,
            'module_display': r.module.display_name,
            'field_name': r.field_name,
            'source_model': r.source_model,
            'source_field': r.source_field,
            'display_field': r.display_field,
            'allowed_values': r.allowed_values,
            'restricted_values': r.restricted_values,
            'filter_conditions': r.filter_conditions,
            'is_multi_select': r.is_multi_select,
            'default_value': r.default_value,
            'placeholder_text': r.placeholder_text,
            'is_active': r.is_active,
            'order': r.order,
        } for r in restrictions]
        return JsonResponse({'success': True, 'restrictions': restrictions_data})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'create':
                module = get_object_or_404(Module, id=data.get('module_id'))
                dropdown = DynamicDropdown.objects.create(
                    profile=profile,
                    module=module,
                    name=data.get('name'),
                    field_name=data.get('field_name'),
                    source_model=data.get('source_model'),
                    source_field=data.get('source_field'),
                    display_field=data.get('display_field'),
                    allowed_values=data.get('allowed_values', []),
                    restricted_values=data.get('restricted_values', []),
                    filter_conditions=data.get('filter_conditions', {}),
                    is_multi_select=data.get('is_multi_select', False),
                    default_value=data.get('default_value', ''),
                    placeholder_text=data.get('placeholder_text', ''),
                    is_active=data.get('is_active', True),
                    order=data.get('order', 0)
                )
                return JsonResponse({
                    'success': True,
                    'message': 'Dropdown restriction created successfully',
                    'restriction_id': dropdown.id
                })
            
            elif action == 'update':
                dropdown = get_object_or_404(DynamicDropdown, id=data.get('restriction_id'), profile=profile)
                dropdown.name = data.get('name', dropdown.name)
                dropdown.field_name = data.get('field_name', dropdown.field_name)
                dropdown.source_model = data.get('source_model', dropdown.source_model)
                dropdown.source_field = data.get('source_field', dropdown.source_field)
                dropdown.display_field = data.get('display_field', dropdown.display_field)
                dropdown.allowed_values = data.get('allowed_values', dropdown.allowed_values)
                dropdown.restricted_values = data.get('restricted_values', dropdown.restricted_values)
                dropdown.filter_conditions = data.get('filter_conditions', dropdown.filter_conditions)
                dropdown.is_multi_select = data.get('is_multi_select', dropdown.is_multi_select)
                dropdown.default_value = data.get('default_value', dropdown.default_value)
                dropdown.placeholder_text = data.get('placeholder_text', dropdown.placeholder_text)
                dropdown.is_active = data.get('is_active', dropdown.is_active)
                dropdown.order = data.get('order', dropdown.order)
                dropdown.save()
                return JsonResponse({'success': True, 'message': 'Dropdown restriction updated successfully'})
            
            elif action == 'delete':
                dropdown = get_object_or_404(DynamicDropdown, id=data.get('restriction_id'), profile=profile)
                dropdown.delete()
                return JsonResponse({'success': True, 'message': 'Dropdown restriction deleted successfully'})
            
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
