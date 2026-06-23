import streamlit as st

# Configuración global de la página
st.set_page_config(page_title="MDO - Portal Médico", page_icon="🏥", layout="centered")

# --- SISTEMA DE LOGIN GLOBAL ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Acceso Restringido")
    st.markdown("Plataforma exclusiva de **Medicina Deportiva Osorno**.")
    clave = st.text_input("Ingrese la clave de acceso profesional", type="password")
    
    if st.button("Ingresar al Sistema", type="primary"):
        if clave == st.secrets["PASSWORD_MEDICO"]:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta.")
    st.stop()

# --- PANTALLA DE BIENVENIDA (Solo visible si entró la clave) ---
st.title("🏥 Sistema de Gestión Clínica")
st.success("✅ Sesión segura iniciada. Bienvenido, **Dr. Muñoz**.")

st.markdown("""
### 👈 Navegación de la Plataforma
Utilice el **menú lateral izquierdo** para acceder a los distintos módulos del sistema:

* **🗂️ Ficha Clínica:** Busque pacientes, actualice sus antecedentes, revise su historial y suba resultados de exámenes.
* **🏥 Emisión de Documentos:** (Próximamente agregaremos aquí tu motor de recetas).
""")
