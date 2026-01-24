from openai import OpenAI
from dotenv import load_dotenv
import json
import os

load_dotenv()
client = OpenAI()

def parse_cv_with_gpt(cv_text: str, formatos: dict) -> dict:
    prompt = f"""
Eres un sistema ATS experto en análisis y extracción ESTRUCTURADA de CVs profesionales
para un MAQUETADOR AUTOMÁTICO de currículums.

TU SALIDA DEBE SER EXCLUSIVAMENTE UN JSON VÁLIDO.
NO incluyas explicaciones, comentarios, texto adicional ni markdown.
NO RESUMAS información salvo donde se indique explícitamente.
NO INVENTES datos bajo ningún concepto.

--------------------------------------------------
REGLA CRÍTICA ABSOLUTA
--------------------------------------------------
DEBES EXTRAER LA INFORMACIÓN TAL CUAL APARECE EN EL CV,
RESPETANDO LA SEPARACIÓN REAL DE EXPERIENCIAS Y EDUCACIONES.

PROHIBIDO:
- Unir varias experiencias en una sola
- Unir varias educaciones en una sola
- Convertir experiencia o educación en strings largos
- Mezclar experiencia con educación
- Inferir datos no explícitos

--------------------------------------------------
ESTRUCTURA JSON OBLIGATORIA (NO MODIFICABLE)
--------------------------------------------------
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
  "resumen": "",
  "resumen_profesional": "",
  "areas_especializacion": "",
  "anyos": "",
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

--------------------------------------------------
EXPERIENCIA LABORAL (REGLAS OBLIGATORIAS)
--------------------------------------------------
La clave "experiencia" DEBE ser una LISTA DE OBJETOS.
CADA EXPERIENCIA = UN TRABAJO DIFERENTE.

Cada objeto DEBE contener SOLO estas claves:
- fecha_inicio
- fecha_fin
- empresa (EN MAYÚSCULAS)
- puesto
- ubicacion
- funciones (lista de strings) con un salto de línea entre cada función (\n)

REGLAS DE PARSING:
- Detecta UNA experiencia por cada bloque real del CV
- NO mezcles empresas distintas
- NO mezcles fechas distintas
- NO combines funciones de trabajos diferentes
- Mantén el orden cronológico ORIGINAL (más reciente primero)
- Si la experiencia es actual: usa "Present", "Actualidad" o "Current" como fecha_fin

FUNCIONES:
- Cada función debe ser UNA FRASE LIMPIA
- SIN bullets (•, -, *, etc.)
- SIN etiquetas tipo "Funciones:"
- SIN formateo visual

--------------------------------------------------
EDUCACIÓN (REGLAS OBLIGATORIAS)
--------------------------------------------------
La clave "educacion" DEBE ser una LISTA DE OBJETOS.
CADA OBJETO = UNA FORMACIÓN DIFERENTE.

Claves obligatorias:
- fecha_inicio
- fecha_fin
- titulo
- institucion
- ubicacion
- nota_final

REGLAS CRÍTICAS:
- NUNCA devuelvas educación como string
- NUNCA unas dos titulaciones en una sola entrada
- Si hay varias líneas con fechas distintas → son educaciones distintas
- Si un dato no existe, deja el string vacío ""
- Si NO hay educación → devuelve []

--------------------------------------------------
FORMATO VISUAL (OBLIGATORIO)
--------------------------------------------------
NO INVENTES FORMATO.

REGLAS:
- Usa SOLO el formato de su sección
- NO mezcles formatos
- NO alteres etiquetas
- NO agregues texto
- Si una clave no existe → elimina ESA LÍNEA COMPLETA

--------------------------------------------------
RESÚMENES
--------------------------------------------------
"resumen" y "resumen_profesional":
- Redactados en tercera persona
- Basados ÚNICAMENTE en el CV
- NO inventes tecnologías, empresas ni roles
- NO extrapoles experiencia
- En el caso de "resumen_profesional" habla de lo que domina y años de experiencia en eso

Si NO existe sección "perfil":
- Copia EXACTAMENTE el contenido de "resumen" en "perfil"

--------------------------------------------------
AÑOS DE EXPERIENCIA
--------------------------------------------------
"anyos":
- Calcula a partir de fechas de experiencia
- Si no es exacto, usa estimación conservadora
- NO inventes
- Formato obligatorio: "X años de experiencia" o "X años y Y meses de experiencia"

--------------------------------------------------
SKILLS
--------------------------------------------------
Formato obligatorio por elemento:
"Grupo: skill1, skill2, skill3"

Ejemplo:
"Lenguajes: Java, Python"
"Herramientas: Git, Jenkins"

Incluye SIEMPRE soft skills en una línea separada.

--------------------------------------------------
PROVINCIAS Y ESPECIALIZACIÓN
--------------------------------------------------
provincia_pais:
- Usa la indicada en el CV
- Si NO existe → estima y añade [Estimado]
- La experiencia o educación ACTUAL tiene prioridad para estimar ubicación

areas_especializacion:
- Usa la indicada en el CV
- Si NO existe → estima según skills/experiencias y añade [Estimado]

--------------------------------------------------
DOCUMENTOS NO VÁLIDOS
--------------------------------------------------
Si el documento NO es un CV:
→ Devuelve el JSON con TODAS las claves vacías

Si el archivo NO es válido (no PDF/DOC):
→ Devuelve el JSON vacío

--------------------------------------------------
PROHIBICIONES ABSOLUTAS
--------------------------------------------------
- NO inventar datos
- NO añadir campos nuevos
- NO eliminar claves
- NO guardar datos en memoria
- NO usar markdown

--------------------------------------------------
CV A ANALIZAR:
\"\"\"
{cv_text}
\"\"\"
"""


    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "Eres un sistema ATS experto para un maquetador de CVs que realiza parsing de CVs."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)
