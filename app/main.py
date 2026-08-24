import logging
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse

from app.config import settings
from app.database import get_connection, initialize_database
from app.schemas import (
    AuditLogResponse,
    ChatRequest,
    ChatResponse,
    DiagnosisResponse,
    DocumentCreate,
    DocumentResponse,
    IncidentCreate,
    IncidentResponse,
    JavaAlertCallback,
)
from app.services import (
    answer,
    create_document,
    create_incident_via_alert_service,
    dashboard_summary,
    diagnose_incident,
    list_audit_logs,
    list_documents,
    list_incidents,
    llm_status,
    sync_java_alert,
)


def configure_logging() -> None:
    Path("logs").mkdir(exist_ok=True)
    logger = logging.getLogger()
    if logger.handlers:
        return
    logger.setLevel(settings.log_level)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    file_handler = RotatingFileHandler("logs/app.log", maxBytes=1_000_000, backupCount=3)
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


configure_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    logger.info("application started")
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "请求参数不合法", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled error: %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "服务内部错误"})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get("/demo", include_in_schema=False)
def demo_page() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "demo.html")


@app.post("/api/v1/documents", response_model=DocumentResponse, status_code=201)
def add_document(payload: DocumentCreate) -> dict:
    document_id = create_document(payload.title, payload.content, payload.tags)
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, title, tags, created_at FROM documents WHERE id = ?", (document_id,)
        ).fetchone()
    return {**dict(row), "tags": [tag for tag in row["tags"].split(",") if tag]}


@app.get("/api/v1/documents", response_model=list[DocumentResponse])
def get_documents() -> list[dict]:
    return list_documents()


@app.get("/api/v1/dashboard")
def dashboard() -> dict:
    return dashboard_summary()


@app.get("/api/v1/incidents", response_model=list[IncidentResponse])
def get_incidents() -> list[dict]:
    return list_incidents()


@app.post("/api/v1/incidents", response_model=IncidentResponse, status_code=201)
async def add_incident(payload: IncidentCreate) -> dict:
    return await create_incident_via_alert_service(
        payload.category, payload.severity, payload.title, payload.detail
    )


@app.post("/api/v1/integrations/java-alerts", response_model=IncidentResponse)
def receive_java_alert(payload: JavaAlertCallback) -> dict:
    """Java 告警微服务的回调入口，按外部 ID 幂等同步到工作台。"""
    return sync_java_alert(payload.model_dump())


@app.post("/api/v1/incidents/{incident_id}/diagnose", response_model=DiagnosisResponse)
async def diagnose(incident_id: int, use_llm: bool = False) -> dict:
    try:
        diagnosis, sources, mode, duration_ms = await diagnose_incident(incident_id, use_llm)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "incident_id": incident_id,
        "diagnosis": diagnosis,
        "sources": [
            {"id": item["id"], "title": item["title"], "score": item["score"]}
            for item in sources
        ],
        "answer_mode": mode,
        "duration_ms": duration_ms,
    }


@app.get("/api/v1/audit-logs", response_model=list[AuditLogResponse])
def get_audit_logs() -> list[dict]:
    return list_audit_logs()


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> dict:
    reply, documents, mode = await answer(payload.question, payload.use_llm)
    return {
        "answer": reply,
        "sources": [
            {"id": item["id"], "title": item["title"], "score": item["score"]}
            for item in documents
        ],
        "answer_mode": mode,
    }


@app.get("/api/v1/llm/status")
def get_llm_status() -> dict:
    """仅返回安全的配置状态，不会泄露模型密钥。"""
    return llm_status()


@app.get("/api/v1/metrics")
def metrics() -> dict[str, int | str]:
    with get_connection() as connection:
        count = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    return {"documents": count, "status": "ok"}
