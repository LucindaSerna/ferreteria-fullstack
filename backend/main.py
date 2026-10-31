
from fastapi import FastAPI

app = FastAPI(
    title="API Ferretería",
    description="Sistema de inventario y recomendaciones",
    version="1.0.0"
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
