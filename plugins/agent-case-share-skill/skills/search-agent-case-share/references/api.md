# Agent Case Share Read API

## Authentication

Published content is public. Hidden and draft content requires a signed-in browser session or a personal API key:

```http
Authorization: Bearer acsp_live_<secret>
```

Use a bearer token only when needed. Never store or print real keys.

## Categories

```http
GET /api/categories
```

Returns visible categories:

```json
{
  "items": [
    {
      "id": "category-id",
      "name": "Customer Service",
      "slug": "customer-service",
      "description": "",
      "sortOrder": 10,
      "updatedAt": "2026-07-05T00:00:00.000Z"
    }
  ]
}
```

## Tags

```http
GET /api/tags?q=agent&limit=20
```

Parameters:

- `q`: optional name or slug search
- `limit`: optional, default 50, maximum 100

Returns:

```json
{
  "items": [
    {
      "id": "tag-id",
      "name": "Agent",
      "slug": "agent",
      "count": 12
    }
  ],
  "limit": 20
}
```

## Unified Search

```http
GET /api/search?q=agent&type=task&category=customer-service&tag=automation&limit=10
```

Parameters:

- `q`: optional keyword
- `type`: optional, one of `task`, `article`, `news`, `project`, `paper`
- `category`: optional category slug
- `tag`: optional tag slug or name
- `limit`: optional, default 10, maximum 50

Returns lightweight results:

```json
{
  "items": [
    {
      "type": "task",
      "title": "Support review agent",
      "slug": "support-review-agent",
      "url": "/tasks/support-review-agent",
      "excerpt": "Short summary...",
      "tags": [{ "name": "Automation", "slug": "automation" }],
      "updatedAt": "2026-07-05T00:00:00.000Z"
    }
  ],
  "limit": 10
}
```

## Task List

```http
GET /api/tasks?q=agent&category=customer-service&tag=automation&status=PUBLISHED&limit=10&page=1
```

Parameters:

- `q`: optional keyword
- `category`: optional category slug
- `tag`: optional tag slug or name
- `status`: optional, default `PUBLISHED`; `DRAFT` and `HIDDEN` require authorization
- `limit`: optional, default 10, maximum 50
- `page`: optional, default 1

Returns card fields only, not long body text:

```json
{
  "items": [
    {
      "id": "task-id",
      "title": "Support review agent",
      "slug": "support-review-agent",
      "url": "/tasks/support-review-agent",
      "summary": "Short summary...",
      "industry": "Customer Service",
      "difficulty": "BEGINNER",
      "agentStack": "Next.js, OpenAI",
      "status": "PUBLISHED",
      "category": { "id": "category-id", "name": "Customer Service", "slug": "customer-service" },
      "tags": [{ "id": "tag-id", "name": "Automation", "slug": "automation" }],
      "counts": { "articles": 1, "repositories": 1, "reusableAssets": 1 },
      "updatedAt": "2026-07-05T00:00:00.000Z"
    }
  ],
  "page": 1,
  "limit": 10,
  "total": 1,
  "hasMore": false
}
```

## Task Detail

```http
GET /api/tasks/:slug
```

Returns case details, related articles, repositories, and reusable assets:

```json
{
  "task": {
    "title": "Support review agent",
    "slug": "support-review-agent",
    "url": "/tasks/support-review-agent",
    "summary": "Short summary...",
    "problem": "Business problem...",
    "solution": "Agent solution...",
    "workflow": "Step 1\nStep 2",
    "impact": "Result...",
    "tools": ["OpenAI", "Slack"],
    "articles": [
      {
        "title": "Deployment guide",
        "slug": "deployment-guide",
        "url": "/articles/deployment-guide",
        "excerpt": "Article excerpt..."
      }
    ],
    "repositories": [
      {
        "name": "support-review-agent",
        "url": "https://github.com/example/support-review-agent"
      }
    ],
    "reusableAssets": [
      {
        "title": "Support review skill",
        "type": "SKILL",
        "url": "/assets/asset-id",
        "downloadUrl": "/api/assets/asset-id/download"
      }
    ]
  }
}
```

## Article Detail

```http
GET /api/articles/:slug
```

Returns article metadata and Markdown body:

```json
{
  "article": {
    "title": "Deployment guide",
    "slug": "deployment-guide",
    "url": "/articles/deployment-guide",
    "excerpt": "Article excerpt...",
    "content": "## Markdown body\n\n...",
    "markdown": "## Markdown body\n\n...",
    "status": "PUBLISHED",
    "task": {
      "title": "Support review agent",
      "slug": "support-review-agent",
      "url": "/tasks/support-review-agent"
    }
  }
}
```

## Error Handling

- `400`: invalid query parameter such as `type` or `status`
- `401`: private list requested without credentials
- `404`: content does not exist or is not visible

On failure, show the returned `error` string and ask whether to retry with different filters or credentials.
