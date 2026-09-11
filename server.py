"""Single-origin local application server."""
import asyncio
import json
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from workbench.config import ConfigStore, DATA_DIR, ROOT, Settings, atomic_write
from workbench.documents import MAX_BYTES, MAX_CHARS, parse_document
from workbench.jobs import ReviewManager, now


class ReviewReq(BaseModel):
    document_text: str = Field(min_length=1, max_length=MAX_CHARS)
    filename: str = Field(default="企业材料", max_length=255)


class Decision(BaseModel):
    rule_id: str
    action: Literal["认可初评", "调整等级", "补充依据", "退回重审"]
    review_level: Literal["L1", "L2", "L3", "L4"]
    evidence_note: str = Field(default="", max_length=5000)


class Decisions(BaseModel):
    items: list[Decision] = Field(min_length=1, max_length=100)


def create_app(data_dir: Path = DATA_DIR):
    manager = ReviewManager(data_dir)
    config = ConfigStore(data_dir)
    token = secrets.token_urlsafe(32)

    @asynccontextmanager
    async def lifespan(app):
        yield
        await manager.cancel()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
    app.state.manager = manager
    app.state.config = config

    @app.middleware("http")
    async def local_boundary(request, call_next):
        host = urlsplit("http://" + request.headers.get("host", "")).hostname
        if host not in ("127.0.0.1", "localhost", "::1", "testserver"):
            return JSONResponse({"detail": "仅接受本机访问。"}, status_code=403)
        origin = request.headers.get("origin")
        if origin and origin != str(request.base_url).rstrip("/"):
            return JSONResponse({"detail": "不允许跨站请求。"}, status_code=403)
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            if not secrets.compare_digest(request.headers.get("x-session-token", ""), token):
                return JSONResponse({"detail": "会话已更新，请刷新页面。"}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"
        if request.url.path.startswith(("/api", "/review")):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse({"detail": "请求内容无效，请检查文件、连接地址或必填项。"}, status_code=422)

    @app.exception_handler(Exception)
    async def internal_error(request, exc):
        return JSONResponse({"detail": "操作失败，请检查本地配置或数据目录。"}, status_code=500)

    @app.get("/api/health")
    async def health():
        return {"app": "ai-compliance-workbench", "status": "ok", "version": "1.0.0"}

    @app.get("/api/session")
    async def session():
        return {"token": token}

    @app.post("/api/shutdown")
    async def shutdown():
        callback = getattr(app.state, "request_shutdown", None)
        if callback is None:
            raise HTTPException(409, "请在开发终端停止服务。")
        await manager.cancel()
        callback()
        return {"ok": True}

    @app.get("/api/config")
    async def get_config():
        return config.public()

    @app.put("/api/config")
    async def save_config(settings: Settings):
        try:
            config.save(settings)
        except (ValueError, OSError) as exc:
            raise HTTPException(400, "配置未保存，请检查本机数据目录或重新填写密钥。") from exc
        return config.public()

    @app.post("/api/config/test")
    async def test_config(settings: Settings):
        resolved = config.resolve(settings)
        if not resolved.secret and resolved.auth_mode != "claude_login":
            raise HTTPException(400, "请填写模型密钥。")
        from workbench.connection import test_connection
        from workbench.connection_errors import ConnectionFailure
        try:
            await test_connection(resolved)
        except ConnectionFailure as exc:
            raise HTTPException(400, str(exc)) from exc
        except Exception as exc:
            raise HTTPException(400, "连接测试失败，请检查地址、模型名称、密钥、额度或本机 Claude 登录。") from exc
        return {"ok": True, "message": "模型与审查引擎连接正常"}

    @app.post("/api/documents/parse")
    async def parse(file: UploadFile = File(...)):
        content = await file.read(MAX_BYTES + 1)
        try:
            text = await asyncio.to_thread(parse_document, file.filename or "", content)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        finally:
            await file.close()
        return {"filename": Path((file.filename or "企业材料").replace("\\", "/")).name, "text": text, "chars": len(text), "bytes": len(content)}

    @app.post("/api/config/rag/test")
    async def test_rag(settings: Settings):
        return {"ok": True, "message": "本地 BM25 知识库可用。"}

    @app.get("/api/review/current")
    async def current():
        return manager.snapshot()

    @app.post("/review/stream")
    async def review(req: ReviewReq):
        settings = config.load()
        if not req.document_text.strip():
            raise HTTPException(400, "材料内容不能为空。")
        if not settings.secret and settings.auth_mode != "claude_login":
            raise HTTPException(400, "请先在设置中配置模型连接。")
        try:
            review_id = await manager.start(req.document_text, Path(req.filename.replace("\\", "/")).name, settings)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        return StreamingResponse(manager.stream(review_id), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"})

    @app.get("/api/review/{review_id}/events")
    async def events(review_id: str):
        if not manager.current or manager.current["id"] != review_id:
            raise HTTPException(404, "当前审查不存在。")
        return StreamingResponse(manager.stream(review_id), media_type="text/event-stream")

    @app.post("/api/review/{review_id}/cancel")
    async def cancel(review_id: str):
        if not manager.current or manager.current["id"] != review_id:
            raise HTTPException(404, "当前审查不存在。")
        await manager.cancel()
        return manager.snapshot()

    @app.post("/api/review/{review_id}/decisions")
    async def decisions(review_id: str, req: Decisions):
        async with manager.lock:
            job = manager.current
            if not job or job["id"] != review_id or job["status"] != "completed":
                raise HTTPException(409, "请等待正式审查完成后提交复核。")
            if job["reviewed"]:
                raise HTTPException(409, "本次复核已经提交。")
            rules = {r["id"]: r for r in job["report"]["risk_scan"].get("matched_rules", [])}
            ids = [item.rule_id for item in req.items]
            if len(ids) != len(set(ids)) or set(ids) != set(rules):
                raise HTTPException(400, "请逐条完成所有风险的复核。")
            rows = []
            for item in req.items:
                rule = rules[item.rule_id]
                if item.action != "认可初评" and not item.evidence_note.strip():
                    raise HTTPException(400, "调级、补证和退回需要填写复核依据。")
                level = item.review_level if item.action == "调整等级" else rule["final_level"]
                rows.append({**item.model_dump(), "review_level": level, "system_level": rule["final_level"], "adjusted": level != rule["final_level"], "category": rule.get("category"), "risk_type": rule.get("risk_type"), "matched_keywords": list(rule.get("matched_keywords", {})), "evidence_needed": rule.get("evidence_needed", []), "source_report": "risk_report_" + review_id + ".json", "review_id": review_id, "report_generated_at": job["report"]["generated_at"], "reviewed_at": now()})
            try:
                atomic_write(data_dir / "reviews" / ("review_" + review_id + ".jsonl"), "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n")
            except OSError as exc:
                raise HTTPException(500, "复核记录保存失败，内容尚未提交，请重试。") from exc
            job["reviewed"] = True
            job["decisions"] = rows
            return {"ok": True, "count": len(rows)}

    @app.get("/api/example")
    async def example():
        return json.loads((ROOT / "assets" / "example-report.json").read_text(encoding="utf-8"))

    dist = ROOT / "frontend" / "dist"
    if dist.exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("COMPLIANCE_PORT", "8000")), access_log=False)
