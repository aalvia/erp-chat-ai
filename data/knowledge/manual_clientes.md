# Manual de clientes

## Objetivo

Mantener el catálogo de clientes y consultar su historial de compras.

## Funcionalidad

Puedes crear, editar, buscar, activar y desactivar clientes. El listado está en `/customers`. El alta está en `/customers/new`. El detalle y la edición están en `/customers/{id}`.

## Procedimiento

1. Abre Clientes.
2. Busca por nombre o identificación, o pulsa Nuevo cliente.
3. Guarda identificación, nombre y, si los tienes, correo, teléfono y dirección.
4. En el detalle puedes corregir datos y ver compras.

## Pasos de uso

- La identificación es única.
- Un cliente inactivo no puede usarse en una venta nueva.
- El historial muestra número, fecha y total de cada compra.
- Quien no tiene permiso para ver todas las ventas no ve el nombre del vendedor en ese historial.

## Campos relevantes

Identificación, nombre, correo, teléfono, dirección y estado.

## Validaciones

La identificación y el nombre son obligatorios. No se repite la identificación.

## Permisos

`customers.read` permite consultar. `customers.write` permite crear y editar. El administrador los tiene. VENDEDOR y CONSULTA solo consultan.

## Ejemplos

Registrar `Comercial Demo 31` con identificación `900000031`.

## Errores frecuentes

- "Ya existe un cliente con esa identificación."
- Intentar vender a un cliente inactivo.
