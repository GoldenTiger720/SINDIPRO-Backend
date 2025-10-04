from django.urls import path
from . import views

urlpatterns = [
    path('account/', views.financial_account_view, name='financial_account_view'),
    path('annual/', views.annual_budget_view, name='annual_budget_view'),
    path('expense/', views.expense_view, name='expense_view'),
    path('collection/', views.collection_view, name='collection_view'),
]
