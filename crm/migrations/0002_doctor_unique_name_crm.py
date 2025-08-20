from django.db import migrations, models
import django.db.models.functions.text

class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0001_initial'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='doctor',
            constraint=models.UniqueConstraint(django.db.models.functions.text.Lower('name'), 'crm', name='uniq_doctor_name_crm_ci'),
        ),
    ]
