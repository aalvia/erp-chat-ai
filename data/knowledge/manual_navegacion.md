# Manual de navegación

## Objetivo

Indicar las rutas reales del ERP. El asistente solo puede enlazar pantallas de este catálogo.

## Funcionalidad

El menú lateral muestra únicamente los módulos del rol. El asistente usa el catálogo interno y devuelve un botón solo si la ruta existe y el usuario tiene permiso.

## Procedimiento

1. Mira el menú.
2. En pantallas estrechas, pulsa Menú para abrir el lateral.
3. Si preguntas "¿dónde...?" o "llévame...", el asistente propone un botón.
4. El botón usa el enrutador de la aplicación. No se ejecuta HTML del modelo.

## Pasos de uso

- Tablero: `/`
- Usuarios: `/admin/users`
- Nuevo usuario: `/admin/users/new`
- Roles: `/admin/roles`
- Clientes: `/customers`
- Nuevo cliente: `/customers/new`
- Productos: `/products`
- Nuevo producto: `/products/new`
- Inventario: `/inventory`
- Historial de inventario: `/inventory/movements`
- Ventas: `/sales`
- Nueva venta: `/sales/new`
- Auditoría: `/audit`
- Configuración: `/settings`

## Campos relevantes

Módulo, nombre de la pantalla, descripción, ruta y permiso requerido.

## Validaciones

Si el rol no tiene el permiso, el asistente explica la restricción y no ofrece el enlace. No inventa direcciones.

## Permisos

Cada ruta del menú está filtrada por permiso. El detalle de una venta o un cliente solo se abre desde un registro existente.

## Ejemplos

"¿Dónde puedo crear un usuario?" responde Administración > Usuarios > Nuevo usuario y enlaza `/admin/users/new` si eres administrador.

"Llévame al módulo de productos" enlaza `/products`.

## Errores frecuentes

- Pedir una pantalla que no existe: el asistente dice que no la encontró.
- Pedir el alta de usuarios siendo vendedor: no hay enlace porque falta `users.write`.
