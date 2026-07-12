# Personal Retrieval Decision

Decides whether the Agent should use the user's personal Agent Case Share library for the current task. This is a turn-level Agent decision, not a background listener.

## Input

```json
{
  "user_message": "string",
  "conversation_history": [
    {"role": "user|assistant", "content": "string"}
  ],
  "explicit_skill_call": "string|null",
  "config": {
    "enabled": true,
    "max_results": 5,
    "min_relevance_score": 0.3
  }
}
```

## Output

```json
{
  "should_retrieve": "boolean",
  "reason": "string",
  "query": "string|null",
  "case_slugs": ["string"],
  "asset_ids": ["string"],
  "max_results": 5,
  "download_assets": true
}
```

## Decision Logic

```python
def decide_retrieval(input):
    if not input.config.enabled:
        return no_retrieval("Personal retrieval disabled for this task")

    if has_personal_retrieval_opt_out(input.user_message):
        return no_retrieval("User opted out of personal retrieval")

    explicit = bool(input.explicit_skill_call)
    personal_request = clearly_asks_to_search_or_reuse_personal_library(input.user_message)
    task_benefit = substantive_domain_task_likely_benefits_from_prior_cases(input.user_message)

    if not (explicit or personal_request or task_benefit):
        return no_retrieval("Personal retrieval is unlikely to improve this task")

    case_slugs = extract_case_slugs(input.user_message)
    asset_ids = extract_asset_ids(input.user_message)
    query = extract_query(input.user_message, case_slugs, asset_ids)

    return {
        "should_retrieve": True,
        "reason": retrieval_reason(explicit, personal_request, task_benefit),
        "query": query,
        "case_slugs": case_slugs,
        "asset_ids": asset_ids,
        "max_results": input.config.max_results,
        "download_assets": True
    }
```

## Positive Examples

These should return `should_retrieve: true`:

- `/skill agent-case-share-personal-retrieval "推荐系统"`
- `参考我以前在 Agent Case Share 里的推荐系统案例`
- `找我上传的客服质检 Skill，下载后参考它的工作流`
- `设计一个 Milvus 向量检索方案，看看我以前有没有类似实践`
- `帮我排查这个 Agent 工作流问题，优先参考我的历史案例`

The Agent may also decide to retrieve for a substantive domain-specific design, implementation, debugging, or optimization task when prior personal examples are likely to improve the answer, even if the user did not use the exact words “案例库” or “资产库”.

## Negative Examples

These should return `should_retrieve: false`:

- `今天天气怎么样？`
- `把这句话翻译成英文`
- `怎么设计一个推荐系统？` when there is no meaningful reason to use personal history
- `我有个 case-k3j9f2a8，先记着` without a request to use it
- Any task after the user says not to search or reuse the personal library

## Scope Rules

- A case slug or asset ID narrows retrieval after the decision is positive; it is not required for retrieval.
- A generic word such as `案例`, `经验`, `skill`, or `asset` is only a signal when the surrounding request asks to search, reuse, or reference personal material.
- If the user explicitly names a case or asset, prefer it over broad search results.
- If the task does not benefit from personal context, do not search merely because this skill is installed.
