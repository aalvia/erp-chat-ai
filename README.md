# Intelligent ERP

ERP comercial de demostración para Horizonte Distribución. Tiene backend, base de datos, pantallas reales y un asistente local que consulta el sistema en español. No es solo un chatbot: las cifras salen de PostgreSQL y las rutas salen de un catálogo del propio ERP.

## Objetivo

Mostrar cómo una empresa puede preguntar a su ERP en lenguaje natural, encontrar una pantalla, aprender un procedimiento y consultar ventas, inventario, clientes o usuarios sin que el modelo invente datos ni ejecute SQL libre.

## Tecnologías

- Backend: Python 3.12.10, FastAPI, SQLAlchemy, Alembic, Pydantic, Uvicorn, JWT y pwdlib con Argon2.
- Frontend: React, TypeScript, Vite, CSS y React Router.
- Datos: PostgreSQL 18.
- IA local: Ollama, `qwen2.5:1.5b` y `nomic-embed-text`. Vectores en ChromaDB.
- Moneda de demostración: USD. Impuesto inicial: 0 %, configurable.

El modelo por defecto es `qwen2.5:1.5b` porque el equipo de referencia tiene 8 GB de RAM y no tiene tarjeta gráfica. `qwen2.5:7b` no cabe en esa máquina. El modelo se cambia con `OLLAMA_MODEL` sin reescribir el ERP.

## Arquitectura

El navegador habla con FastAPI. Los módulos de negocio leen y escriben PostgreSQL. El orquestador de IA, en `backend/app/ai/ai_orchestrator.py`, clasifica la pregunta, pide a Ollama una llamada de herramienta y ejecuta solo funciones Python ya definidas. Esas funciones vuelven a pasar por permisos y servicios. Los manuales de `data/knowledge/` se usan para explicar procedimientos, no para responder cuánto se vendió.

El detalle está en [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md).

## Requisitos

- Windows 10 u 11.
- Python 3.12.10, el que ya está en esta máquina. No hace falta instalar otro.
- Node.js 22 y npm 10, ya presentes. El comando `node` responde `v22.23.2`.
- PostgreSQL 18 en `localhost:5432`. En esta máquina el servicio es `postgresql-x64-18` y el cliente está en `C:\Program Files\PostgreSQL\18\bin`.
- Ollama en `http://127.0.0.1:11434`, con `qwen2.5:1.5b` y `nomic-embed-text`.
- Unos 8 GB de RAM. Cierra otras aplicaciones pesadas antes de usar el asistente. El modelo de chat se mantiene cargado unos minutos; el de embeddings se descarga al terminar cada índice.

## Instalación

Desde `G:\ERP CHAT` en CMD:

```bat
cd /d "G:\ERP CHAT\backend"
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

Edita `backend\.env` y pon la contraseña real de PostgreSQL en `DATABASE_URL`. En esta instalación local el usuario `postgres` acepta la contraseña `postgres`. El archivo `.env` no se versiona.

Crea las bases si todavía no existen. `psql` no está en el PATH; usa la ruta completa:

```bat
set PGPASSWORD=postgres
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -w -U postgres -h 127.0.0.1 -d postgres -c "CREATE DATABASE intelligent_erp;"
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -w -U postgres -h 127.0.0.1 -d postgres -c "CREATE DATABASE intelligent_erp_test;"
```

Aplica migraciones, datos y el índice de manuales:

```bat
cd /d "G:\ERP CHAT\backend"
.venv\Scripts\python.exe -m alembic upgrade head
cd /d "G:\ERP CHAT"
backend\.venv\Scripts\python.exe scripts\seed_database.py
backend\.venv\Scripts\python.exe scripts\index_knowledge.py
```

Frontend:

```bat
cd /d "G:\ERP CHAT\frontend"
npm install
```

## Ejecución

Terminal 1:

```bat
cd /d "G:\ERP CHAT\backend"
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```bat
cd /d "G:\ERP CHAT\frontend"
npm run dev
```

- Aplicación: http://127.0.0.1:5173
- API y Swagger: http://127.0.0.1:8000/docs

Para repetir la demostración desde cero:

```bat
cd /d "G:\ERP CHAT"
backend\.venv\Scripts\python.exe scripts\seed_database.py
```

Eso borra los datos de negocio y vuelve a crear 3 roles, 10 usuarios, 30 clientes, 40 productos y 130 ventas entre enero y noviembre de 2026.

## Usuarios de prueba

La contraseña de todos es `Demo123!`. Son personas ficticias, solo para esta máquina.

| Usuario | Rol | Qué puede hacer |
|---|---|---|
| admin | ADMINISTRADOR | Todo |
| vendedor.ana | VENDEDOR | Clientes, productos, inventario y sus ventas |
| vendedor.luis | VENDEDOR | Igual que Ana |
| vendedor.marta | VENDEDOR | Igual que Ana |
| vendedor.carlos | VENDEDOR | Igual que Ana |
| vendedor.julia | VENDEDOR | Igual que Ana |
| consulta.sofia | CONSULTA | Lectura de catálogo e indicadores |
| consulta.diego | CONSULTA | Igual que Sofía |
| consulta.elena | CONSULTA | Igual que Sofía |
| consulta.pablo | CONSULTA | Igual que Sofía |

## Funcionalidades

- Inicio de sesión, JWT y cierre de sesión.
- Usuarios, roles y permisos comprobados en el servidor.
- Clientes con historial de compras.
- Productos, categorías, precio, costo, SKU y existencias.
- Entradas, salidas, ajustes e historial de inventario.
- Ventas que descuentan stock en una transacción y rechazan stock insuficiente.
- Tablero con consultas reales.
- Asistente con navegación, manuales y herramientas.
- Auditoría de accesos, cambios y herramientas.

## Pruebas

```bat
cd /d "G:\ERP CHAT\backend"
.venv\Scripts\python.exe -m pytest -q
```

Las pruebas de negocio usan la base `intelligent_erp_test` y no dependen de Ollama. Cubren login, permisos, ventas, inventario, tablero, rutas del asistente y el rechazo de borrados masivos.

## Documentación

- [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md)
- [docs/MANUAL_IMPLEMENTACION.md](docs/MANUAL_IMPLEMENTACION.md)
- [docs/GUIA_IA_RAG.md](docs/GUIA_IA_RAG.md)
- [docs/GUIA_FUNCTION_CALLING.md](docs/GUIA_FUNCTION_CALLING.md)
- [docs/GUIA_CODIGO.md](docs/GUIA_CODIGO.md)
- [docs/GUIA_ENTREVISTA.md](docs/GUIA_ENTREVISTA.md)
- [docs/API.md](docs/API.md)
