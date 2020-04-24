from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from scg_app import views

urlpatterns = [
    path('', views.index, name='index'),

    path('delete/<str:model>/<int:pk>', views.confirm_delete, name="confirm_delete"),

    ### clases ###
    path('clases/', views.ClasesView.as_view(), name='clases_view'),
    path('clase/<int:pk>/edit/', views.clase_edit, name='clase_update'),
    path('action_process/', views.action_process, name='action_process'),
    path('gestion_ausencia/<str:ids_clases>', views.gestion_ausencia, name="gestion_ausencia"),
    path('asignar_reemplazo/<str:id_clase>', views.asignar_reemplazo, name="asignar_reemplazo"),
    path('gestion_marcajes/<str:id_empleado>/<str:fecha>', views.gestion_marcajes, name="gestion_marcajes"),

    ### certificados ###
    path('certificados/<int:id_clase>', views.certificados_list, name="certificados_list"),

    ### lists ###
    path('list/empleados/', views.EmpleadosList.as_view(), name='empleados_view'),
    path('list/saldos/', views.SaldosList.as_view(), name='saldos_view'),
    path('list/programaciones/', views.RecurrenciasList.as_view(), name='programaciones_view'),
    path('list/motivos_ausencia/', views.MotivosAusenciaList.as_view(), name='motivos_ausencia_view'),

    ### create ###
    path('create/programacion/', views.programar, name='programar'),
    path('create/saldo/', views.generar_saldo, name='generar_saldo'),

    ### update ###
    path('update/programacion/<int:pk>', views.programacion_update, name='programacion_update'),
    path('update/saldo/<int:pk>', views.saldo_update, name='saldo_update'),

    ### others ###
    path('wiki/', views.wiki, name='wiki'),
    path('register/', views.register, name='register'), 

    path('about/', views.about, name='about'), 
    path('auto_clockings/', views.auto_clockings, name='auto_clockings'), 
    
    #nettime operations
    path('pulls/pulldbs/', views.pulldbs, name='pull_dbs'), 
    path('pulls/pull_clockings/', views.pull_clockings, name='pull_clockings'),
    path('netTime/pull/empleados/', views.get_nt_empleados, name='get_nt_empleados'), 
    path('pulls/pull_sedes/', views.get_nt_sedes, name='get_nt_sedes'), 

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)