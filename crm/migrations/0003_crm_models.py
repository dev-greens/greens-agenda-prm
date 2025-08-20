from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0002_doctor_unique_name_crm'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=160, unique=True, verbose_name='Organização')),
                ('cnpj', models.CharField(blank=True, max_length=32, verbose_name='CNPJ')),
                ('city', models.CharField(blank=True, max_length=80, verbose_name='Cidade')),
                ('state', models.CharField(blank=True, max_length=2, verbose_name='UF')),
                ('phone', models.CharField(blank=True, max_length=50, verbose_name='Telefone')),
                ('notes', models.TextField(blank=True, verbose_name='Notas')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Pipeline',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, unique=True)),
                ('is_default', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Stage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80)),
                ('order', models.PositiveIntegerField(default=0)),
                ('pipeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stages', to='crm.pipeline')),
            ],
            options={'ordering': ('order',)},
        ),
        migrations.AlterUniqueTogether(
            name='stage',
            unique_together={('pipeline', 'name')},
        ),
        migrations.CreateModel(
            name='Deal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=180, verbose_name='Título')),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Valor')),
                ('status', models.CharField(choices=[('open', 'Aberta'), ('won', 'Ganha'), ('lost', 'Perdida')], default='open', max_length=10)),
                ('expected_close', models.DateField(blank=True, null=True, verbose_name='Fechamento previsto')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('contact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='crm.doctor')),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='crm.organization')),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('pipeline', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='crm.pipeline')),
                ('stage', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='crm.stage')),
            ],
        ),
    ]
