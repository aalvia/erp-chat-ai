# Manual general del ERP

## Objetivo

Intelligent ERP es el sistema comercial de Horizonte Distribución. Permite registrar clientes, productos, inventario y ventas, y consultar indicadores reales. El asistente responde en español usando documentación y herramientas controladas.

## Funcionalidad

El sistema tiene tablero, usuarios, roles, clientes, productos, inventario, ventas, auditoría y configuración. La moneda de demostración es USD. El impuesto inicial es 0 % y se puede cambiar en Configuración.

## Procedimiento

1. Abre el navegador en la dirección local del frontend.
2. Inicia sesión con un usuario de prueba.
3. Usa el menú lateral para entrar al módulo que tu rol permita.
4. El botón IA abre ERP AI ASSISTANT.

## Pasos de uso

- El tablero está en `/`.
- Los usuarios se administran en `/admin/users`.
- Los clientes están en `/customers`.
- Los productos están en `/products`.
- El inventario está en `/inventory`.
- Las ventas están en `/sales`.
- La auditoría está en `/audit`.
- La configuración está en `/settings`.

## Campos relevantes

No hay un formulario único. Cada módulo valida sus propios campos. Las ventas guardan subtotal, tasa de impuesto, valor del impuesto y total.

## Validaciones

El backend comprueba permisos, datos obligatorios y existencias. El asistente no puede inventar cifras ni ejecutar SQL libre.

## Permisos

ADMINISTRADOR tiene acceso completo. VENDEDOR consulta clientes, productos e inventario, registra ventas y ve las suyas. CONSULTA lee clientes, productos, inventario e indicadores, sin listar las ventas de todos los vendedores.

## Ejemplos

Un administrador entra con el usuario `admin` y revisa el tablero. Un vendedor entra con `vendedor.ana` y registra una venta.

## Errores frecuentes

- Credenciales incorrectas: el sistema responde que el usuario o la contraseña no son válidos.
- Permiso insuficiente: la pantalla muestra que no puedes ver ese módulo.
- Ollama apagado: el ERP sigue funcionando y el asistente explica que no está disponible.
