import streamlit as st
import sqlite3
import pandas as pd
import datetime
from PIL import Image, ImageOps
import easyocr
import numpy as np
import re

# ==========================================
# 1. BASE DE DATOS (SQLite Local)
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

# Lista oficial de tus 6 tiendas reales
LISTA_TIENDAS = ["Dp Collado", "Dp Valdebebas", "Dp Paracuellos", "Dp Vicálvaro", "Dp Villanueva", "Dp Galapagar"]

# Cargar el lector OCR gratuito optimizando la memoria RAM del servidor
@st.cache_resource
def cargar_lector_ocr():
    # Cargamos el modelo solo para números y letras en español
    return easyocr.Reader(['es'], gpu=False)

try:
    reader = cargar_lector_ocr()
except:
    reader = None

# ==========================================
# 2. INTERFAZ WEB CON STREAMLIT
# ==========================================
st.set_page_config(page_title="Panel Cierres Diarios DP Madrid", page_icon="🍕", layout="wide")
st.title("🍕 Panel Cierres Diarios DP Madrid")
st.markdown("---")

pestaña_tiendas, pestaña_dueño = st.tabs(["📲 Envío de Tiendas", "👁️ Panel del Propietario"])

# ------------------------------------------
# SECCIÓN: ENVÍO DE TIENDAS (Lectura Automática Eficiente)
# ------------------------------------------
with pestaña_tiendas:
    st.header("Formulario de Cierre Diario Automático")
    
    tienda = st.selectbox("Selecciona tu Tienda", LISTA_TIENDAS)
    turno = st.radio("Turno Actual", ["Mañana", "Noche"], horizontal=True)
    fecha = st.date_input("Fecha del Recuadro", datetime.date.today())
    
    st.markdown("---")
    st.markdown("### 📸 Sube o haz la foto del recuadro diario")
    
    uploaded_file = st.file_uploader("Haz clic para activar la cámara o seleccionar imagen", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        st.markdown("### 👁️ Vista previa de la captura")
        imagen_pil = Image.open(uploaded_file)
        
        # --- TRUCO DE PRODUCTIVIDAD: COMPRESIÓN DE IMAGEN ---
        # Reducimos las dimensiones máximas a 800 píxeles para que consuma un 80% menos de memoria RAM
        imagen_pil.thumbnail((800, 800))
        st.image(imagen_pil, caption="Imagen optimizada para lectura automática", width=350)
        
        # Variables para almacenar lo que descubra la máquina
        encargado_detectado = ""
        venta_detectada = 0.0
        quebranto_detectado = 0.0
        
        if st.button("🔍 Iniciar Lectura Automática con IA Gratuita"):
            if reader is None:
                st.error("El lector de imágenes no se ha podido cargar en el servidor gratuito.")
            else:
                with st.spinner("Leyendo los números y textos de la foto de forma automática..."):
                    # Convertir a escala de grises y matriz matemática ligera
                    img_gris = ImageOps.grayscale(imagen_pil)
                    imagen_cv = np.array(img_gris)
                    
                    # Extraer las líneas de texto de la imagen
                    resultados_texto = reader.readtext(imagen_cv, detail=0)
                    texto_limpio = [linea.lower().strip() for linea in resultados_texto]
                    
                    # Algoritmo inteligente para buscar datos entre las líneas leídas
                    for i, linea in enumerate(texto_limpio):
                        # 1. Buscar el encargado
                        if "encargado" in linea or "nombre" in linea or "turno por" in linea:
                            if i + 1 < len(resultados_texto):
                                encargado_detectado = resultados_texto[i+1].strip()
                        
                        # 2. Buscar la venta total (buscando números decimales cerca de la palabra total)
                        if "total" in linea or "venta" in linea or "visa" in linea:
                            if i + 1 < len(texto_limpio):
                                texto_numero = re.sub(r'[^\d.,-]', '', texto_limpio[i+1])
                                try:
                                    texto_numero = texto_numero.replace(",", ".")
                                    venta_detectada = float(texto_numero)
                                except:
                                    pass
                        
                        # 3. Buscar el quebranto
                        if "quebranto" in linea or "descuadre" in linea or "diferencia" in linea:
                            if i + 1 < len(texto_limpio):
                                texto_quebranto = re.sub(r'[^\d.,-]', '', texto_limpio[i+1])
                                try:
                                    texto_quebranto = texto_quebranto.replace(",", ".")
                                    quebranto_detectado = float(texto_quebranto)
                                except:
                                    pass
                    
                    # Si no detectó nombre, dejamos uno genérico de la tienda para que lo vean
                    if encargado_detectado == "": encargado_detectado = "Encargado Detectado"
                    
                    # Guardamos provisionalmente en el estado de la web
                    st.session_state['encargado_auto'] = encargado_detectado
                    st.session_state['venta_auto'] = venta_detectada
                    st.session_state['quebranto_auto'] = quebranto_detectado
                    st.success("¡Lector automático finalizado con éxito!")

        # Recuperar los datos extraídos automáticamente
        val_encargado = st.session_state.get('encargado_auto', "")
        val_venta = st.session_state.get('venta_auto', 0.0)
        val_quebranto = st.session_state.get('quebranto_auto', 0.0)
        
        st.markdown("---")
        st.info("📝 **Filtro de seguridad:** Comprueba los datos extraídos automáticamente de tu foto antes de enviarlos a la base de datos:")
        
        # Se muestran en casillas automáticas rellenas por el OCR. El empleado solo tiene que mirar y darle al botón.
        encargado_final = st.text_input("Encargado leído por la máquina:", value=val_encargado)
        venta_final = st.number_input("Venta Total leída (€):", value=val_venta, min_value=0.0, step=0.01, format="%.2f")
        quebranto_final = st.number_input("Quebranto leído (€):", value=val_quebranto, step=0.01, format="%.2f")
        
        if st.button("🚀 Confirmar y Registrar Turno en la Base de Datos"):
            alerta = "OK"
            if quebranto_final <= -100:
                alerta = "🚨 CRÍTICO (Pérdida)"
            elif quebranto_final >= 100:
                alerta = "⚠️ ATENCIÓN (Exceso)"
            
            conn = sqlite3.connect("tiendas.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO recuadros (fecha, tienda, turno, encargado, venta_total, quebranto, estado_alerta)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (fecha.strftime("%Y-%m-%d"), tienda, turno, encargado_final, venta_final, quebranto_final, alerta))
            conn.commit()
            conn.close()
            
            st.success(f"¡Los datos automáticos de {tienda} han sido guardados perfectamente!")
            # Limpiar memoria
            if 'encargado_auto' in st.session_state: del st.session_state['encargado_auto']
            if 'venta_auto' in st.session_state: del st.session_state['venta_auto']
            if 'quebranto_auto' in st.session_state: del st.session_state['quebranto_auto']

# ------------------------------------------
# SECCIÓN: PANEL DEL PROPIETARIO
# ------------------------------------------
with pestaña_dueño:
    st.header("Histórico de Ventas y Quebrantos en Tiempo Real")
    
    conn = sqlite3.connect("tiendas.db")
    df = pd.read_sql_query("SELECT * FROM recuadros ORDER BY fecha DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("Aún no hay datos registrados por las tiendas.")
    else:
        st.markdown("### 🔍 Filtros de Búsqueda")
        opciones_filtro = ["Todas las tiendas"] + LISTA_TIENDAS
        tienda_filtrada = st.selectbox("Filtrar la información por local:", opciones_filtro)
        
        if tienda_filtrada != "Todas las tiendas":
            df_mostrar = df[df['tienda'] == tienda_filtrada]
        else:
            df_mostrar = df

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Ventas", f"{df_mostrar['venta_total'].sum():,.2f} €")
        c2.metric("Balance Quebrantos", f"{df_mostrar['quebranto'].sum():,.2f} €")
        c3.metric("Alertas Críticas", len(df_mostrar[df_mostrar['estado_alerta'] != "OK"]))
        
        st.markdown("---")
        st.markdown(f"### 📋 Registros de: {tienda_filtrada}")
        st.dataframe(df_mostrar, width="stretch")
