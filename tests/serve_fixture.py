"""Real HTTP server with a deterministic agent process; never shipped."""
import asyncio
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server import create_app
from workbench.config import ConfigStore, Settings
import uvicorn

spawn = asyncio.create_subprocess_exec


async def fake_spawn(*args, **kwargs):
    if 'workbench.worker' in args:
        args = (sys.executable, str(ROOT / 'tests/fake_agent.py'))
    return await spawn(*args, **kwargs)


asyncio.create_subprocess_exec = fake_spawn
with tempfile.TemporaryDirectory(prefix='compliance_e2e_') as temporary:
    directory = Path(temporary)
    ConfigStore(directory).save(Settings(secret='synthetic-test-key'))
    app = create_app(directory)
    uvicorn.run(app, host='127.0.0.1', port=8011, access_log=False)
