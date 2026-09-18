"""Extracción del código de una respuesta del modelo.

El script entregado tiene que coincidir con el que aparece en el log: la
rúbrica compara los dos textos y, si difieren, el ejercicio 2 vale cero.
Copiarlo a mano es justo la vía por la que se cuela una diferencia, así
que se extrae por código, sin tocar nada.
"""
import re

VALLA = re.compile(
    r"```(?:python|py)?[ \t]*\r?\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)


def extraer_codigo(texto):
    """Devuelve el código de la respuesta, sin las vallas de markdown.

    Si el modelo obedeció y contestó solo con el archivo, devuelve el texto
    tal cual. Si lo envolvió en un bloque ```python, devuelve el contenido
    del primer bloque. No reformatea ni corrige: el archivo tiene que ser
    exactamente lo que dijo el modelo.
    """
    if texto is None:
        return ""

    bloques = VALLA.findall(texto)
    if bloques:
        return bloques[0].rstrip() + "\n"

    return texto.strip() + "\n" if texto.strip() else ""


def parece_script_python(texto):
    """Chequeo mínimo antes de guardar: ¿esto tiene forma de script?

    No valida que el programa esté bien, solo que no estemos guardando una
    disculpa del modelo en un archivo .py.
    """
    if not texto.strip():
        return False
    señales = ("import ", "def ", "sys.argv", "print(")
    return any(s in texto for s in señales)
