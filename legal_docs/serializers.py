from rest_framework import serializers
from .models import LegalDocument, LegalObligation, LegalTemplate, LegalObligationCompletion
from building_mgmt.models import Building
from datetime import date


class DueDateField(serializers.Field):
    """
    Custom field that accepts a date string (YYYY-MM-DD) from frontend
    and stores it as a date. Also supports legacy month-only format ("MM")
    for backwards compatibility.
    When serializing, returns full date string (YYYY-MM-DD).
    """
    def to_representation(self, value):
        """Convert date to full date string for frontend"""
        if value is None:
            return None
        return value.strftime('%Y-%m-%d')

    def to_internal_value(self, data):
        """Convert date string to date for storage"""
        if data is None or data == '':
            return None
        try:
            # Accept either just month ("01") for legacy or full date ("2024-01-15")
            if len(data) == 2:
                # Legacy month only - convert to first day of that month in current year
                month = int(data)
                if not 1 <= month <= 12:
                    raise serializers.ValidationError("Month must be between 01 and 12")
                return date(date.today().year, month, 1)
            else:
                # Full date string - parse it
                return date.fromisoformat(data)
        except (ValueError, TypeError):
            raise serializers.ValidationError("Invalid date format. Expected 'YYYY-MM-DD' (e.g., '2025-03-15')")


class LegalDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalDocument
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')


class LegalObligationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalObligation
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')


class LegalTemplateSerializer(serializers.ModelSerializer):
    buildingType = serializers.CharField(source='building_type', required=False)
    requiresQuote = serializers.BooleanField(source='requires_quote')
    dueDate = DueDateField(source='due_month', required=False)
    responsibleEmails = serializers.CharField(source='responsible_emails', required=False)
    noticePeriod = serializers.IntegerField(source='notice_period', required=False)
    lastCompletionDate = serializers.DateField(source='last_completion_date', required=False, allow_null=True)
    building_id = serializers.PrimaryKeyRelatedField(
        source='building',
        queryset=Building.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = LegalTemplate
        fields = [
            'id',
            'name',
            'description',
            'building_id',
            'buildingType',
            'frequency',
            'conditions',
            'requiresQuote',
            'active',
            'dueDate',
            'noticePeriod',
            'responsibleEmails',
            'status',
            'lastCompletionDate',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class LegalObligationCompletionSerializer(serializers.ModelSerializer):
    templateName = serializers.CharField(source='template.name', read_only=True)
    completionDate = serializers.DateField(source='completion_date')
    previousDueDate = serializers.DateField(source='previous_due_date', required=False, allow_null=True)
    newDueDate = serializers.DateField(source='new_due_date', required=False, allow_null=True)
    actualCost = serializers.DecimalField(source='actual_cost', max_digits=10, decimal_places=2, required=False, allow_null=True)
    completedBy = serializers.StringRelatedField(source='completed_by', read_only=True)

    class Meta:
        model = LegalObligationCompletion
        fields = [
            'id',
            'template',
            'templateName',
            'completionDate',
            'previousDueDate',
            'newDueDate',
            'notes',
            'actualCost',
            'completedBy',
            'created_at'
        ]
        read_only_fields = ('id', 'completed_by', 'created_at')


class MarkCompletionSerializer(serializers.Serializer):
    """Serializer for marking an obligation as completed"""
    completionDate = serializers.DateField(source='completion_date')
    notes = serializers.CharField(required=False, allow_blank=True)
    actualCost = serializers.DecimalField(source='actual_cost', max_digits=10, decimal_places=2, required=False, allow_null=True)