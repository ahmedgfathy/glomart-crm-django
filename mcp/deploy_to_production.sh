#!/bin/bash
# Production Deployment Commands
# Run these commands on your production server

echo "🚀 Deploying Property Image Fix to Production"
echo "=========================================="

# 1. Backup current models file
echo "📦 Creating backup..."
cp properties/models.py properties/models.py.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backup created"

# 2. Apply the model fixes
echo "🔧 Apply the model fixes manually:"
echo "   - Open properties/models.py in your editor"
echo "   - Replace the get_all_image_urls method with the fixed version"
echo "   - Replace the get_image_url method with the fixed version"
echo "   - Save the file"

# 3. Restart services
echo "🔄 Restart Django application:"
echo "   sudo systemctl reload your-django-service"
echo "   # OR"
echo "   sudo supervisorctl restart your-django-app"
echo "   # OR restart your gunicorn/uwsgi process"

# 4. Test
echo "🧪 Test the deployment:"
echo "   - Visit a property page with images"
echo "   - Check browser developer tools for image load errors"
echo "   - Verify images display correctly"

echo ""
echo "📋 Summary of changes:"
echo "   ✅ Fixed corrupted JSON parsing in get_all_image_urls()"
echo "   ✅ Added regex fallback for fileUrl extraction"
echo "   ✅ Updated placeholder image path to .svg"
echo "   ✅ Maintained /public/ paths for nginx serving"

echo ""
echo "🎯 Expected result: Property images should now display correctly!"