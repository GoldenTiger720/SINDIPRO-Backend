from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from email.mime.image import MIMEImage
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)


@shared_task
def send_legal_obligation_notification(template_id, email_addresses, template_name, building_name, due_date):
    """
    Send email notification about approaching legal obligation due date.

    Args:
        template_id: ID of the LegalTemplate
        email_addresses: List of email addresses to send notification to
        template_name: Name of the legal template
        building_name: Name of the building
        due_date: Due date in ISO format (YYYY-MM-DD)
    """
    try:
        # Parse due date and calculate days remaining
        due_date_obj = datetime.fromisoformat(due_date).date()
        today = timezone.now().date()
        days_remaining = (due_date_obj - today).days

        # Format date for display
        due_date_formatted = due_date_obj.strftime('%d/%m/%Y')
        current_year = timezone.now().year

        # Prepare context for template
        context = {
            'building_name': building_name,
            'template_name': template_name,
            'due_date': due_date_formatted,
            'days_remaining': days_remaining,
            'current_year': current_year,
            'use_logo_image': False,  # Set to True when logo is added
        }

        # Check if logo exists
        logo_path = os.path.join(settings.BASE_DIR, 'legal_docs/static/legal_docs/images/sindipro-logo.png')
        if os.path.exists(logo_path):
            context['use_logo_image'] = True

        # Render HTML template
        html_content = render_to_string('legal_docs/email/obligation_notification.html', context)

        # Plain text fallback
        text_content = f"""
SINDIPRO - Notificação de Obrigação Legal

Atenção: Uma obrigação legal está se aproximando do vencimento.

Edifício: {building_name}
Obrigação: {template_name}
Data de Vencimento: {due_date_formatted}
Dias Restantes: {days_remaining} dias

Por favor, tome as providências necessárias para cumprir esta obrigação legal dentro do prazo.

---
SINDIPRO - Sistema de Gestão Predial
Este é um e-mail automático. Por favor, não responda.
        """

        subject = f'⚠️ Obrigação Legal: {template_name} - {building_name}'
        from_email = settings.DEFAULT_FROM_EMAIL

        # Create email with both HTML and plain text
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=email_addresses,
        )
        email.attach_alternative(html_content, "text/html")

        # Attach logo if it exists
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as logo_file:
                logo_image = MIMEImage(logo_file.read())
                logo_image.add_header('Content-ID', '<sindipro_logo>')
                logo_image.add_header('Content-Disposition', 'inline', filename='sindipro-logo.png')
                email.attach(logo_image)

        email.send(fail_silently=False)

        logger.info(f'Legal obligation notification sent for template {template_id} to {email_addresses}')
        return f'Email sent successfully to {len(email_addresses)} recipients'

    except Exception as e:
        logger.error(f'Failed to send legal obligation notification for template {template_id}: {str(e)}')
        raise
