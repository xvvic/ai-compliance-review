import json
from types import SimpleNamespace

import pytest

from workbench.config import Settings, agent_environment
from workbench.connection_errors import ConnectionFailure, failure_code


def test_normalize_provider_endpoint_and_secrets(tmp_path):
    settings = Settings(base_url=" https://api.deepseek.com/anthropic/v1/messages/ ",
                        model=" deepseek-v4-flash ", secret=" test-key \n")
    assert settings.base_url == "https://api.deepseek.com/anthropic"
    assert settings.model == "deepseek-v4-flash"
    assert settings.secret == "test-key"
    assert agent_environment(settings, tmp_path)["ANTHROPIC_API_KEY"] == "test-key"


def test_direct_network_overrides_inherited_proxies(tmp_path, monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "socks5://127.0.0.1:10808")
    env = agent_environment(Settings(), tmp_path)
    assert env["HTTPS_PROXY"] == env["http_proxy"] == env["ALL_PROXY"] == ""
    assert env["NO_PROXY"] == "*"
    assert "HTTPS_PROXY" not in agent_environment(Settings(network_mode="system"), tmp_path)


def test_old_mcp_config_migrates_and_can_be_disabled():
    urls = {"LAW_SEARCH_URL": "https://example.com/mcp"}
    assert Settings(mcp_urls=urls).mcp_enabled
    assert not Settings(mcp_urls=urls, mcp_enabled=False).mcp_enabled
    assert not Settings().mcp_enabled


@pytest.mark.parametrize("status,code", [(401, "authentication_failed"), (402, "billing_error"),
                                         (429, "rate_limit"), (404, "invalid_request"), (503, "server_error")])
def test_provider_status_classification(status, code):
    assert failure_code(SimpleNamespace(api_error_status=status)) == code
    assert failure_code(SimpleNamespace(error="billing_error")) == "billing_error"


@pytest.mark.asyncio
async def test_connection_propagates_only_known_error_codes(monkeypatch):
    from workbench.connection import test_connection as connect

    class Process:
        returncode = 0

        async def communicate(self, payload):
            assert json.loads(payload)["connection_test"]
            return b'{"type":"error","code":"billing_error","content":"private-secret"}\n', b""

    async def spawn(*args, **kwargs):
        return Process()

    monkeypatch.setattr("asyncio.create_subprocess_exec", spawn)
    with pytest.raises(ConnectionFailure, match="余额") as error:
        await connect(Settings(secret="fake-key"))
    assert "private-secret" not in str(error.value)
    assert "private-secret" not in str(ConnectionFailure("private-secret"))


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled,token,expected", [(False, "token", {}), (True, "", {}),
                                                  (True, "token", {"Authorization": "Bearer token"})])
async def test_worker_retrieval_switch_and_optional_token(tmp_path, monkeypatch, enabled, token, expected):
    import workbench.worker as worker
    seen = []

    async def query(*, prompt, options):
        seen.append(options)
        if False:
            yield

    monkeypatch.setattr(worker, "query", query)
    settings = Settings(mcp_enabled=enabled, mcp_token=token, mcp_urls={"LAW_SEARCH_URL": "https://example.com/mcp"})
    await worker.run({"work_dir": str(tmp_path), "settings": settings.model_dump()})
    if enabled:
        assert seen[0].mcp_servers["pkulaw-law-search"]["headers"] == expected
    else:
        assert not seen[0].mcp_servers


@pytest.mark.asyncio
async def test_system_socks_proxy_has_actionable_error(tmp_path, monkeypatch, capsys):
    from workbench.worker import run
    monkeypatch.setenv("HTTPS_PROXY", "socks5://127.0.0.1:10808")
    await run({"work_dir": str(tmp_path), "settings": Settings(network_mode="system").model_dump(), "connection_test": True})
    event = json.loads(capsys.readouterr().out)
    assert event["code"] == "proxy"
    assert "直连" in event["content"]
