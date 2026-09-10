# AI 初创企业合规审查系统

上传企业材料，生成合规审查报告并完成人工复核。

适用于 **Windows 10 / 11，64 位（x64）**。使用便携包，无需安装 Python、Node.js 或 Git。

## 1. 下载应用

1. 打开 **[软件下载页](https://github.com/xvvic/ai-compliance-review/releases)**，找到最新版本，展开 **Assets（附件）**。
2. 下载 **`AI-Compliance-Workbench-Windows-x64.zip`**，不要选择 `Source code` 源码包。
3. 找到下载的 ZIP 文件，右键选择 **全部解压**，解压到方便找到的位置。

## 2. 打开应用

打开解压后的 **AI-Compliance-Workbench** 文件夹，双击 **启动应用.vbs**，等待浏览器自动打开工作台。

请从解压后的文件夹启动，并保留其中的其他文件。下次使用时，再次双击 **启动应用.vbs** 即可。

## 3. 关闭应用

回到同一文件夹，双击 **停止应用.vbs**，然后关闭浏览器页面。

**仅关闭浏览器页面不会停止应用。**

## 4. 配置模型（首次使用必读）

审查功能需要一个大模型服务。首次使用请点击界面右上角**设置**，按下表任选一家填写，保存后用**连接测试**确认。

| 服务商 | 服务地址 | 鉴权方式 | 模型名称 | 密钥获取 |
|---|---|---|---|---|
| DeepSeek | `https://api.deepseek.com/anthropic` | Bearer Token | `deepseek-v4-flash` | platform.deepseek.com |
| 智谱 GLM | `https://open.bigmodel.cn/api/anthropic` | Bearer Token | `glm-5.2`（或 glm-4.6） | open.bigmodel.cn |
| 通义千问（百炼） | `https://dashscope.aliyuncs.com/apps/anthropic` | Bearer Token | `qwen3-coder-plus` | 阿里云百炼控制台 |
| 豆包（火山方舟） | `https://ark.cn-beijing.volces.com/api/coding` | Bearer Token | `doubao-seed-code-preview-latest` | 火山方舟控制台 |
| Anthropic Claude | `https://api.anthropic.com`（默认） | API Key | `sonnet` | console.anthropic.com（国内需代理） |

填写要点：

- 国产模型：服务商选 **自定义兼容服务**，展开"服务地址与鉴权"，服务地址填上表地址，鉴权方式选 **Bearer Token**（不是 API Key）；DeepSeek 也可直接选预设"DeepSeek"。
- 网络连接：国产端点选 **直连**；Claude 官方端点需要代理，选 **使用系统代理（HTTP/HTTPS）**，且账号需允许 Claude Code 使用。
- 密钥按 Windows 账户加密保存在本机（`%LOCALAPPDATA%\AIComplianceWorkbench`），**换电脑或换 Windows 账户需重新填写**。
- 连接测试或审查失败时会显示具体原因：密钥或登录无效 / 余额不足 / 限流 / 模型名称或地址错误，按提示处理即可。

**源码开发注意**：走第三方兼容端点时，`.env` 中的 `CLAUDE_CODE_MODEL` 必须删除或注释（否则发送的模型名与此冲突，会被服务商以 400 拒绝），模型名改用 `ANTHROPIC_MODEL` 指定；界面已保存的配置优先于 `.env`。详见 `.env.example` 与 [开发指南](https://github.com/xvvic/ai-compliance-review/blob/HEAD/docs/开发指南.md)。

---

源码运行、测试和打包发布见 [开发指南](https://github.com/xvvic/ai-compliance-review/blob/HEAD/docs/开发指南.md)。
