"""Per-user configuration. Secrets never leave the server in plaintext."""

import base64
import ctypes
import json
import os
import tempfile
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values
from pydantic import BaseModel, Field, model_validator

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("COMPLIANCE_DATA_DIR", str(Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "AIComplianceWorkbench")))
MCP_KEYS = ["LAW_SEARCH_URL", "LAW_KEYWORD_URL", "CASE_SEMANTIC_URL", "LAW_ITEM_URL", "CITATION_VALIDATOR_URL"]
SECRET_FIELDS = ("secret", "mcp_token")


def atomic_write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".pending-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def dpapi(value: bytes, decrypt: bool = False) -> bytes:
    if os.name != "nt":
        raise ValueError("界面密钥保存仅支持 Windows；其他系统请使用 .env。")

    class Blob(ctypes.Structure):
        _fields_ = [("size", ctypes.c_ulong), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    buffer = ctypes.create_string_buffer(value)
    source = Blob(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    function = ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
    function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(Blob)]
    function.restype = ctypes.c_int
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise ValueError("无法读取本机加密配置，请重新填写密钥。")
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        ctypes.windll.kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        ctypes.windll.kernel32.LocalFree(target.data)


class Settings(BaseModel):
    auth_mode: Literal["api_key", "auth_token", "claude_login"] = "api_key"
    network_mode: Literal["direct", "system"] = "direct"
    base_url: str = "https://api.anthropic.com"
    model: str = "sonnet"
    secret: str = Field(default="", max_length=4096)
    clear_secret: bool = False
    mcp_token: str = Field(default="", max_length=4096)
    clear_mcp_token: bool = False
    mcp_urls: dict[str, str] = Field(default_factory=dict)
    mcp_enabled: bool = False
    rag_enabled: bool = False

    @model_validator(mode="before")
    @classmethod
    def migrate_retrieval(cls, values):
        if isinstance(values, dict) and "mcp_enabled" not in values:
            values = {**values, "mcp_enabled": any(values.get("mcp_urls", {}).values())}
        return values

    @model_validator(mode="after")
    def validate_urls(self):
        from urllib.parse import urlsplit
        self.base_url = self.base_url.strip().rstrip("/")
        self.model = self.model.strip()
        self.secret = self.secret.strip()
        self.mcp_token = self.mcp_token.strip()
        self.mcp_urls = {k: v.strip() for k, v in self.mcp_urls.items()}
        # The agent appends /v1/messages itself; accept pasted full endpoints.
        for suffix in ("/v1/messages", "/v1"):
            if self.base_url.endswith(suffix):
                self.base_url = self.base_url[:-len(suffix)]
                break
        if not self.base_url:
            raise ValueError("请填写模型服务地址。")
        for value in [self.base_url, *self.mcp_urls.values()]:
            if not value:
                continue
            url = urlsplit(value)
            if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query or url.fragment:
                raise ValueError("连接地址必须是无账号、查询参数和片段的 HTTP(S) 地址。")
        if any(key not in MCP_KEYS for key in self.mcp_urls):
            raise ValueError("未知的 MCP 配置项。")
        if not self.model.strip():
            raise ValueError("请填写模型名称。")
        return self


class ConfigStore:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.path = data_dir / "settings.json"

    def load(self) -> Settings:
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            for key in SECRET_FIELDS:
                encrypted = raw.pop(key + "_encrypted", "")
                raw[key] = dpapi(base64.b64decode(encrypted), True).decode() if encrypted else ""
            return Settings(**raw)
        env = {**dotenv_values(ROOT / ".env"), **os.environ}
        token = env.get("ANTHROPIC_AUTH_TOKEN", "") or ""
        key = env.get("ANTHROPIC_API_KEY", "") or ""
        return Settings(
            auth_mode="auth_token" if token else "api_key",
            base_url=env.get("ANTHROPIC_BASE_URL") or "https://api.anthropic.com",
            model=env.get("ANTHROPIC_MODEL") or env.get("CLAUDE_CODE_MODEL") or "sonnet",
            secret=token or key,
            mcp_token=env.get("PKULAW_ACCESS_TOKEN") or "",
            mcp_urls={k: env.get("PKULAW_" + k) or "" for k in MCP_KEYS},
            rag_enabled=str(env.get("COMPLIANCE_RAG_ENABLED", "")).lower() in ("1", "true"),
        )

    def resolve(self, settings: Settings) -> Settings:
        try:
            previous = self.load()
        except (ValueError, OSError):
            previous = Settings()
        updated = settings.model_copy(deep=True)
        for key, clear in ((key, "clear_" + key) for key in SECRET_FIELDS):
            if getattr(updated, clear):
                setattr(updated, key, "")
            elif not getattr(updated, key):
                keep = True
                if key == "secret":
                    keep = previous.auth_mode == updated.auth_mode and previous.base_url == updated.base_url
                if keep:
                    setattr(updated, key, getattr(previous, key))
        return updated

    def save(self, settings: Settings):
        updated = self.resolve(settings)
        raw = updated.model_dump(exclude={"clear_" + key for key in SECRET_FIELDS})
        for key in SECRET_FIELDS:
            value = raw.pop(key)
            raw[key + "_encrypted"] = base64.b64encode(dpapi(value.encode())).decode() if value else ""
        atomic_write(self.path, json.dumps(raw, ensure_ascii=False, indent=2))

    def public(self):
        error = None
        try:
            settings = self.load()
        except (ValueError, OSError):
            settings = Settings()
            error = "本机配置无法读取，请重新保存模型设置。"
        return {**settings.model_dump(exclude=set(SECRET_FIELDS) | {"clear_" + key for key in SECRET_FIELDS}),
                "has_secret": bool(settings.secret), "has_mcp_token": bool(settings.mcp_token),
                "knowledge_base": {"status": "ready", "documents": 38, "version": "local-bm25-v1"},
                "configured": bool(settings.secret) or settings.auth_mode == "claude_login", "config_error": error}


def agent_environment(settings: Settings, work_dir: Path) -> dict[str, str]:
    env = {k: "" for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL", "CLAUDE_CODE_MODEL", "CLAUDE_CODE_FALLBACK_MODEL", "CLAUDE_CODE_OAUTH_TOKEN")}
    env.update({"ANTHROPIC_BASE_URL": settings.base_url, "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "CLAUDE_CODE_DISABLE_AUTO_UPDATE": "1"})
    if settings.network_mode == "direct":
        env.update({key: "" for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")})
        env.update({"NO_PROXY": "*", "no_proxy": "*"})
    if settings.auth_mode != "claude_login":
        env["ANTHROPIC_API_KEY" if settings.auth_mode == "api_key" else "ANTHROPIC_AUTH_TOKEN"] = settings.secret
        env["CLAUDE_CONFIG_DIR"] = str(work_dir / ".agent-config")
    runtime_git = ROOT / "runtime" / "git" / "bin" / "bash.exe"
    if runtime_git.exists():
        env["CLAUDE_CODE_GIT_BASH_PATH"] = str(runtime_git)
    import sys
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")
    return env


def worker_environment():
    """Return a sanitized environment for the worker process."""
    return dict(os.environ)

