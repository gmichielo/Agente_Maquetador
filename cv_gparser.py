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
    "linkedin": "",
    "provincia_pais": ""

  }},
  "perfil": "",
  "areas_especializacion": "",
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
- No inventes datos (ESTO SUPER IMPORTANTE)
- NO SUBAS NINGUN DATO A TU REGISTRO O MEMORIA
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
- Ordenar de forma de mas reciente a mas antigua teneiendo prioridad las que son Actuales (current, present,actualidad,etc...)
- Usa bullets • (no ●, no -, no *)
- NO devuelvas objetos, SOLO strings
- Mantén el orden cronológico original
- Si no hay experiencia, devuelve una lista vacía []

Además, el campo "experiencia_formateada" debe ser
la concatenación de todos los elementos de "experiencia"
separados por DOS saltos de línea.

REGLAS DE DIVERSOS ASPECTOS:
En la parte de provincia_pais obivamente si el CV lo indica pues colocar esa informacion, pero el
caso que no lo de pues hacer una estimacion por datos relevantes (educacion, experiencia laboral) e indicar con [Estimado].
Cualquier experiencia o educacion que haga referencia que esta en la actualidad (current, present,actualidad,etc...) tiene mas peso la ubicacion de esa

En la parte de areas_especializacion pues si el CV lo indica pues colocar esa informacion, pero el
caso que no lo de pues hacer una estimacion por datos relevantes (habilidades, experiencias laborales, proyectos) e indicar con [Estimado]

En la seccion de Skills simpre delvolver en este estilo (Grupo: Skills), Ejemplos: Herramientas: Git, Microsoft 365; Lenguajes: C#, Python

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
