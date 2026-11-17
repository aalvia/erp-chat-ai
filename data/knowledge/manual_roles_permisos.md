# Manual de roles y permisos

## Objetivo

Limitar lo que cada persona puede ver y modificar. La restricción se aplica en el backend.

## Funcionalidad

Hay tres roles. La pantalla está en `/admin/roles`.

## Procedimiento

1. Entra como administrador.
2. Abre Roles.
3. Revisa los permisos de ADMINISTRADOR, VENDEDOR y CONSULTA.
4. Asigna el rol al crear o editar un usuario.

## Pasos de uso

- ADMINISTRADOR accede a todo, incluida auditoría, configuración y usuarios.
- VENDEDOR consulta clientes, productos e inventario, crea ventas y consulta sus ventas.
- CONSULTA lee clientes, productos, inventario y el tablero de la empresa.
- CONSULTA no puede listar las ventas de todos los vendedores.
- VENDEDOR no puede ver las ventas de otro vendedor.

## Campos relevantes

Código del rol, nombre y lista de permisos. Los códigos internos son ADMIN, SELLER y READER.

## Validaciones

El modelo de IA no concede permisos. Cada herramienta comprueba el permiso del usuario autenticado.

## Permisos

Ver la pantalla exige `roles.read`, que solo tiene el administrador.

## Ejemplos

Si `consulta.sofia` pide las ventas de todos los vendedores, el asistente rechaza la consulta.

## Errores frecuentes

- Entrar a `/admin/users` con un vendedor muestra que no hay permiso.
- Pedir al asistente una operación de otro rol no cambia el rol del usuario.
