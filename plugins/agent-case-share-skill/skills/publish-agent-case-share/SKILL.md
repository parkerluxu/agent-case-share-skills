---
name: publish-agent-case-share
description: Publish or edit tasks/cases and articles/tutorials on Agent Case Share using HTTP APIs. Use when the user asks Codex, Claude Code, Gemini CLI, or another AI coding agent to upload, create, publish, draft, edit, update, revise, or sync Agent Case Share tasks, cases, tutorials, articles, Markdown images, or reusable assets.
---

# Publish to Agent Case Share

Use this skill to publish content to the Agent Case Share platform.

## Safety

- Never ask for the user's password.
- Ask for the site base URL and personal API key if they are missing.
- Treat the API key as a secret. Do not print it, commit it, log it, or include it in generated files.
- Default AI-generated tasks to `visibility: "HIDDEN"`.
- Default AI-generated articles to `status: "DRAFT"`.
- Only publish publicly when the user explicitly asks.

## Inputs

Confirm:

- Base URL, for example `https://your-domain.com`
- Personal API key generated from `/profile`
- Whether the user wants to create or edit a task/case, article/tutorial, Markdown image, reusable asset, or a combination

## Reference

For endpoint fields, payload examples, responses, and error handling, read:

- `references/api.md`

## Workflow

1. Classify the request:
   - Markdown content image upload -> `POST /api/content-images`
   - Reusable asset upload -> `POST /api/assets`
   - Case/task publishing -> `POST /api/tasks`
   - Case/task editing -> `PATCH /api/tasks/:slug`
   - Article/tutorial publishing -> `POST /api/articles`
   - Article/tutorial editing -> `PATCH /api/articles/:slug`
2. If Markdown contains local image paths, upload each image first and replace local paths with returned URLs.
3. Normalize content into the required payload.
4. Use `Authorization: Bearer <personal-api-key>`.
5. Use hidden/draft defaults unless the user requested public publishing.
6. For reusable assets, upload files first and place returned `asset` objects into `reusableAssets` when creating or updating the task.
7. After success, report returned `slug`, `url`, `taskSlug`, or `taskUrl`.
8. On API failure, show the returned `error` message and ask whether to revise and retry.

## Content Mapping

For a task/case:

- `title`: concise case title
- `summary`: short business problem and agent result
- `visibility`: default `HIDDEN`; use `PUBLISHED` only when requested
- `coverImage`: optional case cover URL, recommended ratio 7:4
- `tags`: comma-separated tags
- `agentStack`: tools/frameworks/stack
- `problem`, `solution`, `workflow`, `impact`: map from the user's notes
- `articleTitle`, `articleContent`: include when the user wants an initial recap article
- `reusableAssets`: include asset objects returned by `POST /api/assets`

For editing an existing task/case:

- Infer the slug from the task URL when possible.
- Use `PATCH /api/tasks/:slug`.
- Send only fields that should change.
- Include `status` when changing visibility: `{ "status": "HIDDEN" }` or `{ "status": "PUBLISHED" }`.
- Omit `repositories` and `reusableAssets` unless replacing the full target list.

For an article/tutorial:

- `title`: article title
- `content` or `markdown`: Markdown body
- `status`: default `DRAFT`; use `PUBLISHED` only when requested
- `taskSlug` or `taskId`: include when attaching to an existing task
- `taskTitle` and `taskSummary`: include when no existing task is provided and the API should create a lightweight task container

For editing an existing article/tutorial:

- Infer the slug from the article URL when possible.
- Use `PATCH /api/articles/:slug`.
- Send only fields that should change.
- Use `taskSlug` only when moving the article to another existing case.

## Public Publishing Rule

If the user says "publish publicly", "make it public", or gives an explicit production publishing instruction:

- Task: `visibility: "PUBLISHED"` or edit with `status: "PUBLISHED"`
- Article: `status: "PUBLISHED"`

Otherwise keep AI-created content hidden/draft.

