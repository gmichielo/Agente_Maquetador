import pdfplumber
from docx import Document
from docx2pdf import convert
import platform
import re
import unicodedata
import shutil
import os
import time
import threading
import pythoncom

# 1. UTILIDADES
def normalize_text(text):
    # Mantiene acentos y caracteres especiales
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{2,}', '\n', text)
    return text.strip()


def read_pdf(path):
    blocks = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text(layout=True)
            if txt:
                blocks.append(txt)
    return "\n".join(blocks)


# 2. NORMALIZACION ATS
def rebuild_structure(text):
    headers = [
        "perfil profesional", "profile",
        "experiencia laboral", "work experience",
        "education", "educacion",
        "skills", "habilidades",
        "languages", "idiomas"
    ]

    for h in headers:
        text = re.sub(rf"\s*{h}\s*", f"\n{h.upper()}\n", text, flags=re.IGNORECASE)

    # Insertar salto de linea antes de cualquier • (u otros bullets) y mantener el simbolo
    text = re.sub(r"\s*([•\*\|▪●])\s*", r"\n\1 ", text)
    
    return normalize_text(text)

def normalize_experience_lines(lines):
    cleaned = []
    for l in lines:
        l = l.replace("|", "").strip()
        l = re.sub(r'^[●•\-]\s*', '', l)
        cleaned.append(l)
    return cleaned

# 3. FORMATEOS
DATE_REGEX = re.compile(
    r"""
    (
        # 03/2025 - 09/2025
        \d{2}/\d{4}\s*[-–]\s*(\d{2}/\d{4}|actualidad|present|current)
        |
        # 2013 - 2014
        \d{4}\s*[-–]\s*(\d{4}|actualidad|present|current)
        |
        # Mar 2015 - Sep 2017
        (ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic|
         enero|febrero|marzo|abril|mayo|junio|julio|agosto|
         septiembre|setiembre|octubre|noviembre|diciembre|
         jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)
        \s+\d{4}\s*[-–]\s*
        (
            (ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic|
             enero|febrero|marzo|abril|mayo|junio|julio|agosto|
             septiembre|setiembre|octubre|noviembre|diciembre|
             jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)
            \s+\d{4}
            |
            actualidad|present|current
        )
    )
    """,
    re.IGNORECASE | re.VERBOSE
)

def format_experiencia_bloques(bloques):
    salida = []
    for b in bloques:
        salida.append(
            f"""{b['fecha']}
Empresa: {b['empresa']}
Puesto: {b['puesto']}
Funciones:
""" + "\n".join(f"• {f}" for f in b["funciones"])
        )
    return "\n\n".join(salida)

def format_experiencia_plantilla(lines):
    bloques = []
    actual = None

    for l in lines:
        l = l.strip()
        if not l:
            continue

        # Fecha sola
        if DATE_REGEX.search(l) and len(l.split()) <= 6:
            if actual:
                actual["fecha"] = l
            continue

        # Puesto + fecha (EUROPASS)
        if DATE_REGEX.search(l) and " – " in l:
            if actual:
                actual["puesto"] = l.split(" – ")[0].strip()
                actual["fecha"] = " – ".join(l.split(" – ")[1:])
            continue

        # Empresa (EUROPASS ICONO / TEXTO)
        if "–" in l and any(city in l.lower() for city in ["madrid", "gijon", "oviedo", "spain"]):
            if actual:
                bloques.append(actual)
            actual = {
                "empresa": l.replace("", "").strip(),
                "puesto": "",
                "fecha": "",
                "funciones": []
            }
            continue

        # Eempresa clasica
        if l.isupper() and len(l.split()) <= 6:
            if actual:
                bloques.append(actual)
            actual = {
                "empresa": l,
                "puesto": "",
                "fecha": "",
                "funciones": []
            }
            continue

        if not actual:
            continue

        # Puesto
        if not actual["puesto"]:
            actual["puesto"] = l
            continue

        # Funciones
        actual["funciones"].append(l)

    if actual:
        bloques.append(actual)

    # Formato final
    salida = []
    for b in bloques:
        salida.append(
            f"""{b['fecha']}
Empresa: {b['empresa']}
Puesto: {b['puesto']}
Funciones:
""" + "\n".join(f"• {f}" for f in b["funciones"])
        )

    return "\n\n".join(salida)

def format_proyectos(lines):
    bloques = []
    actual = []

    for l in lines:
        # Titulo del proyecto
        if not l.startswith(("•", "-", "*")) and len(l.split()) <= 6:
            if actual:
                bloques.append("\n".join(actual))
                actual = []
            actual.append(l)
        else:
            actual.append(l)

    if actual:
        bloques.append("\n".join(actual))

    return "\n\n".join(bloques)

def clean_bullets(lines):
    return [re.sub(r'^[•\-\*]\s*', '', l) for l in lines]

def cv_json_to_docx_data(cv):
    return {
        "NOMBRE": cv.get("nombre") or "Nombre No detectado",
        "EMAIL": cv.get("contacto", {}).get("email") or "Email No detectado",
        "TELEFONO": cv.get("contacto", {}).get("telefono") or "Telefono No detectado",
        "GITHUB": cv.get("contacto", {}).get("github") or "Github No detectado",
        "LINKEDIN": cv.get("contacto", {}).get("linkedin") or "Linkedin No detectado",
        "UBI": cv.get("contacto", {}).get("provincia_pais") or "Ubicacion No detectado",

        "PERFIL": cv.get("perfil") or "Perfil No detectado",
        "ESPECIALIZACION": cv.get("areas_especializacion") or "Especializacion No detectado",

        "SKILLS": " | ".join(cv.get("skills", [])) or "Skills No detectado",
        "FORMACION": "\n".join(cv.get("educacion", [])) or "Formacion No detectado",
        "EDUCACION": "\n".join(cv.get("educacion", [])) or "Educacion No detectado",
        "CERTIFICACIONES": "\n".join(cv.get("certificaciones", [])) or "Certificacion No detectado",

        "EXPERIENCIA": cv.get("experiencia") or "Esperiencia No detectado",
        "EXPERIENCIA_PLANTILLA": cv.get("experiencia_formateada") or "ExperienciaP No detectado",

        "IDIOMAS": (
            "\n".join(f"• {k}: {v}" for k, v in cv.get("idiomas", {}).items())
        ) or "Idiomas No detectado",

        "PROYECTOS": cv.get("proyectos_formateados") or "Proyectos No detectado"
    }

def is_empty_value(v):
    if v is None:
        return True
    if isinstance(v, str) and not v.strip():
        return True
    if isinstance(v, (list, dict)) and len(v) == 0:
        return True
    return False

def replace_placeholders(doc, data, empty_text=""):
    def delete_paragraph(paragraph):
        p = paragraph._element
        p.getparent().remove(p)
        paragraph._p = paragraph._element = None

    # --------- PÁRRAFOS ---------
    for p in list(doc.paragraphs):  # 👈 list() importante
        full_text = p.text

        for k, v in data.items():
            placeholder = f"{{{{{k}}}}}"

            if placeholder not in full_text:
                continue

            if is_empty_value(v):
                # 👉 Si el párrafo SOLO tiene el placeholder → eliminar línea
                if full_text.strip() == placeholder:
                    delete_paragraph(p)
                    break
                else:
                    p.text = full_text.replace(placeholder, empty_text)
            else:
                p.text = full_text.replace(placeholder, str(v))

    # --------- TABLAS ---------
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in list(cell.paragraphs):
                    full_text = p.text

                    for k, v in data.items():
                        placeholder = f"{{{{{k}}}}}"

                        if placeholder not in full_text:
                            continue

                        if is_empty_value(v):
                            if full_text.strip() == placeholder:
                                delete_paragraph(p)
                                break
                            else:
                                p.text = full_text.replace(placeholder, empty_text)
                        else:
                            p.text = full_text.replace(placeholder, str(v))


def replace_placeholders_preserve_style(doc, data, empty_text=""):
    def replace_in_runs(runs, data):
        for run in runs:
            for k, v in data.items():
                placeholder = f"{{{{{k}}}}}"

                if placeholder not in run.text:
                    continue

                if is_empty_value(v):
                    run.text = run.text.replace(placeholder, empty_text)
                else:
                    run.text = run.text.replace(placeholder, str(v))

    # Parrafos
    for p in doc.paragraphs:
        replace_in_runs(p.runs, data)

    # Tablas
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    replace_in_runs(p.runs, data)


def generate_cv_from_template(
    template_path,
    cv_json,
    output_dir="output",
    plantilla_nombre="Plantilla"
    ):
    """
    Genera un DOCX y un PDF desde la plantilla usando docx2pdf.
    Usa threading + pythoncom.CoInitialize() para que funcione en Flask.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Preparar nombres unicos
    def sanitize(text):
        return re.sub(r'[^A-Za-z0-9_-]', '', text.replace(" ", "_"))

    safe_name = sanitize(cv_json["nombre"] or "CV")
    safe_plantilla = sanitize(plantilla_nombre)
    timestamp = int(time.time())

    docx_out = os.path.join(
        output_dir,
        f"CV_{safe_name}_{safe_plantilla}_{timestamp}.docx"
    )

    pdf_out = os.path.join(
        output_dir,
        f"CV_{safe_name}_{safe_plantilla}_{timestamp}.pdf"
    )

    # Limpiar archivos antiguos
    if os.path.exists(docx_out):
        os.remove(docx_out)
    if os.path.exists(pdf_out):
        os.remove(pdf_out)

    # Copiar plantilla y reemplazar placeholders
    shutil.copy(template_path, docx_out)
    doc = Document(docx_out)

    data = cv_json_to_docx_data(cv_json)

    # Reemplazo de placeholders
    replace_placeholders_preserve_style(doc, data)

    doc.save(docx_out)

    # Funcion para generar PDF en hilo separado
    pdf_generated = False

    def convert_pdf_thread():
        nonlocal pdf_generated
        try:
            pythoncom.CoInitialize()  # Inicializar COM en este hilo
            convert(docx_out, pdf_out)
            if os.path.exists(pdf_out):
                pdf_generated = True
        except Exception as e:
            print("Error generando PDF en hilo:", e)

    if platform.system().lower() == "windows":
        thread = threading.Thread(target=convert_pdf_thread)
        thread.start()
        thread.join()  # Esperamos a que termine el PDF

        if not pdf_generated:
            print("PDF no se pudo generar después de intentar en hilo.")
            pdf_out = None
    else:
        # En otros sistemas no se usa docx2pdf
        pdf_out = None

    # Devolver DOCX siempre, PDF si se genero
    return docx_out, pdf_out if pdf_generated else None