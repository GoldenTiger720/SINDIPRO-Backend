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

    # New fields for assembly period and fiscal year
    assembly_start_date = models.DateField(null=True, blank=True)
    assembly_end_date = models.DateField(null=True, blank=True)
    fiscal_year = models.IntegerField(null=True, blank=True)

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
    start_date = models.CharField(max_length=7)  # Format: YYYY-MM (start month)
    end_date = models.CharField(max_length=7, null=True, blank=True)  # Format: YYYY-MM (end month)
    active = models.BooleanField(default=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financials_collection'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.building.building_name} - {self.name} - {self.monthly_amount}"


# New models for comprehensive financial control system

class RevenueAccount(models.Model):
    """
    Fixed monthly revenue account with automatic repetition.
    Each account has a fixed amount that repeats for the defined period.
    """
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='revenue_accounts')
    account = models.ForeignKey(FinancialMainAccount, on_delete=models.CASCADE, related_name='revenue_accounts', null=True, blank=True)
    account_name = models.CharField(max_length=200)  # Denormalized for display purposes
    monthly_amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Period configuration
    start_month = models.CharField(max_length=7)  # Format: YYYY (year only)
    end_month = models.CharField(max_length=7)    # Format: YYYY (year only)

    # Fiscal year tracking
    fiscal_year_start = models.CharField(max_length=7)  # Format: YYYY (year only)
    fiscal_year_end = models.CharField(max_length=7)    # Format: YYYY (year only)

    # Extension tracking
    is_extended = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financials_revenue_account'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.building.building_name} - {self.account_name} - R$ {self.monthly_amount}"


class ExpenseEntry(models.Model):
    """
    Monthly expense entries assigned to one of the five parent accounts.
    Expenses are recorded as they are actually incurred.
    """
    PARENT_ACCOUNT_CHOICES = [
        ('personnel_and_charges', 'Personnel and Charges'),
        ('fees_and_public_taxes', 'Fees and Public Taxes'),
        ('contracts', 'Contracts'),
        ('maintenance', 'Maintenance'),
        ('miscellaneous', 'Miscellaneous'),
    ]

    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='expense_entries')
    parent_account = models.CharField(max_length=30, choices=PARENT_ACCOUNT_CHOICES)
    account_name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference_month = models.CharField(max_length=7)  # Format: YYYY-MM
    description = models.TextField(blank=True)

    # Track if expense is outside fiscal period
    is_outside_fiscal_period = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financials_expense_entry'
        ordering = ['-reference_month', '-created_at']
        indexes = [
            models.Index(fields=['building', 'reference_month']),
            models.Index(fields=['parent_account']),
        ]

    def __str__(self):
        return f"{self.building.building_name} - {self.account_name} - {self.reference_month}"

    def save(self, *args, **kwargs):
        # Auto-detect if expense is outside fiscal period
        if self.building:
            revenue_accounts = self.building.revenue_accounts.all()
            if revenue_accounts.exists():
                # Get the fiscal period from any revenue account
                fiscal_start = revenue_accounts.first().fiscal_year_start
                fiscal_end = revenue_accounts.first().fiscal_year_end
                self.is_outside_fiscal_period = (
                    self.reference_month < fiscal_start or
                    self.reference_month > fiscal_end
                )
        super().save(*args, **kwargs)


class AdditionalCharge(models.Model):
    """
    Additional charges (extra apportionment) that are distributed across units.
    These are special assessments or extraordinary charges that need to be
    allocated in addition to regular condominium fees.
    """
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='additional_charges')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference_month = models.CharField(max_length=7)  # Format: YYYY-MM
    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financials_additional_charge'
        ordering = ['-reference_month', '-created_at']
        indexes = [
            models.Index(fields=['building', 'reference_month']),
            models.Index(fields=['active']),
        ]

    def __str__(self):
        return f"{self.building.building_name} - {self.name} - {self.reference_month}"


class AccountBalance(models.Model):
    """
    Monthly account balances for main accounts.
    At the end of each closed month, record the current balance for each account.
    """
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='account_balances')
    account = models.ForeignKey(FinancialMainAccount, on_delete=models.CASCADE, related_name='balances')
    reference_month = models.CharField(max_length=7)  # Format: YYYY-MM
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financials_account_balance'
        ordering = ['-reference_month', '-created_at']
        unique_together = ('building', 'account', 'reference_month')
        indexes = [
            models.Index(fields=['building', 'reference_month']),
            models.Index(fields=['account', 'reference_month']),
        ]

    def __str__(self):
        return f"{self.building.building_name} - {self.account.name} - {self.reference_month}: R$ {self.balance}"