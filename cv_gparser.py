from openai import OpenAI
from dotenv import load_dotenv
import json
import os

load_dotenv()
client = OpenAI()

def parse_cv_with_gpt(cv_text: str, formatos: dict) -> dict:
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
  "educacion_formateada": "",
  "certificaciones": [],
  "idiomas": {{}},
  "proyectos": [],
  "proyectos_formateados": ""
}}

La sección "experiencia" debe devolverse como una LISTA DE OBJETOS con estas claves:
- fecha_inicio
- fecha_fin
- empresa
- puesto
- ubicacion
- funciones (lista de strings)

La sección "educacion" debe devolverse como una LISTA DE OBJETOS con estas claves:
- fecha_inicio
- fecha_fin
- institucion
- titulo
- ubicacion
- nota_final

REGLA GENERAL DE ESAS SECCIONES: 
Si alguna no se encutra o no existe por favor no la coloques pero tampoco dejes la linea en blanco, hazla coherente

Además recibirás un formato de experiencia y educación.
Debes generar:

- experiencia_formateada: LISTA DE STRINGS
- educacion_formateada: LISTA DE STRINGS

Cada string debe respetar EXACTAMENTE el formato recibido,
sustituyendo los placeholders {{clave}} por los valores del objeto.

REGLAS IMPORTANTES:
- Si no es un documento valido para consideralo un CV no lo proceses, devuelve el json sin rellenarlo
- Si no es archivo de un tipo valido (sea pdf, doc, etc) no lo proceses, devuelve el json sin rellenarlo
- No inventes datos (ESTO SUPER IMPORTANTE)
- NO SUBAS NINGUN DATO A TU REGISTRO O MEMORIA
- Mantén el orden original de skills
- Usa bullets • cuando aplique
- Si una sección no existe, devuélvela vacía
- No agregues ningún campo extra

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

Además, el campo "educacion_formateada" debe ser
la concatenación de todos los elementos de "educacion"
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
FORMATO EXACTO PARA EXPERIENCIA (OBLIGATORIO):
""
{formatos.get("EXPERIENCIA", "")}
""

FORMATO EXACTO PARA EDUCACION (OBLIGATORIO):
""
{formatos.get("EDUCACION", "")}
""

REGLAS DE FORMATO:
- Usa SOLO el formato correspondiente a cada sección
- NO mezcles formatos
- NO cambies etiquetas
- NO agregues texto fuera del formato
- Si una clave no existe, elimina la línea completa

{cv_text}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Eres un sistema ATS experto para un maquetador de CVs que realiza parsing de CVs."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)
