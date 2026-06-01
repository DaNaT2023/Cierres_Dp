import streamlit as st
import sqlite3
import pandas as pd
import datetime
import time
import base64
import json
from google import genai
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
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# Inicializar nuevas variables financieras en el estado de la sesión
NUEVOS_CAMPOS = [
    "fecha_detectada", "venta_neta_detectada", "venta_2025_detectada", 
    "venta_entrega_detectada", "venta_llevar_detectada", "venta_ventana_detectada", 
    "venta_come_bebe_detectada", "venta_visa_detectada", "venta_efectivo_detectada", 
    "venta_pluxee_detectada", "ingreso_prosegur_detectada", "web_detectada", 
    "tgtg_detectada", "uber_eats_detectada", "glovo_detectada", "just_eat_detectada",
    "quebranto_detectado", "venta_detectada"
]

for campo in NUEVOS_CAMPOS:
    if campo not in st.session_state:
        if "fecha" in campo:
            st.session_state[campo] = datetime.date.today()
        else:
            st.session_state[campo] = 0.0

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
            with st.spinner(f"Analizando turno de la {turno_seleccionado} con Google Gemini (SDK Oficial)..."):
                texto_respuesta = ""
                error_detectado = False
                
                try:
                    img = Image.open(imagen_subida)
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    
                    prompt_ocr = f"Analiza la imagen de la tabla de caja diaria. Extrae los datos específicamente para el turno de la: {turno_seleccionado}. Reglas: 1. Extrae los datos de la columna correspondiente al turno solicitado. 2. Si un valor numérico está unificado o centrado (ej. Venta total, Web, TGTG, Uber Eats, Glovo, Just Eat), utiliza ese valor único. 3. Devuelve los datos estrictamente en formato JSON válido, usando exactamente estas llaves: fecha, tienda, encargado, venta_neta, venta_total, venta_2025, venta_entrega, venta_llevar, venta_ventana, venta_come_bebe, venta_visa, venta_efectivo, venta_pluxee, quebranto, ingreso_prosegur, web, tgtg, uber_eats, glovo, just_eat"
                    
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[img, prompt_ocr],
                        config={"response_mime_type": "application/json"}
                    )
                    texto_respuesta = response.text.strip()
                        
                except Exception as api_err:
                    st.error(f"Error con el motor oficial de Gemini: {api_err}. Revisa tu clave en Secrets.")
                    error_detectado = True

                # PROCESAMIENTO LINEAL PROTEGIDO
                if not error_detectado and texto_respuesta:
                    inicio_json = texto_respuesta.find("{")
                    fin_json = texto_respuesta.rfind("}") + 1
                    
                    if inicio_json != -1 and fin_json != 0:
                        datos_json = None
                        try:
                            datos_json = json.loads(texto_respuesta[inicio_json:fin_json])
                        except:
                            st.error("No se pudo estructurar el contenido como JSON.")
                        
                        if datos_json is not None:
                            f_str = datos_json.get("fecha", "")
                            st.session_state.fecha_detectada = datetime.date.today()
                            if len(f_str) == 10:
                                try:
                                    st.session_state.fecha_detectada = datetime.datetime.strptime(f_str, "%d/%m/%Y").date()
                                except:
                                    pass
                            
                            tienda_ia = datos_json.get("tienda", "")
                            for t in LISTA_TIENDAS:
                                if t.lower() in tienda_ia.lower():
                                    st.session_state.tienda_detectada = t
                            
                            st.session_state.encargado_detectado = str(datos_json.get("encargado", ""))
                            st.session_state.venta_neta_detectada = convertir_a_float(datos_json.get("venta_neta"))
                            st.session_state.venta_detectada = convertir_a_float(datos_json.get("venta_total"))
                            st.session_state.venta_2025_detectada = convertir_a_float(datos_json.get("venta_2025"))
                            st.session_state.venta_entrega_detectada = convertir_a_float(datos_json.get("venta_entrega"))
                            st.session_state.venta_llevar_detectada = convertir_a_float(datos_json.get("venta_llevar"))
                            st.session_state.venta_ventana_detectada = convertir_a_float(datos_json.get("venta_ventana"))
                            st.session_state.venta_come_bebe_detectada = convertir_a_float(datos_json.get("venta_come_bebe"))
                            st.session_state.venta_visa_detectada = convertir_a_float(datos_json.get("venta_visa"))
                            st.session_state.venta_efectivo_detectada = convertir_a_float(datos_json.get("venta_efectivo"))
                            st.session_state.venta_pluxee_detectada = convertir_a_float(datos_json.get("venta_pluxee"))
                            st.session_state.quebranto_detectado = convertir_a_float(datos_json.get("quebranto"))
                            st.session_state.ingreso_prosegur_detectada = convertir_a_float(datos_json.get("ingreso_prosegur"))
                            st.session_state.web_detectada = convertir_a_float(datos_json.get("web"))
                            st.session_state.tgtg_detectada = convertir_a_float(datos_json.get("tgtg"))
                            st.session_state.uber_eats_detectada = convertir_a_float(datos_json.get("uber_eats"))
                            st.session_state.glovo_detectada = convertir_a_float(datos_json.get("glovo"))
                            st.session_state.just_eat_detectada = convertir_a_float(datos_json.get("just_eat"))
                            
                            st.success("¡Datos del recuadro cargados con éxito!")
                            st.rerun()
                    else:
                        st.error("La IA no contiene un formato de tabla válido.")

    st.markdown("---")
    st.subheader("📝 Confirmar Datos del Formulario")
    
    tienda_idx = 0
    if st.session_state.tienda_detectada in LISTA_TIENDAS:
        tienda_idx = LISTA_TIENDAS.index(st.session_state.tienda_detectada)
        
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tienda = st.selectbox("Selecciona tu Tienda", LISTA_TIENDAS, index=tienda_idx, key="combo_tiendas_formulario")
        encargado = st.text_input("Nombre del Encargado", value=st.session_state.encargado_detectado, key="input_encargado_formulario")
        fecha = st.date_input("Fecha del Recuadro", value=st.session_state.fecha_detectada, key="input_fecha_formulario")
