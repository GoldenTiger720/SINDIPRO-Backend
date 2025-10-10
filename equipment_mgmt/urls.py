from django.urls import path
from . import views

urlpatterns = [
    path('', views.equipment_list_create, name='equipment_list_create'),
    path('<int:equipment_id>/', views.equipment_detail, name='equipment_detail'),
    path('<int:equipment_id>/maintenance/', views.maintenance_record_list_create, name='maintenance_record_list_create'),
    path('<int:equipment_id>/maintenance/<int:maintenance_id>/', views.maintenance_record_detail, name='maintenance_record_detail'),
]
