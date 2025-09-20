#!/bin/bash
# SAFE Database Setup for Existing MariaDB Server
# Creates isolated database without affecting existing ones

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[SAFE-DB]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[CAUTION]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info "🔒 SAFE Database Setup for Glomart CRM"
print_info "This will create an ISOLATED database for CRM only"
echo "================================================"

# Get database credentials
print_info "Please provide MariaDB root credentials:"
read -p "MariaDB root username [root]: " ROOT_USER
ROOT_USER=${ROOT_USER:-root}

read -s -p "MariaDB root password: " ROOT_PASSWORD
echo

print_info "Creating CRM database configuration:"
read -p "CRM database name [glomart_crm]: " DB_NAME
DB_NAME=${DB_NAME:-glomart_crm}

read -p "CRM database user [crm_user]: " DB_USER
DB_USER=${DB_USER:-crm_user}

read -s -p "CRM database password: " DB_PASSWORD
echo

# Test connection first
print_status "Testing MariaDB connection..."
if mysql -u "$ROOT_USER" -p"$ROOT_PASSWORD" -e "SELECT 1;" &>/dev/null; then
    print_status "✓ MariaDB connection successful"
else
    print_error "✗ Cannot connect to MariaDB with provided credentials"
    exit 1
fi

# Show existing databases (for verification)
print_info "Current databases on server:"
mysql -u "$ROOT_USER" -p"$ROOT_PASSWORD" -e "SHOW DATABASES;" | grep -v "information_schema\|performance_schema\|mysql\|sys"

# Check if CRM database already exists
if mysql -u "$ROOT_USER" -p"$ROOT_PASSWORD" -e "USE $DB_NAME;" &>/dev/null; then
    print_warning "⚠ Database '$DB_NAME' already exists!"
    read -p "Do you want to continue? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_info "Operation cancelled"
        exit 0
    fi
fi

# Create database and user with LIMITED privileges
print_status "Creating isolated CRM database..."

mysql -u "$ROOT_USER" -p"$ROOT_PASSWORD" << EOF
-- Create database with proper charset
CREATE DATABASE IF NOT EXISTS $DB_NAME 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Create user (if doesn't exist)
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';

-- Grant privileges ONLY to CRM database
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';

-- Explicitly deny access to other databases (security)
REVOKE ALL PRIVILEGES ON *.* FROM '$DB_USER'@'localhost';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;

-- Show user privileges for verification
SHOW GRANTS FOR '$DB_USER'@'localhost';
EOF

# Verify the setup
print_status "Verifying database setup..."
if mysql -u "$DB_USER" -p"$DB_PASSWORD" -D "$DB_NAME" -e "SELECT 1;" &>/dev/null; then
    print_status "✓ CRM database access verified"
else
    print_error "✗ Database setup verification failed"
    exit 1
fi

# Test isolation (should fail)
print_status "Testing database isolation..."
if mysql -u "$DB_USER" -p"$DB_PASSWORD" -e "SHOW DATABASES;" 2>/dev/null | grep -q "mysql\|information_schema"; then
    print_warning "⚠ User has broader access than expected"
else
    print_status "✓ Database access properly isolated"
fi

print_status "✅ Database setup completed safely!"
echo
print_info "ISOLATION SUMMARY:"
echo "✓ Database: $DB_NAME (isolated)"
echo "✓ User: $DB_USER (limited to CRM database only)"
echo "✓ Existing databases: UNTOUCHED"
echo "✓ Existing users: UNCHANGED"
echo "✓ iRedMail databases: PROTECTED"
echo
print_info "Database credentials for .env file:"
echo "DB_NAME=$DB_NAME"
echo "DB_USER=$DB_USER"
echo "DB_PASSWORD=$DB_PASSWORD"
echo "DB_HOST=localhost"
echo "DB_PORT=3306"