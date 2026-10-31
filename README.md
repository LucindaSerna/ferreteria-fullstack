
# Ferretería Full Stack — Sistema de inventario y recomendaciones

## 1. Descripción del proyecto

Aplicación web desarrollada como prueba técnica para una ferretería con cinco sucursales: Cancún, Chihuahua, Ciudad de México, Monterrey y Mérida.

El sistema permite consultar un catálogo de productos, seleccionar una sucursal, agregar artículos al carrito, recibir recomendaciones de productos relacionados y registrar compras.

Las cinco sucursales comparten un inventario centralizado.

El proyecto integra un modelo probabilístico de recomendaciones desarrollado a partir de datos históricos de ventas y reglas de negocio implementadas en el backend.

**Estado:** prueba de concepto funcional. No es un sistema preparado para producción.

## 2. Tecnologías utilizadas

- **Python:** procesamiento de datos y lógica del backend.
- **FastAPI:** desarrollo de la API REST.
- **SQLite:** almacenamiento de productos, compras e inventario.
- **React:** interfaz web.
- **Vite:** entorno de desarrollo del frontend.
- **Jupyter Notebook:** exploración de datos, formulación matemática y evaluación del recomendador.
- **Git y GitHub:** control de versiones.

## 3. Estructura del proyecto

```text
ferreteria-fullstack/
├── Data/
│   ├── products.csv
│   ├── sales.csv
│   └── asociaciones_modelo.csv
├── backend/
│   ├── database.py
│   ├── init_db.py
│   └── main.py
├── frontend/
│   ├── package.json
│   └── src/
│       └── App.jsx
├── notebooks/
│   └── 01_exploracion_datos.ipynb
└── README.md
```

El archivo `ferreteria.db` se genera localmente y no se incluye en el repositorio.

## 4. Modelo de recomendaciones

### 4.1. Objetivo

El recomendador busca identificar productos que suelen comprarse conjuntamente, con el propósito de apoyar la venta cruzada.

El modelo utiliza asociaciones dirigidas entre productos.

Una relación `SKU001 → SKU004` no necesariamente tiene la misma puntuación que `SKU004 → SKU001`, porque las probabilidades condicionales dependen del producto de origen.

### 4.2. Datos utilizados

El conjunto de datos contiene:

- 28 productos en el catálogo.
- 42 tickets históricos.
- 89 incidencias de productos en tickets.
- 756 relaciones dirigidas posibles entre productos distintos.

El historial es pequeño, por lo que se utiliza suavizado bayesiano para evitar depender exclusivamente de frecuencias empíricas inestables.

### 4.3. Formulación matemática

Para cada producto de origen $i$ y producto candidato $j$, se estima:

$$
\widehat{p}_{j \mid i}
=
\frac{n_{ij}+kq_j}{n_i+k}
$$

Donde:

- $n_i$: número de tickets que contienen el producto de origen $i$.
- $n_{ij}$: número de tickets que contienen ambos productos.
- $q_j$: popularidad histórica suavizada del producto candidato $j$.
- $k$: parámetro que controla la influencia de la distribución previa.

La popularidad suavizada se calcula mediante:

$$
q_j=\frac{n_j+\varepsilon}{N+2\varepsilon}
$$

Donde:

- $n_j$: número de tickets que contienen el producto candidato.
- $N$: número total de tickets.
- $\varepsilon$: parámetro de suavizado de la popularidad.

En la implementación se utilizan:

$$
k=5,\qquad \varepsilon=0.5
$$

La distribución previa es:

$$
p_{j\mid i}\sim
\operatorname{Beta}(kq_j,\ k(1-q_j))
$$

La puntuación final corresponde a la media posterior de esta distribución, después de incorporar las coocurrencias observadas.

### 4.4. Evaluación cuantitativa

Se realizó una evaluación exploratoria mediante **Leave-One-Ticket-Out**.

En cada iteración se excluyó un ticket del entrenamiento, se recalcularon las puntuaciones y se evaluaron recomendaciones para productos contenidos en el ticket excluido.

Se construyeron 89 casos de evaluación a partir de los 42 tickets históricos.

Se comparó el modelo bayesiano con una referencia basada en popularidad.

| Métrica | Modelo bayesiano | Popularidad |
|---|---:|---:|
| Hit Rate@3 | 0.2697 | 0.0000 |
| Precision@3 | 0.0936 | 0.0000 |
| Recall@3 | 0.2397 | 0.0000 |

En esta evaluación, el modelo bayesiano obtuvo mejores resultados que la referencia de popularidad.

Sin embargo, los casos derivados de un mismo ticket no son independientes. El tamaño del conjunto de datos es reducido y estos resultados no garantizan desempeño futuro.

### 4.5. Análisis de sensibilidad

Se evaluaron los valores:

$$
k \in \{1,2,5,10,20\}
$$

Las métricas permanecieron iguales entre $k=1$ y $k=10$, mientras que disminuyeron para $k=20$.

Se conservó $k=5$ como valor de referencia exploratorio, sin considerarlo estadísticamente óptimo.

### 4.6. Integración con reglas de negocio

El notebook genera el archivo `Data/asociaciones_modelo.csv`, que contiene las puntuaciones calculadas.

FastAPI utiliza estas puntuaciones y aplica reglas adicionales:

1. Excluye el producto de origen.
2. Descarta productos sin existencias.
3. Consulta si existen relaciones manuales configuradas.
4. Cuando existe una puntuación manual para una relación, esta sustituye la puntuación bayesiana correspondiente.
5. Ordena los candidatos por puntuación.
6. Devuelve hasta tres recomendaciones.

Las puntuaciones manuales son reglas de negocio y no deben interpretarse como probabilidades posteriores estimadas por el modelo.

La interfaz también evita mostrar como recomendación productos que ya están en el carrito.

Actualmente, el recomendador utiliza como origen el primer producto agregado al carrito; no calcula una puntuación conjunta para todos los artículos seleccionados.

Las recomendaciones son globales y no dependen de la sucursal.

### 4.7. Limitaciones

- El historial contiene solamente 42 tickets.
- No existe historial de ventas para Mérida.
- Las asociaciones estadísticas no garantizan compatibilidad técnica.
- No se dispone de datos de clics o aceptación de recomendaciones.
- La evaluación es retrospectiva y exploratoria.
- El modelo no se actualiza automáticamente después de cada compra.
- No se ha medido el impacto causal sobre ventas.
- No se implementó un optimizador combinatorio general: los candidatos se ordenan por puntuación y se seleccionan los primeros disponibles.

## 5. Instalación y ejecución

### Requisitos

- Python 3.10 o superior, con dependencias compatibles.
- Node.js y npm.
- Git.

### Paso 1. Clonar el repositorio

```bash
git clone https://github.com/LucindaSerna/ferreteria-fullstack.git
cd ferreteria-fullstack
```

### Paso 2. Preparar el backend

Abrir una terminal en la carpeta `backend`:

```bash
cd backend
```

Se recomienda crear un entorno virtual.

En Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instalar las dependencias:

```bash
python -m pip install -r requirements.txt
```

### Paso 3. Inicializar la base de datos

Desde la carpeta `backend`, ejecutar:

```bash
python init_db.py
```

El script crea las tablas necesarias y carga los productos iniciales desde `Data/products.csv`.

Si los productos ya existen, no los duplica ni restablece sus existencias.

### Paso 4. Iniciar FastAPI

Desde `backend`:

```bash
python -m uvicorn main:app --reload
```

API:

http://127.0.0.1:8000

Documentación interactiva:

http://127.0.0.1:8000/docs

### Paso 5. Preparar el frontend

Abrir una segunda terminal.

Desde la carpeta raíz del proyecto:

```bash
cd frontend
npm install
npm run dev
```

Abrir la dirección indicada por Vite, normalmente:

http://localhost:5173

El backend debe permanecer encendido mientras se utiliza la aplicación.

### Paso 6. Ejecutar el notebook (opcional)

El notebook documenta el análisis estadístico y la evaluación.

Para ejecutarlo se requiere un entorno de Python con Jupyter y las bibliotecas utilizadas en sus celdas.

El archivo `Data/asociaciones_modelo.csv` permite utilizar el recomendador desde la aplicación sin volver a entrenar el modelo en cada consulta.

## 6. API REST

### Endpoints principales

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/` | Comprueba el funcionamiento de la API |
| GET | `/productos` | Consulta catálogo e inventario |
| GET | `/recomendaciones/{sku}` | Obtiene hasta tres recomendaciones |
| POST | `/compras` | Registra compras y descuenta existencias |

El backend también incluye operaciones de mantenimiento de productos y relaciones manuales, disponibles en la documentación interactiva de FastAPI.

### Ejemplo de consulta

```http
GET /recomendaciones/SKU001?limite=3
```

La API devuelve productos relacionados disponibles, junto con sus puntuaciones.

### Ejemplo de compra

Petición a `POST /compras`:

```json
{
  "sucursal": "Mérida",
  "articulos": [
    {
      "sku": "SKU001",
      "cantidad": 1
    }
  ]
}
```

El backend valida la sucursal, los productos, las cantidades y las existencias.

La compra y la actualización del inventario se procesan mediante una transacción SQLite para evitar registros parciales ante errores.

## 7. Inventario compartido

Las cinco sucursales utilizan un inventario centralizado.

Si se registra una compra en una sucursal, la existencia del producto disminuye en la base de datos compartida.

La validación de existencias se realiza en el backend antes de confirmar la compra.

## 8. Validaciones realizadas

Durante el desarrollo se verificaron:

- Consulta del catálogo desde la interfaz.
- Selección de sucursales.
- Incorporación de productos al carrito.
- Cálculo del total.
- Consulta de recomendaciones desde React.
- Límite de tres recomendaciones.
- Exclusión del producto de origen.
- Ausencia de recomendaciones duplicadas en la evaluación del ranking.
- Filtrado de productos sin existencias.
- Registro de una compra desde React.
- Respuesta ante un SKU inexistente.
- Evaluación cuantitativa Leave-One-Ticket-Out.
- Comparación con una referencia de popularidad.
- Análisis de sensibilidad del parámetro $k$.

Las verificaciones automáticas del ranking se realizaron sobre los 89 casos de evaluación y no sustituyen pruebas integrales de toda la aplicación.

## 9. Alcance y mejoras pendientes

Entre las mejoras futuras se encuentran:

- Incorporar reglas explícitas de compatibilidad técnica entre productos.
- Utilizar todos los artículos del carrito para generar recomendaciones.
- Implementar pruebas automatizadas integrales del backend y frontend.
- Evaluar el modelo con más datos y periodos temporales separados.
- Medir aceptación de recomendaciones y efecto sobre ventas.
- Incorporar autenticación y autorización para operaciones administrativas.
- Mejorar la persistencia del carrito.
- Considerar concurrencia y escalabilidad.
- Automatizar la actualización periódica de las puntuaciones.
- Incorporar personalización por sucursal cuando existan suficientes datos.

## 10. Documentación técnica

El notebook `notebooks/01_exploracion_datos.ipynb` contiene:

- Exploración del catálogo y las ventas.
- Construcción de tickets y asociaciones dirigidas.
- Formulación del modelo bayesiano.
- Cálculo de puntuaciones.
- Evaluación Leave-One-Ticket-Out.
- Comparación con popularidad.
- Análisis de sensibilidad.
- Discusión de limitaciones y decisiones metodológicas.

Los archivos de datos se encuentran en `Data/`.

---

**Estado del proyecto:** prueba de concepto funcional con inventario centralizado, registro de compras y recomendaciones probabilísticas integradas en una interfaz web.
