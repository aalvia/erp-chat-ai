# Manual de usuarios

## Objetivo

Administrar las personas que entran al ERP.

## Funcionalidad

Un administrador puede listar, crear, editar, activar y desactivar usuarios, y asignarles un rol. La ruta del listado es `/admin/users`. La ruta para crear es `/admin/users/new`. La edición es `/admin/users/{id}`.

## Procedimiento

1. Entra como administrador.
2. Abre Administración, Usuarios.
3. Pulsa Nuevo usuario o Editar en una fila.
4. Completa los datos y guarda.
5. Para bloquear el acceso, usa Desactivar.

## Pasos de uso

- Busca por nombre, usuario o correo.
- El nombre de usuario se guarda en minúsculas.
- Al crear, la contraseña es obligatoria.
- Al editar, deja la contraseña vacía si no quieres cambiarla.
- No puedes desactivar tu propio usuario.

## Campos relevantes

Usuario, nombre, correo, contraseña, rol y estado activo.

## Validaciones

No se permiten usuarios ni correos duplicados. La contraseña nueva debe tener 8 caracteres, una letra y un número. El rol debe existir.

## Permisos

Se requiere `users.read` para ver y `users.write` para crear o editar. VENDEDOR y CONSULTA no tienen esos permisos.

## Ejemplos

Crear `vendedor.nuevo` con correo `nuevo@horizonte.demo`, contraseña `Demo123!` y rol VENDEDOR.

## Errores frecuentes

- "Ya existe un usuario con ese nombre."
- "No puedes desactivar tu propio usuario."
- El asistente no puede borrar todos los usuarios: esa operación no existe.
