from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.consumption_register, name='consumption_register'),
    path('register/<int:register_id>/', views.consumption_register_detail, name='consumption_register_detail'),
    path('account/', views.consumption_account, name='consumption_account'),
    path('sub-accounts/', views.sub_account_list, name='sub_account_list'),
    path('sub-accounts/<int:sub_account_id>/', views.sub_account_detail, name='sub_account_detail'),
]
