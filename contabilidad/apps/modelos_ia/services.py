# contabilidad/apps/modelos_ia/services.py

import spacy
from django.conf import settings
from pathlib import Path
from decimal import Decimal
import re
from datetime import date
from typing import List, Dict, Optional, Tuple, Any

# --- 1. CONFIGURACIÓN GLOBAL Y CARGA DEL MODELO ---

# Se asume que el modelo entrenado está en: contabilidad/apps/modelos_ia/modelo_contable_v1
MODEL_DIR = Path(settings.BASE_DIR) /'contabilidad'/ 'apps' / 'modelos_ia' / 'modelo_contable_v1'
NLP_MODEL = None
UMBRAL_CONFIANZA = 0.4 # Umbral de confianza para la predicción (ajustado para alta precisión)

def load_nlp_model():
    """Carga el modelo de spaCy una sola vez en la memoria global."""
    global NLP_MODEL
    if NLP_MODEL is None:
        try:
            print("--- 🧠 Cargando modelo de IA de Asientos (spaCy)... ---")
            NLP_MODEL = spacy.load(MODEL_DIR, disable=["parser", "tagger"])
            print("--- ✅ Modelo IA de Asientos cargado y listo. ---")
        except OSError as e:
            # Este error ocurrirá si la carpeta 'modelo_contable_v1' no fue copiada correctamente.
            print(f"--- ❌ ERROR: No se encontró el modelo NLP en {MODEL_DIR} ---")
            raise
    return NLP_MODEL

# --- 2. LÓGICA DE POST-PROCESAMIENTO ---

def es_naturaleza_deudora(codigo: str) -> bool:
    """Clasifica si la cuenta es de naturaleza deudora (Activo 1xxx o Gasto 5xxx)."""
    return codigo[0] in ['1', '5']

def obtener_predicciones_ordenadas(cats: Dict[str, float], umbral: float) -> List[Dict[str, Any]]:
    """Filtra y ordena las predicciones por confianza."""
    predicciones = []
    for label, score in cats.items():
        if score >= umbral:
            predicciones.append({
                "codigo": label,
                "confianza": round(score, 3)
            })
    predicciones.sort(key=lambda x: x['confianza'], reverse=True)
    return predicciones

def asignar_debe_haber(predicciones: List[Dict[str, any]]) -> Optional[Tuple[str, str]]:
    """Aplica la lógica de la partida doble para asignar DEBE y HABER."""
    if len(predicciones) < 2:
        return None 

    c1 = predicciones[0]['codigo']
    c2 = predicciones[1]['codigo']
    
    # --- Lógica de Partida Doble: Siempre se busca (Deudora Aumenta) vs (Acreedora Disminuye) ---
    
    # 1. Gasto vs. Activo (Pago de Sueldos): DEBE: 5xxx | HABER: 1xxx
    if c1[0] == '5' and c2[0] == '1': return (c1, c2)
    if c2[0] == '5' and c1[0] == '1': return (c2, c1) 

    # 2. Activo vs. Patrimonio/Ingreso (Aporte/Venta): DEBE: 1xxx | HABER: 3xxx/4xxx
    if c1[0] == '1' and c2[0] in ['3', '4']: return (c1, c2)
    if c2[0] == '1' and c1[0] in ['3', '4']: return (c2, c1) 
    
    # 3. Activo vs. Pasivo (Compra a Crédito/Pago a Proveedor): DEBE: 1xxx/5xxx | HABER: 2xxx
    if es_naturaleza_deudora(c1) and c2[0] == '2': return (c1, c2)
    if es_naturaleza_deudora(c2) and c1[0] == '2': return (c2, c1)
    
    # Caso por defecto (Ej. Ambas de la misma naturaleza)
    return (c1, c2)

def extraer_datos_adicionales(texto: str) -> Dict[str, Any]:
    """Usa expresiones regulares (Regex) para encontrar Monto y Moneda, haciéndolos opcionales."""
    
    # 💡 REGEX CORREGIDO: Captura cualquier bloque de dígitos, puntos y comas.
    # Patrón: r"([\d\.,]+)"  <-- Captura números enteros grandes sin fallar.
    monto_regex = r"([\d\.,]+)(?:\s*(Bs|BOB|USD|\$))?"
    monto_match = re.search(monto_regex, texto, re.IGNORECASE)
    
    monto = None
    moneda = None
    
    if monto_match:
        # El monto se captura en el grupo 1
        monto_str = monto_match.group(1) 
        # La moneda (si existe) se captura en el grupo 2
        moneda_match = monto_match.group(2) 
        
        # --- LÓGICA DE LIMPIEZA MÁS SIMPLE Y ROBUSTA ---
        monto_limpio = monto_str
        
        # 1. Quitar todos los puntos (separadores de miles en formato español/europeo)
        monto_limpio = monto_limpio.replace('.', '')
        
        # 2. Cambiar la coma (separador decimal en formato español/europeo) por punto
        monto_limpio = monto_limpio.replace(',', '.')

        try:
            # 3. Conversión final a Decimal
            monto = Decimal(monto_limpio)
        except Exception:
            monto = None
            
        # Asume BOB si no se especifica
        moneda = moneda_match if moneda_match else "BOB" 
            
    return {
        "monto": monto,
        "moneda": moneda,
        "fecha": date.today().isoformat()
    }

# --- CLASE PRINCIPAL DE SERVICIO (ENDPOINT) ---
class IAModelService:
    
    def predecir_asiento(self, texto_usuario: str) -> Dict[str, Any]:
        
        nlp = load_nlp_model()
            
        doc = nlp(texto_usuario)
        
        predicciones = obtener_predicciones_ordenadas(doc.cats, UMBRAL_CONFIANZA)
        debe_haber = asignar_debe_haber(predicciones)
        datos_extra = extraer_datos_adicionales(texto_usuario)
        
        if debe_haber:
            monto_final = datos_extra['monto'] if datos_extra['monto'] is not None else Decimal('0.00')
            moneda_final = datos_extra['moneda'] if datos_extra['moneda'] is not None else "BOB"
            
            warning_message = None
            if datos_extra['monto'] is None:
                # 💡 Creamos un mensaje de advertencia suave
                warning_message = "Advertencia: No se detectó un monto. Las cuentas han sido pre-llenadas con 0.00."

            return {
                "success": True,
                "debe": debe_haber[0],
                "haber": debe_haber[1],
                "monto": monto_final, # Puede ser 0.00
                "moneda": moneda_final,
                "confianza": predicciones[0]['confianza'],
                "warning": warning_message # Campo nuevo para el frontend
            }
        
        # Fallback si no se encontró el par contable
        return {
            "success": False,
            "error": "No se pudo predecir un par contable con alta confianza.",
            "predicciones_raw": predicciones
        }