# Context Injector Middleware

Formats search results from `search-agent-case-share-personal` and injects them into the conversation context for the main model.

## Input

```json
{
  "search_results": {                 // Raw response from GET /api/me/search
    "items": [
      {
        "type": "case|asset",
        "id": "string",
        "title": "string",
        "slug": "string|null",        // For cases
        "url": "string",
        "excerpt": "string|null",     // For search results
        "summary": "string|null",     // For case/detail
        "status": "string",
        "tags": [{"id": "string", "name": "string", "slug": "string"}],
        // Case-specific fields (from detail endpoint):
        "problem": "string|null",
        "solution": "string|null",
        "workflow": "string|null",
        "impact": "string|null",
        "reusableAssets": [...],
        // Asset-specific fields (from detail endpoint):
        "assetType": "string|null",   // SKILL, PROMPT, WORKFLOW, TEMPLATE, MCP_CONFIG, OTHER
        "downloadUrl": "string|null",
        "version": "string|null",
        "fileName": "string|null",
        "sourceType": "string|null"
      }
    ],
    "limit": 10
  },
  "extracted_keywords": {             // Output from keyword-extractor
    "keywords": ["string"],
    "domain": "string|null",
    "tech_stack": ["string"],
    "task_type": "string|null",
    "asset_types": ["string"],
    "intent_summary": "string"
  },
  "config": {
    "inject_template": "default|compact|detailed",
    "max_results": 5,
    "min_relevance_score": 0.3
  }
}
```

## Output

```json
{
  "injected_context": "string",       // Formatted context block to prepend to conversation
  "injected_asset_ids": ["string"],   // Asset IDs that were injected (for reference)
  "injected_case_slugs": ["string"]   // Case slugs that were injected
}
```

## Injection Templates

### Template: `default` (Balanced)

```
【你的个人资产库检索到相关经验】

--- 相关案例 (Cases) ---
{case_blocks}

--- 可复用资产 (Assets) ---
{asset_blocks}

--- 检索说明 ---
检索意图：{intent_summary}
检索关键词：{keywords_joined}
匹配数量：{case_count} 个案例，{asset_count} 个资产
```

**Case Block Format:**
```
### {title} ({status})
- **链接**: {url}
- **问题**: {problem或excerpt或summary前200字}
- **方案**: {solution或"见详情"}
- **影响**: {impact或"见详情"}
- **标签**: {tag_names_joined}
- **关联资产**: {reusable_asset_titles_joined或"无"}
- **Slug**: {slug}  # 用于后续详情查询
```

**Asset Block Format:**
```
### {title} ({assetType})  [{status}]
- **链接**: {url}
- **下载**: {downloadUrl}
- **摘要**: {summary或excerpt}
- **版本**: {version或"未标注"}
- **文件**: {fileName}
- **Asset ID**: {id}  # 用于下载/安装/编辑
```

### Template: `compact` (Minimal, for token-constrained contexts)

```
【个人资产库匹配：{case_count}案例 {asset_count}资产】
{case_lines}
{asset_lines}
意图：{intent_summary}
```

**Case Line:** `- {title} [{status}] {problem或excerpt前100字} (slug: {slug})`
**Asset Line:** `- {title} [{assetType}] {summary前100字} (id: {id})`

### Template: `detailed` (Full context, for complex tasks)

```
【你的个人资产库检索到相关经验（详细模式）】

=== 搜索画像 ===
领域：{domain或"未识别"}
技术栈：{tech_stack_joined或"不限"}
任务类型：{task_type或"未识别"}
期望资产类型：{asset_types_joined}

=== 匹配案例 ({case_count}) ===
{case_detailed_blocks}

=== 匹配资产 ({asset_count}) ===
{asset_detailed_blocks}

=== 后续建议 ===
- 如需查看完整案例复盘：使用 search-agent-case-share-personal 读取 slug
- 如需下载安装 Skill：使用 publish-agent-case-share 下载 asset.id
- 如需基于此经验开始新任务：直接告诉我，我会结合上述经验辅助你
```

**Case Detailed Block:** Full problem/solution/workflow/impact + reusable assets list
**Asset Detailed Block:** Full summary + version + fileName + downloadUrl

## Filtering & Ranking

Before formatting, filter and rank results:

1. **Relevance scoring** (simple heuristic):
   - Keyword overlap with extracted_keywords.keywords (weight: 3)
   - Domain match (weight: 2)
   - Tech stack overlap (weight: 2)
   - Task type match (weight: 2)
   - Asset type in extracted_keywords.asset_types (weight: 1)
   - Recency (updatedAt, weight: 1)

2. **Threshold**: Keep items with score >= `config.min_relevance_score * max_possible_score`

3. **Limit**: Top `config.max_results` items total (cases + assets combined)

4. **Deduplication**: If same case appears with multiple assets, merge

## Special Handling

### Cases with Reusable Assets
If a case has `reusableAssets`, include them inline in the case block and ALSO list separately in assets section (marked with `来源案例: {case_title}`).

### Skill Assets (type=SKILL)
Add special note: `💡 可直接安装使用：下载后解压到 .claude/skills/ 目录`

### Hidden/Draft Items
Show status clearly: `🔒 隐私` (HIDDEN), `📝 草稿` (DRAFT), `🌐 公开` (PUBLISHED)

### Empty Results
If no results after filtering:
```
【你的个人资产库暂无相关经验】
检索意图：{intent_summary}
建议：上传相关案例/技能到个人库，或调整关键词重试
```

## Injection Point

The `injected_context` should be inserted as a **system-level context block** BEFORE the current user message, with a clear delimiter:

```
<system-context source="agent-case-share-auto-retrieval">
{injected_context}
</system-context>

<user-message>
{current_user_message}
</user-message>
```

This ensures the main model sees it as contextual knowledge, not as user speech.

## Example Output (default template)

**Input:** Search returned 1 case + 2 assets for "电商推荐系统 向量检索 Milvus"

**Output:**
```
【你的个人资产库检索到相关经验】

--- 相关案例 (Cases) ---
### 电商向量检索系统复盘 (HIDDEN)
- **链接**: /tasks/ecommerce-vector-retrieval
- **问题**: 电商推荐系统召回层延迟高、召回率低，原有 ES 方案无法支撑亿级向量检索
- **方案**: 引入 Milvus 向量数据库，构建 Embedding→ANN召回→重排序全链路，Flask 封装推理服务
- **影响**: 召回延迟从 200ms 降至 30ms，召回率提升 15%，支撑双11 大促流量
- **标签**: 推荐系统, 向量检索, Milvus, Flask
- **关联资产**: 向量检索Pipeline v1.0 (SKILL), 向量召回Prompt模板 (PROMPT)
- **Slug**: ecommerce-vector-retrieval

--- 可复用资产 (Assets) ---
### 向量检索Pipeline v1.0 (SKILL)  [HIDDEN]
- **链接**: /assets/asset-vec-pipeline-001
- **下载**: /api/assets/asset-vec-pipeline-001/download
- **摘要**: 电商向量检索全链路：Embedding生成→Milvus召回→重排序→Flask服务化，含完整脚本和配置
- **版本**: v1.0.0
- **文件**: vector-retrieval-pipeline-v1.0.0.skill.zip
- **Asset ID**: asset-vec-pipeline-001
💡 可直接安装使用：下载后解压到 .claude/skills/ 目录

### 向量召回Prompt模板 (PROMPT)  [HIDDEN]
- **链接**: /assets/asset-prompt-vec-recall
- **下载**: /api/assets/asset-prompt-vec-recall/download
- **摘要**: 向量召回阶段的 Prompt 工程模板，含查询改写、负采样构造、相关性判断等 Prompt
- **版本**: v0.5.0
- **文件**: vector-recall-prompts.md
- **Asset ID**: asset-prompt-vec-recall

--- 检索说明 ---
检索意图：用户想要在 推荐系统 找 向量检索 相关经验，技术栈偏向 Milvus, Flask, Python，希望复用 SKILL, CASE 类型的资产。
检索关键词：电商推荐系统, 向量检索, 召回层, Milvus, Flask, Skill
匹配数量：1 个案例，2 个资产
```