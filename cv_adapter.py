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

def parse_education_block(block: str) -> dict:
    lines = [l.strip() for l in block.split("\n") if l.strip()]

    data = {
        "fecha_inicio": "",
        "fecha_fin": "",
        "titulo": "",
        "institucion": "",
        "ubicacion": "",
        "nota": ""
    }

    for l in lines:
        # Fechas tipo MM/YYYY - MM/YYYY o solo año
        if re.match(r"\d{2}/\d{4}", l):
            fechas = re.split(r"\s*[-–]\s*", l, maxsplit=1)
            data["fecha_inicio"] = fechas[0]
            data["fecha_fin"] = fechas[1] if len(fechas) > 1 else ""
            continue

        elif re.match(r"\d{4}\s*[-–]\s*\d{4}", l):
            y1, y2 = re.split(r"\s*[-–]\s*", l)
            data["fecha_inicio"] = f"01/{y1}"
            data["fecha_fin"] = f"12/{y2}"
            continue

        # Nota final
        if "gpa" in l.lower() or "nota" in l.lower() or "grade" in l.lower():
            data["nota"] = l
            continue

        # Ubicación (ciudad, país)
        if "," in l and any(c.isalpha() for c in l):
            data["ubicacion"] = l
            continue

        # Título e institución (heurística simple y eficaz)
        if not data["titulo"]:
            data["titulo"] = l
        elif not data["institucion"]:
            data["institucion"] = l

    return data


def safe(value: str, value_name: str, fallback="no detectado)") -> str:
    return value.strip() if value and value.strip() else f"{value_name} {fallback}"


def format_experience_dta(exp: dict) -> str:
    bloque = [
        f"{safe(exp['fecha_inicio'], "(Fecha inicio")} - {safe(exp['fecha_fin'], "(Fecha fin")}",
        f"Empresa: {safe(exp['empresa'], "(Empresa")}",
        f"Puesto: {safe(exp['puesto'], "(Puesto")}",
        "Funciones:"
    ]

    if exp["funciones"]:
        bloque += [f"• {f}" for f in exp["funciones"]]
    else:
        bloque.append("• (No encontrado)")

    return "\n".join(bloque)

def format_experience_europass(exp: dict) -> str:
    header = f"[] {safe(exp['empresa'], "(Empresa")} - {safe(exp.get('ubicacion'), "(Ubicacion")}"
    fechas = f"{safe(exp['fecha_inicio'], "(Fecha inicio")} - {safe(exp['fecha_fin'], "(Fecha fin")}"

    bloque = [
        header.strip(" -"),
        f"{safe(exp['puesto'], "(Puesto")} - {fechas}",
    ]

    if exp["funciones"]:
        bloque += [f"    • {f}" for f in exp["funciones"]]
    else:
        bloque.append("    • (No encontrado)")

    return "\n".join(bloque)


def format_education_dta(ed: dict) -> str:
    bloque = []

    bloque.append(
        f"{safe(ed['titulo'], "(Titulo")}, {safe(ed['institucion'], "(Institucion")}"
    )

    extras = ", ".join(
        safe(x, "(Ubicacion") for x in [ed["ubicacion"]] if x
    )

    if extras:
        bloque.append(extras + "\n")

    return "\n".join(bloque)

def format_education_europass(ed: dict) -> str:
    bloque = []

    linea = f"{safe(ed['fecha_inicio'], "(Fecha inicio")} - {safe(ed['fecha_fin'], "(Fecha fin")}"
    if ed["ubicacion"]:
        linea += f", {safe(ed['ubicacion'], "(Ubicacion")}"
    bloque.append(linea)

    bloque.append(
        f"{safe(ed['titulo'], "(Titulo")}, {safe(ed['institucion'], "(Institucion")}"
    )

    bloque.append("⎺" * 40)
    bloque.append(safe(ed["nota"], "(Nota")+ "\n")

    return "\n".join(bloque)


EXPERIENCE_FORMATTERS = {
    "Plantilla-DTA": format_experience_dta,
    "Plantilla-EUROPASS": format_experience_europass,
}

EDUCATION_FORMATTERS = {
    "Plantilla-DTA": format_education_dta,
    "Plantilla-EUROPASS": format_education_europass,
}

def adapt_gpt_cv_to_engine(cv: dict, plantilla_nombre="Plantilla-DTA") -> dict:
    """
    Normaliza el CV GPT al formato esperado por cv_engine
    """
    educacion_struct = []

    if cv.get("educacion"):
        for bloque in cv["educacion"]:
            if isinstance(bloque, str):
                educacion_struct.append(
                    parse_education_block(bloque)
                )

    formatter_ed = EDUCATION_FORMATTERS.get(
        plantilla_nombre,
        format_education_dta
    )

    cv["educacion"] = [
        formatter_ed(e) for e in educacion_struct
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
