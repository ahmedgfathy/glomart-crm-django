# 📚 Deployment Scripts README

This directory contains automated scripts for deploying and maintaining the Glomart CRM system in production.

## 🚀 Quick Start

### For a fresh server deployment:

1. **Server Setup** (run as root):
   ```bash
   chmod +x 01-server-setup.sh
   sudo ./01-server-setup.sh
   ```

2. **Application Deployment** (run as django-user):
   ```bash
   chmod +x 02-app-deployment.sh
   ./02-app-deployment.sh
   ```

3. **Services Configuration** (run as root):
   ```bash
   chmod +x 03-configure-services.sh
   sudo ./03-configure-services.sh
   ```

4. **SSL Certificate** (run as root):
   ```bash
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

## 📁 Script Descriptions

### `01-server-setup.sh`
- **Purpose**: Initial server configuration
- **Run as**: root
- **What it does**:
  - Updates system packages
  - Installs Python 3.11, MariaDB, Nginx
  - Creates django-user
  - Configures firewall
  - Sets up fail2ban for security

### `02-app-deployment.sh`
- **Purpose**: Deploy the Django application
- **Run as**: django-user
- **What it does**:
  - Clones the repository
  - Sets up virtual environment
  - Creates environment configuration
  - Runs Django migrations
  - Collects static files
  - Creates superuser

### `03-configure-services.sh`
- **Purpose**: Configure production services
- **Run as**: root
- **What it does**:
  - Sets up Gunicorn service
  - Configures Nginx with security headers
  - Creates backup and monitoring scripts
  - Sets up log rotation
  - Configures cron jobs

### `update-app.sh`
- **Purpose**: Update application with zero downtime
- **Run as**: django-user
- **What it does**:
  - Creates backup before update
  - Pulls latest code
  - Updates dependencies
  - Runs migrations
  - Restarts services

### `monitor-system.sh`
- **Purpose**: System health monitoring
- **Run as**: any user (preferably via cron)
- **What it does**:
  - Checks service status
  - Monitors disk and memory usage
  - Tests website availability
  - Checks database connectivity
  - Sends email alerts on issues

### `database-maintenance.sh`
- **Purpose**: Database optimization and maintenance
- **Run as**: django-user (preferably via cron)
- **What it does**:
  - Creates verified backups
  - Optimizes database tables
  - Cleans up sessions and logs
  - Checks database integrity
  - Updates statistics

## ⚙️ Configuration Files

### `.env.example`
Template for environment variables. Copy to `.env` and update:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### `requirements-production.txt`
Production-specific Python packages including:
- Security packages
- Production servers (Gunicorn)
- Monitoring tools
- Performance optimizations

## 📋 Pre-deployment Checklist

Before running the deployment scripts:

- [ ] Server with Ubuntu 20.04+ or CentOS 8+
- [ ] Root access to the server
- [ ] Domain name configured (DNS pointing to server)
- [ ] GitHub repository accessible
- [ ] Database credentials prepared
- [ ] Email SMTP settings (for notifications)

## 🔧 Post-deployment Tasks

After successful deployment:

1. **Test the application**:
   ```bash
   curl -I http://yourdomain.com
   ```

2. **Set up SSL certificate**:
   ```bash
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

3. **Configure monitoring**:
   ```bash
   # Add to crontab
   sudo crontab -e
   # Add: */15 * * * * /path/to/monitor-system.sh
   ```

4. **Test backup system**:
   ```bash
   sudo /usr/local/bin/backup-crm.sh
   ```

5. **Configure email notifications**:
   - Update ALERT_EMAIL in monitor-system.sh
   - Test email functionality

## 🚨 Troubleshooting

### Common Issues:

1. **Gunicorn won't start**:
   ```bash
   sudo journalctl -u gunicorn -f
   ```

2. **Nginx configuration errors**:
   ```bash
   sudo nginx -t
   sudo tail -f /var/log/nginx/error.log
   ```

3. **Database connection issues**:
   ```bash
   mysql -u crm_user -p -h localhost glomart_crm
   ```

4. **Permission problems**:
   ```bash
   sudo chown -R django-user:django-user /var/www/glomart-crm
   ```

### Log Locations:
- Application logs: `/var/www/glomart-crm/logs/django.log`
- Nginx logs: `/var/log/nginx/error.log`
- Gunicorn logs: `sudo journalctl -u gunicorn`
- System logs: `/var/log/syslog`

## 🔄 Update Process

To update the application:

1. **Automatic update**:
   ```bash
   cd /var/www/glomart-crm/deployment
   ./update-app.sh
   ```

2. **Manual update**:
   ```bash
   cd /var/www/glomart-crm
   git pull origin main
   source venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py collectstatic --noinput
   sudo systemctl restart gunicorn
   ```

## 📊 Monitoring

The monitoring system provides:
- **Real-time health checks** (every 15 minutes)
- **Email alerts** for critical issues
- **Resource monitoring** (disk, memory, CPU)
- **Application status** checks
- **Database connectivity** tests

View monitoring logs:
```bash
tail -f /var/log/crm-monitor.log
```

## 🔐 Security Features

The deployment includes:
- **Firewall configuration** (UFW)
- **Fail2ban** intrusion prevention
- **SSL/TLS encryption** (via Let's Encrypt)
- **Security headers** in Nginx
- **Rate limiting** for API endpoints
- **Secure file permissions**
- **Database user isolation**

## 📈 Performance Optimization

Production configuration includes:
- **Gunicorn** with optimized worker settings
- **Nginx** with compression and caching
- **Database** optimization and indexing
- **Static file** compression and CDN-ready
- **Log rotation** to prevent disk fill
- **Memory** and CPU monitoring

## 🆘 Support

For deployment issues:
1. Check the logs mentioned above
2. Verify all environment variables in `.env`
3. Ensure all services are running: `sudo systemctl status gunicorn nginx mariadb`
4. Test database connectivity
5. Check firewall settings: `sudo ufw status`

## 📞 Emergency Procedures

If the site goes down:

1. **Quick restart**:
   ```bash
   sudo systemctl restart gunicorn nginx
   ```

2. **Check logs**:
   ```bash
   sudo journalctl -u gunicorn -n 50
   tail -50 /var/log/nginx/error.log
   ```

3. **Restore from backup**:
   ```bash
   # Find latest backup
   ls -la /var/backups/glomart-crm/database/
   # Restore database
   gunzip < backup_file.sql.gz | mysql -u crm_user -p glomart_crm
   ```

4. **Contact support** with log output and error details.