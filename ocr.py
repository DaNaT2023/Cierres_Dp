import streamlit as st
import sqlite3
import pandas as pd
import datetime
import time
import base64
import io

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

# ==========================================
# 1. BASE DE DATOS LOCAL COMPLETA
# ==========================================
def inicializar_bd():
    conexion = sqlite3.connect("pizzerias.db")
    cursor = conexion.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recuadros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            tienda TEXT,
            turno TEXT,
            encargado TEXT,
            total_pedidos INTEGER,
            deliverys INTEGER,
            venta_neta REAL,
            venta_total REAL,
            venta_2025 REAL,
            venta_entrega REAL,
            venta_llevar REAL,
            venta_ventana REAL,
            venta_come_bebe REAL,
            venta_visa REAL,
            venta_efectivo REAL,
            quebranto REAL,
            ingreso_prosegur REAL,
            produccion_real REAL,
            espera_rack TEXT,
            media_reparto TEXT,
            pedidos_mas_45 INTEGER,
            pedidos_mas_10_min INTEGER,
            web REAL,
            tgtg REAL,
            uber_eats REAL,
            glovo REAL,
            just_eat REAL,
            cancelados_motivo TEXT,
            estado_alerta TEXT
        )
    """)
    conexion.commit()
    conexion.close()

inicializar_bd()

# ==========================================
# 2. CONFIGURACIÓN DE PÁGINA E ICONO CORPORATIVO
# ==========================================
try:
    from PIL import Image
    img_logo = Image.open("logo.png")
    st.set_page_config(page_title="Panel Cierre Diario Dp", page_icon=img_logo, layout="wide")
except:
    st.set_page_config(page_title="Panel Cierre Diario Dp", layout="wide")
    img_logo = None

def obtener_imagen_base64(ruta_imagen):
    try:
        with open(ruta_imagen, "rb") as archivo_img:
            return base64.b64encode(archivo_img.read()).decode()
    except:
        return None

logo_base64 = obtener_imagen_base64("logo.png")

if logo_base64:
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: -10px; margin-top: -30px;">
            <img src="data:image/png;base64,{logo_base64}" width="60" style="object-fit: contain;">
            <h1 style="margin: 0; padding: 0; font-size: 2.5rem; font-weight: 700; color: #31333F; line-height: 60px;">Panel Cierre Diario Dp</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.title("🍕 Panel Cierre Diario Dp")

st.markdown("---")

pestaña_tiendas, pestaña_dueño = st.tabs(["📲 Envío de Tiendas", "👁️ Panel del Propietario"])

# ------------------------------------------
# SECCIÓN: ENVÍO DE TIENDAS (FORMULARIO MANUAL)
# ------------------------------------------
with pestaña_tiendas:
    st.header("📝 Formulario Manual Cierre de Turno")
    
    turno_seleccionado = st.radio("¿Qué turno vas a registrar?", ["Mañana", "Noche"], horizontal=True, key="selector_turno_superior")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📌 Datos del Turno")
        tienda = st.selectbox("Tienda", LISTA_TIENDAS, key="combo_tiendas_formulario")
        encargado = st.text_input("Nombre del Encargado", placeholder="Escribe tu nombre", key="input_encargado_formulario")
        fecha = st.date_input("Fecha del Cierre", value=datetime.date.today(), key="input_fecha_formulario")
        
        st.subheader("📊 Métricas Operativas")
        total_pedidos = st.number_input("Total Pedidos", min_value=0, value=0, step=1, key="input_tp_formulario")
        deliverys = st.number_input("Deliverys", min_value=0, value=0, step=1, key="input_del_formulario")
        produccion_real = st.number_input("Producción Real (€)", min_value=0.0, value=0.0, step=10.0, key="input_pr_formulario")
        
        st.subheader("💰 Totales de Caja")
        venta_neta = st.number_input("Venta Neta (€)", min_value=0.0, value=0.0, step=10.0, key="input_vn_formulario")
        venta = st.number_input("Venta Total / Bruta (€)", min_value=0.0, value=0.0, step=10.0, key="input_vt_formulario")
        venta_2025 = st.number_input("Venta 2025 (€)", min_value=0.0, value=0.0, step=10.0, key="input_v25_formulario")

    with col2:
        st.subheader("🛵 Desglose Canales")
        venta_entrega = st.number_input("Venta Entrega (€)", min_value=0.0, value=0.0, step=10.0, key="input_ve_formulario")
        venta_llevar = st.number_input("Venta Llevar (€)", min_value=0.0, value=0.0, step=10.0, key="input_vll_formulario")
        venta_ventana = st.number_input("Venta Ventana (€)", min_value=0.0, value=0.0, step=10.0, key="input_vv_formulario")
        venta_come_bebe = st.number_input("Venta Come & Bebe (€)", min_value=0.0, value=0.0, step=10.0, key="input_vcb_formulario")
        
        st.subheader("💳 Métodos de Pago")
        venta_visa = st.number_input("Venta VISA / Tarjeta (€)", min_value=0.0, value=0.0, step=10.0, key="input_vvi_formulario")
        venta_efectivo = st.number_input("Venta en Efectivo (€)", min_value=0.0, value=0.0, step=10.0, key="input_vef_formulario")
        venta_pluxee = st.number_input("Pluxee Gourmet (€)", min_value=0.0, value=0.0, step=10.0, key="input_vp_formulario")

    with col3:
        st.subheader("⏱️ Tiempos y Alertas")
        espera_rack = st.text_input("Espera Rack (Ej. 3:45)", value="0:00", key="input_rack_formulario")
        media_reparto = st.text_input("Media Reparto (Ej. 22:15)", value="0:00", key="input_reparto_formulario")
        pedidos_mas_45 = st.number_input("Pedidos +45%", min_value=0, value=0, step=1, key="input_p45_formulario")
        pedidos_mas_10_min = st.number_input("Pedidos > 10 min", min_value=0, value=0, step=1, key="input_p10_formulario")
        
        st.subheader("📉 Descuadres y Canales Online")
        quebranto = st.number_input("Quebranto (€) [Usa - para pérdidas]", value=0.0, step=5.0, key="input_quebranto_formulario")
        ingreso_prosegur = st.number_input("Ingreso Prosegur (€)", min_value=0.0, value=0.0, step=10.0, key="input_pro_formulario")
        web = st.number_input("Web (€)", min_value=0.0, value=0.0, step=10.0, key="input_web_formulario")
        tgtg = st.number_input("TGTG (€)", min_value=0.0, value=0.0, step=5.0, key="input_tgtg_formulario")
        uber_eats = st.number_input("Uber Eats (€)", min_value=0.0, value=0.0, step=10.0, key="input_uber_formulario")
        glovo = st.number_input("Glovo (€)", min_value=0.0, value=0.0, step=10.0, key="input_glovo_formulario")
        just_eat = st.number_input("Just Eat (€)", min_value=0.0, value=0.0, step=10.0, key="input_je_formulario")
        
        st.subheader("🚨 Incidencias")
        cancelados_motivo = st.text_area("Cancelados - Motivo", placeholder="Escribe aquí los motivos...", key="input_cancelados_formulario")

    st.markdown("---")
    if st.button("🚀 Guardar Registro del Turno", key="btn_guardar_registro_bd", use_container_width=True):
        if encargado.strip() == "":
            st.error("Por favor, introduce el nombre del encargado para poder guardar el cierre.")
        else:
            alerta = "OK"
            if quebranto <= -100:
                alerta = "🚨 CRÍTICO (Pérdida)"
            elif quebranto >= 100:
                alerta = "⚠️ ATENCIÓN (Exceso)"
                
            conexion_guardar = sqlite3.connect("pizzerias.db")
            cursor = conexion_guardar.cursor()
            cursor.execute("""
                INSERT INTO recuadros (
                    fecha, tienda, turno, encargado, total_pedidos, deliverys, venta_neta, 
                    venta_total, venta_2025, venta_entrega, venta_llevar, venta_ventana, 
                    venta_come_bebe, venta_visa, venta_efectivo, quebranto, ingreso_prosegur, 
                    produccion_real, espera_rack, media_reparto, pedidos_mas_45, pedidos_mas_10_min, 
                    web, tgtg, uber_eats, glovo, just_eat, cancelados_motivo, estado_alerta
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fecha.strftime("%Y-%m-%d"), tienda, turno_seleccionado, encargado, total_pedidos, deliverys, venta_neta,
                venta, venta_2025, venta_entrega, venta_llevar, venta_ventana, venta_come_bebe, venta_visa,
                venta_efectivo, quebranto, ingreso_prosegur, produccion_real, espera_rack, media_reparto,
                pedidos_mas_45, pedidos_mas_10_min, web, tgtg, uber_eats, glovo, just_eat, cancelados_motivo, alerta
            ))
            conexion_guardar.commit()
            conexion_guardar.close()
            
            st.success(f"¡El cierre de {tienda} ({turno_seleccionado}) se ha guardado correctamente!")
            time.sleep(1)
            st.rerun()

# ------------------------------------------
# SECCIÓN: PANEL DEL PROPIETARIO (FILTROS ESTABLES)
# ------------------------------------------
with pestaña_dueño:
    st.subheader("📊 Resumen General de Cierres")
    
    conexion_leer = sqlite3.connect("pizzerias.db")
    df = pd.read_sql_query("SELECT * FROM recuadros ORDER BY fecha DESC, id DESC", conexion_leer)
    conexion_leer.close()
    
    if df.empty:
        st.warning("📥 Base de datos vacía. Envía el primer turno desde la pestaña anterior para activar el histórico.")
    else:
        # FILTROS ROBUSTOS: Selector único y caja de búsqueda para evitar conflictos visuales
        opciones_tiendas_filtro = ["Todas las Tiendas"] + LISTA_TIENDAS
