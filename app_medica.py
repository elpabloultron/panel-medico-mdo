import streamlit as st
import uuid
import os
from datetime import datetime
from supabase import create_client, Client
from playwright.sync_api import sync_playwright

import qrcode
import base64
from io import BytesIO

# --- CONFIGURACIÓN VISUAL Y DE SEGURIDAD ---
st.set_page_config(page_title="Centro Médico Digital - MDO", layout="centered")

# --- INSTALACIÓN AUTOMÁTICA PARA LA NUBE (PLAYWRIGHT) ---
@st.cache_resource
def instalar_navegador():
    os.system("playwright install chromium")
instalar_navegador()
# --------------------------------------------------------

# --- SISTEMA DE LOGIN (MURO DE SEGURIDAD) ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Acceso Restringido")
    st.markdown("Plataforma exclusiva de **Medicina Deportiva Osorno**.")
    clave = st.text_input("Ingrese la clave de acceso profesional", type="password")
    if st.button("Ingresar al Panel", type="primary"):
        # Verificamos contra la contraseña guardada en la bóveda de Streamlit Cloud
        if clave == st.secrets["PASSWORD_MEDICO"]:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta o acceso denegado.")
    st.stop() # Detiene la ejecución si no está logueado
# --------------------------------------------

# 1. Conexión Supabase (Ahora usa Secretos Seguros)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generar_pdf_desde_html(html_modificado, nombre_archivo_salida):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_modificado)
        page.pdf(path=nombre_archivo_salida, format="A4", print_background=True)
        browser.close()

# 2. Interfaz Principal (Solo visible si pasó el login)
st.title("🏥 Sistema de Emisión Médica Digital")
st.markdown(f"Bienvenido, **Dr. Muñoz** | Sesión Segura Iniciada ✅")

# Selector Maestro de Documento
tipo_documento = st.selectbox(
    "¿Qué tipo de documento desea emitir hoy?",
    [
        "Receta Médica Simple", 
        "Receta Cannabis Terapéutico", 
        "Receta Médica Retenida", 
        "Receta Cheque (Estupefacientes)", 
        "Solicitud de Exámenes", 
        "Licencia / Reposo Médico"
    ]
)
st.divider()

# CASO EXCEPCIONAL: Receta Cheque
if tipo_documento == "Receta Cheque (Estupefacientes)":
    st.subheader("⚠️ Emisión de Receta Cheque Oficial")
    st.warning("Por normativa, las recetas cheque para estupefacientes solo pueden ser emitidas a través de la plataforma oficial del Estado.")
    st.link_button("➡️ Ir al Portal Oficial de Receta Cheque MINSAL", "https://prescripcion-receta.minsal.cl/auth/login", type="primary", use_container_width=True)

# CASOS REGULARES
else:
    with st.form("formulario_maestro"):
        st.subheader("📋 Datos Obligatorios del Paciente")
        col1, col2 = st.columns(2)
        with col1:
            rut = st.text_input("RUT del Paciente (ej: 12345678-9)")
            nombre = st.text_input("Nombre Completo")
        with col2:
            edad = st.number_input("Edad", min_value=1, max_value=120, value=30)
            domicilio = st.text_input("Domicilio y Ciudad")

        st.divider()
        
        # Formulario Dinámico
        if tipo_documento == "Receta Médica Simple":
            st.subheader("💊 Especificaciones de Receta Simple")
            diagnostico = st.text_input("Diagnóstico", value="Migraña")
            medicamento = st.text_input("Medicamento / Presentación", value="Paracetamol 500mg")
            dosis = st.text_input("Dosis e Indicaciones", value="1 tableta cada 8 horas por 3 días")
            duracion = st.text_input("Vigencia de la receta", value="30 días")
            via = st.selectbox("Vía de administración", ["Oral", "Sublingual", "Tópica"])
            ratio = "N/A"
            
        elif tipo_documento == "Receta Cannabis Terapéutico":
            st.subheader("🌿 Especificaciones de Cannabis Terapéutico (No Retenible)")
            diagnostico = st.text_input("Diagnóstico Principal", value="Dolor crónico")
            medicamento = "Flores / Extracto de Cannabis"
            duracion = st.text_input("Duración del tratamiento", value="30 días")
            col3, col4 = st.columns(2)
            with col3:
                ratio = st.selectbox("Ratio THC/CBD", ["1:1 THC/CBD", "10:1 THC/CBD", "1:10 THC/CBD"])
                via = st.selectbox("Vía de administración", ["Sublingual", "Vaporización", "Tópica"])
            with col4:
                dosis = st.text_input("Dosis", value="5 gotas cada 12 horas")
                
        elif tipo_documento == "Receta Médica Retenida":
            st.subheader("🔒 Especificaciones de Receta Retenida (Controlados)")
            diagnostico = st.text_input("Diagnóstico", value="Insomnio severo")
            medicamento = st.text_input("Principio Activo / Presentación", value="Zopiclona 7.5mg")
            dosis = st.text_input("Dosis exacta e indicaciones", value="1 tableta en la noche antes de dormir")
            duracion = st.text_input("Cantidad total a despachar", value="30 tabletas (Treinta)")
            via = st.selectbox("Vía de administración", ["Oral"])
            ratio = "N/A"
            
        elif tipo_documento == "Solicitud de Exámenes":
            st.subheader("🔬 Orden de Laboratorio e Imagenología")
            diagnostico = st.text_input("Diagnóstico de Sospecha / Hipótesis Clínica")
            examenes_solicitados = st.text_area("Escriba la lista de exámenes (uno por línea)", value="- Perfil Bioquímico\n- Hemograma Completo")
            
        elif tipo_documento == "Licencia / Reposo Médico":
            st.subheader("🛌 Certificado de Reposo Médico")
            diagnostico = st.text_input("Diagnóstico Clínico")
            dias_reposo = st.number_input("Número de días de reposo", min_value=1, max_value=30, value=3)
            fecha_inicio = st.date_input("Fecha de inicio del reposo")

        st.divider()
        submit_button = st.form_submit_button(f"Emitir {tipo_documento} Electrónica", type="primary")

    # 4. Lógica de Procesamiento
    if submit_button:
        if not rut or not nombre:
            st.error("⚠️ El RUT y el Nombre del paciente son campos obligatorios.")
        else:
            with st.spinner("Generando documento reglamentario..."):
                try:
                    folio_generado = f"MDO-{str(uuid.uuid4())[:8].upper()}"
                    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                    
                    supabase.table("pacientes").upsert({"rut": rut, "nombre_completo": nombre, "domicilio": domicilio}).execute()

                    if tipo_documento in ["Receta Médica Simple", "Receta Cannabis Terapéutico", "Receta Médica Retenida"]:
                        plantilla_archivo = "receta_maestra.html"
                        if tipo_documento == "Receta Médica Simple":
                            payload_clinico = {"tipo": "SIMPLE", "diagnostico": diagnostico, "medicamento": medicamento, "dosis": dosis, "duracion": duracion, "via": via, "ratio": ratio}
                        elif tipo_documento == "Receta Cannabis Terapéutico":
                            payload_clinico = {"tipo": "CANNABIS", "diagnostico": diagnostico, "medicamento": medicamento, "duracion": duracion, "ratio": ratio, "dosis": dosis, "via": via}
                        elif tipo_documento == "Receta Médica Retenida":
                            payload_clinico = {"tipo": "RETENIDA", "diagnostico": diagnostico, "medicamento": medicamento, "dosis": dosis, "duracion": duracion, "via": via, "ratio": ratio}
                    
                    else:
                        plantilla_archivo = "documento_clinico.html"
                        if tipo_documento == "Solicitud de Exámenes":
                            payload_clinico = {"tipo": "EXAMENES", "diagnostico": diagnostico, "lista": examenes_solicitados}
                        elif tipo_documento == "Licencia / Reposo Médico":
                            payload_clinico = {"tipo": "REPOSO", "diagnostico": diagnostico, "dias": dias_reposo, "inicio": str(fecha_inicio)}

                    supabase.table("recetas").insert({
                        "folio": folio_generado, "rut_paciente": rut, "datos_clinicos": payload_clinico, "estado_documento": "VIGENTE"
                    }).execute()

                    # ========================================================
                    # ¡IMPORTANTE! Reemplaza la URL de abajo con la URL REAL 
                    # de tu Portal de Validación público de Farmacia.
                    # ========================================================
                    url_validacion = f"https://TU-URL-REAL-DE-STREAMLIT.app/?folio={folio_generado}"
                    qr = qrcode.make(url_validacion)
                    buffer = BytesIO()
                    qr.save(buffer, format="PNG")
                    qr_base64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")

                    with open(plantilla_archivo, "r", encoding="utf-8") as archivo:
                        html_plantilla = archivo.read()

                    html_plantilla = html_plantilla.replace("{{FOLIO}}", folio_generado)
                    html_plantilla = html_plantilla.replace("{{FECHA}}", fecha_hoy)
                    html_plantilla = html_plantilla.replace("{{NOMBRE}}", nombre)
                    html_plantilla = html_plantilla.replace("{{RUT}}", rut)
                    html_plantilla = html_plantilla.replace("{{QR_BASE64}}", qr_base64)
                    html_plantilla = html_plantilla.replace("{{DIAGNOSTICO}}", diagnostico)

                    if plantilla_archivo == "receta_maestra.html":
                        html_plantilla = html_plantilla.replace("{{ESTADO}}", "VIGENTE")
                        html_plantilla = html_plantilla.replace("{{EDAD}}", str(edad))
                        html_plantilla = html_plantilla.replace("{{DOMICILIO}}", domicilio)
                        html_plantilla = html_plantilla.replace("{{MEDICAMENTO}}", medicamento)
                        html_plantilla = html_plantilla.replace("{{DOSIS}}", dosis)
                        html_plantilla = html_plantilla.replace("{{VIA}}", via)
                        html_plantilla = html_plantilla.replace("{{DURACION}}", duracion)
                        html_plantilla = html_plantilla.replace("{{RATIO}}", ratio)

                        if tipo_documento == "Receta Médica Simple":
                            html_plantilla = html_plantilla.replace("{{TITULO_DOCUMENTO}}", "RECETA MÉDICA")
                            html_plantilla = html_plantilla.replace("{{SUBTITULO_DOCUMENTO}}", "Prescripción General")
                            html_plantilla = html_plantilla.replace("{{TEXTO_USO}}", "")
                        elif tipo_documento == "Receta Médica Retenida":
                            html_plantilla = html_plantilla.replace("{{TITULO_DOCUMENTO}}", "RECETA RETENIDA")
                            html_plantilla = html_plantilla.replace("{{SUBTITULO_DOCUMENTO}}", "Medicamentos Controlados")
                            html_plantilla = html_plantilla.replace("{{TEXTO_USO}}", "Documento sujeto a inhabilitación en farmacia")
                        elif tipo_documento == "Receta Cannabis Terapéutico":
                            html_plantilla = html_plantilla.replace("{{TITULO_DOCUMENTO}}", "RECETA MÉDICA")
                            html_plantilla = html_plantilla.replace("{{SUBTITULO_DOCUMENTO}}", "CANNABIS MEDICINAL")
                            html_plantilla = html_plantilla.replace("{{TEXTO_USO}}", "Uso terapéutico individual y personal")

                    elif plantilla_archivo == "documento_clinico.html":
                        if tipo_documento == "Solicitud de Exámenes":
                            html_plantilla = html_plantilla.replace("{{TITULO_DOCUMENTO}}", "SOLICITUD DE EXÁMENES")
                            html_plantilla = html_plantilla.replace("{{CONTENIDO_DINAMICO}}", examenes_solicitados.replace("\n", "<br>"))
                        elif tipo_documento == "Licencia / Reposo Médico":
                            html_plantilla = html_plantilla.replace("{{TITULO_DOCUMENTO}}", "CERTIFICADO DE REPOSO MÉDICO")
                            texto_reposo = f"Se indica reposo médico por <strong>{dias_reposo} días</strong> a contar del <strong>{fecha_inicio.strftime('%d/%m/%Y')}</strong> inclusive."
                            html_plantilla = html_plantilla.replace("{{CONTENIDO_DINAMICO}}", texto_reposo)

                    nombre_pdf = f"{folio_generado}.pdf"
                    generar_pdf_desde_html(html_plantilla, nombre_pdf)

                    with open(nombre_pdf, "rb") as f:
                        supabase.storage.from_("recetas").upload(path=nombre_pdf, file=f, file_options={"content-type": "application/pdf", "x-upsert": "true"})
                    
                    supabase.table("recetas").update({"url_pdf_original": nombre_pdf}).eq("folio", folio_generado).execute()

                    st.success(f"✅ Documento emitido con éxito. Tipo: {tipo_documento} | Folio: {folio_generado}")
                    
                    with open(nombre_pdf, "rb") as pdf_file:
                        st.download_button(label="📄 Descargar Documento Médico PDF", data=pdf_file, file_name=nombre_pdf, mime="application/pdf", key=folio_generado)

                except Exception as e:
                    st.error(f"Error en la generación dinámica: {e}")