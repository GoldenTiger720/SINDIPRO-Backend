from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import ContactsEvent, ContactsSupplier
from .serializers import ContactsEventSerializer, ContactsSupplierSerializer

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def event_handler(request):
    if request.method == 'GET':
        events = ContactsEvent.objects.all()
        serializer = ContactsEventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = ContactsEventSerializer(data=request.data)
        
        if serializer.is_valid():
            event = serializer.save(created_by=request.user)
            return Response({
                'message': 'Event created successfully',
                'event': ContactsEventSerializer(event).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def event_detail_handler(request, id):
    event = get_object_or_404(ContactsEvent, id=id)
    
    if request.method == 'PUT':
        serializer = ContactsEventSerializer(event, data=request.data, partial=True)
        
        if serializer.is_valid():
            updated_event = serializer.save()
            return Response({
                'message': 'Event updated successfully',
                'event': ContactsEventSerializer(updated_event).data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        event.delete()
        return Response({
            'message': 'Event deleted successfully'
        }, status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def supplier_handler(request):
    if request.method == 'GET':
        suppliers = ContactsSupplier.objects.all()
        serializer = ContactsSupplierSerializer(suppliers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = ContactsSupplierSerializer(data=request.data)
        
        if serializer.is_valid():
            supplier = serializer.save(created_by=request.user)
            return Response({
                'message': 'Supplier created successfully',
                'supplier': ContactsSupplierSerializer(supplier).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
