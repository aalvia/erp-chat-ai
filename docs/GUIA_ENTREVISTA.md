# Guía de entrevista

## ¿Por qué Ollama?

Porque el ejercicio pide una solución local y gratuita. Ollama corre el modelo en la máquina, sin enviar clientes ni ventas a un proveedor. El ERP no depende de una cuota ni de una clave.

## ¿Por qué Qwen 2.5?

La familia entiende español y la variante instalada anuncia function calling. Se eligió 1.5B, y no 7B, después de medir el equipo de referencia: 8 GB de RAM y sin tarjeta gráfica. 7B necesita alrededor de 6 GB solo para el modelo. 1.5B cabe, ya estaba descargado y Ollama 0.40 confirma la capacidad `tools`. El nombre del modelo está en una variable de entorno.

## ¿Qué es RAG?

Es buscar fragmentos de los manuales del ERP y dárselos al modelo antes de que explique un procedimiento. Así la explicación sale de `data/knowledge/` y no de la memoria general del modelo. No se usa para contestar cuánto se vendió.

## ¿Qué es function calling?

Es pedirle al modelo que solicite una función del programa. Ollama devuelve `tool_calls`. Python valida los argumentos, ejecuta un servicio y devuelve el JSON. El modelo redacta encima de ese JSON.

## ¿Cómo se integra la IA con el ERP?

El asistente no tiene su propia base. Llama a los mismos servicios que las pantallas: ventas, inventario, clientes, usuarios y tablero. Por eso un vendedor ve en el chat el mismo alcance que en la pantalla de ventas.

## ¿Cómo se evitan las alucinaciones?

Las cifras no se aceptan si no están en el resultado de la herramienta. Si el modelo agrega un número ajeno, la frase se sustituye por una plantilla alimentada solo con ese resultado. Las rutas salen del catálogo. Si la pregunta es de otro dominio, como la temperatura en Marte, la intención es `UNKNOWN` y no se consulta una herramienta de negocio. Si no hay llamada de herramienta, no se inventa el dato.

## ¿Cómo se controlan los permisos?

El JWT identifica al usuario. Cada herramienta declara un permiso o aplica una regla de alcance. El modelo no puede ampliarlo. Un usuario de consulta que pide las ventas de todos los vendedores recibe un rechazo y una línea de auditoría.

## ¿Cómo se evita el SQL peligroso?

No hay una herramienta que reciba una sentencia. Las consultas están escritas en SQLAlchemy con filtros enlazados. "Elimina todos los usuarios" no coincide con ninguna función y una regla previa lo bloquea.

## ¿Cómo se protege la información?

Contraseñas con Argon2, sin devolver el hash. La auditoría guarda parámetros ya depurados. El historial de chat de la sesión no incluye el hash ni el token. Un vendedor no recibe las ventas de otro. Las altas del asistente exigen un botón de confirmación del mismo usuario.

## ¿Cómo se escala?

Primero se separaría el índice y el modelo del proceso de la API, manteniendo el mismo contrato de herramientas. PostgreSQL ya admite más datos con índices en fechas y clientes. El cuello de botella actual es el modelo en CPU: en un servidor con más RAM se cambia `OLLAMA_MODEL` a una variante mayor. La API puede ponerse detrás de varios workers; la memoria de conversación, hoy en el proceso, pasaría a un almacén compartido si hay más de una instancia.

## ¿Cómo se mide la precisión?

Con preguntas fijas contra la base de prueba: la cantidad de octubre que devuelve la herramienta debe ser igual a la consulta SQL; la ruta de "crear usuario" debe ser `/admin/users/new`; una pregunta fuera del dominio no debe traer ventas. Esas comprobaciones están en `backend/tests`.

## ¿Cómo se mide el ROI?

Se contaría el tiempo que un usuario tarda en llegar a una pantalla o a un total con el menú, y el tiempo con el asistente, más los errores de datos evitados porque la cifra sale de la base. En una empresa real se mediría también cuántas consultas repetitivas al área de sistemas desaparecen.

## ¿Qué harías para llevarlo a producción?

Secreto JWT propio, HTTPS, copias de PostgreSQL, usuario de base con permisos mínimos, rotación de tokens, observabilidad de las herramientas y una evaluación continua de las preguntas reales. El modelo seguiría siendo intercambiable. No expondría Ollama a internet sin una red privada.

## ¿Qué diferencia hay entre un chatbot y un agente?

Un chatbot responde con texto. Este asistente elige una herramienta, el programa actúa sobre el ERP y el texto se apoya en el resultado. Puede encadenar documentación y navegación. No es un agente libre: no escribe código, no abre SQL y no confirma solo las operaciones que cambian datos.

## ¿Qué ocurre si Ollama deja de responder?

`GET /api/assistant/health` queda en `unavailable`. El chat muestra que el asistente no está disponible y que el ERP sigue funcionando. Login, ventas e inventario no pasan por Ollama.

## ¿Cómo se controlan los costos?

Al correr en local, el costo es electricidad y hardware, no una tarifa por token. El contexto corto y un modelo de 1.5B mantienen ese costo bajo. Si más adelante se usara un modelo de pago, el mismo límite de herramientas y de rondas evitaría llamadas innecesarias.

## ¿Qué procesos automatizarías primero?

Los que ya están acotados y se consultan todos los días: stock bajo, ventas del periodo, ficha de un cliente y "dónde registro esto". Dejaría para después los procesos que mueven dinero o permisos, y siempre con confirmación humana, como ya ocurre con las altas.
