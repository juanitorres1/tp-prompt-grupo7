import sys

def main():
    archivo = sys.argv[1]
    generaciones = int(sys.argv[2])

    with open(archivo) as f:
        grid = [line.rstrip("\n") for line in f]

    filas = len(grid)
    columnas = len(grid[0]) if filas else 0

    for _ in range(generaciones):
        nuevo = []
        for r in range(filas):
            fila = []
            for c in range(columnas):
                vecinas = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr = r + dr
                        nc = c + dc
                        if 0 <= nr < filas and 0 <= nc < columnas and grid[nr][nc] == "#":
                            vecinas += 1

                if grid[r][c] == "#":
                    fila.append("#" if vecinas in (2, 3) else ".")
                else:
                    fila.append("#" if vecinas == 3 else ".")
            nuevo.append("".join(fila))
        grid = nuevo

    for fila in grid:
        print(fila)

if __name__ == "__main__":
    main()
