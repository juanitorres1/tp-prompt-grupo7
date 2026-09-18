# Conversación — slot 4: DeepSeek V4 Flash

- **Modelo:** `deepseek/deepseek-v4-flash-0731`
- **Proveedor:** DeepSeek
- **Capacidad que ejercita:** el escalón barato; cache automático por prefijo
- **Inicio:** 2026-09-18 19:39:12

---
### user · 2026-09-18 19:39:29

¿Qué hace la función extraer_usage y por qué completa campos con cero?

### assistant · 2026-09-18 19:40:09

La función `extraer_usage(respuesta)` es un **normalizador**: convierte el bloque `usage` crudo que devuelve OpenRouter en un dict siempre igual, con claves fijas y tipos garantizados.

## Qué hace, paso a paso

1. **Resiste respuestas incompletas**: `(respuesta or {})` contempla que llegue `None`, y `.get("usage") or {}` que el bloque `usage` falte. Lo mismo con los sub-bloques `prompt_tokens_details` y `completion_tokens_details`, que son anidados y también suelen faltar.
2. **Extrae los seis valores que interesan** para el informe:
   - `entrada` → `prompt_tokens`
   - `salida` → `completion_tokens`
   - `razonamiento` → `completion_tokens_details.reasoning_tokens`
   - `cacheados` → `prompt_tokens_details.cached_tokens`
   - `costo` → `cost`
   - `descuento_cache` → `cache_discount`
3. **Fuerza tipos**: `int(...)` y `float(...)` garantizan que después se pueda formatear y sumar sin sorpresas (por ejemplo, `$0.001234` o `12345` como número, no como string).

## Por qué completa con ceros

OpenRouter es un agregador: cada proveedor (Anthropic, Google, OpenAI, DeepSeek...) informa campos distintos. Concretamente:

- **`reasoning_tokens`** solo aparece en modelos con razonamiento, y solo cuando el modelo efectivamente razonó en esa llamada.
- **`cached_tokens`** solo aparece cuando hubo un cache hit real.
- **`cost`** y **`cache_discount`** pueden no venir si el proveedor no los reporta.

La alternativa sería llenar con `None` o dejar las claves ausentes, pero eso obligaría a **casos especiales en todos lados**:

- `mostrar_usage()` tendría que preguntar `if "cacheados" in uso` antes de imprimir cada línea.
- `registro.Conversacion.anotar()` tendría que chequear qué claves existen antes de sumar al acumulado.
- `ahorro_por_cache()` tendría que manejar `None` en los cálculos.

En cambio, con ceros:

- La interfaz siempre imprime los cinco números, sin condicionales.
- `registro.py` suma directamente: `self.totales["cachados"] += uso["cacheados"]`.
- El patrón `uso.get("cached_tokens") or 0` usa el hecho de que tanto `None` como `0` son falsy: si el campo no vino o vino en cero, el resultado es el mismo.

## Ejemplo concreto

Si un proveedor responde solo:

```json
"usage": { "prompt_tokens": 120, "completion_tokens": 40 }
```

la función devuelve:

```python
{
    "entrada": 120,
    "salida": 40,
    "razonamiento": 0,
    "cacheados": 0,
    "costo": 0.0,
    "descuento_cache": 0.0,
}
```

Sin ceros, cualquier código que procese ese `usage` tendría que proteger cada acceso. Con ceros, todo el pipeline (mostrar, registrar, estimar ahorro) puede asumir que el dict siempre tiene la misma forma. La función es, en criollo, un *"o si no, cero"*: un valor por defecto que hace que el resto del programa no se entere de que la respuesta vino incompleta.

**usage**

| entrada | salida | razonamiento | cacheados | costo USD |
|---:|---:|---:|---:|---:|
| 5456 | 2339 | 1494 | 0 | 0.000664 |

---

## Total de la conversación

- Prompts del usuario: **1**
- Tokens de entrada: 5456
- Tokens de salida: 2339
- Tokens de razonamiento: 1494
- Tokens cacheados: 0
- Costo: **$0.000664**
