from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ConsumptionRegister, ConsumptionAccount
from .serializers import ConsumptionRegisterSerializer, ConsumptionAccountSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def consumption_register(request):
    """
    GET: Retrieve all consumption register entries.
    POST: Create a new consumption register entry.
    Expected POST data: {date, gasCategory, utilityType, value}
    """
    if request.method == 'GET':
        registers = ConsumptionRegister.objects.all()
        serializer = ConsumptionRegisterSerializer(registers, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = ConsumptionRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def consumption_account(request):
    """
    GET: Retrieve all consumption account entries.
    POST: Create a new consumption account entry.
    Expected POST data: {amount, month, paymentDate, utilityType}
    """
    if request.method == 'GET':
        accounts = ConsumptionAccount.objects.all()
        serializer = ConsumptionAccountSerializer(accounts, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = ConsumptionAccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)