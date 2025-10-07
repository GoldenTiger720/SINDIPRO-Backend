#!/usr/bin/env python
"""
Email Test Script (Gmail SMTP)
Usage: python test_email.py recipient@email.com
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sindipro_backend.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email(recipient):
    try:
        send_mail(
            subject='Sindipro Email Test - Success!',
            message='Your Sindipro email configuration is working perfectly.\n\nThis is a test email from the legal notification system.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        print(f"✅ Email sent successfully to {recipient}")
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_email.py recipient@email.com")
        sys.exit(1)

    recipient = sys.argv[1]
    test_email(recipient)
