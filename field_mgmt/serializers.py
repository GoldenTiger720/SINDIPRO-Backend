from rest_framework import serializers
from .models import FieldRequest, FieldMgmtTechnical, FieldMgmtTechnicalImage
from building_mgmt.models import Building
import base64
from django.core.files.base import ContentFile


class FieldRequestSerializer(serializers.ModelSerializer):
    building_id = serializers.PrimaryKeyRelatedField(
        queryset=Building.objects.all(), 
        source='building'
    )
    building_name = serializers.CharField(source='building.building_name', read_only=True)
    
    class Meta:
        model = FieldRequest
        fields = ['id', 'building_id', 'building_name', 'caretaker', 'title', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'building_name', 'created_at', 'updated_at']
    
    def validate_items(self, value):
        """Validate items structure"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Items must be a list")
        
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Each item must be an object")
            
            required_fields = ['observations', 'productType', 'quantity']
            for field in required_fields:
                if field not in item:
                    raise serializers.ValidationError(f"Item missing required field: {field}")
            
            if not isinstance(item['quantity'], int) or item['quantity'] <= 0:
                raise serializers.ValidationError("Quantity must be a positive integer")
        
        return value


class FieldMgmtTechnicalImageSerializer(serializers.ModelSerializer):
    image_data_url = serializers.SerializerMethodField()
    
    class Meta:
        model = FieldMgmtTechnicalImage
        fields = ['id', 'image_data_url', 'mime_type', 'filename', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']
    
    def get_image_data_url(self, obj):
        """Convert binary image data back to data URL format for frontend"""
        if obj.image_data:
            # Encode binary data to base64
            base64_data = base64.b64encode(obj.image_data).decode('utf-8')
            # Return as data URL
            return f"data:{obj.mime_type};base64,{base64_data}"
        return None


class FieldMgmtTechnicalSerializer(serializers.ModelSerializer):
    images = FieldMgmtTechnicalImageSerializer(many=True, read_only=True)
    photos = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = FieldMgmtTechnical
        fields = ['id', 'code', 'company_email', 'title', 'description', 'location',
                 'priority', 'images', 'photos', 'created_at', 'updated_at']
        read_only_fields = ['id', 'code', 'created_at', 'updated_at', 'images']
    
    def create(self, validated_data):
        photos_list = validated_data.pop('photos', [])
        technical_request = FieldMgmtTechnical.objects.create(**validated_data)
        
        for idx, image_data_url in enumerate(photos_list):
            if image_data_url.startswith('data:'):
                # Parse the data URL
                # Format: data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA...
                try:
                    # Split header and data
                    header, encoded_data = image_data_url.split(',', 1)
                    # Extract MIME type
                    mime_type = header.split(':')[1].split(';')[0]
                    # Decode base64 to binary
                    binary_data = base64.b64decode(encoded_data)
                    
                    # Generate filename
                    ext = mime_type.split('/')[-1]
                    filename = f'technical_{technical_request.id}_{idx}.{ext}'
                    
                    # Create image record
                    FieldMgmtTechnicalImage.objects.create(
                        technical_request=technical_request,
                        image_data=binary_data,
                        mime_type=mime_type,
                        filename=filename
                    )
                except Exception as e:
                    print(f"Error processing image {idx}: {str(e)}")
                    continue
        
        return technical_request