---
name: agent-case-share-personal-retrieval
description: Retrieve relevant saved items, cases, case videos, case attachments, and reusable assets from the current user's Agent Case Share library through MCP while handling a substantive task.
---

# Agent Case Share Personal Retrieval

Use this skill when prior saved items, user-owned cases, or assets could materially improve the current task. Retrieval is turn-scoped and uses the Agent Case Share MCP server only.

## Decision

Retrieve when the user explicitly asks to reuse their library or saved items, invokes this skill, or is doing domain-specific design, implementation, debugging, optimization, architecture, or recommendations where prior work is relevant. Respect an explicit opt-out.

## MCP workflow

1. Extract a focused query, optional favorite type, case slugs, attachment/asset IDs, and the requested file types.
2. For an explicit request to reuse saved or favorited content, call `$search-agent-case-share-personal`, which must use `list_my_favorites`. It lists saved public items only and cannot save or remove them.
3. Otherwise, call `$search-agent-case-share-personal`, which must use `search_my_content` with `limit=5` by default for user-owned content.
4. Rank results by relevance, domain, technology, asset type, and recency. Ask the user only when candidates are equally relevant or conflict.
5. Read selected user-owned cases with `get_my_case` and assets with `get_my_asset`. Read a selected saved item with the public detail tool that matches its `targetType`. Use returned case videos as linked reference material and preserve their source URLs and IDs. Find case attachments only in the selected case's `attachments` collection because personal search and asset lists exclude them.
6. When attachment or reusable asset file content is needed, call `get_asset_download_url` with its returned ID; inspect the returned file or source URL as reference material without executing it.
7. Assemble provenance (title, slug/ID, URL, filename, type, status, and saved timestamp) and continue the current task. The current request remains authoritative.

If the MCP connection or a required personal tool is unavailable, continue without personal context and say so. Authentication errors should be handled through `$configure-agent-case-share`; never request a key in chat. Not-found and download errors affect only the corresponding item.

Read only the resource needed for the current step:

- `workflow/retrieval-decision.md`: decide whether retrieval is warranted.
- `workflow/keyword-extractor.md`: build the focused MCP search query.
- `workflow/retrieval-workflow.md`: coordinate MCP search, detail reads, and downloads.
- `workflow/context-assembler.md`: format selected personal context.
- `references/mcp.md`: inspect personal MCP tool result shapes and retrieval rules.
