from django.urls import path, include
#from django.conf.urls.static import static
#from django.conf import settings
from . import views

urlpatterns = [
    path('create/', views.help_create, name='help_create'),
    path('update/<int:pk>', views.help_update, name='help_update'),
    path('detail/<int:pk>', views.help_detail, name='help_detail'),
]
