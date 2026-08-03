# Agent Case Share MCP Write Tools

This reference documents the connected MCP write tools. It intentionally omits direct HTTP/API procedures.

## Tools and inputs

| Tool | Required/important fields | Use |
| --- | --- | --- |
| `create_case` | `title`, `summary`; optional case fields such as `agentStack`, `visibility`, `article*`, `repository*`, `reusableAssets`, `models`, `integrations`, `prompts`, `reproduction` | Create a case, optional first article, attachments, reusable assets, and reproducibility details |
| `update_case` | `slug`; optional case fields, repositories, complete `reusableAssets` target list, `models`, `integrations`, `prompts`, `reproduction` | Update a user-owned case and its reproducibility details |
| `create_article` | `title`; optional `content`/`markdown`, `taskSlug`/`taskId`, status | Create an article |
| `update_article` | `slug`; optional title/content/markdown/excerpt/status/order | Update an article |
| `upload_content_image` | `fileBase64`, `fileName`, optional `mimeType` | Upload a Markdown image |
| `upload_case_attachment` | `caseSlug`, `fileBase64`, `fileName`; optional `mimeType`, `title`, `summary` | Atomically append an attachment to an existing case |
| `delete_case_attachment` | `caseSlug`, `attachmentId` | Atomically delete one case attachment |
| `upload_asset` | `title`, `type`; optional `purpose`, file, and metadata | Prepare an attachment/reusable asset for a new case or upload an asset |
| `upload_user_asset` | `title`, `type`, `fileBase64`, `fileName`; optional metadata | Upload a standalone user asset |
| `update_asset` | `id`; optional `title`, `summary`, `version`, `type`, and visibility/status | Update an owned reusable asset or attachment metadata |

Supported asset types are `SKILL`, `PROMPT`, `WORKFLOW`, `TEMPLATE`, `MCP_CONFIG`, and `OTHER`. `purpose` is `ATTACHMENT` or `REUSABLE`; omit it only when the default `REUSABLE` behavior is intended. Visibility/status values are `DRAFT`, `PUBLISHED`, and `HIDDEN` where accepted by the tool.

## Structured reproducibility fields

- `models`: array of at most 8 records. `modelId` is required; optional fields are `id`, `provider`, `version`, `role`, `purpose`, and `parameters`. `role` is `PRIMARY`, `AUXILIARY`, `EMBEDDING`, `EVALUATION`, or `OTHER`.
- `integrations`: array of at most 16 records. `name` and `type` are required; optional fields are `id`, `version`, `sourceUrl`, `purpose`, and `setupNotes`. `type` is `TOOL`, `MCP`, `PLUGIN`, or `SKILL`. Prefer this structure for tools and integrations; reserve the legacy `tools` string for an optional concise overview.
- `prompts`: array of at most 8 records. `title` and `content` are required; optional fields are `id`, `role`, `summary`, `variables`, `version`, and `visibility`. `role` is `SYSTEM`, `DEVELOPER`, `USER`, `TEMPLATE`, or `OTHER`; `visibility` is `PUBLIC`, `SUMMARY_ONLY`, or `PRIVATE`. Use `SUMMARY_ONLY` unless the author explicitly permits public prompt text.
- `reproduction`: one object, or `null` to clear it. Its optional text fields are `prerequisites`, `steps`, `sampleInput`, `expectedResult`, `sampleOutput`, `knownLimitations`, and `verificationNotes`. `verificationStatus` is `UNVERIFIED`, `AUTHOR_TESTED`, or `COMMUNITY_VERIFIED`; `verifiedAt` must be a date string accepted by `Date.parse`.

Formatting rule: send `workflow` and `reproduction.steps` as newline-separated steps, with one workflow point or action per line. Prefer numbered or bullet lines. Do not send several workflow steps as a single paragraph or an inline comma-/semicolon-separated list; preserving line breaks is required for step recognition.

These fields are optional. Do not fabricate a model version, configuration parameter, installation method, prompt, test result, verification date, or limitation. Redact credentials and sensitive data before publishing.

## Case attachment workflow

- New case: call `upload_asset` with `purpose: "ATTACHMENT"`, then place the returned metadata in `create_case.reusableAssets`.
- Existing case: call `upload_case_attachment`; omit `title` to derive it from the filename.
- Metadata edit: call `update_asset` with the attachment ID and only user-editable fields such as `title`, `summary`, `version`, or visibility/status.
- Single deletion: call `delete_case_attachment` only after explicit confirmation of the case slug and attachment ID. It deletes the attachment record while stored-object retention follows the website's storage policy; its result includes `deleted`, `attachmentId`, `taskSlug`, and `taskUrl`.
- Download: obtain the attachment ID from `get_case` or `get_my_case`, then call `get_asset_download_url`.

`update_case.reusableAssets` has full replacement semantics: when present, items omitted from the list are removed. Use the dedicated atomic tools for ordinary attachment changes. Attachments are returned under `attachments`, remain outside asset search/list results, and share a maximum of eight records per case with reusable assets.

Accepted uploaded file extensions are `.zip`, `.md`, `.txt`, `.json`, `.yaml`, `.yml`, `.csv`, `.tsv`, and `.log`; the server enforces its configured size limit.

## Publishing rules

- Default AI-created cases to `visibility: "HIDDEN"`.
- Default AI-created articles to `status: "DRAFT"`.
- Default standalone assets to `visibility: "HIDDEN"`.
- Use `PUBLISHED` only after the user explicitly requests public publishing.
- Use `list_categories` before sending an unknown category slug.
- Read local files only to provide Base64, filename, and MIME type to upload tools. Never include credentials in content.

Only case-attachment deletion is exposed. Do not emulate deletion of cases, articles, or reusable assets with another protocol. If MCP is disconnected, a tool is missing, or authentication fails, stop before writing and ask the user to connect or reconfigure MCP.
