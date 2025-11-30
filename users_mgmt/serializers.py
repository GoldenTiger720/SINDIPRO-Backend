from rest_framework import serializers
from .models import BuildingAccess
from building_mgmt.models import Building


class BuildingAccessSerializer(serializers.ModelSerializer):
    building_id = serializers.IntegerField(source='building.id', read_only=True)
    building_name = serializers.CharField(source='building.building_name', read_only=True)

    class Meta:
        model = BuildingAccess
        fields = (
            'id', 'building_id', 'building_name', 'access_level',
            'can_view_financial', 'can_edit_financial',
            'can_view_equipment', 'can_edit_equipment',
            'can_view_legal', 'can_edit_legal',
            'can_view_field_requests', 'can_edit_field_requests',
            'can_view_reports', 'can_generate_reports',
            'can_manage_users', 'is_active'
        )
        read_only_fields = ('id', 'building_id', 'building_name')


class UserBuildingAssignmentSerializer(serializers.Serializer):
    """Serializer for assigning multiple buildings to a user"""
    building_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=True
    )

    def validate_building_ids(self, value):
        """Validate that all building IDs exist"""
        existing_ids = set(Building.objects.filter(id__in=value).values_list('id', flat=True))
        invalid_ids = set(value) - existing_ids
        if invalid_ids:
            raise serializers.ValidationError(f"Buildings with IDs {invalid_ids} do not exist.")
        return value
