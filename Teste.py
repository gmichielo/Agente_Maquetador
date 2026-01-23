from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from copy import deepcopy
from docx.oxml.text.run import CT_Text


def reemplazar_variables_xml(xml_element, datos):
    for node in xml_element.iter():
        if isinstance(node, CT_Text) and node.text:
            for clave, valor in datos.items():
                marcador = f"{{{{{clave}}}}}"
                if marcador in node.text:
                    node.text = node.text.replace(marcador, str(valor))


def iterar_bloques(doc):
    for child in doc.element.body:
        if child.tag.endswith('}p'):
            yield Paragraph(child, doc)
        elif child.tag.endswith('}tbl'):
            yield Table(child, doc)


def guardar_bloque_mixto(doc, inicio, fin):
    bloque = []
    capturar = False

    for elemento in iterar_bloques(doc):

        if isinstance(elemento, Paragraph):
            texto = elemento.text.strip()

            if inicio in texto:
                capturar = True
                continue

            if fin in texto:
                break

            if capturar:
                bloque.append(("paragraph", deepcopy(elemento._p)))

        elif isinstance(elemento, Table) and capturar:
            bloque.append(("table", deepcopy(elemento._tbl)))

    return bloque


def pegar_bloque_con_datos(doc, bloque, lista_datos):
    body = doc.element.body

    for datos in lista_datos:
        for _, xml in bloque:
            xml_clonado = deepcopy(xml)
            reemplazar_variables_xml(xml_clonado, datos)
            body.append(xml_clonado)


doc = Document(r"C:\Users\Gabriel\Downloads\Plantillas a hacer\INICIO.docx")

bloque = guardar_bloque_mixto(doc, "{{INICIO}}", "{{FIN}}")

datos = [
    {"NOMBRE": "Gabriel", "EDAD": "30", "DIRECCION": "Calle 1", "DIVISION": "IT"},
    {"NOMBRE": "Ana", "EDAD": "25", "DIRECCION": "Calle 2", "DIVISION": "HR"},
    {"NOMBRE": "Luis", "EDAD": "40", "DIRECCION": "Calle 3", "DIVISION": "Finance"},
]

pegar_bloque_con_datos(doc, bloque, datos)

doc.save("resultado.docx")
