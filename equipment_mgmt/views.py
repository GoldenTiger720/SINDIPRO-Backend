from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Equipment, MaintenanceRecord, EquipmentDocument
from .serializers import EquipmentSerializer, MaintenanceRecordSerializer, EquipmentDocumentSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def equipment_list_create(request):
    if request.method == 'GET':
        equipment = Equipment.objects.filter(created_by=request.user)
        serializer = EquipmentSerializer(equipment, many=True)
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_maintenance_record(request, equipment_id):
    equipment = get_object_or_404(Equipment, id=equipment_id, created_by=request.user)
    
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