#!/bin/bash

# Manual Production Deployment Instructions for Navigation Feature
# Run these commands directly on the production server

echo "=== Navigation Feature Manual Deployment ==="
echo "Since you're already on the production server, follow these steps:"
echo ""

echo "1. Create backup of current files:"
echo "cd /var/www/glomart-crm"
echo "cp properties/views.py properties/views.py.backup.$(date +%Y%m%d_%H%M%S)"
echo "cp properties/templates/properties/property_edit.html properties/templates/properties/property_edit.html.backup.$(date +%Y%m%d_%H%M%S)"
echo "cp leads/views.py leads/views.py.backup.$(date +%Y%m%d_%H%M%S)"
echo "cp leads/templates/leads/edit_lead.html leads/templates/leads/edit_lead.html.backup.$(date +%Y%m%d_%H%M%S)"
echo ""

echo "2. You have two options to get the updated files:"
echo ""
echo "OPTION A: Use rsync from your local machine (when connection is stable):"
echo "rsync -avz /Users/ahmedgomaa/Downloads/crm/properties/views.py root@5.180.148.92:/var/www/glomart-crm/properties/"
echo "rsync -avz /Users/ahmedgomaa/Downloads/crm/properties/templates/properties/property_edit.html root@5.180.148.92:/var/www/glomart-crm/properties/templates/properties/"
echo "rsync -avz /Users/ahmedgomaa/Downloads/crm/leads/views.py root@5.180.148.92:/var/www/glomart-crm/leads/"
echo "rsync -avz /Users/ahmedgomaa/Downloads/crm/leads/templates/leads/edit_lead.html root@5.180.148.92:/var/www/glomart-crm/leads/templates/leads/"
echo ""

echo "OPTION B: Create the files manually on the server (if rsync fails):"
echo "I'll provide the file contents separately for manual editing"
echo ""

echo "3. After files are updated, restart the service:"
echo "systemctl restart glomart-crm"
echo "systemctl status glomart-crm --no-pager"
echo ""

echo "4. Test the navigation feature:"
echo "Visit: https://sys.glomartrealestates.com/properties/[any-property-id]/edit/"
echo "You should see navigation arrows on the left and right sides"
echo "And a counter in the top-right corner showing 'Property X of Y'"
echo ""