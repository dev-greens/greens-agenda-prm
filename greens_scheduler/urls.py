from django.http import JsonResponse
from django.contrib import admin
from django.urls import path, include
from crm import views

def health(request):
    return JsonResponse({"ok": True})

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),

    path('admin/', admin.site.urls),

    path('', views.dashboard, name='dashboard'),
    path('agenda/', views.agenda, name='agenda'),

    path('contatos/', views.contacts, name='contacts'),
    path('contatos/novo/', views.contact_create, name='contact_create'),
    path('contatos/<int:pk>/editar/', views.contact_update, name='contact_update'),
    path('contatos/<int:pk>/excluir/', views.contact_delete, name='contact_delete'),

    path('consultas/', views.appointments, name='appointments'),
    path('consultas/nova/', views.appointment_create, name='appointment_create'),
    path('consultas/<int:pk>/editar/', views.appointment_update, name='appointment_update'),
    path('consultas/<int:pk>/excluir/', views.appointment_delete, name='appointment_delete'),

    # Calendar APIs
    path('api/events/', views.api_events, name='api_events'),
    path('api/events/create', views.api_events_create, name='api_events_create'),
    path('api/events/update', views.api_events_update, name='api_events_update'),
    path('api/events/delete', views.api_events_delete, name='api_events_delete'),

    path('api/alerts/', views.api_alerts, name='api_alerts'),

    # Relatórios
    path('relatorios/', views.report_list, name='report_list'),
    path('relatorios/novo/<int:appointment_id>/', views.report_create, name='report_create'),
    path('relatorios/<int:pk>/editar/', views.report_update, name='report_update'),
    path('relatorios/<int:pk>/pdf/', views.report_pdf, name='report_pdf'),
    path('crm/contas/', views.org_list, name='org_list'),
    path('crm/contas/nova/', views.org_create, name='org_create'),
    path('crm/deals/', views.deal_list, name='deal_list'),
    path('crm/kanban/', views.deal_kanban, name='deal_kanban'),
    path('api/deals/', views.api_deals, name='api_deals'),
    path('api/deals/move', views.api_deal_move, name='api_deal_move'),

    path("health/", health, name="health"),

]
