from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from api import views

get_urls = [
	path('empleados/<str:_filter>/', views.get_empleados, name='get_empleados'),
	path('actividades/<str:_filter>/', views.get_actividades, name='get_actividades'),
	path('sedes/<str:_filter>/', views.get_sedes, name='get_sedes'),
	path('day_classes/', views.get_day_classes, name='get_day_classes'),
]

urlpatterns = [
	path('get/', include(get_urls)),
]