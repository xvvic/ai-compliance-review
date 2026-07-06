"""
AI合规审查系统 - 后端接口(修正版)
============================================
安装:
    pip install claude-agent-sdk fastapi uvicorn python-dotenv
前提:
    - 环境变量 ANTHROPIC_API_KEY(放 .env 或系统环境变量)
    - skill 放在 .claude/skills/ 下(标准结构),或用下面的兜底拼prompt方式
    - MCP 配置(北大法宝等)在 .mcp.json 或代码里配置
"""

import os
import json
import tempfile
import shutil
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

# 正确的包:claude-agent-sdk(不是 anthropic 的 Agent)
from claude_agent_sdk import query, ClaudeAgentOptions

load_dotenv()

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

            # 3. 配置 Agent SDK
            #    - cwd 指向工作目录,agent 就能在里面读写文件
            #    - setting_sources=["project"] 让 SDK 自动加载 .claude/skills/ 下的 skill
            #    - mcp_servers 配置北大法宝等 MCP(TODO-1)
            options = ClaudeAgentOptions(
                cwd=work_dir,
                setting_sources=["project"],   # 自动加载 .claude/skills/ 里的 skill
                permission_mode="acceptEdits", # 允许 agent 读写工作区文件
                # ============ TODO-1:配置 MCP ============
                # 把北大法宝等 MCP 服务配进来。参考 claude-agent-sdk 文档的 mcp_servers 写法。
                # 例如(具体字段以真实SDK文档为准):
                # mcp_servers={
                #     "pkulaw": {"type": "http", "url": "https://...北大法宝MCP地址..."}
                # },
                # ==================================================
            )

            prompt = (
                "请审查工作目录中的《待审查材料.txt》,完成合规审查。"
                "优先使用本地MCP工具检索真实法条,按技能规则输出Markdown报告,"
                "包含:风险等级、审查结论、匹配法条、整改建议。"
            )

            # 4. 流式跑 agent,把每条消息转成前端约定的 SSE 格式
            async for message in query(prompt=prompt, options=options):
                # ============ TODO-2:解析真实消息 ============
                # 重要:先用真实SDK跑一次、打印 message 看清结构,再写这里!
                # 真实 claude-agent-sdk 的消息是 AssistantMessage / ToolUseBlock /
                # ToolResultBlock 等对象,字段不是豆包猜的 event.type=="tool_call_start"。
                # 下面是"伪代码框架",按真实字段名改:
                #
                # 参考思路(具体类名/字段以你打印出来的为准):
                #   from claude_agent_sdk import AssistantMessage, TextBlock, ToolUseBlock, ToolResultBlock
                #   if isinstance(message, AssistantMessage):
                #       for block in message.content:
                #           if isinstance(block, TextBlock):
                #               yield sse({"type": "final", "content": block.text})
                #           elif isinstance(block, ToolUseBlock):
                #               yield sse({"type": "tool_start", "tool_name": block.name, "args": block.input})
                #   elif isinstance(message, ToolResultBlock):   # 或在对应消息类型里
                #       yield sse({"type": "tool_end", "tool_name": ..., "result": str(...)[:2000]})
                #
                # 在没改对之前,先把原始消息打印出来看结构:
                print("SDK消息:", type(message), message)
                # 临时:先把能拿到的文本透传,保证前端至少有输出(队友改对后删掉这行)
                text = getattr(message, "text", None) or str(message)
                yield sse({"type": "final", "content": ""})  # 占位,队友按上面改成真解析
                # ======================================================

        except Exception as e:
            yield sse({"type": "final", "content": f"审查出错:{str(e)}(请检查 ANTHROPIC_API_KEY、MCP配置、skill路径)"})
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def sse(event: dict) -> str:
    """打包成 SSE 一行。前端约定格式:{type, tool_name?, args?, result?, content?}"""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@app.get("/")
def root():
    return {"status": "后端运行中,POST /review/stream 开始审查"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)