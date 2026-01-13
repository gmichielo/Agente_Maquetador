def adapt_gpt_cv_to_engine(cv: dict) -> dict:
    """
    Normaliza el CV GPT al formato esperado por cv_engine
    """

    # =========================
    # EDUCACION
    # =========================
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

    # =========================
    # EXPERIENCIA (DICT → FORMATO PLANTILLA)
    # =========================
    if cv.get("experiencia") and isinstance(cv["experiencia"], list):

        # ---- CASO 1: experiencia estructurada (dict) ----
        if cv["experiencia"] and isinstance(cv["experiencia"][0], dict):
            bloques = []

            for e in cv["experiencia"]:
                bloque = []

                if e.get("periodo"):
                    bloque.append(e["periodo"])

                if e.get("empresa"):
                    bloque.append(f"Empresa: {e['empresa']}")

                if e.get("puesto"):
                    bloque.append(f"Puesto: {e['puesto']}")

                if e.get("responsabilidades"):
                    bloque.append("Funciones:")
                    for f in e["responsabilidades"]:
                        bloque.append(f"• {f}")

                bloques.append("\n".join(bloque))

            cv["experiencia"] = bloques
            cv["experiencia_formateada"] = "\n\n".join(bloques)

        # ---- CASO 2: experiencia ya en texto plano ----
        elif cv["experiencia"] and isinstance(cv["experiencia"][0], str):
            cv["experiencia_formateada"] = "\n\n".join(cv["experiencia"])

    # =========================
    # FALLBACK DE SEGURIDAD
    # =========================
    if not cv.get("experiencia_formateada"):
        cv["experiencia_formateada"] = ""

    return cv