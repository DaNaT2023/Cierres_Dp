import streamlit as st
import sqlite3
import pandas as pd
import datetime
from PIL import Image
import easyocr
import numpy as np

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

@st.cache_resource
def cargar_lector_ocr():
    return easyocr.Reader(['es'])

reader = cargar_lector_ocr()

# ==========================================
# 2. INTERFAZ WEB CON STREAMLIT
# ==========================================
# Añadimos también la pizza como icono de la pestaña del navegador
st.set_page_config(page_title="Panel Cierres Diarios DP Madrid", page_icon="🍕", layout="wide")

# Modificamos el título principal con tu nombre personalizado y el icono de pizza
st.title("🍕 Panel Cierres Diarios DP Madrid")
st.markdown("---")

pestaña_tiendas, pestaña_dueño = st.tabs(["📲 Envío de Tiendas", "👁️ Panel del Propietario"])

# ------------------------------------------
# SECCIÓN: ENVÍO DE TIENDAS
# ------------------------------------------
with pestaña_tiendas:
    st.header("Formulario de Cierre con Lectura de Captura")
    
    tienda = st.selectbox("Selecciona tu Tienda", LISTA_TIENDAS)
    turno = st.radio("Turno Actual", ["Mañana", "Noche"], horizontal=True)
    fecha = st.date_input("Fecha del Recuadro", datetime.date.today())
    
    st.markdown("---")
    st.markdown("### 📸 Sube la captura del recuadro diario")
    
    uploaded_file = st.file_uploader("Elige una imagen o arrástrala aquí", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        st.markdown("### 👁️ Vista previa del recuadro")
        imagen_pil = Image.open(uploaded_file)
        st.image(imagen_pil, caption="Captura lista para procesar", width=400)
        
        if st.button("🚀 Leer Captura y Guardar en la Base de Datos"):
            with st.spinner("El sistema gratuito está analizando el texto de la imagen..."):
                
                imagen_cv = np.array(imagen_pil)
                resultados_texto = reader.readtext(imagen_cv, detail=0)
                texto_limpio = [linea.lower().strip() for linea in resultados_texto]
                
                encargado_detectado = "Desconocido"
                venta_detectada = 0.0
                quebranto_detectada = 0.0
                
                for i, linea in enumerate(texto_limpio):
                    if "encargado" in linea or "nombre" in linea:
                        if i + 1 < len(resultados_texto):
                            encargado_detectado = resultados_texto[i+1]
                    
                    if "total" in linea or "venta" in linea:
                        if i + 1 < len(texto_limpio):
                            try:
                                valor = texto_limpio[i+1].replace("€", "").replace(",", ".").strip()
                                venta_detectada = float(valor)
                            except:
                                pass
                                
                    if "quebranto" in linea:
                        if i + 1 < len(texto_limpio):
                            try:
                                valor = texto_limpio[i+1].replace("€", "").replace(",", ".").strip()
                                quebranto_detectada = float(valor)
                            except:
                                pass

                alerta = "OK"
                if quebranto_detectada <= -100:
                    alerta = "🚨 CRÍTICO (Pérdida)"
                elif quebranto_detectada >= 100:
                    alerta = "⚠️ ATENCIÓN (Exceso)"
                
                conn = sqlite3.connect("tiendas.db")
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO recuadros (fecha, tienda, turno, encargado, venta_total, quebranto, estado_alerta)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (fecha.strftime("%Y-%m-%d"), tienda, turno, encargado_detectado, venta_detectada, quebranto_detectada, alerta))
                conn.commit()
                conn.close()
                
                st.success(f"¡Procesado! Detectado: Encargado ({encargado_detectado}), Venta ({venta_detectada}€), Quebranto ({quebranto_detectada}€)")

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
        
        st.markdown("---")
        with st.expander("⚙️ Zona de Administración (Borrar datos)"):
            st.warning("Cuidado: Al pulsar el botón eliminarás permanentemente los registros.")
            
            id_a_borrar = st.number_input("Introduce el ID del registro que quieres borrar:", min_value=1, step=1)
            
            if st.button("🗑️ Borrar este registro único"):
                conn = sqlite3.connect("tiendas.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM recuadros WHERE id = ?", (id_a_borrar,))
                conn.commit()
                conn.close()
                st.success(f"¡Registro con ID {id_a_borrar} eliminado! Recarga la página para actualizar.")
                
            st.markdown("---")
            if st.button("🚨 BORRAR ABSOLUTAMENTE TODOS LOS DATOS"):
                conn = sqlite3.connect("tiendas.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM recuadros")
                conn.commit()
                conn.close()
                st.success("¡Base de datos completamente vaciada!")
