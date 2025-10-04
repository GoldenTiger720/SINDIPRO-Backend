from rest_framework import serializers
from .models import FinancialMainAccount, AnnualBudget, BudgetCategory, Expense, Collection
from building_mgmt.models import Building
from datetime import datetime

class BuildingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ['id', 'building_name', 'building_type', 'cnpj']

class FinancialMainAccountSerializer(serializers.ModelSerializer):
    building_id = serializers.IntegerField()
    parentId = serializers.IntegerField(source='parent_id', required=False, allow_null=True)
    actualAmount = serializers.DecimalField(source='actual_amount', max_digits=12, decimal_places=2)
    expectedAmount = serializers.DecimalField(source='expected_amount', max_digits=12, decimal_places=2)
    
    class Meta:
        model = FinancialMainAccount
        fields = ['building_id', 'code', 'name', 'type', 'parentId', 'actualAmount', 'expectedAmount']
        
    def create(self, validated_data):
        return FinancialMainAccount.objects.create(**validated_data)

class FinancialMainAccountReadSerializer(serializers.ModelSerializer):
    building = BuildingInfoSerializer(read_only=True)
    parentId = serializers.IntegerField(source='parent_id', read_only=True)
    actualAmount = serializers.DecimalField(source='actual_amount', max_digits=12, decimal_places=2, read_only=True)
    expectedAmount = serializers.DecimalField(source='expected_amount', max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = FinancialMainAccount
        fields = ['id', 'building', 'code', 'name', 'type', 'parentId', 'actualAmount', 'expectedAmount', 'created_at', 'updated_at']

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
    startDate = serializers.DateField(source='start_date')
    
    class Meta:
        model = Collection
        fields = ['buildingId', 'name', 'purpose', 'monthlyAmount', 'startDate', 'active']
        
    def create(self, validated_data):
        collection = Collection.objects.create(
            building_id=validated_data['building_id'],
            name=validated_data['name'],
            purpose=validated_data['purpose'],
            monthly_amount=validated_data['monthly_amount'],
            start_date=validated_data['start_date'],
            active=validated_data['active'],
            created_by=self.context.get('request').user if self.context.get('request') else None
        )
        
        return collection

class CollectionReadSerializer(serializers.ModelSerializer):
    building = BuildingInfoSerializer(read_only=True)
    monthlyAmount = serializers.DecimalField(source='monthly_amount', max_digits=12, decimal_places=2, read_only=True)
    startDate = serializers.DateField(source='start_date', read_only=True)
    
    class Meta:
        model = Collection
        fields = ['id', 'building', 'name', 'purpose', 'monthlyAmount', 'startDate', 'active', 
                 'created_at', 'updated_at']