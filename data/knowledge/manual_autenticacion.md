# Manual de autenticación

## Objetivo

Identificar a la persona que usa el ERP y mantener una sesión firmada.

## Funcionalidad

La pantalla de ingreso está en `/login`. El backend entrega un JWT. El navegador lo guarda en la sesión de la pestaña. Cada solicitud protegida envía el token. Al salir, el token se borra.

## Procedimiento

1. Escribe el usuario y la contraseña.
2. Pulsa Ingresar.
3. El sistema abre el tablero si las credenciales y el usuario activo son válidos.
4. Pulsa Salir para cerrar la sesión en este navegador.

## Pasos de uso

- La contraseña de los usuarios de demostración locales es `Demo123!`.
- El usuario `admin` tiene rol ADMINISTRADOR.
- Un usuario inactivo no puede entrar.
- Cambiar la contraseña o desactivar al usuario invalida los tokens anteriores.

## Campos relevantes

Usuario y contraseña. La contraseña debe tener al menos 8 caracteres, una letra y un número. No se guarda en texto plano: se almacena con un hash Argon2.

## Validaciones

El inicio de sesión rechaza usuario inexistente, contraseña incorrecta y usuario inactivo con el mismo mensaje, para no revelar cuál falló.

## Permisos

Cualquier usuario activo puede iniciar sesión. Las pantallas posteriores dependen del rol.

## Ejemplos

`vendedor.ana` entra y ve ventas, clientes, productos e inventario. No ve la administración de usuarios.

## Errores frecuentes

- Contraseña vacía o corta: el formulario no envía la solicitud.
- Token vencido o usuario desactivado: la aplicación vuelve a la pantalla de ingreso.
