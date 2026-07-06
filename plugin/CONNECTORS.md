# 连接器

## 北大法宝 MCP

本插件默认声明了 5 个北大法宝 MCP 连接器，用于增强法规、案例和法条检索能力：

- `pkulaw-law-search`：法规语义检索
- `pkulaw-law-keyword`：法规关键词检索
- `pkulaw-case-semantic-search`：案例语义检索
- `pkulaw-law-item-keyword`：精准法条查询
- `pkulaw-citation-validator`：法条引用校验

这些连接器是可选增强。未配置时，skill 仍可仅依赖本地语料和 `[待核验]` 标签运行。

## 配置方式

`.mcp.json` 使用以下环境变量：

- `PKULAW_ACCESS_TOKEN`
- `PKULAW_LAW_SEARCH_URL`
- `PKULAW_LAW_KEYWORD_URL`
- `PKULAW_CASE_SEMANTIC_URL`
- `PKULAW_LAW_ITEM_URL`
- `PKULAW_CITATION_VALIDATOR_URL`

## 如何获取真实配置

### 1. 获取服务 URL

在北大法宝控制台中依次进入：

`我的应用 -> 选择应用 -> MCP服务购买 -> 配置示例`

对每个已购买服务分别复制真实 URL。

不要直接照抄官方文档里的演示地址。官方文档明确说明每个服务 URL 与购买实例绑定，应以控制台中的“配置示例”为准。

### 2. 获取访问令牌

在北大法宝控制台中依次进入：

`应用详情页 -> 密钥管理 -> 生成 Token 认证`

生成后，将令牌写入：

```bash
export PKULAW_ACCESS_TOKEN="your-access-token"
```

## 默认 URL 对应关系

将控制台中的真实服务 URL 分别写入：

```bash
export PKULAW_LAW_SEARCH_URL="https://apim-gateway.pkulaw.com/..."
export PKULAW_LAW_KEYWORD_URL="https://apim-gateway.pkulaw.com/..."
export PKULAW_CASE_SEMANTIC_URL="https://apim-gateway.pkulaw.com/..."
export PKULAW_LAW_ITEM_URL="https://apim-gateway.pkulaw.com/..."
export PKULAW_CITATION_VALIDATOR_URL="https://apim-gateway.pkulaw.com/..."
```

## 平台差异说明

- 北大法宝官方文档中的 Dify 示例要求在 URL 末尾追加 `/mcp`，这只适用于 Dify，不适用于本插件。
- 本插件的 `.mcp.json` 采用远端 HTTP MCP 配置，不需要额外本地服务进程。
- 连接器“已声明”不等于“已连通”。只有真实工具调用成功后，才能把北大法宝 MCP 视为可用。

## 可选扩展

北大法宝官方文档还列出了 4 个可选服务，本插件默认未声明：

- 案例关键词检索
- 法条识别与溯源
- 案号识别与溯源
- 法宝超链

如后续需要，可按同样模式增补到 `.mcp.json`。
