# contabilidad/apps/modelos_ia/urls.py

from django.urls import path
from .views import PredecirAsientoAPIView

urlpatterns = [
    path('ia/asiento-predict/', PredecirAsientoAPIView.as_view(), name='ia-asiento-predecir'),
]