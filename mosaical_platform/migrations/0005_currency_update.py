
# Generated migration for currency update

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('mosaical_platform', '0004_performancemetric'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userprofile',
            old_name='vbtc_balance',
            new_name='dpsv_balance',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='vnst_balance',
            field=models.DecimalField(decimal_places=8, default=0, max_digits=20),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='preferred_currency',
            field=models.CharField(choices=[('DPSV', 'DPSV'), ('VNST', 'VNST')], default='DPSV', max_length=10),
        ),
    ]
