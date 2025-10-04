from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import FieldRequest, FieldMgmtTechnical
from .serializers import FieldRequestSerializer, FieldMgmtTechnicalSerializer


@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def field_requests(request):
    """
    GET: Retrieve all field requests.
    POST: Create a new field request.
    Expected POST data: {building_id, caretaker, title, items}
    """
    if request.method == 'GET':
        requests = FieldRequest.objects.all().order_by('-created_at')
        serializer = FieldRequestSerializer(requests, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        print(f"Request data: {request.data}")  # Debug logging
        print(f"Request content type: {request.content_type}")  # Debug logging
        
        serializer = FieldRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        print(f"Serializer errors: {serializer.errors}")  # Debug logging
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def technical_requests(request):
    """
    GET: Retrieve all technical field requests.
    POST: Create a new technical field request.
    Expected POST data: {company_email, title, description, location, priority, photos}
    """
    if request.method == 'GET':
        requests = FieldMgmtTechnical.objects.all().order_by('-created_at')
        serializer = FieldMgmtTechnicalSerializer(requests, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        print(f"Technical request data: {request.data}")  # Debug logging
        
        serializer = FieldMgmtTechnicalSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        print(f"Technical serializer errors: {serializer.errors}")  # Debug logging
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)