import streamlit as st
import pandas as pd
import datetime
import time
import base64
from streamlit_gsheets import GSheetsConnection

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

# Conexión nativa con la hoja de cálculo de Google
conn_sheets = st.connection("gsheets", type=GSheetsConnection)

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
            
            nueva_fila = pd.DataFrame([{
                "Fecha": fecha.strftime("%Y-%m-%d"), "Tienda": tienda, "Turno": turno_seleccionado, "Encargado": encargado,
                "Venta Neta": venta_neta, "Venta Total": venta, "Venta 2025": venta_2025,
                "Venta Entrega": venta_entrega, "Venta Llevar": venta_llevar, "Venta Ventana": venta_ventana, "Venta Come&Bebe": venta_come_bebe,
                "Venta Visa": venta_visa, "Venta Efectivo": venta_efectivo, "Venta Pluxee Gourmet": venta_pluxee,
                "Quebranto": quebranto, "Ingreso Prosegur": ingresado_prosegur, "Web": web, "TGTG": tgtg, "Uber Eats": uber_eats, "Glovo": glovo, "Just Eat": just_eat,
                "Estado": alerta
            }])
            
            try:
                datos_actuales = conn_sheets.read(ttl=0)
                datos_actualizados = pd.concat([datos_actuales, nueva_fila], ignore_index=True)
                conn_sheets.update(data=datos_actualizados)
                
                st.success("¡El cierre se ha enviado y guardado directamente en tu Google Sheets!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar en Google Sheets: {e}")

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
        st.subheader("📊 Resumen General de Cierres (Google Sheets)")
    with col_logout:
        if st.button("🔒 Salir", key="btn_logout", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()
    
    try:
        df = conn_sheets.read(ttl=0)
    except Exception as e:
        st.error(f"No se pudo leer la hoja de cálculo: {e}")
        st.stop()
        
    if df.empty or len(df) == 0:
        st.info("Aún no se han registrado cierres en tu Google Sheets.")
    else:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            tiendas_filtro = st.multiselect("Filtrar por Tienda:", options=LISTA_TIENDAS, default=LISTA_TIENDAS)
        with col_f2:
            alertas_disponibles = list(df['Estado'].unique()) if 'Estado' in df.columns else ["OK"]
            alertas_filtro = st.multiselect("Filtrar por Estado de Alerta:", options=alertas_disponibles, default=alertas_disponibles)
        
        df_filtrado = df[df['Tienda'].isin(tiendas_filtro) & df['Estado'].isin(alertas_filtro)].copy()
        
        columnas_visibles = ['Fecha', 'Tienda', 'Turno', 'Encargado', 'Venta Neta', 'Venta Total', 'Venta 2025', 'Venta Visa', 'Venta Efectivo', 'Venta Pluxee Gourmet', 'Quebranto', 'Ingreso Prosegur', 'Estado']
        df_vista = df_filtrado[[c for c in columnas_visibles if c in df_filtrado.columns]]
        
        st.markdown("### 📈 Métricas del Grupo (Totales de Google Sheets)")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Venta Bruta Total", f"{pd.to_numeric(df_filtrado['Venta Total'], errors='coerce').sum():,.2f} €")
        with col_m2:
            st.metric("Balance de Quebrantos", f"{pd.to_numeric(df_filtrado['Quebranto'], errors='coerce').sum():,.2f} €")
        with col_m3:
            st.metric("Turnos Registrados", f"{len(df_filtrado)}")
        
        st.markdown("---")
        st.subheader("📝 Tabla Histórica de Cierres (Editable)")
        st.caption("💡 Modifica los valores directamente en la tabla. Al finalizar, pulsa el botón de abajo para confirmar los cambios.")
        
        # Formato de dinero profesional
        cfg_dinero = st.column_config.NumberColumn(format="%.2f €")
        config_final = {
            "Venta Neta": cfg_dinero, "Venta Total": cfg_dinero, "Venta 2025": cfg_dinero,
            "Venta Visa": cfg_dinero, "Venta Efectivo": cfg_dinero, "Venta Pluxee Gourmet": cfg_dinero,
            "Quebranto": cfg_dinero, "Ingreso Prosegur": cfg_dinero,
            "Tienda": st.column_config.SelectboxColumn(options=LISTA_TIENDAS),
            "Turno": st.column_config.SelectboxColumn(options=["Mañana", "Noche"])
        }
        
        # Formulario limpio de edición
        formulario_dueño = st.form("form_edicion_limpio")
        tabla_editada = formulario_dueño.data_editor(df_vista, use_container_width=True, hide_index=True, num_rows="dynamic", column_config=config_final, key="editor_propietario")
        ejecutar_guardado = formulario_dueño.form_submit_button("💾 Guardar Cambios en Google Sheets", use_container_width=True, type="primary")
            
