from rest_framework import serializers
from .models import ConsumptionRegister, ConsumptionAccount, SubAccount


class ConsumptionRegisterSerializer(serializers.ModelSerializer):
    utilityType = serializers.CharField(source='utility_type')
    subAccount = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ConsumptionRegister
        fields = ['id', 'building_id', 'date', 'utilityType', 'value', 'subAccount', 'sub_account', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'subAccount']
        extra_kwargs = {
            'building_id': {'source': 'building', 'write_only': False},
            'sub_account': {'write_only': True, 'required': False},
        }

    def get_subAccount(self, obj):
        """Return sub_account details including id and name"""
        if obj.sub_account:
            return {
                'id': obj.sub_account.id,
                'name': obj.sub_account.name,
                'utilityType': obj.sub_account.utility_type
            }
        return None

    def to_internal_value(self, data):
        # Create a mutable copy of the data
        internal_data = data.copy() if hasattr(data, 'copy') else dict(data)

        # Map subAccount -> sub_account for write operations
        if 'subAccount' in internal_data:
            internal_data['sub_account'] = internal_data.pop('subAccount')

        # The utilityType -> utility_type mapping is handled automatically by the field declaration
        return super().to_internal_value(internal_data)


class ConsumptionAccountSerializer(serializers.ModelSerializer):
    utilityType = serializers.CharField(source='utility_type')
    paymentDate = serializers.DateField(source='payment_date')

    class Meta:
        model = ConsumptionAccount
        fields = ['id', 'month', 'utilityType', 'amount', 'paymentDate', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_internal_value(self, data):
        # Map frontend field names to model field names
        internal_data = data.copy()

        if 'utilityType' in data:
            internal_data['utility_type'] = data['utilityType']

        if 'paymentDate' in data:
            internal_data['payment_date'] = data['paymentDate']

        return super().to_internal_value(internal_data)


class SubAccountSerializer(serializers.ModelSerializer):
    utilityType = serializers.CharField(source='utility_type')

    class Meta:
        model = SubAccount
        fields = ['id', 'utilityType', 'name', 'icon', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_internal_value(self, data):
        # Map frontend field names to model field names
        internal_data = data.copy()

        if 'utilityType' in data:
            internal_data['utility_type'] = data['utilityType']

        return super().to_internal_value(internal_data)