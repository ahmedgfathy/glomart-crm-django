# 🚀 Glomart CRM Deployment for Production Server
# Server: 5.180.148.92
# Domain: sys.glomartrealestates.com
# SAFE for existing iRedMail + MariaDB

## ⚡ Quick Deployment Commands

### Step 1: Upload deployment files
```bash
# From your local machine
scp -r deployment/ root@5.180.148.92:/root/glomart-deployment/
```

### Step 2: SSH to server and run setup
```bash
ssh root@5.180.148.92
cd /root/glomart-deployment
chmod +x *.sh
./01-safe-server-setup.sh
```

### Step 3: Setup database (isolated)
```bash
./safe-database-setup.sh
# Use these values when prompted:
# MariaDB root username: root
# MariaDB root password: ZeroCall20!@HH##1655&&
# CRM database name: glomart_crm
# CRM database user: crm_user
# CRM database password: [choose secure password]
```

### Step 4: Deploy application
```bash
sudo su - django-user
cd /var/www/glomart-crm
git clone https://github.com/ahmedgfathy/glomart-crm-django.git .
./deployment/02-app-deployment.sh
# Domain: sys.glomartrealestates.com
# Server IP: 5.180.148.92
```

### Step 5: Configure services
```bash
exit  # back to root
cd /root/glomart-deployment
./03-configure-services.sh
```

### Step 6: Setup SSL certificate
```bash
sudo certbot --nginx -d sys.glomartrealestates.com
```

## 🔒 Safety Guarantees
- ✅ iRedMail services: UNTOUCHED
- ✅ Existing databases: PROTECTED  
- ✅ Mail configurations: PRESERVED
- ✅ Only adds new isolated CRM system

## 📞 Access Details
- **URL**: https://sys.glomartrealestates.com
- **Admin**: Create during setup
- **42 Residential Users**: Already configured