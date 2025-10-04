from django.core.management.base import BaseCommand
from consumptions.models import ConsumptionType
from financials.models import BudgetCategory

class Command(BaseCommand):
    help = 'Populate initial data for the SINDIPRO system'

    def handle(self, *args, **options):
        self.stdout.write('Populating initial data...')
        
        # Create consumption types
        consumption_types = [
            {'name': 'water', 'unit': 'm³', 'description': 'Water consumption'},
            {'name': 'electricity', 'unit': 'kWh', 'description': 'Electricity consumption'},
            {'name': 'gas', 'unit': 'm³', 'description': 'Gas consumption'},
        ]
        
        for ct_data in consumption_types:
            consumption_type, created = ConsumptionType.objects.get_or_create(
                name=ct_data['name'],
                defaults=ct_data
            )
            if created:
                self.stdout.write(f'Created consumption type: {consumption_type.name}')
        
        # Create budget categories
        budget_categories = [
            {'name': 'Maintenance', 'description': 'Building and equipment maintenance'},
            {'name': 'Cleaning', 'description': 'Cleaning services and supplies'},
            {'name': 'Security', 'description': 'Security services and equipment'},
            {'name': 'Administration', 'description': 'Administrative expenses'},
            {'name': 'Electricity', 'description': 'Electrical expenses'},
            {'name': 'Water', 'description': 'Water and sewer expenses'},
            {'name': 'Gas', 'description': 'Gas expenses'},
            {'name': 'Insurance', 'description': 'Insurance premiums'},
            {'name': 'Legal', 'description': 'Legal and professional services'},
            {'name': 'Equipment', 'description': 'Equipment purchases and upgrades'},
        ]
        
        for bc_data in budget_categories:
            budget_category, created = BudgetCategory.objects.get_or_create(
                name=bc_data['name'],
                defaults=bc_data
            )
            if created:
                self.stdout.write(f'Created budget category: {budget_category.name}')
        
        self.stdout.write(self.style.SUCCESS('Successfully populated initial data'))