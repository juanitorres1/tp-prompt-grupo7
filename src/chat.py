"""Interfaz de chat sobre OpenRouter: cuatro modelos, un solo endpoint.

Uso:

    python src/chat.py            (en Git Bash: winpty python src/chat.py)

Comandos dentro del chat:

    /modelo             elegir otro modelo (arranca conversación nueva)
    /effort <nivel>     low | medium | high | off   (slot 1)
    /json on|off        salida estructurada con JSON Schema (slot 3)
    /contexto <archivos>  carga contexto estático; en el slot 2 va marcado
                          con cache_control para provocar cache hits
    /prompt <archivo>   manda el contenido de un archivo como UN turno
    /guardar <destino>  escribe el código de la última respuesta en un archivo
    /resumen            totales de la conversación en curso
    /salir              cierra el log y termina
"""
import sys
from pathlib import Path

# En Git Bash, Python no reconoce la salida como terminal y la bufferea:
# el proceso corre pero no se ve nada hasta que termina. Con line_buffering
# cada print sale en el momento.
try:
    # errors="replace" evita que un acento o un guión largo tumbe el
    # proceso en consolas cp1252, que es lo normal en Windows.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace",
                           line_buffering=True)
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

import extraccion  # noqa: E402
import openrouter  # noqa: E402
import registro  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_LOGS = RAIZ / "logs"

# Esquema de ejemplo para el slot 3. La consigna pide ejercitar salidas
# estructuradas; con esto la respuesta viene como JSON validado.
ESQUEMA_JSON = {
    "type": "json_schema",
    "json_schema": {
        "name": "respuesta_estructurada",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "respuesta": {"type": "string"},
                "confianza": {"type": "number"},
                "supuestos": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["respuesta", "confianza", "supuestos"],
            "additionalProperties": False,
        },
    },
}


def elegir_modelo():
    print("\n  Modelos disponibles\n")
    for slot, m in openrouter.MODELOS.items():
        print(f"    {slot}. {m['nombre']:<20} {m['id']}")
        print(f"       {m['proveedor']} · {m['capacidad']}")
        print(f"       ${m['precio_entrada']}/M entrada · "
              f"${m['precio_salida']}/M salida\n")
    while True:
        try:
            slot = input("  Slot (1-4): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            return None, None
        if slot in openrouter.MODELOS:
            return slot, openrouter.MODELOS[slot]
        print("  No existe ese slot.")


def bloque_sistema(texto, con_cache):
    """El contexto estático, marcado para cachear si el modelo lo soporta.

    Anthropic y Qwen necesitan la marca explícita `cache_control`; en
    OpenAI, Gemini y DeepSeek el cache es automático por prefijo repetido.
    """
    if con_cache:
        return {
            "role": "system",
            "content": [{
                "type": "text",
                "text": texto,
                "cache_control": {"type": "ephemeral"},
            }],
        }
    return {"role": "system", "content": texto}


def cargar_contexto(rutas):
    partes = []
    for r in rutas:
        archivo = Path(r)
        if not archivo.is_absolute():
            archivo = RAIZ / r
        if not archivo.exists():
            print(f"  No encuentro {archivo}")
            continue
        partes.append(f"### {archivo.name}\n\n"
                      + archivo.read_text(encoding="utf-8"))
        print(f"  Cargado {archivo.name} ({archivo.stat().st_size} bytes)")
    return "\n\n".join(partes)


def mostrar_usage(uso, modelo, acumulado):
    # Solo ASCII: la consola de Windows (cp1252) no dibuja cajas Unicode y
    # un UnicodeEncodeError acá tumbaría la corrida después de haber pagado
    # la llamada.
    ahorro = openrouter.ahorro_por_cache(uso, modelo)
    print("\n  -- usage " + "-" * 38)
    print(f"     entrada       {uso['entrada']:>8}")
    print(f"     salida        {uso['salida']:>8}")
    print(f"     razonamiento  {uso['razonamiento']:>8}")
    print(f"     cacheados     {uso['cacheados']:>8}"
          + (f"   (ahorro ${ahorro:.6f})" if ahorro else ""))
    print(f"     costo         ${uso['costo']:.6f}")
    print(f"     acumulado     ${acumulado:.6f}")
    print("  " + "-" * 47 + "\n")


def sesion(slot, modelo):
    """Una conversación con un modelo. Cambiar de modelo termina esta."""
    conv = registro.Conversacion(CARPETA_LOGS, slot, modelo)
    print(f"\n  Conversación nueva con {modelo['nombre']}")
    print(f"  Log: {conv.ruta.relative_to(RAIZ)}\n")
    try:
        return _bucle(conv, modelo)
    finally:
        # El total va al pie del log pase lo que pase: si el proceso se
        # corta, el archivo igual queda cerrado y auditable.
        conv.cerrar()


def _bucle(conv, modelo):
    mensajes = []
    effort = None
    json_on = False
    ultima_respuesta = ""

    while True:
        try:
            entrada = input("  vos > ").strip()
        except (EOFError, KeyboardInterrupt):
            return "salir"

        if not entrada:
            continue

        if entrada == "/salir":
            return "salir"

        if entrada == "/modelo":
            return "cambiar"

        if entrada == "/resumen":
            t = conv.totales
            print(f"\n  prompts {conv.turnos} · entrada {t['entrada']} · "
                  f"salida {t['salida']} · razonamiento {t['razonamiento']} · "
                  f"cacheados {t['cacheados']} · costo ${t['costo']:.6f}\n")
            continue

        if entrada.startswith("/effort"):
            nivel = entrada.split(maxsplit=1)[-1].strip().lower()
            if nivel in ("low", "medium", "high"):
                effort = nivel
                print(f"  reasoning.effort = {nivel}\n")
            else:
                effort = None
                print("  reasoning desactivado\n")
            continue

        if entrada.startswith("/json"):
            json_on = entrada.endswith("on")
            print(f"  salida estructurada {'activada' if json_on else 'desactivada'}\n")
            continue

        if entrada.startswith("/contexto"):
            rutas = entrada.split()[1:]
            if not rutas:
                print("  Uso: /contexto archivo1 [archivo2 ...]\n")
                continue
            texto = cargar_contexto(rutas)
            if texto:
                con_cache = modelo["proveedor"] == "Anthropic"
                mensajes = [bloque_sistema(texto, con_cache)] + [
                    m for m in mensajes if m.get("role") != "system"]
                print(f"  Contexto estático cargado"
                      + (" con cache_control\n" if con_cache
                         else " (cache automático por prefijo)\n"))
            continue

        if entrada.startswith("/guardar"):
            partes = entrada.split(maxsplit=1)
            if len(partes) < 2:
                print("  Uso: /guardar vida.py\n")
                continue
            if not ultima_respuesta:
                print("  Todavía no hay ninguna respuesta que guardar.\n")
                continue
            codigo = extraccion.extraer_codigo(ultima_respuesta)
            if not extraccion.parece_script_python(codigo):
                print("  La última respuesta no parece un script de Python. "
                      "No guardo nada.\n")
                continue
            destino = Path(partes[1].strip())
            if not destino.is_absolute():
                destino = RAIZ / destino
            destino.write_text(codigo, encoding="utf-8")
            print(f"  Guardado {destino.name}: {len(codigo.splitlines())} líneas, "
                  f"tal cual lo devolvió el modelo (sin tocar nada).\n")
            continue

        if entrada.startswith("/prompt"):
            # El prompt se manda desde un archivo para que viaje como UN
            # solo turno: pegar varias líneas en el input las mandaría como
            # varios prompts. Además el archivo queda versionado, que es lo
            # que garantiza que el prefijo estático sea idéntico entre
            # intentos y que el cache pegue.
            partes = entrada.split(maxsplit=1)
            if len(partes) < 2:
                print("  Uso: /prompt prompts/conway-v1.md\n")
                continue
            archivo = Path(partes[1].strip())
            if not archivo.is_absolute():
                archivo = RAIZ / archivo
            if not archivo.exists():
                print(f"  No encuentro {archivo}\n")
                continue
            entrada = archivo.read_text(encoding="utf-8")
            print(f"  Prompt cargado de {archivo.name}: "
                  f"{len(entrada.splitlines())} líneas, {len(entrada)} caracteres.")
            print("  Va como un único turno de usuario.\n")

        elif entrada.startswith("/"):
            # Un comando mal escrito NO se manda al modelo: costaría tokens
            # y, peor, sumaría un turno de usuario al log. La rúbrica cuenta
            # esos turnos para decidir si la corrida fue "1 prompt".
            print(f"  '{entrada.split()[0]}' no es un comando. Disponibles: "
                  f"/modelo /effort /json /contexto /prompt /guardar /resumen /salir")
            print("  (si querías mandarlo como mensaje, escribilo sin la barra)\n")
            continue

        mensajes.append({"role": "user", "content": entrada})
        parametros = []
        if effort:
            parametros.append(f"reasoning.effort={effort}")
        if json_on:
            parametros.append("response_format=json_schema")
        conv.anotar("user", entrada,
                    parametros=", ".join(parametros) or None)

        try:
            respuesta = openrouter.pedir(
                modelo["id"], mensajes,
                reasoning={"effort": effort} if effort else None,
                response_format=ESQUEMA_JSON if json_on else None,
            )
        except openrouter.ErrorOpenRouter as e:
            print(f"\n  Error: {e}\n")
            mensajes.pop()
            continue

        texto = openrouter.texto_de(respuesta)
        uso = openrouter.extraer_usage(respuesta)
        ultima_respuesta = texto

        print(f"\n  {modelo['nombre']} >\n")
        print("  " + texto.replace("\n", "\n  "))

        mensajes.append({"role": "assistant", "content": texto})
        conv.anotar("assistant", texto, uso)
        mostrar_usage(uso, modelo, conv.totales["costo"])


def una_sola_llamada(slot, ruta_prompt, effort=None, destino=None,
                     etiqueta=None):
    """Un intento: un prompt desde archivo, una respuesta, y se cierra.

    Existe para la corrida del ejercicio 2. Garantiza por construcción que
    el log tenga exactamente un turno de usuario: no hay input interactivo
    donde se pueda colar un typo o un pegado partido en varias líneas.
    """
    modelo = openrouter.MODELOS[slot]
    archivo = Path(ruta_prompt)
    if not archivo.is_absolute():
        archivo = RAIZ / archivo
    if not archivo.exists():
        print(f"  No encuentro {archivo}")
        return 1
    prompt = archivo.read_text(encoding="utf-8")

    conv = registro.Conversacion(CARPETA_LOGS, slot, modelo, etiqueta=etiqueta)
    print(f"\n  Modelo: {modelo['nombre']} ({modelo['id']})")
    print(f"  Prompt: {archivo.name} — {len(prompt.splitlines())} líneas, "
          f"{len(prompt)} caracteres")
    if effort:
        print(f"  reasoning.effort = {effort}")
    print(f"  Log: {conv.ruta.relative_to(RAIZ)}")
    print("\n  Mandando un único turno de usuario...\n")

    parametros = f"reasoning.effort={effort}" if effort else None
    conv.anotar("user", prompt, parametros=parametros)

    try:
        respuesta = openrouter.pedir(
            modelo["id"], [{"role": "user", "content": prompt}],
            reasoning={"effort": effort} if effort else None,
        )
    except openrouter.ErrorOpenRouter as e:
        print(f"  Error: {e}\n")
        conv.cerrar()
        return 1
    except KeyboardInterrupt:
        # El log queda cerrado igual, con la nota de que no hubo respuesta:
        # un intento interrumpido no es un intento, pero tampoco se oculta.
        conv.anotar("sistema", "Llamada interrumpida por el usuario: "
                               "no hubo respuesta del modelo.")
        conv.cerrar()
        print("\n  Interrumpido. El log quedó cerrado sin respuesta.\n")
        return 130

    texto = openrouter.texto_de(respuesta)
    uso = openrouter.extraer_usage(respuesta)
    conv.anotar("assistant", texto, uso)
    mostrar_usage(uso, modelo, conv.totales["costo"])

    if destino:
        codigo = extraccion.extraer_codigo(texto)
        if not extraccion.parece_script_python(codigo):
            print("  La respuesta no parece un script de Python. No guardo nada.\n")
        else:
            salida = Path(destino)
            if not salida.is_absolute():
                salida = RAIZ / salida
            salida.write_text(codigo, encoding="utf-8")
            print(f"  Guardado {salida.name}: {len(codigo.splitlines())} líneas, "
                  f"tal cual lo devolvió el modelo.\n")

    conv.cerrar()
    print(f"  Log cerrado: {conv.ruta.relative_to(RAIZ)}")
    print(f"  Prompts del usuario en este log: {conv.turnos}\n")
    return 0


def main():
    import argparse

    ap = argparse.ArgumentParser(
        description="Chat sobre OpenRouter. Sin argumentos abre el modo interactivo.")
    ap.add_argument("--slot", choices=sorted(openrouter.MODELOS))
    ap.add_argument("--prompt", help="archivo con el prompt; se manda como un turno")
    ap.add_argument("--effort", choices=["low", "medium", "high"])
    ap.add_argument("--guardar", help="dónde escribir el código de la respuesta")
    ap.add_argument("--etiqueta", help="sufijo para el nombre del log, ej: intento-1")
    args = ap.parse_args()

    print("\n" + "=" * 60)
    print("  Chat sobre OpenRouter — TP: el prompt mínimo")
    print("=" * 60)
    try:
        openrouter.cargar_key()
    except openrouter.ErrorOpenRouter as e:
        print(f"\n  {e}\n")
        return 1

    if args.prompt:
        if not args.slot:
            print("\n  --prompt necesita --slot\n")
            return 2
        return una_sola_llamada(args.slot, args.prompt, args.effort,
                                args.guardar, args.etiqueta)

    while True:
        slot, modelo = elegir_modelo()
        if slot is None:
            print("  Listo.\n")
            return 0
        accion = sesion(slot, modelo)
        if accion == "salir":
            print("\n  Listo. Los logs quedaron en logs/\n")
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
