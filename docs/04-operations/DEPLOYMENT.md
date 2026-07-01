# Deployment Guide

## Overview

This guide covers deploying the Flask application to production environments, including server setup, database configuration, and best practices.

**See also:** [INFRASTRUCTURE.md](INFRASTRUCTURE.md) for Phase 1.5 (backup automation, Redis, Celery Beat/Flower, Sentry, DB indexes).

## Prerequisites

- Production server (Linux recommended)
- PostgreSQL database server
- Domain name and SSL certificate
- Reverse proxy (Nginx or Apache)
- Process manager (systemd, supervisor, or gunicorn)

## Pre-Deployment Checklist

- [ ] All environment variables configured
- [ ] Database migrations run
- [ ] Secret keys generated and secure
- [ ] Database backups configured
- [ ] SSL certificate obtained
- [ ] Firewall configured
- [ ] Monitoring setup
- [ ] Log rotation configured

## Server Setup

### 1. System Requirements

**Minimum:**
- 2 CPU cores
- 4GB RAM
- 20GB disk space

**Recommended:**
- 4+ CPU cores
- 8GB+ RAM
- 50GB+ disk space
- SSD storage

### 2. Operating System

**Ubuntu 22.04 LTS (Recommended)**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.14 python3.14-venv python3-pip postgresql nginx git -y
```

### 3. Create Application User

```bash
# Create dedicated user
sudo adduser --system --group --home /var/www/boilerplate flaskapp

# Add to necessary groups
sudo usermod -aG www-data flaskapp
```

### 4. Clone Application

```bash
# Switch to application user
sudo su - flaskapp

# Clone repository
git clone <repository-url> /var/www/boilerplate/app
cd /var/www/boilerplate/app

# Create virtual environment
python3.14 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Database Setup

### 1. PostgreSQL Configuration

```bash
# Create database and user
sudo -u postgres psql

CREATE DATABASE boilerplate_prod;
CREATE USER boilerplate_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE boilerplate_prod TO boilerplate_user;
\q
```

### 2. Run Migrations

```bash
# Set production environment
export FLASK_ENV=production

# Run schema migration
python3 scripts/migrate_to_schemas.py --confirm --superuser postgres

# Run Flask migrations
flask db upgrade
```

### 3. Create Initial Data

```bash
# Create default roles and users
python3 scripts/create_default_roles_groups.py
python3 scripts/create_user.py
```

## Application Configuration

### 1. Environment Variables

Create `/var/www/boilerplate/app/.env`:

```env
# Flask
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=<strong-random-key>

# Database
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=boilerplate_prod
DB_USER=boilerplate_user
DB_PASSWORD=strong_password

# PostgreSQL Superuser (for migrations)
POSTGRES_SUPERUSER=postgres
POSTGRES_SUPERUSER_PASSWORD=postgres_password

# Application
APP_NAME=Your Application
COMPANY_NAME=Your Company

# Security
JWT_SECRET_KEY=<strong-random-key>

# Email (if using)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Cache (if using Redis)
REDIS_URL=redis://localhost:6379/0
CACHE_TYPE=redis
```

**Secure the file:**
```bash
chmod 600 .env
chown flaskapp:flaskapp .env
```

### 2. Generate Secret Keys

```bash
python3 scripts/generate_secret_key.py
# Use output for SECRET_KEY and JWT_SECRET_KEY
```

## Process Management

### Option 1: systemd (Recommended)

**Create service file:** `/etc/systemd/system/boilerplate.service`

```ini
[Unit]
Description=Flask Boilerplate Application
After=network.target postgresql.service

[Service]
User=flaskapp
Group=flaskapp
WorkingDirectory=/var/www/boilerplate/app
Environment="PATH=/var/www/boilerplate/app/venv/bin"
ExecStart=/var/www/boilerplate/app/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5000 \
    --timeout 120 \
    --access-logfile /var/log/boilerplate/access.log \
    --error-logfile /var/log/boilerplate/error.log \
    run:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable boilerplate
sudo systemctl start boilerplate
sudo systemctl status boilerplate
```

### Option 2: Gunicorn Directly

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn --workers 4 --bind 127.0.0.1:5000 run:app
```

### Option 3: Supervisor

**Install supervisor:**
```bash
sudo apt install supervisor
```

**Create config:** `/etc/supervisor/conf.d/boilerplate.conf`

```ini
[program:boilerplate]
command=/var/www/boilerplate/app/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 run:app
directory=/var/www/boilerplate/app
user=flaskapp
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/boilerplate/supervisor.log
```

**Start:**
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start boilerplate
```

## Reverse Proxy (Nginx)

### 1. Install Nginx

```bash
sudo apt install nginx
```

### 2. Create Nginx Configuration

**Create:** `/etc/nginx/sites-available/boilerplate`

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Logging
    access_log /var/log/nginx/boilerplate_access.log;
    error_log /var/log/nginx/boilerplate_error.log;
    
    # Client body size
    client_max_body_size 16M;
    
    # Proxy to Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Static files
    location /static {
        alias /var/www/boilerplate/app/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Favicon
    location /favicon.ico {
        alias /var/www/boilerplate/app/app/static/favicon.ico;
        access_log off;
    }
}
```

### 3. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/boilerplate /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (already configured)
sudo certbot renew --dry-run
```

## Database Backup

### Automated Backups

**Create backup script:** `/usr/local/bin/backup-boilerplate.sh`

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/boilerplate"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="boilerplate_prod"
DB_USER="boilerplate_user"

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: db_$DATE.sql.gz"
```

**Make executable:**
```bash
sudo chmod +x /usr/local/bin/backup-boilerplate.sh
```

**Add to crontab:**
```bash
# Daily backup at 2 AM
0 2 * * * /usr/local/bin/backup-boilerplate.sh >> /var/log/boilerplate/backup.log 2>&1
```

## Monitoring

### 1. Application Logs

**Log locations:**
- Application logs: `logs/app.log`
- Access logs: `/var/log/boilerplate/access.log`
- Error logs: `/var/log/boilerplate/error.log`
- Nginx logs: `/var/log/nginx/boilerplate_*.log`

### 2. Health Checks

**Application health:**
```bash
curl http://localhost:5000/health
curl http://localhost:5000/health/database
```

**Set up monitoring:**
- Uptime monitoring (UptimeRobot, Pingdom)
- Error tracking (Sentry, Rollbar)
- Performance monitoring (New Relic, Datadog)

### 3. Log Rotation

**Create:** `/etc/logrotate.d/boilerplate`

```
/var/www/boilerplate/app/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 flaskapp flaskapp
    sharedscripts
    postrotate
        systemctl reload boilerplate > /dev/null 2>&1 || true
    endscript
}
```

## Security Hardening

### 1. Firewall Configuration

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Database Security

```bash
# Edit PostgreSQL config
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Only allow local connections
host    all    all    127.0.0.1/32    md5
```

### 3. Application Security

- Use strong secret keys
- Enable CSRF protection
- Use HTTPS only
- Set secure cookie flags
- Regular security updates

### 4. File Permissions

```bash
# Application files
sudo chown -R flaskapp:flaskapp /var/www/boilerplate/app
sudo chmod -R 755 /var/www/boilerplate/app
sudo chmod 600 /var/www/boilerplate/app/.env

# Logs
sudo chown -R flaskapp:flaskapp /var/log/boilerplate
sudo chmod -R 755 /var/log/boilerplate
```

## Performance Optimization

### 1. Database Optimization

```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_users_username ON auth.users(username);
CREATE INDEX idx_accounts_name ON accounts.accounts(account_name);
```

### 2. Caching

**Redis setup:**
```bash
sudo apt install redis-server
sudo systemctl enable redis
sudo systemctl start redis
```

**Configure in .env:**
```env
REDIS_URL=redis://localhost:6379/0
CACHE_TYPE=redis
```

### 3. Static File Serving

Nginx serves static files directly (configured above).

### 4. Gunicorn Workers

**Calculate workers:**
```
workers = (2 × CPU cores) + 1
```

**Example (4 cores):**
```bash
gunicorn --workers 9 --bind 127.0.0.1:5000 run:app
```

## Deployment Process

### 1. Update Code

```bash
cd /var/www/boilerplate/app
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Migrations

```bash
flask db upgrade
python3 scripts/migrate_to_schemas.py --confirm  # If schema changes
```

### 3. Restart Application

```bash
sudo systemctl restart boilerplate
# Or
sudo supervisorctl restart boilerplate
```

### 4. Verify Deployment

```bash
# Check application status
sudo systemctl status boilerplate

# Check logs
tail -f /var/log/boilerplate/error.log

# Test endpoints
curl http://localhost:5000/health
```

## Rollback Procedure

### 1. Restore Previous Version

```bash
cd /var/www/boilerplate/app
git checkout <previous-commit>
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart boilerplate
```

### 2. Database Rollback

```bash
# Rollback migrations
flask db downgrade <revision>

# Or restore from backup
gunzip < backup.sql.gz | psql -U boilerplate_user boilerplate_prod
```

## Troubleshooting

### Application Won't Start

1. Check logs: `journalctl -u boilerplate -n 50`
2. Verify environment variables
3. Check database connection
4. Verify file permissions

### Database Connection Issues

1. Verify PostgreSQL is running: `sudo systemctl status postgresql`
2. Check credentials in `.env`
3. Test connection: `psql -U boilerplate_user -d boilerplate_prod`
4. Check firewall rules

### High Memory Usage

1. Reduce Gunicorn workers
2. Enable Redis caching
3. Optimize database queries
4. Check for memory leaks

### Slow Performance

1. Check database indexes
2. Enable caching (Redis)
3. Optimize static file serving
4. Review slow query log
5. Increase server resources

## Maintenance

### Regular Tasks

**Daily:**
- Monitor logs for errors
- Check disk space
- Verify backups completed

**Weekly:**
- Review security logs
- Check application performance
- Update dependencies (if needed)

**Monthly:**
- Security updates
- Database optimization
- Backup restoration test
- Review and rotate logs

## See Also

- [GETTING_STARTED.md](GETTING_STARTED.md) - Initial setup
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration details
- [SCHEMA_MIGRATION.md](SCHEMA_MIGRATION.md) - Database migrations
