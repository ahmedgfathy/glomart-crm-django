#!/bin/bash

# Upload Media Files to Production Server
# Run this script after the main deployment is complete

# Server Configuration
SERVER_IP="5.180.148.92"
SERVER_USER="root"
SSH_KEY="$HOME/.ssh/glomart_deploy"
LOCAL_MEDIA_PATH="/path/to/your/property-images"  # Update this path
LOCAL_VIDEOS_PATH="/path/to/your/property-videos"  # Update this path

echo "🚀 Uploading Property Media Files to Production Server..."

# Check if local media directories exist
if [ ! -d "$LOCAL_MEDIA_PATH" ]; then
    echo "❌ Local property images directory not found: $LOCAL_MEDIA_PATH"
    echo "Please update LOCAL_MEDIA_PATH in this script to point to your property images folder"
    exit 1
fi

# Create media directories on server
echo "📁 Creating media directories on server..."
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP << 'EOF'
    mkdir -p /var/www/glomart-crm/media/property-images
    mkdir -p /var/www/glomart-crm/media/property-videos
    mkdir -p /var/www/glomart-crm/media/documents
    chown -R django-user:www-data /var/www/glomart-crm/media
    chmod -R 755 /var/www/glomart-crm/media
EOF

# Upload property images
echo "🖼️ Uploading property images..."
if [ -d "$LOCAL_MEDIA_PATH" ]; then
    rsync -avz --progress -e "ssh -i $SSH_KEY" "$LOCAL_MEDIA_PATH/" $SERVER_USER@$SERVER_IP:/var/www/glomart-crm/media/property-images/
    echo "✅ Property images uploaded successfully"
else
    echo "⚠️ Property images directory not found, skipping..."
fi

# Upload property videos
echo "🎥 Uploading property videos..."
if [ -d "$LOCAL_VIDEOS_PATH" ]; then
    rsync -avz --progress -e "ssh -i $SSH_KEY" "$LOCAL_VIDEOS_PATH/" $SERVER_USER@$SERVER_IP:/var/www/glomart-crm/media/property-videos/
    echo "✅ Property videos uploaded successfully"
else
    echo "⚠️ Property videos directory not found, skipping..."
fi

# Set proper permissions on server
echo "🔒 Setting proper permissions..."
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP << 'EOF'
    chown -R django-user:www-data /var/www/glomart-crm/media
    find /var/www/glomart-crm/media -type d -exec chmod 755 {} \;
    find /var/www/glomart-crm/media -type f -exec chmod 644 {} \;
EOF

# Test media access
echo "🔍 Testing media file access..."
ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP << 'EOF'
    echo "Media directory structure:"
    ls -la /var/www/glomart-crm/media/
    echo ""
    echo "Property images count:"
    find /var/www/glomart-crm/media/property-images -name "*.jpg" -o -name "*.png" -o -name "*.jpeg" | wc -l
    echo ""
    echo "Property videos count:"
    find /var/www/glomart-crm/media/property-videos -name "*.mp4" -o -name "*.avi" -o -name "*.mov" | wc -l
EOF

echo ""
echo "🎉 Media Files Upload Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Update Django settings to serve media files correctly"
echo "2. Test property image loading: https://sys.glomartrealestates.com/properties/"
echo "3. Verify image URLs in property detail pages"
echo ""
echo "🔗 Media URLs will be accessible at:"
echo "   - Images: https://sys.glomartrealestates.com/media/property-images/"
echo "   - Videos: https://sys.glomartrealestates.com/media/property-videos/"