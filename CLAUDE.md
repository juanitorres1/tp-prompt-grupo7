# Instrucciones del proyecto

Chat sobre OpenRouter para la misión *el prompt mínimo*. Este archivo dirige
cómo se trabaja acá: leelo antes de tocar nada.

## Cómo se corre

```bash
python -m unittest discover -s tests -v   # tests, no tocan la red
winpty python src/chat.py                 # el chat (winpty solo en Git Bash)
```

No hay dependencias: **solo biblioteca estándar**. No agregar `requirements.txt`
ni `pip install` sin una razón que justifique romper eso — el repo tiene que
correr en la máquina del corrector sin instalar nada.

La API key vive en `.env`, que está en `.gitignore`. **Nunca** commitear la key
ni pegarla en un archivo de código. Si se filtra a un commit, rotarla en
OpenRouter antes que nada: el historial de git es público.

## Arquitectura

| Archivo | Responsabilidad |
|---|---|
| `src/openrouter.py` | Cliente HTTP y normalización del `usage`. No sabe nada de la interfaz. |
| `src/registro.py` | Escribe el log `.md` de cada conversación. No sabe nada de HTTP. |
| `src/chat.py` | El REPL: pega las dos piezas y maneja los comandos. |

La separación importa: el parseo del `usage` y el formato del log son las dos
cosas que se pueden testear sin gastar un centavo, y son justo las que tienen
que estar bien para que el informe cierre contra los logs.

## Reglas que no se negocian

**`vida.py` no se toca.** Entra al repo tal cual salió del chat. Si los tests
fallan, se arregla **el prompt** y se abre una conversación nueva, nunca el
archivo. La rúbrica compara el `vida.py` entregado contra el que aparece en el
log ganador: si no coinciden, el ejercicio 2 vale cero.

**`tests/test_vida.py` es de la cátedra.** Entra tal cual se entregó. No se
adapta el test al código.

**Los logs son evidencia, no se editan.** Ni para corregir un typo. Un log con
marcas de tiempo fuera de orden es una señal de alarma explícita en la rúbrica.

**Los intentos quemados se entregan.** Esconder un intento fallido cuesta más
puntos que haberlo tenido.

## Cómo se agrega código

TDD: primero el test, después la implementación. Todo lo que no toca la red se
testea. Lo que toca la red se prueba a mano desde el chat y queda registrado en
un log.

Commits chicos y con mensaje que explique el cambio, en imperativo y con
prefijo: `feat:`, `fix:`, `docs:`, `chore:`, `test:`. Un único commit "todo" es
un criterio perdido de la rúbrica.

## Contabilidad

Cada respuesta muestra cinco números: entrada, salida, razonamiento, cacheados
y costo. Los cinco van también al log. El informe del ejercicio 3 se arma
sumando esos logs, y tiene que cerrar contra el dashboard de OpenRouter. Si no
cierra, la diferencia se explica; no se maquilla.
