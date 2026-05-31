import streamlit as st
import sqlite3
import pandas as pd
import datetime
import time
import google.generativeai as genai  # Librería clásica optimizada para control de cuotas
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

# Inicializar variables de estado de forma limpia
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
            venta_total REAL,
            quebranto REAL,
            estado_alerta TEXT
        )
    """)
    conexion.commit()
    conexion.close()

inicializar_bd()

# ==========================================
# 2. DISEÑO DE LA INTERFAZ WEB
# ==========================================
st.set_page_config(page_title="Panel Cierre Diario Dp 🍕", layout="wide")

st.title("🍕 Panel Cierre Diario Dp")
st.markdown("---")

pestaña_tiendas, pestaña_dueño = st.tabs(["📲 Envío de Tiendas", "👁️ Panel del Propietario"])

# ------------------------------------------
# PESTAÑA 1: ENVÍO DE TIENDAS
# ------------------------------------------
with pestaña_tiendas:
    st.header("Formulario de Cierre de Turno")
    
    turno_seleccionado = st.radio(
        "¿Qué turno vas a escanear/subir ahora?", 
        ["Mañana", "Noche"], 
        horizontal=True, 
        key="selector_turno_superior"
    )
    
    st.subheader("📸 Subir Recuadro Diario")
    imagen_subida = st.file_uploader("Arrastra o selecciona la foto del recuadro diario", type=["png", "jpg", "jpeg"], key="cargador_imagenes_tiendas")
    
    if imagen_subida is not None:
        st.image(imagen_subida, caption="Imagen cargada correctamente", width=300)
        
        if st.button("🔍 Leer Recuadro con IA", key="btn_ejecutar_ocr_ia"):
            with st.spinner(f"Analizando minuciosamente el turno de la {turno_seleccionado}..."):
                try:
                    img = Image.open(imagen_subida)
                    
                    # Configuración clásica del cliente de Google
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    prompt_ocr = f"""
                    Analiza la imagen de este recuadro de caja de la tienda.
                    Estamos procesando el turno de la: **{turno_seleccionado}**.
                    
                    REGLAS DE EXTRACCIÓN EXTRA ESTRICTAS:
                    1. ENCARGADO: Extrae única y exclusivamente el nombre de la persona que trabajó en el turno de la **{turno_seleccionado}**. Desecha por completo el nombre del otro turno.
                    2. VENTA TOTAL: Busca la cifra de "Venta Total" (importe bruto final acumulado). 
                       - REGLA DE CENTRADO: Si la casilla o celda de la "Venta Total" se encuentra físicamente centrada o unificada aplicando a todo el día entero (sin divisiones por líneas para mañana y noche), debes usar obligatoriamente ese mismo valor numérico tanto si te pedimos la Mañana como si te pedimos la **{turno_seleccionado}**.
                       - IGNORA por completo el año de la fecha (como 2025 o 2026), no lo asocies con la venta.
                       - IGNORA el campo o fila que diga "Venta Neta" o "Base Imponible".
                    3. QUEBRANTO: Extrae el número del quebranto asignado a la **{turno_seleccionado}** (si viene con signo menos, mantén el valor negativo).
                    
                    Responde ÚNICAMENTE en este formato exacto, sin introducciones ni textos extra:
                    Tienda: [Debe ser exactamente uno de estos nombres: {', '.join(LISTA_TIENDAS)}]
                    Encargado: [Nombre del encargado de la {turno_seleccionado}]
                    Venta: [Número de la venta total sin símbolos]
                    Quebranto: [Número del quebranto de la {turno_seleccionado} sin símbolos]
                    """
                    
                    # Manejo avanzado de cuota y reintentos (Rate Limits)
                    response_ocr = None
                    for intento in range(5):
                        try:
                            response_ocr = model.generate_content([img, prompt_ocr])
                            break
                        except Exception as api_error:
                            if "429" in str(api_error) and intento < 4:
                                st.warning(f"Google está saturado. Reintentando de forma automática en {5 + intento * 5} segundos...")
                                time.sleep(5 + intento * 5)
                            else:
                                raise api_error
                    
                    texto_extraido = response_ocr.text
                    st.info("Datos detectados en la imagen:")
                    st.text(texto_extraido)
                    
                    for linea in texto_extraido.split("\n"):
                        if ":" in linea:
                            clave, valor = linea.split(":", 1)
                            clave = clave.strip().lower()
                            valor = valor.strip()
                            
                            if clave == "tienda" and valor in LISTA_TIENDAS:
                                st.session_state.tienda_detectada = valor
                            elif clave == "encargado":
                                st.session_state.encargado_detectado = valor
                            elif clave == "venta":
                                valor_limpio = valor.replace("€", "").replace(" ", "").replace(",", ".")
                                # Filtro de año corregido al 100% de forma limpia
                                if valor_limpio not in ["2025", "2026", "2025.0", "2026.0"]:
                                    if valor_limpio.replace(".", "", 1).isdigit():
                                        st.session_state.venta_detectada = float(valor_limpio)
                            elif clave == "quebranto":
                                valor_limpio = valor.replace("€", "").replace(" ", "").replace(",", ".")
                                test_val = valor_limpio.replace("-", "", 1).replace(".", "", 1)
                                if test_val.isdigit():
                                    st.session_state.quebranto_detectado = float(valor_limpio)
                                
                    st.success("¡Datos guardados en memoria! Revisa abajo.")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error al analizar la imagen: {e}")

    st.markdown("---")
    st.subheader("📝 Confirmar Datos del Formulario")
    
    tienda_idx = 0
    if st.session_state.tienda_detectada in LISTA_TIENDAS:
        tienda_idx = LISTA_TIENDAS.index(st.session_state.tienda_detectada)
        
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        tienda = st.selectbox("Selecciona tu Tienda", LISTA_TIENDAS, index=tienda_idx, key="combo_tiendas_formulario")
        encargado = st.text_input("Nombre del Encargado", value=st.session_state.encargado_detectado, key="input_encargado_formulario")
        
    with col_der:
        fecha = st.date_input("Fecha del Recuadro", datetime.date.today(), key="input_fecha_formulario")
        venta = st.number_input("Venta Total del Turno (€)", min_value=0.0, step=10.0, value=st.session_state.venta_detectada, key="input_venta_formulario")
        quebranto = st.number_input("Importe del Quebranto (€)", step=5.0, value=st.session_state.quebranto_detectado, key="input_quebranto_formulario")

    if st.button("🚀 Procesar y Guardar Registro", key="btn_guardar_registro_bd"):
        if encargado.strip() == "":
            st.error("Por favor, introduce el nombre del encargado.")
        else:
            alerta = "OK"
            if quebranto <= -100:
                alerta = "🚨 CRÍTICO (Pérdida)"
            elif quebranto >= 100:
                alerta = "⚠️ ATENCIÓN (Exceso)"
                
            conn = sqlite3.connect("tiendas.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO recuadros (fecha, tienda, turno, encargado, venta_total, quebranto, estado_alerta)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (fecha.strftime("%Y-%m-%d"), tienda, turno_seleccionado, encargado, venta, quebranto, alerta))
            conn.commit()
            conn.close()
            
            st.success(f"¡Datos de {tienda} ({turno_seleccionado}) guardados con éxito!")
            
            st.session_state.encargado_detectado = ""
            st.session_state.venta_detectada = 0.0
            st.session_state.quebranto_detectado = 0.0
            st.rerun()

# ------------------------------------------
# PESTAÑA 2: PANEL DEL PROPIETARIO
# ------------------------------------------
with pestaña_dueño:
    if not st.session_state.autenticado:
