import re
import time
from collections import Counter
from typing import Any

import httpx

from app.config import get_llm_config, settings
from app.database import get_connection


def create_document(title: str, content: str, tags: list[str]) -> int:
    normalized_tags = ",".join(tag.strip() for tag in tags if tag.strip())
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO documents (title, content, tags) VALUES (?, ?, ?)",
            (title.strip(), content.strip(), normalized_tags),
        )
        return int(cursor.lastrowid)


def list_documents() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, title, tags, created_at FROM documents ORDER BY id DESC"
        ).fetchall()
    return [
        {**dict(row), "tags": [tag for tag in row["tags"].split(",") if tag]}
        for row in rows
    ]


def _serialize_row(row: Any) -> dict[str, Any]:
    return dict(row)


def list_incidents(limit: int = 20) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM incidents ORDER BY CASE severity WHEN '高' THEN 1 WHEN '中' THEN 2 ELSE 3 END, id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_serialize_row(row) for row in rows]


def get_incident(incident_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    return _serialize_row(row) if row else None


def create_incident(category: str, severity: str, title: str, detail: str) -> dict[str, Any]:
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO incidents (category, severity, title, detail) VALUES (?, ?, ?, ?)",
            (category, severity, title, detail),
        )
        incident_id = int(cursor.lastrowid)
    log_audit("创建告警", f"{category}｜{title}", "system")
    return get_incident(incident_id) or {}


def sync_java_alert(alert: dict[str, Any]) -> dict[str, Any]:
    """接收 Java 告警服务的回调，并以 Java 告警 ID 做幂等同步。"""
    external_id = str(alert["id"])
    status = "已关闭" if alert.get("status") == "RESOLVED" else "待处理"
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM incidents WHERE source = 'java' AND external_id = ?",
            (external_id,),
        ).fetchone()
        if existing:
            incident_id = int(existing["id"])
            connection.execute(
                "UPDATE incidents SET category = ?, severity = ?, title = ?, detail = ?, "
                "status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (
                    alert["category"],
                    alert["severity"],
                    alert["title"],
                    alert["detail"],
                    status,
                    incident_id,
                ),
            )
        else:
            cursor = connection.execute(
                "INSERT INTO incidents (category, severity, title, detail, status, source, external_id) "
                "VALUES (?, ?, ?, ?, ?, 'java', ?)",
                (
                    alert["category"],
                    alert["severity"],
                    alert["title"],
                    alert["detail"],
                    status,
                    external_id,
                ),
            )
            incident_id = int(cursor.lastrowid)
    log_audit("Java 告警同步", f"Java#{external_id}｜{alert['title']}", "java_callback")
    return get_incident(incident_id) or {}


async def create_incident_via_alert_service(
    category: str, severity: str, title: str, detail: str
) -> dict[str, Any]:
    """由 Python 工作台调用 Java 告警服务；不可用时保留本地降级能力。"""
    if not settings.alert_service_url:
        return create_incident(category, severity, title, detail)

    try:
        async with httpx.AsyncClient(timeout=4) as client:
            response = await client.post(
                f"{settings.alert_service_url}/api/v1/alerts",
                json={
                    "category": category,
                    "severity": severity,
                    "title": title,
                    "detail": detail,
                },
            )
            response.raise_for_status()
        incident = sync_java_alert(response.json())
        log_audit("Python 调用 Java 告警服务", f"Java#{incident['external_id']}｜{title}", "service_call")
        return incident
    except httpx.HTTPError as exc:
        log_audit("Java 告警服务降级", f"{title}｜{type(exc).__name__}", "service_call", is_error=True)
        return create_incident(category, severity, title, detail)


def log_audit(
    action: str,
    detail: str,
    mode: str,
    duration_ms: int | None = None,
    is_error: bool = False,
) -> None:
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO audit_logs (action, detail, mode, duration_ms, is_error) VALUES (?, ?, ?, ?, ?)",
            (action, detail, mode, duration_ms, int(is_error)),
        )


def list_audit_logs(limit: int = 12) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [{**_serialize_row(row), "is_error": bool(row["is_error"])} for row in rows]


def dashboard_summary() -> dict[str, Any]:
    with get_connection() as connection:
        total = connection.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        high = connection.execute(
            "SELECT COUNT(*) FROM incidents WHERE severity = '高' AND status != '已关闭'"
        ).fetchone()[0]
        pending = connection.execute(
            "SELECT COUNT(*) FROM incidents WHERE status = '待处理'"
        ).fetchone()[0]
    return {
        "api_availability": 99.98,
        "active_incidents": total,
        "high_risk_incidents": high,
        "pending_diagnoses": pending,
        "recent_tasks": list_audit_logs(5),
    }


def _tokens(text: str) -> Counter[str]:
    """同时提取英文单词与中文双字词，避免额外依赖中文分词库。"""
    text = text.lower()
    english_words = re.findall(r"[a-z0-9_+-]{2,}", text)
    chinese = "".join(re.findall(r"[\u4e00-\u9fff]", text))
    chinese_bigrams = [chinese[index : index + 2] for index in range(len(chinese) - 1)]
    return Counter(english_words + chinese_bigrams)


def retrieve(question: str, limit: int = 3) -> list[dict[str, Any]]:
    question_tokens = _tokens(question)
    if not question_tokens:
        return []

    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, title, content, tags FROM documents"
        ).fetchall()

    results: list[dict[str, Any]] = []
    for row in rows:
        document = dict(row)
        document_tokens = _tokens(
            f"{document['title']} {document['tags']} {document['content']}"
        )
        overlap = sum(
            min(count, document_tokens.get(token, 0))
            for token, count in question_tokens.items()
        )
        if overlap:
            score = overlap / max(1, sum(question_tokens.values()))
            results.append({**document, "score": round(score, 3)})
    return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]


def _local_answer(question: str, documents: list[dict[str, Any]]) -> str:
    if not documents:
        return "知识库中暂未找到相关内容。请补充文档后重试。"

    snippets = []
    for document in documents:
        content = re.sub(r"\s+", " ", document["content"]).strip()
        snippets.append(f"《{document['title']}》：{content[:180]}")
    return "基于已检索到的知识库内容：\n" + "\n".join(snippets)


async def _llm_answer(question: str, documents: list[dict[str, Any]]) -> str:
    llm = get_llm_config()
    if not (llm.base_url and llm.api_key and llm.model):
        raise ValueError("未配置有效的大模型服务")

    context = "\n\n".join(
        f"标题：{item['title']}\n内容：{item['content']}" for item in documents
    )
    payload = {
        "model": llm.model,
        "messages": [
            {
                "role": "system",
                "content": "你是企业知识库助手。仅基于给定资料回答；资料不足时明确说明。",
            },
            {"role": "user", "content": f"资料：\n{context}\n\n问题：{question}"},
        ],
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {llm.api_key}"}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            f"{llm.base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
    return str(response.json()["choices"][0]["message"]["content"])


async def answer(question: str, use_llm: bool) -> tuple[str, list[dict[str, Any]], str]:
    documents = retrieve(question)
    if use_llm and documents:
        try:
            return await _llm_answer(question, documents), documents, "llm"
        except (httpx.HTTPError, KeyError, ValueError):
            # 大模型服务不可用时降级到本地检索，保证 API 可用。
            return _local_answer(question, documents), documents, "local_fallback"
    return _local_answer(question, documents), documents, "local_retrieval"


def llm_status() -> dict[str, Any]:
    llm = get_llm_config()
    return {
        "provider": llm.provider,
        "model": llm.model,
        "base_url": llm.base_url,
        "configured": bool(llm.api_key and llm.base_url and llm.model),
    }


async def diagnose_incident(incident_id: int, use_llm: bool = False) -> tuple[str, list[dict[str, Any]], str, int]:
    incident = get_incident(incident_id)
    if not incident:
        raise LookupError("告警不存在")
    started_at = time.perf_counter()
    question = (
        f"告警类型：{incident['category']}；等级：{incident['severity']}；"
        f"告警标题：{incident['title']}；详情：{incident['detail']}。"
        "请给出优先排查步骤、风险判断与处置建议。"
    )
    diagnosis, sources, mode = await answer(question, use_llm)
    duration_ms = int((time.perf_counter() - started_at) * 1000)
    with get_connection() as connection:
        connection.execute(
            "UPDATE incidents SET status = '已诊断', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (incident_id,),
        )
    log_audit("AI 告警诊断", incident["title"], mode, duration_ms)
    return diagnosis, sources, mode, duration_ms
