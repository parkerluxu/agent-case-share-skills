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
      "name": "销售与客户服务",
      "slug": "customer-service-operations",
      "description": "",
      "sortOrder": 10,
      "updatedAt": "2026-07-05T00:00:00.000Z"
    }
  ]
}
```

Default industry categories commonly available on Agent Case Share:

| Name | Slug |
| --- | --- |
| 电子信息与硬件 | `electronics-hardware` |
| 软件与互联网 | `web-development` |
| 智能制造 | `supply-chain-manufacturing` |
| 金融与财税 | `finance-accounting` |
| 医疗与健康 | `healthcare` |
| 教育与培训 | `education-training` |
| 零售与电商 | `retail-ecommerce` |
| 内容与传媒 | `content-creation` |
| 创意艺术与设计 | `creative-arts-design` |
| 政务与公共服务 | `government-public-services` |
| 企业服务与办公 | `enterprise-service-office` |
| 销售与客户服务 | `customer-service-operations` |
| 市场与增长 | `marketing` |
| 研发与 IT | `rd-it` |
| 数据与经营分析 | `data-analysis` |
| 法务与合规 | `legal-compliance` |
| 人力资源 | `human-resources` |
| 科研与学术 | `research` |
| 个人效率与生活 | `personal-productivity-life` |
| 通用自动化 | `general-automation` |
| 其他 | `other` |

Prefer live `/api/categories` data when available, because categories can change over time. Use these slugs as stable defaults for filtering.

Known category descriptions:

- `creative-arts-design`: 面向艺术、设计、创意内容和 AIGC 创作工作流的 AI Agent 案例。

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
GET /api/search?q=agent&type=task&category=customer-service-operations&tag=automation&limit=10
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
GET /api/tasks?q=agent&category=customer-service-operations&tag=automation&status=PUBLISHED&limit=10&page=1
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
      "industry": "销售与客户服务",
      "difficulty": "BEGINNER",
      "agentStack": "Next.js, OpenAI",
      "status": "PUBLISHED",
      "category": { "id": "category-id", "name": "销售与客户服务", "slug": "customer-service-operations" },
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

## Project Detail

```http
GET /api/projects/:slug
```

Returns one open-source project detail record. Published projects are public. Draft or hidden projects require an admin signed-in session or an admin personal API key.

```json
{
  "project": {
    "id": "project-id",
    "name": "Open-source agent framework",
    "slug": "open-source-agent-framework",
    "url": "/projects/open-source-agent-framework",
    "summary": "Short project summary...",
    "description": "Longer project description...",
    "repoUrl": "https://github.com/example/agent-framework",
    "websiteUrl": "https://example.com",
    "tutorialUrl": "https://example.com/tutorial",
    "techStack": "TypeScript, Python",
    "maturity": "Production-ready",
    "license": "MIT",
    "status": "PUBLISHED",
    "featured": false,
    "qualityScore": 4,
    "likeCount": 12,
    "category": { "id": "category-id", "name": "AI Agents", "slug": "ai-agents" },
    "tags": [{ "id": "tag-id", "name": "Agent", "slug": "agent" }],
    "createdAt": "2026-07-07T00:00:00.000Z",
    "updatedAt": "2026-07-07T00:00:00.000Z"
  }
}
```

## Paper Detail

```http
GET /api/papers/:slug
```

Returns one paper detail record. Published papers are public. Draft or hidden papers require an admin signed-in session or an admin personal API key.

```json
{
  "paper": {
    "id": "paper-id",
    "title": "Agent Research Paper",
    "slug": "agent-research-paper",
    "url": "/papers/agent-research-paper",
    "excerpt": "Short paper summary...",
    "authors": "A. Researcher, B. Builder",
    "year": 2026,
    "paperUrl": "https://example.com/paper",
    "pdfUrl": "https://example.com/paper.pdf",
    "doi": "10.0000/example",
    "keywords": "agents, evaluation",
    "note": "Curator notes...",
    "status": "PUBLISHED",
    "featured": false,
    "qualityScore": 4,
    "likeCount": 8,
    "category": { "id": "category-id", "name": "Research", "slug": "research" },
    "tags": [{ "id": "tag-id", "name": "Evaluation", "slug": "evaluation" }],
    "createdAt": "2026-07-07T00:00:00.000Z",
    "updatedAt": "2026-07-07T00:00:00.000Z"
  }
}
```

## Public Asset List

```http
GET /api/assets?q=skill&type=SKILL&status=PUBLISHED&limit=10&page=1
```

Use this to discover reusable assets across the public asset library. Published assets are public. `DRAFT` and `HIDDEN` require authorization and only return assets visible to the authenticated user.

Parameters:

- `q`: optional keyword; searches title, summary, file name, linked task title, and linked task summary
- `type`: optional asset type, one of `SKILL`, `PROMPT`, `WORKFLOW`, `TEMPLATE`, `MCP_CONFIG`, `OTHER`
- `status`: optional, default `PUBLISHED`; `DRAFT` and `HIDDEN` require authorization
- `limit`: optional, default 10, maximum 50
- `page`: optional, default 1

Returns asset metadata, linked task context when present, and a download endpoint:

```json
{
  "items": [
    {
      "id": "asset-id",
      "title": "Support review skill",
      "type": "SKILL",
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
      "task": {
        "id": "task-id",
        "title": "Support review agent",
        "slug": "support-review-agent",
        "url": "/tasks/support-review-agent",
        "summary": "Short summary...",
        "industry": "Customer service",
        "status": "PUBLISHED"
      },
      "updatedAt": "2026-07-07T00:00:00.000Z"
    }
  ],
  "page": 1,
  "limit": 10,
  "total": 1,
  "hasMore": false
}
```

## Error Handling

- `400`: invalid query parameter such as `type` or `status`
- `401`: private list requested without credentials
- `404`: content does not exist or is not visible

On failure, show the returned `error` string and ask whether to retry with different filters or credentials.
