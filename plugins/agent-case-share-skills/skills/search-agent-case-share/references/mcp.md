# Agent Case Share MCP Read Tools

This reference intentionally documents MCP tools, not the website's HTTP API. Skills must call the connected `agent-case-share` MCP server and must not construct network requests themselves.

## Public read tools

| Tool | Input | Use |
| --- | --- | --- |
| `search_content` | `q`, `type` (`task\|article\|asset\|news\|project\|paper`), `tag`, `category`, `limit` (1-50) | Search published content |
| `list_cases` | `q`, `category`, `tag`, `status`, `page`, `limit` (1-50) | List/filter cases |
| `get_case` | `slug` | Read a case and related content |
| `get_article` | `slug` | Read article/tutorial Markdown |
| `get_project` | `slug` | Read an open-source project |
| `get_paper` | `slug` | Read a paper |
| `list_categories` | none | List visible categories |
| `list_tags` | `q`, `limit` (1-100) | Find tags |
| `list_assets` | `q`, `type`, `source`, `category`, `featured`, `status`, `page`, `limit` (1-50) | List reusable assets |
| `get_asset` | `id` | Read an asset |
| `get_asset_download_url` | `id` | Resolve a file or source URL |

The tool result is JSON text. Inspect its `items` list or the relevant `case`, `article`, `project`, `paper`, or `asset` object. Keep returned URLs, slugs, and IDs unchanged.

## Selection rules

- Start broad searches with `limit=10`.
- Use `list_categories` before filtering by an unknown category.
- Use `list_tags` before filtering by an unknown tag.
- Use `get_case` for complete case context; use `get_article` for article Markdown.
- Use `get_asset_download_url` when the user asks for the actual asset file. Do not fetch a download URL directly from the skill.

## Connection and errors

The client must already have a connected Agent Case Share MCP server. A missing connection or tool is a configuration issue, not a reason to use a direct API. Report authentication, validation, not-found, and download errors without exposing credentials, then suggest reconnecting MCP or refining the query.
