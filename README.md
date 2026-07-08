# AI 初创企业合规审查系统

这是一个面向法律/合规场景的 agent 应用。

用户在网页端上传企业材料后，前端会把文本发送给后端；后端再通过 `claude-agent-sdk` 调起 Claude agent，并挂载本仓库内的本地 skill 与法律语料，生成一份 Markdown 格式的合规审查报告，同时把思考过程和工具调用轨迹以 SSE 流的形式实时返回给前端。

## 项目架构

1. 前端展示层：`app.py`
   使用 Streamlit 搭建聊天式网页界面，负责文件上传、调用后端 SSE 接口、展示执行轨迹、下载最终报告
2. 后端编排层：`server.py`
   使用 FastAPI 暴露 `/review/stream`，接收材料文本，通过 `claude-agent-sdk` 调起 Claude agent，并将 Claude 消息转换为前端 SSE 事件
3. 知识与技能层：`claude-code-plugin/ai-startup-compliance-review/`
   包含 Claude Code 可加载的本地插件、skill、引用模板、脚本和法律语料，后端当前直接挂载这个本地插件目录

## 目录

- `app.py`：前端入口
- `server.py`：后端入口
- `requirements.txt`：后端基础依赖
- `claude-code-plugin/ai-startup-compliance-review/`：当前后端实际挂载的本地插件
- `claude-code-plugin/ai-startup-compliance-review/skills/ai-startup-compliance-review/SKILL.md`：审查 skill 主说明
- `plugin/`：更完整的参考资料、镜像 skill 与语料，维护时需要和 `claude-code-plugin/` 保持一致

注意：

- 当前网页应用运行时，后端直接使用 `claude-code-plugin/` 下的插件目录
- `plugin/` 和 `claude-code-plugin/` 有镜像内容；如果后续改 skill 或语料，两边一起更新

## 环境依赖

先确认 Claude CLI 可用，然后安装后端和前端依赖

```bash
pip install -r requirements.txt
pip install streamlit python-docx pypdf requests
```

配置环境变量
- `CLAUDE_CODE_MODEL`：指定主模型
- `CLAUDE_CODE_FALLBACK_MODEL`：指定 fallback 模型
- `ANTHROPIC_API_KEY`

参考 [CLAUDE_CODE接入说明.md](/home/witt/harness/ai-compliance-review/CLAUDE_CODE接入说明.md) ，配置北大法宝MCP变量：

- `PKULAW_ACCESS_TOKEN`
- `PKULAW_LAW_SEARCH_URL`
- `PKULAW_LAW_KEYWORD_URL`
- `PKULAW_CASE_SEMANTIC_URL`
- `PKULAW_LAW_ITEM_URL`
- `PKULAW_CITATION_VALIDATOR_URL`

## 快速启动


```bash
# 启动后端，默认监听 http://127.0.0.1:8000
python server.py

# 启动前端，默认使用网址 http://127.0.0.1:8000/review/stream
streamlit run app.py
```