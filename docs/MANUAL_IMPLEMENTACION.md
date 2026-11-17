# Manual de implementación

Esta guía reconstruye Intelligent ERP en Windows con CMD. Los comandos usan la carpeta `G:\ERP CHAT` y el Python 3.12 que ya está instalado. No actualices Python ni Node como parte de estos pasos.

## 1. Verificación del entorno

Objetivo: saber qué hay instalado antes de crear nada.

Comandos:

```bat
python --version
py --list
where python
node --version
npm --version
"C:\Program Files\PostgreSQL\18\bin\psql.exe" --version
ollama --version
ollama list
```

Resultado esperado en la máquina de desarrollo: Python 3.12.10, Node v22.23.2, npm 10.9.8, PostgreSQL 18.4 y Ollama 0.40.16 con `qwen2.5:1.5b` y `nomic-embed-text`.

Error frecuente: `psql` no se reconoce. El servicio puede estar corriendo aunque el ejecutable no esté en el PATH. Usa la ruta de `C:\Program Files\PostgreSQL\18\bin`.

## 2. Preparación de Python

Objetivo: un entorno aislado con las librerías ya probadas en 3.12.

Archivos: `backend\requirements.txt`, `backend\.venv`.

```bat
cd /d "G:\ERP CHAT\backend"
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Resultado: FastAPI, SQLAlchemy 2.1, Alembic, Pydantic 2, psycopg 3, PyJWT, pwdlib, httpx, ChromaDB y pytest.

Error frecuente: instalar con otro `python` distinto de 3.12. `where python` debe señalar `C:\Program Files\Python312\python.exe` o el del entorno virtual.

## 3. Preparación de Node

Objetivo: el frontend React.

```bat
cd /d "G:\ERP CHAT\frontend"
npm install
```

El proyecto ya incluye React, React Router y Recharts. No cambies la versión global de npm.

Error frecuente: ejecutar `npm install` en la raíz. Hay que hacerlo dentro de `frontend`.

## 4. PostgreSQL

Objetivo: dos bases, la de demostración y la de pruebas.

```bat
set PGPASSWORD=postgres
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -w -U postgres -h 127.0.0.1 -d postgres -c "CREATE DATABASE intelligent_erp;"
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -w -U postgres -h 127.0.0.1 -d postgres -c "CREATE DATABASE intelligent_erp_test;"
```

Si la contraseña local no es `postgres`, usa la tuya y escríbela solo en `backend\.env`.

Error frecuente: `no password supplied`. La autenticación de este servidor pide contraseña; `-w` evita que el comando se quede esperando.

## 5. FastAPI

Objetivo: dejar la configuración y arrancar la API.

Archivos: `backend\.env`, `backend\app\main.py`, `backend\app\config.py`.

```bat
cd /d "G:\ERP CHAT\backend"
copy .env.example .env
```

Ajusta `DATABASE_URL`. Luego:

```bat
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Resultado: http://127.0.0.1:8000/docs abre Swagger. Sin tablas todavía, el login fallará: es lo esperado antes de migrar.

## 6. SQLAlchemy

Objetivo: las clases de `backend\app\models\entities.py` representan las tablas. `session.py` abre la conexión con el dialecto `postgresql+psycopg`.

No se usa SQL escrito por el modelo. Los servicios usan `select` y parámetros.

## 7. Alembic

Objetivo: crear las tablas con una migración reproducible.

Archivos: `backend\alembic.ini`, `backend\migrations\env.py` y `backend\migrations\versions`.

```bat
cd /d "G:\ERP CHAT\backend"
.venv\Scripts\python.exe -m alembic upgrade head
```

`env.py` lee la URL desde `.env` e importa los modelos. La revisión inicial se generó con `alembic revision --autogenerate -m "initial schema"`.

Error frecuente: ejecutar Alembic fuera de `backend`. El paquete `app` no se encuentra.

## 8. Autenticación

Objetivo: login con JWT y contraseñas con Argon2.

Archivos: `core\security.py`, `core\dependencies.py`, `api\routes\auth.py`.

Después del seed, `POST /api/auth/login` con `admin` y `Demo123!` devuelve el token. `GET /api/auth/me` lo usa en la cabecera `Authorization`.

Error frecuente: guardar la contraseña en claro. El seed llama a `hash_password` y la columna es `password_hash`.

## 9. Roles

Objetivo: tres roles y permisos en base, no solo en el menú.

Archivo: `core\permissions.py` y `database\seed.py`.

ADMIN recibe todos los códigos. SELLER recibe lectura comercial, crear ventas y ver las propias. READER recibe lectura de catálogo y tablero. La pantalla `/admin/roles` los muestra.

## 10. Módulos empresariales

Objetivo: clientes, productos, inventario, ventas y tablero.

Archivos: `services\customer_service.py`, `product_service.py`, `inventory_service.py`, `sales_service.py`, `dashboard_service.py` y las rutas homónimas.

La venta confirma e inventaría en una transacción. El tablero usa `count` y `sum` sobre ventas confirmadas.

Prueba:

```bat
cd /d "G:\ERP CHAT\backend"
.venv\Scripts\python.exe -m pytest -q
```

Resultado esperado: las pruebas de `tests\test_erp.py` y `tests\test_tools.py` pasan.

## 11. Frontend

Objetivo: las pantallas que el catálogo del asistente nombra.

```bat
cd /d "G:\ERP CHAT\frontend"
npm run dev
```

Abre http://127.0.0.1:5173. El proxy de `vite.config.ts` envía `/api` al puerto 8000.

Error frecuente: el navegador llama al puerto 5173 sin el proxy y recibe 404. Hay que usar `npm run dev`, no abrir `dist` como archivo suelto, salvo que se publique el build detrás del mismo origen.

## 12. Ollama

Objetivo: comprobar que el servicio local responde.

```bat
ollama list
```

Deben aparecer `qwen2.5:1.5b` y `nomic-embed-text`. `OLLAMA_BASE_URL` en `.env` es `http://127.0.0.1:11434`.

Error frecuente: el asistente dice que no está disponible. Arranca la aplicación de Ollama y verifica `GET /api/assistant/health` con un token.

## 13. Qwen

Objetivo: usar el modelo que cabe en 8 GB sin GPU.

No descargues 7B en esa máquina. Si más adelante hay más memoria, cambia `OLLAMA_MODEL` y descarga esa variante con `ollama pull`. El código no tiene el nombre del modelo escrito en las llamadas: lo lee de la configuración.

En CPU la primera respuesta tarda más porque carga el modelo. `OLLAMA_KEEP_ALIVE=10m` evita recargarlo en cada frase de la misma conversación.

## 14. Function calling

Objetivo: que Qwen pida `consultar_ventas` y Python consulte PostgreSQL.

Archivos: `ai\tool_registry.py`, `ai\tool_executor.py`, `ai\ai_orchestrator.py`.

El orquestador manda un solo esquema por llamada. Se comprobó con Ollama 0.40 que `qwen2.5:1.5b` devuelve `tool_calls` cuando la instrucción y el esquema son cortos.

Error frecuente: pasar las herramientas mal serializadas. El cliente debe enviar JSON de verdad. PowerShell a veces deforma el cuerpo; el servicio usa `httpx`.

## 15. RAG

Objetivo: indexar los manuales escritos en `data\knowledge`.

```bat
cd /d "G:\ERP CHAT"
backend\.venv\Scripts\python.exe scripts\index_knowledge.py
```

Resultado: un conteo de documentos y fragmentos. Chroma queda en `data\chroma_db`.

Error frecuente: indexar con Ollama apagado. El script necesita `nomic-embed-text`.

## 16. Integración del chatbot

Objetivo: el panel ERP AI ASSISTANT en todas las pantallas autenticadas.

Archivo: `frontend\src\components\chat\AssistantPanel.tsx`. Envía `session_id`, muestra fuentes y, si la acción es `NAVIGATE`, llama a `navigate` solo con rutas de la lista blanca.

## 17. Pruebas

Objetivo: repetir los escenarios.

Sin Ollama, `pytest` ya cubre octubre, el producto más vendido, el stock menor de 10, la ruta de nuevo usuario y el rechazo de "elimina todos" y de "ventas de todos los vendedores".

Con Ollama encendido, entra como `admin` y pregunta en el panel:

- ¿Dónde puedo crear un usuario?
- ¿Cuántas ventas tuvimos durante octubre?
- ¿Cómo registro una venta?
- ¿Cuál fue la temperatura promedio del océano en Marte?

Las tres primeras deben apoyarse en una ruta real o en la base. La última debe decir que no corresponde a este ERP.

Error frecuente: juzgar el asistente con la base vacía. Ejecuta antes `scripts\seed_database.py`.
