from openai import OpenAI
from dotenv import load_dotenv
import json
import os

load_dotenv()
client = OpenAI()

def parse_cv_with_gpt(cv_text: str) -> dict:
    prompt = f"""
Eres un extractor de CVs profesionales.
Devuelve SOLO JSON válido, sin texto adicional.

La estructura debe ser EXACTAMENTE esta:

{{
  "nombre": "",
  "contacto": {{
    "email": "",
    "telefono": "",
    "github": "",
    "linkedin": ""
  }},
  "perfil": "",
  "skills": [],
  "experiencia": [],
  "experiencia_formateada": "",
  "educacion": [],
  "certificaciones": [],
  "idiomas": {{}},
  "proyectos": [],
  "proyectos_formateados": ""
}}

REGLAS IMPORTANTES:
- No inventes datos
- Mantén el orden original de skills y experiencia
- Usa bullets • cuando aplique
- Si una sección no existe, devuélvela vacía
- No agregues ningún campo extra

La sección "experiencia" DEBE devolverse como una LISTA DE STRINGS.
Cada string debe tener EXACTAMENTE este formato:

MM/YYYY - MM/YYYY
Empresa: NOMBRE_EMPRESA
Puesto: NOMBRE_PUESTO
Funciones:
• Función 1
• Función 2
• Función 3

REGLAS:
- Usa siempre "Empresa:", "Puesto:" y "Funciones:"
- Usa bullets • (no ●, no -, no *)
- NO devuelvas objetos, SOLO strings
- Mantén el orden cronológico original
- Si no hay experiencia, devuelve una lista vacía []

Además, el campo "experiencia_formateada" debe ser
la concatenación de todos los elementos de "experiencia"
separados por DOS saltos de línea.

CV A ANALIZAR:
\"\"\"
{cv_text}
\"\"\"
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Eres un sistema ATS experto en parsing de CVs."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)
