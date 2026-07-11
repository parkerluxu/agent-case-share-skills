# API Reference for Auto Retrieval Skill

This document describes the external API dependencies and data contracts for the `agent-case-share-auto-retrieval` skill.

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
      "summary": "完整案例复盘...",
      "status": "HIDDEN",
      "tags": [
        {"id": "tag-1", "name": "推荐系统", "slug": "recommender-system"},
        {"id": "tag-2", "name": "向量检索", "slug": "vector-search"}
      ],
      "updatedAt": "2026-07-10T12:00:00Z",
      "problem": "业务问题描述...",
      "solution": "解决方案...",
      "workflow": "工作流步骤...",
      "impact": "业务影响...",
      "reusableAssets": [
        {
          "id": "asset-1",
          "title": "向量检索Pipeline v1.0",
          "type": "SKILL",
          "url": "/assets/asset-1",
          "downloadUrl": "/api/assets/asset-1/download",
          "status": "HIDDEN"
        }
      ]
    },
    {
      "type": "asset",
      "id": "asset-2",
      "title": "向量召回Prompt模板",
      "assetType": "PROMPT",
      "sourceType": "USER_UPLOAD",
      "url": "/assets/asset-2",
      "downloadUrl": "/api/assets/asset-2/download",
      "excerpt": "向量召回阶段的Prompt工程模板...",
      "summary": "完整Prompt模板内容...",
      "version": "v0.5.0",
      "fileName": "vector-recall-prompts.md",
      "mimeType": "text/markdown",
      "fileSize": 2048,
      "status": "HIDDEN",
      "downloadCount": 3,
      "likeCount": 1,
      "category": null,
      "author": {"id": "user-1", "name": "用户", "email": "user@example.com"},
      "task": null,
      "createdAt": "2026-07-08T10:00:00Z",
      "updatedAt": "2026-07-08T10:00:00Z"
    }
  ],
  "limit": 5
}
```

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

### Case (Personal)
```typescript
interface PersonalCase {
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
  sourceType: "USER_UPLOAD" | "TASK_GENERATED" | "ARTICLE_GENERATED";
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

Auto-retrieval middleware calls:
```typescript
const results = await invokeSkill("search-agent-case-share-personal", "search", {
  q: extractedKeywords.join(" "),
  limit: config.max_results
});
```

### Fallback Behavior

If `search-agent-case-share-personal` is not available:
1. Log warning: "Auto-retrieval skipped: search-agent-case-share-personal skill not installed"
2. Return `should_inject: false` with error in debug
3. Continue normal conversation

### Rate Limiting

- Respect API rate limits (if any)
- Cache search results for 5 minutes per unique query within a conversation
- Max 1 search per user message (unless explicit re-trigger)

## Testing API Contract

Use the search skill's explicit invocation to verify API connectivity:

```
/skill search-agent-case-share-personal "向量检索 Milvus"
```

Should return items array with cases and/or assets from your personal library.