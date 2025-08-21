from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.utils import timezone
from django.db.models.functions import TruncMonth
from django.db.models import Count
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_datetime
from django.template.loader import render_to_string
from datetime import timedelta, datetime

from .models import Doctor, Appointment, STATUS_CHOICES, VisitReport
from .forms import DoctorForm, AppointmentForm, VisitReportForm
from .utils import append_visit_to_excel
from .google_calendar import add_event_to_google_calendar

def _is_manager(user):
    # Admin ou membro do grupo Gestor pode ver/editar tudo
    return user.is_superuser or user.groups.filter(name__in=["Admin", "Gestor"]).exists()

def _parse_iso_safe(s):
    """
    Aceita 'YYYY-MM-DDTHH:MM:SS' (naive) e ISO com offset (ex.: ...-03:00).
    Retorna datetime *aware* na timezone atual do Django.
    """
    dt = None
    try:
        dt = datetime.fromisoformat(s)  # aceita com/sem offset
    except ValueError:
        try:
            dt = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")  # naive
        except ValueError:
            return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    # normaliza para tz atual
    return timezone.localtime(dt, timezone.get_current_timezone())

def _scope_by_owner(qs, user):
    # Representante só enxerga o que é dele
    return qs if _is_manager(user) else qs.filter(owner=user)


STATUS_MAP = dict(STATUS_CHOICES)
STATUS_COLORS = {
    'agendada': {'bg': '#0d6efd', 'bd': '#0b5ed7'},
    'concluida': {'bg': '#198754', 'bd': '#157347'},
    'cancelada': {'bg': '#dc3545', 'bd': '#c82333'},
}

def _get_rep(request):
    try:
        rep, _ = Representative.objects.get_or_create(user=request.user)
        return rep
    except Exception:
        return None


def _apply_filters(qs, request):
    doctor_id = request.GET.get('medico') or request.GET.get('doctor')
    status = request.GET.get('status')
    if doctor_id:
        qs = qs.filter(doctor_id=doctor_id)
    if status in STATUS_MAP:
        qs = qs.filter(status=status)
    return qs

def _parse_iso(value):
    if not value:
        return None
    value = value.replace('Z', '+00:00')
    dt = parse_datetime(value)
    if dt is None:
        try:
            dt = datetime.fromisoformat(value)
        except Exception:
            return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt

# Dashboard
@login_required
def dashboard(request):
    ctx = {}
    # KPIs básicos existentes continuam
    # KPIs de cobertura (últimos 30 dias)
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=30)
    if request.user.is_superuser:
        assigned_doctors = Doctor.objects.all().distinct()
        visits_30d = Appointment.objects.filter(when__gte=cutoff).count()
        visited_doctors = Doctor.objects.filter(appointments__when__gte=cutoff).distinct()
    else:
        rep = _get_rep(request)
        if rep:
            assigned_doctors = Doctor.objects.filter(assignments__representative=rep, assignments__active=True).distinct()
            visits_30d = Appointment.objects.filter(doctor__in=assigned_doctors, when__gte=cutoff).count()
            visited_doctors = assigned_doctors.filter(appointments__when__gte=cutoff).distinct()
        else:
            assigned_doctors = Doctor.objects.filter(owner=request.user)
            visits_30d = Appointment.objects.filter(owner=request.user, when__gte=cutoff).count()
            visited_doctors = assigned_doctors.filter(appointments__when__gte=cutoff).distinct()
    a = assigned_doctors.count() or 1
    v = visited_doctors.count()
    coverage_pct = round(100 * v / a, 1)
    ctx.update({
        'kpi_assigned': a,
        'kpi_visited': v,
        'kpi_coverage_pct': coverage_pct,
        'kpi_visits_30d': visits_30d,
    })
    return render(request, 'dashboard.html', ctx)

# Agenda
@login_required
def agenda(request):
    ctx = {
        'doctors': Doctor.objects.all().order_by('name'),
        'selected_doctor': int(request.GET.get('medico') or 0) if request.GET.get('medico') else None,
        'selected_status': request.GET.get('status') or '',
    }
    return render(request, 'agenda.html', ctx)


# --- CRM basic views ---
from .models import Organization, Pipeline, Stage, Deal, Representative, Assignment, Territory

@login_required
def org_list(request):
    qs = Organization.objects.order_by('name')
    if not request.user.is_superuser:
        qs = qs.filter(owner=request.user)
    orgs = qs
    return render(request, 'crm/org_list.html', {'orgs': orgs})

@login_required
def org_create(request):
    if request.method == 'POST':
        Organization.objects.create(
            name=request.POST.get('name','').strip(),
            cnpj=request.POST.get('cnpj','').strip(),
            city=request.POST.get('city','').strip(),
            state=request.POST.get('state','').strip(),
            phone=request.POST.get('phone','').strip(),
            owner=request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        )
        return redirect('org_list')
    return render(request, 'crm/org_form.html')

@login_required
def deal_list(request):
    deals = Deal.objects.select_related('organization','contact','stage').order_by('-updated_at')
    if not request.user.is_superuser:
        deals = deals.filter(owner=request.user)
    return render(request, 'crm/deal_list.html', {'deals': deals})

@login_required
def deal_kanban(request):
    pipe = Pipeline.objects.filter(is_default=True).first() or Pipeline.objects.first()
    if not pipe:
        # seed minimal pipeline if none
        pipe = Pipeline.objects.create(name='Padrão', is_default=True)
        Stage.objects.bulk_create([
            Stage(pipeline=pipe, name='Prospecção', order=1),
            Stage(pipeline=pipe, name='Qualificação', order=2),
            Stage(pipeline=pipe, name='Proposta', order=3),
            Stage(pipeline=pipe, name='Fechamento', order=4),
        ])
    stages = Stage.objects.filter(pipeline=pipe).prefetch_related('deal_set')
    return render(request, 'crm/kanban.html', {'pipeline': pipe, 'stages': stages})

@login_required
def api_deals(request):
    pipe_id = request.GET.get('pipeline')
    qs = Deal.objects.select_related('organization','contact','stage','pipeline')
    if not request.user.is_superuser:
        qs = qs.filter(owner=request.user)
    if pipe_id: qs = qs.filter(pipeline_id=pipe_id)
    payload = [{
        'id': d.id, 'title': d.title, 'amount': float(d.amount),
        'org': d.organization.name if d.organization else '',
        'contact': d.contact.name if d.contact else '',
        'stage_id': d.stage_id, 'status': d.status,
    } for d in qs]
    return JsonResponse(payload, safe=False)

@require_POST
@login_required
def api_deal_move(request):
    try:
        d = Deal.objects.get(pk=int(request.POST['id']))
        stage_id = int(request.POST['stage_id'])
        st = Stage.objects.get(pk=stage_id)
        if d.pipeline_id != st.pipeline_id:
            return HttpResponseBadRequest('stage/pipeline mismatch')
        d.stage = st
        d.save(update_fields=['stage'])
        return JsonResponse({'ok': True})
    except Exception:
        return HttpResponseBadRequest('invalid')

# Contatos
@login_required
def contacts(request):
    qs = Doctor.objects.order_by('-created_at')
    if not request.user.is_superuser:
        rep = _get_rep(request)
        if rep:
            qs = qs.filter(assignments__representative=rep, assignments__active=True).distinct()
        else:
            qs = qs.filter(owner=request.user)
    doctors = qs
    form = DoctorForm()
    return render(request, 'contacts.html', {'doctors': doctors, 'form': form})

@require_POST
@login_required
def contact_create(request):
    form = DoctorForm(request.POST)
    if form.is_valid():
        form.save(request=request)
    return redirect('contacts')

@login_required
def contact_update(request, pk):
    doc = get_object_or_404(Doctor, pk=pk)
    if not request.user.is_superuser and doc.owner_id and doc.owner_id != request.user.id:
        return redirect('contacts')
    if request.method == 'POST':
        form = DoctorForm(request.POST, instance=doc)
        if form.is_valid():
            form.save()
            return redirect('contacts')
    else:
        form = DoctorForm(instance=doc)
    return render(request, 'contact_edit.html', {'form': form, 'doc': doc})

@require_POST
@login_required
def contact_delete(request, pk):
    doc = get_object_or_404(Doctor, pk=pk)
    if request.user.is_superuser or not doc.owner_id or doc.owner_id == request.user.id:
        doc.delete()
    return redirect('contacts')

# Consultas
@login_required
def appointments(request):
    appts = Appointment.objects.select_related('doctor').all()
    form = AppointmentForm(request=request)
    return render(request, 'appointments.html', {'appointments': appts, 'form': form})

@require_POST
@login_required
def appointment_create(request):
    form = AppointmentForm(request.POST, request=request)
    if form.is_valid():
        appt = form.save(commit=False)
        appt.owner = request.user
        appt.save()
        append_visit_to_excel({
            'Medico': appt.doctor.name, 'CRM': appt.doctor.crm,
            'Especialidade': appt.doctor.specialty, 'Contato': appt.contact_name,
            'DataHora': appt.when, 'Status': appt.status, 'Observacoes': appt.notes
        })
        start_dt = appt.when; end_dt = start_dt + timedelta(minutes=30)
        add_event_to_google_calendar(f'Visita: {appt.doctor.name}', start_dt, end_dt, appt.notes or '')
    return redirect('appointments')

@login_required
def appointment_update(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appt, request=request)
        if form.is_valid():
            form.save()
            return redirect('appointments')
    else:
        form = AppointmentForm(instance=appt, request=request)
    return render(request, 'appointment_edit.html', {'form': form, 'appt': appt})

@require_POST
@login_required
def appointment_delete(request, pk):
    get_object_or_404(Appointment, pk=pk).delete()
    return redirect('appointments')

# Calendar APIs
@login_required
def api_events(request):
    qs = _apply_filters(Appointment.objects.select_related('doctor'), request)
    qs = _scope_by_owner(qs, request.user)
    events = []
    tz = timezone.get_current_timezone()
    for a in qs:
        col = STATUS_COLORS.get(a.status, {'bg': '#6c757d', 'bd': '#6c757d'})
        start = timezone.localtime(a.when, tz)
        end = start + timedelta(minutes=30)
        # render naive strings (no offset) to avoid shifts in client
        start_s = start.strftime('%Y-%m-%dT%H:%M:%S')
        end_s = end.strftime('%Y-%m-%dT%H:%M:%S')
        events.append({
            'id': a.id,
            'title': f"{a.doctor.name}",
            'start': start_s,
            'end': end_s,
            'status': a.status,
            'doctor_id': a.doctor_id,
            'notes': a.notes or '',
            'backgroundColor': col['bg'],
            'borderColor': col['bd'],
        })
    return JsonResponse(events, safe=False)

@require_POST
@login_required
def api_events_create(request):
    when = _parse_iso(request.POST.get('start'))
    if when is None:
        return HttpResponseBadRequest('invalid start')
    appt = Appointment.objects.create(owner=request.user, 
        doctor_id=int(request.POST.get('doctor')),
        when=when,
        status=request.POST.get('status') or 'agendada',
        contact_name=request.POST.get('contact_name', ''),
        notes=request.POST.get('notes', '')
    )
    return JsonResponse({'ok': True, 'id': appt.id})

@require_POST
@login_required
def api_events_update(request):
    appt_id = request.POST.get('id')
    if not appt_id:
        return HttpResponseBadRequest('missing id')

    # 1) carrega o registro
    try:
        appt = Appointment.objects.select_related('doctor').get(pk=int(appt_id))
    except Exception:
        return HttpResponseBadRequest('invalid id')

    # 2) 🔐 PERMISSÃO: checa o dono ANTES de validar/alterar campos
    if not _is_manager(request.user) and getattr(appt, 'owner_id', None) != request.user.id:
        return HttpResponseForbidden('not allowed')

    # 3) atualizações
    if request.POST.get('start'):
        when = _parse_iso_safe(request.POST['start'])
        if when is None:
            return HttpResponseBadRequest('invalid start')
        appt.when = when

    status = request.POST.get('status')
    if status in STATUS_MAP:
        appt.status = status

    if 'notes' in request.POST:
        appt.notes = request.POST.get('notes', '')

    appt.save()
    return JsonResponse({'ok': True})

@require_POST
@login_required
def api_events_delete(request):
    appt_id = request.POST.get('id')
    if not appt_id:
        return HttpResponseBadRequest('missing id')

    try:
        appt = Appointment.objects.select_related('doctor').get(pk=int(appt_id))
    except Exception:
        return HttpResponseBadRequest('invalid id')

    # 🔐 Permissão: representante só pode apagar o que É DELE
    if not _is_manager(request.user) and getattr(appt, 'owner_id', None) != request.user.id:
        return HttpResponseForbidden('not allowed')

    appt.delete()
    return JsonResponse({'ok': True})



@login_required
def api_alerts(request):
    """Retorna eventos 'agendada' nas próximas 72h, marca 'urgent' se < 24h."""
    now = timezone.now()
    soon = now + timedelta(hours=72)
    tz = timezone.get_current_timezone()
    qs = (Appointment.objects
            .select_related('doctor')
            .filter(status='agendada', when__gte=now, when__lte=soon)
            .order_by('when')[:20])
    alerts = []
    for a in qs:
        delta = a.when - now
        urgency = 'urgent' if delta.total_seconds() <= 24*3600 else 'soon'
        when_str = timezone.localtime(a.when, tz).strftime('%d/%m %H:%M')
        alerts.append({
            'id': a.id,
            'doctor': a.doctor.name,
            'when': when_str,
            'urgency': urgency,
            'message': f"Visita com {a.doctor.name} • {when_str}",
        })
    return JsonResponse({'count': len(alerts), 'alerts': alerts})
# Relatórios
@login_required
def report_list(request):
    items = Appointment.objects.select_related('doctor').order_by('-when')
    return render(request, 'relatorios/list.html', {'items': items})

@login_required
def report_create(request, appointment_id):
    appt = get_object_or_404(Appointment, pk=appointment_id)
    if hasattr(appt, 'report'):
        return redirect('report_update', pk=appt.report.id)
    if request.method == 'POST':
        form = VisitReportForm(request.POST)
        if form.is_valid():
            rep = form.save(commit=False)
            rep.appointment = appt
            rep.save()
            return redirect('report_list')
    else:
        form = VisitReportForm()
    return render(request, 'relatorios/form.html', {'form': form, 'appt': appt})

@login_required
def report_update(request, pk):
    rep = get_object_or_404(VisitReport, pk=pk)
    if request.method == 'POST':
        form = VisitReportForm(request.POST, instance=rep)
        if form.is_valid():
            form.save()
            return redirect('report_list')
    else:
        form = VisitReportForm(instance=rep)
    return render(request, 'relatorios/form.html', {'form': form, 'appt': rep.appointment, 'rep': rep})

@login_required
def report_pdf(request, pk):
    from xhtml2pdf import pisa
    rep = get_object_or_404(VisitReport, pk=pk)
    html = render_to_string('relatorios/pdf.html', {'rep': rep})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=relatorio-{rep.pk}.pdf'
    pisa.CreatePDF(src=html, dest=response)
    return response
