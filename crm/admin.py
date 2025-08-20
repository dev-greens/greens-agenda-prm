from django.contrib import admin
from .models import Doctor, Appointment, VisitReport
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name','crm','specialty')
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('doctor','when','status')
@admin.register(VisitReport)
class VisitReportAdmin(admin.ModelAdmin):
    list_display = ('appointment','visit_number','mode','objective','updated_at')

from .models import Organization, Pipeline, Stage, Deal, Representative
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name','state','owner')
@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('title','status','owner','updated_at')
@admin.register(Representative)
class RepresentativeAdmin(admin.ModelAdmin):
    list_display = ('user',)

from .models import Territory, Assignment
@admin.register(Territory)
class TerritoryAdmin(admin.ModelAdmin):
    list_display = ('name','region')
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('physician','representative','territory','active','monthly_target')
    list_filter = ('active','territory')
    search_fields = ('physician__name','representative__user__username','representative__user__first_name','representative__user__last_name')
