from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import FinancialMainAccount, AnnualBudget, Expense, Collection, FinancialAccountTransaction
from .serializers import (FinancialMainAccountSerializer, FinancialMainAccountReadSerializer,
                          AnnualBudgetSerializer, ExpenseSerializer, ExpenseReadSerializer,
                          AnnualBudgetReadSerializer, CollectionSerializer, CollectionReadSerializer,
                          FinancialAccountTransactionSerializer)
from datetime import datetime
from collections import defaultdict
from decimal import Decimal

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


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def financial_account_detail_view(request, account_id):
    """
    PUT: Update a financial account
    DELETE: Delete a financial account
    """
    try:
        account = FinancialMainAccount.objects.get(id=account_id)
    except FinancialMainAccount.DoesNotExist:
        return Response({'error': 'Financial account not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = FinancialMainAccountSerializer(account, data=request.data, partial=True)
        if serializer.is_valid():
            updated_account = serializer.save()
            response_serializer = FinancialMainAccountReadSerializer(updated_account)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid data', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        account.delete()
        return Response({'message': 'Financial account deleted successfully'}, status=status.HTTP_200_OK)


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
                'start_date': collection.start_date,  # start_date is already a string (YYYY-MM format)
                'end_date': collection.end_date,  # end_date is also a string
                'building_id': collection.building_id,
                'active': collection.active
            }, status=status.HTTP_201_CREATED)

        return Response({
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def collection_detail_view(request, collection_id):
    """
    PUT: Update a collection entry
    DELETE: Delete a collection entry
    """
    try:
        collection = Collection.objects.get(id=collection_id)
    except Collection.DoesNotExist:
        return Response({'error': 'Collection not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = CollectionSerializer(collection, data=request.data, partial=True)
        if serializer.is_valid():
            updated_collection = serializer.save()
            # Return the updated collection using the read serializer
            response_serializer = CollectionReadSerializer(updated_collection)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid data', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        collection.delete()
        return Response({'message': 'Collection deleted successfully'}, status=status.HTTP_200_OK)


# New views for comprehensive financial control system

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def revenue_account_view(request):
    """
    GET: Retrieve revenue accounts
         Query parameter: building_id (required)
    POST: Create a new revenue account
    """
    if request.method == 'GET':
        building_id = request.GET.get('building_id')
        if not building_id:
            return Response({'error': 'building_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        from .models import RevenueAccount
        from .serializers import RevenueAccountSerializer

        revenues = RevenueAccount.objects.filter(building_id=building_id).order_by('-created_at')
        serializer = RevenueAccountSerializer(revenues, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        from .serializers import RevenueAccountSerializer

        serializer = RevenueAccountSerializer(data=request.data)
        if serializer.is_valid():
            revenue = serializer.save()
            response_serializer = RevenueAccountSerializer(revenue)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response({'error': 'Invalid data', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def revenue_account_detail_view(request, revenue_id):
    """
    DELETE: Delete a revenue account
    """
    from .models import RevenueAccount

    try:
        revenue = RevenueAccount.objects.get(id=revenue_id)
        revenue.delete()
        return Response({'message': 'Revenue account deleted successfully'}, status=status.HTTP_200_OK)
    except RevenueAccount.DoesNotExist:
        return Response({'error': 'Revenue account not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def extend_revenue_view(request, revenue_id):
    """
    POST: Extend revenue validity period
    Expected data: {"extend_to_month": "YYYY-MM"}
    """
    from .models import RevenueAccount

    try:
        revenue = RevenueAccount.objects.get(id=revenue_id)
        extend_to_month = request.data.get('extend_to_month')

        if not extend_to_month:
            return Response({'error': 'extend_to_month is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Extend the end_month and mark as extended
        revenue.end_month = extend_to_month
        revenue.is_extended = True
        revenue.save()

        from .serializers import RevenueAccountSerializer
        serializer = RevenueAccountSerializer(revenue)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except RevenueAccount.DoesNotExist:
        return Response({'error': 'Revenue account not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def expense_entry_view(request):
    """
    GET: Retrieve expense entries
         Query parameter: building_id (required)
    POST: Create a new expense entry
    """
    if request.method == 'GET':
        building_id = request.GET.get('building_id')
        if not building_id:
            return Response({'error': 'building_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        from .models import ExpenseEntry
        from .serializers import ExpenseEntrySerializer

        expenses = ExpenseEntry.objects.filter(building_id=building_id).order_by('-reference_month', '-created_at')
        serializer = ExpenseEntrySerializer(expenses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        from .serializers import ExpenseEntrySerializer

        serializer = ExpenseEntrySerializer(data=request.data)
        if serializer.is_valid():
            expense = serializer.save()
            response_serializer = ExpenseEntrySerializer(expense)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response({'error': 'Invalid data', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def expense_entry_detail_view(request, expense_id):
    """
    DELETE: Delete an expense entry
    """
    from .models import ExpenseEntry

    try:
        expense = ExpenseEntry.objects.get(id=expense_id)
        expense.delete()
        return Response({'message': 'Expense entry deleted successfully'}, status=status.HTTP_200_OK)
    except ExpenseEntry.DoesNotExist:
        return Response({'error': 'Expense entry not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def financial_report_view(request):
    """
    GET: Generate financial report
         Query parameters:
         - building_id (required)
         - fiscal_year_start (required, format: YYYY-MM)
         - fiscal_year_end (required, format: YYYY-MM)
    """
    building_id = request.GET.get('building_id')
    fiscal_year_start = request.GET.get('fiscal_year_start')
    fiscal_year_end = request.GET.get('fiscal_year_end')

    if not all([building_id, fiscal_year_start, fiscal_year_end]):
        return Response({
            'error': 'building_id, fiscal_year_start, and fiscal_year_end are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        from .serializers import FinancialReportSerializer

        data = {
            'building_id': int(building_id),
            'fiscal_year_start': fiscal_year_start,
            'fiscal_year_end': fiscal_year_end
        }

        serializer = FinancialReportSerializer(data)
        result = serializer.to_representation(data)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating financial report: {str(e)}")
        logger.error(traceback.format_exc())
        return Response({
            'error': f'Failed to generate report: {str(e)}',
            'type': type(e).__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def additional_charge_view(request):
    """
    GET: Retrieve additional charges
         Query parameters:
         - building_id (required)
         - reference_month (optional)
    POST: Create a new additional charge
    """
    if request.method == 'GET':
        building_id = request.GET.get('building_id')
        if not building_id:
            return Response({'error': 'building_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        from .models import AdditionalCharge
        from .serializers import AdditionalChargeSerializer

        charges = AdditionalCharge.objects.filter(building_id=building_id)

        # Optional filter by reference_month
        reference_month = request.GET.get('reference_month')
        if reference_month:
            charges = charges.filter(reference_month=reference_month)

        charges = charges.order_by('-reference_month', '-created_at')
        serializer = AdditionalChargeSerializer(charges, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        from .serializers import AdditionalChargeSerializer

        serializer = AdditionalChargeSerializer(data=request.data)
        if serializer.is_valid():
            charge = serializer.save()
            response_serializer = AdditionalChargeSerializer(charge)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response({'error': 'Invalid data', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def additional_charge_detail_view(request, charge_id):
    """
    PUT: Update an additional charge
    DELETE: Delete an additional charge
    """
    from .models import AdditionalCharge
    from .serializers import AdditionalChargeSerializer

    try:
        charge = AdditionalCharge.objects.get(id=charge_id)
    except AdditionalCharge.DoesNotExist:
        return Response({'error': 'Additional charge not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = AdditionalChargeSerializer(charge, data=request.data, partial=True)
        if serializer.is_valid():
            updated_charge = serializer.save()
            response_serializer = AdditionalChargeSerializer(updated_charge)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid data', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        charge.delete()
        return Response({'message': 'Additional charge deleted successfully'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calculate_fees_view(request):
    """
    GET: Calculate fees for all units in a building
         Query parameters:
         - building_id (required)
         - reference_month (required, format: YYYY-MM)
    """
    building_id = request.GET.get('building_id')
    reference_month = request.GET.get('reference_month')

    if not building_id or not reference_month:
        return Response({
            'error': 'building_id and reference_month are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        from building_mgmt.models import Unit
        from .models import RevenueAccount, AdditionalCharge
        from decimal import Decimal

        # Get all units for the building
        units = Unit.objects.filter(building_id=building_id).select_related('building')

        if not units.exists():
            return Response({
                'error': 'No units found for this building'
            }, status=status.HTTP_404_NOT_FOUND)

        # Calculate total ideal fraction
        total_ideal_fraction = sum(float(unit.ideal_fraction) for unit in units)
        is_fraction_valid = abs(total_ideal_fraction - 1.0) < 0.0001  # Allow small floating point errors

        # Get revenue accounts for the building and reference month
        revenue_accounts = RevenueAccount.objects.filter(
            building_id=building_id
        )

        # Calculate total regular budget from revenue accounts
        total_regular_budget = Decimal('0.00')
        for revenue in revenue_accounts:
            # Extract year from reference_month (YYYY-MM format)
            reference_year = reference_month[:4]

            # Check if the reference year is within the revenue period (years are stored as YYYY)
            if revenue.start_month <= reference_year <= revenue.end_month:
                total_regular_budget += revenue.monthly_amount

        # Get active additional charges for the reference month
        additional_charges = AdditionalCharge.objects.filter(
            building_id=building_id,
            reference_month=reference_month,
            active=True
        )

        total_additional_charges = sum(charge.total_amount for charge in additional_charges)

        # Calculate total monthly collection
        total_monthly_collection = total_regular_budget + total_additional_charges

        # Calculate fees for each unit
        unit_fees = []
        for unit in units:
            ideal_fraction = float(unit.ideal_fraction)

            # Calculate regular fee
            regular_fee = float(total_regular_budget) * ideal_fraction

            # Calculate additional fee
            additional_fee = float(total_additional_charges) * ideal_fraction

            # Calculate total fee
            total_fee = regular_fee + additional_fee

            unit_fees.append({
                'unitId': unit.id,
                'unitNumber': unit.number,
                'ownerName': unit.owner or '',
                'idealFraction': ideal_fraction,
                'regularFee': round(regular_fee, 2),
                'additionalFee': round(additional_fee, 2),
                'totalFee': round(total_fee, 2)
            })

        response_data = {
            'buildingId': int(building_id),
            'referenceMonth': reference_month,
            'totalRegularBudget': float(total_regular_budget),
            'totalAdditionalCharges': float(total_additional_charges),
            'totalMonthlyCollection': float(total_monthly_collection),
            'totalIdealFraction': total_ideal_fraction,
            'isIdealFractionValid': is_fraction_valid,
            'unitFees': unit_fees
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to calculate fees',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def validate_fractions_view(request):
    """
    GET: Validate ideal fractions for a building
         Query parameter: building_id (required)
    """
    building_id = request.GET.get('building_id')

    if not building_id:
        return Response({
            'error': 'building_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        from building_mgmt.models import Unit

        units = Unit.objects.filter(building_id=building_id)

        if not units.exists():
            return Response({
                'isValid': True,
                'totalFraction': 0.0,
                'unitCount': 0
            }, status=status.HTTP_200_OK)

        # Calculate total ideal fraction
        total_fraction = sum(float(unit.ideal_fraction) for unit in units)

        # Check if total is approximately 1.0 (100%)
        is_valid = abs(total_fraction - 1.0) < 0.0001  # Allow small floating point errors

        return Response({
            'isValid': is_valid,
            'totalFraction': round(total_fraction, 6),
            'unitCount': units.count()
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'Failed to validate ideal fractions',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def account_balance_view(request):
    """
    GET: Retrieve account balances
         Query parameters:
         - building_id (required)
         - reference_month (optional)
         - account_id (optional)
    POST: Create a new account balance
    """
    if request.method == 'GET':
        building_id = request.GET.get('building_id')
        if not building_id:
            return Response({'error': 'building_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        from .models import AccountBalance
        from .serializers import AccountBalanceSerializer

        balances = AccountBalance.objects.filter(building_id=building_id)

        # Optional filters
        reference_month = request.GET.get('reference_month')
        if reference_month:
            balances = balances.filter(reference_month=reference_month)

        account_id = request.GET.get('account_id')
        if account_id:
            balances = balances.filter(account_id=account_id)

        balances = balances.order_by('-reference_month', 'account_name')
        serializer = AccountBalanceSerializer(balances, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        from .serializers import AccountBalanceSerializer

        serializer = AccountBalanceSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            balance = serializer.save()
            response_serializer = AccountBalanceSerializer(balance)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response({'error': 'Invalid data', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def account_balance_detail_view(request, balance_id):
    """
    PUT: Update an account balance
    DELETE: Delete an account balance
    """
    from .models import AccountBalance
    from .serializers import AccountBalanceSerializer

    try:
        balance = AccountBalance.objects.get(id=balance_id)
    except AccountBalance.DoesNotExist:
        return Response({'error': 'Account balance not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = AccountBalanceSerializer(balance, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            updated_balance = serializer.save()
            response_serializer = AccountBalanceSerializer(updated_balance)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid data', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        balance.delete()
        return Response({'message': 'Account balance deleted successfully'}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def account_transaction_view(request):
    """
    GET: Retrieve account transactions
         Query parameters:
         - building_id (required)
         - account_id (optional)
         - reference_month (optional)
    POST: Create a new account transaction (expense entry for an account)
    Expected data structure:
    {
        "accountId": 1,
        "buildingId": 1,
        "amount": 100.50,
        "referenceMonth": "2025-10",
        "description": "Optional description"
    }
    """
    if request.method == 'GET':
        building_id = request.GET.get('building_id')
        if not building_id:
            return Response({'error': 'building_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        transactions = FinancialAccountTransaction.objects.filter(building_id=building_id).select_related('account')

        # Optional filters
        account_id = request.GET.get('account_id')
        if account_id:
            transactions = transactions.filter(account_id=account_id)

        reference_month = request.GET.get('reference_month')
        if reference_month:
            transactions = transactions.filter(reference_month=reference_month)

        transactions = transactions.order_by('-reference_month', '-created_at')
        serializer = FinancialAccountTransactionSerializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = FinancialAccountTransactionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            transaction = serializer.save()
            response_serializer = FinancialAccountTransactionSerializer(transaction)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response({'error': 'Invalid data', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def account_transaction_detail_view(request, transaction_id):
    """
    GET: Get a specific transaction
    PUT: Update a transaction and adjust the account's actual_amount accordingly
    DELETE: Delete a transaction and adjust the account's actual_amount
    """
    try:
        transaction = FinancialAccountTransaction.objects.select_related('account').get(id=transaction_id)
    except FinancialAccountTransaction.DoesNotExist:
        return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = FinancialAccountTransactionSerializer(transaction)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        # Update the transaction
        serializer = FinancialAccountTransactionSerializer(
            transaction,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        # Adjust the account's actual_amount before deleting
        account = transaction.account
        account.actual_amount -= transaction.amount
        account.save()

        transaction.delete()
        return Response({'message': 'Transaction deleted successfully'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def account_monthly_data_view(request):
    """
    GET: Retrieve monthly breakdown data for a specific account
         Query parameters:
         - account_id (required): The financial account ID
         - year (optional): Year to filter data (defaults to current year)
    """
    account_id = request.GET.get('account_id')
    year = request.GET.get('year', str(datetime.now().year))

    if not account_id:
        return Response({
            'error': 'account_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get the account
        account = FinancialMainAccount.objects.get(id=account_id)

        # Get all transactions for this account in the specified year
        transactions = FinancialAccountTransaction.objects.filter(
            account_id=account_id,
            reference_month__startswith=year
        ).order_by('reference_month')

        # Aggregate transactions by month
        monthly_actual = defaultdict(Decimal)
        for transaction in transactions:
            monthly_actual[transaction.reference_month] += transaction.amount

        # Generate data for all 12 months
        months_data = []
        for month_num in range(1, 13):
            month_str = f"{year}-{str(month_num).zfill(2)}"

            # Calculate expected amount for this month if within assembly period
            expected_amount = Decimal('0')
            if account.assembly_start_date and account.assembly_end_date:
                # Handle both string and date objects
                if isinstance(account.assembly_start_date, str):
                    start_date = datetime.strptime(account.assembly_start_date, '%Y-%m')
                    end_date = datetime.strptime(account.assembly_end_date, '%Y-%m')
                else:
                    start_date = datetime(account.assembly_start_date.year, account.assembly_start_date.month, 1)
                    end_date = datetime(account.assembly_end_date.year, account.assembly_end_date.month, 1)

                month_date = datetime(int(year), month_num, 1)

                if start_date <= month_date <= end_date:
                    expected_amount = account.expected_amount or Decimal('0')

            actual_amount = monthly_actual.get(month_str, Decimal('0'))

            months_data.append({
                'month': month_str,
                'expectedAmount': float(expected_amount),
                'actualAmount': float(actual_amount),
            })

        return Response({
            'accountId': account.id,
            'accountCode': account.code,
            'accountName': account.name,
            'year': year,
            'totalExpected': float(account.expected_amount or 0),
            'totalActual': float(account.actual_amount or 0),
            'monthlyData': months_data
        }, status=status.HTTP_200_OK)

    except FinancialMainAccount.DoesNotExist:
        return Response({
            'error': 'Account not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching account monthly data: {str(e)}")
        logger.error(traceback.format_exc())
        return Response({
            'error': f'Failed to fetch account monthly data: {str(e)}',
            'type': type(e).__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
