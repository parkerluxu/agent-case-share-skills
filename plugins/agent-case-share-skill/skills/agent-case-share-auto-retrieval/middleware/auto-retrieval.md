# Auto Retrieval Orchestration Middleware

Main entry point that coordinates the full auto-retrieval pipeline:
1. Trigger detection → 2. Keyword extraction → 3. Search → 4. Context injection

## Interface

### Input (from host environment)

```json
{
  "user_message": "string",              // Current user message
  "conversation_history": [              // Previous messages (for new conversation detection)
    {"role": "user|assistant", "content": "string"}
  ],
  "is_new_conversation": "boolean",      // True if first user message in session
  "explicit_skill_call": "string|null",  // If user explicitly invoked this skill
  "config": {                            // Merged with defaults from SKILL.md
    "enabled": true,
    "trigger_keywords": [],
    "exclude_keywords": [],
    "max_results": 5,
    "min_relevance_score": 0.3,
    "inject_template": "default",
    "trigger_on_new_conversation": true,
    "trigger_on_explicit_call": true
  },
  "credentials": {
    "source": "user_config|environment|session",
    "base_url": "string",
    "api_key": "string"
  }
}
```

### Output (to host environment)

```json
{
  "should_inject": true,
  "injected_context": "string",          // From context-injector
  "injected_asset_ids": ["string"],
  "injected_case_slugs": ["string"],
  "debug": {
    "triggered": true,
    "trigger_reason": "string",
    "extracted_keywords": {...},         // From keyword-extractor
    "search_results_count": 3,
    "filtered_results_count": 2,
    "search_latency_ms": 145,
    "errors": []
  }
}
```

## Pipeline Steps

### Step 1: Trigger Detection

```python
def detect_trigger(input) -> {should_search: bool, reason: str}:
    config = input.config
    msg = input.user_message.lower()

    # 1. Explicit skill call (highest priority)
    if config.trigger_on_explicit_call and input.explicit_skill_call:
        return {should_search: True, reason: f"Explicit skill call: {input.explicit_skill_call}"}

    # 2. New conversation
    if config.trigger_on_new_conversation and input.is_new_conversation:
        return {should_search: True, reason: "New conversation (first user message)"}

    # 3. Exclude keywords (suppress trigger)
    for kw in config.exclude_keywords:
        if kw.lower() in msg:
            return {should_search: False, reason: f"Excluded by keyword: {kw}"}

    # 4. Trigger keywords
    all_triggers = DEFAULT_TRIGGERS + config.trigger_keywords
    for kw in all_triggers:
        if kw.lower() in msg:
            return {should_search: True, reason: f"Trigger keyword matched: {kw}"}

    # 5. Implicit trigger: question + domain keywords
    # "怎么做推荐系统" "如何优化向量检索" "设计一个RAG架构"
    question_patterns = ["怎么", "如何", "怎样", "设计", "实现", "优化", "搭建", "构建", "开发"]
    domain_indicators = DOMAIN_KEYWORDS  # 50+ domain terms

    has_question = any(p in msg for p in question_patterns)
    has_domain = any(d in msg for d in domain_indicators)

    if has_question and has_domain:
        return {should_search: True, reason: "Implicit trigger: question + domain keyword"}

    return {should_search: False, reason: "No trigger condition met"}
```

**DEFAULT_TRIGGERS** (from design doc + extended):
```python
DEFAULT_TRIGGERS = [
    # 显式触发词
    "参考我以前", "复用", "经验", "案例", "类似", "踩坑", "避坑", "最佳实践",
    "参考", "复盘", "沉淀", "技能", "skill", "prompt", "workflow", "资产", "asset",
    # 隐式触发词（需配合领域词）
    "怎么做", "如何", "最佳", "推荐", "方案", "架构", "设计", "实现", "优化", "解决", "问题"
]
```

### Step 2: Keyword Extraction

If `should_search == True`, call `keyword-extractor.md` logic:

```python
extracted = extract_keywords({
    "user_message": input.user_message,
    "conversation_history": input.conversation_history,
    "trigger_reason": trigger_result.reason
})
# Returns: {keywords, domain, tech_stack, task_type, asset_types, intent_summary}
```

### Step 3: Search Personal Library

Call `search-agent-case-share-personal` skill via skill invocation mechanism:

```python
search_params = {
    "q": " ".join(extracted.keywords[:10]),  # Top 10 keywords
    "limit": config.max_results,
    # Note: search endpoint doesn't support type/tag filters directly
    # But we can post-filter by asset_type
}

# Skill invocation (pseudo-code):
search_results = await invoke_skill(
    "search-agent-case-share-personal",
    {"action": "search", "params": search_params}
)
# Expected: {items: [...], limit: N}
```

**Error handling:**
- Skill not installed → log warning, return `should_inject: false`
- Auth error (401) → log warning, add to debug.errors, return `should_inject: false`
- Network error → log warning, add to debug.errors, return `should_inject: false`
- Empty results → continue to injection (will produce "no results" message)

### Step 4: Context Injection

Call `context-injector.md` logic:

```python
injection = inject_context({
    "search_results": search_results,
    "extracted_keywords": extracted,
    "config": {
        "inject_template": config.inject_template,
        "max_results": config.max_results,
        "min_relevance_score": config.min_relevance_score
    }
})
# Returns: {injected_context, injected_asset_ids, injected_case_slugs}
```

### Step 5: Return Result

```python
return {
    "should_inject": True,
    "injected_context": injection.injected_context,
    "injected_asset_ids": injection.injected_asset_ids,
    "injected_case_slugs": injection.injected_case_slugs,
    "debug": {
        "triggered": True,
        "trigger_reason": trigger_result.reason,
        "extracted_keywords": extracted,
        "search_results_count": len(search_results.items),
        "filtered_results_count": len(injection.injected_asset_ids) + len(injection.injected_case_slugs),
        "search_latency_ms": search_latency,
        "errors": []
    }
}
```

## Host Integration Points

### For Claude Desktop / Agent SDK

This middleware should be invoked as a **pre-processing hook** before the main model receives the user message.

**Pseudo-integration:**

```python
async def on_user_message(user_message, conversation_history, session_state):
    # 1. Check if auto-retrieval is enabled for this session
    if not session_state.get("auto_retrieval_enabled", True):
        return user_message  # Pass through unchanged

    # 2. Run auto-retrieval pipeline
    retrieval_result = await run_auto_retrieval({
        "user_message": user_message,
        "conversation_history": conversation_history,
        "is_new_conversation": len(conversation_history) == 0,
        "explicit_skill_call": detect_explicit_skill_call(user_message),
        "config": session_state.get("auto_retrieval_config", DEFAULT_CONFIG),
    "credentials": resolve_agent_case_share_credentials()
    })

    # 3. If context was injected, prepend to conversation
    if retrieval_result.should_inject:
        enhanced_messages = [
            {"role": "system", "content": retrieval_result.injected_context},
            *conversation_history,
            {"role": "user", "content": user_message}
        ]
        # Store debug info for transparency
        session_state["last_retrieval_debug"] = retrieval_result.debug
        return enhanced_messages

    return conversation_history + [{"role": "user", "content": user_message}]
```

### Configuration via Session State

Users can configure per-session via chat:

```
用户: "这次对话关闭自动检索"
→ 设置 session_state.auto_retrieval_enabled = False

用户: "开启自动检索，模板用 compact 模式"
→ 设置 session_state.auto_retrieval_config = {enabled: true, inject_template: "compact"}

用户: "添加触发词：RAG、Agent"
→ 追加到 session_state.auto_retrieval_config.trigger_keywords
```

## Testing Checklist

| Scenario | Expected |
|----------|----------|
| New conversation, no trigger words | Search triggered (new conversation) |
| "帮我参考以前做过的推荐系统案例" | Search triggered (keyword: 参考以前) |
| "这次不需要查资产库" | No search (exclude keyword) |
| Explicit `/skill agent-case-share-auto-retrieval "向量检索"` | Search triggered (explicit) |
| "今天天气怎么样？" | No search (no domain keyword) |
| "怎么优化 Milvus 索引？" | Search triggered (question + domain) |
| Search API returns 401 | should_inject=false, error logged |
| Search returns 0 results | should_inject=true, "暂无相关经验" message injected |
| Skill not installed | should_inject=false, warning logged |

## Performance Targets

- Trigger detection: < 5ms
- Keyword extraction: < 100ms (LLM call) or < 10ms (deterministic)
- Search API call: < 500ms (network dependent)
- Context injection: < 10ms
- **Total added latency: < 600ms typical**

## Fallback Behavior (Fail-Open)

Any error in pipeline → log error, return `should_inject: false`, continue normal conversation. User never sees retrieval errors unless they ask "为什么没查我的资产库？"

## Debugging

When `should_inject: true`, the host should make `debug` info available to user on request:
- "刚才自动检索了什么？" → Show debug.trigger_reason, debug.extracted_keywords, debug.search_results_count
- "关闭调试信息" → Stop showing debug
