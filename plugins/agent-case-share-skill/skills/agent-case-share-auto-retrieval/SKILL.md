---
name: agent-case-share-auto-retrieval
description: Automatically retrieve relevant personal cases/assets from Agent Case Share during AI conversations. Triggers on keywords, new conversations, or explicit calls; extracts keywords; searches personal library; injects results into context for zero-perception reuse.
---

# Agent Case Share Auto Retrieval

This skill enables **zero-perception reuse** of your personal Agent Case Share library. It automatically detects when your conversation could benefit from past experience, searches your personal library, and injects relevant context into the AI's response.

## Architecture

```
User Message / New Conversation
         │
         ▼
┌─────────────────────────────────────┐
│  trigger-detector.md                │  ← Should we search?
│  (keywords / new chat / explicit)   │
└─────────────────────────────────────┘
         │ Yes
         ▼
┌─────────────────────────────────────┐
│  keyword-extractor.md               │  ← Extract: domain + tech stack + task type
│  (LLM-based extraction)             │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  search-agent-case-share-personal   │  ← Call existing search skill
│  (GET /api/me/search)               │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  context-injector.md                │  ← Inject results into context
│  (template-based injection)         │
└─────────────────────────────────────┘
         │
         ▼
   Enhanced Context → Main Model
```

## Trigger Conditions (any one triggers)

1. **Keyword trigger**: User message contains trigger words:
   - 显式触发词：`参考我以前`、`复用`、`经验`、`案例`、`类似`、`踩坑`、`避坑`、`最佳实践`、`参考`、`复盘`、`沉淀`、`技能`、`skill`、`prompt`、`workflow`、`资产`、`asset`
   - 隐式触发词：`怎么做`、`如何`、`最佳`、`推荐`、`方案`、`架构`、`设计`、`实现`、`优化`、`解决`、`问题` + 领域词

2. **New conversation trigger**: First user message in a new conversation/session

3. **Explicit trigger**: User explicitly invokes `/skill agent-case-share-auto-retrieval` or mentions "搜索我的资产库"

## Configuration

Environment variables:
- `AGENT_CASE_SHARE_BASE_URL` (default: `https://agentcaseshare.cn/`)
- `AGENT_CASE_SHARE_API_KEY` (personal API key from `/profile`)

Desktop configuration takes precedence over these compatible environment variables. It is created by `$configure-agent-case-share` at `%APPDATA%\\agent-case-share\\config.json` on Windows, `~/Library/Application Support/agent-case-share/config.json` on macOS, or `$XDG_CONFIG_HOME/agent-case-share/config.json` (fallback `~/.config/agent-case-share/config.json`) on Linux. If no key is configured, invoke `$configure-agent-case-share` and continue without retrieval until setup completes.

Skill configuration (can be overridden per session):
```yaml
auto_retrieval:
  enabled: true                    # Master switch
  trigger_keywords: [...]          # Custom trigger keywords (extends defaults)
  exclude_keywords: [...]          # Keywords that suppress auto-retrieval
  max_results: 5                   # Max results to retrieve
  min_relevance_score: 0.3         # Minimum relevance threshold
  inject_template: "default"       # Injection template name
  trigger_on_new_conversation: true
  trigger_on_explicit_call: true
```

## Middleware Components

| File | Purpose |
|------|---------|
| `middleware/trigger-detector.md` | Detect if auto-retrieval should trigger |
| `middleware/keyword-extractor.md` | Extract search keywords from user message |
| `middleware/context-injector.md` | Format and inject search results into context |
| `middleware/auto-retrieval.md` | Main orchestration entry point |

## Usage

### Automatic (zero-perception)
Just chat normally. When trigger conditions match, relevant past cases/assets are automatically injected into the AI's context.

### Explicit invocation
```
/skill agent-case-share-auto-retrieval "向量检索 推荐系统"
```

### Disable for a conversation
Tell the AI: "这次对话不要自动检索我的资产库" or set `enabled: false` in config.

## Integration with search-agent-case-share-personal

This skill **orchestrates** the existing `search-agent-case-share-personal` skill. It does not duplicate search logic — it calls the search skill's API via the standard skill invocation mechanism.

Required: `search-agent-case-share-personal` must be installed and configured with valid API credentials.

## Data Flow

1. User sends message / new conversation starts
2. `trigger-detector` evaluates → `should_search: boolean, reason: string`
3. If `should_search`: `keyword-extractor` extracts `{domain, tech_stack, task_type, keywords[]}`
4. Call `search-agent-case-share-personal` with extracted keywords, `limit=max_results`
5. `context-injector` formats results: cases (problem/solution/impact) + assets (title/type/summary/id)
6. Inject formatted context into conversation with marker: `【你的个人资产库检索到相关经验】`
7. Main model generates response with enhanced context

## Error Handling

- Search skill not installed → Log warning, continue without retrieval
- API auth failure (401) → Log warning, prompt user to configure API key
- Network error → Log warning, continue without retrieval
- No results → Silent continue (no injection)
- Any middleware error → Log, continue without retrieval (fail-open)

## Privacy

- Only searches **personal** library (`/api/me/*` endpoints)
- Requires personal API key from `$configure-agent-case-share`, compatible environment variables, or a signed-in session
- Never sends data to public endpoints
- Results injected only into current conversation context

## Download Retrieved Assets

When auto-retrieval surfaces relevant assets (especially `SKILL` type packages), users can download and install them:

1. **From injected context**: Each asset block includes `Asset ID` and `下载` (download URL).
2. **Download via search skill**: Use `search-agent-case-share-personal` with the asset ID to get fresh `downloadUrl`, then `GET` that URL with auth header.
3. **Install skill packages**: For `type: SKILL` assets, download the `.skill.zip`, extract to `.claude/skills/` (or your skills directory), and the skill becomes available immediately.

Example flow:
```
用户: "帮我用向量检索的 Skill"
→ 自动检索注入包含 "向量检索Pipeline v1.0 (SKILL) [Asset ID: asset-xxx]"
→ 用户说: "下载这个 Skill"
→ AI 调用 search-agent-case-share-personal 读取 asset-xxx 详情 → 获取 downloadUrl
→ AI 引导用户: "下载地址: /api/assets/asset-xxx/download，解压到 .claude/skills/ 即可使用"
```
