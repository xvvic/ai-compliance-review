import asyncio
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import psutil
import yaml

from workbench.config import DATA_DIR, ROOT, Settings, atomic_write
from workbench.rag import retrieve, report_citations
from workbench.risk_merge import merge_risk_items

PLUGIN = ROOT / "claude-code-plugin" / "ai-startup-compliance-review"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def redact(text: str, secrets=()) -> str:
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[已隐藏]")
    text = re.sub(r"(?i)[A-Z]:[\\/](?:[^\s\"<>|]+)", "[本机路径]", text)
    return re.sub(r"\b(?:sk-ant-|sk-)[A-Za-z0-9_-]{12,}", "[已隐藏]", text)


def redact_event(value, secrets):
    if isinstance(value, str):
        return redact(value, secrets)
    if isinstance(value, dict):
        return {key: redact_event(item, secrets) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_event(item, secrets) for item in value]
    return value


def scan(text):
    try:
        script = PLUGIN / "skills/ai-startup-compliance-review/scripts/detect_risks.py"
        spec = importlib.util.spec_from_file_location("risk_detection", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.detect(text, yaml.safe_load((PLUGIN / "risk_rules.yaml").read_text(encoding="utf-8")))
    except Exception:
        return {"error": "规则预扫描未完成，请在人工复核中核查风险。", "matched_rules": [], "summary": {}}


def terminate_tree(pid):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in reversed(children):
            try:
                child.kill()
            except psutil.Error:
                pass
        parent.kill()
        psutil.wait_procs(children + [parent], timeout=3)
    except psutil.Error:
        pass


class ReviewManager:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.current = None
        self.task = None
        self.process = None
        self.lock = asyncio.Lock()

    def event(self, event):
        job = self.current
        event = {**event, "review_id": job["id"], "seq": len(job["events"]) + 1}
        job["events"].append(event)
        if event["type"] == "todos":
            job["tasks"] = event["items"]
        elif event["type"] == "tool_start":
            job["activities"] = (job["activities"] + [{"label": event["tool_name"], "at": now()}])[-100:]
        elif event["type"] == "rag":
            job["rag"] = event["rag"]
        return event

    async def start(self, text, name, settings: Settings):
        async with self.lock:
            if self.task and not self.task.done():
                raise ValueError("已有审查进行中，请等待完成或取消。")
            self.current = {"id": uuid.uuid4().hex, "status": "running", "started_at": now(), "filename": name,
                            "tasks": [], "activities": [], "events": [], "report": None, "error": None, "saved": False, "reviewed": False}
            self.event({"type": "started"})
            self.task = asyncio.create_task(self.execute(text, settings))
            return self.current["id"]

    def snapshot(self):
        return {k: v for k, v in self.current.items() if k != "events"} if self.current else None

    async def execute(self, text, settings):
        work = Path(tempfile.mkdtemp(prefix="compliance_"))
        job = self.current
        try:
            (work / "待审查材料.txt").write_text(text, encoding="utf-8")
            detection = await asyncio.to_thread(scan, text)
            rag = await retrieve(text, detection, settings)
            rag = redact_event(rag, (settings.secret, settings.mcp_token))
            self.event({"type": "rag", "rag": rag})
            from workbench.config import worker_environment
            spawning = asyncio.create_task(asyncio.create_subprocess_exec(
                sys.executable, "-m", "workbench.worker", cwd=ROOT,
                env=worker_environment(),
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
                creationflags=0x08000000 if os.name == "nt" else 0, limit=8 * 1024 * 1024,
            ))
            try:
                self.process = await asyncio.shield(spawning)
            except asyncio.CancelledError:
                self.process = await spawning
                raise
            worker_settings = settings.model_dump()
            payload = json.dumps({"work_dir": str(work), "settings": worker_settings, "rag": rag}, ensure_ascii=False)
            self.process.stdin.write(payload.encode("utf-8"))
            await self.process.stdin.drain()
            self.process.stdin.close()
            report = ""
            report_risks = []
            async with asyncio.timeout(1800):
                while line := await self.process.stdout.readline():
                    event = json.loads(line.decode("utf-8"))
                    event = redact_event(event, (settings.secret, settings.mcp_token))
                    if event["type"] == "error":
                        raise RuntimeError(event["content"])
                    if event["type"] == "final":
                        report = event["content"]
                    elif event["type"] == "rag_injected" and rag["fragments"]:
                        rag = {**rag, "injected": True}
                        self.event({"type": "rag", "rag": rag})
                    elif event["type"] == "risk_items":
                        report_risks = event.get("items") or []
                    elif event["type"] in ("todos", "tool_start"):
                        self.event(event)
                code = await self.process.wait()
            if code or not report.strip():
                raise RuntimeError("模型未生成完整报告，请检查连接或额度后重试。")
            rag = {**rag, "cited_ids": report_citations(report, rag)}
            self.event({"type": "rag", "rag": rag})
            result = {"generated_at": now(), "model": settings.model, "material": {"chars": len(text), "preview": text[:200]},
                      "risk_scan": detection, "risk_items": merge_risk_items(detection.get("matched_rules"), report_risks),
                      "report_markdown": report, "schema_version": "1.2", "review_id": job["id"], "rag": rag}
            job["report"] = result
            saved_as = "risk_report_" + job["id"] + ".json"
            try:
                await asyncio.to_thread(atomic_write, self.data_dir / "reports" / saved_as, json.dumps(result, ensure_ascii=False, indent=2))
                job["saved"] = True
            except OSError:
                job["save_error"] = "报告已生成，但本机存档失败，请下载保存。"
            self.event({"type": "final", "content": report})
            self.event({"type": "report_json", "content": json.dumps(result, ensure_ascii=False), "saved_as": saved_as if job["saved"] else ""})
            job["status"] = "completed"
        except asyncio.CancelledError:
            job["status"] = "cancelled"
        except Exception as exc:
            job["status"] = "failed"
            message = str(exc) if isinstance(exc, RuntimeError) else "审查未完成，请检查模型连接后重试。"
            job["error"] = message
            self.event({"type": "error", "content": message})
        finally:
            if self.process and self.process.returncode is None:
                await asyncio.to_thread(terminate_tree, self.process.pid)
                await self.process.wait()
            self.process = None
            await asyncio.to_thread(shutil.rmtree, work, True)
            self.event({"type": "done", "status": job["status"], "saved": job["saved"]})

    async def cancel(self):
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                self.current["status"] = "cancelled"
                self.event({"type": "done", "status": "cancelled", "saved": False})

    async def stream(self, review_id, after=0):
        while self.current and self.current["id"] == review_id:
            events = self.current["events"]
            for event in events[after:]:
                after = event["seq"]
                yield "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"
            if self.current["status"] != "running" and (not self.task or self.task.done()):
                break
            yield ": heartbeat\n\n"
            await asyncio.sleep(0.4)
