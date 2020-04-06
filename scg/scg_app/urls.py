from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('clases/', views.ClasesView.as_view(), name='clases_view'),
    path('action_process/', views.action_process, name='action_process'),
    path('gestion_ausencia/<str:ids_clases>', views.gestion_ausencia, name="gestion_ausencia"),
    path('asignar_reemplazo/<str:id_clase>', views.asignar_reemplazo, name="asignar_reemplazo"),
    path('gestion_marcajes/<str:id_empleado>/<str:fecha>', views.gestion_marcajes, name="gestion_marcajes"),

    
	 
    #path('gestionar_reemplazos/', views.gestionar_reemplazos, name='gestionar_reemplazos'),
    #path('agregar_marcaje/', views.agregar_marcaje, name='agregar_marcaje'), 
    #path('filtro/', views.filtros, name='filtro'), 
    #path('monitor/', views.monitor_clases, name='monitor'), 

    path('about/', views.about, name='about'), 
    path('auto_clockings/', views.auto_clockings, name='auto_clockings'), 
	path('modificar_estado/', views.modificar_estado, name='modificar_estado'), 
    
    path('pulls/pulldbs/', views.pulldbs, name='pull_dbs'), 
    path('pulls/pull_clockings/', views.pull_clockings, name='pull_clockings'),
    path('pulls/pull_empleados/', views.pull_empleados, name='pull_empleados'), 
    path('pulls/pull_sedes/', views.pull_sedes, name='pull_sedes'), 
    path('register/', views.register, name='register'), 
    path('programar_clase/', views.programar_clase, name='programar_clase'), 
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) #remover para produccion!
