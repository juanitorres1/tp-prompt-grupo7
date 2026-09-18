"""Cliente mínimo de OpenRouter. Solo biblioteca estándar.

OpenRouter expone una API compatible con el formato de OpenAI: un solo
endpoint y una sola key sirven para todos los proveedores. Lo único que
cambia entre modelos es el id y los parámetros que cada uno acepta.
"""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

# Precios en dólares por millón de tokens, tomados de las fichas de
# OpenRouter. Se usan para estimar el ahorro por cache; el costo real de
# cada respuesta viene en el campo `cost` que devuelve la API.
MODELOS = {
    "1": {
        "id": "openai/gpt-5.6-luna",
        "nombre": "GPT-5.6 Luna",
        "proveedor": "OpenAI",
        "capacidad": "effort configurable (reasoning.effort)",
        "precio_entrada": 0.20,
        "precio_salida": 1.20,
        "precio_cache_lectura": None,
        "contexto": 1_050_000,
    },
    "2": {
        "id": "anthropic/claude-haiku-4.5",
        "nombre": "Claude Haiku 4.5",
        "proveedor": "Anthropic",
        "capacidad": "prompt caching explícito (cache_control)",
        "precio_entrada": 1.00,
        "precio_salida": 5.00,
        "precio_cache_lectura": 0.10,
        "contexto": 200_000,
    },
    "3": {
        "id": "google/gemini-3.7-flash",
        "nombre": "Gemini 3.7 Flash",
        "proveedor": "Google",
        "capacidad": "salidas estructuradas (JSON Schema)",
        "precio_entrada": 0.75,
        "precio_salida": 3.75,
        "precio_cache_lectura": None,
        "contexto": 1_048_576,
    },
    "4": {
        "id": "deepseek/deepseek-v4-flash-0731",
        "nombre": "DeepSeek V4 Flash",
        "proveedor": "DeepSeek",
        "capacidad": "el escalón barato; cache automático por prefijo",
        "precio_entrada": 0.055,
        "precio_salida": 0.165,
        "precio_cache_lectura": 0.00175,
        "contexto": 1_310_720,
    },
}


class ErrorOpenRouter(RuntimeError):
    """La API contestó algo que no es una respuesta válida."""


def cargar_key(ruta=".env"):
    """Devuelve la API key: primero la variable de entorno, después el .env.

    El .env nunca entra a git (está en .gitignore). Se parsea a mano para
    no depender de python-dotenv.
    """
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key.strip()

    archivo = Path(ruta)
    if archivo.exists():
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            nombre, valor = linea.split("=", 1)
            if nombre.strip() == "OPENROUTER_API_KEY":
                return valor.strip().strip('"').strip("'")

    raise ErrorOpenRouter(
        "No encuentro la API key. Poné OPENROUTER_API_KEY en el archivo .env "
        "o exportala como variable de entorno."
    )


def extraer_usage(respuesta):
    """Normaliza el bloque `usage` de una respuesta de OpenRouter.

    Los proveedores no devuelven todos los campos: los tokens de
    razonamiento y los cacheados aparecen solo cuando existen. Se completa
    con ceros para que la interfaz siempre pueda mostrar los cinco números
    y para que el informe pueda sumarlos sin casos especiales.
    """
    usage = (respuesta or {}).get("usage") or {}
    detalle_entrada = usage.get("prompt_tokens_details") or {}
    detalle_salida = usage.get("completion_tokens_details") or {}

    return {
        "entrada": int(usage.get("prompt_tokens") or 0),
        "salida": int(usage.get("completion_tokens") or 0),
        "razonamiento": int(detalle_salida.get("reasoning_tokens") or 0),
        "cacheados": int(detalle_entrada.get("cached_tokens") or 0),
        "costo": float(usage.get("cost") or 0.0),
        "descuento_cache": float(usage.get("cache_discount") or 0.0),
    }


def formatear_usage(uso):
    """Una línea legible con los cinco números que pide la consigna."""
    return (
        f"entrada {uso['entrada']} · salida {uso['salida']} · "
        f"razonamiento {uso['razonamiento']} · cacheados {uso['cacheados']} · "
        f"costo ${uso['costo']:.6f}"
    )


def ahorro_por_cache(uso, modelo):
    """Estima en dólares lo que se ahorró por leer tokens del cache.

    Si la API ya informó `cache_discount`, ese número manda. Si no, se
    estima con la diferencia entre el precio de entrada y el de lectura de
    cache del modelo. Devuelve 0.0 cuando no hay datos para estimarlo.
    """
    if uso["descuento_cache"]:
        return abs(uso["descuento_cache"])

    precio_cache = modelo.get("precio_cache_lectura")
    if not precio_cache or not uso["cacheados"]:
        return 0.0

    diferencia = modelo["precio_entrada"] - precio_cache
    return uso["cacheados"] * diferencia / 1_000_000


def pedir(modelo_id, mensajes, key=None, reasoning=None, response_format=None,
          timeout=180):
    """Una llamada de chat completion. Devuelve la respuesta cruda en dict.

    `reasoning` y `response_format` son los parámetros unificados de
    OpenRouter; se mandan solo si el slot los usa, porque no todos los
    modelos los aceptan.
    """
    cuerpo = {"model": modelo_id, "messages": mensajes}
    if reasoning:
        cuerpo["reasoning"] = reasoning
    if response_format:
        cuerpo["response_format"] = response_format

    datos = json.dumps(cuerpo).encode("utf-8")
    pedido = urllib.request.Request(
        ENDPOINT,
        data=datos,
        headers={
            "Authorization": f"Bearer {key or cargar_key()}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/",
            "X-Title": "TP prompt minimo",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(pedido, timeout=timeout) as r:
            respuesta = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detalle = e.read().decode("utf-8", errors="replace")
        raise ErrorOpenRouter(f"HTTP {e.code}: {detalle}") from e
    except urllib.error.URLError as e:
        raise ErrorOpenRouter(f"No se pudo conectar: {e.reason}") from e

    if "error" in respuesta and not respuesta.get("choices"):
        raise ErrorOpenRouter(str(respuesta["error"]))

    return respuesta


def texto_de(respuesta):
    """El contenido del primer choice, o cadena vacía si no vino."""
    choices = (respuesta or {}).get("choices") or []
    if not choices:
        return ""
    return (choices[0].get("message") or {}).get("content") or ""
