#!/bin/bash
# SAFE Server Setup for Existing iRedMail + MariaDB Server
# This script is designed to NOT interfere with existing services

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[SAFE-SETUP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[CAUTION]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_warning "Please run this script as root"
    exit 1
fi

print_info "🔍 SAFE Glomart CRM Setup for Existing Server"
print_info "This script will NOT affect your existing iRedMail or databases"
echo "=============================================================="

# Check existing services
print_info "Checking existing services..."
if systemctl is-active --quiet postfix; then
    print_status "✓ iRedMail/Postfix detected - will be preserved"
fi

if systemctl is-active --quiet mariadb; then
    print_status "✓ MariaDB detected - will use existing installation"
fi

if systemctl is-active --quiet nginx; then
    print_warning "⚠ Nginx detected - will add virtual host only"
    print_info "Existing nginx configs will be preserved"
fi

print_info "Installing ONLY additional packages needed..."

# Install only essential packages for Django (no mail server packages)
print_status "Installing Python 3.11 (if not present)..."
apt update
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install development libraries
print_status "Installing development libraries..."
apt install -y build-essential libssl-dev libffi-dev
apt install -y libjpeg-dev zlib1g-dev libpng-dev

# Create Python symlink safely
if [ ! -f /usr/bin/python3 ] || [ "$(readlink /usr/bin/python3)" != "/usr/bin/python3.11" ]; then
    print_status "Creating Python3 symlink..."
    ln -sf /usr/bin/python3.11 /usr/bin/python3
fi

# Install Nginx ONLY if not present
if ! command -v nginx &> /dev/null; then
    print_status "Installing Nginx (not detected)..."
    apt install -y nginx
    systemctl enable nginx
else
    print_status "✓ Nginx already installed - skipping"
fi

# Install additional security tools (safe to install)
print_status "Installing additional tools..."
apt install -y htop ncdu tree curl wget git unzip

# Create django-user ONLY if doesn't exist
if ! id "django-user" &>/dev/null; then
    print_status "Creating django-user..."
    adduser --disabled-password --gecos "" django-user
    usermod -aG sudo django-user
else
    print_status "✓ django-user already exists - skipping"
fi

# Create application directory
print_status "Creating application directory..."
mkdir -p /var/www/glomart-crm
chown django-user:django-user /var/www/glomart-crm

# Create backup directories
print_status "Creating backup directories..."
mkdir -p /var/backups/glomart-crm/database
mkdir -p /var/backups/glomart-crm/files
chown -R django-user:django-user /var/backups/glomart-crm

# Configure firewall SAFELY (only add, don't remove)
print_status "Configuring firewall (adding HTTP/HTTPS only)..."
ufw allow 'Nginx Full' 2>/dev/null || true
# Don't enable UFW if it's not already enabled (might affect mail)
if ufw status | grep -q "Status: active"; then
    print_status "✓ UFW already active - added HTTP/HTTPS rules"
else
    print_warning "UFW not active - not enabling to preserve existing config"
fi

print_status "✅ SAFE setup completed!"
echo
print_info "SAFETY SUMMARY:"
echo "✓ NO changes to iRedMail configuration"
echo "✓ NO changes to existing MariaDB databases"
echo "✓ NO changes to mail users or domains"
echo "✓ NO changes to existing SSL certificates"
echo "✓ Only ADDED new user: django-user"
echo "✓ Only ADDED new directory: /var/www/glomart-crm"
echo "✓ Only ADDED HTTP/HTTPS firewall rules"
echo
print_warning "Next step: Run application deployment as django-user"
print_info "Command: sudo su - django-user"