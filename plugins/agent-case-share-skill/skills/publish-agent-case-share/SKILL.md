---
name: publish-agent-case-share
description: Publish, edit, or delete tasks/cases, articles/tutorials, Markdown images, and reusable assets on Agent Case Share using HTTP APIs. Use when the user asks Codex, Claude Code, Gemini CLI, or another AI coding agent to upload, create, publish, draft, edit, update, revise, delete, or sync Agent Case Share tasks, cases, tutorials, articles, Markdown images, standalone user assets, case-attached reusable assets, or asset metadata.
---

# Publish to Agent Case Share

Use this skill to publish content to the Agent Case Share platform.

## Safety

- Never ask for the user's password.
- Use `https://agentcaseshare.cn/` as the default base URL; ask only for a different site if the user mentions one.
- Ask for the personal API key if it is missing.
- Treat the API key as a secret. Do not print it, commit it, log it, or include it in generated files.
- Default AI-generated tasks to `visibility: "HIDDEN"`.
- Default AI-generated articles to `status: "DRAFT"`.
- Default AI-generated standalone user assets to `visibility: "HIDDEN"`.
- Only publish publicly when the user explicitly asks.

## Inputs

Confirm:

- Base URL, default `https://agentcaseshare.cn/`
- Personal API key generated from `/profile`
- Whether the user wants to create, edit, or delete a task/case, article/tutorial, Markdown image, case-attached reusable asset, standalone user asset, asset metadata, or a combination

## Reference

For endpoint fields, payload examples, responses, and error handling, read:

- `references/api.md`

## Slug Handling

- Let the API generate slugs for new content. New case slugs use `case-xxxxxxxx`; new article slugs use `article-xxxxxxxx`.
- Omit `slug` when creating a new article. Supplying `slug` targets that normalized ASCII slug and can update an existing manageable article.
- Treat returned `slug` and `taskSlug` values as opaque identifiers; do not derive them from titles.
- Use returned `url` and `taskUrl` values directly because they are already percent-encoded.
- When constructing `PATCH` or `DELETE` paths from a raw slug, encode the path segment exactly once with `encodeURIComponent`. Decode an already encoded URL segment once before rebuilding a path.

## Workflow

1. Classify the request:
   - Markdown content image upload -> `POST /api/content-images`
   - Case-attached reusable asset draft -> `POST /api/assets`
   - Standalone user asset upload -> `POST /api/assets/user`
   - Compatibility standalone asset upload -> `POST /api/assets` with `publishAsset=true`
   - Asset metadata editing -> `PATCH /api/assets/:id`
   - Case/task publishing -> `POST /api/tasks`
   - Case/task editing -> `PATCH /api/tasks/:slug`
   - Case/task deletion -> `DELETE /api/tasks/:slug` when a signed-in browser session is available
   - Article/tutorial publishing -> `POST /api/articles`
   - Article/tutorial editing -> `PATCH /api/articles/:slug`
   - Article/tutorial deletion -> `DELETE /api/articles/:slug`
2. If Markdown contains local image paths, upload each image first and replace local paths with returned URLs.
3. Normalize content into the required payload.
4. Resolve the base URL from `AGENT_CASE_SHARE_BASE_URL`, the user, or default to `https://agentcaseshare.cn/`.
5. Use `Authorization: Bearer <personal-api-key>`.
6. Use hidden/draft defaults unless the user requested public publishing.
7. For assets that should appear on a case, upload files to `POST /api/assets` first and place returned draft `asset` objects into `reusableAssets` when creating or updating the task.
8. For assets that should exist in the user's asset library independent of a case, upload files to `POST /api/assets/user` and report the returned `asset.id`.
9. For editing existing asset metadata, send only fields that should change to `PATCH /api/assets/:id`; do not try to replace the uploaded file through this endpoint.
10. For deletion, confirm the target slug/id and use the relevant `DELETE` endpoint only when the user explicitly asks to delete.
11. After success, report returned `slug`, `url`, `taskSlug`, `taskUrl`, `asset.id`, or `asset.url`.
12. On API failure, show the returned `error` message and ask whether to revise and retry.

## Content Mapping

For a task/case:

- `title`: concise case title
- `summary`: short business problem and agent result
- `categorySlug`: choose a visible industry category slug from `/api/categories`; use the default category table in `references/api.md` when live discovery is unavailable
- `industry`: optional display name fallback; prefer matching the selected category name
- `visibility`: default `HIDDEN`; use `PUBLISHED` only when requested
- `coverImage`: optional case cover URL, recommended ratio 7:4
- `tags`: comma-separated tags
- `agentStack`: tools/frameworks/stack
- `problem`, `solution`, `workflow`, `impact`: map from the user's notes
- `articleTitle`, `articleContent`: include when the user wants an initial recap article
- `reusableAssets`: include asset objects returned by `POST /api/assets`

For a standalone user asset:

- Use `POST /api/assets/user`.
- `file`: local file to upload
- `title`: concise reusable asset title
- `type`: one of `SKILL`, `PROMPT`, `WORKFLOW`, `TEMPLATE`, `MCP_CONFIG`, `OTHER`
- `summary`: optional reuse guidance
- `version`: optional version label
- `visibility`: default `HIDDEN`; use `PUBLISHED` only when requested
- Do not put standalone user asset responses into a task's `reusableAssets`; use draft assets from `POST /api/assets` for case attachment.

For editing an existing reusable asset:

- Infer the asset `id` from `/assets/:id`, `/api/assets/:id/download`, a personal asset lookup, or the user's provided id.
- Use `PATCH /api/assets/:id`.
- Send only metadata fields that should change.
- Editable fields: `title`, `type`, `summary`, `version`, `visibility` or `status`.
- This endpoint does not replace the uploaded file; upload a new asset if the binary content must change.

For editing an existing task/case:

- Infer the slug from the task URL when possible.
- Use `PATCH /api/tasks/:slug`.
- Send only fields that should change.
- Include `status` when changing visibility: `{ "status": "HIDDEN" }` or `{ "status": "PUBLISHED" }`.
- Omit `repositories` and `reusableAssets` unless replacing the full target list.
- Use `DELETE /api/tasks/:slug` only when the user explicitly asks to delete a case. This endpoint requires a signed-in browser session and returns `{ "url": "/profile" }` on success.

For an article/tutorial:

- `title`: article title
- `content` or `markdown`: Markdown body
- `status`: default `DRAFT`; use `PUBLISHED` only when requested
- `taskSlug` or `taskId`: include when attaching to an existing task
- `taskTitle` and `taskSummary`: include when no existing task is provided and the API should create a lightweight task container
- Omit `slug` for a new article so the API generates an `article-xxxxxxxx` identifier; send a known existing slug only when intentionally updating through `POST /api/articles`

For editing an existing article/tutorial:

- Infer the slug from the article URL when possible.
- Use `PATCH /api/articles/:slug`.
- Send only fields that should change.
- Use `taskSlug` only when moving the article to another existing case.
- Use `DELETE /api/articles/:slug` only when the user explicitly asks to delete an article. It returns the parent `taskSlug` and `taskUrl` on success.

## Public Publishing Rule

If the user says "publish publicly", "make it public", or gives an explicit production publishing instruction:

- Task: `visibility: "PUBLISHED"` or edit with `status: "PUBLISHED"`
- Article: `status: "PUBLISHED"`
- Standalone user asset: `visibility: "PUBLISHED"`

Otherwise keep AI-created content hidden/draft.
