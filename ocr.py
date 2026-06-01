import streamlit as st
import pandas as pd
import datetime
import time
import base64
import io
from streamlit_gsheets import GSheetsConnection

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

# ESTABLECER CONEXIÓN REAL CON EL EXCEL ONLINE DE GOOGLE SECRETS
try:
    conn_sheets = st.connection("gsheets", type=GSheetsConnection)
except:
    conn_sheets = None

# ------------------------------------------
# SECCIÓN 1: FORMULARIO DE ENVÍO DIRECTO A GOOGLE SHEETS
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
        elif conn_sheets is None:
            st.error("Error: Conector de Google Sheets no configurado correctamente.")
        else:
            try:
                # 📦 Crear la fila con las 28 palabras exactas de tu lista para inyectar
                fila_nueva = pd.DataFrame([{
                    "Fecha": fecha.strftime("%Y-%m-%d"), "Tienda": tienda, "Turno": turno_seleccionado, "Encargado": encargado,
                    "Total Pedidos": total_pedidos, "Deliverys": deliverys, "Venta Neta": venta_neta, "Venta Total": venta,
                    "Venta 2025": venta_2025, "Venta Entrega": venta_entrega, "Venta Llevar": venta_llevar, "Venta Ventana": venta_ventana,
                    "Venta Come & Bebe": venta_come_bebe, "Venta VISA": venta_visa, "Venta Efectivo": venta_efectivo, "Quebranto": quebranto,
                    "Ingreso Prosegur": ingreso_prosegur, "Produccion Real": produccion_real, "Espera Rack": espera_rack, "Media Reparto": media_reparto,
                    "Pedidos +45%": pedidos_mas_45, "Pedidos > 10 min": pedidos_mas_10_min, "Web": web, "TGTG": tgtg, "Uber Eats": uber_eats,
                    "Glovo": glovo, "Just Eat": just_eat, "Cancelados - Motivo": cancelados_motivo
                }])
                
                # Leer tu Google Sheets desde el enlace secreto de Secrets
                df_existente = conn_sheets.read(spreadsheet=st.secrets["URL_GOOGLE_SHEETS"])
                
                # Unir la fila nueva abajo de todo de forma horizontal limpia
                df_final = pd.concat([df_existente, fila_nueva], ignore_index=True)
                
                # Reescribir tu hoja online con la nueva línea añadida
                conn_sheets.update(spreadsheet=st.secrets["URL_GOOGLE_SHEETS"], data=df_final)
                
                st.success("🚀 ¡Registro inyectado y guardado de forma permanente en tu Google Sheets!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error al transmitir los datos al Excel online: {e}")

# ------------------------------------------
# SECCIÓN 2: PANEL DEL PROPIETARIO (PESTAÑAS LEÍDAS DE TU EXCEL ONLINE)
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
            df_db = conn_sheets.read(spreadsheet=st.secrets["URL_GOOGLE_SHEETS"])
        except:
            df_db = pd.DataFrame()
        
        if df_db.empty or df_db.shape < 1:
            st.info("ℹ— Tu Google Sheets online está conectado. En cuanto guardes el primer turno con el nuevo botón, aparecerá aquí de forma automática.")
        else:
            tiendas_filtro = st.multiselect("Filtrar por Tienda:", options=LISTA_TIENDAS, default=LISTA_TIENDAS)
            if not tiendas_filtro:
                tiendas_filtro = LISTA_TIENDAS
                
            df_filtrado = df_db[df_db['Tienda'].isin(tiendas_filtro)].copy()
            
            st.markdown("### 📈 Métricas Generales")
