from rest_framework import serializers
from .models import ReportJustification


class ReportJustificationSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source='building.building_name', read_only=True)

    class Meta:
        model = ReportJustification
        fields = [
            'id',
            'building',
            'building_name',
            # Page 3
            'page3_financial_justification',
            # Page 4
            'page4_income_justification',
            'page4_expenses_justification',
            'page4_balance_justification',
            # Page 5 - Sections for accounts 3-10
            'page5_section1_justification',
            'page5_section2_justification',
            'page5_section3_justification',
            'page5_section4_justification',
            'page5_section5_justification',
            'page5_section6_justification',
            'page5_section7_justification',
            'page5_section8_justification',
            # Page 7
            'page7_legal_justification',
            # Page 8 - Separate fields for each utility type
            'page8_water_justification',
            'page8_electricity_justification',
            'page8_gas_justification',
            # Page 9
            'page9_requests_justification',
            # Page 10
            'page10_calendar_justification',
            # Metadata
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'building_name', 'created_at', 'updated_at']


class ReportJustificationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating justification fields"""

    class Meta:
        model = ReportJustification
        fields = [
            # Page 3
            'page3_financial_justification',
            # Page 4
            'page4_income_justification',
            'page4_expenses_justification',
            'page4_balance_justification',
            # Page 5 - Sections for accounts 3-10
            'page5_section1_justification',
            'page5_section2_justification',
            'page5_section3_justification',
            'page5_section4_justification',
            'page5_section5_justification',
            'page5_section6_justification',
            'page5_section7_justification',
            'page5_section8_justification',
            # Page 7
            'page7_legal_justification',
            # Page 8 - Separate fields for each utility type
            'page8_water_justification',
            'page8_electricity_justification',
            'page8_gas_justification',
            # Page 9
            'page9_requests_justification',
            # Page 10
            'page10_calendar_justification',
        ]
