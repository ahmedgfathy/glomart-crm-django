#!/bin/bash
# Export production data script - RUN THIS ON THE PRODUCTION SERVER
# This creates a backup file that you can then download and import locally

echo "🗄️ Exporting production database (READ-ONLY operation)..."
echo "Database: django_db_glomart_rs"
echo "This will NOT modify the production database in any way"

# Create export directory
mkdir -p /tmp/db_exports
cd /tmp/db_exports

# Export filename with timestamp
EXPORT_FILE="production_export_$(date +%Y%m%d_%H%M%S).sql"

echo "📦 Creating database export..."

# Export the production database
mysqldump -u root -p'ZeroCall20!@HH##1655&&' \
    --single-transaction \
    --routines \
    --triggers \
    --hex-blob \
    --complete-insert \
    --no-create-db \
    django_db_glomart_rs > "$EXPORT_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Export successful!"
    echo "📄 File created: /tmp/db_exports/$EXPORT_FILE"
    echo "📊 File size: $(du -h $EXPORT_FILE | cut -f1)"
    echo ""
    echo "📋 Next steps:"
    echo "1. Download this file to your local machine:"
    echo "   scp user@5.180.148.92:/tmp/db_exports/$EXPORT_FILE ."
    echo ""
    echo "2. Then run the import script on your local machine:"
    echo "   ./import_production_data.sh $EXPORT_FILE"
    echo ""
    echo "🔒 Production database was NOT modified - only exported (READ-ONLY)"
else
    echo "❌ Export failed!"
    exit 1
fi