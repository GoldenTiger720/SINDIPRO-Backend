from rest_framework import serializers
from .models import Building, Address, Tower, TowerUnitDistribution, Unit

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['cep', 'city', 'neighborhood', 'number', 'state', 'street']

class TowerUnitDistributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TowerUnitDistribution
        fields = ['commercial', 'non_residential', 'residential', 'studio', 'wave']

class TowerSerializer(serializers.ModelSerializer):
    unit_distribution = TowerUnitDistributionSerializer(required=False)
    
    class Meta:
        model = Tower
        fields = ['id', 'name', 'units_per_tower', 'unit_distribution']

class UnitSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source='building.building_name', read_only=True)
    building_id = serializers.IntegerField(read_only=True, source='building.id')
    tower_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Unit
        fields = [
            'id', 'area', 'building_id', 'building_name', 'deposit_location',
            'floor', 'ideal_fraction', 'identification',
            'key_delivery', 'number', 'owner', 'owner_phone',
            'parking_spaces', 'status', 'tower_id'
        ]

    def create(self, validated_data):
        # Handle tower_id from the data
        tower_id = validated_data.pop('tower_id', None)
        tower = None

        if tower_id:
            try:
                tower = Tower.objects.get(id=tower_id)
                # Ensure the tower belongs to the same building
                if 'building' in validated_data and validated_data['building'] != tower.building:
                    raise serializers.ValidationError("Tower does not belong to the specified building")
            except Tower.DoesNotExist:
                raise serializers.ValidationError("Invalid tower_id provided")

        # Create the unit with the tower
        if tower:
            validated_data['tower'] = tower

        unit = Unit.objects.create(**validated_data)
        return unit

    def update(self, instance, validated_data):
        # Handle tower_id from the data
        tower_id = validated_data.pop('tower_id', None)

        if tower_id is not None:
            if tower_id:
                try:
                    tower = Tower.objects.get(id=tower_id)
                    # Ensure the tower belongs to the same building
                    if instance.building != tower.building:
                        raise serializers.ValidationError("Tower does not belong to the same building as the unit")
                    instance.tower = tower
                except Tower.DoesNotExist:
                    raise serializers.ValidationError("Invalid tower_id provided")
            else:
                # tower_id is None or 0, clear the tower
                instance.tower = None

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

class UnitDetailSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source='building.building_name', read_only=True)
    building_id = serializers.IntegerField(source='building.id', read_only=True)
    tower_id = serializers.SerializerMethodField()
    tower_name = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = [
            'id', 'area', 'building_id', 'building_name',
            'deposit_location', 'floor', 'ideal_fraction',
            'identification', 'key_delivery', 'number', 'owner', 'owner_phone',
            'parking_spaces', 'status', 'tower_id', 'tower_name', 'created_at', 'updated_at'
        ]

    def get_tower_id(self, obj):
        try:
            return obj.tower.id if obj.tower else None
        except Exception:
            # Handle cases where tower relationship is not loaded or has encoding issues
            return obj.tower_id if hasattr(obj, 'tower_id') else None

    def get_tower_name(self, obj):
        try:
            return obj.tower.name if obj.tower else None
        except Exception:
            # Handle cases where tower relationship is not loaded or has encoding issues
            return None

class BuildingSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    alternative_address = AddressSerializer(required=False, allow_null=True)
    tower_names = serializers.ListField(
        child=serializers.CharField(max_length=100), 
        write_only=True
    )
    units_per_tower_array = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        write_only=True
    )
    tower_unit_distribution = serializers.ListField(
        child=TowerUnitDistributionSerializer(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Building
        fields = [
            'building_name', 'building_type', 'cnpj', 'manager_name', 
            'manager_phone', 'manager_phone_type', 'address', 
            'use_separate_address', 'alternative_address', 'number_of_towers',
            'apartments_per_tower', 'residential_units', 'commercial_units',
            'non_residential_units', 'studio_units', 'wave_units',
            'tower_names', 'units_per_tower_array', 'tower_unit_distribution'
        ]
    
    def to_internal_value(self, data):
        # Map camelCase frontend fields to snake_case
        field_mapping = {
            'buildingName': 'building_name',
            'buildingType': 'building_type', 
            'managerName': 'manager_name',
            'managerPhone': 'manager_phone',
            'managerPhoneType': 'manager_phone_type',
            'numberOfTowers': 'number_of_towers',
            'apartmentsPerTower': 'apartments_per_tower',
            'residentialUnits': 'residential_units',
            'commercialUnits': 'commercial_units',
            'nonResidentialUnits': 'non_residential_units',
            'studioUnits': 'studio_units',
            'waveUnits': 'wave_units',
            'useSeparateAddress': 'use_separate_address',
            'alternativeAddress': 'alternative_address',
            'towerNames': 'tower_names',
            'unitsPerTowerArray': 'units_per_tower_array',
            'towerUnitDistribution': 'tower_unit_distribution'
        }
        
        # Create a new data dict with mapped field names
        mapped_data = {}
        for key, value in data.items():
            mapped_key = field_mapping.get(key, key)
            mapped_data[mapped_key] = value
        
        return super().to_internal_value(mapped_data)
    
    def create(self, validated_data):
        # Extract nested data
        address_data = validated_data.pop('address')
        alternative_address_data = validated_data.pop('alternative_address', None)
        tower_names = validated_data.pop('tower_names')
        units_per_tower_array = validated_data.pop('units_per_tower_array')
        tower_unit_distribution = validated_data.pop('tower_unit_distribution', [])
        
        # Create primary address
        address = Address.objects.create(**address_data)
        validated_data['address'] = address
        
        # Create alternative address if provided
        if alternative_address_data:
            alternative_address = Address.objects.create(**alternative_address_data)
            validated_data['alternative_address'] = alternative_address
        
        # Create building
        building = Building.objects.create(**validated_data)
        
        # Create towers
        for i, tower_name in enumerate(tower_names):
            tower_data = {
                'building': building,
                'name': tower_name,
                'units_per_tower': units_per_tower_array[i]
            }
            tower = Tower.objects.create(**tower_data)
            
            # Create unit distribution for mixed buildings
            if building.building_type == 'mixed' and i < len(tower_unit_distribution):
                distribution_data = tower_unit_distribution[i]
                distribution_data['tower'] = tower
                TowerUnitDistribution.objects.create(**distribution_data)
        
        return building

    def update(self, instance, validated_data):
        # Extract nested data
        address_data = validated_data.pop('address', None)
        alternative_address_data = validated_data.pop('alternative_address', None)
        tower_names = validated_data.pop('tower_names', None)
        units_per_tower_array = validated_data.pop('units_per_tower_array', None)
        tower_unit_distribution = validated_data.pop('tower_unit_distribution', [])

        # Update building fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update primary address
        if address_data:
            for attr, value in address_data.items():
                setattr(instance.address, attr, value)
            instance.address.save()

        # Update alternative address
        if alternative_address_data:
            if instance.alternative_address:
                for attr, value in alternative_address_data.items():
                    setattr(instance.alternative_address, attr, value)
                instance.alternative_address.save()
            else:
                # Create new alternative address if it doesn't exist
                alternative_address = Address.objects.create(**alternative_address_data)
                instance.alternative_address = alternative_address
        elif validated_data.get('use_separate_address') == False and instance.alternative_address:
            # Delete alternative address if use_separate_address is set to False
            instance.alternative_address.delete()
            instance.alternative_address = None

        instance.save()

        # Update towers if provided
        if tower_names is not None and units_per_tower_array is not None:
            # Delete existing towers (this will cascade delete unit distributions)
            instance.towers.all().delete()

            # Create new towers
            for i, tower_name in enumerate(tower_names):
                tower_data = {
                    'building': instance,
                    'name': tower_name,
                    'units_per_tower': units_per_tower_array[i]
                }
                tower = Tower.objects.create(**tower_data)

                # Create unit distribution for mixed buildings
                if instance.building_type == 'mixed' and i < len(tower_unit_distribution):
                    distribution_data = tower_unit_distribution[i]
                    distribution_data['tower'] = tower
                    TowerUnitDistribution.objects.create(**distribution_data)

        return instance

    def validate(self, data):
        building_type = data.get('building_type')
        
        # Get values from either camelCase or snake_case (camelCase takes precedence)
        tower_names = data.get('tower_names', [])
        units_per_tower_array = data.get('units_per_tower_array', []) 
        number_of_towers = data.get('number_of_towers', 0)
        
        # If tower_names is empty but number_of_towers > 0, generate default names
        if len(tower_names) == 0 and number_of_towers > 0:
            if number_of_towers == 1:
                tower_names = ['Tower 1']
            else:
                tower_names = [f'Tower {i+1}' for i in range(number_of_towers)]
            data['tower_names'] = tower_names
        
        # If units_per_tower_array is empty but number_of_towers > 0, use totalUnits
        if len(units_per_tower_array) == 0 and number_of_towers > 0:
            # Check for totalUnits in the original data (before field mapping)
            original_data = self.initial_data
            total_units = original_data.get('totalUnits')
            if total_units:
                # Distribute units evenly across towers
                units_per_tower = total_units // number_of_towers
                remainder = total_units % number_of_towers
                units_per_tower_array = [units_per_tower] * number_of_towers
                # Add remainder to the last tower
                if remainder > 0:
                    units_per_tower_array[-1] += remainder
                data['units_per_tower_array'] = units_per_tower_array
            else:
                # If no totalUnits provided, set a default of 1 unit per tower
                units_per_tower_array = [1] * number_of_towers
                data['units_per_tower_array'] = units_per_tower_array
        
        if len(tower_names) != len(units_per_tower_array):
            raise serializers.ValidationError(
                "tower_names and units_per_tower_array must have the same length"
            )
        
        if len(tower_names) != number_of_towers:
            raise serializers.ValidationError(
                "Number of tower names must match number_of_towers"
            )
        
        # Validate mixed building requirements
        if building_type == 'mixed':
            required_mixed_fields = [
                'residential_units', 'commercial_units', 'non_residential_units',
                'studio_units', 'wave_units'
            ]
            for field in required_mixed_fields:
                if data.get(field) is None:
                    raise serializers.ValidationError(
                        f"{field} is required for mixed building type"
                    )
            
            # Validate tower unit distribution for mixed buildings
            tower_unit_distribution = data.get('tower_unit_distribution', [])
            if len(tower_unit_distribution) != data.get('number_of_towers', 0):
                raise serializers.ValidationError(
                    "tower_unit_distribution must be provided for each tower in mixed buildings"
                )
        
        # Validate residential building requirements
        elif building_type == 'residential':
            if data.get('apartments_per_tower') is None:
                raise serializers.ValidationError(
                    "apartments_per_tower is required for residential building type"
                )
        
        # Validate alternative address usage
        use_separate_address = data.get('use_separate_address', False)
        alternative_address = data.get('alternative_address')
        
        if use_separate_address and not alternative_address:
            raise serializers.ValidationError(
                "alternative_address is required when use_separate_address is True"
            )
        
        return data

class BuildingReadSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=True)
    alternative_address = AddressSerializer(read_only=True)
    towers = TowerSerializer(many=True, read_only=True)
    
    class Meta:
        model = Building
        fields = [
            'id', 'building_name', 'building_type', 'cnpj', 'manager_name', 
            'manager_phone', 'manager_phone_type', 'address', 
            'use_separate_address', 'alternative_address', 'number_of_towers',
            'apartments_per_tower', 'residential_units', 'commercial_units',
            'non_residential_units', 'studio_units', 'wave_units',
            'towers', 'created_at', 'updated_at'
        ]

class BuildingBasicSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=True)
    alternative_address = AddressSerializer(read_only=True)

    class Meta:
        model = Building
        fields = ['id', 'building_name', 'address', 'alternative_address']