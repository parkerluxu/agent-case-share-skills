# API Reference for Personal Retrieval Skill

This document describes the external API dependencies and data contracts for the `agent-case-share-personal-retrieval` skill.

The skill is Agent-driven within the current task. The Agent may retrieve when the task benefits from prior personal examples, and users can always force retrieval by explicitly invoking this skill or clearly asking to search or reuse their library. The repository contains documentation and pseudo-code; it does not install a background conversation hook.

## External Dependency: search-agent-case-share-personal

This skill **requires** the `search-agent-case-share-personal` skill to be installed and configured. It does not make HTTP calls directly — it invokes the search skill through the host's skill invocation mechanism.

### Search Skill Invocation

```json
{
  "skill": "search-agent-case-share-personal",
  "action": "search",
  "params": {
    "q": "keyword1 keyword2 keyword3",
    "limit": 5
  }
}
```

### Search Skill Response Format

```json
{
  "items": [
    {
      "type": "case",
      "id": "case-uuid",
      "title": "电商向量检索系统复盘",
      "slug": "ecommerce-vector-retrieval",
      "url": "/tasks/ecommerce-vector-retrieval",
      "excerpt": "电商推荐系统召回层优化...",
      "status": "HIDDEN",
      "tags": [
        {"id": "tag-1", "name": "推荐系统", "slug": "recommender-system"},
        {"id": "tag-2", "name": "向量检索", "slug": "vector-search"}
      ],
      "updatedAt": "2026-07-10T12:00:00Z"
    },
    {
      "type": "asset",
      "id": "asset-2",
      "title": "向量召回Prompt模板",
      "url": "/assets/asset-2",
      "downloadUrl": "/api/assets/asset-2/download",
      "excerpt": "向量召回阶段的Prompt工程模板...",
      "status": "HIDDEN",
      "assetType": "PROMPT",
      "sourceType": "USER_UPLOAD",
      "category": null,
      "fileName": "vector-recall-prompts.md",
      "task": null,
      "updatedAt": "2026-07-08T10:00:00Z"
    }
  ],
  "limit": 5
}
```

`GET /api/me/search` is a lightweight mixed search. Case items do not include `summary`, `problem`, `solution`, `workflow`, `impact`, or `reusableAssets`; asset items do not include full asset-detail fields such as `summary`, `version`, or `mimeType`. For a case's full context, request `GET /api/me/cases/:slug` using the returned opaque `slug` before formatting those fields.

## Personal API Endpoints (Used by search-agent-case-share-personal)

Base URL: `https://agentcaseshare.cn/` (or `AGENT_CASE_SHARE_BASE_URL`)

### Authentication
```
Authorization: Bearer <personal-api-key>
```
Personal API key obtained from `/profile` page.

### Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/me/search?q=xxx&limit=5` | Mixed search (cases + assets) - PRIMARY |
| GET | `/api/me/cases?q=xxx&tag=xxx&status=HIDDEN&limit=10` | Filter personal cases |
| GET | `/api/me/assets?q=xxx&type=SKILL&status=HIDDEN&limit=10` | Filter personal assets |
| GET | `/api/me/cases/:slug` | Get case detail (includes reusableAssets) |
| GET | `/api/me/assets/:id` | Get asset detail (includes downloadUrl) |
| GET | `/api/assets/:id/download` | **Download asset file binary** |

### Error Responses

```json
// 400 - Bad Request
{"error": "invalid query parameter"}

// 401 - Unauthorized
{"error": "unauthorized", "message": "Invalid or missing personal API key"}

// 404 - Not Found
{"error": "not_found", "message": "Case/Asset not found in your library"}

// 500 - Server Error
{"error": "internal_error", "message": "Server error"}
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AGENT_CASE_SHARE_BASE_URL` | No | `https://agentcaseshare.cn/` | API base URL |
| `AGENT_CASE_SHARE_API_KEY` | Yes* | - | Personal API key from `/profile` |

*Required if no signed-in browser session available.

## Data Models

### Case Search Item (Personal)
```typescript
interface PersonalCaseSearchItem {
  id: string;
  title: string;
  slug: string;
  url: string;
  excerpt: string;
  status: "DRAFT" | "HIDDEN" | "PUBLISHED";
  tags: Tag[];
  updatedAt: string;
}
```

### Case Detail (Personal)
```typescript
interface PersonalCaseDetail {
  id: string;
  title: string;
  slug: string;
  url: string;
  summary: string;
  status: "DRAFT" | "HIDDEN" | "PUBLISHED";
  problem: string;
  solution: string;
  workflow: string;
  impact: string;
  tags: Tag[];
  articles: Article[];
  repositories: Repository[];
  reusableAssets: ReusableAssetRef[];
  category: Category | null;
  updatedAt: string;
}
```

### Asset (Personal)
```typescript
interface PersonalAsset {
  id: string;
  title: string;
  type: "SKILL" | "PROMPT" | "WORKFLOW" | "TEMPLATE" | "MCP_CONFIG" | "OTHER";
  sourceType: "OPEN_SOURCE" | "USER_UPLOAD" | "CASE_EXTRACTED";
  url: string;
  downloadUrl: string;
  summary: string;
  version: string;
  fileName: string;
  mimeType: string;
  fileSize: number;
  status: "DRAFT" | "HIDDEN" | "PUBLISHED";
  downloadCount: number;
  likeCount: number;
  license: string | null;
  category: Category | null;
  author: User;
  task: TaskRef | null;
  createdAt: string;
  updatedAt: string;
}
```

### Tag
```typescript
interface Tag {
  id: string;
  name: string;
  slug: string;
}
```

### Category
```typescript
interface Category {
  id: string;
  name: string;
  slug: string;
}
```

## Integration Notes

### Skill Invocation Pattern

The host environment should provide a skill invocation mechanism:

```typescript
async function invokeSkill(skillName: string, action: string, params: object): Promise<any> {
  // Implementation depends on host (Claude Desktop, Agent SDK, etc.)
}
```

Agent retrieval calls:
```typescript
const results = await invokeSkill("search-agent-case-share-personal", "search", {
  q: extractedKeywords.join(" "),
  limit: config.max_results
});
```

The returned case items are summaries only. If the Agent needs `problem`, `solution`, `workflow`, `impact`, or `reusableAssets`, it must make a separate `GET /api/me/cases/:slug` request for that case before assembling context. Asset detail fields likewise require `GET /api/me/assets/:id` when they are not present in the search result.

### Fallback Behavior

If `search-agent-case-share-personal` is not available:
1. Tell the user that personal retrieval is unavailable.
2. Do not invent or substitute personal context.
3. Continue the current task without retrieved material.

### Rate Limiting

- Respect API rate limits (if any)
- Cache results for the current task when useful and preserve their provenance
- Reassess retrieval for a later task or topic instead of carrying unrelated context forward

## Testing API Contract

Use the search skill's explicit invocation to verify API connectivity:

```
/skill search-agent-case-share-personal "向量检索 Milvus"
```

The response should return an `items` array with lightweight case and/or asset search results from your personal library. Fetch case details separately when the workflow needs the full case narrative or attached assets.
