# TP: el prompt mínimo — Grupo 7

Chat propio sobre OpenRouter con cuatro modelos, y el juego de la vida de
Conway resuelto en la mínima cantidad de prompts posible.

## Puesta en marcha

Hace falta Python 3 y nada más: el proyecto usa solo biblioteca estándar.

```bash
cp .env.example .env          # y poné adentro tu API key de OpenRouter
python -m unittest discover -s tests -v
python src/chat.py            # en Git Bash: winpty python src/chat.py
```

La key se saca en https://openrouter.ai/keys y el crédito se carga en
https://openrouter.ai/settings/credits.

## Qué hay acá

```
src/openrouter.py     cliente de la API y normalización del usage
src/registro.py       log de conversaciones en Markdown
src/chat.py           la interfaz
tests/                27 tests propios + test_vida.py de la cátedra
logs/                 un .md por conversación (la evidencia de auditoría)
vida.py               el script de Conway, tal cual salió del chat
informe/              la cuenta final y el trabajo previo
```

## Comandos del chat

| Comando | Qué hace |
|---|---|
| `/modelo` | Elegir otro modelo. Arranca conversación nueva y log nuevo. |
| `/effort low\|medium\|high\|off` | Nivel de razonamiento (slot 1). |
| `/json on\|off` | Salida estructurada con JSON Schema (slot 3). |
| `/contexto <archivos>` | Carga contexto estático. En el slot 2 lo marca para cachear. |
| `/resumen` | Totales de la conversación en curso. |
| `/salir` | Cierra el log escribiendo el total al pie. |

## Los cuatro modelos

| Slot | Modelo | Entrada | Salida | Contexto |
|---|---|---:|---:|---:|
| 1 | `openai/gpt-5.6-luna` | $0,20/M | $1,20/M | 1,05M |
| 2 | `anthropic/claude-haiku-4.5` | $1,00/M | $5,00/M | 200K |
| 3 | `google/gemini-3.7-flash` | $0,75/M | $3,75/M | 1,05M |
| 4 | `deepseek/deepseek-v4-flash-0731` | $0,055/M | $0,165/M | 1,31M |

Precios tomados de las fichas de OpenRouter. El costo real de cada llamada lo
informa la API en el campo `cost` de cada respuesta.

## Los tests de Conway

```bash
python tests/test_vida.py vida.py
```

Son los nueve casos de la cátedra, sin modificar.

## Documentos

- [`CLAUDE.md`](CLAUDE.md) — cómo se trabaja en este repo.
- [`SPEC.md`](SPEC.md) — qué se construyó y por qué.
- [`informe/informe.md`](informe/informe.md) — la cuenta final del ejercicio 3.
- [`informe/trabajo-previo.md`](informe/trabajo-previo.md) — router, mapa de
  modelos y parámetros soportados.
