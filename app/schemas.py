from datetime import datetime

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120, description="文档标题")
    content: str = Field(min_length=10, max_length=10000, description="知识库正文")
    tags: list[str] = Field(default_factory=list, max_length=10)


class DocumentResponse(BaseModel):
    id: int
    title: str
    tags: list[str]
    created_at: datetime


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    use_llm: bool = Field(
        default=False,
        description="配置了兼容 OpenAI 的大模型服务后，可设为 true",
    )


class SourceDocument(BaseModel):
    id: int
    title: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]
    answer_mode: str


class IncidentCreate(BaseModel):
    category: str = Field(pattern="^(WAF|Linux|网络)$")
    severity: str = Field(pattern="^(高|中|低)$")
    title: str = Field(min_length=4, max_length=120)
    detail: str = Field(min_length=10, max_length=2000)


class IncidentResponse(BaseModel):
    id: int
    category: str
    severity: str
    title: str
    detail: str
    status: str
    source: str = "python"
    external_id: str | None = None
    created_at: datetime
    updated_at: datetime


class DiagnosisResponse(BaseModel):
    incident_id: int
    diagnosis: str
    sources: list[SourceDocument]
    answer_mode: str
    duration_ms: int


class AuditLogResponse(BaseModel):
    id: int
    action: str
    detail: str
    mode: str
    duration_ms: int | None
    is_error: bool
    created_at: datetime


class JavaAlertCallback(BaseModel):
    id: int
    category: str = Field(pattern="^(WAF|Linux|网络)$")
    severity: str = Field(pattern="^(高|中|低)$")
    title: str = Field(min_length=4, max_length=120)
    detail: str = Field(min_length=10, max_length=2000)
    status: str = "OPEN"
