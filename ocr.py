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

# ==========================================
# 1. BASE DE DATOS LOCAL (CON TODOS LOS CAMPOS NUEVOS)
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
            with st.spinner(f"Analizando turno de la {turno_seleccionado} con Together AI (Sin bloqueos)..."):
                try:
                    imagen_subida.seek(0)
                    bytes_imagen = imagen_subida.read()
                    imagen_base64 = base64.b64encode(bytes_imagen).decode('utf-8')
                    
                    # Conexión con Together AI usando OpenAI SDK compatible
                    client = OpenAI(
                        base_url="https://together.xyz",
                        api_key=st.secrets["TOGETHER_API_KEY"]
                    )
                    
                    prompt_ocr = f"""
                    Analiza la imagen de la tabla de caja diaria. Extrae los datos específicamente para el turno de la: **{turno_seleccionado}**.
                    
                    Reglas críticas de extracción:
                    1. Identifica las columnas 'Turno Mañana' y 'Turno Noche'. Extrae los datos de la columna correspondiente al turno solicitado.
                    2. Si un valor numérico está unificado, centrado o solo aparece una cifra para todo el día (ej. Venta total, Web, TGTG, Uber Eats, Glovo, Just Eat), utiliza ese valor único independientemente del turno seleccionado.
                    3. Devuelve los datos estrictamente en este formato JSON, sin texto adicional, sin bloques de código markdown, solo el objeto JSON limpio:
                    {{
                        "fecha": "DD/MM/AAAA",
                        "tienda": "Especifica el nombre de la tienda si aparece, o dejas vacío",
                        "encargado": "Nombre del encargado del turno",
                        "venta_neta": número,
                        "venta_total": número,
                        "venta_2025": número,
                        "venta_entrega": número,
                        "venta_llevar": número,
                        "venta_ventana": número,
                        "venta_come_bebe": número,
                        "venta_visa": número,
                        "venta_efectivo": número,
                        "venta_pluxee": número,
                        "quebranto": número,
                        "ingreso_prosegur": número,
                        "web": número,
                        "tgtg": número,
                        "uber_eats": número,
                        "glovo": número,
                        "just_eat": número
                    }}
                    """
                    
                    response = client.chat.completions.create(
                        model="meta-llama/Llama-3.2-11B-Vision-Instruct",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt_ocr},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{imagen_base64}"
                                        }
                                    }
                                ]
                            }
                        ],
                        temperature=0.1
                    )
                    
                    texto_limpio = response.choices.message.content.replace("```json", "").replace("```", "").strip()
                    datos = json.loads(texto_limpio)
                    
                    # Mapear datos a variables de sesión de Streamlit
                    try:
                        st.session_state.fecha_detectada = datetime.datetime.strptime(datos.get("fecha", ""), "%d/%m/%Y").date()
                    except:
                        st.session_state.fecha_detectada = datetime.date.today()
                        
                    if datos.get("tienda") in LISTA_TIENDAS:
                        st.session_state.tienda_detectada = datos.get("tienda")
                        
                    st.session_state.encargado_detectado = datos.get("encargado", "")
                    st.session_state.venta_neta_detectada = float(datos.get("venta_neta", 0.0))
                    st.session_state.venta_detectada = float(datos.get("venta_total", 0.0))
                    st.session_state.venta_2025_detectada = float(datos.get("venta_2025", 0.0))
                    st.session_state.venta_entrega_detectada = float(datos.get("venta_entrega", 0.0))
                    st.session_state.venta_llevar_detectada = float(datos.get("venta_llevar", 0.0))
                    st.session_state.venta_ventana_detectada = float(datos.get("venta_ventana", 0.0))
                    st.session_state.venta_come_bebe_detectada = float(datos.get("venta_come_bebe", 0.0))
                    st.session_state.venta_visa_detectada = float(datos.get("venta_visa", 0.0))
                    st.session_state.venta_efectivo_detectada = float(datos.get("venta_efectivo", 0.0))
                    st.session_state.venta_pluxee_detectada = float(datos.get("venta_pluxee", 0.0))
                    st.session_state.quebranto_detectado = float(datos.get("quebranto", 0.0))
                    st.session_state.ingreso_prosegur_detectada = float(datos.get("ingreso_prosegur", 0.0))
                    st.session_state.web_detectada = float(datos.get("web", 0.0))
                    st.session_state.tgtg_detectada = float(datos.get("tgtg", 0.0))
                    st.session_state.uber_eats_detectada = float(datos.get("uber_eats", 0.0))
                    st.session_state.glovo_detectada = float(datos.get("glovo", 0.0))
                    st.session_state.just_eat_detectada = float(datos.get("just_eat", 0.0))
                    
                    st.success("¡Datos del recuadro cargados con éxito desde el saldo de Together AI!")
                    st.rerun()
                    
                except Exception as e:
