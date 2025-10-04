# Fix installation_date field issue

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipment_mgmt', '0002_update_equipment_structure'),
    ]

    operations = [
        # Make installation_date nullable and set default from purchase_date
        migrations.AlterField(
            model_name='equipment',
            name='installation_date',
            field=models.DateField(null=True, blank=True),
        ),
    ]