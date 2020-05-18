from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from scg_app import views

list_urls = [
    ### lists ###
    path('empleados/', views.EmpleadosList.as_view(), name='empleados_view'),
    path('saldos/', views.SaldosList.as_view(), name='saldos_view'),
    path('programaciones/', views.RecurrenciasList.as_view(),
        name='programaciones_view'),
    path('motivos_ausencia/', views.MotivosAusenciaList.as_view(),
        name='motivos_ausencia_view'),
    path('periodos/', views.PeriodosList.as_view(), name='periodos_view'),
]

clases_urls = [
    ### clases ###
    path('monitor/', views.ClasesView.as_view(), name='clases_view'),
    path('<int:pk>/edit/', views.clase_edit, name='clase_update'),
    path('action_process/', views.action_process, name='action_process'),
    path('gestion_ausencia/<str:ids_clases>',
        views.gestion_ausencia, name="gestion_ausencia"),
    path('asignar_reemplazo/<str:id_clase>',
        views.asignar_reemplazo, name="asignar_reemplazo"),
    path('gestion_marcajes/<str:id_empleado>/<str:fecha>',
        views.gestion_marcajes, name="gestion_marcajes"),

    ### certificados ###
    path('certificados/<int:id_clase>',
        views.certificados_list, name="certificados_list"),
]

create_urls = [
    ### create ###
    path('programacion/', views.programar, name='programar'),
    path('saldo/', views.generar_saldo, name='generar_saldo'),
    path('periodo/', views.periodo_create, name='periodo_create'),
]

update_urls = [
    ### update ###
    path('programacion/<int:pk>',
        views.programacion_update, name='programacion_update'),
    path('saldo/<int:pk>', views.saldo_update, name='saldo_update'),
    path('periodo/<int:pk>', views.periodo_update, name='periodo_update'),
]

nettime_urls = [
    #nettime operations
    path('get_clockings/', views.get_nt_marcajes, name='get_nt_marcajes'),
    path('get_empleados/',
        views.get_nt_empleados, name='get_nt_empleados'),
    path('get_sedes/', views.get_nt_sedes, name='get_nt_sedes'),
    path('get_motivos_ausencia/',
        views.get_nt_incidencias, name='get_nt_incidencias'),
]

urlpatterns = [
    path('', views.index, name='index'),

    ### clases ###
    path('clases/', include(clases_urls)),

    ### lists ###
    path('list/', include(list_urls)),

    ### create ###
    path('create/', include(create_urls)),

    ### update ###
    path('update/', include(update_urls)),

    #nettime operations
    path('netTime/', include(nettime_urls)),

    ### others ###
    path('wiki/', views.wiki, name='wiki'),
    path('about/', views.about, name='about'),
    path('tasks/', views.tasks_management, name='tasks_management'),

    #delete view
    path('delete/<str:model>/<int:pk>',
        views.confirm_delete, name="confirm_delete"),

    ### messages
    path('message/<str:_type>/', views.show_message, name='show_message'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_URL)
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT)

