# Manual de procedimientos

## Objetivo

Describir los procedimientos que sí están implementados.

## Funcionalidad

Los procedimientos principales son iniciar sesión, crear un usuario, registrar un cliente, crear un producto, mover inventario, registrar una venta y consultar el tablero.

## Procedimiento

### Registrar una venta

1. Entra con un usuario VENDEDOR o ADMINISTRADOR.
2. Abre Ventas > Nueva venta, ruta `/sales/new`.
3. Selecciona un cliente activo.
4. Agrega productos y cantidades. El sistema muestra el stock y el precio.
5. Confirma. Si el stock alcanza, la venta queda CONFIRMADA y el inventario baja.
6. Abre el número de venta para ver el detalle o anularla.

### Crear un usuario

1. Entra como administrador.
2. Abre `/admin/users/new`.
3. Escribe usuario, nombre, correo, contraseña y rol.
4. Guarda. Si el usuario o el correo ya existen, la operación se rechaza.

## Pasos de uso

El asistente puede preparar un alta, pero no la graba hasta que pulses Confirmar operación. Esa confirmación vence a los 10 minutos y solo vale para el mismo usuario.

## Campos relevantes

Dependen del procedimiento. Una venta necesita cliente, fecha y líneas. Un usuario necesita usuario, correo, nombre, contraseña y rol.

## Validaciones

Cada procedimiento revalida permisos en el servidor. Confirmar en el asistente no omite esas reglas.

## Permisos

Vender exige `sales.create`. Crear usuarios exige `users.write`. Crear clientes exige `customers.write`. Crear productos exige `products.write`.

## Ejemplos

"¿Cómo registro una venta?" debe explicar estos pasos y ofrecer el enlace a `/sales/new` si el rol puede vender.

## Errores frecuentes

- Confirmar una venta sin líneas.
- Pedir "elimina todos los usuarios": no hay borrado masivo.
