"""
AI合规审查系统 - 后端接口(修正版)
============================================
安装:
    pip install claude-agent-sdk fastapi uvicorn python-dotenv
前提:
    - 已登录 Claude Code，或环境变量 ANTHROPIC_API_KEY 可用
    - 可选: 用 CLAUDE_CODE_MODEL / CLAUDE_CODE_FALLBACK_MODEL 指定模型
    - 默认以 full access 启动 Claude agent，避免因权限确认卡住
    - skill 放在 .claude/skills/ 下(标准结构),或用下面的兜底拼prompt方式
    - MCP 配置(北大法宝等)在 .mcp.json 或代码里配置
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

# 正确的包:claude-agent-sdk(不是 anthropic 的 Agent)
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    ServerToolResultBlock,
    ServerToolUseBlock,
    StreamEvent,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    query,
)

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent
PLUGIN_DIR = REPO_ROOT / "claude-code-plugin" / "ai-startup-compliance-review"
DEFAULT_MODEL = os.getenv("CLAUDE_CODE_MODEL")
DEFAULT_FALLBACK_MODEL = os.getenv("CLAUDE_CODE_FALLBACK_MODEL")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReviewReq(BaseModel):
    document_text: str


@app.post("/review/stream")
async def review_stream(req: ReviewReq):
    async def event_generator():
        # 1. 建临时工作目录(agent 读写文件用,审查完删除)
        work_dir = tempfile.mkdtemp(prefix="compliance_")
        try:
            # 2. 把待审材料写进工作目录
            material_path = os.path.join(work_dir, "待审查材料.txt")
            with open(material_path, "w", encoding="utf-8") as fp:
                fp.write(req.document_text)

            if not PLUGIN_DIR.exists():
                raise RuntimeError(f"插件目录不存在: {PLUGIN_DIR}")

            # 3. 配置 Agent SDK
            #    - cwd 指向工作目录,agent 就能在里面读写文件
            #    - plugins 直接挂载仓库内已整理好的 Claude Code 插件
            #    - permission_mode=bypassPermissions 给予 agent full access
            option_kwargs = dict(
                cwd=work_dir,
                setting_sources=["user", "project"],
                plugins=[{"type": "local", "path": str(PLUGIN_DIR)}],
                skills=["ai-startup-compliance-review"],
                permission_mode="bypassPermissions",
            )
            if DEFAULT_MODEL:
                option_kwargs["model"] = DEFAULT_MODEL
            if DEFAULT_FALLBACK_MODEL:
                option_kwargs["fallback_model"] = DEFAULT_FALLBACK_MODEL
            options = ClaudeAgentOptions(**option_kwargs)

            prompt = (
                "请审查工作目录中的《待审查材料.txt》,完成合规审查。"
                "优先使用本地MCP工具检索真实法条,按技能规则输出Markdown报告,"
                "包含:风险等级、审查结论、匹配法条、整改建议。"
            )

            # 4. 流式跑 agent,把每条消息转成前端约定的 SSE 格式
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, ThinkingBlock) and block.thinking:
                            yield sse({"type": "thinking", "content": block.thinking})
                        elif isinstance(block, TextBlock):
                            yield sse({"type": "final", "content": block.text})
                        elif isinstance(block, (ToolUseBlock, ServerToolUseBlock)):
                            yield sse(
                                {
                                    "type": "tool_start",
                                    "tool_name": block.name,
                                    "args": block.input,
                                }
                            )
                        elif isinstance(block, ToolResultBlock):
                            yield sse(
                                {
                                    "type": "tool_end",
                                    "tool_name": block.tool_use_id,
                                    "result": stringify_result(block.content),
                                }
                            )
                        elif isinstance(block, ServerToolResultBlock):
                            yield sse(
                                {
                                    "type": "tool_end",
                                    "tool_name": block.tool_use_id,
                                    "result": stringify_result(block.content),
                                }
                            )
                elif isinstance(message, StreamEvent):
                    delta = message.event.get("delta", {})
                    thinking = delta.get("thinking")
                    if thinking:
                        yield sse({"type": "thinking", "content": thinking})
                elif isinstance(message, ResultMessage) and message.is_error:
                    error_text = message.result or "; ".join(message.errors or []) or "Claude SDK 调用失败"
                    yield sse({"type": "final", "content": f"\n\n审查出错:{error_text}"})

        except Exception as e:
            yield sse(
                {
                    "type": "final",
                    "content": (
                        f"审查出错:{str(e)}"
                        "(请检查 Claude Code 登录状态或 ANTHROPIC_API_KEY、MCP配置、插件目录)"
                    ),
                }
            )
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def sse(event: dict) -> str:
    """打包成 SSE 一行。前端约定格式:{type, tool_name?, args?, result?, content?}"""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def stringify_result(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


@app.get("/")
def root():
    return {"status": "后端运行中,POST /review/stream 开始审查"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
