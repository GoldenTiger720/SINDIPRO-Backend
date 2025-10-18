from django.urls import path
from . import views

urlpatterns = [
    # User management endpoints
    path('<int:pk>/', views.UserUpdateDestroyView.as_view(), name='user-update-destroy'),
]
