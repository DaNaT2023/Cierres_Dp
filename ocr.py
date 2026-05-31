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

# Inicializar variables en el estado de la sesión para evitar fallos de lectura
if "tienda_detectada" not in st.session_state:
    st.session_state.tienda_detectada = "Dp Valdebebas"
if "turno_detectado" not in st.session_state:
    st.session_state.turno_detectado = "Mañana"
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
    
    st.subheader("📸 Subir Recuadro Diario")
    imagen_subida = st.file_uploader("Arrastra o selecciona la foto del recuadro diario", type=["png", "jpg", "jpeg"])
    
    if imagen_subida is not None:
        st.image(imagen_subida, caption="Imagen cargada correctamente", width=300)
        
        if st.button("🔍 Leer Recuadro con IA"):
            with st.spinner("Analizando detalladamente el recuadro..."):
                try:
                    img = Image.open(imagen_subida)
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    
                    # REGLAS REFORZADAS CONTRA EL AÑO Y MEZCLA DE ENCARGADOS
                    prompt_ocr = f"""
                    Analiza la imagen de este recuadro de caja e identifica el turno ("Mañana" o "Noche").
                    Extrae estrictamente los siguientes datos basándote en el turno detectado:
                    
                    REGLAS OPERATIVAS OBLIGATORIAS:
                    1. ENCARGADO: Asegúrate de leer el nombre del encargado específico del turno analizado. Si estás procesando la "Noche", busca el nombre escrito en la sección de la noche o en la segunda línea de personal. No pongas el de la mañana.
                    2. VENTA TOTAL: Busca el valor de la VENTA TOTAL (bruta/final con impuestos). 
                       - PROHIBIDO EXTRAER EL AÑO: No confundas el año "2025" o "2026" de la fecha con la venta. Si el valor es exactamente igual al año en curso, descártalo y busca la cifra de dinero real.
                       - IGNORA por completo el campo "venta neta".
                    3. CIFRAS CENTRADAS: Si una cifra (como la venta o quebranto) está en una celda unificada que abarca todo el día, asígnala por igual a este turno.
                    
                    Responde ÚNICAMENTE en este formato exacto, sin textos adicionales y sin bloques de código ```:
                    Tienda: [Debe ser exactamente uno de estos nombres: {', '.join(LISTA_TIENDAS)}]
                    Turno: [Mañana o Noche]
                    Encargado: [Nombre del encargado correcto de este turno]
                    Venta: [Número de la venta total sin símbolos]
                    Quebranto: [Número del quebranto, si es negativo mantén el signo menos, sin símbolos]
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
                            elif clave == "turno":
                                st.session_state.turno_detectado = "Noche" if "noche" in valor.lower() else "Mañana"
                            elif clave == "encargado":
                                st.session_state.encargado_detectado = valor
                            elif clave == "venta":
                                valor_limpio = valor.replace("€", "").replace(" ", "").replace(",", ".")
                                # Validación extra para descartar el año si la IA se despista
                                if valor_limpio in ["2025", "2026"]:
                                    continue
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
        
    turno_idx = 0 if st.session_state.turno_detectado == "Mañana" else 1
    
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        tienda = st.selectbox("Selecciona tu Tienda", LISTA_TIENDAS, index=tienda_idx)
        turno = st.radio("Turno Actual", ["Mañana", "Noche"], index=turno_idx)
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
        st.write("Por favor, introduce tus credenciales para poder ver la tabla de registros.")
        
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
