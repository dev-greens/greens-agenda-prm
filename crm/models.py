from django.db import models
from django.db.models.functions import Lower
from django.conf import settings
from simple_history.models import HistoricalRecords
from django.db.models import Q

class Doctor(models.Model):
    name = models.CharField('Nome', max_length=120)
    crm = models.CharField('CRM', max_length=50, blank=True)
    specialty = models.CharField('Especialidade', max_length=120, blank=True)
    email = models.EmailField('E-mail', blank=True)
    phone = models.CharField('Telefone', max_length=50, blank=True)
    notes = models.TextField('Observações', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name

    uf = models.CharField('UF', max_length=2, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    institutions = models.ManyToManyField('crm.Organization', blank=True, related_name='physicians')
    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['crm','uf'], name='uniq_crm_uf', condition=~Q(crm='')),
            models.UniqueConstraint(Lower('name'), 'crm', name='uniq_doctor_name_crm_ci')
        ]


STATUS_CHOICES = (
    ('agendada','Agendada'),
    ('concluida','Concluída'),
    ('cancelada','Cancelada'),
)
class Appointment(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments', verbose_name='Médico')
    contact_name = models.CharField('Contato (opcional)', max_length=120, blank=True)
    when = models.DateTimeField('Data e Hora')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='agendada')
    notes = models.TextField('Observações', blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    history = HistoricalRecords()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-when']
    def __str__(self):
        return f"{self.doctor.name} - {self.when:%d/%m/%Y %H:%M}"

VISIT_NUMBER_CHOICES = (
    ('1a', '1ª visita'),
    ('2a', '2ª visita'),
    ('3a+', '3ª ou mais'),
)
VISIT_MODE_CHOICES = (
    ('presencial', 'Presencial'),
    ('remoto', 'Remoto'),
)
class VisitReport(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='report', verbose_name='Consulta')
    visit_number = models.CharField('Número da visita', max_length=10, choices=VISIT_NUMBER_CHOICES, default='1a')
    mode = models.CharField('Tipo de visita', max_length=20, choices=VISIT_MODE_CHOICES, default='presencial')
    objective = models.CharField('Objetivo da visita', max_length=200)
    summary = models.TextField('Resumo do encontro', blank=True)
    outcome = models.TextField('Resultados / decisões', blank=True)
    next_steps = models.TextField('Próximos passos', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Relatório - {self.appointment}"



class Organization(models.Model):
    name = models.CharField('Organização', max_length=160, unique=True)
    cnpj = models.CharField('CNPJ', max_length=32, blank=True)
    city = models.CharField('Cidade', max_length=80, blank=True)
    state = models.CharField('UF', max_length=2, blank=True)
    phone = models.CharField('Telefone', max_length=50, blank=True)
    notes = models.TextField('Notas', blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()
    def __str__(self): return self.name
    history = HistoricalRecords()

class Pipeline(models.Model):
    name = models.CharField(max_length=80, unique=True)
    is_default = models.BooleanField(default=False)
    def __str__(self): return self.name

class Stage(models.Model):
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='stages')
    name = models.CharField(max_length=80)
    order = models.PositiveIntegerField(default=0)
    class Meta:
        unique_together = (('pipeline', 'name'),)
        ordering = ('order',)
    def __str__(self): return f"{self.pipeline} • {self.name}"

class Deal(models.Model):
    STATUS = (('open','Aberta'),('won','Ganha'),('lost','Perdida'))
    title = models.CharField('Título', max_length=180)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
    contact = models.ForeignKey('crm.Doctor', null=True, blank=True, on_delete=models.SET_NULL)
    amount = models.DecimalField('Valor', max_digits=12, decimal_places=2, default=0)
    pipeline = models.ForeignKey(Pipeline, on_delete=models.PROTECT)
    stage = models.ForeignKey(Stage, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=STATUS, default='open')
    expected_close = models.DateField('Fechamento previsto', null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()
    history = HistoricalRecords()
    def __str__(self): return self.title


class Representative(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Territory(models.Model):
    name = models.CharField(max_length=80, unique=True)
    region = models.CharField(max_length=80, blank=True)
    def __str__(self):
        return self.name

class Assignment(models.Model):
    physician = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='assignments')
    representative = models.ForeignKey(Representative, on_delete=models.CASCADE, related_name='assignments')
    territory = models.ForeignKey(Territory, on_delete=models.PROTECT)
    active = models.BooleanField(default=True)
    monthly_target = models.PositiveIntegerField(default=1)
    start = models.DateField(auto_now_add=True)
    end = models.DateField(null=True, blank=True)
    class Meta:
        unique_together = ('physician','representative','territory')
