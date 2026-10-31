import csv
from pathlib import Path

from database import conectar, crear_tablas

BASE_DIR = Path(__file__).resolve().parent.parent
PRODUCTOS_CSV = BASE_DIR / "Data" / "products.csv"


def inicializar_base_datos():
    # Crear las tablas de SQLite
    crear_tablas()

    # Leer el catálogo de productos
    with PRODUCTOS_CSV.open(
        mode="r",
        encoding="utf-8-sig",
        newline=""
    ) as archivo:
        productos = list(csv.DictReader(archivo))

    # Cargar los productos sin duplicar registros
    with conectar() as conexion:
        for producto in productos:
            conexion.execute(
                """
                INSERT OR IGNORE INTO productos (
                    sku, nombre, descripcion, categoria,
                    material, uso_recomendado, precio, stock
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    producto["sku"],
                    producto["nombre"],
                    producto["descripcion"],
                    producto["categoria"],
                    producto["material"],
                    producto["uso_recomendado"],
                    int(producto["precio"]),
                    int(producto["stock"])
                )
            )

        conexion.commit()

    print(
        f"Inicialización completada. "
        f"Catálogo de referencia: {len(productos)} productos."
    )


if __name__ == "__main__":
    inicializar_base_datos()