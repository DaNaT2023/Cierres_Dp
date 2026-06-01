import streamlit as st
import sqlite3
import pandas as pd
import datetime
import time

# ==========================================
# 0. CONFIGURACIÓN DE TUS 6 TIENDAS REALES
# ==========================================
LISTA_TIENDAS = ["Dp Valdebebas", "Dp Collado", "Dp Paracuellos", "Dp Villanueva", "Dp Galapagar", "Dp Vicálvaro"]

# ==========================================
# 1. BASE DE DATOS LOCAL
# ==========================================
def inicializar_bd():
    conexion = sqlite3.connect("tiendas.db")
    cursor = conexion.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recuadros (
            id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, tienda TEXT, turno TEXT, encargado TEXT,
            venta_neta REAL, venta_total REAL, venta_2025 REAL, venta_entrega REAL, venta_llevar REAL,
            venta_ventana REAL, venta_come_bebe REAL, venta_visa REAL, venta_efectivo REAL, venta_pluxee REAL,
            quebranto REAL, ingreso_prosegur REAL, web REAL, tgtg REAL, uber_eats REAL, glovo REAL, just_eat REAL, estado_alerta TEXT
        )
    """)
    conexion.commit()
    conexion.close()

inicializar_bd()

# CONFIGURACIÓN BÁSICA DE PÁGINA
st.set_page_config(page_title="Panel Cierre Diario Dp", layout="wide")
st.title("🍕 Panel Cierre Diario Dp")
st.markdown("---")

pestaña_tiendas, pestaña_dueño = st.tabs(["📲 Envío de Tiendas", "👁️ Panel del Propietario"])

# ------------------------------------------
# SECCIÓN: ENVÍO DE TIENDAS
# ------------------------------------------
with pestaña_tiendas:
    st.header("📝 Formulario Manual Cierre de Turno")
    turno_seleccionado = st.radio("¿Qué turno vas a registrar?", ["Mañana", "Noche"], horizontal=True, key="sel_turno")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("📌 Datos del Turno")
        tienda = st.selectbox("Tienda", LISTA_TIENDAS, key="f_tienda")
        encargado = st.text_input("Nombre del Encargado", placeholder="Escribe tu nombre", key="f_enc")
        fecha = st.date_input("Fecha del Cierre", value=datetime.date.today(), key="f_fecha")
        st.subheader("💰 Totales Caja")
        venta_neta = st.number_input("Venta Neta (€)", min_value=0.0, step=10.0, key="f_vn")
        venta = st.number_input("Venta Total / Bruta (€)", min_value=0.0, step=10.0, key="f_vt")
        venta_2025 = st.number_input("Venta 2025 (€)", min_value=0.0, step=10.0, key="f_v25")
    with col2:
        st.subheader("🛵 Desglose Canales")
        venta_entrega = st.number_input("Venta Entrega (€)", min_value=0.0, step=10.0, key="f_ve")
        venta_llevar = st.number_input("Venta Llevar (€)", min_value=0.0, step=10.0, key="f_vll")
        venta_ventana = st.number_input("Venta Ventana (€)", min_value=0.0, step=10.0, key="f_vv")
        venta_come_bebe = st.number_input("Venta Come & Bebe / Sala (€)", min_value=0.0, step=10.0, key="f_vcb")
        st.subheader("💳 Métodos de Pago")
        venta_visa = st.number_input("Venta VISA / Tarjeta (€)", min_value=0.0, step=10.0, key="f_vvi")
        venta_efectivo = st.number_input("Venta en Efectivo (€)", min_value=0.0, step=10.0, key="f_vef")
    with col3:
        st.subheader("📉 Descuadres")
        venta_pluxee = st.number_input("Pluxee Gourmet (€)", min_value=0.0, step=10.0, key="f_vp")
        quebranto = st.number_input("Quebranto (€) [Usa - para pérdidas]", value=0.0, step=5.0, key="f_q")
        ingresado_prosegur = st.number_input("Ingreso Prosegur (€)", min_value=0.0, step=10.0, key="f_pro")
        st.subheader("🌐 Agregadores y Online")
        web = st.number_input("Web (€)", min_value=0.0, step=10.0, key="f_web")
        tgtg = st.number_input("TGTG (€)", min_value=0.0, step=5.0, key="f_tg")
        uber_eats = st.number_input("Uber Eats (€)", min_value=0.0, step=10.0, key="f_ub")
        glovo = st.number_input("Glovo (€)", min_value=0.0, step=10.0, key="f_gl")
        just_eat = st.number_input("Just Eat (€)", min_value=0.0, step=10.0, key="f_je")

    st.markdown("---")
    if st.button("🚀 Guardar Registro del Turno", key="btn_guardar", use_container_width=True):
        if encargado.strip() == "":
            st.error("Por favor, introduce el nombre del encargado para poder guardar el cierre.")
        else:
            alerta = "OK"
            if quebranto <= -100: alerta = "🚨 CRÍTICO (Pérdida)"
            elif quebranto >= 100: alerta = "⚠️ ATENCIÓN (Exceso)"
                
            conn = sqlite3.connect("tiendas.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO recuadros (
                    fecha, tienda, turno, encargado, venta_neta, venta_total, venta_2025,
                    venta_entrega, venta_llevar, venta_ventana, venta_come_bebe, venta_visa,
                    venta_efectivo, venta_pluxee, quebranto, ingreso_prosegur, web, tgtg, uber_eats, glovo, just_eat, estado_alerta
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fecha.strftime("%Y-%m-%d"), tienda, turno_seleccionado, encargado, venta_neta, venta, venta_2025,
                venta_entrega, venta_llevar, venta_ventana, venta_come_bebe, venta_visa,
                venta_efectivo, venta_pluxee, quebranto, ingresado_prosegur, web, tgtg, uber_eats, glovo, just_eat, alerta
            ))
            conn.commit()
            conn.close()
            st.success("¡El cierre se ha guardado correctamente!")
            time.sleep(1)
            st.rerun()

# ------------------------------------------
# SECCIÓN: PANEL DEL PROPIETARIO (VISTA LIMPIA Y FORMATEADA)
# ------------------------------------------
with pestaña_dueño:
    st.subheader("📊 Resumen General de Cierres")
    
    conn = sqlite3.connect("tiendas.db")
    df = pd.read_sql_query("SELECT * FROM recuadros ORDER BY fecha DESC, id DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("Aún no se han registrado cierres en la base de datos.")
    else:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            tiendas_filtro = st.multiselect("Filtrar por Tienda:", options=LISTA_TIENDAS, default=LISTA_TIENDAS)
        with col_f2:
            alertas_disponibles = list(df['estado_alerta'].unique())
            alertas_filtro = st.multiselect("Filtrar por Estado de Alerta:", options=alertas_disponibles, default=alertas_disponibles)
        
        # Filtrado base
        df_filtrado = df[df['tienda'].isin(tiendas_filtro) & df['estado_alerta'].isin(alertas_filtro)]
        
        # Ocultamos los desgloses irrelevantes para el dueño
        columnas_a_eliminar = [
            'web', 'tgtg', 'uber_eats', 'glovo', 'just_eat', 
            'venta_entrega', 'venta_llevar', 'venta_ventana', 'venta_come_bebe'
        ]
        df_vista = df_filtrado.drop(columns=[col for col in columnas_a_eliminar if col in df_filtrado.columns])
        
        # Renombramos etiquetas para la cabecera de la tabla
        columnas_nuevas_etiquetas = {
            'id': 'ID', 'fecha': 'Fecha', 'tienda': 'Tienda', 'turno': 'Turno', 'encargado': 'Encargado',
            'venta_neta': 'Venta Neta', 'venta_total': 'Venta Bruta', 'venta_2025': 'Venta 2025',
            'venta_visa': 'Tarjeta', 'venta_efectivo': 'Efectivo', 'venta_pluxee': 'Pluxee',
            'quebranto': 'Quebranto', 'ingreso_prosegur': 'Prosegur', 'estado_alerta': 'Estado'
        }
        df_vista = df_vista.rename(columns=columnas_nuevas_etiquetas)
        
        # Métricas principales superiores
        st.markdown("### 📈 Métricas del Grupo")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Venta Bruta Total", f"{df_filtrado['venta_total'].sum():,.2f} €")
        with col_m2:
            st.metric("Balance de Quebrantos", f"{df_filtrado['quebranto'].sum():,.2f} €")
        with col_m3:
            st.metric("Turnos Registrados", f"{len(df_filtrado)}")
        
        st.markdown("---")
        st.subheader("📋 Tabla Histórica de Cierres")
        
        # Aplicamos el formato de moneda (€) solo a las columnas de dinero en la visualización
        st.dataframe(
            df_vista, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Venta Neta": st.column_config.NumberColumn(format="%.2f €"),
                "Venta Bruta": st.column_config.NumberColumn(format="%.2f €"),
                "Venta 2025": st.column_config.NumberColumn(format="%.2f €"),
                "Tarjeta": st.column_config.NumberColumn(format="%.2f €"),
                "Efectivo": st.column_config.NumberColumn(format="%.2f €"),
                "Pluxee": st.column_config.NumberColumn(format="%.2f €"),
                "Quebranto": st.column_config.NumberColumn(format="%.2f €"),
                "Prosegur": st.column_config.NumberColumn(format="%.2f €"),
            }
        )
