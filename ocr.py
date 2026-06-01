import streamlit as st
import pandas as pd
import datetime
import time
import base64
import requests

# ==========================================
# 0. CONFIGURACIÓN DE TUS 6 TIENDAS REALES
# ==========================================
LISTA_TIENDAS = ["Dp Valdebebas", "Dp Collado", "Dp Paracuellos", "Dp Villanueva", "Dp Galapagar", "Dp Vicálvaro"]

# CONFIGURACIÓN BÁSICA DE PÁGINA
st.set_page_config(page_title="Panel Cierre Diario Dp", layout="wide")

# Cargar Logo Corporativo si existe
def obtener_logo_base64(ruta_imagen):
    try:
        with open(ruta_imagen, "rb") as archivo_img:
            return base64.b64encode(archivo_img.read()).decode()
    except Exception:
        return None

logo_codificado = obtener_logo_base64("logo.png")

if logo_codificado:
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 18px; margin-bottom: 15px; margin-top: -15px;">
            <img src="data:image/png;base64,{logo_codificado}" width="65" style="object-fit: contain; border-radius: 4px;">
            <h1 style="margin: 0; padding: 0; font-size: 2.3rem; font-weight: 700; color: #31333F;">Panel Cierre Diario Dp</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
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
            
            # CONTROL DE SEGURIDAD CORREGIDO: Extrae la URL de forma segura si existe
            url_form = st.secrets.get("URL_GOOGLE_FORM", "https://google.com")
            url_limpia = "".join(url_form.split())
            
            payload = {
                "entry.1000001": fecha.strftime("%Y-%m-%d"), "entry.1000002": tienda, "entry.1000003": turno_seleccionado, "entry.1000004": encargado,
                "entry.1000005": str(venta_neta), "entry.1000006": str(venta), "entry.1000007": str(venta_2025),
                "entry.1000008": str(venta_entrega), "entry.1000009": str(venta_llevar), "entry.1000010": str(venta_ventana), "entry.1000011": str(venta_come_bebe),
                "entry.1000012": str(venta_visa), "entry.1000013": str(venta_efectivo), "entry.1000014": str(venta_pluxee),
                "entry.1000015": str(quebranto), "entry.1000016": str(ingresado_prosegur), "entry.1000017": str(web), "entry.1000018": str(tgtg),
                "entry.1000019": str(uber_eats), "entry.1000020": str(glovo), "entry.1000021": str(just_eat), "entry.1000022": alerta
            }
            
            try:
                respuesta = requests.post(url_limpia, data=payload)
                st.success("🚀 ¡El cierre se ha enviado y guardado directamente en tu Google Sheets!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error al enviar los datos: {e}")

# ------------------------------------------
# SECCIÓN: PANEL DEL PROPIETARIO
# ------------------------------------------
with pestaña_dueño:
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.subheader("🔒 Acceso Restringido para Dirección")
        input_usuario = st.text_input("Usuario", key="l_user")
        input_password = st.text_input("Contraseña", type="password", key="l_pass")
        
        if st.button("🔓 Entrar al Panel", key="btn_auth", use_container_width=True):
            if input_usuario == st.secrets["ADMIN_USER"] and input_password == st.secrets["ADMIN_PASSWORD"]:
                st.session_state.autenticado = True
                st.success("¡Acceso concedido!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
        st.stop()

    col_header, col_logout = st.columns(2)
    with col_header:
        st.subheader("📊 Enlaces de Control de Dirección")
    with col_logout:
        if st.button("🔒 Salir", key="btn_logout", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()
            
    st.markdown("---")
    st.markdown("### 📋 Gestión y Visualización de Cierres")
    st.markdown("Para abrir, visualizar y gestionar todo el histórico de cierres diarios de tus 6 tiendas de forma rápida y sin límites, pulsa el siguiente botón:")
    
    # CONTROL DE SEGURIDAD CORREGIDO: Extrae la URL del excel de forma segura
    try:
        url_hoja_cruda = st.secrets["connections"]["gsheets"]["spreadsheet"]
    except Exception:
        url_hoja_cruda = "https://google.com"
        
    url_hoja_limpia = "".join(url_hoja_cruda.split())
    st.link_button("📊 Abrir mi Hoja de Cálculo Principal en Google Drive", url=url_hoja_limpia, use_container_width=True, type="primary")
