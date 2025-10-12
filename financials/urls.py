from django.urls import path
from . import views

urlpatterns = [
    path('account/', views.financial_account_view, name='financial_account_view'),
    path('account/<int:account_id>/', views.financial_account_detail_view, name='financial_account_detail'),
    path('annual/', views.annual_budget_view, name='annual_budget_view'),
    path('expense/', views.expense_view, name='expense_view'),
    path('collection/', views.collection_view, name='collection_view'),
    path('collection/<int:collection_id>/', views.collection_detail_view, name='collection_detail'),

    # New comprehensive financial control system URLs
    path('revenue/', views.revenue_account_view, name='revenue_account_view'),
    path('revenue/<int:revenue_id>/', views.revenue_account_detail_view, name='revenue_account_detail'),
    path('revenue/<int:revenue_id>/extend/', views.extend_revenue_view, name='extend_revenue'),
    path('expense-entries/', views.expense_entry_view, name='expense_entry_view'),
    path('expense-entries/<int:expense_id>/', views.expense_entry_detail_view, name='expense_entry_detail'),
    path('report/', views.financial_report_view, name='financial_report'),

    # Additional charges (extra apportionment)
    path('additional-charge/', views.additional_charge_view, name='additional_charge_view'),
    path('additional-charge/<int:charge_id>/', views.additional_charge_detail_view, name='additional_charge_detail'),

    # Fee calculation and validation
    path('calculate-fees/', views.calculate_fees_view, name='calculate_fees'),
    path('validate-fractions/', views.validate_fractions_view, name='validate_fractions'),
]
