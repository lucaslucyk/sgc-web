"""scg URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

#from scg_app.views import EmployeeAutocomplete

admin.site.site_title = 'SCG'
admin.site.site_header = 'SCG APP'

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('select2/', include('django_select2.urls')),

    #for custom api functions
    path('api/', include('api.urls')),

    path('', include('scg_app.urls')),
    
    path('accounts/', include('django.contrib.auth.urls'))
]
