# API

La documentación interactiva está en `http://127.0.0.1:8000/docs`. Todas las rutas de negocio cuelgan de `/api` y, salvo el login, exigen `Authorization: Bearer <token>`.

Los errores de negocio usan `{"detail": "mensaje en español"}`.

## Autenticación

- `POST /api/auth/login` con `username` y `password`. Devuelve `access_token` y el usuario, incluidos sus permisos.
- `GET /api/auth/me` devuelve el usuario del token.

## Usuarios y roles

- `GET /api/users?search=&role=&page=&page_size=` exige `users.read`.
- `POST /api/users` exige `users.write`.
- `PUT /api/users/{id}` exige `users.write`.
- `PATCH /api/users/{id}/status` con `{"is_active": false}` exige `users.write`.
- `GET /api/roles` exige `roles.read`.

## Clientes

- `GET /api/customers?search=&include_inactive=&page=`
- `POST /api/customers`
- `GET /api/customers/{id}`
- `PUT /api/customers/{id}`
- `GET /api/customers/{id}/purchases`

Lectura: `customers.read`. Escritura: `customers.write`.

## Productos

- `GET /api/products/categories`
- `POST /api/products/categories`
- `GET /api/products?search=&category_id=`
- `POST /api/products` acepta `initial_quantity`.
- `PUT /api/products/{id}` no cambia el stock; el stock se mueve por inventario o por ventas.

## Inventario

- `GET /api/inventory`
- `GET /api/inventory/movements?product_id=`
- `POST /api/inventory/movements` con `movement_type` `ENTRADA`, `SALIDA` o `AJUSTE`.

## Ventas

- `GET /api/sales?customer_id=&status=&date_from=&date_to=`
- `POST /api/sales` confirma la venta y descuenta stock.
- `GET /api/sales/{id}`
- `POST /api/sales/{id}/cancel` anula y repone existencias.

Un usuario sin `sales.read_own` ni `sales.read_all` recibe 403 en el listado. Un vendedor solo ve las suyas.

## Tablero y configuración

- `GET /api/dashboard?date_from=&date_to=`
- `GET /api/settings`
- `PUT /api/settings` exige `settings.write`. Cambia nombre, impuesto y umbral, y aplica el umbral a los productos.

## Auditoría

- `GET /api/audit?action=` exige `audit.read`.

## Asistente

- `POST /api/assistant/chat` con `message` y `session_id`.
- `POST /api/assistant/confirm` con `token`.
- `GET /api/assistant/health`
- `POST /api/assistant/knowledge/index`
- `GET /api/assistant/knowledge/stats`

La respuesta de chat tiene `message`, `intent`, `sources`, `actions`, `data` y `available`. `actions` puede incluir `NAVIGATE` con `route` o `CONFIRM` con `confirmation_token`.
