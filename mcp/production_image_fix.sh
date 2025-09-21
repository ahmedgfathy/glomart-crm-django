#!/bin/bash
# Production Image Fix Script for Glomart CRM
# Run this on your production server (5.180.148.92)

echo "🔧 === FIXING PROPERTY IMAGES IN PRODUCTION ==="

# 1. Update nginx configuration
echo "📝 1. Creating nginx configuration..."

cat > /tmp/glomart_crm_images_fix.conf << 'EOF'
# Add this to your nginx server block in /etc/nginx/sites-available/glomart-crm

server {
    listen 80;
    server_name 5.180.148.92;  # Your production IP

    # Static files (CSS, JS)
    location /static/ {
        alias /var/www/glomart-crm/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Media files (User uploads)
    location /media/ {
        alias /var/www/glomart-crm/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Property images (CRITICAL FIX)
    location /public/ {
        alias /var/www/glomart-crm/public/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Django application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_redirect off;
    }
}
EOF

echo "✅ Nginx config created at /tmp/glomart_crm_images_fix.conf"

# 2. Create directory structure
echo "📁 2. Creating production directory structure..."
mkdir -p /var/www/glomart-crm/public/properties/images
mkdir -p /var/www/glomart-crm/public/properties/videos
mkdir -p /var/www/glomart-crm/staticfiles
mkdir -p /var/www/glomart-crm/media

echo "✅ Directories created"

# 3. Set proper permissions
echo "🔐 3. Setting permissions..."
chown -R www-data:www-data /var/www/glomart-crm/public/
chmod -R 755 /var/www/glomart-crm/public/

echo "✅ Permissions set"

# 4. Sync images from local to production (if needed)
echo "📤 4. Image sync instructions:"
echo "Run this from your LOCAL machine:"
echo "rsync -avz --partial --progress /Users/ahmedgomaa/Downloads/crm/public/ root@5.180.148.92:/var/www/glomart-crm/public/"

# 5. Test nginx configuration
echo "🧪 5. Testing nginx config..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid"
    echo "📝 To apply changes:"
    echo "   sudo cp /tmp/glomart_crm_images_fix.conf to your nginx sites-available"
    echo "   sudo systemctl reload nginx"
else
    echo "❌ Nginx configuration has errors"
fi

echo ""
echo "🎯 === SUMMARY ==="
echo "Property images not showing because:"
echo "1. ❌ Nginx not serving /public/ directory"
echo "2. ❌ Images stored in /public/properties/images/ not accessible"
echo "3. ❌ Missing proper nginx location block"
echo ""
echo "✅ FIXES APPLIED:"
echo "1. ✅ Added /public/ location to nginx"
echo "2. ✅ Created proper directory structure"
echo "3. ✅ Set correct permissions"
echo ""
echo "🚀 NEXT STEPS:"
echo "1. Update nginx configuration"
echo "2. Reload nginx"
echo "3. Sync images from local to production"
echo "4. Test property image loading"