import streamlit as st
import sqlite3
import pandas as pd
import datetime
from PIL import Image
import requests
import base64
import json
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

LISTA_TIENDAS = ["Dp Collado", "Dp Valdebebas", "Dp Paracuellos", "Dp Vicálvaro", "Dp Villanueva", "Dp Galapagar"]

def codificar_y_comprimir_imagen(uploaded_file):
    img = Image.open(uploaded_file)
    img.thumbnail((1000, 1000))
    buffer = io.BytesIO()
    img.convert("RGB").save(buffer, format="JPEG", quality=70)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')

# ==========================================
# 2. INTERFAZ WEB CON STREAMLIT
# ==========================================
st.set_page_config(page_title="Panel Cierres Diarios DP Madrid", page_icon="🍕", layout="wide")
st.title("🍕 Panel Cierres Diarios DP Madrid")
st.markdown("---")

pestaña_tiendas, pestaña_dueño = st.tabs(["📲 Envío de Tiendas", "👁️ Panel del Propietario"])

# ------------------------------------------
# SECCIÓN: ENVÍO DE TIENDAS
# ------------------------------------------
with pestaña_tiendas:
    st.header("Formulario de Cierre Diario Automático")
    
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
        st.image(imagen_pil, caption="Imagen cargada correctamente", width=350)
        
        try:
            api_key_segura = st.secrets["OPENAI_API_KEY"]
        except:
            api_key_segura = None

        if st.button("🔍 Iniciar Lectura Automática Inteligente"):
            if not api_key_segura:
                st.error("Falta configurar la clave en los Settings de Streamlit Cloud.")
            else:
                with st.spinner("La Inteligencia Artificial gratuita está procesando la tabla..."):
                    try:
                        uploaded_file.seek(0)
                        base64_image = codificar_y_comprimir_imagen(uploaded_file)
                        
                        # Definimos las instrucciones estructuradas en formato JSON estricto
                        prompt_sistema = f"Analiza la captura de pantalla de este cierre de caja. Busca la sección del turno de la '{turno}' y extrae: el nombre del encargado, la cifra de la venta total (número) y la cifra del quebranto (número, mantén el signo negativo si es una pérdida). Devuelve ÚNICAMENTE un objeto JSON plano con las llaves 'encargado', 'venta' y 'quebranto'."
                        
                        # Preparamos el paquete de datos HTTP nativo para OpenRouter
                        headers = {
                            "Authorization": f"Bearer {api_key_segura}",
                            "Content-Type": "application/json"
                        }
                        
                        payload = {
                            "model": "google/gemini-2.5-flash",
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": prompt_sistema},
                                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                    ]
                                }
                            ],
                            "response_format": {"type": "json_object"}
                        }
                        
                        # Realizamos la petición pura web de forma directa sin usar la librería conflictiva
                        url_api = "https://openrouter.ai/api/v1/chat/completions"
                        response = requests.post(url_api, headers=headers, json=payload)
                        response_json = response.json()
                        
                        # Desempaquetamos la respuesta de forma ultra segura
                        texto_ia = response_json["choices"][0]["message"]["content"]
                        datos_ia = json.loads(texto_ia)
                        
                        # Guardamos los resultados reales directamente en el panel
                        st.session_state['encargado_val'] = str(datos_ia.get("encargado", "Desconocido"))
                        st.session_state['venta_val'] = float(datos_ia.get("venta", 0.0))
                        st.session_state['quebranto_val'] = float(datos_ia.get("quebranto", 0.0))
                        st.success("¡Lectura inteligente completada con éxito!")
                        
                    except Exception as e:
                        st.error(f"Fallo en la comunicación con el procesador visual: {e}")

        # Recuperar datos extraídos de forma directa
        val_encargado = st.session_state.get('encargado_val', "")
        val_venta = st.session_state.get('venta_val', 0.0)
        val_quebranto = st.session_state.get('quebranto_val', 0.0)
        
        st.markdown("---")
        st.info("📝 **Verificación:** Comprueba que los datos extraídos automáticamente coincidan con tu foto:")
        
        encargado_final = st.text_input("Encargado leído por la máquina:", value=val_encargado)
        venta_final = st.number_input("Venta Total leída (€):", value=val_venta, min_value=0.0, step=0.01, format="%.2f")
        quebranto_final = st.number_input("Quebranto leído (€):", value=val_quebranto, step=0.01, format="%.2f")
        
        if st.button("🚀 Confirmar y Registrar Turno en la Base de Datos"):
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
            
            st.success(f"¡Cierre registrado perfectamente!")
            if 'encargado_val' in st.session_state: del st.session_state['encargado_val']
            if 'venta_val' in st.session_state: del st.session_state['venta_val']
            if 'quebranto_val' in st.session_state: del st.session_state['quebranto_val']

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
