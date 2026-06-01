import streamlit as st
import sqlite3
import pandas as pd
import datetime
import time
import base64
import io

# ==========================================
# 0. CONFIGURACIÓN DE TUS 6 TIENDAS REALES
# ==========================================
LISTA_TIENDAS = ["Dp Valdebebas", "Dp Collado", "Dp Paracuellos", "Dp Villanueva", "Dp Galapagar", "Dp Vicálvaro"]

# ==========================================
# 1. BASE DE DATOS LOCAL (CON NUEVA COLUMNA DE OBSERVACIONES DIRECCIÓN)
# ==========================================
def inicializar_bd():
    conexion = sqlite3.connect("tiendas.db")
    cursor = conexion.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recuadros (
            id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, tienda TEXT, turno TEXT, encargado TEXT,
            venta_neta REAL, venta_total REAL, venta_2025 REAL, venta_entrega REAL, venta_llevar REAL,
            venta_ventana REAL, venta_come_bebe REAL, venta_visa REAL, venta_efectivo REAL, venta_pluxee REAL,
            quebranto REAL, ingreso_prosegur REAL, web REAL, tgtg REAL, uber_eats REAL, glovo REAL, just_eat REAL, 
            cancelaciones_obs TEXT, estado_alerta TEXT, anotaciones_jefe TEXT
        )
    """)
    # Parche de seguridad para bases de datos ya existentes en producción
    try:
        cursor.execute("ALTER TABLE recuadros ADD COLUMN anotaciones_jefe TEXT")
    except sqlite3.OperationalError:
        pass
    conexion.commit()
    conexion.close()

inicializar_bd()

# ==========================================
# 2. CONFIGURACIÓN DE PÁGINA E ICONO CORPORATIVO
# ==========================================
st.set_page_config(page_title="Cierre Diario DP", layout="wide")

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
            <h1 style="margin: 0; padding: 0; font-size: 2.3rem; font-weight: 700; color: #31333F;">Cierre Diario DP</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.title("🍕 Cierre Diario DP")

st.markdown("---")

pestaña_tiendas, pestaña_dueño = st.tabs(["📲 Envío de Tiendas", "👁️ Panel del Propietario"])
# ------------------------------------------
# SECCIÓN: ENVÍO DE TIENDAS
# ------------------------------------------
with pestaña_tiendas:
    st.header("📝 Cierre de Turno")
    turno_seleccionado = st.radio("¿Qué turno vas a registrar?", ["Mañana", "Noche"], horizontal=True, key="sel_turno")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("📌 Datos del Turno")
        tienda = st.selectbox("Tienda", LISTA_TIENDAS, key="f_tienda")
        encargado = st.text_input("Nombre del Encargado", placeholder="Escribe tu nombre", key="f_enc")
        fecha = st.date_input("Fecha del Cierre", value=datetime.date.today(), key="f_fecha")
        
        st.subheader("💰 Totales Caja")
        venta_neta = st.number_input("Venta Neta (€)", min_value=0.0, step=10.0, value=None, placeholder="Escribe la cantidad...", key="f_vn")
        venta = st.number_input("Venta Total / Bruta (€)", min_value=0.0, step=10.0, value=None, placeholder="Escribe la cantidad...", key="f_vt")
        venta_2025 = st.number_input("Venta 2025 (€)", min_value=0.0, step=10.0, value=None, placeholder="Escribe la cantidad...", key="f_v25")
        
        st.subheader("💬 Cancelaciones y observaciones")
        incidencias_texto = st.text_area("Escribe aquí cualquier incidencia o comentario del turno:", placeholder="Ej. Cancelación de pedido por retraso, descuadre de moto...", key="f_obs")

    with col2:
        st.subheader("🛵 Desglose de Canales")
        venta_entrega = st.number_input("Venta Entrega (€)", min_value=0.0, step=10.0, value=None, placeholder="Escribe la cantidad...", key="f_ve")
        venta_llevar = st.number_input("Venta Llevar (€)", min_value=0.0, step=10.0, value=None, placeholder="Escribe la cantidad...", key="f_vll")
        venta_ventana = st.number_input("Venta Ventana (€)", min_value=0.0, step=10.0, value=None, placeholder="Escribe la cantidad...", key="f_vv")
        venta_come_bebe = st.number_input("Venta Come & Bebe / Sala (€)", min_value=0.0, step=10.0, value=None, placeholder="Escribe la cantidad...", key="f_vcb")
        
        st.subheader("💳 Métodos de Pago")
        venta_visa = st.number_input("Venta VISA / Tarjeta (€)", min_value=0.0, step=10.0, value=None, placeholder="Escribe la cantidad...", key="f_vvi")
        venta_efectivo = st.number_input("Venta en Efectivo (€)", min_value=0.0, step=10.0, value=None, placeholder="Escribe la cantidad...", key="f_vef")

    with col3:
        st.subheader("📉 Descuadres")
        quebranto = st.number_input("Quebranto (€) [Usa - para pérdidas]", step=5.0, value=None, placeholder="Escribe la cantidad...", key="f_q")
        ingresado_prosegur = st.number_input("Ingreso Prosegur (€)", min_value=0.0, step=10.0, value=None, placeholder="Escribe la cantidad...", key="f_pro")
        
        st.subheader("🌐 Agregadores y Online")
        venta_pluxee = st.number_input("Pluxee Gourmet (€)", min_value=0.0, step=10.0, value=None, placeholder="Escribe la cantidad...", key="f_vp")
        web = st.number_input("Web (€)", min_value=0.0, step=10.0, value=None, placeholder="Escribe la cantidad...", key="f_web")
        tgtg = st.number_input("TGTG (€)", min_value=0.0, step=5.0, value=None, placeholder="Escribe la cantidad...", key="f_tg")
        uber_eats = st.number_input("Uber Eats (€)", min_value=0.0, step=10.0, value=None, placeholder="Escribe la cantidad...", key="f_ub")
        glovo = st.number_input("Glovo (€)", min_value=0.0, step=10.0, value=None, placeholder="Escribe la cantidad...", key="f_gl")
        just_eat = st.number_input("Just Eat (€)", min_value=0.0, step=10.0, value=None, placeholder="Escribe la cantidad...", key="f_je")

    st.markdown("---")
    if st.button("🚀 Guardar Registro del Turno", key="btn_guardar", use_container_width=True):
        if encargado.strip() == "":
            st.error("Por favor, introduce el nombre del encargado para poder guardar el cierre.")
        else:
            v_neta_val = venta_neta if venta_neta is not None else 0.0
            v_total_val = venta if venta is not None else 0.0
            v_2025_val = venta_2025 if venta_2025 is not None else 0.0
            v_entrega_val = venta_entrega if venta_entrega is not None else 0.0
            v_llevar_val = venta_llevar if venta_llevar is not None else 0.0
            v_ventana_val = venta_ventana if venta_ventana is not None else 0.0
            v_come_bebe_val = venta_come_bebe if venta_come_bebe is not None else 0.0
            v_visa_val = venta_visa if venta_visa is not None else 0.0
            v_efectivo_val = venta_efectivo if venta_efectivo is not None else 0.0
            v_pluxee_val = venta_pluxee if venta_pluxee is not None else 0.0
            v_quebranto_val = quebranto if quebranto is not None else 0.0
            v_prosegur_val = ingresado_prosegur if ingresado_prosegur is not None else 0.0
            v_web_val = web if web is not None else 0.0
            v_tgtg_val = tgtg if tgtg is not None else 0.0
            v_uber_val = uber_eats if uber_eats is not None else 0.0
            v_glovo_val = glovo if glovo is not None else 0.0
            v_just_val = just_eat if just_eat is not None else 0.0
            
            alerta = "OK"
            if v_quebranto_val <= -100: alerta = "🚨 CRÍTICO (Pérdida)"
            elif v_quebranto_val >= 100: alerta = "⚠️ ATENCIÓN (Exceso)"
                
            conn = sqlite3.connect("tiendas.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO recuadros (
                    fecha, tienda, turno, encargado, venta_neta, venta_total, venta_2025,
                    venta_entrega, venta_llevar, venta_ventana, venta_come_bebe, venta_visa,
                    venta_efectivo, venta_pluxee, quebranto, ingreso_prosegur, web, tgtg, uber_eats, glovo, just_eat, 
                    cancelaciones_obs, estado_alerta, anotaciones_jefe
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fecha.strftime("%Y-%m-%d"), tienda, turno_seleccionado, encargado, v_neta_val, v_total_val, v_2025_val,
                v_entrega_val, v_llevar_val, v_ventana_val, v_come_bebe_val, v_visa_val,
                v_efectivo_val, v_pluxee_val, v_quebranto_val, v_prosegur_val, v_web_val, v_tgtg_val, v_uber_val, v_glovo_val, v_just_val, 
                incidencias_texto, alerta, ""
            ))
            conn.commit()
            conn.close()
            st.success("¡El cierre se ha guardado correctamente!")
            
            if "df_original" in st.session_state:
                del st.session_state.df_original
                
            time.sleep(1)
            st.rerun()
# ------------------------------------------
# SECCIÓN: PANEL DEL PROPIETARIO
# ------------------------------------------
with pestaña_dueño:
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
        st.session_state.usuario_activo = ""

    # Sistema de perfiles dobles integrado
    if not st.session_state.autenticado:
        st.subheader("🔒 Acceso Restringido para Dirección")
        input_usuario = st.text_input("Usuario", key="l_user")
        input_password = st.text_input("Contraseña", type="password", key="l_pass")
        
        if st.button("🔓 Entrar al Panel", key="btn_auth", use_container_width=True):
            if input_usuario == st.secrets["ADMIN_USER"] and input_password == st.secrets["ADMIN_PASSWORD"]:
                st.session_state.autenticado = True
                st.session_state.usuario_activo = "Nataly"
                st.success("¡Acceso concedido!")
                time.sleep(0.5)
                st.rerun()
            elif input_usuario == st.secrets["CELIA_USER"] and input_password == st.secrets["CELIA_PASSWORD"]:
                st.session_state.autenticado = True
                st.session_state.usuario_activo = "CeliayDiana"
                st.success("¡Acceso concedido!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
        st.stop()

    col_header, col_refrescar, col_logout = st.columns(3)
    with col_header:
        st.subheader(f"📊 Resumen General de Cierres ({st.session_state.usuario_activo})")
    with col_refrescar:
        if st.button("🔄 Refrescar Datos", use_container_width=True, key="btn_refrescar_datos_iphone"):
            if "df_original" in st.session_state:
                del st.session_state.df_original
            st.rerun()
    with col_logout:
        if st.button("🔒 Salir", key="btn_logout", use_container_width=True):
            st.session_state.autenticado = False
            st.session_state.usuario_activo = ""
            if "df_original" in st.session_state:
                del st.session_state.df_original
            st.rerun()

    columnas_mapeo = {
        'id': 'ID', 'fecha': 'Fecha', 'tienda': 'Tienda', 'turno': 'Turno', 'encargado': 'Encargado',
        'venta_neta': 'Venta Neta', 'venta_total': 'Venta Bruta', 'venta_2025': 'Venta 2025',
        'venta_visa': 'Tarjeta', 'venta_efectivo': 'Efectivo', 'venta_pluxee': 'Pluxee',
        'quebranto': 'Quebranto', 'ingreso_prosegur': 'Prosegur', 'cancelaciones_obs': 'Encargado OBS', 
        'estado_alerta': 'Estado', 'anotaciones_jefe': 'Observaciones'
    }

    if "df_original" not in st.session_state:
        conn = sqlite3.connect("tiendas.db")
        df_base = pd.read_sql_query("SELECT * FROM recuadros ORDER BY fecha DESC, id DESC", conn)
        conn.close()
        
        if not df_base.empty:
            df_base = df_base[list(columnas_mapeo.keys())].rename(columns=columnas_mapeo)
        st.session_state.df_original = df_base

    df_vista = st.session_state.df_original
    if df_vista.empty:
        st.info("Aún no se han registrado cierres en la base de datos.")
        st.markdown("### 🔄 Restaurar Copia de Seguridad Nativa")
        st.caption("Sube tu archivo .xlsx guardado previamente para recuperar el historial íntegro:")
        
        archivo_subido = st.file_uploader("Selecciona el archivo de copia de seguridad:", type=["xlsx"], key="recuperacion_vacia_dueño")
        if archivo_subido is not None:
            try:
                df_recuperado = pd.read_excel(archivo_subido, engine='openpyxl')
                mapeo_inverso_bd = {v: k for k, v in columnas_mapeo.items()}
                df_recuperado_bd = df_recuperado.rename(columns=mapeo_inverso_bd)
                
                columnas_db = ['fecha', 'tienda', 'turno', 'encargado', 'venta_neta', 'venta_total', 'venta_2025', 'venta_entrega', 'venta_llevar', 'venta_ventana', 'venta_come_bebe', 'venta_visa', 'venta_efectivo', 'venta_pluxee', 'quebranto', 'ingreso_prosegur', 'web', 'tgtg', 'uber_eats', 'glovo', 'just_eat', 'cancelaciones_obs', 'estado_alerta', 'anotaciones_jefe']
                for col in columnas_db:
                    if col not in df_recuperado_bd.columns:
                        df_recuperado_bd[col] = "" if col in ['cancelaciones_obs', 'anotaciones_jefe'] else 0.0
                
                df_recuperado_bd = df_recuperado_bd[[c for c in columnas_db if c in df_recuperado_bd.columns]]
                
                conn = sqlite3.connect("tiendas.db")
                df_recuperado_bd.to_sql("recuadros", conn, if_exists="append", index=False)
                conn.close()
                
                st.success("¡Historial completo restaurado con éxito!")
                if "df_original" in st.session_state:
                    del st.session_state.df_original
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error al procesar la copia de seguridad: {e}")
    else:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            tiendas_filtro = st.multiselect("Filtrar por Tienda:", options=LISTA_TIENDAS, default=LISTA_TIENDAS)
        with col_f2:
            alertas_disponibles = list(df_vista['Estado'].unique())
            alertas_filtro = st.multiselect("Filtrar por Estado de Alerta:", options=alertas_disponibles, default=alertas_disponibles)
        
        df_filtrado = df_vista[df_vista['Tienda'].isin(tiendas_filtro) & df_vista['Estado'].isin(alertas_filtro)].copy()
        
        st.markdown("### 📈 Métricas del Grupo")
        
        buffer_excel = io.BytesIO()
        with pd.ExcelWriter(buffer_excel, engine='openpyxl') as escritor:
            df_vista.to_excel(escritor, index=False, sheet_name='Historial Cierres')
        excel_descarga = buffer_excel.getvalue()
        fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
        
        col_m1, col_m2, col_m3, col_btn_descarga = st.columns(4)
        with col_m1:
            st.metric("Venta Bruta Total", f"{df_filtrado['Venta Bruta'].sum():,.2f} €")
        with col_m2:
            st.metric("Balance de Quebrantos", f"{df_filtrado['Quebranto'].sum():,.2f} €")
        with col_m3:
            st.metric("Turnos Registrados", f"{len(df_filtrado)}")
        with col_btn_descarga:
            st.download_button(
                label="📥 Descargar copia seguridad (.xlsx)",
                data=excel_descarga,
                file_name=f"copia_seguridad_cierres_dp_{fecha_hoy}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="btn_descarga_seguridad_propietario"
            )
            
        st.markdown(" ")
        with st.expander("🔄 Importar / Añadir cierres desde un archivo copia externa"):
            archivo_añadir = st.file_uploader("Sube tu archivo .xlsx de copia de seguridad:", type=["xlsx"], key="recuperacion_activa_dueño")
            if archivo_añadir is not None:
                if st.button("⚡ Confirmar inserción masiva de datos", use_container_width=True, type="secondary"):
                    try:
                        df_extraido = pd.read_excel(archivo_añadir, engine='openpyxl')
                        mapeo_inverso_bd = {v: k for k, v in columnas_mapeo.items()}
                        df_extraido_bd = df_extraido.rename(columns=mapeo_inverso_bd)
                        
                        if "id" in df_extraido_bd.columns:
                            df_extraido_bd = df_extraido_bd.drop(columns=["id"])
                            
                        conn = sqlite3.connect("tiendas.db")
                        df_extraido_bd.to_sql("recuadros", conn, if_exists="append", index=False)
                        conn.close()
                        
                        st.success("¡Datos inyectados y consolidados de forma nativa!")
                        if "df_original" in st.session_state:
                            del st.session_state.df_original
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error en la importación: {e}")
        
        st.markdown("---")
        st.subheader("📝 Tabla Histórica de Cierres (Editable)")
        st.caption("💡 Modifica las celdas directamente en la tabla. El botón de guardar aparecerá abajo automáticamente si hay cambios.")
        
        cfg_dinero = st.column_config.NumberColumn(format="%.2f €")
        es_nataly = (st.session_state.usuario_activo == "Nataly")
        
        configuracion_columnas = {
            "ID": st.column_config.NumberColumn(disabled=True),
            "Venta Neta": cfg_dinero, "Venta Bruta": cfg_dinero, "Venta 2025": cfg_dinero,
            "Tarjeta": cfg_dinero, "Efectivo": cfg_dinero, "Pluxee": cfg_dinero,
            "Quebranto": cfg_dinero, "Prosegur": cfg_dinero, 
            "Encargado OBS": st.column_config.TextColumn(disabled=True),
            "Observaciones": st.column_config.TextColumn(disabled=not es_nataly),
            "Tienda": st.column_config.SelectboxColumn(options=LISTA_TIENDAS, disabled=not es_nataly),
            "Turno": st.column_config.SelectboxColumn(options=["Mañana", "Noche"], disabled=not es_nataly),
            "Fecha": st.column_config.TextColumn(disabled=not es_nataly),
            "Encargado": st.column_config.TextColumn(disabled=not es_nataly),
            "Estado": st.column_config.TextColumn(disabled=True)
        }

        edited_df = st.data_editor(
            df_filtrado, 
            use_container_width=True, 
            hide_index=True,
            num_rows="dynamic" if es_nataly else "fixed",
            column_config=configuracion_columnas,
            disabled=not es_nataly,
            key="editor_propietario_definitivo"
        )

        if es_nataly and (not edited_df.equals(df_filtrado)):
            st.warning("⚠️ Hay cambios pendientes por confirmar")
            
            if st.button("💾 Guardar cambios", use_container_width=True, type="primary", key="btn_guardar_cambios_modelo_captura"):
                conn = sqlite3.connect("tiendas.db")
                cursor = conn.cursor()
                
                ids_actuales = set(edited_df["ID"].tolist())
                ids_originales = set(df_filtrado["ID"].tolist())
                ids_borrados = ids_originales - ids_actuales
                
                for id_borrar in ids_borrados:
                    cursor.execute("DELETE FROM recuadros WHERE id = ?", (id_borrar,))
                
                for index, fila in edited_df.iterrows():
                    id_reg = int(fila["ID"])
                    
                    v_quebranto = float(fila["Quebranto"])
                    n_alerta = "OK"
                    if v_quebranto <= -100: n_alerta = "🚨 CRÍTICO (Pérdida)"
                    elif v_quebranto >= 100: n_alerta = "⚠️ ATENCIÓN (Exceso)"
                    
                    cursor.execute("""
                        UPDATE recuadros SET 
                            fecha=?, tienda=?, turno=?, encargado=?, venta_neta=?, venta_total=?, venta_2025=?,
                            venta_visa=?, venta_efectivo=?, venta_pluxee=?, quebranto=?, ingreso_prosegur=?, 
                            cancelaciones_obs=?, estado_alerta=?, anotaciones_jefe=?
                        WHERE id=?
                    """, (
                        str(fila["Fecha"]), str(fila["Tienda"]), str(fila["Turno"]), str(fila["Encargado"]),
                        float(fila["Venta Neta"]), float(fila["Venta Bruta"]), float(fila["Venta 2025"]),
                        float(fila["Tarjeta"]), float(fila["Efectivo"]), float(fila["Pluxee"]),
                        v_quebranto, float(fila["Prosegur"]), str(fila["Encargado OBS"]), n_alerta, 
                        str(fila["Observaciones"]), id_reg
                    ))
                
                conn.commit()
                conn.close()
                
                if "df_original" in st.session_state:
                    del st.session_state.df_original
                
                st.success("Cambios guardados correctamente")
                time.sleep(0.8)
                st.rerun()
