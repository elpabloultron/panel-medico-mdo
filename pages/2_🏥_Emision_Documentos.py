import streamlit as st
import uuid
import os
import base64
import qrcode
from io import BytesIO
from datetime import datetime
from supabase import create_client, Client
from playwright.sync_api import sync_playwright

# --- VERIFICACIÓN DE SEGURIDAD ---
if "autenticado" not in st.session_state or not st.session_state.autenticado:
    st.warning("⚠️ Acceso denegado. Debe iniciar sesión en la página principal.")
    st.stop()

st.set_page_config(page_title="Emisión de Documentos | MDO", page_icon="🏥", layout="wide")

# Conexión a Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- INSTALADOR AUTOMÁTICO DE CHROMIUM ---
@st.cache_resource
def instalar_navegador():
    os.system("playwright install chromium")
instalar_navegador()

# --- CARGAR CATÁLOGO FONASA DESDE SUPABASE ---
@st.cache_data(ttl=86400)
def cargar_catalogo_fonasa():
    try:
        respuesta = supabase.table("catalogo_fonasa").select("codigo, descripcion").execute()
        return [f"{fila['codigo']} | {fila['descripcion']}" for fila in respuesta.data]
    except Exception as e:
        # Modo de respaldo por si la tabla aún no se ha cargado
        return ["03-01-045 | Hemograma", "03-02-075 | Perfil Bioquímico"]

CATALOGO_FONASA = cargar_catalogo_fonasa()

# --- FUNCIÓN DEFINITIVA DE RENDERIZADO DE PDF ---
def generar_pdf_desde_html(html_modificado, nombre_archivo_salida):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Inyectar HTML y forzar espera de fuentes y dibujo de grilla (Combo forzado)
        page.set_content(html_modificado, wait_until="load")
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(1500)
        
        page.pdf(
            path=nombre_archivo_salida, 
            format="A4", 
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"}
        )
        browser.close()

# --- INTERFAZ DE USUARIO ---
st.title("🏥 Emisión de Documentos Médicos")
st.markdown("Generación inteligente de recetas y órdenes conectadas a la Ficha Clínica.")
st.divider()

# 1. BUSCADOR DE PACIENTE PARA AUTOCOMPLETADO
rut_emision = st.text_input("🔍 Ingrese RUT del paciente para cargar antecedentes (Ej: 12345678-9)", max_chars=12)

nombre_pac_bd = ""
domicilio_pac_bd = ""
edad_calculada = 30 # Valor numérico base para el componente de edad

if rut_emision:
    resp = supabase.table("pacientes").select("*").eq("rut", rut_emision).execute()
    if resp.data:
        paciente = resp.data[0]
        nombre_pac_bd = paciente.get("nombre_completo", "")
        domicilio_pac_bd = paciente.get("domicilio", "")
        
        if paciente.get("fecha_nacimiento"):
            try:
                nacimiento = datetime.strptime(paciente["fecha_nacimiento"], "%Y-%m-%d")
                edad_calculada = datetime.now().year - nacimiento.year
            except:
                pass
        st.success(f"✅ Ficha clínica vinculada: **{nombre_pac_bd}** ({edad_calculada} años)")
    else:
        st.info("ℹ️ Paciente no registrado en fichas. Los datos ingresados se usarán solo para este documento.")

# 2. SELECCIÓN DE DOCUMENTO
tipo_documento = st.selectbox(
    "¿Qué tipo de documento desea emitir?",
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

if tipo_documento == "Receta Cheque (Estupefacientes)":
    st.subheader("⚠️ Emisión de Receta Cheque Oficial")
    st.warning("Por normativa, las recetas cheque para estupefacientes solo pueden ser emitidas a través de la plataforma oficial del Estado.")
    st.link_button("➡️ Ir al Portal Oficial de Receta Cheque MINSAL", "https://prescripcion-receta.minsal.cl/auth/login", type="primary", use_container_width=True)

else:
    # 3. FORMULARIO MAESTRO
    with st.form("formulario_maestro"):
        st.subheader("📋 Datos del Paciente (Verificar)")
        col1, col2 = st.columns(2)
        with col1:
            rut_final = st.text_input("RUT del Paciente", value=rut_emision if rut_emision else "")
            nombre_final = st.text_input("Nombre Completo", value=nombre_pac_bd)
        with col2:
            edad_final = st.number_input("Edad", min_value=1, max_value=120, value=edad_calculada)
            domicilio_final = st.text_input("Domicilio y Ciudad", value=domicilio_pac_bd)

        st.divider()
        
        # --- BLOQUES CLÍNICOS DINÁMICOS ---
        if tipo_documento == "Receta Médica Simple":
            st.subheader("💊 Especificaciones de Receta Simple")
            diagnostico = st.text_input("Diagnóstico", value="Migraña")
            medicamento = st.text_input("Medicamento / Presentación", value="Paracetamol 500mg")
            dosis = st.text_input("Dosis e Indicaciones", value="1 tableta cada 8 horas por 3 días")
            duracion = st.text_input("Vigencia de la receta", value="30 días")
            via = st.selectbox("Vía de administración", ["Oral", "Sublingual", "Tópica"])
            ratio = "N/A"
            
        elif tipo_documento == "Receta Cannabis Terapéutico":
            st.subheader("🌿 Especificaciones de Cannabis Terapéutico")
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
            st.subheader("🔒 Especificaciones de Receta Retenida")
            diagnostico = st.text_input("Diagnóstico", value="Insomnio severo")
            medicamento = st.text_input("Principio Activo / Presentación", value="Zopiclona 7.5mg")
            dosis = st.text_input("Dosis exacta e indicaciones", value="1 tableta en la noche antes de dormir")
            duracion = st.text_input("Cantidad total a despachar", value="30 tabletas (Treinta)")
            via = st.selectbox("Vía de administración", ["Oral"])
            ratio = "N/A"
            
        elif tipo_documento == "Solicitud de Exámenes":
            st.subheader("🔬 Orden de Laboratorio e Imagenología (FONASA)")
            diagnostico = st.text_input("Diagnóstico de Sospecha / Hipótesis Clínica")
            
            # Buscador desde la base de datos de Fonasa
            examenes_seleccionados = st.multiselect(
                "Seleccione los exámenes del Arancel Oficial FONASA",
                options=CATALOGO_FONASA,
                placeholder="Escriba para buscar un examen..."
            )
            otros_examenes = st.text_area("Otros exámenes o indicaciones manuales (Opcional)")
            
        elif tipo_documento == "Licencia / Reposo Médico":
            st.subheader("🛌 Certificado de Reposo Médico")
            diagnostico = st.text_input("Diagnóstico Clínico")
            dias_reposo = st.number_input("Número de días de reposo", min_value=1, max_value=30, value=3)
            fecha_inicio = st.date_input("Fecha de inicio del reposo")

        st.divider()
        submit_button = st.form_submit_button(f"Emitir {tipo_documento} Electrónica", type="primary")

    # 4. LÓGICA DE PROCESAMIENTO Y GENERACIÓN
    if submit_button:
        if not rut_final or not nombre_final:
            st.error("⚠️ El RUT y el Nombre del paciente son campos obligatorios.")
        else:
            with st.spinner("Sincronizando con base de datos y dibujando PDF..."):
                try:
                    folio_generado = f"MDO-{str(uuid.uuid4())[:8].upper()}"
                    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                    
                    # Determinar plantillas y empaquetar payloads clínicos
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
                            lista_final_examenes = [f"- {ex}" for ex in examenes_seleccionados]
                            if otros_examenes.strip():
                                lista_final_examenes.append(otros_examenes)
                            texto_examenes_final = "\n".join(lista_final_examenes)
                            payload_clinico = {"tipo": "EXAMENES", "diagnostico": diagnostico, "lista": texto_examenes_final}
                        elif tipo_documento == "Licencia / Reposo Médico":
                            payload_clinico = {"tipo": "REPOSO", "diagnostico": diagnostico, "dias": dias_reposo, "inicio": str(fecha_inicio)}

                    # Insertar el registro en la tabla recetas enlazando al RUT del paciente
                    supabase.table("recetas").insert({
                        "folio": folio_generado, 
                        "rut_paciente": rut_final, 
                        "datos_clinicos": payload_clinico, 
                        "estado_documento": "VIGENTE"
                    }).execute()

                    # Generación dinámica del Código QR apuntando a tu Validador Público
                    url_validacion = f"https://portal-validacion-mdo.streamlit.app/?folio={folio_generado}"
                    qr = qrcode.make(url_validacion)
                    buffer = BytesIO()
                    qr.save(buffer, format="PNG")
                    qr_base64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")

                    # Leer y reemplazar tokens en la plantilla HTML correspondiente
                    with open(plantilla_archivo, "r", encoding="utf-8") as archivo:
                        html_plantilla = archivo.read()

                    html_plantilla = html_plantilla.replace("{{FOLIO}}", folio_generado)
                    html_plantilla = html_plantilla.replace("{{FECHA}}", fecha_hoy)
                    html_plantilla = html_plantilla.replace("{{NOMBRE}}", nombre_final)
                    html_plantilla = html_plantilla.replace("{{RUT}}", rut_final)
                    html_plantilla = html_plantilla.replace("{{QR_BASE64}}", qr_base64)
                    html_plantilla = html_plantilla.replace("{{DIAGNOSTICO}}", diagnostico)

                    if plantilla_archivo == "receta_maestra.html":
                        html_plantilla = html_plantilla.replace("{{ESTADO}}", "VIGENTE")
                        html_plantilla = html_plantilla.replace("{{EDAD}}", str(edad_final))
                        html_plantilla = html_plantilla.replace("{{DOMICILIO}}", domicilio_final)
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
                            html_plantilla = html_plantilla.replace("{{CONTENIDO_DINAMICO}}", texto_examenes_final.replace("\n", "<br>"))
                        elif tipo_documento == "Licencia / Reposo Médico":
                            html_plantilla = html_plantilla.replace("{{TITULO_DOCUMENTO}}", "CERTIFICADO DE REPOSO MÉDICO")
                            texto_reposo = f"Se indica reposo médico por <strong>{dias_reposo} días</strong> a contar del <strong>{fecha_inicio.strftime('%d/%m/%Y')}</strong> inclusive."
                            html_plantilla = html_plantilla.replace("{{CONTENIDO_DINAMICO}}", texto_reposo)

                    # Renderizar e imprimir PDF con la configuración forzada de la nube
                    nombre_pdf = f"{folio_generado}.pdf"
                    generar_pdf_desde_html(html_plantilla, nombre_pdf)

                    # Subir archivo PDF a la bodega de recetas en Supabase
                    with open(nombre_pdf, "rb") as f:
                        supabase.storage.from_("recetas").upload(path=nombre_pdf, file=f, file_options={"content-type": "application/pdf", "x-upsert": "true"})
                    
                    supabase.table("recetas").update({"url_pdf_original": nombre_pdf}).eq("folio", folio_generado).execute()

                    st.success(f"🎉 Documento emitido con éxito. Folio: {folio_generado}")
                    
                    with open(nombre_pdf, "rb") as pdf_file:
                        st.download_button(label="📄 Descargar Documento Médico PDF", data=pdf_file, file_name=nombre_pdf, mime="application/pdf", key=folio_generado)

                except Exception as e:
                    st.error(f"Error en el procesamiento clínico: {e}")
