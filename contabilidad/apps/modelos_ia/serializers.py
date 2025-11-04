# contabilidad/apps/modelos_ia/serializers.py

from rest_framework import serializers

class PredecirAsientoSerializer(serializers.Serializer):
    descripcion = serializers.CharField(
        max_length=255, 
        help_text="Descripción en lenguaje natural del asiento contable."
    )