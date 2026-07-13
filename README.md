# AI 初创企业合规审查系统

面向法律/合规场景的 agent 应用。用户在网页上传企业材料后,前端把文本发给后端;后端通过 `claude-agent-sdk` 调起 agent,挂载本仓库内的本地 skill 与法律语料,生成一份 Markdown 合规审查报告,并把审查步骤、执行过程以 SSE 流实时回传给前端展示。

> 本文档面向**第一次拉代码的人**,照着从上到下做即可跑通。命令给的是通用形式,Windows 用 PowerShell、Mac/Linux 用终端,差异处会单独标注。

---

## 一、项目架构

| 层 | 文件/目录 | 说明 |
|----|----------|------|
| 前端展示 | `app.py` | Streamlit 网页:上传文件、调后端 SSE、展示步骤/操作、下载报告 |
| 后端编排 | `server.py` | FastAPI 暴露 `/review/stream`,用 `claude-agent-sdk` 调起 agent,把消息转成 SSE 事件 |
| 知识与技能 | `claude-code-plugin/ai-startup-compliance-review/` | 后端实际挂载的本地插件:skill、法律语料、脚本、MCP 声明 |

数据流:`浏览器 → app.py(前端) → server.py(后端) → agent(+插件/语料/MCP) → 报告 & 过程回流`

---

## 二、运行前需要准备

1. **Python 3.10+**(建议 3.11/3.12;本项目在 3.13 上验证过)。检查:`python --version`
2. **一个能用的模型接入**(三选一):
   - 一个 `ANTHROPIC_API_KEY`(见 [四、鉴权](#四鉴权)),**或**
   - 一个**付费的 Claude 订阅账号**(Pro/Max/Team,用于登录),**或**
   - 国产模型(豆包/通义/DeepSeek)的 key,走兼容端点(见 [六、接入其他模型](#六接入其他模型glm--豆包--通义千问--deepseek))
3. 不需要单独安装 Node 或 Claude CLI —— `claude-agent-sdk` **自带内置 CLI**。

---

## 三、快速开始(按顺序做)

### 步骤 1 · 获取代码

```bash
git clone https://github.com/xvvic/ai-compliance-review.git
cd ai-compliance-review
```

### 步骤 2 · 安装依赖

```bash
pip install -r requirements.txt
pip install streamlit python-docx pypdf requests
```

> 🇨🇳 国内如果 `pip` 报 `403 Forbidden`(镜像抽风),换阿里云源重试:
> `pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/`

### 步骤 3 · 创建并填写 `.env`

复制示例文件,得到你自己的 `.env`(它已被 `.gitignore`,不会上传):

```bash
# Windows
copy .env.example .env
# Mac/Linux
cp .env.example .env
```

然后编辑 `.env`,**至少填好鉴权**(下一步详解)。用 Claude 时模型建议保留 `CLAUDE_CODE_MODEL=sonnet`;想用国产免费模型见 [六](#六接入其他模型glm--豆包--通义千问--deepseek)。北大法宝 MCP 那几行是可选的,不填也能跑。

### 步骤 4 · 完成鉴权

见下方 [四、鉴权](#四鉴权)。**最简单的方式**:在 `.env` 里填 `ANTHROPIC_API_KEY=sk-ant-你的key`,这一步就完成了,可直接跳到步骤 5。

### 步骤 5 · 启动后端(开一个终端窗口)

```bash
python server.py
```

看到 `Uvicorn running on http://0.0.0.0:8000` 即成功。**保持这个窗口不关。**

### 步骤 6 · 启动前端(再开一个终端窗口)

```bash
streamlit run app.py
```

它会打印 `Local URL: http://localhost:8501`。

### 步骤 7 · 使用

浏览器打开 **http://localhost:8501** → 上传一份企业材料(txt/docx/pdf)→ 点「开始合规审查」。左侧看审查步骤和执行过程,右侧等最终报告(视模型约几分钟),完成后可下载。

---

## 四、鉴权

`claude-agent-sdk` 用它**自带的内置 claude CLI**(无需你另外安装 Claude CLI)。它需要能通过鉴权,**二选一**(想用国产模型跳到 [六](#六接入其他模型glm--豆包--通义千问--deepseek)):

### 方式 A:用 API Key(推荐,最省事)

在 `.env` 里填:

```dotenv
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
```

- 高校学生可用学校邮箱在 https://console.anthropic.com 申请「Claude for Student Builders」免费额度,拿到 `sk-ant-` 开头的 key。
- 填好即可,`server.py` 用 `load_dotenv()` 会自动读取。

### 方式 B:用订阅账号登录(需付费 Claude 套餐)

不填 API Key 时,需要登录 SDK 自带的内置 CLI。先找到它的路径:

```bash
python -c "import claude_agent_sdk, os; print(os.path.join(os.path.dirname(claude_agent_sdk.__file__), '_bundled'))"
```

在上面打印出的目录里,有 `claude.exe`(Windows)或 `claude`(Mac/Linux)。执行登录:

```powershell
# Windows(把 <上面的目录> 换成实际路径)
& "<上面的目录>\claude.exe" auth login --claudeai
```
```bash
# Mac/Linux
"<上面的目录>/claude" auth login --claudeai
```

浏览器授权后,用同一个可执行文件确认:

```bash
<内置claude> auth status     # 看到 "loggedIn": true 即成功
```

> ⚠️ 登录用的账号**必须有付费套餐**(Pro/Max/Team),否则授权时会被跳到升级付费页。免费账号请改用方式 A,或用国产模型(见 [六](#六接入其他模型glm--豆包--通义千问--deepseek))。

---

## 五、更换 / 选择 Claude 模型

用 Claude 时,模型由 `.env` 里的 `CLAUDE_CODE_MODEL` 决定。可选值与取舍:

| 值 | 特点 | 一次审查耗时(参考) |
|----|------|------------------|
| `haiku` | 最快,但复杂任务/审查步骤规划不稳定 | ~3 分钟 |
| `sonnet` | 均衡,步骤规划稳定,质量好(**推荐**) | ~6 分钟 |
| 不填(默认 Opus) | 质量最高,最慢 | 更久 |

**怎么换(三步):**

1. 编辑 `.env`,改这一行,例如 `CLAUDE_CODE_MODEL=sonnet`(想用默认 Opus,就把这行删掉或用 `#` 注释掉);
2. **重启后端**:到运行 `server.py` 的窗口按 `Ctrl+C` 停掉,再 `python server.py`。
   ⚠️ 模型是**后端启动时读取**的,`.env` 改完**不重启不生效**;
3. 前端**不用**重启,浏览器刷新页面即可。

> - 慢的主因是 skill 工作流本身重(读很多参考文件、多轮检索),不是模型;换更快的模型收效有限。
> - 可选 `CLAUDE_CODE_FALLBACK_MODEL`:主模型不可用时自动兜底的备用模型。

---

## 六、接入其他模型(GLM / 豆包 / 通义千问 / DeepSeek)

没有 Claude 付费额度?想蹭国产模型的免费/便宜额度?可以。智谱 GLM、豆包、通义千问、DeepSeek 都提供了 **"Anthropic 兼容端点"**(专门给 Claude Code 这类工具用):这些模型本身不认 Claude 接口,但各自架了一层"翻译",你把请求地址指过去就能用。

只需在 `.env` 里加/改几个变量,**改完重启后端**即可。三条通用规则:

- 第三方端点一律用 **`ANTHROPIC_AUTH_TOKEN`**(**不要**用 `ANTHROPIC_API_KEY`;两者不能同时设,否则鉴权冲突);
- 有了 `ANTHROPIC_BASE_URL` 后,把原来那行 `CLAUDE_CODE_MODEL` **删掉或注释**,模型改由 `ANTHROPIC_MODEL` 指定;
- 下面的地址/模型名截至编写时有效,**以各家官方文档为准**(附了链接)。

### 智谱 GLM(BigModel)

```dotenv
ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic
ANTHROPIC_AUTH_TOKEN=你的智谱APIKey
ANTHROPIC_MODEL=glm-5.2                     # 也可用 glm-4.6 等
```

- key 在智谱开放平台 https://open.bigmodel.cn 申请。官方接入文档:https://docs.bigmodel.cn/cn/coding-plan/quick-start
- 国际版(z.ai)用户把地址换成 `https://api.z.ai/api/anthropic`。

### DeepSeek

```dotenv
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
ANTHROPIC_AUTH_TOKEN=sk-你的DeepSeek密钥
ANTHROPIC_MODEL=deepseek-v4-flash          # 便宜、快;要更强用 deepseek-v4-pro
```

- key 在 https://platform.deepseek.com 申请。官方接入文档:https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code/
- 注:旧模型名 `deepseek-chat` / `deepseek-reasoner` 将于 2026-07-24 停用,请用上面的 `v4` 名字。

### 通义千问(阿里云百炼 Model Studio)

```dotenv
ANTHROPIC_BASE_URL=https://dashscope.aliyuncs.com/apps/anthropic
ANTHROPIC_AUTH_TOKEN=sk-你的百炼APIKey
ANTHROPIC_MODEL=qwen3-coder-plus           # 具体模型名以百炼文档为准
```

- 百炼对新用户有免费额度;key 在阿里云百炼控制台申请。官方接入文档:https://help.aliyun.com/zh/model-studio/claude-code
- 若用官方 Coding Plan,地址换成 `https://coding.dashscope.aliyuncs.com/apps/anthropic` 并使用 `sk-sp-` 专用 key(详见文档)。

### 豆包(火山方舟 Coding Plan)

```dotenv
ANTHROPIC_BASE_URL=https://ark.cn-beijing.volces.com/api/coding
ANTHROPIC_AUTH_TOKEN=你的火山方舟APIKey
ANTHROPIC_MODEL=doubao-seed-code-preview-latest   # 或 ark-code-latest(自动跟最新)
CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1         # 火山建议加,避免连接报错
```

- key 在火山引擎方舟控制台申请。官方接入文档:https://www.volcengine.com/docs/82379/1928262

### ⚠️ 重要提醒:换非 Claude 模型可能变"笨"

能跑,但**很可能让 agent 表现下降**:审查步骤规划、skill 触发、工具调用、MCP 都是**针对 Claude 调校的**,能力较弱的模型常见问题:

- 不好好规划步骤 → 左侧「审查步骤」面板空;
- skill 不按套路走、法条检索/报告质量下降。

**建议:先用 Claude(方式 A/B)把流程跑通、确认效果,再换国产模型试。** 换了之后如果发现变笨了,那是模型能力差异,不是前端 bug。

---

## 七、北大法宝 MCP(可选)

- **不配置也能运行**:skill 设计为「先查本地语料 `legal_preference_txt/`,不足时才用 MCP」,所以缺 MCP 时会自动用本地语料兜底,照样出报告。
- 要启用真实法条检索,需从**北大法宝控制台**获取并在 `.env` 里填这 6 个值(变量名别写错):

```dotenv
PKULAW_ACCESS_TOKEN=...
PKULAW_LAW_SEARCH_URL=...
PKULAW_LAW_KEYWORD_URL=...
PKULAW_CASE_SEMANTIC_URL=...
PKULAW_LAW_ITEM_URL=...
PKULAW_CITATION_VALIDATOR_URL=...
```

- 这些 URL/token 绑定你们的**购买实例**,只能自行获取。详见 [CLAUDE_CODE接入说明.md](CLAUDE_CODE接入说明.md)。
- 验证:启动后 `/mcp` 能看到 5 个 pkulaw 服务且能实际调用,才算通。

---

## 八、常见问题排查

| 现象 | 原因 & 解决 |
|------|-----------|
| 报告区显示 `审查出错:Claude Code returned an error result: success` | **没鉴权**。填好 `ANTHROPIC_API_KEY`,或用方式 B 登录(`auth status` 确认 `loggedIn: true`),或按 [六](#六接入其他模型glm--豆包--通义千问--deepseek) 配国产模型。 |
| 授权时浏览器跳到 Upgrade/付费页 | 登录的账号没有付费套餐。换有 Pro/Max 的账号,或改用 API Key(方式 A),或用国产模型。 |
| `pip install` 报 403 | 换源:`-i https://mirrors.aliyun.com/pypi/simple/`。 |
| 前端报「连接后端失败」 | 后端没起或地址不对。确认步骤 5 的窗口在跑、侧边栏地址是 `http://127.0.0.1:8000/review/stream`。 |
| 端口 8000/8501 被占用 | 关掉占用的进程,或换端口:后端改 `server.py` 里的 `port=`;前端 `streamlit run app.py --server.port 8600`。 |
| 上传后提示「文件解析为空」 | 多为扫描版 PDF(图片)无法提取文字。换文字版 PDF/docx/txt。 |
| `/mcp` 里 pkulaw 服务调不通 | 6 个 PKULAW 变量没填或填错;不影响出报告(走本地语料)。 |
| 审查步骤没规划出来 / 左侧步骤面板空 | 模型能力波动,`haiku` 和国产模型尤其明显。改用 `CLAUDE_CODE_MODEL=sonnet`。 |
| 配了国产模型仍连不上 | 检查是否用了 `ANTHROPIC_AUTH_TOKEN`(不是 `ANTHROPIC_API_KEY`)、`ANTHROPIC_BASE_URL` 是否正确、改后是否重启了后端。 |

---

## 九、目录结构

```
.
├── app.py                      # 前端入口(Streamlit)
├── server.py                   # 后端入口(FastAPI + claude-agent-sdk)
├── requirements.txt            # 后端基础依赖
├── .env.example                # 环境变量示例(复制成 .env 使用)
├── CLAUDE_CODE接入说明.md       # 插件市场 & 北大法宝 MCP 详细接入说明
└── claude-code-plugin/ai-startup-compliance-review/
    ├── .mcp.json               # 北大法宝 MCP 声明(读取 PKULAW_* 环境变量)
    ├── legal_preference_txt/   # 本地法律语料(MCP 不可用时的兜底来源)
    └── skills/ai-startup-compliance-review/SKILL.md   # 审查 skill 主说明
```

> `plugin/` 是更完整的参考资料与镜像 skill;改 skill 或语料时,`plugin/` 与 `claude-code-plugin/` 两边保持一致。

---

## 十、备注

- 前后端要分别在**两个终端**里常驻;关掉窗口服务就停。
- `.env` 含密钥,**切勿提交**(已在 `.gitignore` 中)。分享配置请改 `.env.example`。
- 运行时 agent 可能在插件目录里生成 `search*.txt` 等临时文件,属正常产物,不必提交。
