import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# --- VERIFICACIÓN DE SEGURIDAD ---
if "autenticado" not in st.session_state or not st.session_state.autenticado:
    st.warning("⚠️ Acceso denegado. Debe iniciar sesión en la página principal.")
    st.stop()

st.set_page_config(page_title="Emisión de Documentos | MDO", page_icon="🏥", layout="wide")

# Conexión a Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("🏥 Emisión de Documentos Médicos")
st.markdown("Generación de recetas, órdenes de exámenes y certificados.")
st.divider()

# 1. BUSCADOR INTELIGENTE (Conectado a la Ficha Clínica)
rut_emision = st.text_input("🔍 Ingrese RUT del paciente para autocompletar datos (Ej: 12345678-9)", max_chars=12)

# Variables vacías por defecto
nombre_pac_bd = ""
edad_pac_bd = ""
domicilio_pac_bd = ""

if rut_emision:
    # Consultar a la base de datos central
    resp = supabase.table("pacientes").select("*").eq("rut", rut_emision).execute()
    
    if resp.data:
        paciente = resp.data[0]
        nombre_pac_bd = paciente.get("nombre_completo", "")
        domicilio_pac_bd = paciente.get("domicilio", "")
        
        # Calcular la edad automáticamente a partir de la fecha de nacimiento
        if paciente.get("fecha_nacimiento"):
            try:
                nacimiento = datetime.strptime(paciente["fecha_nacimiento"], "%Y-%m-%d")
                edad_pac_bd = f"{datetime.now().year - nacimiento.year} años"
            except:
                pass
                
        st.success(f"✅ Datos cargados automáticamente desde la Ficha de **{nombre_pac_bd}**.")
    else:
        st.info("ℹ️ Paciente no encontrado en la base de datos. Los datos ingresados en el formulario no se guardarán en la ficha hasta que lo registre en el Módulo 'Ficha Clínica'.")

st.markdown("### Datos del Documento")

# 2. EL FORMULARIO DE EMISIÓN
with st.form("formulario_emision"):
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        # El parámetro 'value' inyecta lo que el buscador encontró
        nombre_input = st.text_input("Nombre del Paciente", value=nombre_pac_bd)
    with col2:
        edad_input = st.text_input("Edad", value=edad_pac_bd)
    with col3:
        domicilio_input = st.text_input("Domicilio", value=domicilio_pac_bd)
        
    st.divider()
    
    st.write("*(Aquí migraremos tu bloque de Medicamentos, Diagnósticos y el botón de generar PDF...)*")
    
    # Botón temporal para probar el formulario
    submit_emision = st.form_submit_button("Generar Documento", type="primary")
