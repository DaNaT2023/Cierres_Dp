import streamlit as st
import sqlite3
import pandas as pd
import datetime
from google import genai  # Librería oficial de Google
from PIL import Image     # Para manejar la imagen que subas

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
    
    # --- AQUÍ RECUPERAMOS EL BROWSE FILE (SUBIR IMAGEN DEL RECUADRO) ---
    st.subheader("📸 Subir Recuadro Diario")
    imagen_subida = st.file_uploader("Arrastra o selecciona la foto del recuadro diario", type=["png", "jpg", "jpeg"])
    
    datos_automaticos = {}
    
    if imagen_subida is not None:
        st.image(imagen_subida, caption="Imagen cargada correctamente", width=300)
        
        if st.button("🔍 Leer Recuadro con IA"):
            with st.spinner("Analizando la foto del recuadro con Gemini..."):
                try:
                    # Abrir la imagen con PIL
                    img = Image.open(imagen_subida)
                    
                    # Conectar con el cliente de Google
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    
                    # Prompt estricto para extraer datos en formato clave-valor limpia
                    prompt_ocr = """
                    Analiza la imagen de este recuadro de caja de la tienda y extrae estrictamente los siguientes datos.
                    Responde ÚNICAMENTE en este formato exacto, sin textos adicionales, sin introducciones y sin marcas de formato (no uses bloques de código ```):
                    Tienda: [Número de tienda, ej: Tienda 1]
                    Turno: [Mañana o Noche]
                    Encargado: [Nombre del encargado]
                    Venta: [Número de la venta total sin símbolos]
                    Quebranto: [Número del quebranto, si es negativo mantén el signo menos, sin símbolos]
                    """
                    
                    # Gemini 2.5 Flash procesa texto e imágenes a la vez de forma nativa
                    response_ocr = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[img, prompt_ocr]
                    )
                    
                    texto_extraido = response_ocr.text
                    st.info("Datos detectados en la imagen:")
                    st.text(texto_extraido)
                    
                    # Procesar las líneas de texto para precargar el formulario abajo
                    for linea in texto_extraido.split("\n"):
                        if ":" in linea:
                            clave, valor = linea.split(":", 1)
                            datos_automaticos[clave.strip().lower()] = valor.strip()
                            
                    st.success("¡Datos leídos! Revisa el formulario abajo antes de guardar.")
                    
                except Exception as e:
                    st.error(f"Error al analizar la imagen: {e}")

    st.markdown("---")
    st.subheader("📝 Confirmar Datos del Formulario")
    
    # Rellenar inputs con lo que leyó la IA (o vacíos por defecto)
    tienda_def = datos_automaticos.get("tienda", "Tienda 1")
    lista_tiendas = [f"Tienda {i}" for i in range(1, 7)]
    tienda_idx = lista_tiendas.index(tienda_def) if tienda_def in lista_tiendas else 0
    
    turno_def = datos_automaticos.get("turno", "Mañana")
    turno_idx = 0 if turno_def.lower() == "mañana" else 1
    
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        tienda = st.selectbox("Selecciona tu Tienda", lista_tiendas, index=tienda_idx)
        turno = st.radio("Turno Actual", ["Mañana", "Noche"], index=turno_idx)
        encargado = st.text_input("Nombre del Encargado", value=datos_automaticos.get("encargado", ""))
        
    with col_der:
        fecha = st.date_input("Fecha del Recuadro", datetime.date.today())
        
        try:
            venta_val = float(datos_automaticos.get("venta", 0.0))
        except:
            venta_val = 0.0
        venta = st.number_input("Venta Total del Turno (€)", min_value=0.0, step=10.0, value=venta_val)
        
        try:
            quebranto_val = float(datos_automaticos.get("quebranto", 0.0))
        except:
            quebranto_val = 0.0
        quebranto = st.number_input("Importe del Quebranto (€)", step=5.0, value=quebranto_val)

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
        
        st.markdown("---")
        st.markdown("### 🤖 Auditoría Automatizada con IA")
        st.write("Genera un reporte estratégico analizando las desviaciones y rendimientos de las 6 tiendas.")
        
        if st.button("📊 Generar Informe con Gemini"):
            with st.spinner("Analizando métricas y registros con Google Gemini..."):
                try:
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    datos_texto = df.to_string(index=False)
                    
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
                    
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )
                    
                    st.success("¡Informe generado con éxito!")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"Error al conectar con la IA: {e}")
