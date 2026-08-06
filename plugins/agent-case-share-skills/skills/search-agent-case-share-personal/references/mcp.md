# Agent Case Share MCP Personal Read Tools

This reference documents the MCP contract used by the personal search skill. It does not authorize direct HTTP/API calls.

## Tools

| Tool | Input | Use |
| --- | --- | --- |
| `search_my_content` | `q`, `type` (`case\|asset`), `tag`, `limit` (1-50) | Search the user's cases and assets |
| `list_my_favorites` | `q`, `type` (`TASK\|ARTICLE\|REUSABLE_ASSET\|OPEN_SOURCE_PROJECT\|PAPER`), `page`, `limit` (1-50) | List the user's saved content that is currently public, newest saved first |
| `list_my_cases` | `q`, `category`, `tag`, `status`, `page`, `limit` (1-50) | Filter personal cases |
| `get_my_case` | `slug` | Read one personal case with videos, separate attachments and reusable assets, plus models, integrations, prompts, and reproduction details |
| `list_my_assets` | `q`, `type`, `source`, `status`, `page`, `limit` (1-50) | Filter personal assets |
| `get_my_asset` | `id` | Read one personal asset |
| `get_case`, `get_article`, `get_asset`, `get_project`, `get_paper` | Opaque `slug` or `id` | Read the public details of a selected saved item, chosen by its `targetType` |
| `get_asset_download_url` | `id` | Resolve a file or source URL |

Tool results are JSON text. Search/list results normally contain `items`; detail results contain the requested object. `list_my_favorites` returns `{items, page, limit, total, hasMore}`. Each item has `targetType`, `targetId`, `title`, `summary`, `href`, and ISO `savedAt`; it is a lightweight record, so read the public detail with the matching tool when more context is required. Case detail returns `videos`, `attachments` separately from `reusableAssets`, and may include `models`, `integrations`, `prompts`, and `reproduction`. Video records can include `id`, `title`, `summary`, `sourceUrl`, `embedUrl`, `provider`, `externalId`, `sortOrder`, `status`, and `updatedAt`. Preserve each returned URL, filename, status, slug, ID, and saved timestamp exactly.

## Retrieval sequence

1. Call `list_my_favorites` when the request is about saved or favorited content; it is read-only and does not save or remove items.
2. Call `search_my_content` for broad recall of user-owned content, normally with `limit=5`.
3. Call `get_my_case` or `get_my_asset` for selected user-owned results. For a selected saved item, use its `targetType` to select the matching public detail tool.
4. Find case attachments in case detail; personal search and asset lists intentionally exclude them.
5. Call `get_asset_download_url` with a reusable asset or attachment ID only when its file or hosted source is needed.

Extract an opaque slug or ID from a user-provided site URL once. Never derive identifiers from titles, re-encode them, or pass credentials as tool arguments. When MCP is unavailable, report that the personal library cannot be queried until the user connects it.
