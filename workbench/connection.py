import asyncio
import json
import os
import sys
import tempfile
from workbench.config import ROOT, worker_environment
from workbench.jobs import terminate_tree
from workbench.connection_errors import ConnectionFailure


async def test_connection(settings):
    process = None
    with tempfile.TemporaryDirectory(prefix="compliance_connection_") as work:
        try:
            spawning = asyncio.create_task(asyncio.create_subprocess_exec(
                sys.executable, "-m", "workbench.worker", cwd=ROOT,
                env=worker_environment(),
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
                creationflags=0x08000000 if os.name == "nt" else 0))
            try:
                process = await asyncio.shield(spawning)
            except asyncio.CancelledError:
                process = await spawning
                raise
            payload = json.dumps({"work_dir": work, "settings": settings.model_dump(), "connection_test": True}).encode()
            try:
                async with asyncio.timeout(60):
                    stdout, _ = await process.communicate(payload)
            except TimeoutError as exc:
                raise ConnectionFailure("timeout") from exc
            events = [json.loads(line) for line in stdout.decode("utf-8").splitlines() if line.strip()]
            errors = [e for e in events if e.get("type") == "error"]
            if errors:
                raise ConnectionFailure(errors[0].get("code", "unknown"))
            if process.returncode:
                raise ConnectionFailure("runtime")
            if not any(e.get("type") == "connected" for e in events):
                raise ConnectionFailure()
        finally:
            if process and process.returncode is None:
                await asyncio.to_thread(terminate_tree, process.pid)
                await process.wait()
