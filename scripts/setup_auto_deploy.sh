#!/bin/bash
# Auto-Deploy Setup Script for Glomart CRM
# This script sets up automatic deployment from GitHub

echo "=== Setting up Auto-Deploy for Glomart CRM ==="

# 1. Initialize Git repository in production
cd /var/www/glomart-crm
git init
git remote add origin https://github.com/ahmedgfathy/glomart-crm-django.git

# 2. Create deploy script
cat > /root/glomart-deployment/auto-deploy.sh << 'EOF'
#!/bin/bash

# Auto-deploy script for Glomart CRM
echo "Starting auto-deployment..."

cd /var/www/glomart-crm

# Backup current state
cp -r /var/www/glomart-crm /var/backups/glomart-crm-backup-$(date +%Y%m%d_%H%M%S)

# Pull latest changes
git fetch origin main
git reset --hard origin/main

# Set permissions
chown -R www-data:www-data /var/www/glomart-crm/
chmod -R 755 /var/www/glomart-crm/

# Activate virtual environment and run migrations
source venv/bin/activate
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Restart services
systemctl restart glomart-crm
systemctl reload nginx

echo "Deployment completed successfully!"
systemctl status glomart-crm --no-pager
EOF

chmod +x /root/glomart-deployment/auto-deploy.sh

# 3. Create webhook receiver script
cat > /root/glomart-deployment/webhook-deploy.py << 'EOF'
#!/usr/bin/env python3
"""
Simple webhook receiver for GitHub push events
Listens on port 9000 and triggers deployment
"""

import http.server
import subprocess
import json
import hmac
import hashlib
import os

WEBHOOK_SECRET = "your-webhook-secret-here"  # Change this!
DEPLOY_SCRIPT = "/root/glomart-deployment/auto-deploy.sh"

class WebhookHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/deploy':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Verify GitHub signature (optional but recommended)
            signature = self.headers.get('X-Hub-Signature-256')
            if signature:
                expected_signature = 'sha256=' + hmac.new(
                    WEBHOOK_SECRET.encode(),
                    post_data,
                    hashlib.sha256
                ).hexdigest()
                
                if not hmac.compare_digest(signature, expected_signature):
                    self.send_response(401)
                    self.end_headers()
                    return
            
            try:
                # Parse the payload
                payload = json.loads(post_data.decode())
                
                # Check if it's a push to main branch
                if payload.get('ref') == 'refs/heads/main':
                    print("Received push to main branch, triggering deployment...")
                    
                    # Run deployment script
                    subprocess.run([DEPLOY_SCRIPT], check=True)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'Deployment triggered successfully!')
                else:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'Not main branch, ignoring.')
                    
            except Exception as e:
                print(f"Deployment failed: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f'Deployment failed: {e}'.encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server = http.server.HTTPServer(('localhost', 9000), WebhookHandler)
    print("Webhook server starting on port 9000...")
    server.serve_forever()
EOF

chmod +x /root/glomart-deployment/webhook-deploy.py

# 4. Create systemd service for webhook
cat > /etc/systemd/system/glomart-webhook.service << 'EOF'
[Unit]
Description=Glomart CRM Webhook Deployment Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/glomart-deployment
ExecStart=/usr/bin/python3 /root/glomart-deployment/webhook-deploy.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start webhook service
systemctl daemon-reload
systemctl enable glomart-webhook
systemctl start glomart-webhook

echo "Auto-deploy setup completed!"
echo ""
echo "Next steps:"
echo "1. Add webhook URL to GitHub: http://your-server-ip:9000/deploy"
echo "2. Set webhook secret in /root/glomart-deployment/webhook-deploy.py"
echo "3. Test by pushing to GitHub"