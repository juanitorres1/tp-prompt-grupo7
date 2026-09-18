"""Registro de conversaciones en Markdown.

Cada conversación es un archivo `.md` en `logs/`. Es la evidencia de
auditoría que pide la misión: sin log, la corrida no cuenta. Por eso el
archivo se escribe turno por turno y no al final: si el proceso se cae a
la mitad, lo que ya pasó queda registrado igual.
"""
import re
from datetime import datetime
from pathlib import Path


def sanear(texto):
    """Deja solo lo que sirve como nombre de archivo en cualquier sistema."""
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", texto).strip("-")


def nombre_archivo(slot, modelo_id, cuando=None, etiqueta=None):
    """`2026-09-18_1930-slot2-anthropic-claude-haiku-4.5.md`

    El nombre lleva la fecha, el slot y el modelo para que el corrector
    vea de un vistazo qué conversación es cuál sin abrir el archivo.
    """
    cuando = cuando or datetime.now()
    partes = [cuando.strftime("%Y-%m-%d_%H%M"), f"slot{slot}", sanear(modelo_id)]
    if etiqueta:
        partes.append(sanear(etiqueta))
    return "-".join(partes) + ".md"


def bloque_turno(rol, texto, uso=None, cuando=None):
    """Un turno de la conversación, en Markdown.

    El usage va pegado a la respuesta que lo generó, no en una tabla
    aparte: así se puede reconstruir intento por intento.
    """
    cuando = cuando or datetime.now()
    lineas = [
        f"### {rol} · {cuando.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        texto.rstrip(),
        "",
    ]
    if uso is not None:
        lineas += [
            "**usage**",
            "",
            f"| entrada | salida | razonamiento | cacheados | costo USD |",
            f"|---:|---:|---:|---:|---:|",
            f"| {uso['entrada']} | {uso['salida']} | {uso['razonamiento']} "
            f"| {uso['cacheados']} | {uso['costo']:.6f} |",
            "",
        ]
    return "\n".join(lineas)


class Conversacion:
    """Un archivo de log abierto, al que se le van agregando turnos."""

    def __init__(self, carpeta, slot, modelo, etiqueta=None, cuando=None):
        cuando = cuando or datetime.now()
        self.carpeta = Path(carpeta)
        self.carpeta.mkdir(parents=True, exist_ok=True)
        self.ruta = self.carpeta / nombre_archivo(
            slot, modelo["id"], cuando, etiqueta)
        self.modelo = modelo
        self.turnos = 0
        self.totales = {"entrada": 0, "salida": 0, "razonamiento": 0,
                        "cacheados": 0, "costo": 0.0}
        self._escribir(self._encabezado(slot, modelo, cuando))

    def _encabezado(self, slot, modelo, cuando):
        return "\n".join([
            f"# Conversación — slot {slot}: {modelo['nombre']}",
            "",
            f"- **Modelo:** `{modelo['id']}`",
            f"- **Proveedor:** {modelo['proveedor']}",
            f"- **Capacidad que ejercita:** {modelo['capacidad']}",
            f"- **Inicio:** {cuando.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
        ])

    def _escribir(self, texto):
        with open(self.ruta, "a", encoding="utf-8") as f:
            f.write(texto)

    def anotar(self, rol, texto, uso=None, parametros=None):
        """Agrega un turno. `parametros` documenta effort, json, etc."""
        if parametros:
            texto = f"{texto}\n\n_parámetros: {parametros}_"
        self._escribir(bloque_turno(rol, texto, uso) + "\n")
        if rol == "user":
            self.turnos += 1
        if uso:
            for k in ("entrada", "salida", "razonamiento", "cacheados"):
                self.totales[k] += uso[k]
            self.totales["costo"] += uso["costo"]

    def cerrar(self):
        """Escribe el total de la conversación al pie del archivo."""
        t = self.totales
        self._escribir("\n".join([
            "---",
            "",
            "## Total de la conversación",
            "",
            f"- Prompts del usuario: **{self.turnos}**",
            f"- Tokens de entrada: {t['entrada']}",
            f"- Tokens de salida: {t['salida']}",
            f"- Tokens de razonamiento: {t['razonamiento']}",
            f"- Tokens cacheados: {t['cacheados']}",
            f"- Costo: **${t['costo']:.6f}**",
            "",
        ]))
