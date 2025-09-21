#!/bin/bash

# Navigation Feature Deployment Script
# This script uploads the navigation feature files to production

echo "=== Property and Lead Navigation Feature Deployment ==="
echo "This script will upload the following updated files:"
echo ""

echo "1. properties/views.py - Added navigation logic"
echo "2. properties/templates/properties/property_edit.html - Added navigation arrows"
echo "3. leads/views.py - Added navigation logic"
echo "4. leads/templates/leads/edit_lead.html - Added navigation arrows"
echo ""

# Upload properties views
echo "Uploading properties/views.py..."
rsync -avz --partial --progress /Users/ahmedgomaa/Downloads/crm/properties/views.py root@5.180.148.92:/var/www/glomart-crm/properties/

# Upload properties template
echo "Uploading property edit template..."
rsync -avz --partial --progress /Users/ahmedgomaa/Downloads/crm/properties/templates/properties/property_edit.html root@5.180.148.92:/var/www/glomart-crm/properties/templates/properties/

# Upload leads views
echo "Uploading leads/views.py..."
rsync -avz --partial --progress /Users/ahmedgomaa/Downloads/crm/leads/views.py root@5.180.148.92:/var/www/glomart-crm/leads/

# Upload leads template
echo "Uploading lead edit template..."
rsync -avz --partial --progress /Users/ahmedgomaa/Downloads/crm/leads/templates/leads/edit_lead.html root@5.180.148.92:/var/www/glomart-crm/leads/templates/leads/

# Restart the CRM service
echo "Restarting glomart-crm service..."
ssh root@5.180.148.92 "systemctl restart glomart-crm"

echo "Checking service status..."
ssh root@5.180.148.92 "systemctl status glomart-crm --no-pager"

echo ""
echo "=== Deployment completed ==="
echo ""
echo "Navigation Features Added:"
echo "- Left/Right arrow buttons for continuous property/lead editing"
echo "- Keyboard navigation (left/right arrow keys)"
echo "- Navigation counter showing current position (e.g., 'Property 3 of 25')"
echo "- Unsaved changes warning when navigating away"
echo "- Mobile-responsive design (arrows hidden on small screens)"
echo ""
echo "Usage:"
echo "- Use left/right arrow buttons or keyboard arrows to navigate"
echo "- The system will warn you about unsaved changes"
echo "- Navigation respects user permissions and filters"
echo "- Counter shows your current position in the filtered list"