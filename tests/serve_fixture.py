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
from fastapi import FastAPI, Request
from scripts.prepare_assets import example_rag

spawn = asyncio.create_subprocess_exec


async def fake_spawn(*args, **kwargs):
    if 'workbench.worker' in args:
        args = (sys.executable, str(ROOT / 'tests/fake_agent.py'))
    return await spawn(*args, **kwargs)


asyncio.create_subprocess_exec = fake_spawn
with tempfile.TemporaryDirectory(prefix='compliance_e2e_') as temporary:
    directory = Path(temporary)
    ConfigStore(directory).save(Settings(secret='synthetic-test-key', rag_enabled=True, embedding_url='http://127.0.0.1:8011/embedding/embeddings', embedding_api_key='synthetic-rag-key'))
    workbench_app = create_app(directory)
    fake_rag = FastAPI()
    fragments = example_rag()[0]['fragments']

    from workbench import knowledge, embeddings
    from tokenizers import Tokenizer, models, pre_tokenizers
    raw = Tokenizer(models.WordLevel({"[UNK]": 0}, unk_token="[UNK]"))
    raw.pre_tokenizer = pre_tokenizers.Whitespace()
    raw.save(str(directory / "tokenizer.json"))
    tokenizer = embeddings.LocalTokenizer(directory / "tokenizer.json")
    knowledge.knowledge_status = lambda: {"status": "ready", "documents": 38, "version": "browser-fixture", "dimension": 1024}

    @fake_rag.post('/embeddings')
    async def embedding_data(request: Request):
        assert request.headers.get('authorization') == 'Bearer synthetic-rag-key'
        body = await request.json()
        return {"data": [{"index": i, "embedding": [1.] + [0.] * 1023} for i in range(len(body["input"]))]}

    async def check(settings):
        await embeddings.embed([embeddings.PROBE], settings, tokenizer)
    knowledge.check_embedding = check

    class FixtureRuntime:
        async def query(self, query, settings):
            await asyncio.sleep(0.2)
            chunks = [] if 'NO_RAG' in query else [
                {'chunk_id': f['source_id'], 'file_path': f['path'], 'content': f['text']} for f in fragments
            ]
            return query, {'status': 'success', 'data': {'chunks': chunks}}, {"version": "browser-fixture", "model": embeddings.MODEL}
    knowledge.runtime = FixtureRuntime

    app = FastAPI(lifespan=workbench_app.router.lifespan_context)
    app.mount('/embedding', fake_rag)
    app.mount('/', workbench_app)
    uvicorn.run(app, host='127.0.0.1', port=8011, access_log=False)
