from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from . import views

urlpatterns = [
    path('', views.index, name='index'), 
    path('about/', views.about, name='about'), 
    path('agregar_marcaje/', views.agregar_marcaje, name='agregar_marcaje'), 
    path('auto_clockings/', views.auto_clockings, name='auto_clockings'), 
	path('gestionar_ausencias/', views.gestionar_ausencias, name='gestionar_ausencias'), 
	path('gestionar_recurrencias/', views.gestionar_recurrencias, name='gestionar_recurrencias'), 
    path('gestionar_reemplazos/', views.gestionar_reemplazos, name='gestionar_reemplazos'), 
    path('filtro/', views.filtros, name='filtro'), 
	path('modificar_estado/', views.modificar_estado, name='modificar_estado'), 
    path('monitor/', views.monitor_clases, name='monitor'), 
    path('pulls/pulldbs/', views.pulldbs, name='pull_dbs'), 
    path('pulls/pull_clockings/', views.pull_clockings, name='pull_clockings'),
    path('pulls/pull_empleados/', views.pull_empleados, name='pull_empleados'), 
    path('pulls/pull_sedes/', views.pull_sedes, name='pull_sedes'), 
    path('register/', views.register, name='register'), 
    path('programar_clase/', views.programar_clase, name='programar_clase'), 
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) #remover para produccion!
