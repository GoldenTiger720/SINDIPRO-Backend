# Generated by Django 5.2.4 on 2025-07-28 17:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('building_mgmt', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ConsumptionType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('water', 'Water'), ('electricity', 'Electricity'), ('gas', 'Gas')], max_length=20, unique=True)),
                ('unit', models.CharField(max_length=10)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ConsumptionReading',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period', models.CharField(choices=[('daily', 'Daily'), ('monthly', 'Monthly')], max_length=10)),
                ('reading_date', models.DateField()),
                ('consumption_value', models.DecimalField(decimal_places=2, max_digits=10)),
                ('cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('notes', models.TextField(blank=True)),
                ('previous_month_consumption', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('percentage_change', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('building', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consumption_readings', to='building_mgmt.building')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('consumption_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='consumptions.consumptiontype')),
            ],
            options={
                'ordering': ['-reading_date'],
                'unique_together': {('building', 'consumption_type', 'period', 'reading_date')},
            },
        ),
    ]
