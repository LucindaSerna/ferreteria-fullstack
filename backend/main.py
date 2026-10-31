from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI

app = FastAPI(
    title="API Ferretería",
    description="Sistema de inventario y recomendaciones",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def inicio():
    return {
        "mensaje": "Bienvenido a la API de Ferretería",
        "estado": "funcionando"
    }


from database import conectar

@app.get("/productos")
def obtener_productos():
    with conectar() as conexion:
        productos = conexion.execute(
            "SELECT * FROM productos ORDER BY sku"
        ).fetchall()

    return [dict(producto) for producto in productos]


from pydantic import BaseModel, Field
from fastapi import HTTPException
from database import registrar_compra, SUCURSALES

class ArticuloCompra(BaseModel):
    sku: str
    cantidad: int = Field(gt=0, strict=True)

class SolicitudCompra(BaseModel):
    sucursal: str
    articulos: list[ArticuloCompra]

@app.post("/compras", status_code=201)
def crear_compra(solicitud: SolicitudCompra):
    if solicitud.sucursal not in SUCURSALES:
        raise HTTPException(status_code=422, detail="Sucursal no válida")

    try:
        return registrar_compra(
            solicitud.sucursal,
            [articulo.model_dump() for articulo in solicitud.articulos]
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


import csv
from pathlib import Path

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

    disponibles = {
        producto["sku"]: dict(producto)
        for producto in productos
    }

    ruta_modelo = (
        Path(__file__).resolve().parent.parent
        / "Data"
        / "asociaciones_modelo.csv"
    )

    recomendaciones = []

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

            recomendaciones.append({
                **disponibles[candidato],
                "puntuacion": float(fila["media_posterior"])
            })

    recomendaciones.sort(
        key=lambda producto: producto["puntuacion"],
        reverse=True
    )

    return {
        "sku_origen": sku,
        "recomendaciones": recomendaciones[:limite]
    }
