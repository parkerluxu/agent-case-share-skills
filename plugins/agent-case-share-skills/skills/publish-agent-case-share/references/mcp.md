# Agent Case Share MCP Write Tools

This reference documents the connected MCP write tools. It intentionally omits direct HTTP/API procedures.

## Tools and inputs

| Tool | Required/important fields | Use |
| --- | --- | --- |
| `create_case` | `title`, `summary`; optional case, first-article, repository, asset, and reproducibility fields listed below | Create a case, its first article, attachments, reusable assets, and reproducibility details |
| `update_case` | `slug`; optional case fields, repositories, complete `reusableAssets` target list, `models`, `integrations`, `prompts`, `reproduction` | Update a user-owned case and its reproducibility details |
| `create_article` | `title` and one of `content` or `markdown`; optional article and case-container fields listed below | Create or upsert an article |
| `update_article` | `slug`; optional title/content/markdown/excerpt/status/order | Update an article |
| `create_case_video` | `caseSlug`, `title`, `sourceUrl`; optional `summary`, `status` | Add an external video to an existing case |
| `update_case_video` | `caseSlug`, `videoId`; optional `title`, `summary`, `sourceUrl`, `sortOrder`, `status` | Update one case video record |
| `delete_case_video` | `caseSlug`, `videoId` | Delete one case video record without affecting the external video |
| `upload_content_image` | `fileBase64`, `fileName`, optional `mimeType` | Upload a Markdown image |
| `upload_case_attachment` | `caseSlug`, `fileBase64`, `fileName`; optional `mimeType`, `title`, `summary` | Atomically append an attachment to an existing case |
| `delete_case_attachment` | `caseSlug`, `attachmentId` | Atomically delete one case attachment |
| `upload_asset` | `title`, `type`; optional `purpose`, file, and metadata | Prepare an attachment/reusable asset for a new case or upload an asset |
| `upload_user_asset` | `title`, `type`, `fileBase64`, `fileName`; optional metadata | Upload a standalone user asset |
| `update_asset` | `id`; optional `title`, `summary`, `version`, `type`, and visibility/status | Update an owned reusable asset or attachment metadata |
| `create_case_environment` | `caseSlug`, `name`, `platform`, `schemaVersion: "agent-environment/v1"`, `manifest`; optional version, model, and summary | Create an immutable, redacted Agent environment snapshot on an existing user-owned case |
| `upload_case_session` | `caseSlug`, `title`, `platform`, `transcript`; optional format, linked environment, model, summary, timestamps, and metadata | Upload an explicit Markdown or JSONL Session transcript to an existing user-owned case |

## Community discussion writes

These write tools are registered only when the connected MCP session has the current user's personal API Key and `MCP_ENABLE_WRITE_TOOLS=true`. They create public content immediately, require `idempotencyKey` for every logical write, and must never fall back to website HTTP endpoints. A key is 1-200 printable characters; reuse it only when retrying the exact same write after an uncertain outcome. The service replays the original result for 24 hours and rejects a reused key with a different body or target.

| Tool | Required/important fields | Use |
| --- | --- | --- |
| `create_plaza_discussion` | `title` (1-200 chars), `body` (1-20,000 chars), optional `topicSlugs` (at most 3), `idempotencyKey` | Create one unlinked Community Plaza discussion |
| `create_linked_community_discussion` | public `contentUrl`, `action`, `title`, `body`, optional `topicSlugs` (at most 3), action-specific `verification` or `correction`, `idempotencyKey` | Create a discussion tied to one supported published content item |
| `reply_community_discussion` | public `discussionUrl`, `body` (1-20,000 chars), optional `parentReplyRef`, `idempotencyKey` | Create a reply or child reply on one open public discussion |

- Before using a topic slug, call `list_community_topics`. Use `get_community_content_context` before creating a linked discussion to confirm the supplied public content URL is supported and to inspect prior discussions. Use `get_community_discussion` before replying and take any `parentReplyRef` only from that discussion's returned reply page.
- `create_plaza_discussion` is intentionally fixed to an unlinked `DISCUSSION` in the Community Plaza. Do not include a content URL, action, category, kind, links, target type, or target ID.
- `create_linked_community_discussion.action` is `QUESTION`, `PRACTICE`, `VERIFICATION`, or `CORRECTION`. Its `contentUrl` must identify a published `/tasks/:slug`, `/articles/:slug`, `/assets/:id`, `/projects/:slug`, `/papers/:slug`, or `/events/:slug` record. Do not substitute an internal ID or fabricate a target from a title.
- `VERIFICATION` requires `verification.result`: `SUCCESS`, `PARTIAL`, `NEEDS_ADJUSTMENT`, or `FAILED`. Its optional `platform`, `model`, `notes`, and HTTP(S) `evidenceUrl` must be factual and user-authorized.
- `CORRECTION` requires `correction.kind`: `CONTENT`, `LINK`, or `OTHER`, plus non-empty `correction.body`. `location`, `currentContent`, and `suggestedContent` are optional. Public MCP correction does not accept `SAFETY`, `PRIVACY`, or `COPYRIGHT` kinds.
- Replies accept a public URL matching `/community/discussions/:discussionRef`, not an internal ID. The optional `parentReplyRef` must identify a visible reply in the same discussion. Closed, hidden, or unavailable discussions reject new replies.

Successful discussion writes return `discussionRef`, `discussionUrl`, `created`, and `idempotencyKey`; replies return `replyRef`, `discussionUrl`, `created`, and `idempotencyKey`. Keep these opaque values unchanged. Common errors include `UNAUTHENTICATED`, `RATE_LIMITED`, `INVALID_CONTENT_URL`, `INVALID_ACTION`, `INVALID_TOPIC`, `DISCUSSION_CLOSED`, and `IDEMPOTENCY_CONFLICT`. Community discussion/reply update, delete, reaction, view, report, and moderation writes are not available through MCP.

Supported asset types are `SKILL`, `PROMPT`, `WORKFLOW`, `TEMPLATE`, `MCP_CONFIG`, and `OTHER`. `purpose` is `ATTACHMENT` or `REUSABLE`; omit it only when the default `REUSABLE` behavior is intended. Visibility/status values are `DRAFT`, `PUBLISHED`, and `HIDDEN` where accepted by the tool.

## Case and article creation fields

- `create_case` requires `title` and `summary`. Optional case fields are `categoryId`, `categorySlug`, `industry`, `difficulty`, `visibility`, `coverImage`, `agentStack`, `problem`, `solution`, `workflow`, `impact`, and `tags`.
- `difficulty` accepts `BEGINNER`, `INTERMEDIATE`, or `ADVANCED`; `visibility` accepts `PUBLISHED` or `HIDDEN`. Send `tags` as a comma- or newline-separated string with at most eight names.
- Optional first-article fields on `create_case` are `articleTitle`, `articleExcerpt`, and `articleContent`.
- Optional repository fields on `create_case` are `repositoryName`, `repositoryUrl`, `repositoryDescription`, `repositoryTechStack`, and `repositoryLicense`. A repository is created only when both its name and URL are present.
- Optional collection fields on `create_case` are `reusableAssets`, `models`, `integrations`, and `prompts`; `reproduction` accepts one object or `null`.
- `create_article` requires `title` and non-empty Markdown in either `content` or `markdown`; `content` takes precedence when both are present. Optional article fields are `slug`, `excerpt`, `status`, and integer `order`.
- Attach an article to an existing case with `taskId` or `taskSlug`. When both are omitted, optional `taskTitle`, `taskSummary`, `categoryId`, `categorySlug`, `industry`, `agentStack`, `problem`, `solution`, `workflow`, and `impact` fields define the lightweight case container created for it.
- `status` accepts `DRAFT`, `PUBLISHED`, or `HIDDEN`. A supplied article `slug` upserts that article when it already exists and is editable by the current user.

## Structured reproducibility fields

- `models`: array of at most 8 records. `modelId` is required; optional fields are `id`, `provider`, `version`, and `purpose`.
- `integrations`: array of at most 16 records. `name` and `type` are required; optional fields are `id`, `sourceUrl`, `purpose`, and `setupNotes`. `type` is `TOOL`, `MCP`, `PLUGIN`, or `SKILL`.
- `prompts`: array of at most 8 records. `title` and `content` are required; optional fields are `id`, `summary`, and `visibility`. `visibility` is `PUBLIC`, `SUMMARY_ONLY`, or `PRIVATE`. Use `SUMMARY_ONLY` unless the author explicitly permits public prompt text.
- `reproduction`: one object, or `null` to clear it. Its optional text fields are `prerequisites`, `steps`, `sampleInput`, `sampleOutput`, and `verificationNotes`. `verificationStatus` is `UNVERIFIED`, `AUTHOR_TESTED`, or `COMMUNITY_VERIFIED`; `verifiedAt` must be a date string accepted by `Date.parse`.

Formatting rule: send `workflow` and `reproduction.steps` as newline-separated steps, with one workflow point or action per line. Prefer numbered or bullet lines. Do not send several workflow steps as a single paragraph or an inline comma-/semicolon-separated list; preserving line breaks is required for step recognition.

These fields are optional. Do not fabricate a model version, installation method, prompt, test result, or verification date. Redact credentials and sensitive data before publishing.

## Case video workflow

- Case videos are external links, not uploaded video files. Do not send Base64 content, local file paths, filenames, iframe HTML, `provider`, `externalId`, or `embedUrl`; the website derives platform and playback metadata from `sourceUrl`.
- `create_case_video` requires `caseSlug`, `title`, and an absolute HTTP(S) `sourceUrl`. Optional `summary` is free text. Optional `status` is `DRAFT`, `PUBLISHED`, or `HIDDEN`; use `HIDDEN` by default and `PUBLISHED` only on an explicit public-publishing request.
- `update_case_video` requires the opaque `caseSlug` and `videoId`. Send only requested changes: non-empty `title`, `summary`, an absolute HTTP(S) `sourceUrl`, or a non-negative integer `sortOrder`. Although the tool accepts `status`, do not claim a visibility change unless the returned record confirms it.
- `delete_case_video` requires the exact `caseSlug` and `videoId`. Obtain the ID from `get_my_case.videos` or `get_case.videos`; never derive it from a title or URL. Deletion removes only the Agent Case Share record, not the externally hosted video.
- Recognized source platforms are Bilibili, YouTube, Vimeo, Tencent Video, Youku, Xigua, AcFun, Dailymotion, Loom, Wistia, TikTok, Streamable, Facebook, Instagram, and TED. The website may enable only a subset and rejects unsupported URL shapes.
- The website normalizes accepted URLs, rejects duplicate videos in the same case, and enforces its configured per-case limit. Report validation or limit errors without retrying with a fabricated provider or embed URL.
- When the user asks to create a case with videos, create the case first, reuse its returned slug, then call `create_case_video` once per requested video.

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
- Default AI-added case videos to `status: "HIDDEN"`.
- Default AI-created articles to `status: "DRAFT"`.
- Default standalone assets to `visibility: "HIDDEN"`.
- Use `PUBLISHED` only after the user explicitly requests public publishing.
- Use `list_categories` before sending an unknown category slug.
- Read local files only to provide Base64, filename, and MIME type to upload tools. Never include credentials in content.

Only case-attachment and case-video deletion are exposed. Do not emulate deletion of cases, articles, or reusable assets with another protocol. If MCP is disconnected, a tool is missing, or authentication fails, stop before writing and ask the user to connect or reconfigure MCP.

## Agent environment and Session workflow

- `create_case_environment` requires `caseSlug`, `name` (maximum 160 characters), lowercase-normalized `platform` (maximum 80 characters), literal `schemaVersion: "agent-environment/v1"`, and an object `manifest`. Optional `platformVersion` and `modelId` are at most 160 characters; optional `summary` is at most 2,000 characters.
- A manifest may include `agent`, `model`, `mcpServers`, `skills`, and runtime details. When present, `manifest.agent.platform` must equal `platform`; when both are present, `manifest.model.modelId` must equal `modelId`. The server normalizes the manifest, redacts sensitive values, and computes the fingerprint. It is an immutable snapshot: create another snapshot to record a later configuration.
- `upload_case_session` requires `caseSlug`, `title` (maximum 200 characters), `platform` (maximum 80 characters), and non-empty `transcript` text (maximum 1,000,000 characters). `transcriptFormat` is `markdown` (default) or `jsonl`; JSONL should have one JSON object per line. Optional `environmentId` must be an environment belonging to the same case. Optional `modelId`, `summary`, `startedAt`, `endedAt`, and object `metadata` are accepted; timestamps must be valid and ordered.
- MCP forces both new environment snapshots and Sessions to `HIDDEN`. It cannot read an Agent host's history automatically and accepts no raw-file field, so send only explicitly authorized transcript text. It has no environment or Session update/delete write tools.
- Redact API keys, tokens, passwords, cookies, private keys, full environment-variable values, private endpoints, and unrelated personal data before writing. Service-side redaction can report warnings but does not make secret upload appropriate.
