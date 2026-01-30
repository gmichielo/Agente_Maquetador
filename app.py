from flask import Flask, render_template, request, send_file
from docx import Document
import os
import signal
import threading
import webbrowser
import sys
import time
from cv_gparser import parse_cv_with_gpt
from cv_adapter import adapt_gpt_cv_to_engine
from cv_engine import read_pdf, rebuild_structure, generate_cv_from_template, extract_format_blocks
app = Flask(__name__)

LAST_ACTIVITY = time.time()
IDLE_TIMEOUT = 300  # ⏱️ segundos (ej: 300 = 5 minutos)

def inactivity_watcher():
    global LAST_ACTIVITY

    while True:
        time.sleep(5)  # cada 5 segundos revisa
        idle_time = time.time() - LAST_ACTIVITY

        if idle_time > IDLE_TIMEOUT:
            print("🕒 Inactividad detectada. Cerrando app...")
            os.kill(os.getpid(), signal.SIGTERM)

@app.route("/activity", methods=["POST"])
def activity():
    global LAST_ACTIVITY
    LAST_ACTIVITY = time.time()
    return "", 204

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")
TEMPLATES_FOLDER = os.path.join(BASE_DIR, "templates_docx")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

PLANTILLAS = {
    "1": {
        "file": "PlantillaDTA.docx",
        "name": "Plantilla-DTA"
    },
    "2": {
        "file": "PlantillaEUROPASS.docx",
        "name": "Plantilla-EUROPASS"
    },
    "3": {
        "file": "PlantillaIBM.docx",
        "name": "Plantilla-IBM"
    },
    "4": {
        "file": "PlantillaNNT.docx",
        "name": "Plantilla-NNT"
    },
    "5": {
        "file": "PlantillaNNT_S.docx",
        "name": "Plantilla-NNT_S"
    },
    "6": {
        "file": "PlantillaINETUM.docx",
        "name": "Plantilla-INETUM"
    },
    "7": {
        "file": "PlantillaRICOH.docx",
        "name": "Plantilla-RICOH"
    },
    "8": {
        "file": "PlantillaSAPIENS.docx",
        "name": "Plantilla-SAPIENS"
    },
    "9": {
        "file": "PlantillaACCENTURE.docx",
        "name": "Plantilla-ACCENTURE"
    },
    "10": {
        "file": "PlantillaTesteo.docx",
        "name": "Plantilla-Testeo"
    },
    "11": {
        "file": "PlantillaBasica.docx",
        "name": "Plantilla-Basica"
    }
}

LAST_CV_PATH = None
LAST_CV_JSON = None

@app.route("/", methods=["GET", "POST"])
def index():
    global LAST_CV_PATH, LAST_CV_JSON

    last_cv_exists = LAST_CV_PATH is not None and LAST_CV_JSON is not None

    if request.method == "POST":
        pdf_file = request.files.get("cv_pdf")
        plantilla_id = request.form.get("plantilla")
        reuse_last = request.form.get("reuse_last") == "1"

        if not plantilla_id:
            return render_template(
                "index.html",
                success=False,
                error="Faltan datos",
                last_cv_exists=last_cv_exists
            )
        
        print("📄 Plantilla:", plantilla_id)

        # -----------------------------
        # 1️⃣ Obtener CV
        # -----------------------------
        if reuse_last and last_cv_exists:
            print("♻️ Reutilizando CV en memoria")
            cv_json = LAST_CV_JSON
            pdf_path = LAST_CV_PATH
        else:
            if not pdf_file:
                return render_template(
                    "index.html",
                    success=False,
                    error="No se ha subido ningún CV",
                    last_cv_exists=last_cv_exists
                )

            pdf_path = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
            pdf_file.save(pdf_path)

            print("📄 CV recibido:", pdf_file.filename)

            print("🔍 Parseando CV...")
            # Parsear CV SOLO AQUÍ
            raw_text = read_pdf(pdf_path)
            clean_text = rebuild_structure(raw_text)

            doc_tmp = Document(
                os.path.join(
                    BASE_DIR,
                    "templates_docx",
                    PLANTILLAS[plantilla_id]["file"]
                )
            )
            format_blocks = extract_format_blocks(doc_tmp)

            cv_json = parse_cv_with_gpt(clean_text, format_blocks)

            # Cachear
            LAST_CV_PATH = pdf_path
            LAST_CV_JSON = cv_json
            last_cv_exists = True

        # -----------------------------
        # 2️⃣ Limpiar output
        # -----------------------------
        for f in os.listdir(OUTPUT_FOLDER):
            os.remove(os.path.join(OUTPUT_FOLDER, f))

        # -----------------------------
        # 3️⃣ Generar CV
        # -----------------------------
        plantilla_info = PLANTILLAS.get(plantilla_id)
        plantilla_path = os.path.join(
            BASE_DIR,
            "templates_docx",
            plantilla_info["file"]
        )

        plantilla_nombre = plantilla_info["name"]

        cv_json = adapt_gpt_cv_to_engine(cv_json, plantilla_nombre)

        print("✅ CV parseado:")
        print(cv_json)

        print("\n📝 Generando CV final...")
        docx_path, pdf_out = generate_cv_from_template(
            plantilla_path,
            cv_json,
            OUTPUT_FOLDER,
            plantilla_nombre=plantilla_nombre
        )

        return render_template(
            "index.html",
            success=True,
            nombre=cv_json.get("nombre", ""),
            docx=os.path.basename(docx_path),
            pdf=os.path.basename(pdf_out) if pdf_out else None,
            last_cv_exists=last_cv_exists
        )

    return render_template(
        "index.html",
        success=False,
        last_cv_exists=last_cv_exists
    )


@app.route("/download/<filename>")
def download(filename):
    return send_file(
        os.path.join(OUTPUT_FOLDER, filename),
        as_attachment=True
    )

@app.route("/shutdown", methods=["POST"])
def shutdown():
    if request.remote_addr not in ("127.0.0.1", "::1"):
        return "No permitido", 403

    print("🛑 App cerrada por el usuario")
    os.kill(os.getpid(), signal.SIGTERM)
    return "Servidor detenido"

if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    threading.Thread(target=inactivity_watcher, daemon=True).start()
    threading.Timer(1.5, open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=False)