"""
AI合规审查系统 - 后端接口
自动适配claude-code-plugin下的MCP配置和Skill，无需手动修改
启动直接跑在8000端口，和前端默认地址完全匹配
"""
import os
import json
import tempfile
import shutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from anthropic import Anthropic, Agent
from mcp import MCPClient
from pydantic import BaseModel
import uvicorn

# ============================================================
# 初始化FastAPI，开跨域
# ============================================================
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# 自动加载队友的插件配置
# ============================================================
PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "claude-code-plugin/ai-startup-compliance-review")
MCP_CONFIG_PATH = os.path.join(PLUGIN_ROOT, ".mcp.json")
SKILL_PATH = os.path.join(PLUGIN_ROOT, "skills/ai-startup-compliance-review")

def load_all_skills() -> str:
    """自动加载插件目录下所有Skill md文件，拼系统提示词"""
    skill_content = []
    for root, _, files in os.walk(SKILL_PATH):
        for f in files:
            if f.endswith(".md"):
                with open(os.path.join(root, f), "r", encoding="utf-8") as fp:
                    skill_content.append(fp.read())
    base_prompt = """你是专业的科创企业合规审查专家，严格按照给定的技能规则完成审查，优先使用本地MCP工具检索真实法条，审查结果输出Markdown格式，包含风险等级、审查结论、匹配法条、整改建议。
所有审查过程中需要读写的文件，请放在给定的临时工作目录中。
"""
    return base_prompt + "\n\n---\n\n".join(skill_content)

async def load_all_mcp_tools():
    """自动读取插件里的.mcp.json配置，加载所有北大法宝MCP工具"""
    tools = []
    if os.path.exists(MCP_CONFIG_PATH):
        with open(MCP_CONFIG_PATH, "r", encoding="utf-8") as fp:
            mcp_config = json.load(fp)
        for server_name, server_conf in mcp_config.get("mcpServers", {}).items():
            if server_conf.get("type") == "http" or "url" in server_conf:
                try:
                    async with MCPClient(server_conf["url"]) as client:
                        tools.extend(await client.get_tools())
                except Exception as e:
                    print(f"加载MCP服务{server_name}失败: {e}")
    return tools

# ============================================================
# 接口定义
# ============================================================
class ReviewReq(BaseModel):
    document_text: str

@app.post("/review/stream")
async def review_stream(req: ReviewReq):
    from fastapi.responses import StreamingResponse
    async def event_generator():
        # 1. 创建临时工作目录（满足Agent文件读写需求，审查完自动删除）
        work_dir = tempfile.mkdtemp(prefix="compliance_")
        try:
            # 2. 初始化模型、MCP、Skill、Agent
            llm = Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                model="claude-3-5-sonnet-latest"
            )
            tools = await load_all_mcp_tools()
            system_prompt = load_all_skills() + f"\n当前工作目录：{work_dir}"
            agent = Agent(
                model=llm,
                system_prompt=system_prompt,
                tools=tools,
                working_dir=work_dir
            )

            # 3. 把待审材料存到工作目录
            with open(os.path.join(work_dir, "待审查材料.txt"), "w", encoding="utf-8") as fp:
                fp.write(req.document_text)

            # 4. 流式跑Agent，把事件转成前端要的格式
            async for event in agent.query(f"请审查工作目录中的《待审查材料.txt》，完成合规审查："):
                event_data = {}
                if event.type == "thinking":
                    event_data = {"type": "thinking", "content": event.delta}
                elif event.type == "tool_call_start":
                    event_data = {"type": "tool_start", "tool_name": event.tool_name, "args": event.args}
                elif event.type == "tool_call_end":
                    res = str(event.result)[:2000]
                    event_data = {"type": "tool_end", "tool_name": event.tool_name, "result": res}
                elif event.type == "text":
                    event_data = {"type": "final", "content": event.delta}
                else:
                    continue
                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
        except Exception as e:
            err_event = {"type": "final", "content": f"审查出错：{str(e)}，请检查大模型Key和MCP配置"}
            yield f"data: {json.dumps(err_event, ensure_ascii=False)}\n\n"
        finally:
            # 审查完删临时目录
            shutil.rmtree(work_dir, ignore_errors=True)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)