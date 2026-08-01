# Agent Case Share MCP Personal Read Tools

This reference documents the MCP contract used by the personal search skill. It does not authorize direct HTTP/API calls.

## Tools

| Tool | Input | Use |
| --- | --- | --- |
| `search_my_content` | `q`, `type` (`case\|asset`), `tag`, `limit` (1-50) | Search the user's cases and assets |
| `list_my_cases` | `q`, `category`, `tag`, `status`, `page`, `limit` (1-50) | Filter personal cases |
| `get_my_case` | `slug` | Read one personal case |
| `list_my_assets` | `q`, `type`, `source`, `status`, `page`, `limit` (1-50) | Filter personal assets |
| `get_my_asset` | `id` | Read one personal asset |
| `get_asset_download_url` | `id` | Resolve a file or source URL |

Tool results are JSON text. Search/list results normally contain `items`; detail results contain `case` or `asset`. Preserve each returned URL, filename, status, slug, and ID exactly.

## Retrieval sequence

1. Call `search_my_content` for broad recall, normally with `limit=5`.
2. Call `get_my_case` or `get_my_asset` for selected results.
3. Call `get_asset_download_url` only when the asset bytes or hosted source are needed.

Extract an opaque slug or ID from a user-provided site URL once. Never derive identifiers from titles, re-encode them, or pass credentials as tool arguments. When MCP is unavailable, report that the personal library cannot be queried until the user connects it.
