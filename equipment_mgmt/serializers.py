from rest_framework import serializers
from .models import Equipment, MaintenanceRecord, EquipmentDocument


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    technicianPhone = serializers.CharField(source='technician_phone', allow_blank=True, required=False)

    class Meta:
        model = MaintenanceRecord
        fields = ['id', 'cost', 'date', 'description', 'notes', 'technician', 'technicianPhone', 'type']
        read_only_fields = ['id']


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


class EquipmentWithMaintenanceSerializer(serializers.ModelSerializer):
    contractorName = serializers.CharField(source='contractor_name')
    contractorPhone = serializers.CharField(source='contractor_phone')
    maintenanceFrequency = serializers.CharField(source='maintenance_frequency')
    purchaseDate = serializers.DateField(source='purchase_date')
    building_id = serializers.CharField()
    maintenanceRecords = MaintenanceRecordSerializer(source='maintenance_records', many=True, read_only=True)

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
            'updated_at',
            'maintenanceRecords'
        ]
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')


class EquipmentDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentDocument
        fields = '__all__'
        read_only_fields = ('uploaded_by', 'created_at')