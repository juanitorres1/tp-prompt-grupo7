# ROL

Sos un programador Python senior. Escribís scripts de línea de comandos
pequeños, correctos y sin dependencias externas. No explicás de más: entregás
el archivo.

# CONTEXTO

Necesito un script `vida.py` que implemente el juego de la vida de Conway. El
script va a ser evaluado por una batería de tests automáticos que lo invocan
como subproceso y comparan su salida exacta por stdout, carácter por carácter.
No hay tolerancia a diferencias de formato: un espacio de más o una línea en
blanco de más hacen fallar el test.

# INSTRUCCIONES

Escribí el contenido completo del archivo `vida.py`, usando únicamente la
biblioteca estándar de Python 3. El script lee un archivo de estado inicial y
la cantidad de generaciones desde los argumentos de línea de comandos, simula
esa cantidad de generaciones y escribe la grilla resultante por stdout.

# RESTRICCIONES

Este es el contrato exacto. No es negociable: es la interfaz que invocan los
tests.

1. Uso: `python3 vida.py <archivo_estado_inicial> <generaciones>`
2. El archivo de estado es una grilla rectangular: una línea por fila, `#` es
   célula viva y `.` es célula muerta.
3. El mundo es **finito**, del tamaño de la grilla. Todo lo que está fuera de
   los bordes cuenta como muerto. **No hay wrap-around**: la grilla no es un
   toro, los bordes no se conectan entre sí.
4. Cada célula tiene 8 vecinas (las 4 ortogonales y las 4 diagonales).
5. Reglas de transición, aplicadas **simultáneamente** sobre toda la grilla a
   partir del estado anterior:
   - Una célula viva con 2 o 3 vecinas vivas sigue viva.
   - Una célula viva con cualquier otra cantidad de vecinas vivas muere.
   - Una célula muerta con exactamente 3 vecinas vivas nace.
   - Cualquier otra célula muerta sigue muerta.
6. El script imprime por stdout la grilla resultante tras N generaciones, en el
   mismo formato de entrada: una línea por fila, sin espacios, sin numeración,
   sin encabezados y sin ningún texto adicional.
7. Con `generaciones = 0` imprime el estado inicial tal cual, sin aplicar
   ninguna regla.
8. El conteo de generaciones llega como texto en `sys.argv[2]` y hay que
   convertirlo a entero.
9. Solo biblioteca estándar. Sin numpy, sin argparse opcional, sin archivos
   auxiliares: un único archivo `vida.py`.

# EJEMPLOS

Tres casos de comportamiento, en el formato exacto de entrada y salida.

**Ejemplo 1 — el blinker oscila (1 generación).**

Archivo de estado:

```
.....
..#..
..#..
..#..
.....
```

Salida esperada con `generaciones = 1`:

```
.....
.....
.###.
.....
.....
```

**Ejemplo 2 — el borde no envuelve (1 generación).**

Archivo de estado:

```
###
...
...
```

Salida esperada con `generaciones = 1`:

```
.#.
.#.
...
```

Este caso es el que distingue un mundo finito de uno toroidal. La célula del
centro de la fila superior tiene 2 vecinas vivas y sobrevive; la de abajo del
centro tiene 3 vecinas vivas y nace. Si la grilla envolviera por los bordes, el
resultado sería otro.

**Ejemplo 3 — generación cero no cambia nada.**

Archivo de estado:

```
.....
..#..
..#..
..#..
.....
```

Salida esperada con `generaciones = 0`: el mismo bloque de texto, idéntico.

# INPUT

Devolvé únicamente el contenido del archivo `vida.py`, listo para guardar y
ejecutar. Sin explicación antes ni después, sin comentarios sobre tus
decisiones, y sin envolverlo en un bloque de markdown.
