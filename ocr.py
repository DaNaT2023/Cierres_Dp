iimport streamlit as st
import sqlite3
import pandas as pd
import datetime
import time  # Para controlar las pausas de reintento contra el error 429
from google import genai  # Librería oficial de Google
from PIL import Image     # Para manejar la imagen que subas

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

# ==========================================
# 1. BASE DE DATOS (Se crea sola al arrancar)
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
        turno_seleccionado = st.radio("¿Qué turno vas a escanear/subir ahora?", ["Mañana", "Noche"], horizontal=True)
    
    st.subheader("📸 Subir Recuadro Diario")
    imagen_subida = st.file_uploader("Arrastra o selecciona la foto del recuadro diario", type=["png", "jpg", "jpeg"])
    
    if imagen_subida is not None:
        st.image(imagen_subida, caption="Imagen cargada correctamente", width=300)
        
        if st.button("🔍 Leer Recuadro con IA"):
            with st.spinner(f"Analizando minuciosamente el turno de la {turno_seleccionado}..."):
                try:
                    img = Image.open(imagen_subida)
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    
                    # PROMPT REFORZADO CON LA REGLA DE LA CELDA BRUTA CENTRADA
                    prompt_ocr = f"""
                    Analiza la imagen de este recuadro de caja de la tienda.
                    Estamos procesando el turno de la: **{turno_seleccionado}**.
                    
                    REGLAS DE EXTRACCIÓN SEVERAS:
                    1. ENCARGADO: Extrae única y exclusivamente el nombre de la persona que trabajó en el turno de la **{turno_seleccionado}**. Desecha el nombre del otro turno.
                    2. VENTA TOTAL (REGLA CRÍTICA DE CELDA CENTRADA): 
                       - Busca la cifra de "Venta Total" (importe bruto final acumulado). 
                       - IGNORA por completo el campo o fila que diga "Venta Neta" o "Base Imponible".
                       - REGLA DE CENTRADO: Si la casilla o celda de la "Venta Total" se encuentra físicamente centrada o unificada aplicando a todo el día entero (sin divisiones por líneas para mañana y noche), debes usar obligatoriamente ese mismo valor numérico tanto si te pedimos la Mañana como si te pedimos la **{turno_seleccionado}**. No saltes a otras celdas numéricas ni al año (2025/2026).
                    3. QUEBRANTO: Extrae el número del quebranto asignado a la **{turno_seleccionado}** (si viene con signo menos, mantén el valor negativo).
                    
                    Responde ÚNICAMENTE en este formato exacto, sin introducciones ni marcas de formato Markdown:
                    Tienda: [Debe ser exactamente uno de estos nombres: {', '.join(LISTA_TIENDAS)}]
                    Encargado: [Nombre del encargado de la {turno_seleccionado}]
                    Venta: [Número de la venta total sin símbolos]
                    Quebranto: [Número del quebranto de la {turno_seleccionado} sin símbolos]
                    """
                    
                    response_ocr = None
                    intentos = 0
                    tiempo_espera = 4
                    
                    while intentos < 5:
                        try:
                            response_ocr = client.models.generate_content(
                                model="gemini-2.5-flash-lite",
                                contents=[img, prompt_ocr]
                            )
                            break
                        except Exception as api_error:
                            if "429" in str(api_error):
                                intentos += 1
                                if intentos == 5:
                                    raise api_error
                                st.warning(f"Saturación de API (429). Esperando {tiempo_espera} segundos...")
                                time.sleep(tiempo_espera)
                                tiempo_espera += 4
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
                                if valor_limpio not in ["2025", "2026"] and valor_limpio.replace(".", "", 1).isdigit():
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
        tienda = st.selectbox("Selecciona tu Tienda", LISTA_TIENDAS, index=tienda_idx)
        encargado = st.text_input("Nombre del Encargado", value=st.session_state.encargado_detectado)
        
    with col_der:
        fecha = st.date_input("Fecha del Recuadro", datetime.date.today())
        venta = st.number_input("Venta Total del Turno (€)", min_value=0.0, step=10.0, value=st.session_state.venta_detectada)
        quebranto = st.number_input("Importe del Quebranto (€)", step=5.0, value=st.session_state.quebranto_detectado)

    if st.button("🚀 Procesar y Guardar Registro"):
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
# SECCIÓN: PANEL DEL PROPIETARIO (PROTEGIDO)
# ------------------------------------------
with pestaña_dueño:
    if not st.session_state.autenticado:
