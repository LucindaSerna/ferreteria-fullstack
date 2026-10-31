\# Ferretería Full Stack — Sistema de inventario y recomendaciones



\## 1. Descripción del proyecto



Aplicación web desarrollada como prueba técnica para una ferretería con cinco sucursales: Cancún, Chihuahua, Ciudad de México, Monterrey y Mérida.



El sistema permite consultar un catálogo de productos, seleccionar una sucursal, agregar artículos al carrito, recibir recomendaciones de productos relacionados y registrar compras.



Las cinco sucursales comparten un único inventario centralizado.



El proyecto incluye un modelo probabilístico de recomendaciones construido a partir de datos históricos de ventas.



\## 2. Tecnologías utilizadas



\- \*\*Python:\*\* procesamiento de datos y lógica del backend.

\- \*\*FastAPI:\*\* desarrollo de la API REST.

\- \*\*SQLite:\*\* almacenamiento de productos, compras e inventario.

\- \*\*React:\*\* interfaz web del cliente.

\- \*\*Vite:\*\* entorno de desarrollo del frontend.

\- \*\*Jupyter Notebook:\*\* exploración de datos, desarrollo del modelo y documentación técnica.

\- \*\*Git y GitHub:\*\* control de versiones.



\## 3. Estructura del proyecto



```text

ferreteria-fullstack/

├── Data/

│   ├── products.csv

│   ├── sales.csv

│   └── asociaciones\_modelo.csv

├── backend/

│   ├── database.py

│   ├── init\_db.py

│   └── main.py

├── frontend/

│   ├── package.json

│   └── src/

│       └── App.jsx

├── notebooks/

│   └── 01\_exploracion\_datos.ipynb

└── README.md

```



El archivo `ferreteria.db` se genera localmente y no se incluye en el repositorio.



\## 4. Modelo de recomendaciones



Se implementó un modelo probabilístico basado en la frecuencia con que dos productos aparecen en un mismo ticket de compra.



Para cada producto de origen \\(i\\) y producto candidato \\(j\\), se calcula una puntuación mediante suavizado bayesiano:



\\\[

\\hat{p}\_{ij}=\\frac{n\_{ij}+kq\_j}{n\_i+k}

\\]



Donde:



\- \\(n\_i\\): número de tickets que contienen el producto de origen.

\- \\(n\_{ij}\\): número de tickets que contienen ambos productos.

\- \\(q\_j\\): probabilidad base estimada para el producto candidato.

\- \\(k=5\\): parámetro de suavizado.



La probabilidad base se estima a partir de la frecuencia del producto candidato en los tickets, incorporando un suavizado adicional.



Este enfoque evita depender exclusivamente de frecuencias observadas en una muestra pequeña.



\### Funcionamiento de las recomendaciones



1\. El cliente agrega productos al carrito.

2\. Al abrir el carrito, React identifica el primer producto agregado.

3\. El frontend consulta el endpoint `GET /recomendaciones/{sku}`.

4\. FastAPI recupera las puntuaciones calculadas por el modelo.

5\. Se descartan los productos sin existencias.

6\. El frontend excluye los artículos que ya están en el carrito.

7\. Se muestran hasta cinco recomendaciones, ordenadas por puntuación.



Las recomendaciones son globales y no dependen de la sucursal seleccionada.



\### Limitaciones del modelo



\- El historial de ventas es reducido.

\- No existe historial de ventas para Mérida.

\- Las asociaciones estadísticas no garantizan compatibilidad técnica entre productos.

\- No se dispone de información sobre clics, visualizaciones o aceptación de recomendaciones.

\- La evaluación actual es principalmente exploratoria y cualitativa; no se presenta como una validación predictiva concluyente.

\- El modelo utiliza un archivo de puntuaciones previamente calculadas, por lo que no se actualiza automáticamente después de cada compra.



Como mejoras futuras se propone incorporar información de compatibilidad técnica, recomendaciones basadas en todos los productos del carrito, evaluación temporal y métricas como Precision@K y Recall@K.



\## 5. Instalación y ejecución



\### Requisitos



\- Python 3.10 o superior, con las dependencias compatibles.

\- Node.js y npm.

\- Git.



\### Paso 1. Clonar el repositorio



```bash

git clone https://github.com/LucindaSerna/ferreteria-fullstack.git

cd ferreteria-fullstack

```



\### Paso 2. Preparar el backend



Abrir una terminal en la carpeta `backend`:



```bash

cd backend

```



Crear y activar un entorno virtual es recomendable.



En Windows:



```powershell

python -m venv .venv

.\\.venv\\Scripts\\Activate.ps1

```



Instalar las dependencias:



```bash

python -m pip install fastapi "uvicorn\[standard]"

```



\### Paso 3. Inicializar la base de datos



Desde la carpeta `backend`, ejecutar:



```bash

python init\_db.py

```



El script crea las tablas necesarias y carga los 28 productos de `Data/products.csv`.



Si los productos ya existen, no los duplica ni restablece sus existencias.



\### Paso 4. Iniciar FastAPI



Desde la carpeta `backend`:



```bash

python -m uvicorn main:app --reload

```



La API estará disponible en:



http://127.0.0.1:8000



La documentación interactiva de los endpoints estará disponible en:



http://127.0.0.1:8000/docs



\### Paso 5. Preparar el frontend



Abrir una segunda terminal, entrar a la carpeta `frontend` e instalar las dependencias:



```bash

cd frontend

npm install

```



Iniciar React:



```bash

npm run dev

```



Abrir en el navegador la dirección que muestre Vite, normalmente:



http://localhost:5173



El backend debe permanecer encendido mientras se utiliza la aplicación.



\## 6. Endpoints principales



| Método | Endpoint | Descripción |

|---|---|---|

| GET | `/` | Comprueba que la API está funcionando |

| GET | `/productos` | Consulta el catálogo y el inventario actual |

| GET | `/recomendaciones/{sku}` | Obtiene productos relacionados y disponibles |

| POST | `/compras` | Registra una compra y descuenta existencias |



\### Ejemplo de compra



Petición a `POST /compras`:



```json

{

&#x20; "sucursal": "Mérida",

&#x20; "articulos": \[

&#x20;   {

&#x20;     "sku": "SKU001",

&#x20;     "cantidad": 1

&#x20;   }

&#x20; ]

}

```



El backend verifica la sucursal, los productos y las cantidades solicitadas.



El registro de compra y la actualización de existencias se realizan mediante una transacción SQLite. Si alguna validación falla, la operación se revierte para evitar compras parciales.



\## 7. Inventario compartido



El inventario es único para las cinco sucursales.



Por ejemplo, si un cliente compra una unidad del SKU001 en Mérida, la existencia central disminuye una unidad. La nueva cantidad queda disponible para las demás sucursales.



El sistema valida las existencias en el backend antes de confirmar la compra, en lugar de confiar únicamente en la información mostrada por React.



\## 8. Validaciones realizadas



Durante el desarrollo se comprobaron los siguientes escenarios:



\- Consulta del catálogo desde React.

\- Selección de las cinco sucursales.

\- Incorporación de productos al carrito.

\- Cálculo de cantidades y total.

\- Consulta de recomendaciones a FastAPI.

\- Exclusión de productos que ya están en el carrito.

\- Registro de una compra desde la interfaz.

\- Actualización de existencias en SQLite.

\- Rechazo de una compra con inventario insuficiente y reversión de la transacción.



La aplicación constituye una prueba de concepto funcional y no un sistema preparado para producción.



\## 9. Alcance y mejoras pendientes



La versión entregada prioriza el flujo de compra y la integración del modelo de recomendaciones.



Entre las funcionalidades y mejoras pendientes se encuentran:



\- Interfaz administrativa para crear, editar y eliminar productos.

\- Interfaz administrativa para consultar y modificar relaciones entre productos.

\- Pruebas automatizadas y evaluación cuantitativa del recomendador.

\- Persistencia del carrito después de recargar la página.

\- Autenticación y autorización de usuarios.

\- Manejo de concurrencia y escalabilidad para un entorno de producción.

\- Actualización periódica de las puntuaciones del modelo.

\- Personalización de recomendaciones por sucursal cuando exista suficiente información.



\## 10. Documentación técnica



El notebook `notebooks/01\_exploracion\_datos.ipynb` contiene la exploración de los datos, el desarrollo matemático del modelo, las decisiones de implementación y las validaciones realizadas.



Los archivos originales del catálogo y las ventas se encuentran en `Data/`.



\---



\*\*Estado del proyecto:\*\* prueba de concepto funcional con inventario centralizado, registro de compras y recomendaciones probabilísticas integradas en la interfaz web.

