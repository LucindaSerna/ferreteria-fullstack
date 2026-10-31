
import csv
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import conectar, registrar_compra, SUCURSALES


app = FastAPI(
    title="API Ferretería",
    description="Sistema de inventario y recomendaciones",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# INICIO
# --------------------------------------------------

@app.get("/")
def inicio():
    return {
        "mensaje": "Bienvenido a la API de Ferretería",
        "estado": "funcionando"
    }


# --------------------------------------------------
# CONSULTA DE PRODUCTOS
# --------------------------------------------------

@app.get("/productos")
def obtener_productos():
    with conectar() as conexion:
        productos = conexion.execute(
            "SELECT * FROM productos ORDER BY sku"
        ).fetchall()

    return [dict(producto) for producto in productos]


# --------------------------------------------------
# COMPRAS
# --------------------------------------------------

class ArticuloCompra(BaseModel):
    sku: str
    cantidad: int = Field(gt=0, strict=True)


class SolicitudCompra(BaseModel):
    sucursal: str
    articulos: list[ArticuloCompra]


@app.post("/compras", status_code=201)
def crear_compra(solicitud: SolicitudCompra):
    if solicitud.sucursal not in SUCURSALES:
        raise HTTPException(
            status_code=422,
            detail="Sucursal no válida"
        )

    try:
        return registrar_compra(
            solicitud.sucursal,
            [
                articulo.model_dump()
                for articulo in solicitud.articulos
            ]
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# --------------------------------------------------
# RECOMENDACIONES
# --------------------------------------------------

@app.get("/recomendaciones/{sku}")
def obtener_recomendaciones(sku: str, limite: int = 5):

    if not 1 <= limite <= 28:
        raise HTTPException(
            status_code=422,
            detail="El límite debe estar entre 1 y 28"
        )

    with conectar() as conexion:
        origen = conexion.execute(
            "SELECT sku FROM productos WHERE sku = ?",
            (sku,)
        ).fetchone()

        if origen is None:
            raise HTTPException(
                status_code=404,
                detail="Producto no encontrado"
            )

        productos = conexion.execute(
            "SELECT * FROM productos WHERE stock > 0"
        ).fetchall()

        relaciones_manuales = conexion.execute(
            """
            SELECT sku_recomendado, puntuacion
            FROM relaciones_manual
            WHERE sku_origen = ?
            """,
            (sku,)
        ).fetchall()

    disponibles = {
        producto["sku"]: dict(producto)
        for producto in productos
    }

    puntuaciones_manuales = {
        relacion["sku_recomendado"]: relacion["puntuacion"]
        for relacion in relaciones_manuales
    }

    ruta_modelo = (
        Path(__file__).resolve().parent.parent
        / "Data"
        / "asociaciones_modelo.csv"
    )

    recomendaciones_por_sku = {}

    # Cargar las puntuaciones del modelo bayesiano
    with ruta_modelo.open(
        encoding="utf-8-sig",
        newline=""
    ) as archivo:

        lector = csv.DictReader(archivo)

        for fila in lector:
            candidato = fila["sku_recomendado"]

            if fila["sku_origen"] != sku:
                continue

            if candidato == sku or candidato not in disponibles:
                continue

            recomendaciones_por_sku[candidato] = {
                **disponibles[candidato],
                "puntuacion": float(fila["media_posterior"])
            }

    # Las modificaciones manuales tienen prioridad
    for candidato, puntuacion in puntuaciones_manuales.items():

        if candidato == sku or candidato not in disponibles:
            continue

        recomendaciones_por_sku[candidato] = {
            **disponibles[candidato],
            "puntuacion": puntuacion
        }

    recomendaciones = list(recomendaciones_por_sku.values())

    recomendaciones.sort(
        key=lambda producto: producto["puntuacion"],
        reverse=True
    )

    return {
        "sku_origen": sku,
        "recomendaciones": recomendaciones[:limite]
    }


# --------------------------------------------------
# CRUD DE PRODUCTOS
# --------------------------------------------------

class ProductoNuevo(BaseModel):
    sku: str = Field(min_length=1)
    nombre: str = Field(min_length=1)
    descripcion: str = ""
    categoria: str = ""
    material: str = ""
    uso_recomendado: str = ""
    precio: int = Field(ge=0, strict=True)
    stock: int = Field(ge=0, strict=True)


@app.post("/productos", status_code=201)
def crear_producto(producto: ProductoNuevo):
    with conectar() as conexion:

        existente = conexion.execute(
            "SELECT sku FROM productos WHERE sku = ?",
            (producto.sku,)
        ).fetchone()

        if existente is not None:
            raise HTTPException(
                status_code=409,
                detail="Ya existe un producto con ese SKU"
            )

        conexion.execute(
            """
            INSERT INTO productos (
                sku, nombre, descripcion, categoria,
                material, uso_recomendado, precio, stock
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                producto.sku,
                producto.nombre,
                producto.descripcion,
                producto.categoria,
                producto.material,
                producto.uso_recomendado,
                producto.precio,
                producto.stock
            )
        )

        conexion.commit()

    return {
        "mensaje": "Producto creado correctamente",
        "sku": producto.sku
    }


class ProductoActualizado(BaseModel):
    nombre: str = Field(min_length=1)
    descripcion: str = ""
    categoria: str = ""
    material: str = ""
    uso_recomendado: str = ""
    precio: int = Field(ge=0, strict=True)
    stock: int = Field(ge=0, strict=True)


@app.put("/productos/{sku}")
def actualizar_producto(
    sku: str,
    producto: ProductoActualizado
):
    with conectar() as conexion:

        existente = conexion.execute(
            "SELECT sku FROM productos WHERE sku = ?",
            (sku,)
        ).fetchone()

        if existente is None:
            raise HTTPException(
                status_code=404,
                detail="Producto no encontrado"
            )

        conexion.execute(
            """
            UPDATE productos
            SET nombre = ?,
                descripcion = ?,
                categoria = ?,
                material = ?,
                uso_recomendado = ?,
                precio = ?,
                stock = ?
            WHERE sku = ?
            """,
            (
                producto.nombre,
                producto.descripcion,
                producto.categoria,
                producto.material,
                producto.uso_recomendado,
                producto.precio,
                producto.stock,
                sku
            )
        )

        conexion.commit()

    return {
        "mensaje": "Producto actualizado correctamente",
        "sku": sku
    }


@app.delete("/productos/{sku}")
def eliminar_producto(sku: str):
    with conectar() as conexion:

        existente = conexion.execute(
            "SELECT sku FROM productos WHERE sku = ?",
            (sku,)
        ).fetchone()

        if existente is None:
            raise HTTPException(
                status_code=404,
                detail="Producto no encontrado"
            )

        try:
            conexion.execute(
                "DELETE FROM productos WHERE sku = ?",
                (sku,)
            )
            conexion.commit()

        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=409,
                detail=(
                    "No se puede eliminar un producto "
                    "que tenga compras o relaciones asociadas"
                )
            )

    return {
        "mensaje": "Producto eliminado correctamente",
        "sku": sku
    }


# --------------------------------------------------
# ADMINISTRACIÓN DE RELACIONES
# --------------------------------------------------

class RelacionActualizada(BaseModel):
    puntuacion: float = Field(ge=0, le=1)


@app.get("/relaciones/{sku}")
def consultar_relaciones(sku: str):
    with conectar() as conexion:

        producto = conexion.execute(
            "SELECT sku FROM productos WHERE sku = ?",
            (sku,)
        ).fetchone()

        if producto is None:
            raise HTTPException(
                status_code=404,
                detail="Producto no encontrado"
            )

        relaciones_manuales = conexion.execute(
            """
            SELECT sku_recomendado, puntuacion
            FROM relaciones_manual
            WHERE sku_origen = ?
            ORDER BY puntuacion DESC
            """,
            (sku,)
        ).fetchall()

    return {
        "sku_origen": sku,
        "relaciones_manuales": [
            dict(relacion)
            for relacion in relaciones_manuales
        ]
    }


@app.put("/relaciones/{sku_origen}/{sku_recomendado}")
def actualizar_relacion(
    sku_origen: str,
    sku_recomendado: str,
    relacion: RelacionActualizada
):
    if sku_origen == sku_recomendado:
        raise HTTPException(
            status_code=422,
            detail="Un producto no puede recomendarse a sí mismo"
        )

    with conectar() as conexion:

        productos = conexion.execute(
            """
            SELECT sku
            FROM productos
            WHERE sku IN (?, ?)
            """,
            (sku_origen, sku_recomendado)
        ).fetchall()

        if len(productos) != 2:
            raise HTTPException(
                status_code=404,
                detail="Uno o ambos productos no existen"
            )

        conexion.execute(
            """
            INSERT INTO relaciones_manual
                (sku_origen, sku_recomendado, puntuacion)
            VALUES (?, ?, ?)
            ON CONFLICT(sku_origen, sku_recomendado)
            DO UPDATE SET puntuacion = excluded.puntuacion
            """,
            (
                sku_origen,
                sku_recomendado,
                relacion.puntuacion
            )
        )

        conexion.commit()

    return {
        "mensaje": "Relación actualizada correctamente",
        "sku_origen": sku_origen,
        "sku_recomendado": sku_recomendado,
        "puntuacion": relacion.puntuacion
    }


@app.delete("/relaciones/{sku_origen}/{sku_recomendado}")
def eliminar_relacion_manual(
    sku_origen: str,
    sku_recomendado: str
):
    with conectar() as conexion:

        resultado = conexion.execute(
            """
            DELETE FROM relaciones_manual
            WHERE sku_origen = ?
              AND sku_recomendado = ?
            """,
            (sku_origen, sku_recomendado)
        )

        if resultado.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="No existe una modificación manual para esa relación"
            )

        conexion.commit()

    return {
        "mensaje": "Modificación manual eliminada correctamente",
        "sku_origen": sku_origen,
        "sku_recomendado": sku_recomendado
    }
