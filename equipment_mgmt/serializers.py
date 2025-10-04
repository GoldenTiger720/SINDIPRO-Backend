from rest_framework import serializers
from .models import Equipment, MaintenanceRecord, EquipmentDocument


class EquipmentSerializer(serializers.ModelSerializer):
    contractorName = serializers.CharField(source='contractor_name')
    contractorPhone = serializers.CharField(source='contractor_phone')
    maintenanceFrequency = serializers.CharField(source='maintenance_frequency')
    purchaseDate = serializers.DateField(source='purchase_date')
    building_id = serializers.CharField()

    class Meta:
        model = Equipment
        fields = [
            'id',
            'building_id',
            'name',
            'type',
            'location',
            'purchaseDate',
            'status',
            'maintenanceFrequency',
            'contractorName',
            'contractorPhone',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRecord
        fields = ['cost', 'date', 'description', 'notes', 'technician', 'type']


class EquipmentDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentDocument
        fields = '__all__'
        read_only_fields = ('uploaded_by', 'created_at')