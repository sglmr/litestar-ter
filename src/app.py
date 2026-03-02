import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from io import StringIO
from pathlib import Path
from typing import Annotated

import aiosqlite
from dotenv import load_dotenv
from litestar import Litestar, Request, Response, get, post
from litestar.background_tasks import BackgroundTask
from litestar.config.compression import CompressionConfig
from litestar.config.csrf import CSRFConfig
from litestar.connection import ASGIConnection
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.datastructures import State
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotAuthorizedException
from litestar.handlers import BaseRouteHandler
from litestar.logging.config import LoggingConfig
from litestar.middleware.logging import LoggingMiddlewareConfig
from litestar.middleware.session.client_side import CookieBackendConfig
from litestar.params import Body
from litestar.plugins.flash import FlashConfig, FlashPlugin
from litestar.plugins.problem_details import ProblemDetailsConfig, ProblemDetailsPlugin
from litestar.response import Redirect, Template
from litestar.static_files import create_static_files_router
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from litestar.template.config import TemplateConfig
from litestar_browser_reload import BrowserReloadPlugin
from rich.console import Console
from watchfiles import DefaultFilter

from helpers import rand_id, send_email_async
from repository import UserRepository

# --- LOGGING ---
logging_config = LoggingConfig(
    root={"level": "INFO", "handlers": ["console"]},
    formatters={"standard": {"format": "%(name)s - %(message)s"}},
    handlers={
        "console": {
            "class": "rich.logging.RichHandler",
            "rich_tracebacks": True,
            "show_time": True,
            "show_path": False,
        }
    },
)

logging_middleware_config = LoggingMiddlewareConfig()


# --- TEMPLATE CONFIG ---
templates_path = Path("templates")
template_config: TemplateConfig = TemplateConfig(
    directory=templates_path,
    engine=JinjaTemplateEngine,
)
browser_reload = BrowserReloadPlugin(
    watch_paths=(templates_path, Path("static")),
    watch_filter=DefaultFilter(ignore_dirs=(".git", ".hg", ".svn", ".tox")),
)

# TODO: Figure out how to use the flash plugin
flash_plugin = FlashPlugin(config=FlashConfig(template_config=template_config))
problem_details_plugin = ProblemDetailsPlugin(ProblemDetailsConfig())


# --- DATABASE SETUP ---
@asynccontextmanager
async def db_connection(app: Litestar) -> AsyncGenerator[None, None]:
    db_path = os.getenv("DATABASE_URL", "app.sqlite")
    conn = await aiosqlite.connect(db_path)
    await conn.execute("PRAGMA journal_mode=WAL;")
    await conn.execute("PRAGMA foreign_keys=ON;")
    app.state.db_conn = conn
    try:
        yield
    finally:
        await conn.close()


async def provide_db_conn(state: State) -> AsyncGenerator[aiosqlite.Connection, None]:
    """Dependency provider injecting a raw DB connection into routes."""
    yield state.db_conn


async def provide_user_repo(db: aiosqlite.Connection) -> UserRepository:
    return UserRepository(db)


# --- AUTH & SESSION ---
secret_key = os.getenv("SECRET_KEY", rand_id(length=32))
if len(secret_key) < 32:
    raise ValueError("SECRET_KEY must be at least 32 characters long")
secret_key = secret_key[:32]

session_config = CookieBackendConfig(secret=secret_key.encode("utf-8"))


def session_auth_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    if not connection.session.get("username"):
        raise NotAuthorizedException("You must be logged in to view this page.")


# --- BACKGROUND TASKS ---
async def process_new_user_background(username: str, email: str):
    log = logging.getLogger("background_worker")
    log.info(f"Starting background processing for {username}...")
    await send_email_async(email, "Welcome!", f"Hi {username}, you're registered.")
    log.info(f"Finished background tasks for {username}.")


# --- EXCEPTION HANDLERS ---
def handle_404(request: Request, exc: Exception) -> Template:
    return Template(template_name="404.html", status_code=404)


def handle_500(request: Request, exc: Exception) -> Template:
    request.logger.error("Internal Server Error", exc_info=exc)
    return Template(template_name="500.html", status_code=500)


def handle_exception(request: Request, exc: Exception) -> Template:

    if request.app.debug:
        console = Console(file=StringIO(), force_terminal=True, width=100, record=True)
        console.print_exception(show_locals=True)
        traceback_str = console.export_html(inline_styles=True)

        return Template(
            template_name="debug_exception.html.jinja2",
            context={"exception": str(exc), "traceback": traceback_str},
            status_code=500,
        )


exception_handlers = {
    HTTP_404_NOT_FOUND: handle_404,
    HTTP_500_INTERNAL_SERVER_ERROR: handle_500,
    Exception: handle_exception,
}


# --- ROUTES ---
@get("/")
async def index() -> Redirect:
    return Redirect(path="/login")


@get("/login")
async def login_page() -> Template:
    return Template(template_name="login.html")


@post("/login")
async def process_login(
    request: Request,
    data: Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)],
) -> Response | Template:
    username, password = data.get("username"), data.get("password")
    if username == os.getenv("ADMIN_USER") and password == os.getenv("ADMIN_PASS"):
        request.set_session({"username": username})
        return Redirect(path="/secure")
    return Template(
        template_name="login.html", context={"error": "Invalid credentials"}
    )


@post("/logout")
async def logout(request: Request) -> Redirect:
    request.clear_session()
    return Redirect(path="/login")


@get("/secure", guards=[session_auth_guard])
async def secure_page(request: Request, user_repo: UserRepository) -> Template:
    users = await user_repo.get_all_users()
    return Template(
        template_name="secure.html",
        context={"username": request.session.get("username"), "users": users},
    )


@post("/users", guards=[session_auth_guard])
async def add_user(data: dict[str, str], user_repo: UserRepository) -> Response:
    username = data.get("username", "Anonymous")
    await user_repo.create_user(username=username)
    users = await user_repo.get_all_users()
    template = Template(template_name="users_list.html", context={"users": users})
    return Response(
        template,
        background=BackgroundTask(
            process_new_user_background, username, "test@example.com"
        ),
    )


@get("/favicon.ico")
async def favicon() -> Response:
    # This SVG creates a square with an emoji in the center
    svg_favicon = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<text y=".9em" font-size="90">🚀</text>'
        "</svg>"
    )

    return Response(
        content=svg_favicon,
        media_type="image/svg+xml",
        headers={
            # Cache it for 1 year (31,536,000 seconds)
            "Cache-Control": "public, max-age=31536000, immutable"
        },
        status_code=HTTP_200_OK,
    )


# --- APP INIT ---
def create_app(debug: bool = False, db_url: str | None = None) -> Litestar:
    # If a db_url is passed (from tests), you can inject it
    # into your provide_db_conn or set the environment here.
    if db_url:
        os.environ["DATABASE_URL"] = db_url

    app = Litestar(
        route_handlers=[
            favicon,
            index,
            login_page,
            process_login,
            logout,
            secure_page,
            add_user,
            create_static_files_router(path="/static", directories=["static"]),
        ],
        compression_config=CompressionConfig(backend="gzip", gzip_compress_level=9),
        lifespan=[db_connection],
        dependencies={
            "db": Provide(provide_db_conn),
            "user_repo": Provide(provide_user_repo),
        },
        template_config=template_config,
        logging_config=logging_config,
        csrf_config=CSRFConfig(
            secret=secret_key,
            cookie_name="x-csrftoken",
            cookie_secure=False,
            cookie_httponly=False,
        ),
        middleware=[logging_middleware_config.middleware, session_config.middleware],
        debug=debug,
        exception_handlers=exception_handlers,
    )

    return app


# Keep this for your production ASGI server (uvicorn src.app:app)
load_dotenv()
DEBUG = os.environ["DEBUG"].lower() is True
app = create_app()
