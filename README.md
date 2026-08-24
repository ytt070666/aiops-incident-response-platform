# 云网智能故障处置助手

一个可运行、可部署的 AI 应用后端个人项目。项目以云网运维场景为背景，提供告警管理、AI 辅助诊断、知识库检索、审计日志、可选大模型生成和 Docker 部署能力。

## 技术栈

- Python 3.12、FastAPI、SQLite
- HTTPX（兼容 OpenAI 风格的大模型 API）
- Docker / Docker Compose
- Pytest

## 项目能力

1. 提供云网运行工作台，展示演示可用率、模拟告警、最近任务和审计日志；演示指标不等同于生产监控数据。
2. 支持 WAF、Linux、网络连通性等模拟告警的创建、列表查看和 AI 辅助诊断。
3. 使用中文双字词和英文关键词进行本地检索，不配置模型密钥也能演示。
4. 配置兼容 OpenAI 的模型服务后，可由模型基于检索资料生成答案；服务异常时自动降级为本地检索结果。
5. 通过 Vue 3 工作台展示诊断结论、引用来源与调用模式；后端使用滚动日志、参数校验和统一异常响应。
6. 使用 Docker 在 Linux 环境一键运行，并通过 GitHub Actions 执行自动测试。

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

访问 `http://127.0.0.1:8000/docs` 查看 Swagger API 文档，或访问 `http://127.0.0.1:8000/demo` 使用 Vue 工作台演示界面。

访问 `http://127.0.0.1:8000/api/v1/llm/status` 可检查模型是否已配置；该接口只返回状态，不会返回密钥。

## Docker 运行

```bash
docker compose up --build
```

## Java 微服务与 Vue 控制台

- `alert-service/`：Spring Boot 3 + MySQL + Redis + Actuator 的告警微服务，提供告警创建、查询和关闭接口；使用 Redis 缓存告警列表，并在创建、关闭后回调 Python 工作台。
- `web-console/`：基于 Vite 和 Vue 3 的工程化前端控制台源码。

运行完整服务栈：

```bash
docker compose --profile full up --build
```

Java 服务健康检查地址为 `http://127.0.0.1:8081/actuator/health`。

### 跨服务链路

工作台创建告警时，Python 会调用 Java 告警服务；Java 将告警写入 MySQL、清理 Redis 缓存后，再以 HTTP/1.1 回调 Python 的同步接口。Java 侧直接创建或关闭告警时，Python 工作台也会同步显示对应状态，并写入审计日志。

## 压测

```bash
pip install -r performance/requirements.txt
locust -f performance/locustfile.py --host http://127.0.0.1:8000
```

压测报告中的并发、吞吐和延迟应以你实际运行结果为准，不应预先写入简历。

## 快速演示

新增知识文档：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -d '{"title":"部署规范","content":"服务采用 Docker 部署，部署后检查健康接口、日志和告警。","tags":["Docker","Linux"]}'
```

提问：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"Docker 部署后要检查什么？"}'
```

## 接入 DeepSeek / Qwen（真实模型调用）

本项目使用 OpenAI Chat Completions 兼容协议。密钥只保存在本机或部署平台，不能上传到 GitHub。

DeepSeek：

```bash
export LLM_PROVIDER="deepseek"
export DEEPSEEK_API_KEY="your-secret"
export LLM_MODEL="deepseek-chat"
```

Qwen：

```bash
export LLM_PROVIDER="qwen"
export DASHSCOPE_API_KEY="your-secret"
export LLM_MODEL="qwen-plus"
```

调用 `/api/v1/chat` 时传入 `"use_llm": true` 即可启用。未配置密钥或模型请求失败时，接口会自动使用本地检索结果。

## 测试

```bash
python -m pytest -q
```

## 演示材料

`demo-assets/` 中包含本项目本地 Docker 运行时录制的 API 演示视频、知识库问答结果截图和 Swagger 接口文档截图。上传 GitHub 后可在仓库中直接展示；演示数据均为本地样例数据。
