# AI 初创企业合规审查系统

Windows 本机合规审查工作台。上传企业材料，查看审查进度、报告和规则预扫描风险清单，再逐项完成人工复核。

## 使用便携包

1. 解压 `AI-Compliance-Workbench-Windows-x64.zip` 到可写目录，打开其中的 `AI-Compliance-Workbench` 文件夹。
2. 双击 **启动应用.vbs**，浏览器自动打开本机工作台。无需安装 Python、Node、Git 或管理员权限。
3. 点击右上角 **设置**，在 **模型服务** 中选择服务商、填写密钥，点击 **测试模型连接**，成功后点击 **保存设置**。测试连接不会自动保存配置。DeepSeek 预设自动填写 Anthropic 兼容地址和 `deepseek-v4-flash`。自定义地址与鉴权位于“服务地址与鉴权”；已有 Claude 登录的用户可在其中选择“使用本机 Claude 登录”。
4. 上传 TXT、DOCX 或文字型 PDF，点击 **开始审查**。完成后下载 Markdown/JSON 报告，在 **人工复核** 中逐项确认并提交。
5. 使用完毕，双击 **停止应用.vbs**。关闭浏览器标签不会停止后台审查。

未配置模型时，可在 **审查示例** 区域点击 **查看示例报告**，报告页会提示当前为合成案例；该操作不调用模型、不产生正式复核记录。正式审查和连接测试需要联网，使用所配置模型账户的额度。材料在本机解析，提取文本会发送到所配置的模型服务。

默认监听 `http://127.0.0.1:8000`，端口已占用时自动选择空闲端口。重复启动会打开已运行的实例，不启动第二份服务。仅面向 Windows 10/11 x64 本机单用户使用。

## 工作台操作

1. **准备材料**：在“待审查材料”区域选择或拖入一份文件。解析完成后核对文件名，可展开“材料预览”检查提取文本。需要更换文件时再次选择或拖入。
2. **开始审查**：点击 **开始审查**。若按钮显示 **配置模型并审查**，先完成模型配置，再开始任务。审查过程中可查看当前步骤和执行进度；需要中止时点击 **取消审查**。
3. **阅读结果**：完成后在 **审查报告** 中阅读正文，在 **风险清单** 中按风险或规则编号搜索、按等级筛选，并打开条目查看命中关键词、所需证据与整改方向。
4. **人工复核**：切换到 **人工复核**，为每个命中项选择“认可初评”“调整等级”“补充依据”或“退回重审”。调整等级时选择复核等级；调级、补证或退回时填写依据。填写完整后点击 **提交复核**；成功后记录存档，当前页面不可再次编辑。
5. **导出与继续**：通过 **下载报告** 选择 Markdown 或 JSON。审查下一份材料时点击右上角 **新建审查**，按弹窗确认清空当前页面。该操作不会删除已保存的报告和复核记录。

手机窄屏下，右上角“设置”显示为滑杆图标，审查示例排列在材料上传区域下方。工作台入口和设置均位于页面顶部。

## 配置与数据

所有本机配置和产物保存在 `%LOCALAPPDATA%\AIComplianceWorkbench`：

| 目录或文件 | 内容 |
| --- | --- |
| `settings.json` | 模型和可选 MCP 配置；密钥使用 Windows DPAPI 加密 |
| `reports/` | 已生成的结构化报告，包含报告正文及材料短预览 |
| `reviews/` | 与报告 ID 关联的逐项复核记录，JSONL 格式 |
| `logs/startup.log` | 启动失败的脱敏提示 |
| `instance.json` | 当前服务的进程及端口记录 |

DPAPI 密钥绑定当前 Windows 用户，拷贝配置到其他用户或机器后需重新填写。界面不读取密钥明文，不使用浏览器持久化存储保存密钥。修改设置对下一次审查生效；服务地址或鉴权方式变化时需要重新填写模型密钥。

界面设置优先于源码目录 `.env` 和环境变量；尚未保存界面设置时才读取后两者。网络连接默认直连，不继承启动终端的代理；需要代理时选择“使用系统代理”，支持 HTTP(S) 代理。测试和正式审查使用同一网络设置与审查引擎。连接失败会区分鉴权、余额、限流、无效请求、超时及运行环境问题。

“法规检索”默认使用本地法规与案例。有北大法宝服务的用户可开启在线检索，选择已开通的服务，填写对应 URL 和可选访问令牌。关闭在线检索会保留已保存的连接资料，但审查不加载这些连接。原有非空 MCP 地址配置会自动迁移为启用状态。“测试模型连接”仅验证模型与审查引擎，不验证在线法规服务。

单实例同时审查一份材料。刷新页面可恢复本次服务实例中的任务与结果；停止服务后不恢复页面状态，但已保存的报告和复核文件仍保留。本版不提供历史记录中心。

## 文件与复核

- 单文件不超过 20MB，提取文本不超过 30 万字符。DOCX 提取段落和表格；PDF 支持可提取文字的文档，不包含 OCR。
- 风险清单来自确定性规则预扫描，与 Agent 报告分别展示，不代表两者等级一定相同。预扫描失败会提示“未完成”，不会当成无风险。
- L3/L4 和规则要求的项目标记为必须复核。所有命中项需选择复核动作；调级、补证及退回需填写依据。复核不会改写原始报告。
- 审查失败或取消不生成成功报告。报告生成但磁盘保存失败时，页面明确提示并允许下载；复核写入失败可重试。
- “退回重审”记录复核决定，不自动再次调用模型；补充材料后新建审查。

## 源码开发

需要 Windows x64、Python 3.13 和 Node.js 22+。首次安装与构建：

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock
npm --prefix frontend ci
npm --prefix frontend run build
.venv\Scripts\python.exe launcher.py start
```

之后可双击源码目录的 `start.vbs` / `stop.vbs`。`python app.py` 也是新启动器的兼容入口。生产使用不再依赖 Streamlit。

开发前端时，在两个终端分别运行：

```powershell
.venv\Scripts\python.exe server.py
npm --prefix frontend run dev
```

开发页由 Vite 打印地址；接口通过本机代理访问 FastAPI。运行数据可通过 `COMPLIANCE_DATA_DIR` 指向独立测试目录，服务端口可通过 `COMPLIANCE_PORT` 设置。

## 测试与构建便携包

```powershell
.venv\Scripts\python.exe -m pip install pytest pytest-asyncio
.venv\Scripts\python.exe -m pytest tests -q
npm --prefix frontend test
cd frontend
npx playwright test
cd ..
.venv\Scripts\python.exe scripts\build_portable.py
```

浏览器测试默认使用本机 Chrome，启动独立测试服务器和模拟 Agent，不消耗模型额度。截图位于 `output/playwright/`。构建脚本输出 ZIP、SHA256 文件和解压目录到 `dist/`；下载缓存在 `build/downloads/`。可使用 `--skip-frontend` 复用已有前端构建，或 `--proxy http://host:port` 指定仅本次构建使用的代理。

便携包包含嵌入式 Python、锁定依赖、SDK 内置 CLI、PortableGit、本地插件语料、字体和前端资源。第三方许可保留在依赖目录、字体目录和 `licenses/`。发布包排除 Git 元数据、真实配置、用户上传材料和运行日志。

## 结构与接口

| 模块 | 职责 |
| --- | --- |
| `frontend/` | React、TypeScript、Ant Design 企业工作台 |
| `server.py`、`workbench/` | 文件解析、配置、单任务审查、SSE、报告与人工复核 |
| `launcher.py` | 本机进程管理、端口选择、浏览器启动 |
| `claude-code-plugin/ai-startup-compliance-review/` | 审查技能、规则与语料 |
| `scripts/` | 依赖锁定、合成示例生成和便携包构建 |

`POST /review/stream` 保留 `document_text` 输入及 `todos`、`tool_start`、`final`、`report_json` 成功事件，新增 `started`、`error`、`done` 和审查 ID。最终以 `done.status` 判断成功、失败或取消。

其他接口：`/api/health`、`/api/session`、`/api/config`、`/api/config/test`、`/api/documents/parse`、`/api/review/current`、`/api/review/{id}/events`、`/api/review/{id}/cancel`、`/api/review/{id}/decisions`、`/api/example`。写请求必须携带 `/api/session` 返回的 `x-session-token`，仅接受同源本机请求。

## 常见问题

| 现象 | 处理 |
| --- | --- |
| 双击没有打开页面 | 确认完整解压；检查本地应用数据目录的 `logs/startup.log` |
| Windows 禁用 VBS | 终端运行 `runtime\python\python.exe launcher.py start`；停止时将 `start` 换成 `stop` |
| 模型连接失败 | 检查服务地址、鉴权方式、模型名称和额度；第三方服务必须兼容 Anthropic 协议 |
| 已保存配置无法读取 | 换机或换用户后重新填写密钥并保存 |
| PDF 没有提取文字 | 使用文字型 PDF，或先完成 OCR |
| 报告保存失败 | 先下载报告，再检查用户数据目录权限与磁盘空间 |

Git 新增提交使用 `LegalAgent <legalagent@example.com>` 作为作者和提交者。可在当前仓库设置提交身份：

```powershell
git config --local user.name "LegalAgent"
git config --local user.email "legalagent@example.com"
```

提交前检查暂存内容，不提交真实密钥、个人目录路径、用户材料或运行日志；保留第三方许可与署名，不改写既有共享历史。
