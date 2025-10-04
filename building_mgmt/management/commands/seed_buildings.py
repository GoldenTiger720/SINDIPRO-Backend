from django.core.management.base import BaseCommand
from django.db import transaction
from building_mgmt.models import Building, Address, Tower, TowerUnitDistribution, Unit
from auth_system.models import User
import random

class Command(BaseCommand):
    help = 'Seed initial building data for the SINDIPRO system'

    def handle(self, *args, **options):
        self.stdout.write('Seeding building data...')
        
        with transaction.atomic():
            # Create sample addresses
            addresses_data = [
                {
                    'cep': '01310-100',
                    'street': 'Avenida Paulista',
                    'number': '1578',
                    'neighborhood': 'Bela Vista',
                    'city': 'São Paulo',
                    'state': 'SP'
                },
                {
                    'cep': '22290-160',
                    'street': 'Rua Visconde de Pirajá',
                    'number': '550',
                    'neighborhood': 'Ipanema',
                    'city': 'Rio de Janeiro',
                    'state': 'RJ'
                },
                {
                    'cep': '30130-100',
                    'street': 'Avenida Afonso Pena',
                    'number': '1000',
                    'neighborhood': 'Centro',
                    'city': 'Belo Horizonte',
                    'state': 'MG'
                },
                {
                    'cep': '80060-000',
                    'street': 'Rua XV de Novembro',
                    'number': '1234',
                    'neighborhood': 'Centro',
                    'city': 'Curitiba',
                    'state': 'PR'
                },
                {
                    'cep': '01404-001',
                    'street': 'Rua Oscar Freire',
                    'number': '379',
                    'neighborhood': 'Jardim Paulista',
                    'city': 'São Paulo',
                    'state': 'SP'
                }
            ]
            
            # Create sample buildings
            buildings_data = [
                {
                    'building_name': 'Edifício Copan',
                    'building_type': 'residential',
                    'cnpj': '12.345.678/0001-90',
                    'manager_name': 'Carlos Silva',
                    'manager_phone': '(11) 98765-4321',
                    'manager_phone_type': 'mobile',
                    'number_of_towers': 1,
                    'apartments_per_tower': 120
                },
                {
                    'building_name': 'Torre Comercial Paulista',
                    'building_type': 'commercial',
                    'cnpj': '23.456.789/0001-01',
                    'manager_name': 'Ana Santos',
                    'manager_phone': '(11) 3456-7890',
                    'manager_phone_type': 'landline',
                    'number_of_towers': 2,
                    'commercial_units': 50,
                    'non_residential_units': 5
                },
                {
                    'building_name': 'Condomínio Residencial Vista Verde',
                    'building_type': 'residential',
                    'cnpj': '34.567.890/0001-12',
                    'manager_name': 'Maria Oliveira',
                    'manager_phone': '(21) 99876-5432',
                    'manager_phone_type': 'mobile',
                    'number_of_towers': 3,
                    'apartments_per_tower': 40
                },
                {
                    'building_name': 'Edifício Misto Central',
                    'building_type': 'mixed',
                    'cnpj': '45.678.901/0001-23',
                    'manager_name': 'João Pereira',
                    'manager_phone': '(31) 98765-1234',
                    'manager_phone_type': 'mobile',
                    'number_of_towers': 2,
                    'residential_units': 60,
                    'commercial_units': 20,
                    'studio_units': 10
                },
                {
                    'building_name': 'Residencial Park Plaza',
                    'building_type': 'residential',
                    'cnpj': '56.789.012/0001-34',
                    'manager_name': 'Pedro Costa',
                    'manager_phone': '(41) 3333-4444',
                    'manager_phone_type': 'landline',
                    'number_of_towers': 4,
                    'apartments_per_tower': 30
                }
            ]
            
            created_buildings = []
            
            for i, building_data in enumerate(buildings_data):
                # Create address
                address = Address.objects.create(**addresses_data[i])
                self.stdout.write(f'Created address: {address}')
                
                # Create building
                building = Building.objects.create(
                    building_name=building_data['building_name'],
                    building_type=building_data['building_type'],
                    cnpj=building_data['cnpj'],
                    manager_name=building_data['manager_name'],
                    manager_phone=building_data['manager_phone'],
                    manager_phone_type=building_data['manager_phone_type'],
                    address=address,
                    number_of_towers=building_data['number_of_towers'],
                    apartments_per_tower=building_data.get('apartments_per_tower'),
                    residential_units=building_data.get('residential_units'),
                    commercial_units=building_data.get('commercial_units'),
                    non_residential_units=building_data.get('non_residential_units'),
                    studio_units=building_data.get('studio_units'),
                    wave_units=building_data.get('wave_units')
                )
                created_buildings.append(building)
                self.stdout.write(f'Created building: {building.building_name}')
                
                # Create towers for each building
                for tower_num in range(1, building.number_of_towers + 1):
                    tower_name = f'Torre {tower_num}' if building.number_of_towers > 1 else 'Torre Única'
                    
                    # Calculate units per tower based on building type
                    if building.building_type == 'residential':
                        units_per_tower = building.apartments_per_tower or 40
                    elif building.building_type == 'commercial':
                        units_per_tower = (building.commercial_units or 20) // building.number_of_towers
                    else:  # mixed
                        total_units = (building.residential_units or 30) + (building.commercial_units or 10) + (building.studio_units or 5)
                        units_per_tower = total_units // building.number_of_towers
                    
                    tower = Tower.objects.create(
                        building=building,
                        name=tower_name,
                        units_per_tower=units_per_tower
                    )
                    self.stdout.write(f'  Created tower: {tower.name}')
                    
                    # Create tower unit distribution for mixed buildings
                    if building.building_type == 'mixed':
                        TowerUnitDistribution.objects.create(
                            tower=tower,
                            commercial=(building.commercial_units or 0) // building.number_of_towers,
                            residential=(building.residential_units or 0) // building.number_of_towers,
                            studio=(building.studio_units or 0) // building.number_of_towers,
                            non_residential=(building.non_residential_units or 0) // building.number_of_towers,
                            wave=(building.wave_units or 0) // building.number_of_towers
                        )
                    
                    # Create units for each tower
                    floors = 10 if building.building_type == 'commercial' else 15
                    units_per_floor = max(1, units_per_tower // floors)
                    
                    for floor in range(1, floors + 1):
                        for unit_num in range(1, min(units_per_floor + 1, units_per_tower - (floor - 1) * units_per_floor + 1)):
                            unit_number = f'{floor:02d}{unit_num:02d}'
                            
                            # Determine unit type based on building type
                            if building.building_type == 'residential':
                                identification = 'residential'
                            elif building.building_type == 'commercial':
                                identification = 'commercial'
                            else:  # mixed - distribute different types
                                identification = random.choice(['residential', 'commercial'])
                            
                            # Random status with more occupied than vacant
                            status = random.choices(['occupied', 'vacant'], weights=[7, 3])[0]
                            
                            unit = Unit.objects.create(
                                block=tower,
                                number=unit_number,
                                floor=floor,
                                area=random.uniform(50, 200),
                                ideal_fraction=random.uniform(0.5, 2.5),
                                identification=identification,
                                deposit_location=f'Depósito {unit_number}' if random.choice([True, False]) else '',
                                key_delivery=random.choice(['Sim', 'Não']),
                                owner=f'Proprietário {unit_number}',
                                owner_phone=f'(11) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}',
                                parking_spaces=random.randint(0, 2),
                                status=status
                            )
                    
                    self.stdout.write(f'    Created {units_per_tower} units for {tower.name}')
            
            # Create a demo user for testing
            demo_user, created = User.objects.get_or_create(
                email='demo@sindipro.com',
                defaults={
                    'username': 'demo_user',
                    'first_name': 'Demo',
                    'last_name': 'User',
                    'role': 'manager',
                    'is_active': True,
                    'building': created_buildings[0]  # Assign to first building
                }
            )
            
            if created:
                demo_user.set_password('demo123456')
                demo_user.save()
                self.stdout.write(f'Created demo user: {demo_user.email} (password: demo123456)')
            else:
                self.stdout.write(f'Demo user already exists: {demo_user.email}')
            
            # Summary
            self.stdout.write(self.style.SUCCESS(f'\nSuccessfully seeded building data:'))
            self.stdout.write(f'- {len(created_buildings)} buildings created')
            self.stdout.write(f'- {Tower.objects.count()} towers created')
            self.stdout.write(f'- {Unit.objects.count()} units created')
            self.stdout.write(f'- {Address.objects.count()} addresses created')
            self.stdout.write(self.style.SUCCESS('\nYou can now log in with:'))
            self.stdout.write(f'Email: demo@sindipro.com')
            self.stdout.write(f'Password: demo123456')