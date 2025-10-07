# Legal Obligation Email Notification Setup Guide

## Overview
This system automatically sends email notifications when legal obligation expiration dates are approaching.

## How It Works
1. When a Legal Template is created via POST `/api/legal/template/` request
2. Notification is scheduled for `dueMonth - noticePeriod` days
3. Automatically sent to email addresses in `responsibleEmails`

### Example
- `dueMonth`: "2025-10-31"
- `noticePeriod`: 14
- Notification send date: 2025-10-17 (9:00 AM)

## Installation and Setup

### 1. Install Packages
```bash
cd /var/www/sindipro
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Install and Run Redis
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Check status
sudo systemctl status redis-server
```

### 3. Database Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Environment Variables Setup
Add the following settings to your `.env` file:

```env
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email Configuration (Gmail SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Sindipro <your-email@gmail.com>
```

**How to get Gmail App Password:**
1. Enable 2-factor authentication on your Gmail account
2. Go to: https://myaccount.google.com/apppasswords
3. Create app password and use it in `EMAIL_HOST_PASSWORD`

### 5. Run Celery Worker and Beat

#### Development Environment:
Open 3 terminals and run:

```bash
# Terminal 1 - Celery Worker
cd /var/www/sindipro
source venv/bin/activate
celery -A sindipro_backend worker --loglevel=info

# Terminal 2 - Celery Beat (Scheduler)
cd /var/www/sindipro
source venv/bin/activate
celery -A sindipro_backend beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Terminal 3 - Django Server
cd /var/www/sindipro
source venv/bin/activate
python manage.py runserver
```

#### Production Environment (Systemd Service):

**Celery Worker Service** (`/etc/systemd/system/celery-sindipro.service`):
```ini
[Unit]
Description=Celery Worker for Sindipro
After=network.target redis-server.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/var/www/sindipro
ExecStart=/usr/local/bin/celery -A sindipro_backend worker --loglevel=info --logfile=/var/log/celery/worker.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Celery Beat Service** (`/etc/systemd/system/celerybeat-sindipro.service`):
```ini
[Unit]
Description=Celery Beat Scheduler for Sindipro
After=network.target redis-server.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/var/www/sindipro
ExecStart=/usr/local/bin/celery -A sindipro_backend beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler --logfile=/var/log/celery/beat.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start services:
```bash
sudo systemctl daemon-reload
sudo systemctl start celery-sindipro
sudo systemctl start celerybeat-sindipro
sudo systemctl enable celery-sindipro
sudo systemctl enable celerybeat-sindipro

# Check status
sudo systemctl status celery-sindipro
sudo systemctl status celerybeat-sindipro
```

## API Usage Example

### POST /api/legal/template/
```json
{
  "name": "Fire Safety Inspection",
  "description": "Annual fire safety inspection requirement",
  "dueMonth": "2025-10-31",
  "noticePeriod": 14,
  "responsibleEmails": "admin@sindipro.com.br, safety@sindipro.com.br",
  "frequency": "annual",
  "requiresQuote": false
}
```

### Response:
```json
{
  "message": "Legal template created successfully",
  "template_id": 1,
  "template_name": "Fire Safety Inspection"
}
```

Email will be automatically sent on 2025-10-17 at 9:00 AM.

## Email Content

**Subject:** Legal Obligation Expiration Notice

**Body:**
```
The legal obligation expiration date is approaching. You need to prepare.

Template: Fire Safety Inspection
```

## Troubleshooting

### If emails are not sending:
1. Verify Celery Worker and Beat are running
2. Check Redis is running: `redis-cli ping` (should return PONG)
3. Verify Gmail credentials in `.env` file
4. Check Gmail app password is valid
5. Check Periodic Tasks in Django Admin: `/admin/django_celery_beat/periodictask/`

### Check Logs:
```bash
# Celery Worker logs
tail -f /var/log/celery/worker.log

# Celery Beat logs
tail -f /var/log/celery/beat.log
```

### Test Email Sending:
```python
# In Django shell
python manage.py shell

from legal_docs.tasks import send_legal_obligation_notification
send_legal_obligation_notification.delay(1, ["test@example.com"], "Test Template")
```

## Important Notes

1. **Timezone:** Currently set to UTC. Modify `TIME_ZONE` in `settings.py` if needed
2. **Email Limits:** Gmail has daily sending limits (500 emails/day for free accounts)
3. **Redis Security:** Recommended to set Redis password in production environment
4. **Backup:** Periodic Tasks are stored in DB, ensure regular backups
5. **API Key Security:** Never commit `.env` file to Git (check `.gitignore`)

## Implemented Files

1. `/var/www/sindipro/requirements.txt` - Package dependencies
2. `/var/www/sindipro/sindipro_backend/celery.py` - Celery configuration
3. `/var/www/sindipro/sindipro_backend/__init__.py` - Celery app initialization
4. `/var/www/sindipro/sindipro_backend/settings.py` - Django settings
5. `/var/www/sindipro/legal_docs/tasks.py` - Email sending task
6. `/var/www/sindipro/legal_docs/views.py` - Notification scheduling logic
