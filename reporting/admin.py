from django.contrib import admin
from .models import ReportTemplate, GeneratedReport, ReportSchedule, ReportAccess, ReportJustification


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'is_active', 'created_by', 'created_at']
    list_filter = ['report_type', 'is_active']
    search_fields = ['name', 'description']


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ['report_name', 'building', 'status', 'report_format', 'generated_by', 'created_at']
    list_filter = ['status', 'report_format', 'building']
    search_fields = ['report_name']


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'building', 'frequency', 'is_active', 'next_run_date']
    list_filter = ['frequency', 'is_active', 'building']
    search_fields = ['name']


@admin.register(ReportAccess)
class ReportAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'building', 'report_template', 'access_level']
    list_filter = ['access_level', 'building']
    search_fields = ['user__username']


@admin.register(ReportJustification)
class ReportJustificationAdmin(admin.ModelAdmin):
    list_display = ['building', 'updated_by', 'updated_at']
    search_fields = ['building__building_name']
    readonly_fields = ['created_at', 'updated_at']
