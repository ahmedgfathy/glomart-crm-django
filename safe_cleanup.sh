#!/bin/bash
# Safe cleanup script for CRM project
# Preserves critical files: db.sqlite3, migrations, core Django files

echo "🧹 Starting safe cleanup of CRM project..."
echo "⚠️  CRITICAL: db.sqlite3 and migrations will be preserved"

# Remove test files (keep migrations)
echo "Removing test files..."
find . -name "*test*" -type f \
  -not -path "./*/migrations/*" \
  -not -name "test*.py-tpl" \
  -not -path "./venv/*" \
  -not -path "./local_venv/*" \
  -not -path "./mcp/venv/*" \
  -not -path "./.git/*" \
  -delete

# Remove backup files (but keep the CRITICAL_BACKUP we just made)
echo "Removing backup files..."
rm -f ./complete_data_backup.json
rm -f ./data_backup.json  
rm -f ./properties/views_backup.py
rm -f ./real_estate_crm/settings.py.backup*

# Remove temporary and reconstruction files
echo "Removing temporary reconstruction files..."
rm -f ./generate_production_sql.py
rm -f ./generate_simple_sql.py
rm -f ./quick_db_comparison.py
rm -f ./reconstruct_production_data.py
rm -f ./reconstruct_image_data.py
rm -f ./repair_image_metadata.py
rm -f ./temp_settings.py
rm -f ./production_*.sql
rm -f ./test_images_production.py
rm -f ./fix_image_url_production.py

# Remove temporary deployment files but keep core requirements
echo "Removing temporary deployment files..."
rm -f ./production_deployment_commands.txt

# Remove MCP test files but keep core MCP functionality
echo "Cleaning MCP directory..."
cd mcp
rm -f test_*.py
rm -f production_*.py
rm -f deploy_production_direct.py
rm -f fix_production_images.py
rm -f update_production.py
cd ..

# Remove unnecessary SQLite files but keep the main one
echo "Cleaning database files..."
rm -f ./local_db.sqlite3  # This was just a copy, not the main db

# Clean Python cache files
echo "Cleaning Python cache..."
find . -name "__pycache__" -type d -not -path "./venv/*" -not -path "./local_venv/*" -not -path "./mcp/venv/*" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -not -path "./venv/*" -not -path "./local_venv/*" -not -path "./mcp/venv/*" -delete 2>/dev/null || true

# Remove virtual environments (they can be recreated)
echo "Removing virtual environments (can be recreated)..."
rm -rf ./local_venv
rm -rf ./venv

# Keep MCP venv as it has specific packages
echo "Keeping ./mcp/venv (MCP specific packages)"

echo "✅ Safe cleanup completed!"
echo ""
echo "📋 PRESERVED CRITICAL FILES:"
echo "  ✓ db.sqlite3 (main database)"
echo "  ✓ db.sqlite3.CRITICAL_BACKUP_* (backup)"
echo "  ✓ All Django apps and models"
echo "  ✓ All migrations/"
echo "  ✓ manage.py and settings"
echo "  ✓ MCP core server functionality"
echo "  ✓ requirements*.txt"
echo ""
echo "🗑️  REMOVED:"
echo "  ✗ Test files and scripts"
echo "  ✗ Backup files (except critical backup)"
echo "  ✗ Temporary reconstruction scripts"
echo "  ✗ Python cache files"
echo "  ✗ Virtual environments (venv, local_venv)"
echo "  ✗ Temporary database copies"
echo ""
echo "🔄 TO RECREATE VIRTUAL ENVIRONMENT:"
echo "  python3 -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r requirements.txt"