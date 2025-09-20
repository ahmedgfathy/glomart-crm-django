#!/bin/bash
# Deploy Core Application Only (without media files)
# This is a lightweight deployment for the Django application

set -e

# Server configuration
SERVER="5.180.148.92"
USER="root"
DOMAIN="sys.glomartrealestates.com"
SSH_KEY="$HOME/.ssh/glomart_deploy"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[LOCAL]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info "🚀 Glomart CRM - Core Application Deployment"
print_info "Target: $USER@$SERVER ($DOMAIN)"
echo "================================================="

# Upload deployment scripts only
print_status "📤 Uploading deployment scripts..."
ssh -i $SSH_KEY $USER@$SERVER "mkdir -p /root/glomart-deployment"
scp -i $SSH_KEY -r deployment/* $USER@$SERVER:/root/glomart-deployment/

# Upload core application code (without media)
print_status "📤 Uploading core application code..."
ssh -i $SSH_KEY $USER@$SERVER "mkdir -p /tmp/glomart-app"

# Create a temporary tar file excluding large directories
print_status "📦 Creating application package..."
tar -czf /tmp/glomart-core.tar.gz \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='db.sqlite3' \
    --exclude='.DS_Store' \
    --exclude='node_modules' \
    --exclude='public/properties' \
    --exclude='media' \
    --exclude='staticfiles' \
    .

# Upload the tar file
print_status "📤 Uploading application package..."
scp -i $SSH_KEY /tmp/glomart-core.tar.gz $USER@$SERVER:/tmp/

# Extract on server
print_status "📦 Extracting application on server..."
ssh -i $SSH_KEY $USER@$SERVER "cd /tmp && tar -xzf glomart-core.tar.gz -C glomart-app/"

# Make scripts executable
print_status "🔧 Setting up permissions..."
ssh -i $SSH_KEY $USER@$SERVER "chmod +x /root/glomart-deployment/*.sh"

# Run automated deployment
print_status "🚀 Starting automated deployment on server..."
ssh -i $SSH_KEY $USER@$SERVER "cd /root/glomart-deployment && ./automated-deployment.sh"

print_status "📱 Setting up Django application..."
ssh -i $SSH_KEY $USER@$SERVER << 'EOF'
# Copy application files
sudo -u django-user cp -r /tmp/glomart-app/* /var/www/glomart-crm/
sudo -u django-user chown -R django-user:django-user /var/www/glomart-crm

# Setup Django application
sudo -u django-user bash << 'DJANGO_SETUP'
cd /var/www/glomart-crm
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs media staticfiles

# Set Django settings
export DJANGO_SETTINGS_MODULE=real_estate_crm.settings_production

# Run migrations
python manage.py migrate

# Create superuser
echo "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@glomartrealestates.com', 'admin123')" | python manage.py shell

# Collect static files
python manage.py collectstatic --noinput

# Create residential users
if [ -f "authentication/management/commands/create_residential_users_v2.py" ]; then
    python manage.py create_residential_users_v2
fi

DJANGO_SETUP

# Start services
systemctl start gunicorn
systemctl enable gunicorn
systemctl start nginx
systemctl enable nginx

# Check service status
systemctl status gunicorn --no-pager
systemctl status nginx --no-pager

# Clean up temp files
rm -rf /tmp/glomart-app /tmp/glomart-core.tar.gz
EOF

print_status "🔒 Setting up SSL..."
ssh -i $SSH_KEY $USER@$SERVER "certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@glomartrealestates.com" || print_warning "SSL setup may need manual configuration"

# Clean up local temp file
rm -f /tmp/glomart-core.tar.gz

print_status "✅ CORE APPLICATION DEPLOYED!"
echo "================================================="
print_info "🌐 Your CRM is now live at:"
echo "   → https://$DOMAIN"
echo "   → https://$SERVER (IP access)"
echo
print_info "🔐 Default admin credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo "   ⚠️  CHANGE THIS IMMEDIATELY!"
echo
print_info "📊 Next steps:"
echo "1. Test the application: https://$DOMAIN"
echo "2. Upload media files with: ./deployment/upload-media-files.sh"
echo "3. Test residential user access"
echo "4. Change admin password"
echo
print_status "🎉 Core deployment successful!"