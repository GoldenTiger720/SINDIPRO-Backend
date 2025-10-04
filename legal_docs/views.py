from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import LegalDocument, LegalObligation, LegalTemplate
from .serializers import LegalDocumentSerializer, LegalObligationSerializer, LegalTemplateSerializer


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
        template.delete()
        
        return Response({
            'message': 'Legal template deleted successfully',
            'template_name': template_name
        }, status=status.HTTP_200_OK)