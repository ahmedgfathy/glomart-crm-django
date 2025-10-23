#!/bin/bash
# Selective sync - sync only what you choose

PROD_SERVER="root@5.180.148.92"
PROD_PATH="/var/www/glomart-crm"
LOCAL_PATH="/Users/ahmedgomaa/Downloads/glomart-crm-django"

echo "What do you want to sync from production?"
echo ""
echo "1. static/ only (76KB - CSS, JS, images, themes)"
echo "2. templates/ only (316KB - HTML design files)"
echo "3. media/ only (4KB - user uploads)"
echo "4. staticfiles/ only (2.4GB - property videos/images) ⚠️  LARGE!"
echo "5. ALL EXCEPT property images/videos (Recommended - no staticfiles/)"
echo "6. ALL INCLUDING property images/videos (2.4GB download!)"
echo "7. Exit"
echo ""
read -p "Choose (1-7): " choice

sync_static() {
    echo "Syncing static/..."
    rsync -avz --delete ${PROD_SERVER}:${PROD_PATH}/static/ ${LOCAL_PATH}/static/
    echo "✓ static/ synced (CSS, JS, images)"
}

sync_templates() {
    echo "Syncing templates/..."
    rsync -avz --delete ${PROD_SERVER}:${PROD_PATH}/templates/ ${LOCAL_PATH}/templates/
    echo "✓ templates/ synced (HTML files)"
}

sync_media() {
    echo "Syncing media/..."
    rsync -avz --delete ${PROD_SERVER}:${PROD_PATH}/media/ ${LOCAL_PATH}/media/
    echo "✓ media/ synced (uploads)"
}

sync_staticfiles() {
    echo "⚠️  Syncing staticfiles/ (2.4GB - this will take time)..."
    rsync -avz --progress --delete ${PROD_SERVER}:${PROD_PATH}/staticfiles/ ${LOCAL_PATH}/staticfiles/
    echo "✓ staticfiles/ synced (property videos/images)"
}

case $choice in
    1) sync_static ;;
    2) sync_templates ;;
    3) sync_media ;;
    4) sync_staticfiles ;;
    5) 
        echo "Syncing everything EXCEPT property images/videos..."
        sync_static
        sync_templates
        sync_media
        echo "✓ Design files synced (skipped large staticfiles/)"
        ;;
    6) 
        echo "Syncing EVERYTHING including 2.4GB property images/videos..."
        sync_static
        sync_templates
        sync_media
        sync_staticfiles
        ;;
    7) echo "Cancelled"; exit 0 ;;
    *) echo "Invalid choice"; exit 1 ;;
esac

echo ""
echo "✅ Sync complete!"
echo "Current local sizes:"
du -sh static staticfiles media templates 2>/dev/null
