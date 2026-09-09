import asyncio
import json
import os
import sys
import tempfile
from workbench.config import ROOT
from workbench.jobs import terminate_tree


async def test_connection(settings):
    process = None
    with tempfile.TemporaryDirectory(prefix="compliance_connection_") as work:
        try:
            spawning = asyncio.create_task(asyncio.create_subprocess_exec(
                sys.executable, "-m", "workbench.worker", cwd=ROOT,
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
                creationflags=0x08000000 if os.name == "nt" else 0))
            try:
                process = await asyncio.shield(spawning)
            except asyncio.CancelledError:
                process = await spawning
                raise
            payload = json.dumps({"work_dir": work, "settings": settings.model_dump(), "connection_test": True}).encode()
            async with asyncio.timeout(60):
                stdout, _ = await process.communicate(payload)
            events = [json.loads(line) for line in stdout.decode("utf-8").splitlines() if line.strip()]
            if process.returncode or not any(e.get("type") == "connected" for e in events) or any(e.get("type") == "error" for e in events):
                raise ValueError("模型连接测试失败。")
        finally:
            if process and process.returncode is None:
                await asyncio.to_thread(terminate_tree, process.pid)
                await process.wait()
