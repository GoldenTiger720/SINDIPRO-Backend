from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Equipment, MaintenanceRecord, EquipmentDocument
from .serializers import EquipmentSerializer, MaintenanceRecordSerializer, EquipmentDocumentSerializer, EquipmentWithMaintenanceSerializer
from auth_system.models import User


def get_equipment_queryset(user):
    """
    Returns the equipment queryset based on user role.
    Master users can see all equipment from manager and operator users.
    Other users only see their own equipment.
    """
    if user.role == 'master':
        # Master users can see all equipment from manager and operator users
        return Equipment.objects.filter(
            created_by__role__in=['master', 'manager', 'operator']
        ).prefetch_related('maintenance_records')
    else:
        # Other users only see their own equipment
        return Equipment.objects.filter(created_by=user).prefetch_related('maintenance_records')


def get_equipment_for_user(user, equipment_id):
    """
    Returns a specific equipment if the user has access to it.
    Master users can access equipment from manager and operator users.
    Other users can only access their own equipment.
    """
    if user.role == 'master':
        return get_object_or_404(
            Equipment,
            id=equipment_id,
            created_by__role__in=['master', 'manager', 'operator']
        )
    else:
        return get_object_or_404(Equipment, id=equipment_id, created_by=user)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def equipment_list_create(request):
    if request.method == 'GET':
        # Get equipment based on user role
        equipment = get_equipment_queryset(request.user)
        serializer = EquipmentWithMaintenanceSerializer(equipment, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = EquipmentSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            equipment = serializer.save()
            return Response({
                'message': 'Equipment created successfully',
                'equipment_id': equipment.id,
                'equipment_name': equipment.name
            }, status=status.HTTP_201_CREATED)

        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def maintenance_record_list_create(request, equipment_id):
    equipment = get_equipment_for_user(request.user, equipment_id)

    if request.method == 'GET':
        maintenance_records = MaintenanceRecord.objects.filter(equipment=equipment)
        serializer = MaintenanceRecordSerializer(maintenance_records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = MaintenanceRecordSerializer(data=request.data)

        if serializer.is_valid():
            maintenance_record = serializer.save(equipment=equipment)
            return Response({
                'message': 'Maintenance record created successfully',
                'maintenance_record_id': maintenance_record.id
            }, status=status.HTTP_201_CREATED)

        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        # Get the maintenance record id from request data
        maintenance_id = request.data.get('id')

        if not maintenance_id:
            return Response({
                'error': 'Maintenance record id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Find the specific maintenance record
        maintenance_record = get_object_or_404(
            MaintenanceRecord,
            id=maintenance_id,
            equipment=equipment
        )

        # Update the maintenance record
        serializer = MaintenanceRecordSerializer(
            maintenance_record,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Maintenance record updated successfully',
                'maintenance_record_id': maintenance_record.id
            }, status=status.HTTP_200_OK)

        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        # Delete all maintenance records for this equipment
        maintenance_records = MaintenanceRecord.objects.filter(equipment=equipment)

        if not maintenance_records.exists():
            return Response({
                'error': 'No maintenance records found for this equipment'
            }, status=status.HTTP_404_NOT_FOUND)

        deleted_count = maintenance_records.count()
        maintenance_records.delete()

        return Response({
            'message': f'Deleted {deleted_count} maintenance record(s) successfully',
            'deleted_count': deleted_count
        }, status=status.HTTP_200_OK)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def maintenance_record_detail(request, equipment_id, maintenance_id):
    equipment = get_equipment_for_user(request.user, equipment_id)
    maintenance_record = get_object_or_404(MaintenanceRecord, id=maintenance_id, equipment=equipment)

    if request.method == 'PUT':
        serializer = MaintenanceRecordSerializer(maintenance_record, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Maintenance record updated successfully',
                'maintenance_record_id': maintenance_record.id
            }, status=status.HTTP_200_OK)

        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        maintenance_record.delete()
        return Response({
            'message': 'Maintenance record deleted successfully'
        }, status=status.HTTP_200_OK)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def equipment_detail(request, equipment_id):
    equipment = get_equipment_for_user(request.user, equipment_id)

    if request.method == 'PUT':
        serializer = EquipmentSerializer(equipment, data=request.data, partial=True, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Equipment updated successfully',
                'equipment_id': equipment.id,
                'equipment_name': equipment.name
            }, status=status.HTTP_200_OK)

        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        equipment_name = equipment.name
        equipment.delete()
        return Response({
            'message': f'Equipment "{equipment_name}" deleted successfully'
        }, status=status.HTTP_200_OK)