# Trabajo previo — exploración de OpenRouter

Las tres respuestas que la misión pide antes de escribir código. Los datos se
tomaron de las fichas de OpenRouter el 18 de septiembre de 2026.

## 1. Qué hace un router de modelos

Un router de modelos recibe el pedido y **elige por vos a qué modelo mandarlo**,
en vez de obligarte a decidirlo de antemano.

El Auto Router de OpenRouter (`openrouter/auto`) clasifica cada request y lo
manda al modelo que la comunidad de OpenRouter más usa para ese tipo de tarea,
mirando el gasto de los últimos 7 días. Esa ventana móvil es lo que hace que
incorpore modelos nuevos solo, sin que nadie actualice una tabla. Se le puede
fijar un `cost_tier` (low, medium, high, xhigh, max) para inclinar la elección
hacia lo barato o hacia lo capaz; el default es `low`.

**Qué problema resuelve:** el costo de mantenerse actualizado. Elegir bien el
modelo exige comparar precios, ventanas y benchmarks que cambian cada pocas
semanas, y multiplicarlo por cada tipo de tarea. El router reemplaza esa
investigación por una señal de mercado agregada. Se paga al precio del modelo
que termine eligiendo; el ruteo en sí no cuesta nada.

El costo de usarlo es perder el control: no sabés de antemano qué modelo te va
a atender, y por lo tanto tampoco su latencia, su ventana ni si soporta el
parámetro que necesitás.

## 2. El mapa de modelos

El modelo más avanzado de cada proveedor conocido, con precio por millón de
tokens y ventana de contexto.

| Proveedor | Modelo | Entrada | Salida | Contexto |
|---|---|---:|---:|---:|
| OpenAI | `openai/gpt-5.6-luna` | $0,20 | $1,20 | 1,05M |
| Anthropic | `anthropic/claude-haiku-4.5` | $1,00 | $5,00 | 200K |
| Google | `google/gemini-3.7-flash` | $0,75 | $3,75 | 1,05M |
| DeepSeek | `deepseek/deepseek-v4-flash-0731` | $0,055 | $0,165 | 1,31M |
| xAI | `x-ai/grok-4.6` | $2,00 | $6,00 | 500K |
| Qwen | `qwen/qwen3.8-max-0902` | $2,00 | $6,00 | 1M |
| Moonshot | `kimi-k3` | $1,95 | $10,92 | 1,05M |

> **Pendiente de completar:** la posición en los benchmarks que muestra la
> página de cada modelo. Se completa desde `openrouter.ai/discover` y desde la
> vista comparativa.

Lo que salta de la tabla:

**El rango de precios es de casi dos órdenes de magnitud.** DeepSeek V4 Flash
cuesta $0,055 por millón de tokens de entrada y Grok 4.6 cuesta $2,00: **36
veces más**. En salida, DeepSeek está en $0,165 y Kimi K3 en $10,92: **66 veces
más**. Elegir modelo es, antes que nada, una decisión económica.

**La ventana de contexto ya no es el diferenciador.** Cinco de los siete
superan el millón de tokens. Haiku 4.5, con 200K, es el más chico de la lista y
es también el que la misión usa para ejercitar caching — que es justamente la
técnica que importa cuando el contexto es caro.

**Los cuatro slots de la misión no fueron elegidos al azar.** Cubren cuatro
proveedores distintos y cuatro capacidades distintas: effort configurable,
caching explícito, salidas estructuradas y el escalón barato.

## 3. Parámetros soportados

No todos los modelos aceptan las mismas perillas. La versión programática de
esta comparación es `GET https://openrouter.ai/api/v1/models`, que devuelve un
campo `supported_parameters` por modelo.

| Capacidad | Cómo se pide | Quién lo soporta |
|---|---|---|
| Esfuerzo de razonamiento | `reasoning: {"effort": "low"\|"medium"\|"high"}` | OpenAI (slot 1); Anthropic y Gemini aceptan además `{"max_tokens": N}` como presupuesto de pensamiento |
| Salidas estructuradas | `response_format: {"type": "json_schema", ...}` | Gemini (slot 3) |
| Caching explícito | `cache_control: {"type": "ephemeral"}` en el bloque | Anthropic (slot 2) y Qwen |
| Caching automático | nada: se activa por prefijo repetido | OpenAI, Gemini y DeepSeek |

La consecuencia práctica de esta tabla es que **el caching no se activa igual en
todos lados**. En Anthropic hay que marcar el bloque a mano; en DeepSeek lo
único que se puede hacer es **diseñar el prompt** para que la parte estática
quede al principio y no cambie entre llamadas. Esa diferencia es la que hizo
que la interfaz tuviera que distinguir por proveedor al armar el mensaje de
sistema.

`reasoning` es un parámetro **unificado** de OpenRouter: la misma clave sirve
para proveedores que por debajo lo implementan distinto. Es el mismo argumento
que justifica usar OpenRouter en vez de la API de cada proveedor: un endpoint,
una key y un formato de request para todos.
