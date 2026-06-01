import streamlit as st
import sqlite3
import pandas as pd
import datetime
import time
from openai import OpenAI
import base64
import json
from PIL import Image

# ==========================================
# 0. CONFIGURACIÓN DE TUS 6 TIENDAS REALES (DP)
# ==========================================
LISTA_TIENDAS = [
    "Dp Valdebebas",
    "Dp Collado",
    "Dp Paracuellos",
    "Dp Villanueva",
    "Dp Galapagar",
    "Dp Vicálvaro"
]

# Inicializar variables en el estado de la sesión para evitar fallos de lectura
if "tienda_detectada" not in st.session_state:
    st.session_state.tienda_detectada = "Dp Valdebebas"
if "encargado_detectado" not in st.session_state:
    st.session_state.encargado_detectado = ""
if "venta_detectada" not in st.session_state:
    st.session_state.venta_detectada = 0.0
if "quebranto_detectado" not in st.session_state:
    st.session_state.quebranto_detectado = 0.0
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# Inicializar nuevas variables financieras en el estado de la sesión
NUEVOS_CAMPOS = [
    "fecha_detectada", "venta_neta_detectada", "venta_2025_detectada", 
    "venta_entrega_detectada", "venta_llevar_detectada", "venta_ventana_detectada", 
    "venta_come_bebe_detectada", "venta_visa_detectada", "venta_efectivo_detectada", 
    "venta_pluxee_detectada", "ingreso_prosegur_detectada", "web_detectada", 
    "tgtg_detectada", "uber_eats_detectada", "glovo_detectada", "just_eat_detectada"
]

for campo in NUEVOS_CAMPOS:
    if campo not in st.session_state:
        if "fecha" in campo:
            st.session_state[campo] = datetime.date.today()
        else:
            st.session_state[campo] = 0.0

# Función auxiliar para convertir valores a float de forma segura sin romper la indentación
def convertir_a_float(valor):
    if valor is None:
        return 0.0
    try:
        return float(valor)
    except:
        return 0.0

# ==========================================
# 1. BASE DE DATOS LOCAL
# ==========================================
def inicializar_bd():
    conexion = sqlite3.connect("tiendas.db")
    cursor = conexion.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recuadros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            tienda TEXT,
            turno TEXT,
            encargado TEXT,
            venta_neta REAL,
            venta_total REAL,
            venta_2025 REAL,
            venta_entrega REAL,
            venta_llevar REAL,
            venta_ventana REAL,
            venta_come_bebe REAL,
            venta_visa REAL,
            venta_efectivo REAL,
            venta_pluxee REAL,
            quebranto REAL,
            ingreso_prosegur REAL,
            web REAL,
            tgtg REAL,
            uber_eats REAL,
            glovo REAL,
            just_eat REAL,
            estado_alerta TEXT
        )
    """)
    conexion.commit()
    conexion.close()

inicializar_bd()

# ==========================================
# 2. INTERFAZ WEB CON STREAMLIT
# ==========================================
st.set_page_config(page_title="Panel Cierre Diario Dp 🍕", layout="wide")

st.title("🍕 Panel Cierre Diario Dp")
st.markdown("---")

pestaña_tiendas, pestaña_dueño = st.tabs(["📲 Envío de Tiendas", "👁️ Panel del Propietario"])

# ------------------------------------------
# SECCIÓN: ENVÍO DE TIENDAS
# ------------------------------------------
with pestaña_tiendas:
    st.header("Formulario de Cierre de Turno")
    
    col_pre1, col_pre2 = st.columns(2)
    with col_pre1:
        turno_seleccionado = st.radio("¿Qué turno vas a escanear/subir ahora?", ["Mañana", "Noche"], horizontal=True, key="selector_turno_superior")
    
    st.subheader("📸 Subir Recuadro Diario")
    imagen_subida = st.file_uploader("Arrastra o selecciona la foto del recuadro diario", type=["png", "jpg", "jpeg"], key="cargador_imagenes_tiendas")
    
    if imagen_subida is not None:
        st.image(imagen_subida, caption="Imagen cargada correctamente", width=300)
        
        if st.button("🔍 Leer Recuadro con IA", key="btn_ejecutar_ocr_ia"):
            with st.spinner(f"Analizando turno de la {turno_seleccionado} con Together AI..."):
                texto_respuesta = ""
                error_detectado = False
                
                try:
                    imagen_subida.seek(0)
                    bytes_imagen = imagen_subida.read()
                    imagen_base64 = base64.b64encode(bytes_imagen).decode('utf-8')
                    
                    client = OpenAI(
                        base_url="https://together.xyz",
                        api_key=st.secrets["TOGETHER_API_KEY"]
                    )
                    
                    prompt_ocr = f"""
                    Analiza la imagen de la tabla de caja diaria. Extrae los datos específicamente para el turno de la: **{turno_seleccionado}**.
                    Reglas:
                    1. Extrae los datos de la columna correspondiente al turno solicitado ({turno_seleccionado}).
                    2. Si un valor numérico está unificado o centrado (ej. Venta total, Web, TGTG, Uber Eats, Glovo, Just Eat), utiliza ese valor único.
                    3. Devuelve los datos estrictamente en este formato JSON, sin código markdown, solo el objeto JSON limpio:
                    {{
                        "fecha": "DD/MM/AAAA",
                        "tienda": "Nombre exacto",
                        "encargado": "Nombre del encargado",
                        "venta_neta": 0.0,
                        "venta_total": 0.0,
                        "venta_2025": 0.0,
                        "venta_entrega": 0.0,
                        "venta_llevar": 0.0,
                        "venta_ventana": 0.0,
                        "venta_come_bebe": 0.0,
                        "venta_visa": 0.0,
                        "venta_efectivo": 0.0,
                        "venta_pluxee": 0.0,
                        "quebranto": 0.0,
                        "ingreso_prosegur": 0.0,
                        "web": 0.0,
                        "tgtg": 0.0,
                        "uber_eats": 0.0,
                        "glovo": 0.0,
                        "just_eat": 0.0
                    }}
                    """
                    
                    response = client.chat.completions.create(
                        model="meta-llama/Llama-3.2-90B-Vision-Instruct",
                        messages=[{"role": "user", "content": [{"type": "text", "text": prompt_ocr}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{imagen_base64}"}}]}],
                        temperature=0.1
                    )
                    texto_respuesta = response.choices.message.content.strip()
                except Exception as api_err:
                    st.error(f"Error de conexión con la IA: {api_err}")
                    error_detectado = True

                # FLUJO SEGURO 100% LINEAL
                if not error_detectado and texto_respuesta:
                    if "doctype" in texto_respuesta.lower() or "<html" in texto_respuesta.lower():
                        st.error("El servidor de la IA está saturado. Pulsa el botón de nuevo.")
                    else:
                        inicio_json = texto_respuesta.find("{")
                        fin_json = texto_respuesta.rfind("}") + 1
                        
                        if inicio_json != -1 and fin_json != 0:
                            try:
                                datos = json.loads(texto_respuesta[inicio_json:fin_json])
                                
                                # Procesar fecha de forma aislada e independiente
                                f_str = datos.get("fecha", "")
                                st.session_state.fecha_detectada = datetime.date.today()
                                if len(f_str) == 10:
                                    try:
                                        st.session_state.fecha_detectada = datetime.datetime.strptime(f_str, "%d/%m/%Y").date()
                                    except:
                                        pass
                                
                                if datos.get("tienda") in LISTA_TIENDAS:
                                    st.session_state.tienda_detectada = datos.get("tienda")
                                
                                # Mapeo usando la función de conversión segura sin sub-bloques try/except
                                st.session_state.encargado_detectado = str(datos.get("encargado", ""))
                                st.session_state.venta_neta_detectada = convertir_a_float(datos.get("venta_neta"))
                                st.session_state.venta_detectada = convertir_a_float(datos.get("venta_total"))
                                st.session_state.venta_2025_detectada = convertir_a_float(datos.get("venta_2025"))
                                st.session_state.venta_entrega_detectada = convertir_a_float(datos.get("venta_entrega"))
                                st.session_state.venta_llevar_detectada = convertir_a_float(datos.get("venta_llevar"))
                                st.session_state.venta_ventana_detectada = convertir_a_float(datos.get("venta_ventana"))
                                st.session_state.venta_come_bebe_detectada = convertir_a_float(datos.get("venta_come_bebe"))
                                st.session_state.venta_visa_detectada = convertir_a_float(datos.get("venta_visa"))
                                st.session_state.venta_efectivo_detectada = convertir_a_float(datos.get("venta_efectivo"))
                                st.session_state.venta_pluxee_detectada = convertir_a_float(datos.get("venta_pluxee"))
                                st.session_state.quebranto_detectado = convertir_a_float(datos.get("quebranto"))
