from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import LegalDocument, LegalObligation, LegalTemplate, LegalObligationCompletion, ObligationLibrary
from .serializers import (
    LegalDocumentSerializer,
    LegalObligationSerializer,
    LegalTemplateSerializer,
    LegalObligationCompletionSerializer,
    MarkCompletionSerializer,
    ObligationLibrarySerializer,
    ActivateLibraryObligationSerializer
)
from .tasks import send_legal_obligation_notification
from building_mgmt.models import Building
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

        # Get building name
        building_name = template.building.building_name if template.building else "Edifício não especificado"

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

        # Create new periodic task with building name and due date
        PeriodicTask.objects.create(
            crontab=schedule,
            name=task_name,
            task='legal_docs.tasks.send_legal_obligation_notification',
            args=json.dumps([
                template.id,
                email_list,
                template.name,
                building_name,
                template.due_month.isoformat()
            ]),
            one_off=True,  # Execute only once
            start_time=notification_date,
        )

    except Exception as e:
        # Log the error but don't fail the template creation
        print(f"Error scheduling notification email: {str(e)}")


def add_to_library(template):
    """
    Helper function to add a legal template to the global library.
    If an obligation with the same name already exists, it won't be duplicated.
    """
    library_entry, created = ObligationLibrary.objects.get_or_create(
        name=template.name,
        defaults={
            'description': template.description,
            'building_type': template.building_type,
            'frequency': template.frequency,
            'conditions': template.conditions,
            'requires_quote': template.requires_quote,
            'notice_period': template.notice_period,
            'created_by': template.created_by
        }
    )
    return library_entry, created


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

            # Automatically add to the global library
            add_to_library(template)

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_obligation_completed(request, template_id):
    """
    Mark a legal obligation as completed and calculate the next due date.
    """
    try:
        template = get_object_or_404(LegalTemplate, id=template_id, created_by=request.user)
    except LegalTemplate.DoesNotExist:
        return Response({
            'error': 'Template not found or you do not have permission to access it'
        }, status=status.HTTP_404_NOT_FOUND)

    serializer = MarkCompletionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data
    completion_date = validated_data['completion_date']
    notes = validated_data.get('notes', '')
    actual_cost = validated_data.get('actual_cost')

    # Store previous due date
    previous_due_date = template.due_month

    # Calculate next due date based on completion date and frequency
    next_due_date = template.calculate_next_due_date(completion_date)

    # Create completion record
    completion = LegalObligationCompletion.objects.create(
        template=template,
        completion_date=completion_date,
        previous_due_date=previous_due_date,
        new_due_date=next_due_date,
        notes=notes,
        actual_cost=actual_cost,
        completed_by=request.user
    )

    # Update template with new due date and completion info
    template.last_completion_date = completion_date
    template.status = 'pending'  # Reset to pending for next cycle
    if next_due_date:
        template.due_month = next_due_date
    template.save()

    # Reschedule notification if there's a next due date
    if next_due_date and template.notice_period and template.responsible_emails:
        schedule_notification_email(template)

    completion_serializer = LegalObligationCompletionSerializer(completion)

    return Response({
        'message': 'Obligation marked as completed successfully',
        'completion': completion_serializer.data,
        'new_due_date': next_due_date.isoformat() if next_due_date else None
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_completion_history(request, template_id):
    """
    Get completion history for a specific legal obligation template.
    """
    try:
        template = get_object_or_404(LegalTemplate, id=template_id, created_by=request.user)
    except LegalTemplate.DoesNotExist:
        return Response({
            'error': 'Template not found or you do not have permission to access it'
        }, status=status.HTTP_404_NOT_FOUND)

    completions = LegalObligationCompletion.objects.filter(template=template)
    serializer = LegalObligationCompletionSerializer(completions, many=True)

    return Response({
        'template_id': template_id,
        'template_name': template.name,
        'completions': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_completions(request):
    """
    Get all completion history for all templates of the authenticated user.
    """
    templates = LegalTemplate.objects.filter(created_by=request.user)
    completions = LegalObligationCompletion.objects.filter(
        template__in=templates
    ).select_related('template', 'completed_by')

    serializer = LegalObligationCompletionSerializer(completions, many=True)

    return Response({
        'completions': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_obligation_library(request):
    """
    Get all obligations in the global library.
    This provides a complete repository of all unique legal obligations.
    Automatically syncs all existing LegalTemplates to the library.
    """
    # Sync all existing templates to the library (ensures library is always up-to-date)
    sync_templates_to_library()

    library_entries = ObligationLibrary.objects.all()
    serializer = ObligationLibrarySerializer(library_entries, many=True)

    return Response({
        'library': serializer.data
    }, status=status.HTTP_200_OK)


def sync_templates_to_library():
    """
    Sync all existing LegalTemplates to the ObligationLibrary.
    This ensures the library contains all unique obligations from all condominiums.
    Uses get_or_create to avoid duplicates (based on name).
    """
    # Get all active templates from all users/buildings
    all_templates = LegalTemplate.objects.filter(active=True)

    synced_count = 0
    for template in all_templates:
        library_entry, created = ObligationLibrary.objects.get_or_create(
            name=template.name,
            defaults={
                'description': template.description,
                'building_type': template.building_type,
                'frequency': template.frequency,
                'conditions': template.conditions or '',
                'requires_quote': template.requires_quote,
                'notice_period': template.notice_period,
                'created_by': template.created_by
            }
        )
        if created:
            synced_count += 1

    return synced_count


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def activate_library_obligation(request):
    """
    Activate a library obligation for a specific building.
    This creates a new LegalTemplate for the building based on the library entry.
    """
    serializer = ActivateLibraryObligationSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data
    library_obligation_id = validated_data['library_obligation_id']
    building_id = validated_data['building_id']
    due_date = validated_data['due_date']
    responsible_emails = validated_data.get('responsible_emails', '')

    # Get the library obligation
    try:
        library_entry = ObligationLibrary.objects.get(id=library_obligation_id)
    except ObligationLibrary.DoesNotExist:
        return Response({
            'error': 'Library obligation not found'
        }, status=status.HTTP_404_NOT_FOUND)

    # Get the building
    try:
        building = Building.objects.get(id=building_id)
    except Building.DoesNotExist:
        return Response({
            'error': 'Building not found'
        }, status=status.HTTP_404_NOT_FOUND)

    # Check if obligation already exists for this building
    existing = LegalTemplate.objects.filter(
        building=building,
        name=library_entry.name,
        created_by=request.user
    ).first()

    if existing:
        return Response({
            'error': 'This obligation already exists for this building',
            'existing_template_id': existing.id
        }, status=status.HTTP_400_BAD_REQUEST)

    # Create new template for the building based on library entry
    new_template = LegalTemplate.objects.create(
        name=library_entry.name,
        description=library_entry.description,
        building=building,
        building_type=library_entry.building_type,
        frequency=library_entry.frequency,
        conditions=library_entry.conditions,
        requires_quote=library_entry.requires_quote,
        notice_period=library_entry.notice_period,
        due_month=due_date,
        responsible_emails=responsible_emails,
        active=True,
        status='pending',
        created_by=request.user
    )

    # Update usage count in the library
    library_entry.usage_count += 1
    library_entry.save()

    # Schedule notification if required fields are present
    if new_template.due_month and new_template.notice_period and new_template.responsible_emails:
        schedule_notification_email(new_template)

    template_serializer = LegalTemplateSerializer(new_template)

    return Response({
        'message': 'Obligation activated for building successfully',
        'template': template_serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_obligation_to_library(request):
    """
    Manually add a new obligation to the library.
    """
    serializer = ObligationLibrarySerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        library_entry = serializer.save()
        return Response({
            'message': 'Obligation added to library successfully',
            'library_entry': ObligationLibrarySerializer(library_entry).data
        }, status=status.HTTP_201_CREATED)

    return Response({
        'error': 'Invalid data',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)