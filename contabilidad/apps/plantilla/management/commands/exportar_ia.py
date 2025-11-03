# en tu_app_contable/management/commands/exportar_ia.py

import json
from django.core.management.base import BaseCommand
from contabilidad.apps.gestion_asiento.models import AsientoContable # ¡Importa tus modelos!

# --- ¡IMPORTANTE! ---
# Esta lista debe coincidir con los códigos que usaste en tu seeder.
# Es la lista de "respuestas" que tu IA aprenderá a predecir.
CODIGOS_ENTRENABLES = [
    # Activos
    "11102", "11103", "11301", "11302", "11401", "11501", "12302", "12303", "12401", "11201",
    # Pasivos
    "21101", "21201", "21301",
    # Patrimonio
    "31101",
    # Ingresos
    "41101", "42101",
    # Egresos
    "51101", "52101", "52201", "52301", "52401", "52501", "53101", "53201", "54101", "55101"
]


class Command(BaseCommand):
    help = 'Exporta los datos de asientos contables al formato JSONL para entrenar spaCy.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando exportación para IA...")
        
        output_filename = 'entrenamiento.jsonl'
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            # .prefetch_related() es una optimización para cargar todos los movimientos
            # de una sola vez. Es mucho más rápido.
            asientos = AsientoContable.objects.prefetch_related('movimientos__cuenta').all()
            
            lineas_exportadas = 0
            
            for asiento in asientos:
                # 1. Limpiamos la descripción (quitamos el " #i+1" que agregamos)
                # "Pago de factura de luz #123" -> "Pago de factura de luz"
                texto_limpio = asiento.descripcion.split(' #')[0].strip()
                
                # 2. Creamos el diccionario de 'cats'
                cats = {codigo: 0.0 for codigo in CODIGOS_ENTRENABLES}
                
                movimientos_relevantes = 0
                for mov in asiento.movimientos.all():
                    codigo_str = str(mov.cuenta.codigo)
                    
                    # Si el movimiento usa una de nuestras cuentas entrenables...
                    if codigo_str in cats:
                        # ...la marcamos como "respuesta correcta" (1.0)
                        cats[codigo_str] = 1.0
                        movimientos_relevantes += 1
                
                # 3. Solo guardamos la línea si tiene al menos un movimiento relevante
                if movimientos_relevantes > 0:
                    linea = {
                        "text": texto_limpio,
                        "cats": cats,
                    }
                    f.write(json.dumps(linea, ensure_ascii=False) + '\n')
                    lineas_exportadas += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ ¡Exportación completa! Se guardaron {lineas_exportadas} líneas en '{output_filename}'."
        ))