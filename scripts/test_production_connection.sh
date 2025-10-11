#!/bin/bash
# Quick test of production database connection

echo "Testing production database connection..."
echo "Host: 5.180.148.92"
echo "Database: django_db_glomart_rs"
echo "User: root"

# Test connection with timeout
timeout 10 mysql -h5.180.148.92 -uroot -p'ZeroCall20!@HH##1655&&' django_db_glomart_rs -e "SELECT COUNT(*) as total_properties FROM properties_property;" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Production database connection successful!"
    echo "Getting table counts from production..."
    
    echo "Properties:"
    timeout 10 mysql -h5.180.148.92 -uroot -p'ZeroCall20!@HH##1655&&' django_db_glomart_rs -e "SELECT COUNT(*) FROM properties_property;" 2>/dev/null
    
    echo "Leads:"
    timeout 10 mysql -h5.180.148.92 -uroot -p'ZeroCall20!@HH##1655&&' django_db_glomart_rs -e "SELECT COUNT(*) FROM leads_lead;" 2>/dev/null
    
    echo "Projects:"  
    timeout 10 mysql -h5.180.148.92 -uroot -p'ZeroCall20!@HH##1655&&' django_db_glomart_rs -e "SELECT COUNT(*) FROM projects_project;" 2>/dev/null
    
else
    echo "❌ Cannot connect to production database"
    echo "Please check:"
    echo "1. Network connection"
    echo "2. Production server is accessible" 
    echo "3. Database credentials are correct"
    echo "4. Firewall allows connections on port 3306"
fi