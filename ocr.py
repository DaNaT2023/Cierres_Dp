import streamlit as st
import sqlite3
import pandas as pd
import datetime
import time
import re
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

# Función para buscar un número justo al lado de una palabra clave detectada
def buscar_cifra(texto, palabra_clave):
    patron = re.compile(rf"{palabra_clave}\s*[:\-=\s]*\s*([\d.,\s]+)", re.IGNORECASE)
    coincidencia = patron.search(texto)
    if coincidencia:
        valor = coincidencia.group(1).replace("€", "").replace(" ", "").replace(",", ".")
        try:
            return float(valor)
        except:
            return 0.0
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
    
    st.subheader("📸 Subir Recuadro Diario desde el Móvil")
    imagen_subida = st.file_uploader("Arrastra o selecciona la foto del recuadro diario", type=["png", "jpg", "jpeg"], key="cargador_imagenes_tiendas")
    
    if imagen_subida is not None:
        st.image(imagen_subida, caption="Imagen cargada correctamente", width=300)
        
        if st.button("🔍 Extraer Palabras del Recuadro", key="btn_ejecutar_ocr_ia"):
            with st.spinner("Analizando y emparejando etiquetas del recuadro..."):
                try:
                    # Usamos la librería OCR nativa que procesa el texto en el servidor de Streamlit
                    import pytesseract
                    img = Image.open(imagen_subida)
                    texto_extraido = pytesseract.image_to_string(img)
                    
                    # Limpieza lineal del texto extraído por palabras
                    lineas = [linea.strip() for linea in texto_extraido.split("\n") if linea.strip()]
                    texto_unificado = "\n".join(lineas)
                    
                    # Mapear los datos palabra por palabra de forma ultra-segura
                    st.session_state.venta_neta_detectada = buscar_cifra(texto_unificado, "venta neta")
                    st.session_state.venta_detectada = buscar_cifra(texto_unificado, "venta total")
                    st.session_state.venta_2025_detectada = buscar_cifra(texto_unificado, "venta 2025")
                    st.session_state.venta_entrega_detectada = buscar_cifra(texto_unificado, "venta entrega")
                    st.session_state.venta_llevar_detectada = buscar_cifra(texto_unificado, "venta llevar")
                    st.session_state.venta_ventana_detectada = buscar_cifra(texto_unificado, "venta ventana")
                    st.session_state.venta_come_bebe_detectada = buscar_cifra(texto_unificado, "come & bebe")
                    st.session_state.venta_visa_detectada = buscar_cifra(texto_unificado, "venta visa")
                    st.session_state.venta_efectivo_detectada = buscar_cifra(texto_unificado, "venta en efectivo")
                    st.session_state.venta_pluxee_detectada = buscar_cifra(texto_unificado, "pluxee gourmet")
                    st.session_state.quebranto_detectado = buscar_cifra(texto_unificado, "quebranto")
                    st.session_state.ingreso_prosegur_detectada = buscar_cifra(texto_unificado, "ingreso prosegur")
                    st.session_state.web_detectada = buscar_cifra(texto_unificado, "web")
                    st.session_state.tgtg_detectada = buscar_cifra(texto_unificado, "tgtg")
                    st.session_state.uber_eats_detectada = buscar_cifra(texto_unificado, "uber eats")
                    st.session_state.glovo_detectada = buscar_cifra(texto_unificado, "glovo")
                    st.session_state.just_eat_detectada = buscar_cifra(texto_unificado, "just eat")
                    
                    # Intentar buscar el encargado de forma genérica
                    for linea in lineas:
                        if "encargado" in linea.lower():
                            st.session_state.encargado_detectado = linea.lower().replace("encargado", "").replace(":", "").strip().capitalize()
                    
                    st.success("¡Palabras procesadas! Verifica los datos abajo.")
                    st.rerun()
                except Exception as e_ocr:
                    st.error(f"Falta configurar el motor gráfico en el servidor: {e_ocr}. Introduce los datos manualmente abajo.")

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
        venta_neta = st.number_input("Venta Neta (€)", value=st.session_state.venta_neta_detectada, step=10.0, key="input_vn_formulario")
        venta = st.number_input("Venta Total del Turno (€)", value=st.session_state.venta_detectada, step=10.0, key="input_vt_formulario")
        venta_2025 = st.number_input("Venta 2025 (€)", value=st.session_state.venta_2025_detectada, step=10.0, key="input_v25_formulario")

    with col2:
        venta_entrega = st.number_input("Venta Entrega (€)", value=st.session_state.venta_entrega_detectada, step=10.0, key="input_ve_formulario")
        venta_llevar = st.number_input("Venta Llevar (€)", value=st.session_state.venta_llevar_detectada, step=10.0, key="input_vll_formulario")
        venta_ventana = st.number_input("Venta Ventana (€)", value=st.session_state.venta_ventana_detectada, step=10.0, key="input_vv_formulario")
        venta_come_bebe = st.number_input("Venta Come & Bebe (€)", value=st.session_state.venta_come_bebe_detectada, step=10.0, key="input_vcb_formulario")
        venta_visa = st.number_input("Venta VISA (€)", value=st.session_state.venta_visa_detectada, step=10.0, key="input_vvi_formulario")
        venta_efectivo = st.number_input("Venta en Efectivo (€)", value=st.session_state.venta_efectivo_detectada, step=10.0, key="input_vef_formulario")

    with col3:
        venta_pluxee = st.number_input("Venta Pluxee Gourmet (€)", value=st.session_state.venta_pluxee_detectada, step=10.0, key="input_vp_formulario")
        quebranto = st.number_input("Importe del Quebranto (€)", value=st.session_state.quebranto_detectado, step=5.0, key="input_quebranto_formulario")
        ingreso_prosegur = st.number_input("Ingreso Prosegur (€)", value=st.session_state.ingreso_prosegur_detectada, step=10.0, key="input_pro_formulario")
