#!/bin/bash
# Glomart CRM - Server Setup Script
# Run this script as root on a fresh Ubuntu server

set -e

echo "🚀 Starting Glomart CRM Server Setup..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root"
    exit 1
fi

print_status "Updating system packages..."
apt update && apt upgrade -y

print_status "Installing essential packages..."
apt install -y software-properties-common curl wget git unzip build-essential
apt install -y libssl-dev libffi-dev python3-dev libjpeg-dev zlib1g-dev libpng-dev

print_status "Installing Python 3.11..."
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Create Python symlink
ln -sf /usr/bin/python3.11 /usr/bin/python3

print_status "Installing MariaDB..."
apt install -y mariadb-server mariadb-client

print_status "Installing Nginx..."
apt install -y nginx

print_status "Installing additional tools..."
apt install -y certbot python3-certbot-nginx fail2ban htop ncdu tree

print_status "Creating django-user..."
if ! id "django-user" &>/dev/null; then
    adduser --disabled-password --gecos "" django-user
    usermod -aG sudo django-user
    print_status "django-user created successfully"
else
    print_warning "django-user already exists"
fi

print_status "Configuring firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

print_status "Starting and enabling services..."
systemctl start nginx
systemctl enable nginx
systemctl start mariadb
systemctl enable mariadb

print_status "Securing MariaDB installation..."
print_warning "Please run 'mysql_secure_installation' manually after this script completes"

print_status "Creating application directory..."
mkdir -p /var/www/glomart-crm
chown django-user:django-user /var/www/glomart-crm

print_status "Creating backup directories..."
mkdir -p /var/backups/glomart-crm/database
mkdir -p /var/backups/glomart-crm/files
chown -R django-user:django-user /var/backups/glomart-crm

print_status "Installing fail2ban configuration..."
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
EOF

systemctl restart fail2ban
systemctl enable fail2ban

print_status "✅ Server setup completed successfully!"
echo
print_warning "Next steps:"
echo "1. Run 'mysql_secure_installation' to secure MariaDB"
echo "2. Switch to django-user: sudo su - django-user"
echo "3. Run the application deployment script"
echo "4. Configure your domain name in the environment file"
echo
print_status "Server is ready for Django application deployment!"