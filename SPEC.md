# SPEC — Interfaz de chat sobre OpenRouter

Qué se construyó y por qué. Corresponde al ejercicio 1 de la misión.

## Objetivo

Un chat propio que sirva cuatro modelos de cuatro proveedores distintos a
través de OpenRouter, muestre el consumo de cada respuesta y deje un log
auditable de cada conversación.

La interfaz no busca ser linda: la misión lo dice explícitamente y la rúbrica
no lo puntúa. Busca ser **medible y auditable**.

## Decisiones de diseño

**Solo biblioteca estándar.** El cliente HTTP es `urllib.request`. Evita el
entorno virtual y el `pip install`, y hace que el repo corra tal cual en
cualquier máquina con Python 3. El costo es escribir a mano el manejo de
errores HTTP, que son veinte líneas.

**CLI en vez de web.** Una interfaz web habría agregado servidor, plantillas y
estado de sesión sin sumar un punto de la rúbrica. El REPL da lo mismo con una
fracción de las piezas que pueden fallar.

**El `usage` se normaliza siempre a los mismos seis campos.** Los proveedores no
devuelven lo mismo: los tokens de razonamiento y los cacheados aparecen solo
cuando existen. `extraer_usage()` completa con cero para que la interfaz pueda
mostrar los cinco números siempre y para que el informe los sume sin casos
especiales.

**El log se escribe turno por turno.** No se arma en memoria para volcarlo al
final. Si el proceso se corta, lo que ya pasó queda registrado. El log es la
condición de admisibilidad de la misión: sin log, la corrida no cuenta.

**Cambiar de modelo abre un archivo nuevo.** Así ningún log mezcla modelos, que
es lo que verifica el criterio 1.3.

**Los comandos mal escritos no viajan a la API.** Un `/sair` en vez de `/salir`
sumaría un turno de usuario al log y gastaría tokens. Como la rúbrica cuenta
los turnos `user` del log ganador para decidir si la corrida fue de un prompt,
un typo podría costar tres puntos. El bucle rechaza cualquier entrada que
empiece con `/` y no sea un comando conocido.

## Los cuatro slots

| Slot | Modelo | Capacidad ejercitada | Cómo se ejercita |
|---|---|---|---|
| 1 | `openai/gpt-5.6-luna` | Effort configurable | `/effort low\|medium\|high` manda `reasoning.effort` |
| 2 | `anthropic/claude-haiku-4.5` | Caching explícito | `/contexto` marca el bloque estático con `cache_control: ephemeral` |
| 3 | `google/gemini-3.7-flash` | Salidas estructuradas | `/json on` manda un `response_format` con JSON Schema |
| 4 | `deepseek/deepseek-v4-flash-0731` | El escalón barato | Misma pregunta que el slot 2, para comparar costo |

Los cuatro ids fueron verificados contra las fichas de OpenRouter antes de
escribir el código. Ninguno hizo falta sustituir.

El caching funciona distinto según el proveedor y el código lo refleja: en
Anthropic hay que marcar el bloque con `cache_control`; en OpenAI, Gemini y
DeepSeek es automático por prefijo repetido, así que lo único que se puede
hacer es diseñar el prompt para que el prefijo estático no cambie.

## Formato del log

Un archivo por conversación en `logs/`, nombrado
`<fecha>_<hora>-slot<N>-<modelo>.md`. Adentro:

- Encabezado con modelo, proveedor, capacidad e inicio.
- Un bloque por turno con rol, marca de tiempo y contenido.
- Debajo de cada respuesta, una tabla con entrada, salida, razonamiento,
  cacheados y costo.
- Al pie, el total de la conversación y **la cantidad de prompts del usuario**,
  que es el número que mira la rúbrica.

Los parámetros usados en cada turno (`reasoning.effort`, `response_format`)
quedan anotados junto al mensaje, para que se pueda reconstruir con qué
configuración salió cada respuesta.

## Qué se testea

27 tests que no tocan la red:

- **`test_openrouter.py`** — el parseo del `usage` con todos los campos, con
  campos faltantes y con respuestas rotas; el cálculo del ahorro por cache por
  las dos vías; y el catálogo de modelos.
- **`test_registro.py`** — el nombre del archivo, el bloque de cada turno, el
  conteo de prompts del usuario, la acumulación de totales y el cierre.
- **`test_comandos.py`** — que ningún comando, bien o mal escrito, se mande al
  modelo.

Lo que toca la red no se mockea: se prueba a mano desde el chat y la evidencia
queda en los logs del repo.

## Lo que queda afuera

No hay streaming, no hay reintentos automáticos ni selección de proveedor
dentro de OpenRouter. Nada de eso lo pide la misión y cada uno habría agregado
superficie que mantener.
