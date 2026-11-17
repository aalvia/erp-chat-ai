# Manual de inventario

## Objetivo

Conocer las existencias y registrar entradas, salidas y ajustes con su origen.

## Funcionalidad

Las existencias están en `/inventory`. El historial está en `/inventory/movements`. Cada producto tiene una fila de inventario. El umbral de stock bajo nace en 10 unidades y se puede cambiar en Configuración.

## Procedimiento

1. Abre Inventario.
2. Revisa la columna Existencia. Si está en el umbral o por debajo, se muestra como alerta.
3. Si tienes permiso de escritura, registra ENTRADA, SALIDA o AJUSTE.
4. Abre el historial para ver el antes, el después y el origen.

## Pasos de uso

- ENTRADA suma la cantidad.
- SALIDA resta la cantidad y falla si no hay suficiente.
- AJUSTE deja la existencia en el valor indicado.
- Una venta confirmada crea un movimiento VENTA y descuenta stock.
- Anular una venta crea una ENTRADA con origen ANULACION y devuelve las unidades.

## Campos relevantes

Producto, tipo, cantidad y nota. El historial guarda cantidad anterior, cantidad nueva, tipo de referencia y usuario.

## Validaciones

No se permiten existencias negativas. Una salida mayor que el disponible se rechaza y no cambia el stock.

## Permisos

`inventory.read` consulta existencias e historial. `inventory.write` registra movimientos manuales. VENDEDOR y CONSULTA leen. El administrador escribe.

## Ejemplos

Preguntar al asistente qué productos tienen menos de 10 unidades. La respuesta sale de la tabla de inventario, no de una cifra inventada.

## Errores frecuentes

- "Existencias insuficientes."
- Tipo distinto de ENTRADA, SALIDA o AJUSTE.
