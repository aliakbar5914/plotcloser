"""PlotCloser API.  Run locally:  venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8000"""
import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from app import config
from app.agent.graph import build_graph
from app.agent.runner import run_chat
from app.db.connection import close_pool, create_tables, open_pool
from app.db.seed import seed_listings
from app.memory.setup import setup_memory_tables
from app.routes.admin import admin_router, public_router
from app.safety.rate_limit import allow_request
from app.schemas import ChatRequest, chat_response

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("plotcloser")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts.
    open_pool()
    create_tables()
    setup_memory_tables()
    seed_listings()
    app.state.graph = build_graph()
    logger.info("PlotCloser API ready")
    yield
    # Runs once when the server stops.
    close_pool()


app = FastAPI(title="PlotCloser API", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(public_router)
app.include_router(admin_router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, error: RequestValidationError):
    """Bad input still gets the same JSON shape on /chat, so clients never break."""
    if request.url.path == "/chat":
        fields = ", ".join(str(e["loc"][-1]) for e in error.errors())
        return JSONResponse(status_code=422, content=chat_response(
            f"Invalid request. Please send user_id, thread_id and message (problem with: {fields})."))
    return JSONResponse(status_code=422, content={"detail": error.errors()})


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, error: Exception):
    logger.exception("Unexpected error on %s", request.url.path)
    if request.url.path == "/chat":
        return JSONResponse(status_code=500, content=chat_response("Sorry, something went wrong. Please try again."))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/")
def root():
    return {"name": "PlotCloser API", "endpoints": ["POST /chat", "GET /health", "GET /docs"]}


@app.get("/health", response_class=PlainTextResponse)
def health():
    return "ok"


# "def" (not "async def"): the graph is synchronous, so FastAPI runs it in a thread pool.
@app.post("/chat")
def chat(body: ChatRequest, background_tasks: BackgroundTasks):
    message = body.message.strip()
    if not message:
        return chat_response("Please type a message. For example: \"10 marla house in DHA under 3 crore\".")
    if not allow_request(body.user_id):
        return JSONResponse(status_code=429, content=chat_response(
            "You're sending messages too fast. Please wait a moment and try again."))
    return run_chat(app.state.graph, body.user_id, body.thread_id, message, background_tasks)
