# Preguntas frecuentes

## Objetivo

Aclarar los límites del ERP y del asistente con lo que el sistema hace de verdad.

## Funcionalidad

El asistente combina tres vías: manuales para explicar procedimientos, herramientas para consultar PostgreSQL y un catálogo para navegar. No usa los manuales para inventar ventas ni el modelo para inventar rutas.

## Procedimiento

Formula la pregunta en español. Espera la respuesta. Si hay un botón, puedes pulsarlo. Si la operación cambia datos, confírmala.

## Pasos de uso

- "¿Cuántas ventas tuvimos durante octubre?" consulta las ventas confirmadas de ese mes.
- "¿Cuál fue el producto más vendido?" agrupa las líneas de venta por producto.
- "¿Qué productos tienen menos de 10 unidades?" lee el inventario.
- "¿Qué usuarios tienen permisos de administrador?" exige permiso para ver usuarios.
- "¿Cuál fue la temperatura en Marte?" queda fuera del ERP.

## Campos relevantes

El asistente devuelve un mensaje, la intención, fuentes, acciones y datos. El navegador muestra texto, botones y tablas. No ejecuta HTML ni JavaScript generado por el modelo.

## Validaciones

Las cifras del mensaje se contrastan con el resultado de la herramienta. Si el modelo agrega un número que no está en ese resultado, se usa una frase construida con los datos reales.

## Permisos

El asistente usa la sesión de quien está conectado. Un vendedor no obtiene las ventas de los demás. Un usuario de consulta no administra usuarios.

## Ejemplos

Si Ollama está apagado, verás: "El asistente no está disponible porque Ollama no responde o el modelo configurado no está cargado. El resto del ERP sigue funcionando."

## Errores frecuentes

- Preguntar por un periodo sin datos: la cantidad puede ser cero y eso es una respuesta real.
- Pedir ciencia, clima o temas ajenos a la empresa: el asistente indica que no corresponde a este ERP.
