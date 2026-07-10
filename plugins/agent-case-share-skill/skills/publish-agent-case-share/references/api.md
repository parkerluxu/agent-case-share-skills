# Agent Case Share Publishing API

## Authentication

Ask the user to sign in to Agent Case Share, open `/profile`, and generate a personal API key.

Use it as a bearer token:

```http
Authorization: Bearer acsp_live_<secret>
Content-Type: application/json
```

Do not ask for the user's password. Do not store the API key in logs, committed files, screenshots, shared prompts, or generated artifacts.

## Slug and URL Encoding

Let the API generate slugs for new content. New cases use `case-xxxxxxxx`, and new articles use `article-xxxxxxxx`; each suffix has 8 lowercase letters or digits. Omit `slug` when creating a new article. If a custom article slug is supplied, the API normalizes it to lowercase ASCII letters, digits, and hyphens, and an existing manageable article with that slug is updated.

Treat returned `slug` and `taskSlug` fields as opaque identifiers. Use returned `url` and `taskUrl` fields directly because they are already percent-encoded. When building `PATCH` or `DELETE` endpoints from a raw slug, encode the path segment exactly once with `encodeURIComponent`; decode an already encoded URL segment once before rebuilding a path.

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

## Upload a Case-Attached Reusable Asset Draft

Endpoint:

```http
POST /api/assets
Content-Type: multipart/form-data
```

Use this before `POST /api/tasks` when a case should include reusable assets such as skills, prompts, workflows, templates, or MCP configs. Without `publishAsset=true`, this endpoint uploads the file and returns metadata that can be placed in a task `reusableAssets` array.

Form fields:

- `file`: required file upload
- `title`: required asset title
- `type`: required enum, one of `SKILL`, `PROMPT`, `WORKFLOW`, `TEMPLATE`, `MCP_CONFIG`, `OTHER`
- `summary`: optional asset summary
- `version`: optional version label
- `publishAsset`: optional boolean; omit or set false for a case-attached draft
- `visibility`: ignored for draft mode

Supported extensions:

- `.zip`
- `.md`
- `.txt`
- `.json`
- `.yaml`
- `.yml`

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

Use the returned `asset` object inside `reusableAssets` when creating or editing a task. Do not use `POST /api/assets/user` for this path because task creation stores attached assets as case-scoped records from draft metadata.

## Upload a Standalone User Asset

Endpoint:

```http
POST /api/assets/user
Content-Type: multipart/form-data
```

Use this when the user wants to add an asset to their personal asset library independent of a case. This is the preferred endpoint for normal users and AI agents.

Form fields:

- `file`: required file upload
- `title`: required asset title
- `type`: required enum, one of `SKILL`, `PROMPT`, `WORKFLOW`, `TEMPLATE`, `MCP_CONFIG`, `OTHER`
- `summary`: optional asset summary
- `version`: optional version label
- `visibility`: optional enum, `PUBLISHED` or `HIDDEN`; API default is `PUBLISHED`, but AI agents should send `HIDDEN` unless the user explicitly requests public publishing

Successful response:

```json
{
  "asset": {
    "id": "asset-id",
    "title": "Support Review Skill",
    "type": "SKILL",
    "sourceType": "USER_UPLOAD",
    "summary": "Reusable support review skill",
    "version": "v1.0.0",
    "fileName": "support-review-skill.zip",
    "storageKey": "task-assets/user-id/uuid/support-review-skill.zip",
    "mimeType": "application/zip",
    "fileSize": 12345,
    "fileHash": "qiniu-file-hash",
    "status": "HIDDEN"
  }
}
```

Report `asset.id` after success. This response represents an independent asset record, not a draft object intended for `reusableAssets`.

## Compatibility Standalone Asset Upload

Endpoint:

```http
POST /api/assets
Content-Type: multipart/form-data
```

`POST /api/assets` can also create a standalone user asset when `publishAsset=true` is included. Prefer `POST /api/assets/user` for ordinary user uploads, but use this compatibility path if a client only knows `/api/assets`.

Additional form fields:

- `publishAsset`: set to `true`
- `visibility`: optional enum, `PUBLISHED` or `HIDDEN`; send `HIDDEN` unless the user explicitly requests public publishing

Successful response shape matches `POST /api/assets/user`.

## Edit Asset Metadata

Endpoint:

```http
PATCH /api/assets/:id
Content-Type: application/json
```

Use this to edit metadata for an existing reusable asset. It does not replace the uploaded file.

Permissions:

- Asset authors can edit their own assets.
- Authors of a linked case can edit assets attached to that case.

Optional fields:

- `title`: asset title; empty strings are rejected
- `type`: one of `SKILL`, `PROMPT`, `WORKFLOW`, `TEMPLATE`, `MCP_CONFIG`, `OTHER`
- `summary`: asset summary
- `version`: version label
- `visibility`: one of `DRAFT`, `PUBLISHED`, `HIDDEN`
- `status`: alias for `visibility`; one of `DRAFT`, `PUBLISHED`, `HIDDEN`

Successful response:

```json
{
  "asset": {
    "id": "asset-id",
    "title": "Support Review Skill v2",
    "type": "SKILL",
    "sourceType": "USER_UPLOAD",
    "summary": "Updated reuse notes.",
    "version": "v1.0.0",
    "fileName": "support-review-skill.zip",
    "mimeType": "application/zip",
    "fileSize": 12345,
    "downloadCount": 3,
    "likeCount": 1,
    "status": "HIDDEN",
    "updatedAt": "2026-07-07T00:00:00.000Z",
    "taskId": null,
    "url": "/assets/asset-id",
    "downloadUrl": "/api/assets/asset-id/download"
  }
}
```

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
- `tags`: comma-separated, Chinese-comma-separated, or newline-separated tag names; maximum 8
- `agentStack`
- `problem`
- `solution`
- `workflow`
- `impact`
- `humanInLoop`
- `estimatedTimeSaved`
- `costLevel`: `LOW`, `MEDIUM`, `HIGH`, or `UNKNOWN`
- `coverImage`: case cover URL, recommended ratio 7:4
- `tools`: comma-separated, Chinese-comma-separated, or newline-separated tool names; maximum 12
- `articleTitle`
- `articleExcerpt`
- `articleContent`
- `repositoryName`
- `repositoryUrl`
- `repositoryDescription`
- `repositoryTechStack`
- `repositoryLicense`
- `reusableAssets`: array of uploaded asset metadata objects, maximum 8 items

Category guidance:

- Prefer `categorySlug` over free-form `industry` when publishing or creating an article container.
- Discover the current visible list with `GET /api/categories` before publishing when possible.
- If live discovery is unavailable, use these stable default slugs:
  `electronics-hardware`, `web-development`, `supply-chain-manufacturing`, `finance-accounting`, `healthcare`, `education-training`, `retail-ecommerce`, `content-creation`, `creative-arts-design`, `government-public-services`, `enterprise-service-office`, `customer-service-operations`, `marketing`, `rd-it`, `data-analysis`, `legal-compliance`, `human-resources`, `research`, `personal-productivity-life`, `general-automation`, `other`.
- `industry` is display text; when provided, keep it aligned with the chosen category name.

Unsupported through this endpoint:

- Multiple repositories in one request
- Multiple articles in one request
- Raw file binary uploads

Successful response:

```json
{
  "slug": "case-k3j9f2a8"
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
- `tags`: comma-separated, Chinese-comma-separated, or newline-separated tag names; maximum 8
- `agentStack`
- `problem`
- `solution`
- `workflow`
- `impact`
- `humanInLoop`
- `estimatedTimeSaved`
- `costLevel`: `LOW`, `MEDIUM`, `HIGH`, or `UNKNOWN`
- `coverImage`: case cover URL, recommended ratio 7:4
- `tools`: comma-separated, Chinese-comma-separated, or newline-separated tool names; maximum 12
- `repositories`: full target repository list; omit to keep unchanged, send `[]` to clear
- `reusableAssets`: full target reusable asset list; omit to keep unchanged, send `[]` to clear

`PATCH /api/tasks/:slug` edits case metadata, retrospective fields, repositories, and reusable assets. It does not edit article Markdown text.

Successful response:

```json
{
  "id": "task-id",
  "slug": "case-k3j9f2a8",
  "url": "/tasks/case-k3j9f2a8",
  "status": "HIDDEN"
}
```

## Delete a Task

Endpoint:

```http
DELETE /api/tasks/:slug
```

Use this only when the user explicitly asks to delete a case. This endpoint currently requires a signed-in browser session; a bearer personal API key is not enough for task deletion.

Successful response:

```json
{
  "url": "/profile"
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
- `slug`: omit for new articles; when supplied, it is ASCII-normalized and updates the existing article with that slug when the user can manage it
- `status`: `DRAFT`, `PUBLISHED`, or `HIDDEN`
- `order`

If `taskId` and `taskSlug` are omitted, the API creates a lightweight task container for the article.

Successful response:

```json
{
  "id": "article-id",
  "slug": "article-m4n8q2x7",
  "url": "/articles/article-m4n8q2x7",
  "taskSlug": "case-k3j9f2a8",
  "taskUrl": "/tasks/case-k3j9f2a8"
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

Successful response:

```json
{
  "id": "article-id",
  "slug": "article-m4n8q2x7",
  "url": "/articles/article-m4n8q2x7",
  "taskSlug": "case-k3j9f2a8",
  "taskUrl": "/tasks/case-k3j9f2a8"
}
```

## Delete an Article

Endpoint:

```http
DELETE /api/articles/:slug
```

Use this only when the user explicitly asks to delete an article. Article authors and linked case authors can delete through this endpoint.

Successful response:

```json
{
  "taskSlug": "case-k3j9f2a8",
  "taskUrl": "/tasks/case-k3j9f2a8"
}
```

## Error Handling

- `400`: required fields are missing, enum values are invalid, JSON is malformed, or file upload form data is invalid
- `401`: API key is missing, invalid, revoked, or the endpoint requires a signed-in session
- `403`: authenticated user cannot edit or delete the requested task, article, or asset
- `404`: task, article, asset, or slug does not exist, or is not editable by the current user

On failure:

1. Parse the JSON response.
2. Show the returned `error` string to the user.
3. Ask whether to revise the payload and retry.
