# contabilidad/apps/modelos_ia/apps.py

from django.apps import AppConfig

class ModelosIaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contabilidad.apps.modelos_ia'
    verbose_name = 'Servicios de IA'

    def ready(self):
        # Importa y carga el modelo al inicio de la aplicación
        try:
            from . import services
            services.load_nlp_model()
        except Exception as e:
            # Esto permite al servidor arrancar aunque el modelo no se haya copiado 
            # (útil en desarrollo o si el modelo está en otra máquina).
            print(f"Advertencia: El modelo de IA de Asientos no se pudo cargar: {e}")