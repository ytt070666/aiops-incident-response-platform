import sqlite3
from pathlib import Path

from app.config import settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    detail TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT '待处理',
    source TEXT NOT NULL DEFAULT 'python',
    external_id TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    detail TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'system',
    duration_ms INTEGER,
    is_error INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

SEED_DOCUMENTS = (
    (
        "WAF 高危告警处置规范",
        "当 WAF 触发高危拦截告警时，应先核验来源 IP、URI、命中规则与访问频率，确认是否影响正常业务；必要时执行临时拦截、规则调整和升级处置，并保留审计日志。",
        "WAF,安全告警,应急处置",
    ),
    (
        "Linux 服务异常排查手册",
        "Linux 服务响应异常时，应检查健康接口、进程状态、CPU 与内存、磁盘空间、容器日志和应用错误栈；优先定位近期发布与配置变更，再执行回滚或重启等操作。",
        "Linux,Docker,日志分析",
    ),
    (
        "网络连通性故障排查流程",
        "网络连通性异常应依次核验 DNS 解析、路由可达性、端口连通性、负载均衡健康检查及上下游接口状态，并记录命令输出和处置结论。",
        "网络,DNS,接口联调",
    ),
)

SEED_INCIDENTS = (
    (
        "WAF",
        "高",
        "WAF 高频 SQL 注入拦截告警",
        "10 分钟内同一来源 IP 对登录接口触发 187 次拦截，业务接口暂未出现错误率上升。",
    ),
    (
        "Linux",
        "中",
        "AI 推理服务容器内存使用率过高",
        "推理服务容器内存使用率持续 15 分钟高于 85%，健康检查正常。",
    ),
    (
        "网络",
        "低",
        "知识库服务 DNS 解析耗时波动",
        "部分请求 DNS 解析耗时超过 200ms，暂未发现接口失败。",
    ),
)


def get_connection() -> sqlite3.Connection:
    database_path: Path = settings.database_path
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(SCHEMA)
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(incidents)").fetchall()
        }
        if "source" not in columns:
            connection.execute(
                "ALTER TABLE incidents ADD COLUMN source TEXT NOT NULL DEFAULT 'python'"
            )
        if "external_id" not in columns:
            connection.execute("ALTER TABLE incidents ADD COLUMN external_id TEXT")
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_incidents_external "
            "ON incidents(source, external_id) WHERE external_id IS NOT NULL"
        )
        for document in SEED_DOCUMENTS:
            exists = connection.execute(
                "SELECT 1 FROM documents WHERE title = ?", (document[0],)
            ).fetchone()
            if not exists:
                connection.execute(
                    "INSERT INTO documents (title, content, tags) VALUES (?, ?, ?)", document
                )
        for incident in SEED_INCIDENTS:
            exists = connection.execute(
                "SELECT 1 FROM incidents WHERE title = ?", (incident[2],)
            ).fetchone()
            if not exists:
                connection.execute(
                    "INSERT INTO incidents (category, severity, title, detail) VALUES (?, ?, ?, ?)",
                    incident,
                )
