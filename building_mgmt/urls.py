from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_buildings, name='get_buildings'),
    path('all/', views.get_all_buildings, name='get_all_buildings'),
    path('create/', views.create_building, name='create_building'),
    path('<int:id>/', views.update_building, name='update_building'),
    path('<int:id>/units/', views.create_unit, name='create_unit'),
    path('<int:id>/units/export/excel/', views.export_units_excel, name='export_units_excel'),
    path('<int:id>/units/import/excel/', views.import_units_excel, name='import_units_excel'),
    path('units/', views.get_units, name='get_units'),
    path('units/<int:id>/', views.update_unit, name='update_unit'),
    path('units/debug/<int:id>/', views.debug_unit, name='debug_unit'),
    path('<int:id>/units/test-import/', views.test_import_endpoint, name='test_import_endpoint'),
    path('<int:id>/units/import-simple/', views.simple_import_test, name='simple_import_test'),
]
