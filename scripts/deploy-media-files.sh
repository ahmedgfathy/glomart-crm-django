#!/bin/bash

# Deploy media files script for Glomart CRM
# This script uploads property images and videos to the production server

set -e

# Configuration
SERVER_HOST="5.180.148.92"
SERVER_USER="root"
SSH_KEY="$HOME/.ssh/glomart_deploy"
LOCAL_MEDIA_PATH="/Users/ahmedgomaa/Downloads/crm/public/properties"
REMOTE_MEDIA_PATH="/var/www/glomart-crm/public/properties"

echo "========================================="
echo "  Glomart CRM Media Files Deployment"
echo "========================================="
echo "Local path: $LOCAL_MEDIA_PATH"
echo "Remote path: $REMOTE_MEDIA_PATH"
echo ""

# Check if local media directory exists
if [ ! -d "$LOCAL_MEDIA_PATH" ]; then
    echo "❌ Error: Local media directory not found: $LOCAL_MEDIA_PATH"
    exit 1
fi

# Count local files
LOCAL_FILES=$(find "$LOCAL_MEDIA_PATH" -type f | wc -l)
echo "📊 Total media files to upload: $LOCAL_FILES"

# Create remote directory structure
echo "📁 Creating remote directory structure..."
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "
    sudo -u django-user mkdir -p $REMOTE_MEDIA_PATH/{images,videos}
    sudo chown -R django-user:django-user /var/www/glomart-crm/public/
"

# Upload images
echo ""
echo "🖼️  Uploading property images..."
rsync -avz --progress \
    -e "ssh -i $SSH_KEY" \
    --include='*/' \
    --include='*.jpg' \
    --include='*.jpeg' \
    --include='*.png' \
    --include='*.gif' \
    --include='*.webp' \
    --exclude='*' \
    "$LOCAL_MEDIA_PATH/images/" \
    "$SERVER_USER@$SERVER_HOST:$REMOTE_MEDIA_PATH/images/"

# Upload videos
echo ""
echo "🎥 Uploading property videos..."
rsync -avz --progress \
    -e "ssh -i $SSH_KEY" \
    --include='*/' \
    --include='*.mp4' \
    --include='*.avi' \
    --include='*.mov' \
    --include='*.wmv' \
    --include='*.flv' \
    --include='*.webm' \
    --exclude='*' \
    "$LOCAL_MEDIA_PATH/videos/" \
    "$SERVER_USER@$SERVER_HOST:$REMOTE_MEDIA_PATH/videos/"

# Set correct permissions
echo ""
echo "🔐 Setting correct permissions..."
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "
    sudo chown -R django-user:django-user $REMOTE_MEDIA_PATH
    sudo chmod -R 755 $REMOTE_MEDIA_PATH
"

# Count uploaded files
echo ""
echo "🔍 Verifying upload..."
REMOTE_FILES=$(ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "find $REMOTE_MEDIA_PATH -type f | wc -l")
echo "📊 Remote files count: $REMOTE_FILES"

if [ "$REMOTE_FILES" -eq "$LOCAL_FILES" ]; then
    echo "✅ Media files deployment completed successfully!"
    echo "📍 Media files available at: http://sys.glomartrealestates.com/public/properties/"
else
    echo "⚠️  Warning: File count mismatch (Local: $LOCAL_FILES, Remote: $REMOTE_FILES)"
    echo "This might be normal if some file types were filtered out."
fi

echo ""
echo "🎉 Deployment Summary:"
echo "   • Local files: $LOCAL_FILES"
echo "   • Remote files: $REMOTE_FILES"
echo "   • Server: $SERVER_HOST"
echo "   • Path: $REMOTE_MEDIA_PATH"
echo ""
echo "You can now access the CRM at: http://sys.glomartrealestates.com"
echo "========================================="