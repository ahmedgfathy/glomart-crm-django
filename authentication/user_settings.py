from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User

@login_required
def user_profile_settings(request):
    """User profile settings - accessible to all users"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            # Update user profile information
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            
            # Validation
            if not first_name:
                messages.error(request, 'First name is required.')
            elif not email:
                messages.error(request, 'Email is required.')
            elif User.objects.filter(email=email).exclude(id=request.user.id).exists():
                messages.error(request, 'Email already exists.')
            else:
                # Update user profile
                request.user.first_name = first_name
                request.user.last_name = last_name
                request.user.email = email
                request.user.save()
                messages.success(request, 'Profile updated successfully!')
                
        elif action == 'change_password':
            # Handle password change
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, 'Password changed successfully!')
            else:
                for error in form.errors.values():
                    messages.error(request, error[0])
    
    # Get user profile for display
    password_form = PasswordChangeForm(request.user)
    
    context = {
        'user': request.user,
        'password_form': password_form,
    }
    
    return render(request, 'authentication/user_profile_settings.html', context)

@login_required
def company_settings(request):
    """Company settings - only for users with proper permissions"""
    # Check if user has permission to access company settings
    # This will be expanded when you create the settings module
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. You do not have permission to access company settings.')
        return redirect('authentication:dashboard')
    
    context = {
        'user': request.user,
    }
    
    # For now, just a placeholder - you can expand this later
    return render(request, 'authentication/company_settings.html', context)