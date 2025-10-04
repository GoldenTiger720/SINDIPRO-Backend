from rest_framework import serializers
from .models import ConsumptionRegister, ConsumptionAccount


class ConsumptionRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsumptionRegister
        fields = ['id', 'date', 'utility_type', 'gas_category', 'value', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_internal_value(self, data):
        # Map frontend field names to model field names
        internal_data = data.copy()
        
        if 'gasCategory' in data:
            internal_data['gas_category'] = data['gasCategory']
        
        if 'utilityType' in data:
            internal_data['utility_type'] = data['utilityType']
            
        return super().to_internal_value(internal_data)


class ConsumptionAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsumptionAccount
        fields = ['id', 'month', 'utility_type', 'amount', 'payment_date', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_internal_value(self, data):
        # Map frontend field names to model field names
        internal_data = data.copy()
        
        if 'utilityType' in data:
            internal_data['utility_type'] = data['utilityType']
        
        if 'paymentDate' in data:
            internal_data['payment_date'] = data['paymentDate']
            
        return super().to_internal_value(internal_data)