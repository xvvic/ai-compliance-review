# Claude Code 接入说明

本文档说明如何把本仓库中已经整理好的本地插件市场与插件包接入 Claude Code，并完成北大法宝 MCP 的配置。

适用范围：

- 仅针对 `claude-code-plugin/` 目录下的 Claude Code 插件接入
- 不涉及本仓库中的 Streamlit 前端、LLM 调用封装、`pkulaw_mcp.py` 原型代码

## 一、当前仓库中的插件目录

本次适配后的 Claude Code 接入入口不在旧的 `plugin/` 目录，而在新的：

- [claude-code-plugin](/home/witt/harness/ai-compliance-review/claude-code-plugin)

这个目录本身是一个本地插件市场，里面当前包含一个可安装插件：

- [ai-startup-compliance-review](/home/witt/harness/ai-compliance-review/claude-code-plugin/ai-startup-compliance-review)

关键文件如下：

- 市场清单：[claude-code-plugin/.claude-plugin/marketplace.json](/home/witt/harness/ai-compliance-review/claude-code-plugin/.claude-plugin/marketplace.json)
- 插件清单：[claude-code-plugin/ai-startup-compliance-review/.claude-plugin/plugin.json](/home/witt/harness/ai-compliance-review/claude-code-plugin/ai-startup-compliance-review/.claude-plugin/plugin.json)
- MCP 配置：[claude-code-plugin/ai-startup-compliance-review/.mcp.json](/home/witt/harness/ai-compliance-review/claude-code-plugin/ai-startup-compliance-review/.mcp.json)
- Skill 目录：[claude-code-plugin/ai-startup-compliance-review/skills/ai-startup-compliance-review](/home/witt/harness/ai-compliance-review/claude-code-plugin/ai-startup-compliance-review/skills/ai-startup-compliance-review)
- 本地语料目录：[claude-code-plugin/ai-startup-compliance-review/legal_preference_txt](/home/witt/harness/ai-compliance-review/claude-code-plugin/ai-startup-compliance-review/legal_preference_txt)

## 二、Claude Code 插件结构说明

当前整理后的结构是：

```text
claude-code-plugin/
├── .claude-plugin/
│   └── marketplace.json
└── ai-startup-compliance-review/
    ├── .claude-plugin/
    │   └── plugin.json
    ├── .mcp.json
    ├── README.md
    ├── legal_preference_txt/
    └── skills/
        └── ai-startup-compliance-review/
            ├── SKILL.md
            ├── references/
            ├── scripts/
            └── agents/
```

含义如下：

- `marketplace.json`：让 Claude Code 把整个 `claude-code-plugin/` 识别为一个本地插件市场
- `plugin.json`：定义单个插件的元数据
- `.mcp.json`：定义插件附带的 MCP 服务
- `skills/`：Claude Code 可加载的 skill
- `legal_preference_txt/`：skill 运行时优先检索的本地语料

## 三、北大法宝 MCP 的配置方式

### 1. 需要配置的环境变量

在启动 Claude Code 之前，先在 shell 中设置以下环境变量：

```bash
export PKULAW_ACCESS_TOKEN="your-access-token"
export PKULAW_LAW_SEARCH_URL="https://apim-gateway.pkulaw.com/..."
export PKULAW_LAW_KEYWORD_URL="https://apim-gateway.pkulaw.com/..."
export PKULAW_CASE_SEMANTIC_URL="https://apim-gateway.pkulaw.com/..."
export PKULAW_LAW_ITEM_URL="https://apim-gateway.pkulaw.com/..."
export PKULAW_CITATION_VALIDATOR_URL="https://apim-gateway.pkulaw.com/..."
```

这些变量会被插件中的 [.mcp.json](/home/witt/harness/ai-compliance-review/claude-code-plugin/ai-startup-compliance-review/.mcp.json) 自动展开，用于填充：

- `url`
- `Authorization: Bearer ...`

也就是说，当前插件不需要你额外写本地 Python MCP server；它走的是远端 HTTP MCP。

### 2. 每个变量的含义

- `PKULAW_ACCESS_TOKEN`
  北大法宝的访问令牌

- `PKULAW_LAW_SEARCH_URL`
  法规语义检索服务 URL

- `PKULAW_LAW_KEYWORD_URL`
  法规关键词检索服务 URL

- `PKULAW_CASE_SEMANTIC_URL`
  案例语义检索服务 URL

- `PKULAW_LAW_ITEM_URL`
  精准法条查询服务 URL

- `PKULAW_CITATION_VALIDATOR_URL`
  法条引用校验服务 URL

### 3. 如何获取北大法宝的真实配置

按你原先 `plugin/CONNECTORS.md` 的约定，真实配置应从北大法宝控制台获取：

1. 获取服务 URL

路径：

`我的应用 -> 选择应用 -> MCP服务购买 -> 配置示例`

对每个已购买服务分别复制真实 URL。

2. 获取访问令牌

路径：

`应用详情页 -> 密钥管理 -> 生成 Token 认证`

生成后写入：

```bash
export PKULAW_ACCESS_TOKEN="your-access-token"
```

### 4. 一个重要注意点

不要直接照抄示例文档中的演示地址。

原因是：

- 不同北大法宝 MCP 服务的 URL 可能和你的购买实例绑定
- 演示 URL 不能保证在你的账号下可用
- 本插件依赖真实服务地址，不做 URL 自动修正

## 四、如何接入 Claude Code

### 1. 启动前确认环境变量已经生效

先在同一个 shell 会话里检查：

```bash
echo "$PKULAW_ACCESS_TOKEN"
echo "$PKULAW_LAW_SEARCH_URL"
echo "$PKULAW_CASE_SEMANTIC_URL"
```

只要是非空，Claude Code 启动后就能读到。

如果你平时通过 `~/.zshrc` 或 `~/.bashrc` 管理环境变量，也可以把这些 `export` 写进去，然后重新打开一个终端。

### 2. 启动 Claude Code

在已经带有上述环境变量的终端中启动 Claude Code。

重点是：

- 先设置环境变量
- 再启动 Claude Code

否则 Claude Code 进程可能拿不到这些值。

### 3. 添加本地插件市场

在 Claude Code 中执行：

```text
/plugin marketplace add /home/witt/harness/ai-compliance-review/claude-code-plugin
```

这一步的作用是把仓库里的 `claude-code-plugin/` 注册成一个本地插件市场。

### 4. 安装插件

执行：

```text
/plugin install ai-startup-compliance-review@ai-compliance-review-local
```

这里：

- `ai-startup-compliance-review` 是插件名
- `ai-compliance-review-local` 是市场名，对应 `marketplace.json` 中的 `name`

### 5. 重新加载插件

安装之后，优先使用：

```text
/reload-plugins
```

如果你的 Claude Code 版本没有这个命令，直接重启 Claude Code 也可以。

建议顺序：

1. 先尝试 `/reload-plugins`
2. 如果插件状态异常，再完全退出并重新打开 Claude Code

## 五、如何验证 skill 已经加载

### 1. 直接触发相关任务

可以直接问 Claude：

```text
帮我做一个 AI 产品上线合规审查框架
```

或者：

```text
帮我评估一个 AI 初创公司的训练数据合规风险
```

如果 skill 触发正常，Claude 的回答会体现出：

- 使用 AI startup compliance review 的审查框架
- 优先从本地语料和结构化阶段指引出发
- 在需要时尝试使用北大法宝 MCP

### 2. 观察 slash picker

如果你当前的 Claude Code 版本会在 slash picker 中显示插件 skill，可以输入：

```text
/ai-startup-compliance-review:
```

如果看到了对应命名空间或相关 skill，说明插件已被识别。

注意：

- 不同版本的 Claude Code 在 UI 上的展示方式可能不同
- 是否出现在 slash picker 不是唯一判断标准
- 最可靠的判断方式仍然是直接触发相关任务，观察行为

## 六、如何验证 MCP 已经加载

### 1. 查看 MCP 列表

在 Claude Code 中执行：

```text
/mcp
```

正常情况下应能看到以下服务：

- `pkulaw-law-search`
- `pkulaw-law-keyword`
- `pkulaw-case-semantic-search`
- `pkulaw-law-item-keyword`
- `pkulaw-citation-validator`

### 2. 实际发起一次检索任务

例如让 Claude 执行一类明显需要法规或案例检索的任务：

```text
帮我检索生成式人工智能产品上线涉及的个人信息保护法相关义务，并给出出处
```

如果 MCP 可用，Claude 在合适时机会调用 PKULAW 工具。

### 3. 常见现象说明

如果 `/mcp` 里能看到服务，但调用失败，常见原因通常是：

- `PKULAW_ACCESS_TOKEN` 没配对
- 服务 URL 配错
- 某个服务未购买
- Claude Code 启动时没有继承到环境变量

## 七、当前插件中 MCP 的声明内容

当前插件在 [.mcp.json](/home/witt/harness/ai-compliance-review/claude-code-plugin/ai-startup-compliance-review/.mcp.json) 中声明了 5 个 HTTP MCP 服务：

1. `pkulaw-law-search`
   用于法规语义检索

2. `pkulaw-law-keyword`
   用于法规关键词检索

3. `pkulaw-case-semantic-search`
   用于案例或执法语义检索

4. `pkulaw-law-item-keyword`
   用于精准法条检索

5. `pkulaw-citation-validator`
   用于法条引用校验

这些服务是“声明即随插件加载”的。

但是否真正可调用，取决于：

- 环境变量是否已配置
- URL 是否真实有效
- token 是否有效
- 你的北大法宝侧是否已开通对应服务

## 八、skill 与本地语料的关系

当前插件不是只加载一个 `SKILL.md`，而是一起带上了：

- `references/`
- `scripts/`
- `legal_preference_txt/`

这是为了保证 skill 在 Claude Code 中是“可用”的，而不只是“被识别”。

skill 的约束已经改成：

- 优先使用插件目录内的 `legal_preference_txt/`
- 在插件环境下用 `${CLAUDE_PLUGIN_ROOT}` 定位脚本和本地语料

也就是说，当前插件已经尽量避免依赖仓库里旧的 `plugin/` 原型目录。

## 九、常见问题排查

### 1. `/plugin marketplace add` 失败

先检查目录是否存在：

```bash
ls /home/witt/harness/ai-compliance-review/claude-code-plugin
```

以及市场文件是否存在：

```bash
ls /home/witt/harness/ai-compliance-review/claude-code-plugin/.claude-plugin/marketplace.json
```

### 2. 插件安装后看不到效果

优先执行：

```text
/reload-plugins
```

如果还不行，完全重启 Claude Code。

### 3. `/mcp` 能看到服务，但无法调用

检查：

```bash
echo "$PKULAW_ACCESS_TOKEN"
echo "$PKULAW_LAW_SEARCH_URL"
echo "$PKULAW_LAW_KEYWORD_URL"
echo "$PKULAW_CASE_SEMANTIC_URL"
echo "$PKULAW_LAW_ITEM_URL"
echo "$PKULAW_CITATION_VALIDATOR_URL"
```

任意一个为空，都可能导致 MCP 实际不可用。

### 4. Claude 不走 PKULAW，只走本地语料

这不一定是错误。

当前 skill 的设计本来就是：

1. 先查本地语料
2. 本地不足时再调用北大法宝 MCP

所以只要本地语料已经足够回答问题，Claude 可能不会主动打 MCP。

### 5. `pkulaw_mcp.py` 为什么没被用到

因为这次接入 Claude Code 走的是插件 `.mcp.json` 方案，不是应用内自己用 `requests` 手工调用远端接口的方案。

所以：

- `pkulaw_mcp.py` 是仓库原型代码
- Claude Code 接入实际使用的是插件目录里的 `.mcp.json`

## 十、建议的实际接入顺序

建议你按下面顺序做：

1. 在 shell 中设置全部 PKULAW 环境变量
2. 启动 Claude Code
3. 执行：

```text
/plugin marketplace add /home/witt/harness/ai-compliance-review/claude-code-plugin
```

4. 执行：

```text
/plugin install ai-startup-compliance-review@ai-compliance-review-local
```

5. 执行：

```text
/reload-plugins
```

如果没有这个命令，就重启 Claude Code

6. 执行：

```text
/mcp
```

确认 5 个 PKULAW 服务已经出现

7. 发送一个合规审查类问题，观察 skill 和 MCP 是否实际参与

## 十一、补充说明

当前仓库里已经有插件内 README：

- [claude-code-plugin/README.md](/home/witt/harness/ai-compliance-review/claude-code-plugin/README.md)
- [claude-code-plugin/ai-startup-compliance-review/README.md](/home/witt/harness/ai-compliance-review/claude-code-plugin/ai-startup-compliance-review/README.md)

但它们主要是插件包内部说明。

本文档的目的，是从“仓库根目录使用者”的视角，把：

- 配置环境变量
- 加入 Claude Code
- 安装插件
- 验证 skill
- 验证 MCP
- 排查失败原因

全部串成一套完整流程。
