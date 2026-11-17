# Manual del tablero

## Objetivo

Mostrar indicadores calculados en PostgreSQL, no cifras fijas de una presentación.

## Funcionalidad

La pantalla está en `/`. Muestra importe de ventas confirmadas, cantidad de ventas, productos activos, clientes activos, productos con stock en el umbral o por debajo, evolución mensual y los cinco productos con más unidades.

## Procedimiento

1. Inicia sesión.
2. Abre Tablero.
3. Lee el alcance: "Toda la empresa" o "Tus ventas".
4. Revisa la gráfica de evolución y la tabla de productos.

## Pasos de uso

- ADMINISTRADOR y CONSULTA ven los totales de la empresa.
- El administrador también ve el desglose por vendedor en la API. La pantalla principal muestra totales y productos.
- VENDEDOR ve solo sus ventas confirmadas. Los conteos de productos y clientes siguen siendo del catálogo.
- Las ventas anuladas no entran en los totales.

## Campos relevantes

Total de ventas, cantidad, productos, clientes, bajo inventario, mes, importe y unidades.

## Validaciones

Los valores salen de consultas agrupadas. El asistente, cuando pide el tablero, usa la misma consulta y no calcula por su cuenta.

## Permisos

Se requiere `dashboard.read`. Los tres roles lo tienen, con el alcance descrito.

## Ejemplos

Después de cargar la demostración, el tablero del administrador refleja las ventas generadas entre enero y noviembre de 2026.

## Errores frecuentes

- Un vendedor compara su tablero con el del administrador y ve un importe menor: es el alcance de sus propias ventas.
