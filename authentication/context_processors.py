from authentication.models import Module

def permissions_context(request):
    """Add permission context to all templates"""
    context = {}
    
    if request.user.is_authenticated:
        try:
            if request.user.is_superuser:
                # Superuser has access to everything
                from leads.models import Lead
                from properties.models import Property
                from projects.models import Project
                
                user_leads_count = Lead.objects.count()
                user_properties_count = Property.objects.count()
                user_projects_count = Project.objects.filter(is_active=True).count()
                
                context.update({
                    'has_leads_view': True,
                    'has_leads_create': True,
                    'has_leads_edit': True,
                    'has_leads_delete': True,
                    'user_leads_count': user_leads_count,
                    'has_properties_view': True,
                    'has_properties_create': True,
                    'has_properties_edit': True,
                    'has_properties_delete': True,
                    'user_properties_count': user_properties_count,
                    'has_projects_view': True,
                    'has_projects_create': True,
                    'has_projects_edit': True,
                    'has_projects_delete': True,
                    'user_projects_count': user_projects_count,
                    'user_accessible_modules': Module.objects.all(),
                })
            else:
                # Check user profile permissions
                try:
                    user_profile = request.user.user_profile
                    if user_profile and user_profile.profile:
                        profile = user_profile.profile
                        
                        # Get all accessible modules for this user
                        accessible_modules = profile.get_accessible_modules()
                        
                        # Check leads permissions specifically
                        leads_module = Module.objects.filter(name='leads').first()
                        if leads_module:
                            leads_permissions = profile.permissions.filter(
                                module=leads_module,
                                is_active=True
                            )
                            
                            has_leads_view = leads_permissions.filter(level__gte=1).exists()
                            
                            # Count user's leads
                            user_leads_count = 0
                            if has_leads_view:
                                from leads.models import Lead
                                user_leads_count = Lead.objects.filter(assigned_to=request.user).count()
                            
                            context.update({
                                'has_leads_view': has_leads_view,
                                'has_leads_create': leads_permissions.filter(level__gte=3).exists(),
                                'has_leads_edit': leads_permissions.filter(level__gte=2).exists(),
                                'has_leads_delete': leads_permissions.filter(level__gte=4).exists(),
                                'user_leads_count': user_leads_count,
                            })
                        else:
                            context.update({
                                'has_leads_view': False,
                                'has_leads_create': False,
                                'has_leads_edit': False,
                                'has_leads_delete': False,
                                'user_leads_count': 0,
                            })
                        
                        # Check properties permissions
                        properties_module = Module.objects.filter(name='property').first()
                        if properties_module:
                            properties_permissions = profile.permissions.filter(
                                module=properties_module,
                                is_active=True
                            )
                            
                            has_properties_view = properties_permissions.filter(level__gte=1).exists()
                            
                            # Count user's properties
                            user_properties_count = 0
                            if has_properties_view:
                                from properties.models import Property
                                # For now, show all properties to authorized users
                                # Later can filter by assigned_users or handler
                                user_properties_count = Property.objects.count()
                            
                            context.update({
                                'has_properties_view': has_properties_view,
                                'has_properties_create': properties_permissions.filter(level__gte=3).exists(),
                                'has_properties_edit': properties_permissions.filter(level__gte=2).exists(),
                                'has_properties_delete': properties_permissions.filter(level__gte=4).exists(),
                                'user_properties_count': user_properties_count,
                            })
                        else:
                            context.update({
                                'has_properties_view': False,
                                'has_properties_create': False,
                                'has_properties_edit': False,
                                'has_properties_delete': False,
                                'user_properties_count': 0,
                            })
                        
                        # Check projects permissions
                        projects_module = Module.objects.filter(name='projects').first()
                        if projects_module:
                            projects_permissions = profile.permissions.filter(
                                module=projects_module,
                                is_active=True
                            )
                            
                            has_projects_view = projects_permissions.filter(level__gte=1).exists()
                            
                            # Count user's projects
                            user_projects_count = 0
                            if has_projects_view:
                                from projects.models import Project
                                # For now, show all projects to authorized users
                                # Later can filter by assigned_to or created_by
                                user_projects_count = Project.objects.filter(is_active=True).count()
                            
                            context.update({
                                'has_projects_view': has_projects_view,
                                'has_projects_create': projects_permissions.filter(level__gte=3).exists(),
                                'has_projects_edit': projects_permissions.filter(level__gte=2).exists(),
                                'has_projects_delete': projects_permissions.filter(level__gte=4).exists(),
                                'user_projects_count': user_projects_count,
                            })
                        else:
                            context.update({
                                'has_projects_view': False,
                                'has_projects_create': False,
                                'has_projects_edit': False,
                                'has_projects_delete': False,
                                'user_projects_count': 0,
                            })
                        
                        context['user_accessible_modules'] = accessible_modules
                        
                    else:
                        # No profile assigned
                        context.update({
                            'has_leads_view': False,
                            'has_leads_create': False,
                            'has_leads_edit': False,
                            'has_leads_delete': False,
                            'user_leads_count': 0,
                            'has_properties_view': False,
                            'has_properties_create': False,
                            'has_properties_edit': False,
                            'has_properties_delete': False,
                            'user_properties_count': 0,
                            'has_projects_view': False,
                            'has_projects_create': False,
                            'has_projects_edit': False,
                            'has_projects_delete': False,
                            'user_projects_count': 0,
                            'user_accessible_modules': Module.objects.none(),
                        })
                except Exception as e:
                    # Handle any user profile errors gracefully
                    context.update({
                        'has_leads_view': False,
                        'has_leads_create': False,
                        'has_leads_edit': False,
                        'has_leads_delete': False,
                        'user_leads_count': 0,
                        'has_properties_view': False,
                        'has_properties_create': False,
                        'has_properties_edit': False,
                        'has_properties_delete': False,
                        'user_properties_count': 0,
                        'has_projects_view': False,
                        'has_projects_create': False,
                        'has_projects_edit': False,
                        'has_projects_delete': False,
                        'user_projects_count': 0,
                        'user_accessible_modules': Module.objects.none(),
                    })
        except Exception as e:
            # Fallback for any other errors
            context.update({
                'has_leads_view': False,
                'has_leads_create': False,
                'has_leads_edit': False,
                'has_leads_delete': False,
                'user_leads_count': 0,
                'has_properties_view': False,
                'has_properties_create': False,
                'has_properties_edit': False,
                'has_properties_delete': False,
                'user_properties_count': 0,
                'has_projects_view': False,
                'has_projects_create': False,
                'has_projects_edit': False,
                'has_projects_delete': False,
                'user_projects_count': 0,
                'user_accessible_modules': Module.objects.none(),
            })
    else:
        # User not authenticated
        context.update({
            'has_leads_view': False,
            'has_leads_create': False,
            'has_leads_edit': False,
            'has_leads_delete': False,
            'user_leads_count': 0,
            'has_properties_view': False,
            'has_properties_create': False,
            'has_properties_edit': False,
            'has_properties_delete': False,
            'user_properties_count': 0,
            'has_projects_view': False,
            'has_projects_create': False,
            'has_projects_edit': False,
            'has_projects_delete': False,
            'user_projects_count': 0,
            'user_accessible_modules': Module.objects.none(),
        })
    
    return context