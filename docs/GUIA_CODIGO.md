# Guía del código

Las rutas parten de `G:\ERP CHAT`. El backend se ejecuta con el directorio de trabajo `backend`, para que Alembic y Uvicorn encuentren el paquete `app`.

## Configuración y arranque

`backend/app/config.py` define `Settings`. Lee `backend/.env`. Expone la URL de PostgreSQL, el secreto JWT, los modelos de Ollama, el contexto de 2048 tokens y las carpetas `data/knowledge` y `data/chroma_db`. `get_settings()` está en caché.

`backend/app/main.py` crea la aplicación, el CORS y el manejador de `AppError`. Incluye los routers bajo `/api`.

`backend/app/database/session.py` crea el engine y `get_db()`. `base.py` es la base declarativa de SQLAlchemy.

## Modelo de datos

`backend/app/models/entities.py` declara las tablas: roles, permisos, usuarios, clientes, categorías, productos, inventario, movimientos, ventas, detalle, auditoría y configuración. `models/__init__.py` las exporta para que Alembic las vea.

## Seguridad

`core/permissions.py` lista los códigos y qué rol los recibe. `core/security.py` tiene `hash_password`, `verify_password`, `create_access_token` y `decode_access_token`. El token lleva `sub`, `tv` y `exp`.

`core/dependencies.py`: `get_current_user` carga el usuario con su rol y permisos. `require_permissions` corta con 403. `has_permission` lo reutilizan ventas y el asistente.

`core/errors.py`: `AppError(message, status_code)`.

## Esquemas

`schemas/dto.py` contiene los modelos de entrada y salida: login, usuarios, clientes, productos, movimientos, ventas, tablero, ajustes y la respuesta del asistente. `Page` envuelve listados con `items`, `total`, `page` y `page_size`.

## Servicios

`services/user_service.py` autentica, crea, edita y activa usuarios. Rechaza duplicados y la autodesactivación.

`services/customer_service.py` y `services/product_service.py` hacen el alta y la edición. Al crear un producto también crean la fila de inventario y, si hay cantidad inicial, un movimiento ENTRADA.

`services/inventory_service.py`: `register_movement` bloquea la fila y aplica entrada, salida o ajuste.

`services/sales_service.py`: `create_sale` bloquea el inventario, rechaza stock insuficiente, graba la venta, el detalle y el movimiento, y confirma en una sola transacción. `cancel_sale` repone el stock. `scoped_sales` limita al vendedor a sus documentos.

`services/dashboard_service.py`: `build_dashboard` agrupa ventas confirmadas. Un vendedor queda filtrado por su `user_id`. Consulta ve la empresa y no el desglose por vendedor.

`services/settings_service.py` lee o actualiza la fila `company_settings` de id 1.

`services/audit_service.py` escribe el registro y oculta claves como `password` y `token`.

`services/mappers.py` convierte filas a respuestas JSON, con importes en número de dos decimales.

## Repositorios

`repositories/users.py`, `customers.py` y `products.py` arman las consultas de listado y búsqueda. El resto de las consultas vive junto a la regla que las necesita, en el servicio correspondiente.

## Rutas

Cada archivo de `api/routes` traduce HTTP a un servicio. `auth.py` entrega el JWT. `assistant.py` llama al orquestador, a la confirmación y al índice.

## Asistente

`ai/ollama_service.py`: `health`, `chat` y `embed`. `chat` envía `tools` cuando corresponde.

`ai/ai_orchestrator.py`: `handle_message` es el flujo completo. `period_hint` traduce "octubre" o "último trimestre" a fechas. `is_bulk_destructive` y `asks_all_sellers` son las dos cortapisas previas. `confirm_action` ejecuta un alta ya confirmada.

`ai/tool_registry.py` define los esquemas. `ai/tool_executor.py` los ejecuta. Las altas sensibles pasan por `_stage` y `confirm`.

`ai/navigation_service.py` es el catálogo. `search_features(consulta, usuario)` devuelve módulo, descripción, ruta real y si el permiso alcanza.

`ai/rag_service.py`: `index_knowledge`, `stats` y `retrieve`. `ai/embedding_service.py` llama a Ollama. `ai/memory.py` guarda hasta ocho turnos por usuario y sesión.

## Datos de demostración

`database/seed.py`: `seed_reference` crea roles, permisos y usuarios. `seed_demo` vacía las tablas y carga el catálogo y 130 ventas con una semilla aleatoria fija. `scripts/seed_database.py` lo dispara. `scripts/index_knowledge.py` indexa los manuales.

## Frontend

`src/services/api.ts` añade el token y convierte `detail` en un error legible. `contexts/AuthContext.tsx` guarda la sesión. `App.tsx` declara las mismas rutas que el catálogo del asistente. `components/chat/AssistantPanel.tsx` pinta la respuesta y solo navega a rutas conocidas. Las páginas de `src/pages` cubren el tablero, usuarios, roles, clientes, productos, inventario, ventas, auditoría y configuración.

## Pruebas

`tests/conftest.py` apunta a `intelligent_erp_test`, crea el esquema y deja tres usuarios. `test_erp.py` cubre login, permisos, ventas e inventario. `test_tools.py` cubre octubre, el producto más vendido, el stock bajo, la ruta `/admin/users/new` y los rechazos de seguridad.
