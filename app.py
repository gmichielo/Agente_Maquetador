from flask import Flask, render_template, request, send_file
import os
import threading
import webbrowser
import sys
from cv_gparser import parse_cv_with_gpt
from cv_adapter import adapt_gpt_cv_to_engine
from cv_engine import parse_cv, generate_cv_from_template
from cv_engine import read_pdf, rebuild_structure

app = Flask(__name__)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

BASE_DIR = os.path.abspath(".")

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")
TEMPLATES_FOLDER = os.path.join(BASE_DIR, "templates_docx")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

PLANTILLAS = {
    "1": "Plantilla1.docx",
    "2": "Plantilla2.docx",
    "3": "Plantilla3.docx",
    "4": "Plantilla4.docx"
}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        pdf_file = request.files.get("cv_pdf")
        plantilla_id = request.form.get("plantilla")

        if not pdf_file or not plantilla_id:
            return render_template("index.html", success=False, error="Faltan datos")

        print("📄 CV recibido:", pdf_file.filename)
        print("📄 Plantilla:", plantilla_id)

        # Limpiar output
        for f in os.listdir(OUTPUT_FOLDER):
            os.remove(os.path.join(OUTPUT_FOLDER, f))

        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
        pdf_file.save(pdf_path)

        plantilla_path = resource_path(
            os.path.join(
                "templates_docx",
                PLANTILLAS.get(plantilla_id)
            )
        )

        print("🔍 Parseando CV...")
        raw_text = read_pdf(pdf_path)
        clean_text = rebuild_structure(raw_text)

        cv_json = parse_cv_with_gpt(clean_text)
        cv_json = adapt_gpt_cv_to_engine(cv_json)
        
        print("✅ CV parseado:")
        print(cv_json)

        print("📝 Generando CV final...")
        docx_path, pdf_out = generate_cv_from_template(
            plantilla_path,
            cv_json,
            OUTPUT_FOLDER
        )

        return render_template(
            "index.html",
            success=True,
            nombre=cv_json.get("nombre", ""),
            docx=os.path.basename(docx_path),
            pdf=os.path.basename(pdf_out) if pdf_out else None
        )

    return render_template("index.html", success=False)

@app.route("/download/<filename>")
def download(filename):
    return send_file(
        os.path.join(OUTPUT_FOLDER, filename),
        as_attachment=True
    )

if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    threading.Timer(1.5, open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=False)