#!/bin/bash

# Script to deploy the 40 owner databases to production server
# This script exports the specific databases used by the Django CRM application

set -e

# Configuration
LOCAL_DB_USER="root"
LOCAL_DB_PASSWORD="zerocall"
REMOTE_HOST="5.180.148.92"
REMOTE_DB_USER="root" 
REMOTE_DB_PASSWORD="ZeroCall20!@HH##1655&&"
SSH_KEY="$HOME/.ssh/glomart_deploy"
BACKUP_DIR="/tmp/glomart_db_export"

# List of owner databases from Django application
OWNER_DATABASES=(
    "rs_jaguar_xls"
    "rs_jaguar_xlsx"
    "rs_jeep_1_xls"
    "rs_jeep_xls"
    "rs_villas_october_copy_xlsx"
    "rs_zayed_1_xlsx"
    "rs_zayed_2000_xlsx"
    "rs_customer_data_eg_xlsx"
    "rs_emaar_customer_care_client_details_xlsx"
    "rs_mawasem_company_by_network_company_xlsx"
    "rs_sea_shell_by_network_markting_xlsx"
    "rs_vip_company_heads_1500_eg_xlsx"
    "rs_amwaj_xlsx"
    "rs_uptown_xlsx"
    "rs_amwaj_hacienda_lavista_bay_marassi_4120_customers_xlsx"
    "rs_copy_of_marassi_2020_2500le_eg_xlsx"
    "rs_marassi_2020_xlsx"
    "rs_marassi_3693_xlsx"
    "rs_mivida_3795_xlsx"
    "rs_uptown_cairo_mivida_avenues_greens_2042_leads_xlsx"
    "rs_uptown_cairo_mivida_grove_4092_leads_xlsx"
    "rs_palm_hills_3965_eg_xlsx"
    "rs_palm_xlsx"
    "rs_rehab_xlsx"
    "rs_katameya_hills_tagamoa_xlsx"
    "rs_2_sabour_xlsx"
    "rs_grand_sabour_tagamoa_2_xlsx"
    "rs_sabour_1_diyar_park_tagamoa_xlsx"
    "rs_alexandria_xlsx"
    "rs_hadaeq_maadi_xlsx"
    "rs_jedar_xlsx"
    "rs_gouna_106_xlsx"
    "rs_gouna_1500_xls"
    "rs_mangroovy_elgouna_55_leads_xls"
    "rs_sahel_xlsx"
    "rs_sodic_1_xlsx"
    "rs_sodic_3_xlsx"
    "rs_sodic_4_xlsx"
    "rs_12_xlsx"
    "rs_14_xlsx"
)

echo "========================================="
echo "  Glomart CRM Database Deployment"
echo "========================================="
echo "Deploying ${#OWNER_DATABASES[@]} owner databases to production"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Export main CRM database first
echo "🗄️  Exporting main CRM database..."
mysqldump -u "$LOCAL_DB_USER" -p"$LOCAL_DB_PASSWORD" glomart_crm > "$BACKUP_DIR/glomart_crm.sql"

# Export each owner database
echo ""
echo "📊 Exporting owner databases..."
for db in "${OWNER_DATABASES[@]}"; do
    echo "  - Exporting $db..."
    if mysql -u "$LOCAL_DB_USER" -p"$LOCAL_DB_PASSWORD" -e "USE $db;" 2>/dev/null; then
        mysqldump -u "$LOCAL_DB_USER" -p"$LOCAL_DB_PASSWORD" "$db" > "$BACKUP_DIR/$db.sql"
        echo "    ✅ $db exported successfully"
    else
        echo "    ⚠️  Database $db not found locally, skipping"
    fi
done

# Create compressed archive
echo ""
echo "📦 Creating compressed archive..."
cd "$BACKUP_DIR"
tar -czf glomart_databases.tar.gz *.sql
echo "✅ Archive created: $(ls -lh glomart_databases.tar.gz | awk '{print $5}')"

# Upload to remote server
echo ""
echo "🚀 Uploading databases to production server..."
scp -i "$SSH_KEY" glomart_databases.tar.gz root@"$REMOTE_HOST":/tmp/

# Import databases on remote server
echo ""
echo "📥 Importing databases on production server..."
ssh -i "$SSH_KEY" root@"$REMOTE_HOST" "
    cd /tmp
    tar -xzf glomart_databases.tar.gz
    
    echo '🗄️  Importing main CRM database...'
    mysql -u '$REMOTE_DB_USER' -p'$REMOTE_DB_PASSWORD' glomart_crm < glomart_crm.sql
    echo '✅ Main CRM database imported'
    
    echo ''
    echo '📊 Importing owner databases...'
    for sql_file in rs_*.sql; do
        db_name=\$(basename \"\$sql_file\" .sql)
        echo \"  - Importing \$db_name...\"
        mysql -u '$REMOTE_DB_USER' -p'$REMOTE_DB_PASSWORD' -e \"CREATE DATABASE IF NOT EXISTS \$db_name;\"
        mysql -u '$REMOTE_DB_USER' -p'$REMOTE_DB_PASSWORD' \"\$db_name\" < \"\$sql_file\"
        echo \"    ✅ \$db_name imported successfully\"
    done
    
    echo ''
    echo '🧹 Cleaning up temporary files...'
    rm -f *.sql glomart_databases.tar.gz
"

# Update Django settings to use MariaDB
echo ""
echo "⚙️  Updating Django configuration..."
ssh -i "$SSH_KEY" root@"$REMOTE_HOST" "
    cd /var/www/glomart-crm
    sed -i \"s/'ENGINE': 'django.db.backends.sqlite3'/'ENGINE': 'django.db.backends.mysql'/\" real_estate_crm/settings.py
    sed -i \"s/'NAME': BASE_DIR \/ 'db.sqlite3'/'NAME': 'glomart_crm'/\" real_estate_crm/settings.py
    sed -i \"/django.db.backends.mysql/a\\        'HOST': 'localhost',\\n        'USER': 'root',\\n        'PASSWORD': '$REMOTE_DB_PASSWORD',\\n        'OPTIONS': {'charset': 'utf8mb4'},\" real_estate_crm/settings.py
    sed -i \"s/'PASSWORD': 'zerocall'/'PASSWORD': '$REMOTE_DB_PASSWORD'/\" real_estate_crm/settings.py
"

# Restart Django application
echo ""
echo "🔄 Restarting Django application..."
ssh -i "$SSH_KEY" root@"$REMOTE_HOST" "systemctl restart glomart-crm"

# Cleanup local files
echo ""
echo "🧹 Cleaning up local temporary files..."
rm -rf "$BACKUP_DIR"

echo ""
echo "🎉 Database deployment completed successfully!"
echo "   • Main database: glomart_crm"
echo "   • Owner databases: ${#OWNER_DATABASES[@]} databases"
echo "   • Django configuration updated"
echo "   • Application restarted"
echo ""
echo "You can now login at: https://sys.glomartrealestates.com"
echo "========================================="