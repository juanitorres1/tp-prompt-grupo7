# Informe — la cuenta final

Ejercicio 3. Todos los números salen de los logs de `logs/`, que están en el
repositorio. Cada fila es reconciliable contra el archivo que la respalda.

## Resultado del ejercicio 2

**El target salió en un solo prompt.** Los 9 tests de `tests/test_vida.py`
pasan contra el `vida.py` entregado, que es exactamente el texto que devolvió
`deepseek/deepseek-v4-flash-0731` en el log
`2026-09-18_1954-slot4-deepseek-deepseek-v4-flash-0731-intento-1.md`.

El archivo no se tocó a mano en ningún momento. Se extrajo del log con
`src/recuperar_codigo.py`, que aplica la misma extracción que usa la interfaz.

## Todos los intentos del ejercicio 2

| # | Corrida | Entrada | Salida | Razonamiento | Cacheados | Costo USD | Resultado |
|---|---|---:|---:|---:|---:|---:|---|
| 0 | Llamada interrumpida (19:49) | — | — | — | — | ver nota | Cortada por el usuario, sin respuesta |
| 1 | `intento-1` — el ganador | 1.056 | 7.616 | 7.291 | 0 | 0,002280 | **9/9 tests** |
| 2 | `demo-cache` | 1.056 | 366 | 286 | 0 | 0,000114 | Demostración de caching |
| 3 | `cache-A` | 1.424 | 152 | 132 | 0 | 0,000158 | Escribe el cache |
| 4 | `cache-B` | 1.424 | 254 | 218 | **1.423** | 0,000119 | Lee el cache |
| | **Total ejercicio 2** | **4.960** | **8.388** | **7.927** | **1.423** | **0,002671** | |

Las corridas 2, 3 y 4 **no son intentos de resolver el target**: su bloque
INPUT pide una respuesta en texto, no código. Existen para demostrar el
caching, que la misión exige y que la corrida ganadora no podía mostrar por
haber salido a la primera. Están acá igual, contadas, porque gastaron dinero.

**Nota sobre la corrida 0.** A las 19:49 se lanzó el mismo prompt del intento
ganador y la llamada se interrumpió con Ctrl+C mientras se recibía la
respuesta. El modelo ya había generado, así que es probable que esté facturada
en el dashboard sin log que la respalde: el archivo parcial se borró porque no
contenía ninguna respuesta. Es la causa esperada de la diferencia contra el
dashboard.

## Tokens de pensamiento y qué se facturó por ellos

**DeepSeek V4 Flash sí devuelve los tokens de razonamiento** en
`completion_tokens_details.reasoning_tokens`. No hizo falta documentar la
ausencia que la consigna anticipa para otros modelos.

El dato más fuerte del informe está acá: en el intento ganador, **7.291 de los
7.616 tokens de salida fueron razonamiento**. El 96%. El archivo `vida.py`
propiamente dicho son unos 325 tokens.

Es decir: **pagamos 23 veces más por pensar que por escribir**. Y el
razonamiento se factura como salida, que en este modelo cuesta tres veces la
entrada.

## Tokens cacheados y ahorro

El caching se demostró en dos proveedores, con mecánicas distintas.

**Anthropic (slot 2), caching explícito.** Contexto estático de ~6.000 tokens
marcado con `cache_control: ephemeral`:

| Pasada | Entrada | Cacheados | Costo USD |
|---|---:|---:|---:|
| Primera | 6.042 | 0 | 0,011890 |
| Segunda | 6.935 | 6.013 | **0,004173** |

La segunda pasada mandó **más** tokens que la primera y costó **un 65% menos**:
$0,007717 de ahorro en una sola llamada.

**DeepSeek (slot 4), caching automático por prefijo.** Acá hubo un hallazgo que
vale la pena reportar.

El primer intento de demostración (corrida 2) **no produjo ningún cache hit**,
pese a compartir con el intento ganador un prefijo idéntico de 3.147
caracteres. El prompt completo eran 1.056 tokens, así que el prefijo compartido
rondaba los **985 tokens**.

Al repetir el experimento con un prefijo de **1.424 tokens** (corridas 3 y 4),
el cache pegó de inmediato: 1.423 tokens cacheados de 1.424, todos menos uno.

**Conclusión medida: el cache por prefijo de DeepSeek necesita superar un
umbral que está entre 985 y 1.424 tokens**, compatible con el mínimo de 1.024
tokens que la documentación de OpenRouter declara para otros proveedores
(Gemini 2.5 Flash, Anthropic). La documentación no publica un mínimo para
DeepSeek; este experimento lo acota.

El ahorro en la corrida 4 fue de $0,000076, chico en términos absolutos porque
el prefijo es chico. Extrapolado al intento ganador, cachear su prefijo habría
ahorrado alrededor de un 5% del costo de entrada — una cifra menor, porque en
este target **el costo está en la salida, no en la entrada**.

## Gasto total

| Concepto | Entrada | Salida | Razonamiento | Cacheados | Costo USD |
|---|---:|---:|---:|---:|---:|
| Ejercicio 1 (4 logs de prueba) | 18.826 | 4.567 | 1.762 | 6.013 | 0,018821 |
| Ejercicio 2 (4 corridas) | 4.960 | 8.388 | 7.927 | 1.423 | 0,002671 |
| **Total según los logs** | **23.786** | **12.955** | **9.689** | **7.436** | **0,021492** |

**Contraste contra el dashboard de OpenRouter:**

> **Pendiente de completar:** el total que muestra `openrouter.ai/activity`.
> Se espera que sea **mayor** que $0,021492 por la llamada interrumpida de la
> corrida 0, que se facturó sin quedar registrada en ningún log. La diferencia
> debería rondar los $0,002, que es lo que costó la misma llamada cuando se
> completó.

**Una discrepancia adicional que conviene dejar anotada.** El campo `cost` que
informa la API no coincide con el cálculo directo precio × tokens usando los
precios de la ficha. Para el intento ganador:

- Esperado: 1.056 × $0,055/M + 7.616 × $0,165/M = **$0,001315**
- Informado por la API: **$0,002280** (un 73% más)

El precio efectivo de salida da ~$0,29/M en vez de los $0,165/M de la ficha. La
hipótesis más probable es que **los tokens de razonamiento se facturen a una
tarifa distinta** de los de salida común. En las corridas sin razonamiento
pesado la diferencia casi desaparece (la corrida 2 informó $0,000114 contra
$0,000118 calculados). Se reporta como hallazgo, no como conclusión cerrada:
haría falta una prueba controlada con y sin razonamiento para confirmarlo.

## Conclusión

**Bajaríamos el `reasoning.effort` de `high` a `medium` o lo apagaríamos.** El
96% de los tokens de salida del intento ganador fue pensamiento, y la tarea no
lo necesitaba: el prompt ya era una especificación completa con el contrato
literal y tres ejemplos de entrada/salida. El razonamiento estaba resolviendo
un problema que el prompt ya tenía resuelto.

**No moveríamos el modelo.** DeepSeek V4 Flash resolvió el target a la primera
por $0,00228. El slot 2, Claude Haiku, cuesta 18 veces más por token de entrada
y 30 veces más por token de salida: la misma corrida habría costado cerca de
$0,04. No hay margen de mejora que justifique subir de escalón.

**El caching no es la palanca en este target.** Se demostró que funciona en los
dos proveedores, pero acá el gasto está en la salida y el cache solo abarata la
entrada. Sirve cuando se repite un contexto grande —como el del slot 2, donde
ahorró el 65%—, no cuando el prompt es corto y la respuesta larga. Reconocer
dónde *no* conviene aplicar una técnica es parte de la respuesta.
