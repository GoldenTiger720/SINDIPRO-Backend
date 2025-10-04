from rest_framework import serializers
from .models import LegalDocument, LegalObligation, LegalTemplate
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
            'created_at',
            'updated_at'
        ]
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)