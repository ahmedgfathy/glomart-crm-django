from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import UserCreationForm
from django import forms
import json

from .models import Module, Permission, Rule, Profile, UserProfile, UserActivity


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
    
    return render(request, 'authentication/dashboard.html', {
        'user': request.user,
        'accessible_modules': accessible_modules
    })


@login_required
def user_management_view(request):
    """User management interface"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('authentication:dashboard')
    
    search_query = request.GET.get('search', '')
    users = User.objects.select_related('user_profile__profile').all()
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    profiles = Profile.objects.filter(is_active=True)
    
    return render(request, 'authentication/user_management.html', {
        'users': users_page,
        'profiles': profiles,
        'search_query': search_query
    })


@login_required
def profile_management_view(request):
    """Profile management interface"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('authentication:dashboard')
    
    profiles = Profile.objects.all().prefetch_related('permissions__module', 'rules')
    modules = Module.objects.filter(is_active=True).prefetch_related('permissions')
    
    return render(request, 'authentication/profile_management.html', {
        'profiles': profiles,
        'modules': modules
    })


@login_required
def create_profile_view(request):
    """Create new profile"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('authentication:dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if Profile.objects.filter(name=name).exists():
            messages.error(request, f'Profile "{name}" already exists.')
        else:
            profile = Profile.objects.create(name=name, description=description)
            messages.success(request, f'Profile "{name}" created successfully.')
            return redirect('authentication:profile_detail', profile_id=profile.id)
    
    return render(request, 'authentication/create_profile.html')


@login_required
def profile_detail_view(request, profile_id):
    """Profile detail with permission management"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('authentication:dashboard')
    
    profile = get_object_or_404(Profile, id=profile_id)
    modules = Module.objects.filter(is_active=True).prefetch_related('permissions')
    
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
    
    return render(request, 'authentication/profile_detail.html', {
        'profile': profile,
        'modules': modules,
        'current_permissions': current_permissions,
        'current_permissions_json': current_permissions_json
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
    user.save()
    
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
    
    profiles = Profile.objects.all().annotate(
        user_count=Count('users')
    ).order_by('name')
    
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
        
        if not name:
            messages.error(request, 'Profile name is required.')
            return render(request, 'authentication/create_profile.html')
        
        if Profile.objects.filter(name=name).exists():
            messages.error(request, 'A profile with this name already exists.')
            return render(request, 'authentication/create_profile.html')
        
        profile = Profile.objects.create(
            name=name,
            description=description
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
