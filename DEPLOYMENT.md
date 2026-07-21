# 🚀 Deployment Guide — PakChoice

This guide covers deploying the PakChoice application to a production Linux server (Ubuntu/Debian).

---

## 📋 Prerequisites

- Ubuntu 20.04+ or Debian 11+ server
- Python 3.8+
- MySQL 8.0+ or PostgreSQL 12+ (recommended over SQLite for production)
- Nginx
- Systemd
- SSL certificate (Let's Encrypt recommended)
- Domain name pointed to your server

---

## 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv \
    mysql-server nginx git curl
```

---

## 2. Database Setup (MySQL Example)

```bash
# Secure MySQL installation
sudo mysql_secure_installation

# Create database and user
sudo mysql -u root -p
```

```sql
CREATE DATABASE boycott_pk CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'boycott_pk'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON boycott_pk.* TO 'boycott_pk'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## 3. Application Setup

```bash
# Clone repository
cd /var/www
sudo git clone https://github.com/yourusername/pakistan-boycott-alternatives.git boycott_pk
cd boycott_pk

# Create virtual environment
sudo python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt gunicorn
```

---

## 4. Environment Configuration

Create a `.env` file in the project root:

```env
# Security
DEBUG=False
SECRET_KEY=your-production-secret-key-here-generate-with-openssl
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,127.0.0.1

# Database (MySQL example)
DB_ENGINE=django.db.backends.mysql
DB_NAME=boycott_pk
DB_USER=boycott_pk
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=3306

```

> **Important**: Generate a strong `SECRET_KEY`:
> ```bash
> python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

---

## 5. Django Configuration

```bash
# Activate virtual environment
source venv/bin/activate

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Load initial data (optional)
python manage.py loaddata data.json
```

---

## 6. Gunicorn Setup

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

```ini
[Unit]
Description=Gunicorn daemon for PakChoice
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/boycott_pk
Environment="PATH=/var/www/boycott_pk/venv/bin"
EnvironmentFile=/var/www/boycott_pk/.env
ExecStart=/var/www/boycott_pk/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/gunicorn.sock \
    --access-logfile /var/log/gunicorn-access.log \
    --error-logfile /var/log/gunicorn-error.log \
    boycott_pk.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start Gunicorn:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn

# Check status
sudo systemctl status gunicorn
```

---

## 7. Nginx Configuration

Create Nginx site configuration:

```bash
sudo nano /etc/nginx/sites-available/boycott_pk
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Client max body size (for avatar uploads)
    client_max_body_size 10M;

    # Static files
    location /static/ {
        root /var/www/boycott_pk/staticfiles;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files (user avatars)
    location /media/ {
        root /var/www/boycott_pk/media;
        expires 1d;
        add_header Cache-Control "public";
    }

    # Gunicorn proxy
    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/boycott_pk /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 8. SSL Certificate (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Certbot will automatically configure SSL and set up auto-renewal.

---

## 9. Firewall Configuration

```bash
# Allow SSH, HTTP, and HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 10. Log Rotation

Create log rotation for Gunicorn:

```bash
sudo nano /etc/logrotate.d/gunicorn
```

```
/var/log/gunicorn-*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    postrotate
        systemctl reload gunicorn
    endscript
}
```

---

## 11. Backup Strategy

### Database Backup

```bash
# Create backup script
sudo nano /usr/local/bin/backup_boycott_pk.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/boycott_pk"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# MySQL backup
mysqldump -u boycott_pk -p'your_secure_password' boycott_pk > $BACKUP_DIR/db_$DATE.sql

# Media files backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/boycott_pk/media

# Keep only last 7 days
find $BACKUP_DIR -type f -mtime +7 -delete
```

```bash
sudo chmod +x /usr/local/bin/backup_boycott_pk.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup_boycott_pk.sh
```

---

## 12. Monitoring & Maintenance

### Check Application Status

```bash
# Gunicorn status
sudo systemctl status gunicorn

# Nginx status
sudo systemctl status nginx

# View logs
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/nginx/error.log
```

### Update Application

```bash
cd /var/www/boycott_pk
sudo git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

---

## 13. Performance Optimization

### Enable Gzip Compression in Nginx

Add to your Nginx config:

```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript application/json image/svg+xml;
```

### Database Indexing

For large datasets, ensure proper indexes:

```sql
-- Run in MySQL
CREATE INDEX idx_alternative_status ON core_pakistanialternative(status);
CREATE INDEX idx_alternative_product ON core_pakistanialternative(product_id);
CREATE INDEX idx_product_verified ON core_boycottproduct(verified);
CREATE INDEX idx_product_subcategory ON core_boycottproduct(subcategory_id);
```

---

## 14. Security Checklist

- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` generated and stored securely
- [ ] `ALLOWED_HOSTS` configured with your domain only
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Database credentials stored in `.env` (not in code)
- [ ] Regular backups configured
- [ ] Firewall enabled (UFW)
- [ ] Server OS kept updated
- [ ] Gunicorn running as non-root user (`www-data`)
- [ ] File permissions restricted (static/media directories writable only by app user)

---

## 15. Troubleshooting

### 502 Bad Gateway
- Check Gunicorn is running: `sudo systemctl status gunicorn`
- Check socket permissions: `ls -la /run/gunicorn.sock`
- Check Gunicorn logs: `sudo journalctl -u gunicorn -n 50`

### Static Files Not Loading
- Run `python manage.py collectstatic --noinput`
- Check Nginx `root` path matches `STATIC_ROOT`
- Verify file permissions: `sudo chown -R www-data:www-data /var/www/boycott_pk/staticfiles`

### Database Connection Errors
- Verify MySQL is running: `sudo systemctl status mysql`
- Check credentials in `.env`
- Test connection: `mysql -u boycott_pk -p boycott_pk`

### Permission Denied on Media Uploads
```bash
sudo chown -R www-data:www-data /var/www/boycott_pk/media
sudo chmod -R 755 /var/www/boycott_pk/media
```

---

## Quick Reference Commands

```bash
# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# View logs
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/nginx/access.log

# Run Django management commands
cd /var/www/boycott_pk
source venv/bin/activate
python manage.py <command>

# Update application
cd /var/www/boycott_pk && sudo git pull && source venv/bin/activate && pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput && sudo systemctl restart gunicorn
```
