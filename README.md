# 🏢 Glomart Real Estate CRM

A comprehensive **Customer Relationship Management (CRM) system** specifically designed for real estate businesses. Built with Django 5.2.6, this application provides complete property management, lead tracking, project management, and user administration with role-based access control (RBAC).

## 📋 Table of Contents

- [🎯 Project Overview](#-project-overview)
- [✨ Key Features](#-key-features)
- [🏗️ Project Architecture](#️-project-architecture)
- [📊 Database Schema](#-database-schema)
- [🔐 Authentication & Authorization](#-authentication--authorization)
- [🚀 Installation & Setup](#-installation--setup)
- [📱 Application Modules](#-application-modules)
- [🛠️ Technology Stack](#️-technology-stack)
- [📁 Project Structure](#-project-structure)
- [🔧 Management Commands](#-management-commands)
- [📸 Screenshots](#-screenshots)
- [🤝 Contributing](#-contributing)

## 🎯 Project Overview

**Glomart Real Estate CRM** is a full-featured customer relationship management system tailored for real estate agencies, developers, and property management companies. The system enables efficient management of properties, leads, projects, and team members with sophisticated permission controls.

### Business Objectives
- **Centralized Property Management**: Manage property listings, details, and media
- **Lead Generation & Conversion**: Track prospects from initial contact to sale
- **Project Management**: Oversee development projects and timelines
- **Team Collaboration**: Role-based access with granular permissions
- **Data Integration**: Connect with MariaDB for existing property data

## ✨ Key Features

### 🏠 **Property Management**
- Comprehensive property listings with detailed specifications
- Multi-media support (images, videos, documents)
- Advanced search and filtering capabilities
- Property categorization and status tracking
- Integration with external property databases
- Property assignment and team collaboration

### 👥 **Lead Management**
- Complete lead lifecycle management
- Lead scoring and temperature tracking
- Activity logging and follow-up scheduling
- Lead conversion tracking
- Source attribution and ROI analysis
- Automated lead assignment

### 🏗️ **Project Management**
- Development project tracking
- Project phases and milestone management
- Resource allocation and team assignments
- Project status monitoring
- Progress reporting and analytics
- Integration with property portfolio

### 🔐 **Advanced Authentication System**
- Role-Based Access Control (RBAC)
- Module-level permission management
- User activity auditing
- Profile-based access rules
- Secure session management
- Permission inheritance

### 📊 **Analytics & Reporting**
- Dashboard with key performance indicators
- Property performance metrics
- Lead conversion analytics
- Team productivity reports
- Revenue tracking and forecasting
- Custom report generation

## 🏗️ Project Architecture

### **Application Structure**
```
real_estate_crm/
├── authentication/     # User management and RBAC
├── properties/        # Property management system
├── leads/            # Lead tracking and conversion
├── projects/         # Project management module
├── static/           # CSS, JavaScript, images
├── templates/        # HTML templates and layouts
└── real_estate_crm/  # Main project configuration
```

### **Design Patterns**
- **Model-View-Template (MVT)**: Django's architectural pattern
- **Repository Pattern**: Data access abstraction
- **Decorator Pattern**: Permission and authentication decorators
- **Factory Pattern**: Model instance creation
- **Observer Pattern**: Activity logging and notifications

## 📊 Database Schema

### **Core Tables Overview**
The application uses **SQLite** as the primary database with comprehensive relational design:

```sql
-- Authentication & Authorization (8 tables)
├── auth_user                    # Django built-in user model
├── authentication_module        # System modules (leads, properties, etc.)
├── authentication_permission    # Permission definitions
├── authentication_rule          # Business rules
├── authentication_profile       # User profiles with assigned permissions
├── authentication_userprofile   # User-profile relationships
└── authentication_useractivity  # Activity audit trail

-- Properties Management (15 tables)
├── properties_property          # Main property records
├── properties_propertystatus    # Property status lookup
├── properties_propertytype      # Property type categories
├── properties_propertycategory  # Property classifications
├── properties_compound          # Compound/development info
├── properties_region            # Geographic regions
├── properties_finishingtype     # Finishing specifications
├── properties_unitpurpose       # Unit purposes (sale/rent)
├── properties_currency          # Currency definitions
├── properties_project           # Associated projects
├── properties_propertyactivity  # Property activity logs
├── properties_propertyhistory   # Property change history
└── properties_property_assigned_users # Property assignments

-- Leads Management (12 tables)
├── leads_lead                   # Main lead records
├── leads_leadstatus            # Lead status pipeline
├── leads_leadtype              # Lead type classifications
├── leads_leadpriority          # Priority levels
├── leads_leadtemperature       # Hot/warm/cold ratings
├── leads_leadsource            # Lead source tracking
├── leads_leadtag               # Tagging system
├── leads_leadactivity          # Lead activity logs
├── leads_leadnote              # Lead notes and comments
├── leads_leaddocument          # Lead document attachments
└── leads_leadaudit             # Lead audit trail

-- Projects Management (8 tables)
├── projects_project            # Main project records
├── projects_projectstatus      # Project status definitions
├── projects_projecttype        # Project type categories
├── projects_projectcategory    # Project classifications
├── projects_projectpriority    # Priority management
├── projects_projecthistory     # Project change logs
├── projects_projectassignment  # Team assignments
└── projects_currency           # Project currency handling
```

### **Key Relationships**

#### **Authentication Relationships**
```python
User (1) ←→ (1) UserProfile ←→ (1) Profile
Profile (M) ←→ (M) Permission ←→ (1) Module
Profile (M) ←→ (M) Rule
```

#### **Property Relationships**
```python
Property (M) ←→ (1) PropertyStatus
Property (M) ←→ (1) PropertyType
Property (M) ←→ (1) PropertyCategory
Property (M) ←→ (1) Compound
Property (M) ←→ (1) Region
Property (M) ←→ (M) User (assigned_users)
Property (1) ←→ (M) PropertyActivity
```

#### **Lead Relationships**
```python
Lead (M) ←→ (1) LeadStatus
Lead (M) ←→ (1) LeadType
Lead (M) ←→ (1) LeadPriority
Lead (M) ←→ (1) LeadTemperature
Lead (M) ←→ (1) LeadSource
Lead (M) ←→ (1) User (assigned_to)
Lead (1) ←→ (M) LeadActivity
Lead (1) ←→ (M) LeadNote
Lead (M) ←→ (M) LeadTag
```

#### **Project Relationships**
```python
Project (M) ←→ (1) ProjectStatus
Project (M) ←→ (1) ProjectType
Project (M) ←→ (1) ProjectCategory
Project (M) ←→ (1) ProjectPriority
Project (M) ←→ (1) User (assigned_to)
Project (1) ←→ (M) ProjectHistory
Project (1) ←→ (M) ProjectAssignment
```

## 🔐 Authentication & Authorization

### **Role-Based Access Control (RBAC)**

The system implements a sophisticated 4-level permission structure:

#### **Permission Levels**
1. **View (Level 1)**: Read-only access to data
2. **Edit (Level 2)**: Modify existing records
3. **Create (Level 3)**: Add new records
4. **Delete (Level 4)**: Remove records (highest privilege)

#### **Module-Based Permissions**
```python
# Available Modules
- authentication  # User and permission management
- leads          # Lead management system
- properties     # Property management system
- projects       # Project management system

# Permission Matrix Example
Profile: "Sales Agent"
├── leads: [view, create, edit]
├── properties: [view]
└── projects: [view]

Profile: "Property Manager"
├── properties: [view, create, edit, delete]
├── leads: [view, edit]
└── projects: [view]
```

#### **Permission Decorators**
```python
@login_required
@permission_required('properties', 'view')
def property_list(request):
    # View requires 'view' permission for properties module
    pass

@permission_required('leads', 'create')
def lead_create(request):
    # Create requires 'create' permission for leads module
    pass
```

#### **User Profile System**
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='user_profile')
    profile = models.ForeignKey(Profile)  # Links to permission profile
    
    def has_permission(self, module_name, permission_code):
        """Check if user has specific permission"""
        
    def get_accessible_modules(self):
        """Get modules user can access"""
```

## 🚀 Installation & Setup

### **Prerequisites**
- Python 3.8 or higher
- pip (Python package manager)
- Git

### **Step 1: Clone Repository**
```bash
git clone https://github.com/ahmedgfathy/glomart-crm-django.git
cd glomart-crm-django
```

### **Step 2: Create Virtual Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### **Step 3: Install Dependencies**
```bash
# Install required packages
pip install -r requirements.txt
```

### **Step 4: Database Setup**
```bash
# Apply database migrations
python manage.py migrate

# Create superuser account
python manage.py createsuperuser

# Initialize RBAC system
python manage.py init_rbac
```

### **Step 5: Load Sample Data** (Optional)
```bash
# Setup property lookup data
python manage.py setup_property_lookup_data

# Setup project lookup data  
python manage.py setup_project_lookup_data

# Import real property data (if MariaDB available)
python manage.py migrate_properties

# Import real project data (if MariaDB available)
python manage.py import_real_projects
```

### **Step 6: Run Development Server**
```bash
python manage.py runserver
```

### **Step 7: Access Application**
- **URL**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **Login**: Use superuser credentials created in Step 4

## 📱 Application Modules

### **1. Authentication Module** (`/authentication/`)

#### **Features:**
- User login/logout functionality
- Dashboard with module access overview
- User management and profile assignment
- Activity tracking and audit logs
- Permission management interface

#### **Key Views:**
```python
├── login_view              # User authentication
├── dashboard_view          # Main dashboard
├── user_management_view    # User administration
├── profile_management      # Profile and permission setup
└── activity_logs          # User activity monitoring
```

#### **Templates:**
```
authentication/templates/
├── login.html             # Login form
├── dashboard.html         # Main dashboard
├── user_profile_settings.html
├── company_settings.html
└── partials/
    ├── navbar.html        # Navigation bar
    └── sidebar.html       # Module navigation
```

### **2. Properties Module** (`/properties/`)

#### **Features:**
- Property listing with advanced filtering
- Detailed property information management
- Property image and document handling
- Property assignment to team members
- Activity tracking and history
- Integration with external databases

#### **Key Models:**
```python
Property:
├── Basic Info: name, description, location
├── Financial: price, currency, payment terms
├── Technical: area, rooms, bathrooms, finishing
├── Status: property_status, available_from
├── Relationships: compound, region, assigned_users
└── Metadata: created_by, created_at, updated_at

Related Models:
├── PropertyType        # Villa, Apartment, Office, etc.
├── PropertyCategory    # Residential, Commercial, etc.
├── PropertyStatus      # Available, Sold, Rented, etc.
├── Compound           # Development/building info
├── Region             # Geographic locations
├── FinishingType      # Finishing specifications
└── UnitPurpose        # Sale, Rent, Investment
```

#### **Key Views:**
```python
├── property_list          # Paginated property listing
├── property_detail        # Individual property view
├── property_create        # Add new property
├── property_edit          # Modify property details
├── property_delete        # Remove property
├── property_search        # Advanced search functionality
├── property_assign        # Assign to team members
└── property_images        # Media management
```

#### **API Endpoints:**
```
GET    /properties/                    # List all properties
GET    /properties/<id>/               # Property details
POST   /properties/create/             # Create new property
PUT    /properties/<id>/edit/          # Update property
DELETE /properties/<id>/delete/        # Delete property
GET    /properties/search/             # Search properties
POST   /properties/<id>/assign/        # Assign property
GET    /properties/<id>/images/        # Property media
```

### **3. Leads Module** (`/leads/`)

#### **Features:**
- Complete lead lifecycle management
- Lead scoring and temperature tracking
- Activity timeline and follow-up scheduling
- Lead conversion to customers
- Source tracking and attribution
- Team collaboration and assignment

#### **Key Models:**
```python
Lead:
├── Contact Info: first_name, last_name, email, phone
├── Classification: lead_type, priority, temperature, status
├── Tracking: source, score, assigned_to
├── Timeline: created_at, last_contact, next_follow_up
└── Relationships: activities, notes, documents, tags

Related Models:
├── LeadStatus         # New, Contacted, Qualified, etc.
├── LeadType          # Buyer, Seller, Investor, etc.
├── LeadPriority      # Low, Medium, High, Critical
├── LeadTemperature   # Hot, Warm, Cold
├── LeadSource        # Website, Referral, Campaign, etc.
├── LeadActivity      # Calls, meetings, emails
├── LeadNote          # Comments and observations
├── LeadDocument      # Attachments and files
└── LeadTag           # Flexible tagging system
```

#### **Key Views:**
```python
├── leads_list_view        # Lead management dashboard
├── lead_detail_view       # Individual lead profile
├── lead_create_view       # Add new lead
├── lead_edit_view         # Update lead information
├── lead_delete_view       # Remove lead
├── lead_convert_view      # Convert lead to customer
├── lead_assign_view       # Assign to team member
├── update_lead_score_view # Update lead scoring
├── add_activity_view      # Log lead activities
└── leads_dashboard_view   # Analytics and reporting
```

#### **Lead Workflow:**
```
1. Lead Creation → 2. Initial Contact → 3. Qualification → 
4. Needs Assessment → 5. Proposal → 6. Negotiation → 
7. Conversion/Closure
```

### **4. Projects Module** (`/projects/`)

#### **Features:**
- Development project management
- Project phase and milestone tracking
- Team assignment and resource allocation
- Progress monitoring and reporting
- Integration with property portfolio
- Project financial tracking

#### **Key Models:**
```python
Project:
├── Basic Info: name, project_id, description
├── Location: location, developer, compound
├── Financial: budget, currency, start_price, end_price
├── Timeline: start_date, end_date, delivery_date
├── Status: status, priority, category, type
├── Team: assigned_to, created_by
└── Progress: completion_percentage, current_phase

Related Models:
├── ProjectStatus      # Planning, Active, Completed, etc.
├── ProjectType        # Residential, Commercial, Mixed-use
├── ProjectCategory    # Development, Renovation, etc.
├── ProjectPriority    # Low, Medium, High, Critical
├── ProjectHistory     # Change tracking
├── ProjectAssignment  # Team member assignments
└── Currency          # Multi-currency support
```

#### **Key Views:**
```python
├── project_list          # Project portfolio overview
├── project_detail        # Individual project dashboard
├── project_create        # Create new project
├── project_edit          # Update project details
├── project_delete        # Remove project
├── project_export        # Export project data
└── project_import        # Import project data
```

#### **Project Management Features:**
- **Timeline Management**: Gantt-style project scheduling
- **Resource Allocation**: Team member assignment and workload management
- **Progress Tracking**: Completion percentages and milestone monitoring
- **Financial Management**: Budget tracking and cost analysis
- **Reporting**: Project performance and analytics

## 🛠️ Technology Stack

### **Backend Framework**
- **Django 5.2.6**: Web framework
- **Python 3.13**: Programming language
- **SQLite**: Primary database
- **MariaDB**: External data integration

### **Frontend Technologies**
- **HTML5**: Semantic markup
- **CSS3**: Styling and animations
- **Bootstrap 5**: Responsive framework
- **JavaScript**: Interactive functionality
- **jQuery**: DOM manipulation

### **Additional Libraries**
- **Pillow**: Image processing
- **openpyxl**: Excel file handling
- **python-dateutil**: Date/time utilities
- **django-extensions**: Development tools

### **Development Tools**
- **Git**: Version control
- **VS Code**: IDE
- **Django Debug Toolbar**: Development debugging
- **Django Management Commands**: Custom automation

## 📁 Project Structure

```
glomart-crm-django/
├── 📁 authentication/              # User management & RBAC
│   ├── 📄 models.py                # User profiles, permissions, modules
│   ├── 📄 views.py                 # Authentication views
│   ├── 📄 decorators.py            # Permission decorators
│   ├── 📄 context_processors.py    # Template context
│   ├── 📄 user_settings.py         # User preference views
│   ├── 📁 templates/               # Authentication templates
│   ├── 📁 management/commands/     # RBAC setup commands
│   └── 📄 urls.py                  # Authentication URL patterns
│
├── 📁 properties/                  # Property management system
│   ├── 📄 models.py                # Property models (393 lines)
│   ├── 📄 views.py                 # Property CRUD views
│   ├── 📄 forms.py                 # Property forms
│   ├── 📁 templates/properties/    # Property templates
│   ├── 📁 templatetags/            # Custom template filters
│   ├── 📁 management/commands/     # Property import/sync commands
│   └── 📄 urls.py                  # Property URL patterns
│
├── 📁 leads/                       # Lead management system
│   ├── 📄 models.py                # Lead models (521 lines)
│   ├── 📄 views.py                 # Lead management views
│   ├── 📁 templates/leads/         # Lead templates
│   ├── 📁 templatetags/            # Lead permission tags
│   └── 📄 urls.py                  # Lead URL patterns
│
├── 📁 projects/                    # Project management system
│   ├── 📄 models.py                # Project models (264 lines)
│   ├── 📄 views.py                 # Project CRUD views
│   ├── 📁 templates/projects/      # Project templates
│   ├── 📁 management/commands/     # Project import commands
│   └── 📄 urls.py                  # Project URL patterns
│
├── 📁 static/                      # Static assets
│   ├── 📁 css/                     # Stylesheets
│   ├── 📁 js/                      # JavaScript files
│   └── 📁 images/                  # Application images
│
├── 📁 templates/                   # Global templates
│   ├── 📄 app_layout.html          # Main application layout
│   └── 📄 base.html                # Base template
│
├── 📁 real_estate_crm/             # Project configuration
│   ├── 📄 settings.py              # Django settings
│   ├── 📄 urls.py                  # Main URL configuration
│   └── 📄 wsgi.py                  # WSGI configuration
│
├── 📄 manage.py                    # Django management script
├── 📄 db.sqlite3                   # SQLite database
├── 📄 requirements.txt             # Python dependencies
├── 📄 .gitignore                   # Git ignore rules
└── 📄 README.md                    # This documentation

# File Statistics:
├── Total tracked files: 165
├── Total database tables: 42
├── Total model definitions: 7,077 lines
├── Total views and logic: 15,000+ lines
└── Template files: 50+ HTML templates
```

## 🔧 Management Commands

The application includes custom Django management commands for setup and data import:

### **Authentication Commands**
```bash
# Initialize RBAC system with modules and permissions
python manage.py init_rbac
```

### **Property Commands**
```bash
# Setup property lookup data (types, categories, etc.)
python manage.py setup_property_lookup_data

# Migrate properties from MariaDB
python manage.py migrate_properties

# Sync owner data
python manage.py sync_owner_data

# Update property data
python manage.py update_property_data

# Fix currency data
python manage.py fix_currencies
```

### **Project Commands**
```bash
# Setup project lookup data
python manage.py setup_project_lookup_data

# Setup project permissions
python manage.py setup_project_permissions

# Import projects from MariaDB
python manage.py import_projects_from_mariadb

# Import real projects data
python manage.py import_real_projects
```

### **Usage Examples**
```bash
# Complete fresh setup
python manage.py migrate
python manage.py init_rbac
python manage.py setup_property_lookup_data
python manage.py setup_project_lookup_data
python manage.py createsuperuser

# Import real data (requires MariaDB connection)
python manage.py migrate_properties
python manage.py import_real_projects
```

## 📸 Screenshots

### Dashboard Overview
![Dashboard](docs/screenshots/dashboard.png)
*Main dashboard with module access and quick stats*

### Property Management
![Properties](docs/screenshots/properties.png)
*Property listing with advanced filtering and search*

### Lead Management
![Leads](docs/screenshots/leads.png)
*Lead management with pipeline view and activity tracking*

### Project Management
![Projects](docs/screenshots/projects.png)
*Project portfolio with status tracking and team assignments*

### User Management
![Users](docs/screenshots/users.png)
*User administration with role-based access control*

## 🚀 Development Roadmap

### **Phase 1: Core Functionality** ✅ **COMPLETED**
- [x] User authentication and RBAC system
- [x] Property management with full CRUD operations
- [x] Lead management and tracking system
- [x] Project management capabilities
- [x] Database integration with MariaDB
- [x] Responsive UI design

### **Phase 2: Advanced Features** 🚧 **IN PROGRESS**
- [ ] Email integration and automated notifications
- [ ] Advanced reporting and analytics dashboard
- [ ] Calendar integration for scheduling
- [ ] Document management system
- [ ] Mobile application companion
- [ ] API development for third-party integrations

### **Phase 3: Enterprise Features** 📋 **PLANNED**
- [ ] Multi-tenant architecture
- [ ] Advanced workflow automation
- [ ] Integration with property portals
- [ ] Financial module with invoicing
- [ ] Marketing campaign management
- [ ] Advanced analytics and AI insights

## 🤝 Contributing

We welcome contributions to improve the Glomart Real Estate CRM! Here's how you can contribute:

### **Getting Started**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

### **Development Guidelines**
- Follow Django best practices and PEP 8 style guide
- Write comprehensive tests for new features
- Update documentation for any new functionality
- Ensure backward compatibility when possible
- Use meaningful commit messages

### **Code Standards**
- **Models**: Include docstrings and proper field validation
- **Views**: Use class-based views where appropriate
- **Templates**: Follow consistent naming conventions
- **URLs**: Use descriptive URL patterns
- **Tests**: Maintain test coverage above 80%

### **Reporting Issues**
Please use the GitHub Issues tracker to report bugs or request features. Include:
- Clear description of the issue
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- System information (OS, Python version, etc.)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Ahmed Gomaa Fathy**  
- GitHub: [@ahmedgfathy](https://github.com/ahmedgfathy)
- Repository: [glomart-crm-django](https://github.com/ahmedgfathy/glomart-crm-django)

## 🙏 Acknowledgments

- Django community for the excellent framework
- Bootstrap team for the responsive design framework
- MariaDB for database integration capabilities
- All contributors and users of this CRM system

---

## 📞 Support

For support, email [ahmed@example.com](mailto:ahmed@example.com) or create an issue in the GitHub repository.

## 🔄 Version History

- **v1.0.0** (Current) - Initial release with core CRM functionality
- **v0.9.0** - Beta release with property and lead management
- **v0.8.0** - Alpha release with authentication system

---

*Last updated: September 18, 2025*