# AI Startup Compliance Review Plugin

This directory is an installable Claude Code plugin package. It exposes:

- the `ai-startup-compliance-review` skill
- five optional PKULAW MCP connectors
- a plugin-packaged local corpus under `legal_preference_txt/`

This package does not use the repository's Streamlit UI, local LLM wrappers, or `pkulaw_mcp.py`.

## Directory Shape

```text
ai-startup-compliance-review/
├── .claude-plugin/plugin.json
├── .mcp.json
├── README.md
├── legal_preference_txt/
└── skills/
    └── ai-startup-compliance-review/
```

## Install In Claude Code

1. Add the local marketplace root:

```text
/plugin marketplace add /home/witt/harness/ai-compliance-review/claude-code-plugin
```

2. Install the plugin from that marketplace:

```text
/plugin install ai-startup-compliance-review@ai-compliance-review-local
```

3. Restart Claude Code. Plugin skills and MCP declarations are not reliably available until restart.

## Configure PKULAW MCP

Set the required environment variables before starting Claude Code:

```bash
export PKULAW_ACCESS_TOKEN="your-access-token"
export PKULAW_LAW_SEARCH_URL="https://apim-gateway.pkulaw.com/..."
export PKULAW_LAW_KEYWORD_URL="https://apim-gateway.pkulaw.com/..."
export PKULAW_CASE_SEMANTIC_URL="https://apim-gateway.pkulaw.com/..."
export PKULAW_LAW_ITEM_URL="https://apim-gateway.pkulaw.com/..."
export PKULAW_CITATION_VALIDATOR_URL="https://apim-gateway.pkulaw.com/..."
```

Use the real per-service URLs from the PKULAW console. Do not copy demo URLs blindly.

If these variables are unset, Claude Code can still install the plugin and load the skill, but the PKULAW MCP servers will not be usable.

## Verify Load

### Verify the skill

- Ask a prompt that should match the skill, for example: `帮我做一个 AI 产品上线合规审查框架`.
- If your Claude Code build exposes plugin skills in the slash picker, confirm the plugin namespace also appears there after restart.

### Verify MCP

- Run `/mcp` and confirm the following servers appear:
  - `pkulaw-law-search`
  - `pkulaw-law-keyword`
  - `pkulaw-case-semantic-search`
  - `pkulaw-law-item-keyword`
  - `pkulaw-citation-validator`
- Trigger a retrieval task after setting the environment variables and confirm Claude can call the tool successfully.

## Notes

- The skill is designed to search the plugin-packaged `legal_preference_txt/` corpus first.
- This package currently exposes a plugin skill, not a separate `commands/` directory.
- PKULAW MCP is an optional enhancement layer, not final legal verification.
- All outputs remain draft compliance review work product for human verification.
