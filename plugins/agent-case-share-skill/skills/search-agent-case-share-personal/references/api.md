# Agent Case Share Personal Read API

## Authentication

Personal endpoints require a signed-in browser session or a personal API key generated from `/profile`:

```http
Authorization: Bearer acsp_live_<secret>
```

Use a bearer token for external scripts and AI agents. Never store or print real keys.

## Slug and URL Encoding

New cases use opaque `case-xxxxxxxx` slugs, and their articles use `article-xxxxxxxx`; each suffix has 8 lowercase letters or digits. Use returned `url` values directly because they are already percent-encoded. When building `/api/me/cases/:slug` from a raw `slug` field, encode the path segment exactly once with `encodeURIComponent`. Decode an already encoded task URL segment once before rebuilding a different path. Do not infer a slug from its title.

## Personal Search

```http
GET /api/me/search?q=agent&type=case&tag=automation&limit=10
```

Searches the authenticated user's cases and reusable assets in one lightweight response.

Parameters:

- `q`: optional keyword
- `type`: optional, `case` or `asset`
- `tag`: optional tag slug or name; applies to case results
- `limit`: optional, default 10, maximum 50

Returns:

```json
{
  "items": [
    {
      "type": "case",
      "id": "case-id",
      "title": "Support review agent",
      "slug": "case-k3j9f2a8",
      "url": "/tasks/case-k3j9f2a8",
      "excerpt": "Short summary...",
      "status": "HIDDEN",
      "tags": [{ "id": "tag-id", "name": "Automation", "slug": "automation" }],
      "updatedAt": "2026-07-07T00:00:00.000Z"
    },
    {
      "type": "asset",
      "id": "asset-id",
      "title": "Support review skill",
      "url": "/assets/asset-id",
      "downloadUrl": "/api/assets/asset-id/download",
      "excerpt": "Reusable support review workflow.",
      "status": "PUBLISHED",
      "assetType": "SKILL",
      "sourceType": "USER_UPLOAD",
      "category": null,
      "fileName": "support-review-skill.zip",
      "task": null,
      "updatedAt": "2026-07-07T00:00:00.000Z"
    }
  ],
  "limit": 10
}
```

## My Cases

```http
GET /api/me/cases?q=agent&category=customer-service-operations&tag=automation&status=HIDDEN&limit=10&page=1
```

Lists the authenticated user's own cases. When `status` is omitted, published, hidden, and draft cases are included.

Parameters:

- `q`: optional keyword
- `category`: optional category slug
- `tag`: optional tag slug or name
- `status`: optional, one of `DRAFT`, `PUBLISHED`, `HIDDEN`
- `limit`: optional, default 10, maximum 50
- `page`: optional, default 1

Returns card fields:

```json
{
  "items": [
    {
      "id": "case-id",
      "title": "Support review agent",
      "slug": "case-k3j9f2a8",
      "url": "/tasks/case-k3j9f2a8",
      "summary": "Short summary...",
      "status": "HIDDEN",
      "category": { "id": "category-id", "name": "Customer service", "slug": "customer-service-operations" },
      "tags": [{ "id": "tag-id", "name": "Automation", "slug": "automation" }],
      "counts": { "articles": 1, "repositories": 1, "reusableAssets": 1 },
      "updatedAt": "2026-07-07T00:00:00.000Z"
    }
  ],
  "page": 1,
  "limit": 10,
  "total": 1,
  "hasMore": false
}
```

## My Case Detail

```http
GET /api/me/cases/:slug
```

Returns one authenticated-user-owned case. This endpoint can return hidden or draft user-owned content.

```json
{
  "case": {
    "id": "case-id",
    "title": "Support review agent",
    "slug": "case-k3j9f2a8",
    "url": "/tasks/case-k3j9f2a8",
    "summary": "Short summary...",
    "status": "HIDDEN",
    "problem": "Business problem...",
    "solution": "Agent solution...",
    "workflow": "Step 1\nStep 2",
    "impact": "Result...",
    "articles": [
      {
        "id": "article-id",
        "title": "Deployment guide",
        "slug": "article-m4n8q2x7",
        "url": "/articles/article-m4n8q2x7",
        "status": "DRAFT",
        "order": 1
      }
    ],
    "repositories": [
      {
        "id": "repository-id",
        "name": "support-review-agent",
        "url": "https://github.com/example/support-review-agent",
        "description": "Repository notes"
      }
    ],
    "reusableAssets": [
      {
        "id": "asset-id",
        "title": "Support review skill",
        "type": "SKILL",
        "url": "/assets/asset-id",
        "downloadUrl": "/api/assets/asset-id/download",
        "status": "HIDDEN"
      }
    ]
  }
}
```

## My Assets

```http
GET /api/me/assets?q=skill&type=SKILL&status=PUBLISHED&limit=10&page=1
```

Lists the authenticated user's own reusable assets. When `status` is omitted, published, hidden, and draft assets are included.

Parameters:

- `q`: optional keyword; searches title, summary, file name, linked task title, and linked task summary
- `type`: optional asset type, one of `SKILL`, `PROMPT`, `WORKFLOW`, `TEMPLATE`, `MCP_CONFIG`, `OTHER`
- `status`: optional, one of `DRAFT`, `PUBLISHED`, `HIDDEN`
- `limit`: optional, default 10, maximum 50
- `page`: optional, default 1

Returns:

```json
{
  "items": [
    {
      "id": "asset-id",
      "title": "Support review skill",
      "type": "SKILL",
      "sourceType": "USER_UPLOAD",
      "url": "/assets/asset-id",
      "downloadUrl": "/api/assets/asset-id/download",
      "summary": "Reusable support review workflow.",
      "version": "v1.0.0",
      "fileName": "support-review-skill.zip",
      "mimeType": "application/zip",
      "fileSize": 12345,
      "status": "PUBLISHED",
      "downloadCount": 3,
      "likeCount": 1,
      "license": null,
      "category": null,
      "author": { "id": "user-id", "name": "Author", "email": "author@example.com" },
      "task": null,
      "updatedAt": "2026-07-07T00:00:00.000Z"
    }
  ],
  "page": 1,
  "limit": 10,
  "total": 1,
  "hasMore": false
}
```

## My Asset Detail

```http
GET /api/me/assets/:id
```

Returns one authenticated-user-owned reusable asset.

```json
{
  "asset": {
    "id": "asset-id",
    "title": "Support review skill",
    "type": "SKILL",
    "sourceType": "USER_UPLOAD",
    "url": "/assets/asset-id",
    "downloadUrl": "/api/assets/asset-id/download",
    "summary": "Reusable support review workflow.",
    "version": "v1.0.0",
    "fileName": "support-review-skill.zip",
    "mimeType": "application/zip",
    "fileSize": 12345,
    "status": "PUBLISHED",
    "downloadCount": 3,
    "likeCount": 1,
    "license": null,
    "category": null,
    "author": { "id": "user-id", "name": "Author", "email": "author@example.com" },
    "task": null,
    "createdAt": "2026-07-07T00:00:00.000Z",
    "updatedAt": "2026-07-07T00:00:00.000Z"
  }
}
```

## Error Handling

- `400`: invalid query parameter such as `type` or `status`
- `401`: missing, invalid, or revoked personal API key, or no signed-in session
- `404`: the case or asset does not exist in the authenticated user's library

On failure, show the returned `error` string and ask whether to retry with different filters or credentials.
