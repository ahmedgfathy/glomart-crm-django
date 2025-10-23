# How to Copy ALL Production Data to Local Development

## You are CORRECT - You need ALL production data, not sample data!

The production database contains the real company data with all properties, leads, projects, and users. Here's how to copy **ALL** of it to your local database:

## Method 1: Direct Connection (if possible)
```bash
# Try the direct sync script first
./sync_production_to_local.sh
```

## Method 2: Export/Import (if direct connection fails)

### Step 1: On Production Server
SSH into your production server and run:
```bash
# Upload and run the export script on production server
./export_production_data.sh
```

This will create a file like: `/tmp/db_exports/production_export_20251011_180000.sql`

### Step 2: Download the Export File
From your local machine:
```bash
# Download the export file from production server
scp user@5.180.148.92:/tmp/db_exports/production_export_*.sql .
```

### Step 3: Import to Local Database  
```bash
# Import ALL production data to local database
./import_production_data.sh production_export_20251011_180000.sql
```

## What This Does:

### ✅ Copies EVERYTHING from production:
- **All Properties** (not just 5 samples)
- **All Leads** (not just 5 samples)  
- **All Projects** (not just 3 samples)
- **All Users and Authentication**
- **All Lookup Tables** (regions, types, statuses, etc.)
- **All Real Company Data**

### ✅ Safety Features:
- **Production database is NEVER modified** (READ-ONLY operation)
- **Local database is backed up** before import
- **You get REAL data** for development and testing

### ✅ After Import You Get:
- **Complete production database** in your local environment
- **All real properties** that the company manages
- **All real leads** and customer data
- **All real projects** and their details
- **Ability to test with REAL data** instead of samples

## Local Database After Import:
```bash
# Check your local database now has ALL production data
mysql -u root -pzerocall glomart_crm_local

# Count real data:
SELECT COUNT(*) FROM properties_property;  -- All real properties
SELECT COUNT(*) FROM leads_lead;          -- All real leads  
SELECT COUNT(*) FROM projects_project;    -- All real projects
SELECT COUNT(*) FROM auth_user;          -- All real users
```

## Login After Import:
- **Existing production users**: Use their normal credentials
- **Local admin user**: admin / admin123 (created automatically)

You now have the **COMPLETE MASTER DATABASE** copied to your local environment for safe development!

## Important Notes:
1. **Production database remains untouched** - this is a copy operation only
2. **All changes you make locally** will NOT affect production
3. **Re-run the sync** anytime you need fresh production data
4. **Never push local database changes** back to production

This gives you the **REAL COMPANY DATA** for proper development and testing!