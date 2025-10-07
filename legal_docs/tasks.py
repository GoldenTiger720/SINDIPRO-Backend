from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_legal_obligation_notification(template_id, email_addresses, template_name):
    """
    Send email notification about approaching legal obligation due date.

    Args:
        template_id: ID of the LegalTemplate
        email_addresses: List of email addresses to send notification to
        template_name: Name of the legal template
    """
    try:
        subject = 'Legal Obligation Expiration Notice'
        message = f'The legal obligation expiration date is approaching. You need to prepare.\n\nTemplate: {template_name}'
        from_email = settings.DEFAULT_FROM_EMAIL

        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=email_addresses,
            fail_silently=False,
        )

        logger.info(f'Legal obligation notification sent for template {template_id} to {email_addresses}')
        return f'Email sent successfully to {len(email_addresses)} recipients'

    except Exception as e:
        logger.error(f'Failed to send legal obligation notification for template {template_id}: {str(e)}')
        raise
