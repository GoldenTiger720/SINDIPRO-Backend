#!/bin/bash

echo "=========================================="
echo "Legal Notification System Test"
echo "=========================================="
echo ""

# Test 1: Check Redis
echo "1. Testing Redis connection..."
redis-cli ping
if [ $? -eq 0 ]; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not running. Start with: sudo systemctl start redis-server"
    exit 1
fi
echo ""

# Test 2: Check if Django is running
echo "2. Checking Django server..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/ > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Django server is accessible"
else
    echo "⚠️  Django server may not be running. Start with: python manage.py runserver"
fi
echo ""

# Test 3: Create Legal Template (example)
echo "3. Example API request to create Legal Template:"
echo ""
echo "POST /api/legal/template/"
echo "Authorization: Bearer <your-token>"
echo ""
echo "Request Body:"
cat <<'EOF'
{
  "name": "Fire Safety Inspection",
  "description": "Annual fire safety inspection requirement",
  "dueMonth": "2025-11-15",
  "noticePeriod": 7,
  "responsibleEmails": "admin@example.com, safety@example.com",
  "frequency": "annual",
  "requiresQuote": false
}
EOF
echo ""
echo ""

echo "4. Email notification will be scheduled for:"
echo "   Date: dueMonth - noticePeriod days"
echo "   Time: 9:00 AM"
echo ""

echo "5. To start Celery services (required for email sending):"
echo ""
echo "Terminal 1 - Celery Worker:"
echo "  celery -A sindipro_backend worker --loglevel=info"
echo ""
echo "Terminal 2 - Celery Beat:"
echo "  celery -A sindipro_backend beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler"
echo ""

echo "=========================================="
echo "Test Complete!"
echo "=========================================="
