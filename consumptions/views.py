from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ConsumptionRegister, ConsumptionAccount, SubAccount
from .serializers import ConsumptionRegisterSerializer, ConsumptionAccountSerializer, SubAccountSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def consumption_register(request):
    """
    GET: Retrieve all consumption register entries with sub_account details.
    POST: Create a new consumption register entry.
    Expected POST data: {date, utilityType, value, subAccount (optional)}
    """
    if request.method == 'GET':
        registers = ConsumptionRegister.objects.select_related('sub_account').all()
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


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def sub_account_list(request):
    """
    GET: Retrieve all sub-accounts (can filter by utility_type query param).
    POST: Create a new sub-account.
    Expected POST data: {utilityType, name, icon (optional)}
    """
    if request.method == 'GET':
        sub_accounts = SubAccount.objects.all()

        # Filter by utility_type if provided
        utility_type = request.GET.get('utility_type')
        if utility_type:
            sub_accounts = sub_accounts.filter(utility_type=utility_type)

        serializer = SubAccountSerializer(sub_accounts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = SubAccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def sub_account_detail(request, sub_account_id):
    """
    GET: Retrieve a specific sub-account.
    PUT: Update a specific sub-account.
    DELETE: Delete a specific sub-account.
    """
    try:
        sub_account = SubAccount.objects.get(id=sub_account_id)
    except SubAccount.DoesNotExist:
        return Response({
            'error': 'Sub-account not found'
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = SubAccountSerializer(sub_account)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = SubAccountSerializer(sub_account, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        sub_account.delete()
        return Response({
            'message': 'Sub-account deleted successfully'
        }, status=status.HTTP_200_OK)