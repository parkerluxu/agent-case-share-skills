# Agent Case Share Publishing API

## Authentication

Ask the user to sign in to Agent Case Share, open `/profile`, and generate a personal API key.

Use it as a bearer token:

```http
Authorization: Bearer acsp_live_<secret>
Content-Type: application/json
```

Do not ask for the user's password. Do not store the API key in logs, committed files, screenshots, shared prompts, or generated artifacts.

## Upload a Content Image

Endpoint:

```http
POST /api/content-images
Content-Type: multipart/form-data
```

Use this before `POST /api/tasks` or `POST /api/articles` when Markdown content references local image files.

Form fields:

- `file`: required image upload

Supported extensions:

- `.png`
- `.jpg`
- `.jpeg`
- `.webp`
- `.gif`

curl example:

```bash
curl -X POST "$AGENT_CASE_SHARE_BASE_URL/api/content-images" \
  -H "Authorization: Bearer $AGENT_CASE_SHARE_API_KEY" \
  -F "file=@./images/flow-screenshot.png"
```

Successful response:

```json
{
  "url": "https://assets.example.com/article-images/user-id/uuid/flow-screenshot.png",
  "markdown": "![flow screenshot](https://assets.example.com/article-images/user-id/uuid/flow-screenshot.png)",
  "image": {
    "fileName": "flow-screenshot.png",
    "storageKey": "article-images/user-id/uuid/flow-screenshot.png",
    "url": "https://assets.example.com/article-images/user-id/uuid/flow-screenshot.png",
    "markdown": "![flow screenshot](https://assets.example.com/article-images/user-id/uuid/flow-screenshot.png)",
    "mimeType": "image/png",
    "fileSize": 12345,
    "fileHash": "qiniu-file-hash"
  }
}
```

Replace local Markdown image paths with the returned `url`, or insert the returned `markdown`.

## Upload a Reusable Asset

Endpoint:

```http
POST /api/assets
Content-Type: multipart/form-data
```

Use this before `POST /api/tasks` when a task should include reusable assets such as skills, prompts, workflows, templates, or MCP configs.

Form fields:

- `file`: required file upload
- `title`: required asset title
- `type`: required enum, one of `SKILL`, `PROMPT`, `WORKFLOW`, `TEMPLATE`, `MCP_CONFIG`, `OTHER`
- `summary`: optional asset summary
- `version`: optional version label

Supported extensions:

- `.zip`
- `.md`
- `.txt`
- `.json`
- `.yaml`
- `.yml`

curl example:

```bash
curl -X POST "$AGENT_CASE_SHARE_BASE_URL/api/assets" \
  -H "Authorization: Bearer $AGENT_CASE_SHARE_API_KEY" \
  -F "file=@./support-review-skill.zip" \
  -F "title=Support Review Skill" \
  -F "type=SKILL" \
  -F "summary=Reusable support review skill" \
  -F "version=v1.0.0"
```

Successful response:

```json
{
  "asset": {
    "title": "Support Review Skill",
    "type": "SKILL",
    "summary": "Reusable support review skill",
    "version": "v1.0.0",
    "fileName": "support-review-skill.zip",
    "storageKey": "task-assets/user-id/uuid/support-review-skill.zip",
    "mimeType": "application/zip",
    "fileSize": 12345,
    "fileHash": "qiniu-file-hash"
  }
}
```

Use the returned `asset` object inside `reusableAssets`.

## Create a Task

Endpoint:

```http
POST /api/tasks
```

Required fields:

- `title`
- `summary`

Recommended AI default:

- `visibility`: `HIDDEN`

Optional fields:

- `categoryId`
- `categorySlug`
- `industry`
- `difficulty`: `BEGINNER`, `INTERMEDIATE`, or `ADVANCED`
- `visibility`: `PUBLISHED` or `HIDDEN`
- `tags`: comma-separated or newline-separated tag names
- `agentStack`
- `problem`
- `solution`
- `workflow`
- `impact`
- `humanInLoop`
- `estimatedTimeSaved`
- `costLevel`: `LOW`, `MEDIUM`, `HIGH`, or `UNKNOWN`
- `coverImage`: case cover URL, recommended ratio 7:4
- `tools`: comma-separated or newline-separated tool names
- `articleTitle`
- `articleExcerpt`
- `articleContent`
- `repositoryName`
- `repositoryUrl`
- `repositoryDescription`
- `repositoryTechStack`
- `repositoryLicense`
- `reusableAssets`: array of uploaded asset metadata objects, maximum 8 items

Unsupported through this endpoint:

- `featured`
- `reviewNote`
- `qualityScore`
- `viewCount`
- Multiple repositories in one request
- Multiple articles in one request
- Raw file binary uploads

Example payload:

```json
{
  "title": "AI agent support review report",
  "summary": "Connects conversations, tickets, and a knowledge base so an agent can generate review summaries.",
  "visibility": "HIDDEN",
  "tags": "support, automation",
  "agentStack": "Next.js, OpenAI, PostgreSQL"
}
```

Successful response:

```json
{
  "slug": "generated-task-slug"
}
```

## Edit a Task

Endpoint:

```http
PATCH /api/tasks/:slug
```

Send only fields that should change. Omitted fields keep their current values.

Optional fields:

- `title`
- `summary`
- `categoryId`: use an empty string to clear the category
- `difficulty`: `BEGINNER`, `INTERMEDIATE`, or `ADVANCED`
- `status`: `DRAFT`, `PUBLISHED`, or `HIDDEN`
- `tags`: comma-separated or newline-separated tag names, maximum 8
- `agentStack`
- `problem`
- `solution`
- `workflow`
- `impact`
- `humanInLoop`
- `estimatedTimeSaved`
- `costLevel`: `LOW`, `MEDIUM`, `HIGH`, or `UNKNOWN`
- `coverImage`: case cover URL, recommended ratio 7:4
- `tools`: comma-separated or newline-separated tool names, maximum 12
- `repositories`: full target repository list; omit to keep unchanged
- `reusableAssets`: full target reusable asset list; omit to keep unchanged

Status-only edit:

```json
{
  "status": "HIDDEN"
}
```

`PATCH /api/tasks/:slug` edits case metadata, retrospective fields, repositories, and reusable assets. It does not edit article Markdown text.

Successful response:

```json
{
  "id": "task-id",
  "slug": "agent-customer-support-quality-review",
  "url": "/tasks/agent-customer-support-quality-review",
  "status": "HIDDEN"
}
```

## Create an Article

Endpoint:

```http
POST /api/articles
```

Required fields:

- `title`
- `content` or `markdown`

Recommended AI default:

- `status`: `DRAFT`

Optional fields:

- `taskId`
- `taskSlug`
- `taskTitle`
- `taskSummary`
- `categoryId`
- `categorySlug`
- `industry`
- `agentStack`
- `problem`
- `solution`
- `workflow`
- `impact`
- `humanInLoop`
- `excerpt`
- `slug`
- `status`: `DRAFT`, `PUBLISHED`, or `HIDDEN`
- `order`

If `taskId` and `taskSlug` are omitted, the API creates a lightweight task container for the article.

Example payload:

```json
{
  "taskSlug": "agent-customer-support-quality-review",
  "title": "Support review agent deployment guide",
  "content": "## Setup\n\n## Deployment\n\n## Troubleshooting",
  "status": "DRAFT"
}
```

Successful response:

```json
{
  "id": "article-id",
  "slug": "article-slug",
  "url": "/articles/article-slug",
  "taskSlug": "task-slug",
  "taskUrl": "/tasks/task-slug"
}
```

## Edit an Article

Endpoint:

```http
PATCH /api/articles/:slug
```

Send only fields that should change.

Optional fields:

- `title`
- `content` or `markdown`
- `excerpt`
- `status`: `DRAFT`, `PUBLISHED`, or `HIDDEN`
- `order`
- `taskSlug`: move the article to another existing case the authenticated user can manage

`PATCH /api/articles/:slug` edits article fields only. It does not edit case title, summary, cover, tags, or retrospective fields.

Example payload:

```json
{
  "status": "PUBLISHED"
}
```

Successful response:

```json
{
  "id": "article-id",
  "slug": "support-review-agent-deployment-guide",
  "url": "/articles/support-review-agent-deployment-guide",
  "taskSlug": "agent-customer-support-quality-review",
  "taskUrl": "/tasks/agent-customer-support-quality-review"
}
```

## Error Handling

- `400`: required fields are missing, enum values are invalid, or JSON is malformed
- `401`: API key is missing, invalid, or revoked
- `403`: authenticated user cannot edit the requested task or article
- `404`: task, article, or slug does not exist

On failure:

1. Parse the JSON response.
2. Show the returned `error` string to the user.
3. Ask whether to revise the payload and retry.

