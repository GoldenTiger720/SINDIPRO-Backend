from rest_framework import serializers
from .models import LegalDocument, LegalObligation, LegalTemplate, LegalObligationCompletion
from building_mgmt.models import Building


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
    dueMonth = serializers.DateField(source='due_month', required=False)
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
            'dueMonth',
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