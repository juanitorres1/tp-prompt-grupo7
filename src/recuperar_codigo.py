"""Recupera el código de un log y lo escribe en un archivo.

Existe porque la corrida del ejercicio 2 puede completarse en la API y
fallar después, al imprimir en pantalla. La respuesta ya quedó registrada
en el log, así que el script se recupera de ahí en vez de pagar una
segunda llamada, que además contaría como un segundo prompt.

No inventa nada: extrae el texto del turno `assistant` del log y le aplica
la misma extracción de código que usa el chat.

    python src/recuperar_codigo.py logs/<archivo>.md vida.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from extraccion import extraer_codigo, parece_script_python  # noqa: E402

# El turno arranca en "### assistant · <fecha>" y termina donde empieza su
# tabla de usage o el turno siguiente.
TURNO = re.compile(
    r"^### assistant[^\n]*\n(.*?)(?=^\*\*usage\*\*|^### |\Z)",
    re.DOTALL | re.MULTILINE,
)


def respuestas_del_log(texto):
    return [t.strip() for t in TURNO.findall(texto)]


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2

    log = Path(argv[1])
    destino = Path(argv[2])
    if not log.exists():
        print(f"No encuentro {log}")
        return 1

    respuestas = respuestas_del_log(log.read_text(encoding="utf-8"))
    if not respuestas:
        print(f"No hay ningún turno 'assistant' en {log.name}")
        return 1

    if len(respuestas) > 1:
        print(f"Aviso: el log tiene {len(respuestas)} respuestas. "
              f"Uso la última.")

    codigo = extraer_codigo(respuestas[-1])
    if not parece_script_python(codigo):
        print("Lo extraído no parece un script de Python. No escribo nada.")
        return 1

    destino.write_text(codigo, encoding="utf-8")
    print(f"Escrito {destino} : {len(codigo.splitlines())} lineas, "
          f"tal cual quedo en el log.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
