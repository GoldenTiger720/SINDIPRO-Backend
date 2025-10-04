from django.db import models
from django.contrib.auth import get_user_model
from building_mgmt.models import Building

User = get_user_model()

class BudgetCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Budget Categories'

class AnnualBudget(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='annual_budgets')
    year = models.PositiveIntegerField()
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE)
    sub_item = models.CharField(max_length=200, blank=True)
    budgeted_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('building', 'year', 'category', 'sub_item')
    
    def __str__(self):
        return f"{self.building.name} - {self.year} - {self.category.name}"

class Expense(models.Model):
    EXPENSE_TYPE_CHOICES = [
        ('operational', 'Operational'),
        ('maintenance', 'Maintenance'),
        ('emergency', 'Emergency'),
        ('capital', 'Capital Expenditure'),
    ]
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='expenses')
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE)
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPE_CHOICES, default='operational')
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField()
    vendor = models.CharField(max_length=200, blank=True)
    invoice_number = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    
    # File upload for receipts/invoices
    receipt_file = models.FileField(upload_to='expense_receipts/', null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.description} - {self.amount} - {self.expense_date}"
    
    class Meta:
        ordering = ['-expense_date']

class Revenue(models.Model):
    REVENUE_TYPE_CHOICES = [
        ('common_fee', 'Common Area Fee'),
        ('parking_fee', 'Parking Fee'),
        ('rental_income', 'Rental Income'),
        ('late_fee', 'Late Payment Fee'),
        ('special_assessment', 'Special Assessment'),
        ('other', 'Other Revenue'),
    ]
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='revenues')
    revenue_type = models.CharField(max_length=20, choices=REVENUE_TYPE_CHOICES)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    revenue_date = models.DateField()
    unit_number = models.CharField(max_length=20, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.description} - {self.amount} - {self.revenue_date}"
    
    class Meta:
        ordering = ['-revenue_date']

class FinancialMainAccount(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('main', 'Main Account'),
        ('sub', 'Sub Account'),
        ('detailed', 'Detailed Account'),
    ]
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='financial_accounts')
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_accounts')
    expected_amount = models.DecimalField(max_digits=12, decimal_places=2)
    actual_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('building', 'code')
        db_table = 'financials_main_account'
    
    def __str__(self):
        return f"{self.building.building_name} - {self.code} - {self.name}"

class Collection(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='collections')
    name = models.CharField(max_length=200)
    purpose = models.TextField()
    monthly_amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    active = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'financials_collection'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.building.building_name} - {self.name} - {self.monthly_amount}"