from django.contrib import admin
from .models import LegalDocument, LegalObligation, LegalTemplate


@admin.register(LegalDocument)
class LegalDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'building', 'document_type', 'status', 'issue_date', 'expiry_date']
    list_filter = ['document_type', 'status', 'building']
    search_fields = ['title', 'document_number', 'description']
    date_hierarchy = 'issue_date'


@admin.register(LegalObligation)
class LegalObligationAdmin(admin.ModelAdmin):
    list_display = ['title', 'building', 'obligation_type', 'status', 'due_date', 'responsible_party']
    list_filter = ['obligation_type', 'status', 'building']
    search_fields = ['title', 'description', 'responsible_party']
    date_hierarchy = 'due_date'


@admin.register(LegalTemplate)
class LegalTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'frequency', 'active', 'building_type', 'requires_quote', 'due_month', 'created_at']
    list_filter = ['active', 'frequency', 'requires_quote', 'building_type', 'due_month']
    search_fields = ['name', 'description', 'conditions', 'responsible_emails']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
