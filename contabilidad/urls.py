"""
URL configuration for contabilidad project.

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
from django.urls import path ,include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Apps del proyecto
    path('', include('contabilidad.apps.gestion_cuenta.urls')),
    path('', include('contabilidad.apps.gestion_asiento.urls')),
    path('', include('contabilidad.apps.usuario.urls')),
    path('', include('contabilidad.apps.empresa.urls')),
    path('', include('contabilidad.apps.reporte.urls')),
    path('',include('contabilidad.apps.suscripcion.urls')),
    path('', include('contabilidad.apps.ia_reporte.urls')),
    path('', include('contabilidad.apps.modelos_ia.urls')),
    # Also expose usuario app under the legacy API prefix used by the frontend
    path('api/', include('contabilidad.apps.usuario.urls')),

    # 🔹 Rutas de documentación automática
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

]
