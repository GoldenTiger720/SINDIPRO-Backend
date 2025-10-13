from django.contrib import admin
from .models import (
    BudgetCategory, AnnualBudget, Expense, Revenue,
    FinancialMainAccount, Collection, RevenueAccount, ExpenseEntry, AdditionalCharge
)


@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(AnnualBudget)
class AnnualBudgetAdmin(admin.ModelAdmin):
    list_display = ['building', 'year', 'category', 'sub_item', 'budgeted_amount', 'created_at']
    list_filter = ['year', 'category', 'building']
    search_fields = ['building__building_name', 'category__name', 'sub_item']
    date_hierarchy = 'created_at'


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['building', 'category', 'expense_type', 'description', 'amount', 'expense_date', 'created_at']
    list_filter = ['expense_type', 'category', 'building', 'expense_date']
    search_fields = ['building__building_name', 'description', 'vendor', 'invoice_number']
    date_hierarchy = 'expense_date'


@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    list_display = ['building', 'revenue_type', 'description', 'amount', 'revenue_date', 'unit_number', 'created_at']
    list_filter = ['revenue_type', 'building', 'revenue_date']
    search_fields = ['building__building_name', 'description', 'unit_number', 'reference_number']
    date_hierarchy = 'revenue_date'


@admin.register(FinancialMainAccount)
class FinancialMainAccountAdmin(admin.ModelAdmin):
    list_display = ['building', 'code', 'name', 'type', 'parent', 'expected_amount', 'actual_amount', 'created_at']
    list_filter = ['type', 'building']
    search_fields = ['building__building_name', 'code', 'name']
    date_hierarchy = 'created_at'


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['building', 'name', 'monthly_amount', 'start_date', 'end_date', 'active', 'created_at']
    list_filter = ['active', 'building']
    search_fields = ['building__building_name', 'name', 'purpose']
    date_hierarchy = 'created_at'


@admin.register(RevenueAccount)
class RevenueAccountAdmin(admin.ModelAdmin):
    list_display = ['building', 'account_name', 'monthly_amount', 'start_month', 'end_month',
                    'fiscal_year_start', 'fiscal_year_end', 'is_extended', 'created_at']
    list_filter = ['is_extended', 'building', 'fiscal_year_start']
    search_fields = ['building__building_name', 'account_name']
    date_hierarchy = 'created_at'
    readonly_fields = ['is_extended', 'created_at', 'updated_at']


@admin.register(ExpenseEntry)
class ExpenseEntryAdmin(admin.ModelAdmin):
    list_display = ['building', 'parent_account', 'account_name', 'amount', 'reference_month',
                    'is_outside_fiscal_period', 'created_at']
    list_filter = ['parent_account', 'is_outside_fiscal_period', 'building', 'reference_month']
    search_fields = ['building__building_name', 'account_name', 'description']
    date_hierarchy = 'created_at'
    readonly_fields = ['is_outside_fiscal_period', 'created_at', 'updated_at']


@admin.register(AdditionalCharge)
class AdditionalChargeAdmin(admin.ModelAdmin):
    list_display = ['building', 'name', 'total_amount', 'reference_month', 'active', 'created_at']
    list_filter = ['active', 'building', 'reference_month']
    search_fields = ['building__building_name', 'name', 'description']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
