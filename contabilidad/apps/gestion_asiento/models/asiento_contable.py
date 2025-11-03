from django.db import models
from ...empresa.models import Empresa
from django.db.models import Max
from django.db import transaction
import uuid

class AsientoContable(models.Model):
    ESTADO_CHOICES = [
        ('BORRADOR','BORRADOR'),
        ('APROBADO','APROBADO'),
        ('CANCELADO','CANCELADO'),        
    ]
    class Meta:
        db_table = "asiento_contable"
        unique_together = ('numero','empresa')
        
    id = models.UUIDField(primary_key=True,editable=False,default=uuid.uuid4)
    numero = models.PositiveIntegerField(blank=True,null=True)
    descripcion = models.CharField(max_length=100)
    fecha = models.DateField(null=True,blank=True)
    empresa = models.ForeignKey(Empresa,on_delete=models.CASCADE,related_name='asientos')
    estado = models.CharField(max_length=10,choices=ESTADO_CHOICES,default='BORRADOR')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Solo asignar numero si es un registro nuevo
        if not self.numero:
            with transaction.atomic():
                # Bloquear los registros de la empresa para evitar duplicados
                ultimo_numero = (
                    AsientoContable.objects
                    .select_for_update()
                    .filter(empresa=self.empresa)
                    .aggregate(Max('numero'))['numero__max'] or 0
                )
                self.numero = ultimo_numero + 1

        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Asiento #{self.numero} - {self.descripcion}"