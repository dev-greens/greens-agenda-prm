from django.contrib import admin
from django.http import HttpResponseForbidden
from django.contrib.auth.models import Group

from .models import (
    Doctor,
    Appointment,
    VisitReport,
    Organization,
    Pipeline,
    Stage,
    Deal,
    Representative,
    Territory,
    Assignment,
)

# -----------------------------
# Helpers de RBAC (Admin/Gestor vs Representante)
# -----------------------------
def _is_manager(user):
    """Admin ou membro do grupo 'Gestor' têm visão total."""
    return user.is_superuser or user.groups.filter(name__in=["Admin", "Gestor"]).exists()

from django.contrib.auth import get_user_model
User = get_user_model()

class OwnableAdmin(admin.ModelAdmin):
    """
    - Admin/Gestor: visão total e podem escolher 'owner'.
    - Demais usuários: só veem o que é deles e o 'owner' fica travado no próprio usuário.
    """
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if _is_manager(request.user):
            return qs
        # filtra por owner quando existir; visitreport herda do appointment
        field_names = {f.name for f in self.model._meta.fields}
        if "owner" in field_names:
            return qs.filter(owner=request.user)
        if self.model.__name__ == "VisitReport":
            return qs.filter(appointment__owner=request.user)
        return qs.none()

    def get_form(self, request, obj=None, **kwargs):
        """
        Travar o campo 'owner' para não-gestores:
        - no 'add': já vem com o próprio usuário e não deixa trocar
        - no 'change': mostra, mas desabilitado
        """
        form = super().get_form(request, obj, **kwargs)
        if "owner" in form.base_fields:
            if _is_manager(request.user):
                # gestor/admin veem todos os usuários
                form.base_fields["owner"].queryset = User.objects.all()
            else:
                # representante: fixa no próprio usuário
                form.base_fields["owner"].initial = request.user
                form.base_fields["owner"].queryset = User.objects.filter(pk=request.user.pk)
                form.base_fields["owner"].disabled = True
        return form

    def get_readonly_fields(self, request, obj=None):
        """
        Em edição, deixa 'owner' somente leitura para não-gestores.
        """
        ro = list(super().get_readonly_fields(request, obj))
        if not _is_manager(request.user) and obj is not None and hasattr(self.model, "owner"):
            ro.append("owner")
        return ro

    def save_model(self, request, obj, form, change):
        """
        Garante que o owner correto será gravado mesmo se houver tentativa de burla.
        """
        if hasattr(obj, "owner"):
            if not _is_manager(request.user):
                # força o owner do rep SEMPRE
                obj.owner = request.user
            elif not change and not getattr(obj, "owner_id", None):
                # em criação por gestor/admin, se vazio, usa quem criou
                obj.owner = request.user
        super().save_model(request, obj, form, change)
    
    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if not _is_manager(request.user) and obj is None and "owner" in fields:
            fields.remove("owner")
        return fields
    


# -----------------------------
# Admins
# -----------------------------
@admin.register(Doctor)
class DoctorAdmin(OwnableAdmin):
    # Alguns projetos usam campos com nomes levemente diferentes;
    # criamos "callables" para evitar quebrar se houver variação.
    def crm_display(self, obj):
        for attr in ("crm", "crm_code", "crm_number"):
            if hasattr(obj, attr):
                return getattr(obj, attr)
        return ""

    def specialty_display(self, obj):
        for attr in ("specialty", "speciality", "specialization"):
            if hasattr(obj, attr):
                return getattr(obj, attr)
        return ""

    list_display = ("name", "crm_display", "specialty_display", "owner")
    search_fields = ("name", "owner__username")
    list_filter = ("owner",)
    ordering = ("name",)
    crm_display.short_description = "CRM"
    specialty_display.short_description = "Especialidade"


@admin.register(Appointment)
class AppointmentAdmin(OwnableAdmin):
    def when_display(self, obj):
        # Alguns repositórios usam 'when', outros 'scheduled_at'
        return getattr(obj, "when", getattr(obj, "scheduled_at", None))

    list_display = ("doctor", "when_display", "status", "owner")
    list_filter = ("status", "owner")
    search_fields = ("doctor__name", "owner__username")
    ordering = ("-id",)
    when_display.short_description = "Quando"


@admin.register(VisitReport)
class VisitReportAdmin(OwnableAdmin):
    # VisitReport não tem 'owner' direto; o filtro é feito via appointment.owner
    list_display = ("appointment", "visit_number", "mode", "objective", "updated_at")
    search_fields = ("appointment__doctor__name", "objective")
    ordering = ("-updated_at",)


@admin.register(Organization)
class OrganizationAdmin(OwnableAdmin):
    def state_display(self, obj):
        for attr in ("state", "uf", "region"):
            if hasattr(obj, attr):
                return getattr(obj, attr)
        return ""

    list_display = ("name", "state_display", "owner")
    search_fields = ("name", "owner__username")
    list_filter = ("owner",)
    ordering = ("name",)
    state_display.short_description = "UF/Região"


@admin.register(Deal)
class DealAdmin(OwnableAdmin):
    list_display = ("title", "status", "owner", "updated_at")
    list_filter = ("status", "owner")
    search_fields = ("title", "owner__username")
    ordering = ("-updated_at", "-id")


# Modelos que normalmente não têm 'owner' direto:
@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active_display")
    ordering = ("name",)

    def is_active_display(self, obj):
        # suporta 'active', 'is_active' ou False caso não exista
        return getattr(obj, "is_active", getattr(obj, "active", False))

    is_active_display.boolean = True
    is_active_display.short_description = "Ativo"


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    def order_display(self, obj):
        # suporta 'order' ou 'position'
        return getattr(obj, "order", getattr(obj, "position", None))

    list_display = ("name", "pipeline", "order_display")
    list_filter = ("pipeline",)
    search_fields = ("name", "pipeline__name")
    ordering = ("pipeline__name", "name")
    order_display.short_description = "Ordem"


@admin.register(Representative)
class RepresentativeAdmin(admin.ModelAdmin):
    list_display = ("user",)
    search_fields = ("user__username", "user__first_name", "user__last_name")
    ordering = ("user__username",)


@admin.register(Territory)
class TerritoryAdmin(admin.ModelAdmin):
    def region_display(self, obj):
        for attr in ("region", "state", "uf", "name"):
            if hasattr(obj, attr):
                return getattr(obj, attr)
        return ""

    list_display = ("name", "region_display")
    search_fields = ("name",)
    ordering = ("name",)
    region_display.short_description = "Região/UF"


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    def physician_display(self, obj):
        # suporta 'physician' ou 'doctor'
        return getattr(obj, "physician", getattr(obj, "doctor", None))

    list_display = (
        "physician_display",
        "representative",
        "territory",
        "active",
        "monthly_target",
    )
    list_filter = ("active", "territory")
    search_fields = (
        "physician__name",
        "doctor__name",
        "representative__user__username",
        "representative__user__first_name",
        "representative__user__last_name",
    )
    ordering = ("-active", "territory__name", "representative__user__username")
    physician_display.short_description = "Médico"
