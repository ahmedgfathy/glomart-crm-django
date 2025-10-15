# Manual Deployment Commands for Sidebar Fix

Since SSH connection is timing out, here are the commands to run directly on your production server:

## Step 1: Connect to Your Server
```bash
# SSH to your server (run this from your local terminal or server console)
ssh root@sys.glomartrealestates.com
# Enter password: ZeroCall20!@HH##1655&&
```

## Step 2: Navigate to Project Directory
```bash
cd /var/www/glomart-crm
```

## Step 3: Pull Latest Changes
```bash
# Fetch and apply latest changes from GitHub
git fetch origin
git reset --hard origin/main
```

## Step 4: Restart the Service
```bash
# Restart Gunicorn service to apply changes
systemctl restart glomart-crm
```

## Step 5: Verify Service is Running
```bash
# Check service status
systemctl status glomart-crm --no-pager
```

## Step 6: Test the Website
- Open browser and go to: https://sys.glomartrealestates.com
- Clear browser cache (Ctrl+F5 or Cmd+Shift+R)
- Login and check sidebar - should only show:
  - Dashboard
  - Leads (if has permission)
  - Properties (single working link)
  - Projects (if has permission)
  - Administration (superusers only)

## Alternative: Direct File Update (if git pull fails)
If git commands don't work, you can update the sidebar file directly:

```bash
# Backup current file
cp /var/www/glomart-crm/authentication/templates/authentication/partials/sidebar.html /tmp/sidebar_backup.html

# Create the fixed sidebar file
cat > /var/www/glomart-crm/authentication/templates/authentication/partials/sidebar.html << 'EOF'
{% load static %}

<!-- Fixed Left Sidebar -->
<div class="sidebar-fixed">
    <div class="sidebar-header">
        <div class="d-flex align-items-center px-3 py-3">
            <div class="bg-primary rounded-circle p-2 me-3">
                <i class="bi bi-person text-white"></i>
            </div>
            <div class="flex-grow-1">
                <div class="fw-semibold text-white">{{ user.get_full_name|default:user.username }}</div>
                <small class="text-light opacity-75">
                    {% if user.is_superuser %}
                        System Administrator
                    {% else %}
                        {% if user.user_profile.profile %}
                            {{ user.user_profile.profile.name }}
                        {% else %}
                            No Profile
                        {% endif %}
                    {% endif %}
                </small>
            </div>
        </div>
    </div>
    
    <div class="sidebar-content">
        <nav class="sidebar-nav">
            <ul class="nav flex-column">
                <!-- Dashboard -->
                <li class="nav-item">
                    <a class="nav-link {% if request.resolver_match.url_name == 'dashboard' %}active{% endif %}" href="{% url 'authentication:dashboard' %}">
                        <i class="bi bi-speedometer2 me-3"></i>
                        <span>Dashboard</span>
                    </a>
                </li>
                
                <li class="nav-divider">
                    <span class="nav-divider-text">CRM MODULES</span>
                </li>
                
                <!-- Leads Module -->
                {% if has_leads_view %}
                <li class="nav-item">
                    <a class="nav-link {% if 'leads' in request.resolver_match.namespace %}active{% endif %}" href="{% url 'leads:leads_list' %}">
                        <i class="bi bi-person-lines-fill me-3"></i>
                        <span>Leads</span>
                        {% if user_leads_count > 0 %}
                        <span class="badge bg-primary ms-auto">{{ user_leads_count }}</span>
                        {% endif %}
                    </a>
                </li>
                {% endif %}
                
                <!-- Properties Module -->
                {% if has_properties_view %}
                <li class="nav-item">
                    <a class="nav-link {% if 'properties' in request.resolver_match.namespace %}active{% endif %}" href="{% url 'properties:property_list' %}">
                        <i class="bi bi-building me-3"></i>
                        <span>Properties</span>
                        {% if user_properties_count > 0 %}
                        <span class="badge bg-success ms-auto">{{ user_properties_count }}</span>
                        {% endif %}
                    </a>
                </li>
                {% endif %}
                
                <!-- Projects Module -->
                {% if has_projects_view %}
                <li class="nav-item">
                    <a class="nav-link {% if 'projects' in request.resolver_match.namespace %}active{% endif %}" href="{% url 'projects:project_list' %}">
                        <i class="bi bi-diagram-2 me-3"></i>
                        <span>Projects</span>
                        {% if user_projects_count > 0 %}
                        <span class="badge bg-info ms-auto">{{ user_projects_count }}</span>
                        {% endif %}
                    </a>
                </li>
                {% endif %}
                
                {% if user.is_superuser %}
                <li class="nav-divider">
                    <span class="nav-divider-text">ADMINISTRATION</span>
                </li>
                
                <!-- Profile Management -->
                <li class="nav-item">
                    <a class="nav-link {% if request.resolver_match.url_name == 'profiles' %}active{% endif %}" href="{% url 'authentication:profiles' %}">
                        <i class="bi bi-shield-check me-3"></i>
                        <span>Manage Profiles</span>
                    </a>
                </li>
                
                <!-- Field Permissions -->
                <li class="nav-item">
                    <a class="nav-link {% if 'field_permissions' in request.resolver_match.url_name %}active{% endif %}" href="{% url 'authentication:field_permissions_dashboard' %}">
                        <i class="bi bi-key me-3"></i>
                        <span>Field Permissions</span>
                    </a>
                </li>
                
                <!-- Data Filters Manager -->
                <li class="nav-item">
                    <a class="nav-link {% if request.resolver_match.url_name == 'data_filters_manager' %}active{% endif %}" href="{% url 'authentication:data_filters_manager' %}">
                        <i class="bi bi-funnel me-3"></i>
                        <span>Data Filters</span>
                    </a>
                </li>
                
                <!-- Audit Logs -->
                <li class="nav-item">
                    <a class="nav-link {% if 'audit' in request.resolver_match.url_name %}active{% endif %}" href="{% url 'audit:audit_list' %}">
                        <i class="bi bi-shield-exclamation me-3"></i>
                        <span>Audit Logs</span>
                    </a>
                </li>
                {% endif %}
                
                <!-- Audit access for non-superusers with permissions -->
                {% if not user.is_superuser and user.user_profile.profile %}
                    {% for permission in user.user_profile.profile.permissions.all %}
                        {% if permission.module.name == 'audit' and permission.code == 'view' %}
                        <li class="nav-divider">
                            <span class="nav-divider-text">SYSTEM</span>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {% if 'audit' in request.resolver_match.url_name %}active{% endif %}" href="{% url 'audit:audit_list' %}">
                                <i class="bi bi-shield-exclamation me-3"></i>
                                <span>Audit Logs</span>
                            </a>
                        </li>
                        {% endif %}
                    {% endfor %}
                {% endif %}
            </ul>
        </nav>
    </div>
    
    <!-- Sidebar Footer -->
    <div class="sidebar-footer">
        <div class="px-3 py-2">
            <small class="text-light opacity-75 d-block mb-2">Glomart CRM v1.0</small>
            <div class="d-flex gap-2">
                <a href="{% url 'authentication:user_profile_settings' %}" class="btn btn-sm btn-outline-light flex-fill" title="User Settings">
                    <i class="bi bi-gear"></i>
                </a>
                <button class="btn btn-sm btn-outline-light flex-fill" type="button" title="Help">
                    <i class="bi bi-question-circle"></i>
                </button>
                <a href="{% url 'authentication:logout' %}" class="btn btn-sm btn-outline-danger flex-fill" title="Logout">
                    <i class="bi bi-box-arrow-right"></i>
                </a>
            </div>
        </div>
    </div>
</div>

<!-- Mobile Sidebar Overlay -->
<div class="sidebar-overlay d-lg-none" id="sidebarOverlay"></div>

<!-- Mobile Toggle Button (shown only on mobile) -->
<button class="btn btn-gradient sidebar-toggle d-lg-none" type="button" id="sidebarToggle">
    <i class="bi bi-list"></i>
</button>
EOF

# Restart service after file update
systemctl restart glomart-crm
```

## What This Fixed Sidebar Does:
- ❌ **REMOVED** all dynamic module loops that created fake links
- ✅ **USES** only permission-based flags (`has_leads_view`, `has_properties_view`, etc.)
- ✅ **SHOWS** only working, functional links
- ✅ **NO MORE** fake Reports, Calendar, Documents links

After running these commands, the sidebar should only show legitimate, working navigation links!