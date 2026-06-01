import streamlit as st
import pandas as pd
import datetime
import time
import base64

# ==========================================
# 0. CONFIGURACIÓN DE TUS 6 TIENDAS REALES
# ==========================================
LISTA_TIENDAS = ["Dp Valdebebas", "Dp Collado", "Dp Paracuellos", "Dp Villanueva", "Dp Galapagar", "Dp Vicálvaro"]

# ==========================================
# 1. INICIALIZAR ALMACENAMIENTO EN SESIÓN (TOMANDO NOTA DE TU EJEMPLO)
# ==========================================
if "cierres_memoria" not in st.session_state:
    st.session_state.cierres_memoria = []

# ==========================================
# 2. CONFIGURACIÓN DE PÁGINA E ICONO CORPORATIVO
# ==========================================
st.set_page_config(page_title="Panel Cierre Diario Dp", layout="wide")

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
# SECCIÓN: ENVÍO DE TIENDAS (GUARDA EN SESSION_STATE)
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
            
            # GUARDADO DIRECTO EN LA MEMORIA DE LA SESIÓN (SESSION_STATE)
            st.session_state.cierres_memoria.append({
                "Fecha": fecha.strftime("%Y-%m-%d"),
                "Tienda": tienda,
                "Turno": turno_seleccionado,
                "Encargado": encargado,
                "Venta Neta": venta_neta,
                "Venta Bruta": venta,
                "Venta 2025": venta_2025,
                "Tarjeta": venta_visa,
                "Efectivo": venta_efectivo,
                "Pluxee": venta_pluxee,
                "Quebranto": quebranto,
                "Prosegur": ingresado_prosegur,
                "Estado": alerta
            })
            
            st.success("¡El cierre del turno se ha guardado temporalmente en la memoria de la web!")
            time.sleep(1)
            st.rerun()

# ------------------------------------------
# SECCIÓN: PANEL DEL PROPIETARIO (MUESTRA CON ST.DATAFRAME)
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

    # Cabecera superior limpia del propietario
    col_header, col_logout = st.columns(2)
    with col_header:
        st.subheader("📊 Resumen General de Cierres")
    with col_logout:
        if st.button("🔒 Salir", key="btn_logout", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()
            
    st.markdown("---")

    # CARGA REÁCTIVA DESDE TU EJEMPLO DE CAPTURA
    if st.session_state.cierres_memoria:
        # Convertimos la lista acumulada de la sesión en un DataFrame limpio
        df_completo = pd.DataFrame(st.session_state.cierres_memoria)
        
        # Filtros interactivos superiores basados en el DataFrame cargado
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            tiendas_filtro = st.multiselect("Filtrar por Tienda:", options=LISTA_TIENDAS, default=LISTA_TIENDAS)
        with col_f2:
            alertas_disponibles = list(df_completo['Estado'].unique())
            alertas_filtro = st.multiselect("Filtrar por Estado de Alerta:", options=alertas_disponibles, default=alertas_disponibles)
        
        # Filtrado reactivo en pantalla
        df_filtrado = df_completo[df_completo['Tienda'].isin(tiendas_filtro) & df_completo['Estado'].isin(alertas_filtro)].copy()
        
        # Mostrar Métricas del grupo actualizadas en vivo
        st.markdown("### 📈 Métricas del Grupo")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Venta Bruta Total", f"{df_filtrado['Venta Bruta'].sum():,.2f} €")
        with col_m2:
            st.metric("Balance de Quebrantos", f"{df_filtrado['Quebranto'].sum():,.2f} €")
        with col_m3:
            st.metric("Turnos Registrados", f"{len(df_filtrado)}")
        
        st.markdown("---")
        st.subheader("📋 Tabla Histórica de Cierres (Detalle)")
        
        # FORMATO DE DINERO PROFESIONAL PARA TU ST.DATAFRAME()
        cfg_dinero = st.column_config.NumberColumn(format="%.2f €")
        
        # Despliegue de st.dataframe() plano sin errores de guardado según tu ejemplo
        st.dataframe(
            df_filtrado,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Venta Neta": cfg_dinero, "Venta Bruta": cfg_dinero, "Venta 2025": cfg_dinero,
                "Tarjeta": cfg_dinero, "Efectivo": cfg_dinero, "Pluxee": cfg_dinero,
                "Quebranto": cfg_dinero, "Prosegur": cfg_dinero
            }
        )
    else:
        st.info("No hay datos registrados en esta sesión todavía.")
