# Stage: Retrieval

Use this file before searching or citing local corpus material or 北大法宝 MCP results.

## Local Corpus Base

Search `${CLAUDE_PLUGIN_ROOT}/legal_preference_txt` first when the skill is running from the Claude Code plugin package. If the skill is used standalone instead of as a plugin, search `legal_preference_txt/` first.

Recommended categories:

- `legal_preference_txt/官方文件` -> `[本地法规库]`
- `legal_preference_txt/案例` -> `[本地案例]`
- `legal_preference_txt/论文` -> `[本地论文/报告]`
- `legal_preference_txt/书籍` -> `[本地论文/报告]`

## Search Pattern

Use focused terms from the active scenario:

- Product launch: `生成式人工智能`, `算法推荐`, `个人信息`, `自动化决策`, `安全评估`, `深度合成`
- Data export: `数据出境`, `标准合同`, `个人信息保护影响评估`, `重要数据`, `境外`
- Financing: `知识产权`, `商业秘密`, `训练数据`, `开源`, `合规尽调`, `数据资产`
- Vendor contract: `模型训练`, `数据处理者`, `委托处理`, `输出`, `责任限制`, `删除`
- Marketing: `AI washing`, `误导`, `准确性`, `无偏见`, `宣传`

## Retrieval Sequence

1. Search the local corpus first.
2. If the local corpus is missing a needed regulation, case, or exact article, use 北大法宝 MCP if it is configured.
3. Prefer these MCP services by task:
   - `pkulaw-law-search` or `pkulaw-law-keyword` for regulations.
   - `pkulaw-case-semantic-search` for cases or enforcement examples.
   - `pkulaw-law-item-keyword` for exact article text.
   - `pkulaw-citation-validator` before finalizing specific article citations in a report.
4. If MCP is unavailable or the query still has no support, write `[待核验: 缺少来源支持]`.

## Source Handling

- Prefer official or regulator materials for legal duties.
- Use cases to illustrate enforcement or dispute exposure.
- Use papers/books to explain frameworks, not to assert binding duties.
- Record source path and relevant line/snippet for local results.
- Record server, tool, query or doc id, and retrieval date for 北大法宝 MCP results.
- If retrieval finds no local support and no MCP support, write `[待核验: 缺少来源支持]`.

## Optional Script

Run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/ai-startup-compliance-review/scripts/search_corpus.py ${CLAUDE_PLUGIN_ROOT}/legal_preference_txt --query "生成式人工智能" --query "个人信息" --limit 8
```

Use returned snippets as starting points, not as automatic legal conclusions.
