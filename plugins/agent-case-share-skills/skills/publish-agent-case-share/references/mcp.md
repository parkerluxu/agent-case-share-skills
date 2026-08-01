# Agent Case Share MCP Write Tools

This reference documents the connected MCP write tools. It intentionally omits direct HTTP/API procedures.

## Tools and inputs

| Tool | Required/important fields | Use |
| --- | --- | --- |
| `create_case` | `title`, `summary`; optional case fields, `visibility`, `article*`, `repository*`, `reusableAssets` | Create a case and optional first article |
| `update_case` | `slug`; optional case fields, repositories, assets | Update a user-owned case |
| `create_article` | `title`; optional `content`/`markdown`, `taskSlug`/`taskId`, status | Create an article |
| `update_article` | `slug`; optional title/content/markdown/excerpt/status/order | Update an article |
| `upload_content_image` | `fileBase64`, `fileName`, optional `mimeType` | Upload a Markdown image |
| `upload_asset` | `title`, `type`; optional file and metadata | Attach or upload a reusable asset |
| `upload_user_asset` | `title`, `type`, `fileBase64`, `fileName`; optional metadata | Upload a standalone user asset |
| `update_asset` | `id`; optional metadata and visibility | Update an owned asset |

Supported asset types are `SKILL`, `PROMPT`, `WORKFLOW`, `TEMPLATE`, `MCP_CONFIG`, and `OTHER`. Visibility/status values are `DRAFT`, `PUBLISHED`, and `HIDDEN` where accepted by the tool.

## Publishing rules

- Default AI-created cases to `visibility: "HIDDEN"`.
- Default AI-created articles to `status: "DRAFT"`.
- Default standalone assets to `visibility: "HIDDEN"`.
- Use `PUBLISHED` only after the user explicitly requests public publishing.
- Use `list_categories` before sending an unknown category slug.
- Read local files only to provide Base64, filename, and MIME type to upload tools. Never include credentials in content.

The MCP server does not expose deletion tools. Do not emulate deletion with another protocol; explain the limitation and leave content unchanged. If MCP is disconnected, a tool is missing, or authentication fails, stop before writing and ask the user to connect or reconfigure MCP.
