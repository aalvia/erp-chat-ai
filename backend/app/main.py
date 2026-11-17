import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import assistant, audit, auth, customers, dashboard, inventory, products, roles, sales
from app.api.routes import settings as settings_routes
from app.api.routes import users
from app.config import get_settings
from app.core.errors import AppError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Intelligent ERP",
        summary="ERP comercial con asistente local sobre Ollama.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    api_routers = [
        auth.router,
        users.router,
        roles.router,
        customers.router,
        products.router,
        inventory.router,
        sales.router,
        dashboard.router,
        settings_routes.router,
        audit.router,
        assistant.router,
    ]
    for router in api_routers:
        app.include_router(router, prefix="/api")
    return app


app = create_app()
