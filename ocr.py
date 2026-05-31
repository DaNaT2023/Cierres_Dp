import streamlit as st
import sqlite3
import pandas as pd
import datetime
from google import genai  # Nueva librería oficial de Google

# ==========================================
# 1. BASE DE DATOS (Se crea sola al arrancar)
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

# ==========================================
# 2. INTERFAZ WEB CON STREAMLIT
# ==========================================
st.set_page_config(page_title="Control General 6 Tiendas", layout="wide")

st.title("📊 Panel Central de Gestión - 6 Tiendas")
st.markdown("---")

pestaña_tiendas, pestaña_dueño = st.tabs(["📲 Envío de Tiendas", "👁️ Panel del Propietario"])

# ------------------------------------------
# SECCIÓN: ENVÍO DE TIENDAS
# ------------------------------------------
with pestaña_tiendas:
    st.header("Formulario de Cierre de Turno")
    
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        tienda = st.selectbox("Selecciona tu Tienda", [f"Tienda {i}" for i in range(1, 7)])
        turno = st.radio("Turno Actual", ["Mañana", "Noche"])
        encargado = st.text_input("Nombre del Encargado (ej: Diego, Naiara)")
        
    with col_der:
        fecha = st.date_input("Fecha del Recuadro", datetime.date.today())
        venta = st.number_input("Venta Total del Turno (€)", min_value=0.0, step=10.0)
        quebranto = st.number_input("Importe del Quebranto (€)", step=5.0)

    if st.button("🚀 Procesar y Guardar Registro"):
        if encargado == "":
            st.error("Por favor, introduce el nombre del encargado.")
        else:
            alerta = "OK"
            if quebranto <= -100:
                alerta = "🚨 CRÍTICO (Pérdida)"
            elif quebranto >= 100:
                alerta = "⚠️ ATENCIÓN (Exceso)"
                
            conn = sqlite3.connect("tiendas.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO recuadros (fecha, tienda, turno, encargado, venta_total, quebranto, estado_alerta)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (fecha.strftime("%Y-%m-%d"), tienda, turno, encargado, venta, quebranto, alerta))
            conn.commit()
            conn.close()
            
            st.success(f"¡Datos de {tienda} ({turno}) guardados con éxito!")

# ------------------------------------------
# SECCIÓN: PANEL DEL PROPIETARIO
# ------------------------------------------
with pestaña_dueño:
    st.header("Histórico de Ventas y Quebrantos en Tiempo Real")
    
    conn = sqlite3.connect("tiendas.db")
    df = pd.read_sql_query("SELECT * FROM recuadros ORDER BY fecha DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("Aún no hay datos registrados por las tiendas. Rellena el formulario de la otra pestaña para probar.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Ventas Registradas", f"{df['venta_total'].sum():,.2f} €")
        c2.metric("Balance Total Quebrantos", f"{df['quebranto'].sum():,.2f} €")
        c3.metric("Alertas Críticas Activas", len(df[df['estado_alerta'] != "OK"]))
        
        st.markdown("### Tabla Completa de Registros")
        st.dataframe(df, use_container_width=True)
        
        # ------------------------------------------
        # NUEVA FUNCIÓN: AUDITORÍA CON INTELIGENCIA ARTIFICIAL (GEMINI)
        # ------------------------------------------
        st.markdown("---")
        st.markdown("### 🤖 Auditoría Automatizada con IA")
        st.write("Genera un reporte estratégico analizando las desviaciones y rendimientos de las 6 tiendas.")
        
        if st.button("📊 Generar Informe con Gemini"):
            with st.spinner("Analizando métricas y registros con Google Gemini..."):
                try:
                    # Inicializamos el cliente oficial de Google usando la clave de tus Secrets
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    
                    # Convertimos los últimos datos a texto para que la IA los procese
                    datos_texto = df.to_string(index=False)
                    
                    # Creamos un prompt específico para el negocio
                    prompt = f"""
                    Actúa como un Auditor de Finanzas y Operaciones experto en Retail. 
                    Analiza los siguientes registros de cierre de caja de nuestra cadena de 6 tiendas:
                    
                    {datos_texto}
                    
                    Por favor, redacta un informe ejecutivo rápido con:
                    1. Resumen general de la salud financiera del día o periodo.
                    2. Análisis de las alertas críticas detectadas por quebrantos (pérdidas notables o excesos inexplicables).
                    3. Recomendación de a qué tiendas o encargados se les debe solicitar una revisión de caja de forma prioritaria.
                    
                    Hazlo directo, profesional y claro para el dueño del negocio.
                    """
                    
                    # Llamada directa al modelo gratuito y rápido gemini-2.5-flash
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )
                    
                    # Mostramos el resultado limpio en pantalla
                    st.success("¡Informe generado con éxito!")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"Error al conectar con la IA: {e}")
                    st.info("Asegúrate de haber guardado exactamente 'GEMINI_API_KEY' en la pestaña de Secrets en Streamlit.")
