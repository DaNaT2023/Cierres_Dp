import streamlit as st
import sqlite3
import pandas as pd
import datetime
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

# === ENMASCARAMIENTO OPERATIVO DE MEMORIA PERSISTENTE CONTRA REINICIOS ===
if "bd_inicializada" not in st.session_state:
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
    st.session_state.bd_inicializada = True

# Inicializar variables de intercambio del formulario
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
            with st.spinner(f"Analizando detalladamente el turno de la {turno_seleccionado}..."):
                try:
                    img = Image.open(imagen_subida)
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    
                    prompt_ocr = f"""
                    Analiza la imagen de este recuadro de caja de la tienda.
                    Estamos procesando exclusivamente el turno de la **{turno_seleccionado}**.
                    
                    REGLAS DE EXTRACCIÓN OBLIGATORIAS:
                    1. ENCARGADO: Busca la fila o celda correspondiente a la **{turno_seleccionado}** y extrae el nombre de la persona asignada a ese horario. Ignora por completo al encargado del otro turno.
                    2. VENTA TOTAL: Extrae la cifra de la Venta Total (Bruta, final con IVA) de la fila de la **{turno_seleccionado}**. 
                       - Si la cifra de la venta está en una celda unificada/centrada que abarca todo el día, extrae esa.
                       - IGNORA el año de la fecha (2025/2026), no lo confundas con la venta.
                       - IGNORA la venta neta.
                    3. QUEBRANTO: Extrae el importe de quebranto de la **{turno_seleccionado}** (si es negativo, mantén el signo menos).
                    
                    Responde ÚNICAMENTE en este formato exacto, sin textos adicionales y sin marcas de formato:
                    Tienda: [Debe ser exactamente uno de estos nombres: {', '.join(LISTA_TIENDAS)}]
                    Encargado: [Nombre del encargado de la {turno_seleccionado}]
                    Venta: [Número de la venta total sin símbolos]
                    Quebranto: [Número del quebranto de la {turno_seleccionado} sin símbolos]
                    """
                    
                    response_ocr = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[img, prompt_ocr]
                    )
                    
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
        turno = st.radio("Turno Actual", ["Mañana", "Noche"], index=0 if turno_seleccionado == "Mañana" else 1)
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
            """, (fecha.strftime("%Y-%m-%d"), tienda, turno, encargado, venta, quebranto, alerta))
            conn.commit()
            conn.close()
            
            st.success(f"¡Datos de {tienda} ({turno}) guardados con éxito!")
            
            st.session_state.encargado_detectado = ""
            st.session_state.venta_detectada = 0.0
            st.session_state.quebranto_detectado = 0.0
            st.rerun()

# ------------------------------------------
# SECCIÓN: PANEL DEL PROPIETARIO (PROTEGIDO)
# ------------------------------------------
with pestaña_dueño:
    if not st.session_state.autenticado:
        st.subheader("🔒 Acceso Restringido al Propietario")
        st.write("Introduce tus credenciales para ver la tabla histórica y acceder a las funciones de borrado o modificación.")
        
        c_log1, c_log2 = st.columns(2)
        with c_log1:
            input_usuario = st.text_input("Usuario", key="login_user")
        with c_log2:
            input_password = st.text_input("Contraseña", type="password", key="login_pass")
            
        if st.button("🔓 Entrar al Panel"):
            if input_usuario == st.secrets["ADMIN_USER"] and input_password == st.secrets["ADMIN_PASSWORD"]:
                st.session_state.autenticado = True
                st.success("¡Autenticación correcta!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
    else:
        if st.button("🔒 Cerrar Sesión (Ocultar Todo)"):
            st.session_state.autenticado = False
            st.rerun()
            
        st.header("Histórico de Ventas y Quebrantos en Tiempo Real")
        
        # Conexión directa a la base de datos compartida
        conn = sqlite3.connect("tiendas.db")
