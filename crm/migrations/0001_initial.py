from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Doctor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, verbose_name='Nome')),
                ('crm', models.CharField(blank=True, max_length=50, verbose_name='CRM')),
                ('specialty', models.CharField(blank=True, max_length=120, verbose_name='Especialidade')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='E-mail')),
                ('phone', models.CharField(blank=True, max_length=50, verbose_name='Telefone')),
                ('notes', models.TextField(blank=True, verbose_name='Observações')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contact_name', models.CharField(blank=True, max_length=120, verbose_name='Contato (opcional)')),
                ('when', models.DateTimeField(verbose_name='Data e Hora')),
                ('status', models.CharField(choices=[('agendada', 'Agendada'), ('concluida', 'Concluída'), ('cancelada', 'Cancelada')], default='agendada', max_length=20, verbose_name='Status')),
                ('notes', models.TextField(blank=True, verbose_name='Observações')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='crm.doctor', verbose_name='Médico')),
            ],
            options={'ordering': ['-when']},
        ),
        migrations.CreateModel(
            name='VisitReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('visit_number', models.CharField(choices=[('1a', '1ª visita'), ('2a', '2ª visita'), ('3a+', '3ª ou mais')], default='1a', max_length=10, verbose_name='Número da visita')),
                ('mode', models.CharField(choices=[('presencial', 'Presencial'), ('remoto', 'Remoto')], default='presencial', max_length=20, verbose_name='Tipo de visita')),
                ('objective', models.CharField(max_length=200, verbose_name='Objetivo da visita')),
                ('summary', models.TextField(blank=True, verbose_name='Resumo do encontro')),
                ('outcome', models.TextField(blank=True, verbose_name='Resultados / decisões')),
                ('next_steps', models.TextField(blank=True, verbose_name='Próximos passos')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('appointment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='report', to='crm.appointment', verbose_name='Consulta')),
            ],
        ),
    ]
