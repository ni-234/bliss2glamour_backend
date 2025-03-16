from contextlib import asynccontextmanager
from gc import collect
from os.path import join
from typing import Any

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from .ai.ai_helper import qwen_loader
from .auth.auth_helper import AuthDataFiles, hashPassword
from .database.crud import create_default_admin_user
from .database.database import async_session_maker, create_tables
from .routers import ai, auth, lesson, quiz, user
from .settings import settings
from .utils.fastapi_globals import GlobalsMiddleware, g
from .utils.spa import SinglePageApplication


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    async with async_session_maker() as session:
        await create_default_admin_user(
            session,
            settings.ADMIN_EMAIL,
            settings.ADMIN_FIRST_NAME,
            settings.ADMIN_LAST_NAME,
            hashPassword(settings.ADMIN_PASSWORD),
        )
    models: dict[str, Any] = {"qwen2.5-0.5B": qwen_loader()}
    g.set_default("qwen", models["qwen2.5-0.5B"])
    yield
    models.clear()
    g.cleanup()
    collect()


app = FastAPI(redoc_url=None, docs_url=None, lifespan=lifespan)

app.mount("/data", AuthDataFiles(directory="data"), name="data")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=["*"],
    allow_credentials=True,
)
app.add_middleware(GlobalsMiddleware)

app.include_router(auth.router, prefix="/api/auth")
app.include_router(user.router, prefix="/api/user")
app.include_router(lesson.router, prefix="/api/lesson")
app.include_router(quiz.router, prefix="/api/quiz")
app.include_router(ai.router, prefix="/api/ai")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        contact=(
            {"name": settings.CONTACT_NAME, "email": settings.CONTACT_EMAIL}
            if settings.CONTACT_NAME and settings.CONTACT_EMAIL
            else None
        ),
        license_info={"name": settings.LICENSE_NAME} if settings.LICENSE_NAME else None,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/api/health", tags=["DEFAULT"])
async def health():
    """Health Check for the API"""
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "UP"})


@app.get("/docs", include_in_schema=False)
async def swagger_ui_html():
    """Custom Swagger UI HTML page"""
    return get_swagger_ui_html(
        openapi_url=settings.OPENAPI_URL,
        title="Bliss2Galmour API",
        swagger_favicon_url="/icon192.png",
    )


app.mount(
    "/", SinglePageApplication(directory=join(settings.ROOT_DIR, "..", "ui")), name="ui"
)
