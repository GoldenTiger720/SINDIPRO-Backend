from django.urls import path
from . import views

urlpatterns = [
    # User management endpoints
    path('<int:pk>/', views.UserUpdateDestroyView.as_view(), name='user-update-destroy'),
    path('<int:pk>/buildings/', views.UserBuildingAccessView.as_view(), name='user-buildings'),
    path('me/buildings/', views.CurrentUserBuildingsView.as_view(), name='current-user-buildings'),
]
