
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "Data" / "ferreteria.db"


def conectar():
    conexion = sqlite3.connect(DB_PATH, timeout=30)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def crear_tablas():
    with conectar() as conexion:

        conexion.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                sku TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                categoria TEXT,
                material TEXT,
                uso_recomendado TEXT,
                precio INTEGER NOT NULL CHECK (precio >= 0),
                stock INTEGER NOT NULL CHECK (stock >= 0)
            )
        """)

        conexion.execute("""
            CREATE TABLE IF NOT EXISTS compras (
                id_compra INTEGER PRIMARY KEY AUTOINCREMENT,
                sucursal TEXT NOT NULL CHECK (
                    sucursal IN (
                        'Cancún',
                        'Chihuahua',
                        'Ciudad de México',
                        'Monterrey',
                        'Mérida'
                    )
                ),
                fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conexion.execute("""
            CREATE TABLE IF NOT EXISTS detalle_compras (
                id_compra INTEGER NOT NULL,
                sku TEXT NOT NULL,
                cantidad INTEGER NOT NULL CHECK (cantidad > 0),
                precio_unitario INTEGER NOT NULL CHECK (precio_unitario >= 0),

                PRIMARY KEY (id_compra, sku),

                FOREIGN KEY (id_compra)
                    REFERENCES compras(id_compra),

                FOREIGN KEY (sku)
                    REFERENCES productos(sku)
            )
        """)

        conexion.commit()


SUCURSALES = (
    "Cancún",
    "Chihuahua",
    "Ciudad de México",
    "Monterrey",
    "Mérida"
)


def registrar_compra(sucursal, articulos):
    """
    Registra una compra y descuenta el inventario compartido.

    articulos: lista de diccionarios:
        [{"sku": "SKU001", "cantidad": 2}]
    """

    if sucursal not in SUCURSALES:
        raise ValueError("Sucursal no válida")

    if not articulos:
        raise ValueError("La compra debe contener productos")

    # Agrupamos SKU repetidos antes de descontar existencias
    cantidades = {}

    for articulo in articulos:
        sku = articulo["sku"]
        cantidad = articulo["cantidad"]

        if not isinstance(cantidad, int) or isinstance(cantidad, bool):
            raise ValueError("La cantidad debe ser un entero")

        if cantidad <= 0:
            raise ValueError("La cantidad debe ser positiva")

        cantidades[sku] = cantidades.get(sku, 0) + cantidad

    conexion = conectar()

    try:
        # Reservamos el acceso de escritura
        conexion.execute("BEGIN IMMEDIATE")

        cursor = conexion.execute(
            "INSERT INTO compras (sucursal) VALUES (?)",
            (sucursal,)
        )

        id_compra = cursor.lastrowid
        total = 0

        for sku, cantidad in cantidades.items():

            producto = conexion.execute(
                "SELECT precio FROM productos WHERE sku = ?",
                (sku,)
            ).fetchone()

            if producto is None:
                raise ValueError(f"Producto inexistente: {sku}")

            precio = producto["precio"]

            # Solo descuenta si existe inventario suficiente
            resultado = conexion.execute(
                """
                UPDATE productos
                SET stock = stock - ?
                WHERE sku = ? AND stock >= ?
                """,
                (cantidad, sku, cantidad)
            )

            if resultado.rowcount != 1:
                raise ValueError(
                    f"Inventario insuficiente para {sku}"
                )

            conexion.execute(
                """
                INSERT INTO detalle_compras
                    (id_compra, sku, cantidad, precio_unitario)
                VALUES (?, ?, ?, ?)
                """,
                (id_compra, sku, cantidad, precio)
            )

            total += precio * cantidad

        conexion.commit()

        return {
            "id_compra": id_compra,
            "sucursal": sucursal,
            "total": total,
            "articulos": cantidades
        }

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()
