"""
URL configuration for libreria_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.conf import settings # <<< Importar settings
from django.conf.urls.static import static # <<< Importar static

urlpatterns = [
    # URL de administración
    path('admin/', admin.site.urls),
    
    # URL del Catálogo (Punto de Venta)
    # Esto le dice a Django que envíe todas las solicitudes que no sean '/admin/' 
    # a las URLs definidas en inventario_ventas/urls.py
    path('', include('inventario_ventas.urls')), 
]

# Solo sirve archivos media si estamos en DEBUG mode (producción usa un servidor web)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

