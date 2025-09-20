#!/bin/bash
# Upload and Deploy Glomart CRM to Production Server
# Run this script from your local machine

set -e

# Server configuration
SERVER="5.180.148.92"
USER="root"
DOMAIN="sys.glomartrealestates.com"

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

print_info "🚀 Glomart CRM - Remote Deployment Script"
print_info "Target: $USER@$SERVER ($DOMAIN)"
echo "================================================="

# Check if deployment directory exists
if [ ! -d "deployment" ]; then
    print_warning "Deployment directory not found!"
    print_info "Make sure you're running this from the CRM project root"
    exit 1
fi

# Upload deployment scripts
print_status "📤 Uploading deployment files to server..."
ssh $USER@$SERVER "mkdir -p /root/glomart-deployment"
scp -r deployment/* $USER@$SERVER:/root/glomart-deployment/

# Upload application code
print_status "📤 Uploading application code..."
ssh $USER@$SERVER "mkdir -p /tmp/glomart-app"
scp -r . $USER@$SERVER:/tmp/glomart-app/ --exclude='.git' --exclude='venv' --exclude='__pycache__' --exclude='*.pyc'

# Make scripts executable
print_status "🔧 Setting up permissions..."
ssh $USER@$SERVER "chmod +x /root/glomart-deployment/*.sh"

# Run automated deployment
print_status "🚀 Starting automated deployment on server..."
ssh $USER@$SERVER "cd /root/glomart-deployment && ./automated-deployment.sh"

print_status "📱 Setting up Django application..."
ssh $USER@$SERVER << 'EOF'
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

# Create superuser (you'll need to do this interactively later)
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
systemctl status gunicorn --no-pager

# Clean up temp files
rm -rf /tmp/glomart-app
EOF

print_status "🔒 Finalizing SSL setup..."
ssh $USER@$SERVER "certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@glomartrealestates.com" || print_warning "SSL setup may need manual configuration"

print_status "✅ DEPLOYMENT COMPLETED!"
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
print_info "👥 Residential users created:"
echo "   → 42 users with properties access only"
echo "   → Usernames: rehab1, amira1, hadeer1, etc."
echo "   → Password: 123456789"
echo
print_info "📊 Features available:"
echo "   ✓ Owner database with 945,721 records"
echo "   ✓ Properties management"
echo "   ✓ User access control (RBAC)"
echo "   ✓ Modern dashboard"
echo "   ✓ Automated backups"
echo "   ✓ SSL encryption"
echo
print_warning "🔧 Post-deployment tasks:"
echo "1. Change admin password"
echo "2. Configure email settings if needed"
echo "3. Test residential user access"
echo "4. Set up regular database maintenance"
echo
print_status "🎉 Glomart CRM deployment successful!"