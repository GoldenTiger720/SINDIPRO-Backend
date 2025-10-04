from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import FinancialMainAccount, AnnualBudget, Expense, Collection
from .serializers import (FinancialMainAccountSerializer, FinancialMainAccountReadSerializer, 
                          AnnualBudgetSerializer, ExpenseSerializer, ExpenseReadSerializer, 
                          AnnualBudgetReadSerializer, CollectionSerializer, CollectionReadSerializer)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def financial_account_view(request):
    """
    GET: Retrieve financial main accounts with building information
         Optional query parameter: building_id to filter by building
    POST: Create a new financial main account
    """
    if request.method == 'GET':
        accounts = FinancialMainAccount.objects.select_related('building').all()
        
        # Filter by building_id if provided
        building_id = request.GET.get('building_id')
        if building_id:
            accounts = accounts.filter(building_id=building_id)
        
        serializer = FinancialMainAccountReadSerializer(accounts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = FinancialMainAccountSerializer(data=request.data)
        
        if serializer.is_valid():
            account = serializer.save()
            return Response({
                'message': 'Financial account created successfully',
                'account_id': account.id,
                'code': account.code,
                'name': account.name
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def annual_budget_view(request):
    """
    GET: Retrieve annual budget entries with building and category information
         Optional query parameter: building_id to filter by building
    POST: Create a new annual budget entry
    Expected data structure:
    {
        "account_category": "maintenance",
        "budgeted_amount": 5,
        "building_id": 1, 
        "sub_item": "aaa"
    }
    """
    if request.method == 'GET':
        budgets = AnnualBudget.objects.select_related('building', 'category').all()
        
        # Filter by building_id if provided
        building_id = request.GET.get('building_id')
        if building_id:
            budgets = budgets.filter(building_id=building_id)
        
        serializer = AnnualBudgetReadSerializer(budgets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = AnnualBudgetSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            annual_budget = serializer.save()
            return Response({
                'message': 'Annual budget created successfully',
                'budget_id': annual_budget.id,
                'category': annual_budget.category.name,
                'sub_item': annual_budget.sub_item,
                'budgeted_amount': str(annual_budget.budgeted_amount),
                'year': annual_budget.year
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def expense_view(request):
    """
    GET: Retrieve expense entries with building and category information
         Optional query parameter: building_id to filter by building
    POST: Create a new expense entry
    Expected data structure:
    {
        "amount": 7,
        "buildingId": "1", 
        "category": "maintenance",
        "month": "2025-10"
    }
    """
    if request.method == 'GET':
        expenses = Expense.objects.select_related('building', 'category').all()
        
        # Filter by building_id if provided
        building_id = request.GET.get('building_id')
        if building_id:
            expenses = expenses.filter(building_id=building_id)
        
        serializer = ExpenseReadSerializer(expenses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = ExpenseSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            expense = serializer.save()
            return Response({
                'message': 'Expense created successfully',
                'expense_id': expense.id,
                'category': expense.category.name,
                'amount': str(expense.amount),
                'expense_date': expense.expense_date.strftime('%Y-%m-%d'),
                'building_id': expense.building_id
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def collection_view(request):
    """
    GET: Retrieve collection entries with building information
         Optional query parameter: building_id to filter by building
    POST: Create a new collection entry
    Expected data structure:
    {
        "active": true,
        "buildingId": 1,
        "monthlyAmount": 3,
        "name": "Test",
        "purpose": "sdfef",
        "startDate": "2025-09-06"
    }
    """
    if request.method == 'GET':
        collections = Collection.objects.select_related('building').all()
        
        # Filter by building_id if provided
        building_id = request.GET.get('building_id')
        if building_id:
            collections = collections.filter(building_id=building_id)
        
        serializer = CollectionReadSerializer(collections, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = CollectionSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            collection = serializer.save()
            return Response({
                'message': 'Collection created successfully',
                'collection_id': collection.id,
                'name': collection.name,
                'monthly_amount': str(collection.monthly_amount),
                'start_date': collection.start_date.strftime('%Y-%m-%d'),
                'building_id': collection.building_id,
                'active': collection.active
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
