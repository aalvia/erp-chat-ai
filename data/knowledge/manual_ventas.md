# Manual de ventas

## Objetivo

Registrar una venta confirmada y descontar el inventario en la misma transacción de base de datos.

## Funcionalidad

El historial está en `/sales`. La nueva venta está en `/sales/new`. El detalle está en `/sales/{id}`. Al confirmar, el estado queda CONFIRMADA. Se puede anular una venta confirmada: el estado pasa a ANULADA y el stock regresa.

## Procedimiento

1. Abre Ventas y pulsa Nueva venta.
2. Elige el cliente activo y la fecha.
3. Agrega uno o más productos e indica la cantidad.
4. Revisa el total estimado. El precio sale del catálogo, no de un valor escrito a mano.
5. Pulsa Confirmar venta.
6. El detalle muestra líneas, subtotal, impuesto y total.

## Pasos de uso

- Cada línea usa el precio de venta vigente.
- El impuesto es el porcentaje configurado en ese momento. Con el valor inicial 0, el impuesto es cero y el total es igual al subtotal.
- El número de venta tiene la forma `V-año-000000`.
- No se repite el mismo producto en dos líneas: suma la cantidad.
- Si no hay existencias suficientes, la venta completa se rechaza y el stock no cambia.
- VENDEDOR ve y anula solo sus ventas. ADMINISTRADOR ve todas.

## Campos relevantes

Cliente, fecha, notas, producto y cantidad. El sistema calcula precio unitario, subtotal de línea, subtotal, tasa, impuesto y total.

## Validaciones

Cliente activo, producto activo, cantidad mayor que cero y existencia suficiente. Todo ocurre en una transacción.

## Permisos

`sales.create` registra. `sales.read_own` lista las ventas propias. `sales.read_all` lista las de todos los vendedores. `sales.cancel` anula. CONSULTA no tiene estos permisos de ventas.

## Ejemplos

Vender 2 unidades de `OF-001` al cliente Comercial Demo 01. Si había 5 unidades, quedan 3 y aparece un movimiento VENTA.

## Errores frecuentes

- "Existencias insuficientes."
- "El cliente no existe o está inactivo."
- "No tienes permiso para consultar las ventas de otros vendedores."
