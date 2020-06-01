from django.urls import path, include
#from django.conf.urls.static import static
#from django.conf import settings
from . import views

urlpatterns = [
    path('create/', views.help_create, name='help_create'),
    path('list/', views.help_list, name='help_list'),
    path('update/<slug:slug_text>', views.help_update, name='help_update'),
    path('detail/<slug:slug_text>', views.help_detail, name='help_detail'),
    path('print/<slug:slug_text>', views.help_print, name='help_print'),
]
