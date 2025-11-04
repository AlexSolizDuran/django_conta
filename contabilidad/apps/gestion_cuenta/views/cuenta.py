from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models.functions import Cast, Substr
from django.db.models import CharField
from rest_framework import filters
from ...utils.log import registrar_evento  # 🔹 Importamos la función de log

from ..models import Cuenta,ClaseCuenta
from ...gestion_asiento.models import Movimiento
from ...gestion_asiento.serializers import MovimientoListSerializer
from ..serializers.cuenta import (CuentaCreateSerializer,
                                  CuentaDetailSeriliazer,
                                  CuentaListSerializer)


class CuentaViewSet(viewsets.ModelViewSet):
    
    queryset = Cuenta.objects.all()
    serializer_class = CuentaListSerializer
    permission_classes = [IsAuthenticated]
    
    # 💡 Configuración de Filtros
    filter_backends = [filters.SearchFilter, filters.OrderingFilter] # Añadimos SearchFilter
    search_fields = ['codigo', 'nombre'] # Permitimos buscar por código o nombre
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CuentaListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CuentaCreateSerializer
        elif self.action in ['retrieve','destroy']:
            return CuentaDetailSeriliazer
        return super().get_serializer_class()
    
    def get_queryset(self):
        request = self.request
        empresa_id = request.auth.get('empresa')  # o request.user.empresa.id según tu login

        # Filtrar por empresa
        qs = Cuenta.objects.filter(empresa_id=empresa_id)

        # Filtrar por clase seleccionada si se pasa por query params
        clase_id = request.query_params.get('clase_id')
        if clase_id:
            try:
                clase = ClaseCuenta.objects.get(id=clase_id, empresa_id=empresa_id)
                # Obtener IDs de todos los descendientes
                descendientes_ids = clase.get_descendientes_ids()
                qs = qs.filter(clase_cuenta_id__in=descendientes_ids)
            except ClaseCuenta.DoesNotExist:
                qs = qs.none()

        # Convertimos codigo a char, luego extraemos el primer dígito y ordenamos
        qs = qs.annotate(
            codigo_str=Cast('codigo', CharField()),      # convierte a texto
            primer_digito=Substr('codigo_str', 1, 1)    # extrae primer dígito
        ).order_by('primer_digito', 'codigo')           # ordena por primer dígito y luego por código completo

        return qs
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)

        # 🔹 Obtener session token de las cookies o header
        token = request.COOKIES.get("sessionToken") or request.headers.get('Authorization', '').split(' ')[-1]
        username = request.user.id
        empresa_id = str(request.auth.get('empresa'))

        # 🔹 Registrar evento
        registrar_evento(
            id_sesion=token,
            empresa_id=empresa_id,
            usuario_id=username,
            datos_usuario=None,  # no es necesario pasar datos_usuario en eventos posteriores
            nivel="INFO",
            accion="Creación de cuenta",
            detalle=f"El usuario {username} creó una nueva cuenta con ID {response.data.get('codigo')} y nombre '{response.data.get('nombre')}'."
        )

        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        cuenta_id = getattr(instance, "id", "desconocido")
        cuenta_nombre = getattr(instance, "nombre", "desconocido")

        response = super().destroy(request, *args, **kwargs)

        token = request.COOKIES.get("sessionToken") or request.headers.get('Authorization', '').split(' ')[-1]
        username = request.user.id
        empresa_id = str(request.auth.get('empresa'))

        registrar_evento(
            id_sesion=token,
            empresa_id=empresa_id,
            usuario_id=username,
            datos_usuario=None,
            nivel="WARNING",
            accion="Eliminación de cuenta",
            detalle=f"El usuario {username} eliminó la cuenta con ID {cuenta_id} y nombre '{cuenta_nombre}'."
        )

        return response
    
    @action(detail=True, methods=['get'])
    def movimientos(self, request, pk=None):
        """
        GET /cuentas/{id}/movimientos/
        Devuelve los movimientos asociados a la cuenta
        """
        try:
            cuenta = self.get_object()  # Obtiene la cuenta según pk
        except Cuenta.DoesNotExist:
            return Response({"detail": "Cuenta no encontrada"}, status=404)

        movimientos = Movimiento.objects.filter(id_cuenta=cuenta.id)
        serializer = MovimientoListSerializer(movimientos, many=True)
        
        return Response(serializer.data)
