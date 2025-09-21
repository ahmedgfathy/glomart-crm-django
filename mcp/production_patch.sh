#!/bin/bash
# Production deployment script for property image fix
# Run this script on your production server

echo "Updating Property model methods..."

# Backup the current models.py file
cp properties/models.py properties/models.py.backup.$(date +%Y%m%d_%H%M%S)

# Apply the fixes to properties/models.py
# Note: This needs to be done manually or with a proper deployment script

echo "Manual steps required:"
echo "1. Update the get_all_image_urls method in properties/models.py"
echo "2. Update the get_image_url method in properties/models.py" 
echo "3. Restart your Django application server"
echo "4. Test property image display"

echo ""
echo "The fixed methods are saved in production_model_fixes.py"
echo "Copy and replace the corresponding methods in your production properties/models.py"
