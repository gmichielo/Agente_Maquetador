from openai import OpenAI
from dotenv import load_dotenv
import json
import os

load_dotenv()
client = OpenAI()

def parse_cv_with_gpt(cv_text: str, formatos: dict) -> dict:
    prompt = f"""
Eres un sistema especializado en analizar y extraer información estructurada desde CVs profesionales.
Tu salida DEBE ser EXCLUSIVAMENTE un JSON válido.
NO incluyas explicaciones, comentarios, texto adicional ni markdown.
NO RESUMAS NADA, TODA LA INFORMACION QUE SALGA EN EL CV COLOCALA EN SU SITIO TAL CUAL EL CV

La respuesta DEBE seguir EXACTAMENTE la siguiente estructura JSON.
No alteres nombres de claves, no cambies tipos de datos y no agregues campos nuevos.
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

La clave "experiencia" DEBE ser una lista de objetos.
Cada objeto representa una experiencia laboral individual y DEBE contener SOLO las siguientes claves:
- fecha_inicio
- fecha_fin
- empresa (ESTO TODO EN MAYUSCULAS)
- puesto
- ubicacion
- funciones (lista de strings)

La clave "educacion" DEBE ser una lista de objetos.
Cada objeto representa una formación académica y DEBE contener SOLO las siguientes claves:
- fecha_inicio
- fecha_fin
- institucion
- titulo
- ubicacion
- nota_final

IMPORTANTE
La clave "resumen" DEBE contener un resumen profesional redactado en tercera persona,
basado ÚNICAMENTE en la información presente en el CV.
NO inventes información ni extrapoles cargos, empresas o tecnologías no mencionadas, ejemplo:
"Perfil con titulación de técnico Superior en Desarrollo de Aplicaciones y 22 años de experiencia. Actualmente trabaja como analista AS400 en Zemsania para un cliente del sector retail, donde lleva a cabo tareas de análisis y testing de aplicaciones en entorno AS/400, coordinación de equipos técnicos, gestión y análisis de bases de datos en sistemas Iseries de IBM, y análisis funcional en entornos contables. Anteriormente, ha ocupado roles de jefe de proyecto en Capgemini y consultor en telecomunicaciones en Canadá. Ha trabajado en diversos sectores como retail, energética y telecomunicaciones, utilizando una amplia gama de tecnologías como iSeries AS/400, IBM/390, Sun Microsystems, entre otras. Posee un niel experto del inglés y francés debido a su residencia en Canadá"

Si el CV no contiene una sección explícita de "perfil", entonces copia EXACTAMENTE el contenido de "resumen" en el campo "perfil".

El campo "anyos" debe representar el total de años de experiencia profesional,
calculado a partir de las fechas de la sección "experiencia".
Si no se puede calcular con precisión, usa una estimación conservadora basada en las fechas disponibles.

En la clave de "resumen_profesional" DEBE contener un resumen profesional redactado en tercera persona,
basado ÚNICAMENTE en la información presente en el CV.
NO inventes información ni extrapoles cargos, empresas o tecnologías no mencionadas, ejemplo:
Profesional con experiencia en desarrollo de más de 4 años como fullstack, trabajando con Java en backend con Spring (Boot, Security, Batch) y en frontend con Angular (4 años).
Durante 2 años como arquitecto y otros dos desarrollador.
Versiones 9, 11, 14 sobre todo.
Desarrollo de microservicios y APIs REST con Spring Boot (y SOAP cuando ha sido necesario), en versiones de Java desde 7/8 hasta 15/17/21. Diseño de procesos por lotes con Spring Batch y descubrimiento de servicios con Spring Cloud/Eureka, integrando comunicación sincrónica vía HTTP y asíncrona con Kafka. Implementa validación y seguridad de peticiones con Jakarta Validation y gestión de tokens, y genero comunicaciones transaccionales con Thymeleaf. Trabajo habitual con Maven (proyectos multimódulo y librerías comunes) y Git con revisiones de código. En arquitectura aplica enfoque hexagonal para aislar el dominio, principios SOLID y Clean Code, diseño modelos de datos y defino contratos bajo API-First/Last. Despliega y opera en Kubernetes, y ha liderado migraciones de monolitos y aplicaciones legacy (JSP/Symfony/PHP) hacia microservicios Java, estandarizando componentes y acelerando el desarrollo alrededor de un 40%.

REGLA GENERAL DE ESAS SECCIONES: 
Si una sección no existe en el CV:
- Devuelve el campo vacío según su tipo ("" , [] , {{}})
- NO elimines la clave del JSON
- NO dejes valores incoherentes o nulos

Además recibirás un formato de experiencia y educación.
Debes generar los campos:
- experiencia_formateada: string único
- educacion_formateada: string único

Cada uno debe ser la concatenación de los elementos individuales,
separados por EXACTAMENTE dos saltos de línea (\n\n).

Cada string debe respetar EXACTAMENTE el formato recibido,
sustituyendo los placeholders {{clave}} por los valores del objeto.

REGLAS IMPORTANTES:
- Si el documento NO es un CV (por ejemplo: carta, oferta laboral, texto genérico):
    devuelve el JSON con TODAS las claves vacías.
    NO intentes inferir información.
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
caso que no lo de pues Si no se indica explícitamente provincia o país: realiza una estimación basada en experiencia o educación reciente, y agrega el sufijo literal: [Estimado]
Cualquier experiencia o educacion que haga referencia que esta en la actualidad (current, present,actualidad,etc...) tiene mas peso la ubicacion de esa

En la parte de areas_especializacion pues si el CV lo indica pues colocar esa informacion, pero el
caso que no lo de pues hacer una estimacion por datos relevantes (habilidades, experiencias laborales, proyectos) e indicar con [Estimado]

La sección "skills" DEBE contener strings con el formato:
"Grupo: skill1, skill2, skill3"
Ejemplos: Herramientas: Git, Microsoft 365; Lenguajes: C#, Python

Incluye SIEMPRE una línea adicional para soft skills, separada por un salto de línea.
En skills deben estar tambien tras un salto de linea el apartado de soft skills

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
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "Eres un sistema ATS experto para un maquetador de CVs que realiza parsing de CVs."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)
