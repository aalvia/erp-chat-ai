# Manual de productos

## Objetivo

Administrar el catálogo que se vende: categoría, SKU, precio, costo y estado.

## Funcionalidad

El listado está en `/products`. El alta está en `/products/new`. La edición está en `/products/{id}`. Las categorías se eligen al crear el producto. En la demostración existen Oficina, Tecnología, Hogar, Ferretería y Abarrotes.

## Procedimiento

1. Abre Productos.
2. Busca por nombre o SKU.
3. Pulsa Nuevo producto o Editar.
4. Indica SKU, nombre, categoría, precio de venta y costo.
5. En un alta puedes indicar la existencia inicial. Esa cantidad genera una entrada de inventario.

## Pasos de uso

- El SKU se guarda en mayúsculas y no se repite.
- El precio debe ser mayor que cero.
- El costo no puede superar el precio de venta.
- El listado muestra la existencia y marca en rojo el stock en el umbral o por debajo.

## Campos relevantes

SKU, nombre, descripción, categoría, precio, costo, estado y existencia inicial.

## Validaciones

Categoría existente, SKU único, precio positivo y costo menor o igual al precio.

## Permisos

`products.read` consulta. `products.write` crea y edita. Solo el administrador escribe productos en la configuración inicial de roles.

## Ejemplos

Crear el SKU `OF-009`, nombre "Clips caja", categoría Oficina, precio 2.50 y costo 1.00.

## Errores frecuentes

- "Ya existe un producto con ese SKU."
- "El costo no puede ser mayor que el precio de venta."
- "La categoría no existe."
