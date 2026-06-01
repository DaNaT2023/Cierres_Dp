import streamlit as st
import pandas as pd
import datetime
import time
import base64
import io
import urllib.parse
import urllib.request

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

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA E ICONO CORPORATIVO
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
# SECCIÓN 1: FORMULARIO DE ENVÍO DIRECTO A GOOGLE FORMS (MÉTODO GET BLINDADO)
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
    if st.button("🚀 Guardar Registro del Turno", key="btn_guardar_registro_sheets", use_container_width=True):
        if encargado.strip() == "":
            st.error("Por favor, introduce el nombre del encargado.")
        else:
            try:
                # Empaquetamos los 28 datos en una sola línea de texto limpia
                cadena_datos = f"{fecha.strftime('%Y-%m-%d')},{tienda},{turno_seleccionado},{encargado},{total_pedidos},{deliverys},{venta_neta},{venta},{venta_2025},{venta_entrega},{venta_llevar},{venta_ventana},{venta_come_bebe},{venta_visa},{venta_efectivo},{quebranto},{ingreso_prosegur},{produccion_real},{espera_rack},{media_reparto},{pedidos_mas_45},{pedidos_mas_10_min},{web},{tgtg},{uber_eats},{glovo},{just_eat},{cancelados_motivo.replace(',', ' ')}"
                
                # REPARACIÓN RADICAL: Envío mediante simulación GET limpia nativa por cabecera de navegador (Evita error 401)
                url_form_base = st.secrets["URL_GOOGLE_FORM"].replace("/formResponse", "/formResponse")
                campo_entry = st.secrets["ENTRY_ID"]
                
                # Montar la URL completa con los datos codificados directamente en la barra de direcciones
                parametros_url = urllib.parse.urlencode({campo_entry: cadena_datos})
                url_get_completa = f"{url_form_base}?{parametros_url}"
                
                # Lanzar la petición simulando un agente de navegador Chrome normal
                cabeceras_navegador = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                peticion_segura = urllib.request.Request(url_get_completa, headers=cabeceras_navegador)
                
                with urllib.request.urlopen(peticion_segura) as respuesta:
                    pass
                
                st.success("🚀 ¡Registro transmitido e inyectado correctamente en tu Google Sheets!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error al transmitir los datos: {e}. Revisa las direcciones de tus Secrets.")

# ------------------------------------------
# SECCIÓN 2: PANEL DEL PROPIETARIO (LECTURA DIRECTA DE LA HOJA DE RESPUESTAS)
# ------------------------------------------
with pestaña_dueño:
    st.subheader("🔒 Panel de Control del Administrador")
    clave_ingresada = st.text_input("Introduce la contraseña de acceso:", type="password", key="pass_propietario_plana")
    
    if clave_ingresada != st.secrets["ADMIN_PASSWORD"]:
        if clave_ingresada != "":
            st.error("⚠️ La contraseña introducida no es correcta.")
        st.warning("Introduce las credenciales arriba para activar el histórico estructurado.")
    else:
        st.success("🔓 Concedido acceso completo al histórico.")
        st.markdown("---")
        
        try:
            url_base = st.secrets["URL_GOOGLE_SHEETS"]
            # Extraer de forma segura el ID del documento
            sheet_id = url_base.split("/d/")[1].split("/")[0]
            
            # Conexión directa a la pestaña morada de Google Forms (gid=1296960697)
            url_csv = f"https://google.com{sheet_id}/export?format=csv&gid=1296960697"
            df_crudo = pd.read_csv(url_csv)
            
            columnas_finales = [
                "Fecha", "Tienda", "Turno", "Encargado", "Total Pedidos", "Deliverys", 
                "Venta Neta", "Venta Total", "Venta 2025", "Venta Entrega", "Venta Llevar", 
                "Venta Ventana", "Venta Come & Bebe", "Venta VISA", "Venta Efectivo", 
                "Quebranto", "Ingreso Prosegur", "Produccion Real", "Espera Rack", 
                "Media Reparto", "Pedidos +45%", "Pedidos > 10 min", "Web", "TGTG", 
                "Uber Eats", "Glovo", "Just Eat", "Cancelados - Motivo"
            ]
            
            listado_filas = []
