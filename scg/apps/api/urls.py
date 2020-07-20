from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from apps.api import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'clases', views.ClaseViewSet)
router.register(r'empleados', views.EmpleadoViewSet)
router.register(r'escalas', views.EscalaViewSet)
router.register(r'grupos', views.GrupoViewSet)
router.register(r'tipos-de-liquidacion', views.TipoLiquidacionViewSet)
router.register(r'tipos-de-contrato', views.TipoContratoViewSet)
router.register(r'actividades', views.ActividadViewSet)
router.register(r'motivos-de-ausencia', views.MotivoAusenciaViewSet)
router.register(r'sedes', views.SedeViewSet)
router.register(r'programaciones', views.RecurrenciaViewSet)
router.register(r'saldos', views.SaldoViewSet)
router.register(r'marcajes', views.MarcajeViewSet)
router.register(r'bloques-de-presencia', views.BloqueDePresenciaViewSet)
router.register(r'certificados', views.CertificadoViewSet)
router.register(r'periodos', views.PeriodoViewSet)
router.register(r'comentarios', views.ComentarioViewSet)

get_urls = [ 
	path('empleados/<str:_filter>/', views.get_empleados, name='get_empleados'),
	path(
		'actividades/<str:_filter>/', views.get_actividades,
		name='get_actividades'),
	path('sedes/<str:_filter>/', views.get_sedes, name='get_sedes'),
	path('lugares/<str:_filter>/', views.get_lugares, name='get_lugares'),
	path('day_classes/', views.get_day_classes, name='get_day_classes'),
	path(
		'clases_from_certificado/<int:certificado_id>/',
		views.get_clases_from_certificado, name='clases_from_certificado'),
	path('comment/<int:comment>',views.get_comment_data, name='get_comment'),
	path('current-version/', views.get_current_version, name='current_version'),

	path('months-chart/', views.get_months_chart, name='get_months_chart'),
]

urlpatterns = [
	path('get/', include(get_urls)),
	path('v2.0/', include(router.urls)),
	
]

