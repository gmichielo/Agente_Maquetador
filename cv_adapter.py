import re

def parse_dta_experience_block(block: str) -> dict:
    lines = [l.strip() for l in block.split("\n") if l.strip()]

    data = {
        "empresa": "",
        "ubicacion": "",
        "puesto": "",
        "fecha_inicio": "",
        "fecha_fin": "",
        "funciones": []
    }

    if lines:
        # Caso MM/YYYY - MM/YYYY | MM/YYYY - CURRENT
        if re.match(r"\d{2}/\d{4}", lines[0]):
            fechas = re.split(r"\s*-\s*", lines[0], maxsplit=1)
            data["fecha_inicio"] = fechas[0].strip()
            data["fecha_fin"] = fechas[1].strip() if len(fechas) > 1 else ""

        # Caso solo año → normalizamos
        elif re.match(r"\d{4}$", lines[0]):
            data["fecha_inicio"] = f"01/{lines[0]}"
            data["fecha_fin"] = f"12/{lines[0]}"

    for l in lines[1:]:
        if l.startswith("Empresa:"):
            data["empresa"] = l.replace("Empresa:", "").strip()
        elif l.startswith("Puesto:"):
            data["puesto"] = l.replace("Puesto:", "").strip()
        elif l.startswith("•"):
            text = l.replace("•", "").strip()
            if text.lower() != "funciones:":
                data["funciones"].append(text)

    return data

def format_experience_dta(exp: dict) -> str:
    bloque = [
        f"{exp['fecha_inicio']} - {exp['fecha_fin']}",
        f"Empresa: {exp['empresa']}",
        f"Puesto: {exp['puesto']}",
        "Funciones:"
    ]
    bloque += [f"• {f}" for f in exp["funciones"]]
    return "\n".join(bloque)


def format_experience_europass(exp: dict) -> str:
    header = f"{exp['empresa']} - {exp.get('ubicacion', '').strip()}"
    fechas = f"{exp['fecha_inicio']} - {exp['fecha_fin']}"
    bloque = [
        header.strip(" -"),
        f"{exp['puesto']} - {fechas}",
    ]
    bloque += [f"    • {f}" for f in exp["funciones"]]
    return "\n".join(bloque)


EXPERIENCE_FORMATTERS = {
    "Plantilla-DTA": format_experience_dta,
    "Plantilla-EUROPASS": format_experience_europass,
}

def adapt_gpt_cv_to_engine(cv: dict, plantilla_nombre="Plantilla-DTA") -> dict:
    """
    Normaliza el CV GPT al formato esperado por cv_engine
    """
    # Educacion
    if cv.get("educacion") and isinstance(cv["educacion"], list):
        if cv["educacion"] and isinstance(cv["educacion"][0], dict):
            cv["educacion"] = [
                " - ".join(
                    filter(None, [
                        e.get("titulo"),
                        e.get("institucion"),
                        e.get("periodo")
                    ])
                )
                for e in cv["educacion"]
            ]

    # Experiencia (Dict a formato de plantilla)
    experiencias_struct = []

    if cv.get("experiencia"):
        for bloque in cv["experiencia"]:
            if isinstance(bloque, str):
                experiencias_struct.append(
                    parse_dta_experience_block(bloque)
                )

    formatter = EXPERIENCE_FORMATTERS.get(
        plantilla_nombre,
        format_experience_dta  # fallback
    )

    bloques_formateados = [
        formatter(e) for e in experiencias_struct
    ]

    cv["experiencia_formateada"] = "\n\n".join(bloques_formateados)

    # Fallback de seguridad
    if not cv.get("experiencia_formateada"):
        cv["experiencia_formateada"] = ""

    return cv
