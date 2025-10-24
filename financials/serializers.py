from rest_framework import serializers
from .models import (
    FinancialMainAccount, AnnualBudget, BudgetCategory, Expense, Collection,
    RevenueAccount, ExpenseEntry, AdditionalCharge, AccountBalance, FinancialAccountTransaction
)
from building_mgmt.models import Building
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from decimal import Decimal

class BuildingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ['id', 'building_name', 'building_type', 'cnpj']

class FinancialMainAccountSerializer(serializers.ModelSerializer):
    buildingId = serializers.IntegerField(source='building_id')
    parentId = serializers.IntegerField(source='parent_id', required=False, allow_null=True)
    actualAmount = serializers.DecimalField(source='actual_amount', max_digits=12, decimal_places=2)
    expectedAmount = serializers.DecimalField(source='expected_amount', max_digits=12, decimal_places=2)
    assemblyStartDate = serializers.DateField(source='assembly_start_date', required=False, allow_null=True)
    assemblyEndDate = serializers.DateField(source='assembly_end_date', required=False, allow_null=True)
    fiscalYear = serializers.IntegerField(source='fiscal_year', required=False, allow_null=True)
    balanceType = serializers.CharField(source='balance_type', required=False, default='ordinary')

    class Meta:
        model = FinancialMainAccount
        fields = ['buildingId', 'code', 'name', 'type', 'parentId', 'actualAmount', 'expectedAmount',
                  'assemblyStartDate', 'assemblyEndDate', 'fiscalYear', 'balanceType']

    def create(self, validated_data):
        return FinancialMainAccount.objects.create(**validated_data)

class FinancialMainAccountReadSerializer(serializers.ModelSerializer):
    building = BuildingInfoSerializer(read_only=True)
    parentId = serializers.IntegerField(source='parent_id', read_only=True)
    actualAmount = serializers.DecimalField(source='actual_amount', max_digits=12, decimal_places=2, read_only=True)
    expectedAmount = serializers.DecimalField(source='expected_amount', max_digits=12, decimal_places=2, read_only=True)
    assemblyStartDate = serializers.DateField(source='assembly_start_date', read_only=True)
    assemblyEndDate = serializers.DateField(source='assembly_end_date', read_only=True)
    fiscalYear = serializers.IntegerField(source='fiscal_year', read_only=True)
    balanceType = serializers.CharField(source='balance_type', read_only=True)

    class Meta:
        model = FinancialMainAccount
        fields = ['id', 'building', 'code', 'name', 'type', 'parentId', 'actualAmount', 'expectedAmount',
                  'assemblyStartDate', 'assemblyEndDate', 'fiscalYear', 'balanceType', 'created_at', 'updated_at']

class AnnualBudgetSerializer(serializers.ModelSerializer):
    account_category = serializers.CharField(write_only=True)
    building_id = serializers.IntegerField()
    sub_item = serializers.CharField(max_length=200)
    budgeted_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        model = AnnualBudget
        fields = ['account_category', 'building_id', 'sub_item', 'budgeted_amount']
        
    def create(self, validated_data):
        account_category_name = validated_data.pop('account_category')
        
        category, created = BudgetCategory.objects.get_or_create(
            name=account_category_name,
            defaults={'description': f'Category for {account_category_name}'}
        )
        
        current_year = datetime.now().year
        
        annual_budget = AnnualBudget.objects.create(
            building_id=validated_data['building_id'],
            year=current_year,
            category=category,
            sub_item=validated_data['sub_item'],
            budgeted_amount=validated_data['budgeted_amount'],
            created_by=self.context.get('request').user if self.context.get('request') else None
        )
        
        return annual_budget

class ExpenseSerializer(serializers.ModelSerializer):
    buildingId = serializers.IntegerField(source='building_id')
    category = serializers.CharField()
    month = serializers.CharField()
    
    class Meta:
        model = Expense
        fields = ['amount', 'buildingId', 'category', 'month']
        
    def create(self, validated_data):
        category_name = validated_data.pop('category')
        month_str = validated_data.pop('month')
        
        # Get or create budget category
        category, created = BudgetCategory.objects.get_or_create(
            name=category_name,
            defaults={'description': f'Category for {category_name}'}
        )
        
        # Parse month string (format: YYYY-MM) and create expense_date as first day of month
        year, month = month_str.split('-')
        expense_date = datetime(int(year), int(month), 1).date()
        
        # Create expense with required fields
        expense = Expense.objects.create(
            building_id=validated_data['building_id'],
            category=category,
            amount=validated_data['amount'],
            expense_date=expense_date,
            expense_type='maintenance',  # Default type based on input
            description=f'{category_name} expense for {month_str}',
            created_by=self.context.get('request').user if self.context.get('request') else None
        )
        
        return expense

class ExpenseReadSerializer(serializers.ModelSerializer):
    building = BuildingInfoSerializer(read_only=True)
    category = serializers.CharField(source='category.name', read_only=True)
    expense_type = serializers.CharField(read_only=True)
    expense_date = serializers.DateField(read_only=True)
    
    class Meta:
        model = Expense
        fields = ['id', 'building', 'category', 'expense_type', 'description', 'amount', 
                 'expense_date', 'vendor', 'invoice_number', 'payment_method', 'notes', 
                 'created_at', 'updated_at']

class AnnualBudgetReadSerializer(serializers.ModelSerializer):
    building = BuildingInfoSerializer(read_only=True)
    category = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = AnnualBudget
        fields = ['id', 'building', 'year', 'category', 'sub_item', 'budgeted_amount', 
                 'created_at', 'updated_at']

class CollectionSerializer(serializers.ModelSerializer):
    buildingId = serializers.IntegerField(source='building_id')
    monthlyAmount = serializers.DecimalField(source='monthly_amount', max_digits=12, decimal_places=2)
    startDate = serializers.CharField(source='start_date')  # Changed to CharField for YYYY-MM format
    endDate = serializers.CharField(source='end_date', required=False, allow_null=True)  # Added endDate field

    class Meta:
        model = Collection
        fields = ['buildingId', 'name', 'purpose', 'monthlyAmount', 'startDate', 'endDate', 'active']

    def create(self, validated_data):
        collection = Collection.objects.create(
            building_id=validated_data['building_id'],
            name=validated_data['name'],
            purpose=validated_data['purpose'],
            monthly_amount=validated_data['monthly_amount'],
            start_date=validated_data['start_date'],
            end_date=validated_data.get('end_date'),
            active=validated_data['active'],
            created_by=self.context.get('request').user if self.context.get('request') else None
        )

        return collection

class CollectionReadSerializer(serializers.ModelSerializer):
    building = BuildingInfoSerializer(read_only=True)
    monthlyAmount = serializers.DecimalField(source='monthly_amount', max_digits=12, decimal_places=2, read_only=True)
    startDate = serializers.CharField(source='start_date', read_only=True)
    endDate = serializers.CharField(source='end_date', read_only=True)

    class Meta:
        model = Collection
        fields = ['id', 'building', 'name', 'purpose', 'monthlyAmount', 'startDate', 'endDate', 'active',
                 'created_at', 'updated_at']


# New serializers for comprehensive financial control system

class RevenueAccountSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating revenue accounts"""
    buildingId = serializers.IntegerField(source='building_id')
    accountId = serializers.IntegerField(source='account_id', write_only=True, required=True)
    accountName = serializers.CharField(source='account_name', read_only=True)
    monthlyAmount = serializers.DecimalField(source='monthly_amount', max_digits=12, decimal_places=2)
    startMonth = serializers.CharField(source='start_month')
    endMonth = serializers.CharField(source='end_month')
    fiscalYearStart = serializers.CharField(source='fiscal_year_start')
    fiscalYearEnd = serializers.CharField(source='fiscal_year_end')
    isExtended = serializers.BooleanField(source='is_extended', read_only=True)

    class Meta:
        model = RevenueAccount
        fields = ['id', 'buildingId', 'accountId', 'accountName', 'monthlyAmount', 'startMonth',
                 'endMonth', 'fiscalYearStart', 'fiscalYearEnd', 'isExtended',
                 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'accountName', 'isExtended', 'createdAt', 'updatedAt']

    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    def validate_accountId(self, value):
        """Validate that the account exists"""
        try:
            FinancialMainAccount.objects.get(id=value)
        except FinancialMainAccount.DoesNotExist:
            raise serializers.ValidationError('Invalid account ID')
        return value

    def create(self, validated_data):
        # Get the account to populate account_name
        account_id = validated_data.get('account_id')
        account = FinancialMainAccount.objects.get(id=account_id)
        validated_data['account_name'] = f"{account.code} - {account.name}"

        return RevenueAccount.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # If account_id is being updated, update account_name as well
        account_id = validated_data.get('account_id')
        if account_id:
            account = FinancialMainAccount.objects.get(id=account_id)
            validated_data['account_name'] = f"{account.code} - {account.name}"

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ExpenseEntrySerializer(serializers.ModelSerializer):
    """Serializer for creating and updating expense entries"""
    buildingId = serializers.IntegerField(source='building_id')
    parentAccount = serializers.ChoiceField(source='parent_account', choices=ExpenseEntry.PARENT_ACCOUNT_CHOICES)
    accountName = serializers.CharField(source='account_name')
    referenceMonth = serializers.CharField(source='reference_month')
    isOutsideFiscalPeriod = serializers.BooleanField(source='is_outside_fiscal_period', read_only=True)

    class Meta:
        model = ExpenseEntry
        fields = ['id', 'buildingId', 'parentAccount', 'accountName', 'amount',
                 'referenceMonth', 'description', 'isOutsideFiscalPeriod',
                 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'isOutsideFiscalPeriod', 'createdAt', 'updatedAt']

    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    def create(self, validated_data):
        return ExpenseEntry.objects.create(**validated_data)


class AdditionalChargeSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating additional charges (extra apportionment)"""
    buildingId = serializers.IntegerField(source='building_id')
    totalAmount = serializers.DecimalField(source='total_amount', max_digits=12, decimal_places=2)
    referenceMonth = serializers.CharField(source='reference_month')

    class Meta:
        model = AdditionalCharge
        fields = ['id', 'buildingId', 'name', 'description', 'totalAmount',
                 'referenceMonth', 'active', 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'createdAt', 'updatedAt']

    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    def create(self, validated_data):
        return AdditionalCharge.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AccountBalanceSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating account balances"""
    buildingId = serializers.IntegerField(source='building_id')
    accountName = serializers.CharField(source='account_name')
    referenceMonth = serializers.CharField(source='reference_month')
    balanceType = serializers.ChoiceField(source='balance_type', choices=AccountBalance.BALANCE_TYPE_CHOICES, default='ordinary')
    balanceName = serializers.CharField(source='balance_name', required=False, allow_blank=True)

    class Meta:
        model = AccountBalance
        fields = ['id', 'buildingId', 'accountName',
                 'referenceMonth', 'balance', 'delinquency', 'balanceType', 'balanceName', 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'createdAt', 'updatedAt']

    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    def validate(self, data):
        """Validate that extraordinary balances have a balance_name"""
        balance_type = data.get('balance_type', 'ordinary')
        balance_name = data.get('balance_name', '')

        if balance_type == 'extraordinary' and not balance_name:
            raise serializers.ValidationError({
                'balanceName': 'Balance name is required for extraordinary balances'
            })

        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context.get('request').user if self.context.get('request') else None
        return AccountBalance.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class FinancialAccountTransactionSerializer(serializers.ModelSerializer):
    """Serializer for creating and reading financial account transactions"""
    accountId = serializers.IntegerField(source='account_id')
    buildingId = serializers.IntegerField(source='building_id')
    referenceMonth = serializers.CharField(source='reference_month')
    accountCode = serializers.CharField(source='account.code', read_only=True)
    accountName = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = FinancialAccountTransaction
        fields = ['id', 'accountId', 'buildingId', 'amount', 'referenceMonth',
                 'description', 'accountCode', 'accountName', 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'accountCode', 'accountName', 'createdAt', 'updatedAt']

    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    def create(self, validated_data):
        # Create the transaction
        validated_data['created_by'] = self.context.get('request').user if self.context.get('request') else None
        transaction = FinancialAccountTransaction.objects.create(**validated_data)

        # Update the account's actual_amount
        account = transaction.account
        account.actual_amount += transaction.amount
        account.save()

        return transaction

    def update(self, instance, validated_data):
        # Store old values for account adjustment
        old_amount = instance.amount
        old_account = instance.account

        # Get new account if account_id is being changed
        new_account_id = validated_data.get('account_id', instance.account_id)
        new_account = FinancialMainAccount.objects.get(id=new_account_id) if new_account_id != instance.account_id else old_account
        new_amount = validated_data.get('amount', instance.amount)

        # If account changed, adjust both old and new account's actual_amount
        if new_account.id != old_account.id:
            # Remove amount from old account
            old_account.actual_amount -= old_amount
            old_account.save()

            # Add amount to new account
            new_account.actual_amount += new_amount
            new_account.save()
        else:
            # Same account, just adjust the difference
            amount_difference = new_amount - old_amount
            old_account.actual_amount += amount_difference
            old_account.save()

        # Update the transaction fields
        instance.account_id = new_account_id
        instance.amount = new_amount
        instance.reference_month = validated_data.get('reference_month', instance.reference_month)
        instance.description = validated_data.get('description', instance.description)
        instance.save()

        return instance


class FinancialReportSerializer(serializers.Serializer):
    """Serializer for financial report data aggregation"""
    buildingId = serializers.IntegerField()
    referenceMonth = serializers.CharField()
    fiscalYearStart = serializers.CharField()
    fiscalYearEnd = serializers.CharField()
    totalPlannedRevenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    totalActualExpenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthlyData = serializers.ListField()

    def to_representation(self, instance):
        """Generate financial report data"""
        building_id = instance.get('building_id')
        fiscal_year_start = instance.get('fiscal_year_start')
        fiscal_year_end = instance.get('fiscal_year_end')

        # Get all revenue accounts for this building
        revenue_accounts = RevenueAccount.objects.filter(building_id=building_id)

        # Get all expense entries for this building
        expense_entries = ExpenseEntry.objects.filter(building_id=building_id)

        # Generate list of months in the period
        start_date = datetime.strptime(fiscal_year_start, '%Y-%m')
        end_date = datetime.strptime(fiscal_year_end, '%Y-%m')

        # Include extended months from revenue accounts
        for revenue in revenue_accounts:
            revenue_end = datetime.strptime(revenue.end_month, '%Y-%m')
            if revenue_end > end_date:
                end_date = revenue_end

        months = []
        current = start_date
        while current <= end_date:
            months.append(current.strftime('%Y-%m'))
            current += relativedelta(months=1)

        # Aggregate data by month
        monthly_data = []
        total_revenue = Decimal('0')
        total_expenses = Decimal('0')

        for month in months:
            # Calculate revenue for this month
            month_revenue = Decimal('0')
            revenue_by_account = []

            for revenue in revenue_accounts:
                if revenue.start_month <= month <= revenue.end_month:
                    month_revenue += revenue.monthly_amount
                    revenue_by_account.append({
                        'accountName': revenue.account_name,
                        'amount': float(revenue.monthly_amount)
                    })

            # Calculate expenses by parent account for this month
            expenses_by_parent = defaultdict(Decimal)
            month_expenses_entries = expense_entries.filter(reference_month=month)

            for expense in month_expenses_entries:
                expenses_by_parent[expense.parent_account] += expense.amount

            month_expenses = sum(expenses_by_parent.values())

            # Check if month is outside fiscal period
            is_outside = month < fiscal_year_start or month > fiscal_year_end

            monthly_data.append({
                'month': month,
                'totalRevenue': float(month_revenue),
                'totalExpenses': float(month_expenses),
                'isOutsideFiscalPeriod': is_outside,
                'expensesByParent': {
                    'personnel_and_charges': float(expenses_by_parent.get('personnel_and_charges', Decimal('0'))),
                    'fees_and_public_taxes': float(expenses_by_parent.get('fees_and_public_taxes', Decimal('0'))),
                    'contracts': float(expenses_by_parent.get('contracts', Decimal('0'))),
                    'maintenance': float(expenses_by_parent.get('maintenance', Decimal('0'))),
                    'miscellaneous': float(expenses_by_parent.get('miscellaneous', Decimal('0'))),
                },
                'revenueByAccount': revenue_by_account
            })

            total_revenue += month_revenue
            total_expenses += month_expenses

        return {
            'buildingId': building_id,
            'fiscalYearStart': fiscal_year_start,
            'fiscalYearEnd': fiscal_year_end,
            'totalPlannedRevenue': float(total_revenue),
            'totalActualExpenses': float(total_expenses),
            'monthlyData': monthly_data
        }