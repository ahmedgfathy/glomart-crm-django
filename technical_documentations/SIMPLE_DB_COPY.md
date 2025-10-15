## SIMPLEST METHOD: Copy Production Database to Local

### Step 1: Export on Production Server
SSH into your production server and run this **single command**:

```bash
mysqldump -uroot -p'ZeroCall20!@HH##1655&&' --single-transaction --routines --triggers django_db_glomart_rs > /tmp/production_backup.sql && echo "✅ Export complete: $(ls -lh /tmp/production_backup.sql)"
```

### Step 2: Download to Your Mac
From your local machine (replace `YOUR_USERNAME` with your SSH username):

```bash
scp YOUR_USERNAME@5.180.148.92:/tmp/production_backup.sql ~/Downloads/
```

### Step 3: Import to Local Database
Run these commands in your project directory:

```bash
# Go to your project directory
cd /Users/ahmedgomaa/Downloads/glomart-crm-django

# Recreate local database
mysql -hlocalhost -uroot -pzerocall -e "DROP DATABASE IF EXISTS glomart_crm_local;"
mysql -hlocalhost -uroot -pzerocall -e "CREATE DATABASE glomart_crm_local CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Import production data
mysql -hlocalhost -uroot -pzerocall glomart_crm_local < ~/Downloads/production_backup.sql

# Activate virtual environment and run migrations
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_local
python manage.py migrate

# Check imported data
echo "Properties: $(mysql -hlocalhost -uroot -pzerocall glomart_crm_local -e "SELECT COUNT(*) FROM properties_property;" -s -N)"
echo "Leads: $(mysql -hlocalhost -uroot -pzerocall glomart_crm_local -e "SELECT COUNT(*) FROM leads_lead;" -s -N)"
echo "Projects: $(mysql -hlocalhost -uroot -pzerocall glomart_crm_local -e "SELECT COUNT(*) FROM projects_project;" -s -N)"
echo "Users: $(mysql -hlocalhost -uroot -pzerocall glomart_crm_local -e "SELECT COUNT(*) FROM auth_user;" -s -N)"

echo "✅ PRODUCTION DATABASE COPIED TO LOCAL!"
echo "🚀 You can now run: python manage.py runserver"
```

### Result:
- **ALL production data** copied to your local database
- **All real properties, leads, projects, users**
- **Complete company database** for development
- **Production database remains untouched**

This will give you the **complete master database** in your local environment!