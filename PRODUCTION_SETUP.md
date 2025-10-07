# Production Deployment Guide - Legal Notification System

## System Overview

**Domain:** https://backend.sindipro.com.br
**Database:** PostgreSQL (`legal_docs_legaltemplate` table)
**Email Service:** Gmail SMTP
**Task Queue:** Celery + Redis

## How It Works

1. **POST** request to `/api/legal/template/` creates a Legal Template
2. Data is saved to `legal_docs_legaltemplate` table
3. Email notification is scheduled automatically:
   - **Date:** `dueMonth - noticePeriod` days
   - **Time:** 9:00 AM
   - **Recipients:** emails in `responsibleEmails` field

## Production Setup Steps

### 1. Install Dependencies

```bash
cd /var/www/sindipro
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Database Migration

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Environment Variables (`.env`)

Ensure these are configured:

```env
# Email Configuration (Gmail SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Sindipro <your-gmail@gmail.com>

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 4. Start Redis

```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server
sudo systemctl status redis-server
```

### 5. Deploy Celery Services

#### Create Celery Worker Service

Create `/etc/systemd/system/celery-sindipro.service`:

```ini
[Unit]
Description=Celery Worker for Sindipro
After=network.target redis-server.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/var/www/sindipro
Environment="PATH=/var/www/sindipro/venv/bin"
ExecStart=/var/www/sindipro/venv/bin/celery -A sindipro_backend worker --loglevel=info --logfile=/var/log/celery/worker.log --detach
ExecStop=/var/www/sindipro/venv/bin/celery -A sindipro_backend control shutdown
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Create Celery Beat Service

Create `/etc/systemd/system/celerybeat-sindipro.service`:

```ini
[Unit]
Description=Celery Beat Scheduler for Sindipro
After=network.target redis-server.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/sindipro
Environment="PATH=/var/www/sindipro/venv/bin"
ExecStart=/var/www/sindipro/venv/bin/celery -A sindipro_backend beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler --logfile=/var/log/celery/beat.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Create Log Directory

```bash
sudo mkdir -p /var/log/celery
sudo chown www-data:www-data /var/log/celery
```

#### Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl start celery-sindipro
sudo systemctl start celerybeat-sindipro
sudo systemctl enable celery-sindipro
sudo systemctl enable celerybeat-sindipro
```

#### Check Status

```bash
sudo systemctl status celery-sindipro
sudo systemctl status celerybeat-sindipro
```

## API Usage

### Create Legal Template with Email Notification

**Endpoint:** `POST https://backend.sindipro.com.br/api/legal/template/`

**Headers:**
```
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Fire Safety Inspection",
  "description": "Annual fire safety inspection requirement",
  "dueMonth": "2025-12-31",
  "noticePeriod": 14,
  "responsibleEmails": "admin@sindipro.com.br, safety@sindipro.com.br",
  "frequency": "annual",
  "requiresQuote": false
}
```

**Response:**
```json
{
  "message": "Legal template created successfully",
  "template_id": 1,
  "template_name": "Fire Safety Inspection"
}
```

**Result:**
- Template saved to `legal_docs_legaltemplate` table
- Email scheduled for **2025-12-17 at 9:00 AM**
- Sent to: `admin@sindipro.com.br`, `safety@sindipro.com.br`

## Monitoring & Troubleshooting

### Check Celery Logs

```bash
# Worker logs
sudo tail -f /var/log/celery/worker.log

# Beat logs
sudo tail -f /var/log/celery/beat.log
```

### Check Scheduled Tasks

Django Admin: `https://backend.sindipro.com.br/admin/django_celery_beat/periodictask/`

### Restart Services

```bash
sudo systemctl restart celery-sindipro
sudo systemctl restart celerybeat-sindipro
```

### Test Email Manually

```bash
cd /var/www/sindipro
python test_email.py recipient@example.com
```

### Common Issues

**Emails not sending?**
1. Check Gmail app password is correct
2. Verify Celery Worker is running: `sudo systemctl status celery-sindipro`
3. Verify Celery Beat is running: `sudo systemctl status celerybeat-sindipro`
4. Check Redis: `redis-cli ping` (should return `PONG`)
5. Check logs: `/var/log/celery/worker.log`

**Task not scheduled?**
1. Verify `dueMonth`, `noticePeriod`, and `responsibleEmails` are provided
2. Check scheduled tasks in Django Admin
3. Check Beat logs: `/var/log/celery/beat.log`

## Security Checklist

- [ ] Gmail app password in `.env` (not in git)
- [ ] `.env` file permissions: `chmod 600 .env`
- [ ] Redis password configured (production)
- [ ] Celery services running as `www-data` user
- [ ] Log files readable by admin only

## Production Workflow

1. **Developer** creates Legal Template via API
2. **Django** saves to database (`legal_docs_legaltemplate`)
3. **Django** schedules Celery task automatically
4. **Celery Beat** monitors schedule
5. **Celery Worker** sends email at scheduled time
6. **Recipients** receive notification via Gmail SMTP

---

**Status:** ✅ Production Ready

All components configured for `https://backend.sindipro.com.br`
