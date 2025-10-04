from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.consumption_register, name='consumption_register'),
    path('account/', views.consumption_account, name='consumption_account'),
]
