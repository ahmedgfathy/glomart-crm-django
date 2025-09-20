from authentication.models import Module

def enhanced_permissions_context(request):
    """Enhanced permission context processor with granular field-level permissions"""
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
                
                # Owner databases for superuser
                from owner.models import OwnerDatabase
                owner_databases_count = OwnerDatabase.objects.filter(is_active=True).count()
                
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
                    'has_owner_access': True,
                    'owner_databases_count': owner_databases_count,
                    'user_accessible_modules': Module.objects.all(),
                    'user_profile_permissions': None,  # Superuser doesn't need field restrictions
                })
            else:
                # Check user profile permissions
                try:
                    user_profile = request.user.user_profile
                    if user_profile and user_profile.profile:
                        profile = user_profile.profile
                        
                        # Store profile for template access
                        context['user_profile_permissions'] = profile
                        
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
                            
                            # Count user's leads (with data scope applied)
                            user_leads_count = 0
                            if has_leads_view:
                                from leads.models import Lead
                                leads_queryset = Lead.objects.all()
                                # Apply data scope
                                leads_queryset = profile.apply_data_scope(leads_queryset, 'leads', request.user)
                                # Apply data filters
                                leads_queryset = profile.apply_data_filters(leads_queryset, 'leads', 'Lead')
                                user_leads_count = leads_queryset.count()
                            
                            context.update({
                                'has_leads_view': has_leads_view,
                                'has_leads_create': leads_permissions.filter(level__gte=3).exists(),
                                'has_leads_edit': leads_permissions.filter(level__gte=2).exists(),
                                'has_leads_delete': leads_permissions.filter(level__gte=4).exists(),
                                'user_leads_count': user_leads_count,
                                'leads_visible_fields': profile.get_visible_fields('leads', 'Lead') or [],
                                'leads_form_fields': profile.get_visible_fields('leads', 'Lead') or [],
                            })
                        else:
                            context.update({
                                'has_leads_view': False,
                                'has_leads_create': False,
                                'has_leads_edit': False,
                                'has_leads_delete': False,
                                'user_leads_count': 0,
                                'leads_visible_fields': [],
                                'leads_form_fields': [],
                            })
                        
                        # Check properties permissions
                        properties_module = Module.objects.filter(name='property').first()
                        if properties_module:
                            properties_permissions = profile.permissions.filter(
                                module=properties_module,
                                is_active=True
                            )
                            
                            has_properties_view = properties_permissions.filter(level__gte=1).exists()
                            
                            # Count user's properties (with data scope and filters applied)
                            user_properties_count = 0
                            if has_properties_view:
                                from properties.models import Property
                                properties_queryset = Property.objects.all()
                                # Apply data scope
                                properties_queryset = profile.apply_data_scope(properties_queryset, 'property', request.user)
                                # Apply data filters
                                properties_queryset = profile.apply_data_filters(properties_queryset, 'property', 'Property')
                                user_properties_count = properties_queryset.count()
                            
                            context.update({
                                'has_properties_view': has_properties_view,
                                'has_properties_create': properties_permissions.filter(level__gte=3).exists(),
                                'has_properties_edit': properties_permissions.filter(level__gte=2).exists(),
                                'has_properties_delete': properties_permissions.filter(level__gte=4).exists(),
                                'user_properties_count': user_properties_count,
                                'properties_visible_fields': profile.get_visible_fields('property', 'Property') or [],
                                'properties_form_fields': profile.get_visible_fields('property', 'Property') or [],
                                'properties_data_filters': profile.data_filters.filter(
                                    module=properties_module, 
                                    model_name='Property', 
                                    is_active=True
                                ),
                            })
                        else:
                            context.update({
                                'has_properties_view': False,
                                'has_properties_create': False,
                                'has_properties_edit': False,
                                'has_properties_delete': False,
                                'user_properties_count': 0,
                                'properties_visible_fields': [],
                                'properties_form_fields': [],
                                'properties_data_filters': [],
                            })
                        
                        # Check projects permissions
                        projects_module = Module.objects.filter(name='projects').first()
                        if projects_module:
                            projects_permissions = profile.permissions.filter(
                                module=projects_module,
                                is_active=True
                            )
                            
                            has_projects_view = projects_permissions.filter(level__gte=1).exists()
                            
                            # Count user's projects (with data scope and filters applied)
                            user_projects_count = 0
                            if has_projects_view:
                                from projects.models import Project
                                projects_queryset = Project.objects.filter(is_active=True)
                                # Apply data scope
                                projects_queryset = profile.apply_data_scope(projects_queryset, 'projects', request.user)
                                # Apply data filters
                                projects_queryset = profile.apply_data_filters(projects_queryset, 'projects', 'Project')
                                user_projects_count = projects_queryset.count()
                            
                            context.update({
                                'has_projects_view': has_projects_view,
                                'has_projects_create': projects_permissions.filter(level__gte=3).exists(),
                                'has_projects_edit': projects_permissions.filter(level__gte=2).exists(),
                                'has_projects_delete': projects_permissions.filter(level__gte=4).exists(),
                                'user_projects_count': user_projects_count,
                                'projects_visible_fields': profile.get_visible_fields('projects', 'Project') or [],
                                'projects_form_fields': profile.get_visible_fields('projects', 'Project') or [],
                            })
                        else:
                            context.update({
                                'has_projects_view': False,
                                'has_projects_create': False,
                                'has_projects_edit': False,
                                'has_projects_delete': False,
                                'user_projects_count': 0,
                                'projects_visible_fields': [],
                                'projects_form_fields': [],
                            })
                        
                        context['user_accessible_modules'] = accessible_modules
                        
                        # Check owner databases access
                        owner_module = Module.objects.filter(name='owner').first()
                        if owner_module:
                            owner_permissions = profile.permissions.filter(
                                module=owner_module,
                                is_active=True
                            )
                            
                            has_owner_access = owner_permissions.filter(level__gte=1).exists()
                            
                            # Count accessible databases
                            owner_databases_count = 0
                            if has_owner_access:
                                from owner.models import OwnerDatabase
                                owner_databases_count = OwnerDatabase.objects.filter(is_active=True).count()
                            
                            context.update({
                                'has_owner_access': has_owner_access,
                                'owner_databases_count': owner_databases_count,
                            })
                        else:
                            context.update({
                                'has_owner_access': False,
                                'owner_databases_count': 0,
                            })
                        
                    else:
                        # No profile assigned - set everything to False
                        context.update({
                            'has_leads_view': False,
                            'has_leads_create': False,
                            'has_leads_edit': False,
                            'has_leads_delete': False,
                            'user_leads_count': 0,
                            'leads_visible_fields': [],
                            'leads_form_fields': [],
                            'has_properties_view': False,
                            'has_properties_create': False,
                            'has_properties_edit': False,
                            'has_properties_delete': False,
                            'user_properties_count': 0,
                            'properties_visible_fields': [],
                            'properties_form_fields': [],
                            'properties_data_filters': [],
                            'has_projects_view': False,
                            'has_projects_create': False,
                            'has_projects_edit': False,
                            'has_projects_delete': False,
                            'user_projects_count': 0,
                            'projects_visible_fields': [],
                            'projects_form_fields': [],
                            'has_owner_access': False,
                            'owner_databases_count': 0,
                            'user_accessible_modules': Module.objects.none(),
                            'user_profile_permissions': None,
                        })
                except Exception as e:
                    # Handle any user profile errors gracefully
                    import logging
                    logging.error(f"Enhanced permissions context error: {e}")
                    context.update({
                        'has_leads_view': False,
                        'has_leads_create': False,
                        'has_leads_edit': False,
                        'has_leads_delete': False,
                        'user_leads_count': 0,
                        'leads_visible_fields': [],
                        'leads_form_fields': [],
                        'has_properties_view': False,
                        'has_properties_create': False,
                        'has_properties_edit': False,
                        'has_properties_delete': False,
                        'user_properties_count': 0,
                        'properties_visible_fields': [],
                        'properties_form_fields': [],
                        'properties_data_filters': [],
                        'has_projects_view': False,
                        'has_projects_create': False,
                        'has_projects_edit': False,
                        'has_projects_delete': False,
                        'user_projects_count': 0,
                        'projects_visible_fields': [],
                        'projects_form_fields': [],
                        'has_owner_access': False,
                        'owner_databases_count': 0,
                        'user_accessible_modules': Module.objects.none(),
                        'user_profile_permissions': None,
                    })
        except Exception as e:
            # Fallback for any other errors
            import logging
            logging.error(f"Enhanced permissions context critical error: {e}")
            context.update({
                'has_leads_view': False,
                'has_leads_create': False,
                'has_leads_edit': False,
                'has_leads_delete': False,
                'user_leads_count': 0,
                'leads_visible_fields': [],
                'leads_form_fields': [],
                'has_properties_view': False,
                'has_properties_create': False,
                'has_properties_edit': False,
                'has_properties_delete': False,
                'user_properties_count': 0,
                'properties_visible_fields': [],
                'properties_form_fields': [],
                'properties_data_filters': [],
                'has_projects_view': False,
                'has_projects_create': False,
                'has_projects_edit': False,
                'has_projects_delete': False,
                'user_projects_count': 0,
                'projects_visible_fields': [],
                'projects_form_fields': [],
                'has_owner_access': False,
                'owner_databases_count': 0,
                'user_accessible_modules': Module.objects.none(),
                'user_profile_permissions': None,
            })
    else:
        # User not authenticated
        context.update({
            'has_leads_view': False,
            'has_leads_create': False,
            'has_leads_edit': False,
            'has_leads_delete': False,
            'user_leads_count': 0,
            'leads_visible_fields': [],
            'leads_form_fields': [],
            'has_properties_view': False,
            'has_properties_create': False,
            'has_properties_edit': False,
            'has_properties_delete': False,
            'user_properties_count': 0,
            'properties_visible_fields': [],
            'properties_form_fields': [],
            'properties_data_filters': [],
            'has_projects_view': False,
            'has_projects_create': False,
            'has_projects_edit': False,
            'has_projects_delete': False,
            'user_projects_count': 0,
            'projects_visible_fields': [],
            'projects_form_fields': [],
            'has_owner_access': False,
            'owner_databases_count': 0,
            'user_accessible_modules': Module.objects.none(),
            'user_profile_permissions': None,
        })
    
    return context