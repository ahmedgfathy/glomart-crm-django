# Glomart CRM - Safe Development & Deployment Guide

## 🚨 CRITICAL DATABASE RULES 🚨

### Production Database (MASTER DATA)
- **Host**: 5.180.148.92 
- **Database**: django_db_glomart_rs
- **User**: root
- **Password**: ZeroCall20!@HH##1655&&
- **⚠️ NEVER TOUCH THIS DATABASE - IT CONTAINS COMPANY MASTER DATA**
- **⚠️ NO BACKUPS EXIST - THIS IS THE ONLY COPY**

### Local Development Database 
- **Host**: localhost
- **Database**: glomart_crm_local  
- **User**: root
- **Password**: zerocall
- **✅ This can be safely modified/reset for development**

## Safe Development Workflow

### 1. Setting Up Local Development

```bash
# Clone repository
git clone <repo-url>
cd glomart-crm-django

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-minimal.txt

# Set up local database
mysql -u root -p
CREATE DATABASE glomart_crm_local CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'glomart_local'@'localhost' IDENTIFIED BY 'local123';
GRANT ALL PRIVILEGES ON glomart_crm_local.* TO 'glomart_local'@'localhost';
FLUSH PRIVILEGES;

# Run local migrations
export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_local
python manage.py migrate
python manage.py createsuperuser

# Start local server
python manage.py runserver
```

### 2. Syncing Production Data to Local (READ-ONLY)

When you need fresh production data in your local environment:

```bash
# This script safely copies FROM production TO local
# Production database is NEVER modified
./sync_production_to_local.sh
```

**What this script does:**
- ✅ Connects to production database (READ-ONLY)
- ✅ Exports production data
- ✅ Backs up your current local data
- ✅ Imports production data into local database
- ❌ NEVER touches production database

### 3. Local Development

```bash
# Always use local settings
export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_local
python manage.py runserver

# For development tasks
python manage.py shell
python manage.py migrate
python manage.py collectstatic
```

## Safe Production Deployment

### GitHub Actions Workflow
When you push to main branch:

1. **✅ Code is updated** on production server
2. **✅ Dependencies are updated**
3. **✅ Static files are collected**
4. **✅ Services are restarted**
5. **❌ Database is NEVER touched**

### Manual Production Deployment

```bash
# On production server (if needed)
./deploy_production_safe.sh
```

**What deployment does:**
- ✅ Updates application code
- ✅ Updates Python dependencies
- ✅ Collects static files
- ✅ Restarts services
- ✅ Checks migration status (READ-ONLY)
- ❌ NEVER applies migrations automatically
- ❌ NEVER modifies database data

## Database Migration Strategy

### For Local Development
```bash
# Safe to run on local database
python manage.py makemigrations
python manage.py migrate
```

### For Production
**⚠️ EXTREME CAUTION REQUIRED**

1. Test migrations thoroughly on local database with production data copy
2. Create manual backup of production database if possible
3. Apply migrations manually on production with careful monitoring
4. **NEVER use automated migration deployment**

## File Structure

```
glomart-crm-django/
├── real_estate_crm/
│   ├── settings.py              # Base settings
│   ├── settings_local.py        # Local development (safe to modify)
│   ├── settings_production.py   # Production (database protected)
├── .env.local.template          # Local environment template
├── .env.production.template     # Production environment template
├── sync_production_to_local.sh  # Safe data sync FROM production
├── deploy_production_safe.sh    # Safe deployment (no DB changes)
├── .github/workflows/deploy.yml # Automated deployment (DB protected)
└── README_DEPLOYMENT.md         # This file
```

## Environment Variables

### Local Development (.env.local)
```bash
ENVIRONMENT=local
DJANGO_SETTINGS_MODULE=real_estate_crm.settings_local
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=zerocall
DB_NAME=glomart_crm_local
```

### Production (.env.production) 
```bash
ENVIRONMENT=production
DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=ZeroCall20!@HH##1655&&
DB_NAME=django_db_glomart_rs
```

## Safety Checklist

Before any production deployment:

- [ ] Production database credentials are correct and READ-ONLY for deployment
- [ ] Local testing completed with production data copy
- [ ] No migration scripts will run automatically
- [ ] Only code, dependencies, and static files will be updated
- [ ] Database backup exists (if possible to create one)
- [ ] Rollback plan is ready

## Emergency Procedures

### If Something Goes Wrong
1. **NEVER panic and modify production database**
2. Use the rollback feature in deployment script
3. Check application logs: `/var/log/glomart-crm/`
4. Restart services manually if needed
5. Contact system administrator

### If Database Issues Occur
1. **DO NOT attempt to fix production database**
2. Investigate using local copy of production data
3. Test fixes in local environment first
4. Apply fixes manually with extreme caution

## Contact & Support

For deployment issues:
- Check deployment logs: `/var/log/glomart-crm/deployment.log`
- Review service status: `systemctl status glomart-crm`
- Check nginx logs: `/var/log/nginx/`

Remember: **PRODUCTION DATABASE IS SACRED - NEVER TOUCH IT!**