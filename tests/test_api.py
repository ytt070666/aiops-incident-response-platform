from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_document_and_chat() -> None:
    with TestClient(app) as client:
        document = client.post(
            "/api/v1/documents",
            json={
                "title": "Linux 服务部署规范",
                "content": "服务使用 Docker 部署，部署后应检查日志、健康接口和异常告警。",
                "tags": ["Linux", "Docker"],
            },
        )
        assert document.status_code == 201

        response = client.post(
            "/api/v1/chat",
            json={"question": "Docker 部署后需要检查什么？"},
        )
        assert response.status_code == 200
        assert response.json()["sources"]
        assert response.json()["answer_mode"] == "local_retrieval"


def test_dashboard_and_incident_diagnosis() -> None:
    with TestClient(app) as client:
        dashboard = client.get("/api/v1/dashboard")
        assert dashboard.status_code == 200
        assert "api_availability" in dashboard.json()

        incidents = client.get("/api/v1/incidents")
        assert incidents.status_code == 200
        assert incidents.json()

        incident_id = incidents.json()[0]["id"]
        diagnosis = client.post(f"/api/v1/incidents/{incident_id}/diagnose")
        assert diagnosis.status_code == 200
        assert diagnosis.json()["answer_mode"] == "local_retrieval"

        audit_logs = client.get("/api/v1/audit-logs")
        assert audit_logs.status_code == 200
        assert any(log["action"] == "AI 告警诊断" for log in audit_logs.json())


def test_java_alert_callback_and_llm_status() -> None:
    with TestClient(app) as client:
        callback = client.post(
            "/api/v1/integrations/java-alerts",
            json={
                "id": 9001,
                "category": "WAF",
                "severity": "高",
                "title": "Java 服务回调告警",
                "detail": "用于验证 Java 告警服务向 Python 工作台的幂等回调链路。",
                "status": "OPEN",
            },
        )
        assert callback.status_code == 200
        assert callback.json()["source"] == "java"
        assert callback.json()["external_id"] == "9001"

        repeat = client.post(
            "/api/v1/integrations/java-alerts",
            json={
                "id": 9001,
                "category": "WAF",
                "severity": "高",
                "title": "Java 服务回调告警",
                "detail": "用于验证 Java 告警服务向 Python 工作台的幂等回调链路。",
                "status": "RESOLVED",
            },
        )
        assert repeat.status_code == 200
        assert repeat.json()["id"] == callback.json()["id"]
        assert repeat.json()["status"] == "已关闭"

        llm_status = client.get("/api/v1/llm/status")
        assert llm_status.status_code == 200
        assert "configured" in llm_status.json()
