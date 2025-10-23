# 🚨 URGENT: Fix Production Server Issues

## Issue 1: Log File Permissions Error
The service is failing because gunicorn can't write to the log file.

### Fix Log Permissions (Run these commands on your server):

```bash
# Create logs directory if it doesn't exist
mkdir -p /var/www/glomart-crm/logs

# Fix ownership of the entire project
sudo chown -R www-data:www-data /var/www/glomart-crm/

# Make sure logs directory is writable
sudo chmod -R 755 /var/www/glomart-crm/logs/

# Alternative: Create log files manually with correct permissions
sudo touch /var/www/glomart-crm/logs/gunicorn-error.log
sudo touch /var/www/glomart-crm/logs/gunicorn-access.log
sudo chown www-data:www-data /var/www/glomart-crm/logs/*.log
sudo chmod 664 /var/www/glomart-crm/logs/*.log
```

## Issue 2: Update Service Configuration
The service might be trying to use a gunicorn config that specifies log files. Let's simplify it:

```bash
# Check current service configuration
sudo nano /etc/systemd/system/glomart-crm.service
```

**Replace the ExecStart line with this simpler version:**
```ini
ExecStart=/bin/bash -c 'cd /var/www/glomart-crm && source venv/bin/activate && exec gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 30 real_estate_crm.wsgi:application'
```

**Then reload and restart:**
```bash
sudo systemctl daemon-reload
sudo systemctl restart glomart-crm
sudo systemctl status glomart-crm
```

## Issue 3: Git Authentication (Optional - for future deployments)
GitHub now requires Personal Access Tokens. You have two options:

### Option A: Skip git push for now (Recommended)
Just ignore the git sync issue for now. Your site will work fine.

### Option B: Set up GitHub token (for future)
1. Go to https://github.com/settings/tokens
2. Generate a Personal Access Token
3. Use it instead of password

## Quick Test Commands:
```bash
# Test if the service starts now
sudo systemctl restart glomart-crm
sleep 5
sudo systemctl status glomart-crm

# Test if website responds
curl -I http://127.0.0.1:8000/

# If successful, test the dashboard
curl -I http://127.0.0.1:8000/dashboard/
```

## Expected Results:
- Service should show "Active: active (running)"
- Website should return HTTP 200 or 302 (both are good)
- Dashboard should redirect to login (302) - this is correct!

Run these commands in order and let me know the results!