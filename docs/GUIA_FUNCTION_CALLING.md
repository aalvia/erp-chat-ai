# Guía de function calling

## Qué es

Function calling es la capacidad del modelo de pedir que el programa ejecute una función, en lugar de responder él con un dato que no tiene. Ollama devuelve esa petición en `message.tool_calls`. Este proyecto no interpreta un JSON escrito en el texto como si fuera una herramienta: usa el campo `tool_calls` de la API.

## Qué es una tool

Una herramienta es una función Python con nombre, descripción y argumentos. El registro está en `backend/app/ai/tool_registry.py`. El modelo solo recibe las herramientas de la lista. No existe una herramienta de SQL.

Herramientas de consulta: `consultar_ventas`, `consultar_producto`, `consultar_inventario`, `buscar_cliente`, `consultar_clientes`, `consultar_productos`, `consultar_usuarios`, `consultar_top_productos`, `consultar_top_clientes`, `consultar_dashboard` y `consultar_historial_compras`.

Navegación y manuales: `buscar_funcionalidad_erp` y `consultar_documentacion`.

Operaciones, siempre con confirmación: `crear_cliente`, `crear_producto`, `crear_venta` y `crear_usuario`.

## Cómo decide Qwen

El modelo de 1.5B confunde a veces una pregunta de navegación con una orden de alta. Por eso, antes de clasificar, Python aparta tres casos evidentes: una pregunta con "dónde" o "llévame" va a navegación; una con "cómo" y un verbo de procedimiento va al manual; una pregunta de otro dominio, como Marte o el clima, no llama herramientas. El resto lo clasifica Qwen. Después el orquestador hace dos pasos, porque ese modelo se confunde si ve demasiadas herramientas a la vez.

1. Una respuesta JSON elige la intención y el nombre de la herramienta. Las intenciones son `NAVIGATION`, `HOW_TO`, `BUSINESS_QUERY`, `ANALYTICS`, `ACTION`, `GENERAL` y `UNKNOWN`.
2. Una segunda llamada a `/api/chat` incluye un solo esquema. El sistema le dice el rango de fechas cuando la pregunta menciona octubre, este año, este mes o el último trimestre. Esas fechas las calcula Python a partir de la fecha de hoy y se las dicta al modelo. El modelo igual debe devolver `tool_calls`.

Si no hay llamada, se reintenta una vez. Si sigue sin haberla, la respuesta dice que no se consultaron datos. No se inventa el total.

## Esquemas y ejecución

Cada argumento es un modelo Pydantic. `parse_arguments` rechaza campos de más o tipos imposibles. `tool_executor.execute` comprueba el permiso, llama al servicio y registra la auditoría sin contraseñas ni tokens.

Ejemplo de esquema abreviado de ventas:

```json
{
  "name": "consultar_ventas",
  "parameters": {
    "fecha_inicio": "YYYY-MM-DD",
    "fecha_fin": "YYYY-MM-DD",
    "producto": "opcional",
    "cliente": "opcional",
    "usuario_responsable": "opcional"
  }
}
```

## Ejemplo de octubre

Pregunta: "¿Cuántas ventas tuvimos durante octubre?"

Python calcula, con la fecha actual en noviembre de 2026, `fecha_inicio=2026-10-01` y `fecha_fin=2026-10-31`, y se lo indica al modelo. Qwen devuelve una llamada a `consultar_ventas` con esas fechas. SQLAlchemy filtra `status = CONFIRMADA` y ese rango. La frase final usa la cantidad y el importe devueltos. Esos números cambian con la base; no hay un total de demostración escrito en el código.

Si la pregunta nombra un producto, el importe sale de las líneas de ese producto, no de la factura completa.

## Errores

- Ollama caído: mensaje claro y el ERP sigue.
- Argumentos inválidos: el usuario ve el error de validación.
- Permiso insuficiente: no se ejecuta la consulta y queda auditoría `DENIED`.
- Herramienta desconocida, por ejemplo `ejecutar_sql`: se rechaza.

## Permisos

`consultar_usuarios` exige `users.read`. Un vendedor o un usuario de consulta no lo pasa.

`consultar_ventas` con otro `usuario_responsable` exige `sales.read_all`. Además, si el texto pide las ventas de todos los vendedores y el rol no tiene ese permiso, el orquestador corta antes de llamar al modelo.

VENDEDOR, sin ese filtro, solo suma sus ventas. CONSULTA puede ver totales de empresa en el tablero, pero no el listado por vendedor.

## Por qué no hay SQL del modelo

El modelo elige un nombre de herramienta y unos argumentos tipados. La sentencia SQL está escrita en Python, con parámetros de SQLAlchemy. Aunque la pregunta diga "borra la tabla", no hay una función que ejecute ese texto. El borrado masivo de usuarios se rechaza por una regla previa y porque no existe esa herramienta.

## Confirmación

`crear_cliente` y las demás altas guardan la petición en memoria, devuelven un token y esperan `POST /api/assistant/confirm`. El token caduca a los diez minutos y debe pertenecer al mismo usuario. Al confirmar se vuelven a comprobar los permisos.
