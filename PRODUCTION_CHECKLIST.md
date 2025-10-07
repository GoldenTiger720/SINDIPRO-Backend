# Production Deployment Checklist

## ✅ System Status

### Services Running
- [x] Redis Server: `sudo systemctl status redis-server`
- [x] Celery Worker: `sudo systemctl status celery-sindipro`
- [x] Celery Beat: `sudo systemctl status celerybeat-sindipro`
- [x] Django Backend: https://backend.sindipro.com.br

### Configuration Files
- [x] `/var/www/sindipro/.env` - Email and Celery settings
- [x] `/var/www/sindipro/sindipro_backend/settings.py` - Django settings
- [x] `/var/www/sindipro/legal_docs/tasks.py` - Email task
- [x] `/var/www/sindipro/legal_docs/views.py` - Scheduling logic

### Systemd Services
- [x] `/etc/systemd/system/celery-sindipro.service`
- [x] `/etc/systemd/system/celerybeat-sindipro.service`

## 🚀 Production Workflow

### 1. How It Works

```
API Request (POST /api/legal/template/)
           ↓
Django saves to legal_docs_legaltemplate table
           ↓
Django schedules Celery task automatically
           ↓
Celery Beat monitors schedule
           ↓
Celery Worker sends email via Gmail SMTP
           ↓
Recipients receive notification
```

### 2. API Endpoint

**URL:** `https://backend.sindipro.com.br/api/legal/template/`

**Method:** POST

**Headers:**
```
Authorization: Bearer <jwt-token>
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

### 3. Email Schedule

- **Notification Date:** `dueMonth - noticePeriod` days
- **Send Time:** 9:00 AM UTC
- **Example:** If `dueMonth = 2025-12-31` and `noticePeriod = 14`:
  - Email sends on **2025-12-17 at 9:00 AM**

## 📊 Monitoring

### Check Services

```bash
# All services status
sudo systemctl status redis-server celery-sindipro celerybeat-sindipro

# Celery Worker logs
sudo tail -f /var/log/celery/worker.log

# Celery Beat logs
sudo tail -f /var/log/celery/beat.log
```

### Restart Services

```bash
# Restart Celery services
sudo systemctl restart celery-sindipro celerybeat-sindipro

# Restart all
sudo systemctl restart redis-server celery-sindipro celerybeat-sindipro
```

### View Scheduled Tasks

Django Admin: `https://backend.sindipro.com.br/admin/django_celery_beat/periodictask/`

## 🧪 Testing

### 1. Test Email (Manual)

```bash
cd /var/www/sindipro
python test_email.py recipient@example.com
```

### 2. Test via API

```bash
curl -X POST https://backend.sindipro.com.br/api/legal/template/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Template",
    "description": "Test notification",
    "dueMonth": "2025-10-15",
    "noticePeriod": 3,
    "responsibleEmails": "test@example.com",
    "frequency": "annual",
    "requiresQuote": false
  }'
```

Expected: Email scheduled for **2025-10-12 at 9:00 AM**

### 3. Verify Database

```bash
# Check if template was saved
python manage.py dbshell
SELECT id, name, due_month, notice_period, responsible_emails FROM legal_docs_legaltemplate;
```

### 4. Verify Scheduled Task

```bash
# Check scheduled tasks
python manage.py shell
>>> from django_celery_beat.models import PeriodicTask
>>> PeriodicTask.objects.all()
```

## 🔒 Security Checklist

- [x] Gmail app password in `.env` (not committed to git)
- [x] `.env` file permissions: `chmod 600 /var/www/sindipro/.env`
- [x] Redis running locally (no external access)
- [x] Celery services running as root (temporary - consider www-data later)
- [x] Log files in `/var/log/celery/`

## 🐛 Troubleshooting

### Email not sending?

1. **Check Celery Worker is running:**
   ```bash
   sudo systemctl status celery-sindipro
   ```

2. **Check Gmail credentials:**
   ```bash
   grep EMAIL /var/www/sindipro/.env
   ```

3. **Check worker logs:**
   ```bash
   sudo tail -100 /var/log/celery/worker.log
   ```

4. **Test email manually:**
   ```bash
   python test_email.py test@example.com
   ```

### Task not scheduled?

1. **Verify required fields:**
   - `dueMonth` (required)
   - `noticePeriod` (required)
   - `responsibleEmails` (required, comma-separated)

2. **Check Beat scheduler logs:**
   ```bash
   sudo tail -100 /var/log/celery/beat.log
   ```

3. **Check scheduled tasks in admin:**
   https://backend.sindipro.com.br/admin/django_celery_beat/periodictask/

### Redis connection error?

```bash
# Check Redis status
sudo systemctl status redis-server

# Test Redis
redis-cli ping  # Should return PONG

# Restart if needed
sudo systemctl restart redis-server
```

## 📝 Important Notes

1. **Database:** All Legal Templates are stored in `legal_docs_legaltemplate` table
2. **Domain:** Production backend is at `backend.sindipro.com.br`
3. **Timezone:** All times are UTC (9:00 AM UTC)
4. **Email Service:** Gmail SMTP (requires app password)
5. **Auto-restart:** All services configured to restart on failure

## 🎯 Production Ready

- ✅ Email notification system fully operational
- ✅ Celery Worker and Beat running as systemd services
- ✅ Redis configured and running
- ✅ Database migrations applied
- ✅ API endpoint ready: `POST /api/legal/template/`
- ✅ Automatic email scheduling on template creation
- ✅ Monitoring and logging in place

---

**Last Updated:** 2025-10-07
**Status:** PRODUCTION READY ✅
