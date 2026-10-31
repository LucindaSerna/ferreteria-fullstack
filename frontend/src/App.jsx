import { useEffect, useState } from 'react'

function App() {
  // 1. Variables de estado
  const [productos, setProductos] = useState([])
  const [error, setError] = useState('')
  const [carrito, setCarrito] = useState([])
  const [sucursal, setSucursal] = useState('Ciudad de México')
  const [mostrarCarrito, setMostrarCarrito] = useState(false)
  const [recomendaciones, setRecomendaciones] = useState([])
  const [cargandoRecomendaciones, setCargandoRecomendaciones] = useState(false)
  const [errorRecomendaciones, setErrorRecomendaciones] = useState('')
// Producto de referencia para el modelo de recomendaciones
const primerSku = carrito.length > 0 ? carrito[0].sku : null

  // 2. Consultar productos desde FastAPI
  useEffect(() => {
    fetch('http://127.0.0.1:8000/productos')
      .then((respuesta) => {
        if (!respuesta.ok) {
          throw new Error('No se pudo consultar el catálogo')
        }

        return respuesta.json()
      })
      .then((datos) => {
        setProductos(datos)
        setError('')
      })
      .catch(() => {
        setError('No se pudo conectar con el backend')
      })
  }, [])
  
   // Consultar recomendaciones del primer producto del carrito
useEffect(() => {
  if (!mostrarCarrito || !primerSku) {
    return
  }

  setCargandoRecomendaciones(true)
  setErrorRecomendaciones('')

  fetch(`http://127.0.0.1:8000/recomendaciones/${primerSku}?limite=3`)
    .then((respuesta) => {
      if (!respuesta.ok) {
        throw new Error('No se pudieron consultar las recomendaciones')
      }

      return respuesta.json()
    })
    .then((datos) => {
      setRecomendaciones(datos.recomendaciones)
    })
    .catch(() => {
      setErrorRecomendaciones('No fue posible obtener las recomendaciones')
      setRecomendaciones([])
    })
    .finally(() => {
      setCargandoRecomendaciones(false)
    })
}, [mostrarCarrito, primerSku])

  // 3. Agregar productos al carrito
  function agregarAlCarrito(producto) {
    if (producto.stock <= 0) {
      return
    }

    setCarrito((carritoActual) => {
      const existente = carritoActual.find(
        (articulo) => articulo.sku === producto.sku
      )

      if (existente) {
        return carritoActual.map((articulo) =>
          articulo.sku === producto.sku
            ? {
                ...articulo,
                cantidad: Math.min(
                  articulo.cantidad + 1,
                  producto.stock
                )
              }
            : articulo
        )
      }

      return [
        ...carritoActual,
        {
          ...producto,
          cantidad: 1
        }
      ]
    })
  }
// Registrar la compra y actualizar el inventario
async function finalizarCompra() {
  if (carrito.length === 0) return

  try {
    const respuesta = await fetch('http://127.0.0.1:8000/compras', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        sucursal: sucursal,
        articulos: carrito.map((articulo) => ({
          sku: articulo.sku,
          cantidad: articulo.cantidad
        }))
      })
    })

    const datos = await respuesta.json()

    if (!respuesta.ok) {
      throw new Error(datos.detail || 'No se pudo registrar la compra')
    }

    alert(`Compra #${datos.id_compra} registrada. Total: $${datos.total} MXN`)

    setCarrito([])
    setRecomendaciones([])
    setMostrarCarrito(false)

    const respuestaProductos = await fetch(
      'http://127.0.0.1:8000/productos'
    )
    const productosActualizados = await respuestaProductos.json()
    setProductos(productosActualizados)

  } catch (error) {
    alert(`Error: ${error.message}`)
  }
}
  // 4. Interfaz de la aplicación
  return (
    <main
      style={{
        padding: '30px',
        fontFamily: 'Arial'
      }}
    >
      <h1>Ferretería | Catálogo de productos</h1>

      <p>
        Inventario compartido entre nuestras cinco sucursales.
      </p>

      {/* Selector de sucursal */}
      <div style={{ margin: '25px 0' }}>
        <label htmlFor="sucursal">
          <strong>Selecciona tu sucursal: </strong>
        </label>

        <select
          id="sucursal"
          value={sucursal}
          onChange={(evento) => setSucursal(evento.target.value)}
          style={{
            padding: '10px',
            borderRadius: '6px'
          }}
        >
          <option value="Cancún">Cancún</option>
          <option value="Chihuahua">Chihuahua</option>
          <option value="Ciudad de México">
            Ciudad de México
          </option>
          <option value="Monterrey">Monterrey</option>
          <option value="Mérida">Mérida</option>
        </select>
      </div>

      {/* Mensaje de error */}
      {error && (
        <p style={{ color: 'red' }}>
          {error}
        </p>
      )}
{/* Botón para abrir y cerrar el carrito */}
<button
  type="button"
  onClick={() => setMostrarCarrito(!mostrarCarrito)}
  style={{
    padding: '12px 20px',
    marginBottom: '20px',
    backgroundColor: '#166534',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer'
  }}
>
  {mostrarCarrito ? 'Cerrar carrito' : 'Ver carrito'}
  {' '}({carrito.reduce((total, articulo) => total + articulo.cantidad, 0)})
</button>

{/* Contenido del carrito */}
{mostrarCarrito && (
  <section
    style={{
      border: '2px solid #166534',
      borderRadius: '8px',
      padding: '20px',
      marginBottom: '25px'
    }}
  >
    <h2>Mi carrito — {sucursal}</h2>

    {carrito.length === 0 ? (
      <p>Tu carrito está vacío.</p>
    ) : (
      <>
        {carrito.map((articulo) => (
          <p key={articulo.sku}>
            {articulo.nombre} — Cantidad: {articulo.cantidad}
            {' '}— ${articulo.precio * articulo.cantidad} MXN
          </p>
        ))}

        <h3>
          Total: $
          {carrito.reduce(
            (total, articulo) =>
              total + articulo.precio * articulo.cantidad,
            0
          )} MXN
        </h3>
{/* Recomendaciones del modelo probabilístico */}
<div style={{ marginTop: '25px' }}>
  <h3>También te puede interesar</h3>

  {cargandoRecomendaciones && (
    <p>Buscando productos relacionados...</p>
  )}

  {errorRecomendaciones && (
    <p style={{ color: 'red' }}>{errorRecomendaciones}</p>
  )}

  {!cargandoRecomendaciones &&
    recomendaciones
      .filter(
        (producto) =>
          !carrito.some(
            (articulo) => articulo.sku === producto.sku
          )
      )
      .slice(0, 5)
      .map((producto) => (
        <div
          key={producto.sku}
          style={{
            border: '1px solid #ccc',
            borderRadius: '6px',
            padding: '12px',
            marginBottom: '10px'
          }}
        >
          <strong>{producto.nombre}</strong>

          <p>Precio: ${producto.precio} MXN</p>
          <p>Existencias: {producto.stock}</p>

          <button
            type="button"
            onClick={() => agregarAlCarrito(producto)}
          >
            Agregar al carrito
          </button>
        </div>
      ))}
</div>
{/* Botón para confirmar la compra */}
<button
  type="button"
  onClick={finalizarCompra}
  style={{
    padding: '14px 24px',
    marginTop: '20px',
    backgroundColor: '#166534',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontWeight: 'bold'
  }}
>
  Finalizar compra
</button>
      </>
    )}
  </section>
)}

      <h2>Productos disponibles</h2>

      {/* Catálogo de productos */}
      {productos.map((producto) => (
        <div
          key={producto.sku}
          style={{
            border: '1px solid #ccc',
            borderRadius: '8px',
            padding: '15px',
            marginBottom: '12px'
          }}
        >
          <h3>{producto.nombre}</h3>

          <p>SKU: {producto.sku}</p>

          <p>Categoría: {producto.categoria}</p>

          <p>Precio: ${producto.precio} MXN</p>

          <p>Existencias: {producto.stock}</p>
          <button
  type="button"
  onClick={() => agregarAlCarrito(producto)}
  disabled={producto.stock === 0}
  style={{
    padding: '10px 16px',
    backgroundColor: '#2563eb',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    marginTop: '10px'
  }}
>
  {producto.stock === 0
    ? 'Agotado'
    : 'Agregar al carrito'}
</button>
        </div>
      ))}
    </main>
  )
}

export default App
