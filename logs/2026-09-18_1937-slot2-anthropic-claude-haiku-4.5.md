# Conversación — slot 2: Claude Haiku 4.5

- **Modelo:** `anthropic/claude-haiku-4.5`
- **Proveedor:** Anthropic
- **Capacidad que ejercita:** prompt caching explícito (cache_control)
- **Inicio:** 2026-09-18 19:37:56

---
### user · 2026-09-18 19:38:21

¿Qué hace la función extraer_usage y por qué completa campos con cero?

### assistant · 2026-09-18 19:38:29

# `extraer_usage`: normalizar el bloque de uso

La función **extrae y normaliza** la información de consumo de tokens que devuelve la API de OpenRouter.

## ¿Qué hace?

```python
def extraer_usage(respuesta):
    """Normaliza el bloque `usage` de una respuesta de OpenRouter."""
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
```

Devuelve un diccionario con **5 números clave**:
- `entrada`: tokens del prompt
- `salida`: tokens de la respuesta
- `razonamiento`: tokens usados para razonamiento (solo GPT o modelos con reasoning)
- `cacheados`: tokens leídos desde cache
- `costo`: USD gastados en esa llamada

## ¿Por qué completa con ceros?

Porque **los proveedores no devuelven todos los campos**:

| Proveedor | Devuelve | No devuelve |
|-----------|----------|-----------|
| **OpenAI (reasoning)** | razonamiento | cacheados |
| **Anthropic** | cacheados | razonamiento |
| **Google** | entrada/salida | cacheados, razonamiento |
| **DeepSeek** | todo | — |

Si la función no rellenara con `0`, el código que usa los datos tendría que estar lleno de validaciones:

```python
# ❌ Sin normalización: horrible
tokens_razo = uso.get("razonamiento", 0)  # en cada lugar
total = entrada + salida + (razonamiento or 0)  # ifs por todos lados

# ✅ Con normalización: limpio
tokens_razo = uso["razonamiento"]  # garantizado que existe
total = entrada + salida + razonamiento  # suma directo
```

## Caso práctico

Una respuesta de **Claude** puede venir así:
```json
{
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 45,
    "prompt_tokens_details": {
      "cached_tokens": 100
    }
    // falta: completion_tokens_details (sin reasoning_tokens)
  }
}
```

`extraer_usage` lo convierte en:
```python
{
    "entrada": 150,
    "salida": 45,
    "razonamiento": 0,      # ← completado
    "cacheados": 100,
    "costo": 0.00123,
    "descuento_cache": 0.0,  # ← completado
}
```

Así el resto del código (mostrar_usage, ahorro_por_cache, etc.) **siempre ve los 5 campos**, sin importar qué proveedor se usó.

**usage**

| entrada | salida | razonamiento | cacheados | costo USD |
|---:|---:|---:|---:|---:|
| 6042 | 869 | 0 | 0 | 0.011890 |

### user · 2026-09-18 19:38:33

¿Y qué pasa si el proveedor no devuelve el campo cost?

### assistant · 2026-09-18 19:38:39

# Cuando falta `cost`

Si el proveedor **no devuelve el campo `cost`**, la función lo completa con `0.0`:

```python
"costo": float(usage.get("cost") or 0.0),
```

## El flujo

1. `usage.get("cost")` → devuelve `None` (no existe)
2. `None or 0.0` → evalúa a `0.0` (porque `None` es falsy)
3. `float(0.0)` → `0.0`

## ¿Cuándo pasa en la práctica?

**Casi nunca**, porque OpenRouter **siempre devuelve `cost`** en el campo `usage`. Es parte del contrato de su API.

Pero si pasara (timeout parcial, respuesta truncada, mock en tests), el código no crash:

```python
# En mostrar_usage()
print(f"     costo         ${uso['costo']:.6f}")
# → "costo         $0.000000"  (sin error)

# En sesion() 
mostrar_usage(uso, modelo, conv.totales["costo"])
# → el acumulado sigue sumándose normalmente
```

## Comparación con otros campos

Fíjate que la estrategia es **consistente en todos lados**:

```python
"entrada": int(usage.get("prompt_tokens") or 0),          # int, defecto 0
"salida": int(usage.get("completion_tokens") or 0),       # int, defecto 0
"razonamiento": int(detalle_salida.get("reasoning_tokens") or 0),  # int, 0
"cacheados": int(detalle_entrada.get("cached_tokens") or 0),      # int, 0
"costo": float(usage.get("cost") or 0.0),                 # float, 0.0
```

**Todo se completa con cero** si falta. Es el patrón defensivo: la función asume que *cualquier* campo podría no venir y no deja `None` por ahí para sorpresas después.

**usage**

| entrada | salida | razonamiento | cacheados | costo USD |
|---:|---:|---:|---:|---:|
| 6935 | 530 | 0 | 6013 | 0.004173 |

---

## Total de la conversación

- Prompts del usuario: **2**
- Tokens de entrada: 12977
- Tokens de salida: 1399
- Tokens de razonamiento: 0
- Tokens cacheados: 6013
- Costo: **$0.016064**
