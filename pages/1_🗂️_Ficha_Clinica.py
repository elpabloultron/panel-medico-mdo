import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# --- VERIFICACIÓN DE SEGURIDAD (Hereda del login principal) ---
if "autenticado" not in st.session_state or not st.session_state.autenticado:
    st.warning("⚠️ Acceso denegado. Debe iniciar sesión en la página principal.")
    st.stop()

st.set_page_config(page_title="Ficha Clínica | MDO", page_icon="🗂️", layout="wide")

# Conexión a Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("🗂️ Módulo de Ficha Clínica")
st.markdown("Gestión de antecedentes y repositorio de exámenes.")
st.divider()

# 1. BUSCADOR DE PACIENTE
rut_busqueda = st.text_input("🔍 Ingrese RUT del paciente para buscar o crear ficha (Ej: 12345678-9)", max_chars=12)

if rut_busqueda:
    # Buscar datos demográficos en Supabase
    resp_paciente = supabase.table("pacientes").select("*").eq("rut", rut_busqueda).execute()
    datos_bd = resp_paciente.data[0] if resp_paciente.data else {}

    if datos_bd:
        st.success(f"✅ Paciente encontrado: **{datos_bd.get('nombre_completo', '')}**")
    else:
        st.info("ℹ️ RUT no registrado. Complete los datos abajo para crear una nueva Ficha Clínica Única.")

    # 2. PESTAÑAS DE NAVEGACIÓN
    tab_datos, tab_historial, tab_adjuntos = st.tabs([
        "📋 1. Antecedentes y Demografía", 
        "📖 2. Historial de Atenciones", 
        "📎 3. Subir Resultados"
    ])

    # --- PESTAÑA 1: DATOS DEMOGRÁFICOS ---
    with tab_datos:
        with st.form("formulario_ficha"):
            st.markdown("### Datos Personales")
            nombre = st.text_input("Nombre Completo", value=datos_bd.get("nombre_completo", ""))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                sexo_ops = ["Femenino", "Masculino", "Otro"]
                idx_sexo = sexo_ops.index(datos_bd.get("sexo", "Femenino")) if datos_bd.get("sexo") in sexo_ops else 0
                sexo = st.selectbox("Sexo Biológico / Registral", sexo_ops, index=idx_sexo)
            with col2:
                fecha_nac_str = datos_bd.get("fecha_nacimiento")
                fecha_nac_def = datetime.strptime(fecha_nac_str, "%Y-%m-%d").date() if fecha_nac_str else datetime(1990, 1, 1).date()
                fecha_nac = st.date_input("Fecha de Nacimiento", value=fecha_nac_def)
            with col3:
                prev_ops = ["FONASA", "ISAPRE", "Particular", "FFAA/Institucional"]
                idx_prev = prev_ops.index(datos_bd.get("prevision", "FONASA")) if datos_bd.get("prevision") in prev_ops else 0
                prevision = st.selectbox("Sistema de Salud", prev_ops, index=idx_prev)
            
            st.markdown("### Datos de Contacto")
            col4, col5 = st.columns(2)
            with col4:
                domicilio = st.text_input("Domicilio y Comuna", value=datos_bd.get("domicilio", ""))
                telefono = st.text_input("Teléfono de Contacto", value=datos_bd.get("telefono", ""))
            with col5:
                correo = st.text_input("Correo Electrónico", value=datos_bd.get("correo", ""))
            
            st.divider()
            if st.form_submit_button("💾 Guardar / Actualizar Ficha Clínica", type="primary"):
                if not nombre:
                    st.error("⚠️ El nombre es un campo obligatorio.")
                else:
                    payload = {
                        "rut": rut_busqueda, 
                        "nombre_completo": nombre, 
                        "sexo": sexo, 
                        "fecha_nacimiento": str(fecha_nac), 
                        "domicilio": domicilio, 
                        "telefono": telefono, 
                        "correo": correo, 
                        "prevision": prevision
                    }
                    supabase.table("pacientes").upsert(payload).execute()
                    st.success("Datos sincronizados correctamente en la base central.")
                    st.rerun()

    # --- PESTAÑA 2: HISTORIAL CLÍNICO ---
    with tab_historial:
        st.markdown("### Línea de Tiempo del Paciente")
        if not datos_bd:
            st.warning("Debe registrar y guardar los datos del paciente en la pestaña anterior para ver su historial.")
        else:
            # Buscar recetas emitidas (ACTUALIZADO A fecha_emision)
            resp_recetas = supabase.table("recetas").select("*").eq("rut_paciente", rut_busqueda).order("fecha_emision", desc=True).execute()
            
            # Buscar archivos adjuntos
            resp_archivos = supabase.table("archivos_adjuntos").select("*").eq("rut_paciente", rut_busqueda).order("fecha_subida", desc=True).execute()
            
            if not resp_recetas.data and not resp_archivos.data:
                st.info("No hay atenciones ni exámenes previos registrados para este paciente.")
            
            # --- Renderizar Recetas y Documentos ---
            for registro in resp_recetas.data:
                # Extraer la fecha correctamente con el nuevo nombre de columna
                fecha_str = registro.get("fecha_emision")
                try:
                    fecha = datetime.fromisoformat(str(fecha_str)).strftime("%d/%m/%Y a las %H:%M") if fecha_str else "Fecha no registrada"
                except ValueError:
                    fecha = str(fecha_str) # Por si la fecha se guardó en un formato distinto
                    
                datos = registro.get("datos_clinicos", {})
                tipo = datos.get("tipo", "Documento")
                folio = registro.get("folio", "N/A")
                
                with st.expander(f"📄 {fecha} | Emisión de {tipo} (Folio: {folio})"):
                    st.write(f"**Diagnóstico registrado:** {datos.get('diagnostico', 'N/A')}")
                    if tipo in ["SIMPLE", "RETENIDA", "CANNABIS"]:
                        st.write(f"**Prescripción:** {datos.get('medicamento', '')}")
                        st.write(f"**Indicaciones:** {datos.get('dosis', '')}")
                    elif tipo == "EXAMENES":
                        st.write(f"**Exámenes Solicitados:**\n{datos.get('lista', '')}")
            
            # --- Renderizar Archivos Adjuntos ---
            for archivo in resp_archivos.data:
                fecha_arch_str = archivo.get("fecha_subida")
                try:
                    fecha_arch = datetime.fromisoformat(str(fecha_arch_str)).strftime("%d/%m/%Y a las %H:%M") if fecha_arch_str else "Fecha no registrada"
                except ValueError:
                    fecha_arch = str(fecha_arch_str)
                    
                nombre_arch = archivo.get("nombre_archivo", "Documento Adjunto")
                
                with st.expander(f"📎 {fecha_arch} | Resultado Laboratorio/Imagen: {nombre_arch}"):
                    st.info(f"Tipo de archivo: {archivo.get('tipo_documento', 'N/A')}")

    # --- PESTAÑA 3: SUBIDA DE EXÁMENES ---
    with tab_adjuntos:
        st.markdown("### Repositorio de Resultados")
        if not datos_bd:
            st.warning("Debe guardar los datos del paciente primero para poder adjuntar archivos a su RUT.")
        else:
            st.write("Adjunte aquí los exámenes que el paciente traiga a la consulta (Laboratorio, Radiografías, etc).")
            tipo_archivo = st.text_input("Describa el examen (Ej: Perfil Bioquímico RedSalud - Marzo 2026)")
            archivo_subido = st.file_uploader("Arrastre el PDF o la foto aquí", type=["pdf", "jpg", "jpeg", "png"])
            
            if st.button("📤 Subir y adjuntar a la ficha", type="primary"):
                if archivo_subido and tipo_archivo:
                    with st.spinner("Subiendo archivo de forma segura..."):
                        # Crear nombre único para el archivo
                        nombre_seguro = f"{rut_busqueda}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{archivo_subido.name}"
                        
                        try:
                            # Subir a la bodega de Supabase
                            supabase.storage.from_("resultados_pacientes").upload(
                                path=nombre_seguro, 
                                file=archivo_subido.getvalue(), 
                                file_options={"content-type": archivo_subido.type}
                            )
                            
                            # Registrar en la tabla
                            supabase.table("archivos_adjuntos").insert({
                                "rut_paciente": rut_busqueda,
                                "nombre_archivo": tipo_archivo,
                                "tipo_documento": archivo_subido.type
                            }).execute()
                            
                            st.success("✅ Examen adjuntado exitosamente al historial del paciente.")
                        except Exception as e:
                            st.error(f"Hubo un error al subir el archivo: {e}")
                else:
                    st.error("⚠️ Debe ingresar una descripción y seleccionar un archivo.")
