from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import LegalDocument, LegalObligation, LegalTemplate
from .serializers import LegalDocumentSerializer, LegalObligationSerializer, LegalTemplateSerializer
from .tasks import send_legal_obligation_notification
from datetime import datetime, timedelta
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json


def schedule_notification_email(template):
    """
    Schedule email notification based on template's due_month and notice_period.

    Args:
        template: LegalTemplate instance
    """
    try:
        # Calculate notification date: due_month - notice_period days
        notification_date = template.due_month - timedelta(days=template.notice_period)

        # Parse email addresses from comma-separated string
        email_list = [email.strip() for email in template.responsible_emails.split(',') if email.strip()]

        if not email_list:
            return

        # Create crontab schedule for the notification date
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=9,  # Send at 9 AM
            day_of_month=notification_date.day,
            month_of_year=notification_date.month,
        )

        # Create or update periodic task
        task_name = f'legal_notification_{template.id}'

        # Delete existing task if it exists
        PeriodicTask.objects.filter(name=task_name).delete()

        # Create new periodic task
        PeriodicTask.objects.create(
            crontab=schedule,
            name=task_name,
            task='legal_docs.tasks.send_legal_obligation_notification',
            args=json.dumps([template.id, email_list, template.name]),
            one_off=True,  # Execute only once
            start_time=notification_date,
        )

    except Exception as e:
        # Log the error but don't fail the template creation
        print(f"Error scheduling notification email: {str(e)}")


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def legal_template_handler(request):
    if request.method == 'GET':
        templates = LegalTemplate.objects.filter(created_by=request.user, active=True)
        serializer = LegalTemplateSerializer(templates, many=True)
        
        return Response({
            'templates': serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = LegalTemplateSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            template = serializer.save()

            # Schedule email notification if required fields are present
            if template.due_month and template.notice_period and template.responsible_emails:
                schedule_notification_email(template)

            return Response({
                'message': 'Legal template created successfully',
                'template_id': template.id,
                'template_name': template.name
            }, status=status.HTTP_201_CREATED)

        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def update_delete_legal_template(request, template_id):
    try:
        template = get_object_or_404(LegalTemplate, id=template_id, created_by=request.user)
    except LegalTemplate.DoesNotExist:
        return Response({
            'error': 'Template not found or you do not have permission to access it'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'PUT':
        serializer = LegalTemplateSerializer(template, data=request.data, context={'request': request}, partial=True)

        if serializer.is_valid():
            updated_template = serializer.save()

            # Reschedule email notification if required fields are present
            if updated_template.due_month and updated_template.notice_period and updated_template.responsible_emails:
                schedule_notification_email(updated_template)

            return Response({
                'message': 'Legal template updated successfully',
                'template_id': updated_template.id,
                'template_name': updated_template.name
            }, status=status.HTTP_200_OK)

        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        template_name = template.name
        template_id = template.id

        # Delete associated scheduled task if it exists
        task_name = f'legal_notification_{template_id}'
        PeriodicTask.objects.filter(name=task_name).delete()

        template.delete()

        return Response({
            'message': 'Legal template deleted successfully',
            'template_name': template_name
        }, status=status.HTTP_200_OK)