# contabilidad/apps/modelos_ia/views.py
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
# ... (importaciones de views.py de la sección 3.B anterior) ...
from .services import IAModelService
from .serializers import PredecirAsientoSerializer

class PredecirAsientoAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PredecirAsientoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        texto_usuario = serializer.validated_data['descripcion']
        
        try:
            servicio = IAModelService()
            resultado = servicio.predecir_asiento(texto_usuario)
            
            if resultado['success']:
                # Convertimos Decimal a string para el JSON
                resultado['monto'] = str(resultado['monto']) 
                return Response(resultado, status=status.HTTP_200_OK)
            else:
                return Response(resultado, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({"error": "Error interno del servidor al procesar IA."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)