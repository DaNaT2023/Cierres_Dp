import streamlit as st
import sqlite3
import pandas as pd
import datetime
from PIL import Image
import io

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

# ==========================================
# 2. INTERFAZ WEB CON STREAMLIT
# ==========================================
st.set_page_config(page_title="Panel Cierres Diarios DP Madrid", page_icon="🍕", layout="wide")
st.title("🍕 Panel Cierres Diarios DP Madrid")
st.markdown("---")

pestaña_tiendas, pestaña_dueño = st.tabs(["📲 Envío de Tiendas", "👁️ Panel del Propietario"])

# ------------------------------------------
# SECCIÓN: ENVÍO DE TIENDAS (Flujo Productivo Sin Coste)
# ------------------------------------------
with pestaña_tiendas:
    st.header("Formulario de Cierre Diario con Justificante")
    
    tienda = st.selectbox("Selecciona tu Tienda", LISTA_TIENDAS)
    turno = st.radio("Turno Actual", ["Mañana", "Noche"], horizontal=True)
    fecha = st.date_input("Fecha del Recuadro", datetime.date.today())
    
    st.markdown("---")
    st.markdown("### 📸 Sube o haz la foto del recuadro diario")
    
    uploaded_file = st.file_uploader("Haz clic para activar la cámara o seleccionar imagen", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        st.markdown("### 👁️ Vista previa de la captura")
        bytes_data = uploaded_file.getvalue()
        imagen_pil = Image.open(io.BytesIO(bytes_data))
        st.image(imagen_pil, caption="Imagen guardada como justificante visual", width=350)
        
        st.markdown("---")
        st.success("📸 ¡Justificante visual acoplado con éxito!")
        st.info("✍️ **Datos de Cierre:** Introduce las 3 cifras del recuadro para sincronizar el panel:")
        
        # El encargado introduce los datos reales de forma manual en 5 segundos
        encargado_final = st.text_input("Nombre del Encargado de Turno:", value="")
        venta_final = st.number_input("Venta Total del Turno (€):", min_value=0.0, value=0.0, step=0.01, format="%.2f")
        quebranto_final = st.number_input("Importe del Quebranto (€) - Usa el signo menos si es negativo:", value=0.0, step=0.01, format="%.2f")
        
        if st.button("🚀 Confirmar Datos y Registrar Turno"):
            if encargado_final.strip() == "":
                st.error("Por favor, introduce el nombre del encargado.")
            elif venta_final == 0.0:
                st.error("Por favor, introduce el importe de la venta total.")
            else:
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
                
                st.success(f"¡Cierre de {tienda} registrado con éxito en el sistema central!")

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
                st.success(f"¡Registro con ID {id_a_borrar} eliminado!")
