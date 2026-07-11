# Trigger Detector Middleware

Determines whether auto-retrieval should be triggered for the current user message / conversation state.

## Input

```json
{
  "user_message": "string",
  "conversation_history": [
    {"role": "user|assistant", "content": "string"}
  ],
  "is_new_conversation": "boolean",
  "explicit_skill_call": "string|null",
  "config": {
    "enabled": true,
    "trigger_keywords": ["string"],           // User-defined additional triggers
    "exclude_keywords": ["string"],           // User-defined suppress triggers
    "trigger_on_new_conversation": true,
    "trigger_on_explicit_call": true
  }
}
```

## Output

```json
{
  "should_search": "boolean",
  "reason": "string",           // Human-readable reason for decision
  "matched_trigger": "string|null",  // The specific trigger that matched
  "trigger_type": "explicit|new_conversation|keyword|implicit|none"
}
```

## Decision Logic (Priority Order)

### 1. Master Switch
```python
if not config.enabled:
    return {should_search: False, reason: "Auto-retrieval disabled", trigger_type: "none"}
```

### 2. Explicit Skill Call
```python
if config.trigger_on_explicit_call and explicit_skill_call:
    return {
        should_search: True,
        reason: f"Explicit skill invocation: {explicit_skill_call}",
        matched_trigger: explicit_skill_call,
        trigger_type: "explicit"
    }
```
**Detection patterns for explicit call:**
- `/skill agent-case-share-auto-retrieval`
- `@agent-case-share-auto-retrieval`
- "搜索我的资产库"
- "查一下我的案例库"
- "用我的技能库找一下"

### 3. New Conversation Trigger
```python
if config.trigger_on_new_conversation and is_new_conversation:
    return {
        should_search: True,
        reason: "New conversation (first user message)",
        matched_trigger: "new_conversation",
        trigger_type: "new_conversation"
    }
```

### 4. Exclude Keywords (Suppress)
```python
msg_lower = user_message.lower()
for kw in config.exclude_keywords:
    if kw.lower() in msg_lower:
        return {
            should_search: False,
            reason: f"Suppressed by exclude keyword: {kw}",
            matched_trigger: kw,
            trigger_type: "none"
        }
```
**Default exclude keywords:** `["不需要查", "不用找", "关闭自动检索", "禁用检索", "别查库", "不参考"]`

### 5. Explicit Trigger Keywords
```python
all_triggers = DEFAULT_TRIGGERS + config.trigger_keywords
for kw in all_triggers:
    if kw.lower() in msg_lower:
        return {
            should_search: True,
            reason: f"Trigger keyword matched: {kw}",
            matched_trigger: kw,
            trigger_type: "keyword"
        }
```

**DEFAULT_TRIGGERS** (from design doc Section 7 + extensions):
```python
DEFAULT_TRIGGERS = [
    # 显式引用个人经验
    "参考我以前", "参考以前", "以前做过", "之前做过", "过往经验", "历史经验",
    "我的经验", "我以前", "我之前", "我做过", "我遇到过", "我踩过",

    # 复用/技能/资产词汇
    "复用", "复用一下", "拿来用", "直接用", "技能", "skill", "技能包",
    "prompt", "提示词", "workflow", "工作流", "资产", "asset", "素材",
    "模板", "template", "脚手架", "boilerplate", "脚本", "script",

    # 案例/复盘/踩坑
    "案例", "复盘", "踩坑", "避坑", "填坑", "最佳实践", "best practice",
    "经验总结", "教训", "血泪", "坑点", "注意点",

    # 相似/参考/查找
    "类似", "相似", "参考", "查找", "搜一下", "找找", "看看有没有",

    # 沉淀/积累
    "沉淀", "积累", "收藏", "存过", "保存过",

    # 疑问+隐式意图（需配合领域词，见下文隐式触发）
    "怎么做", "如何做", "怎样做", "最佳方案", "推荐方案", "设计方案",
    "架构设计", "技术选型", "选型建议", "优化建议", "性能优化"
]
```

### 6. Implicit Trigger: Question + Domain Keywords
```python
# Only if no explicit trigger matched above
question_indicators = [
    "怎么", "如何", "怎样", "什么", "哪里", "哪个", "哪种",
    "设计", "实现", "开发", "搭建", "构建", "部署", "上线",
    "优化", "改进", "提升", "解决", "修复", "排查", "定位",
    "选型", "评估", "对比", "推荐", "建议", "方案", "架构"
]

domain_keywords = DOMAIN_KEYWORDS  # 50+ terms, see below

has_question = any(q in msg_lower for q in question_indicators)
has_domain = any(d in msg_lower for d in domain_keywords)

if has_question and has_domain:
    matched_q = next(q for q in question_indicators if q in msg_lower)
    matched_d = next(d for d in domain_keywords if d in msg_lower)
    return {
        should_search: True,
        reason: f"Implicit trigger: question ('{matched_q}') + domain ('{matched_d}')",
        matched_trigger: f"{matched_q}+{matched_d}",
        trigger_type: "implicit"
    }
```

### 7. No Trigger
```python
return {
    should_search: False,
    reason: "No trigger condition met",
    matched_trigger: null,
    trigger_type: "none"
}
```

## DOMAIN_KEYWORDS (领域识别词汇)

Used for implicit trigger detection AND keyword extraction.

```python
DOMAIN_KEYWORDS = {
    # AI/ML/LLM
    "推荐系统", "推荐算法", "召回", "排序", "重排", "向量检索", "向量数据库",
    "Embedding", "embedding", "RAG", "检索增强", "大模型", "LLM", "微调",
    "Prompt Engineering", "提示工程", "Agent", "智能体", "多模态",
    "训练", "推理", "蒸馏", "量化", "LoRA", "PEFT", "RLHF",

    # 数据/搜索/向量
    "Milvus", "Weaviate", "Qdrant", "Pinecone", "Chroma", "FAISS",
    "Elasticsearch", "ES", "OpenSearch", "Solr", "倒排索引", "ANN", "HNSW",
    "相似度搜索", "语义搜索", "混合检索", "稀疏向量", "稠密向量",

    # 后端/架构/基础设施
    "微服务", "服务网格", "API网关", "负载均衡", "熔断", "限流", "降级",
    "分布式", "一致性", "事务", "事件驱动", "CQRS", "Event Sourcing",
    "Kubernetes", "K8s", "Docker", "容器化", "Helm", "Operator",
    "CI/CD", "流水线", "ArgoCD", "GitOps", "蓝绿部署", "金丝雀",

    # 数据工程
    "数据仓库", "数据湖", "实时计算", "Flink", "Spark", "Kafka", "Pulsar",
    "ClickHouse", "Doris", "StarRocks", "ETL", "ELT", "数据治理",

    # 语言/框架
    "Python", "Go", "Golang", "Java", "Spring Boot", "TypeScript", "Node.js",
    "React", "Vue", "Next.js", "FastAPI", "Flask", "Django", "gRPC",

    # 观测/运维
    "监控", "告警", "链路追踪", "日志", "指标", "Profiling", "性能分析",
    "Prometheus", "Grafana", "Jaeger", "Zipkin", "ELK", "Loki",

    # 业务领域
    "电商", "广告", "搜索", "风控", "反欺诈", "支付", "订单", "库存",
    "直播", "短视频", "社交", "IM", "即时通讯", "游戏", "匹配", "排位",
    "金融", "量化", "交易", "风控模型", "合规", "审计"
}
```

## Special Cases

### Multi-turn Conversation Context
If `conversation_history` shows user previously asked about a topic, and current message is a follow-up ("那召回层呢？", "再细化一下"), the implicit trigger should still fire because domain context persists.

**Implementation:** Check last 3 user messages for domain keywords if current message is short/follow-up.

### Code/Config Sharing
If user pastes code/config and asks "帮我优化这个" / "这有什么问题" → implicit trigger (question + code context).

### Language Detection
Triggers work for both Chinese and English keywords. Add English equivalents to DEFAULT_TRIGGERS:
```python
ENGLISH_TRIGGERS = [
    "reference my previous", "reuse", "my experience", "past project",
    "similar case", "best practice", "lessons learned", "pitfall",
    "skill", "prompt", "workflow", "asset", "template",
    "how to", "best way", "recommend", "design", "architecture",
    "optimize", "implement", "build", "deploy"
]
```

## Configuration Examples

### Minimal (only explicit triggers)
```yaml
config:
  enabled: true
  trigger_keywords: []
  exclude_keywords: []
  trigger_on_new_conversation: false
  trigger_on_explicit_call: true
```

### Aggressive (search on any technical question)
```yaml
config:
  enabled: true
  trigger_keywords: []
  exclude_keywords: ["别查", "不用找"]
  trigger_on_new_conversation: true
  trigger_on_explicit_call: true
  # Implicit trigger always active
```

### Conservative (only explicit + new conversation)
```yaml
config:
  enabled: true
  trigger_keywords: ["参考我以前", "复用", "找技能"]
  exclude_keywords: []
  trigger_on_new_conversation: true
  trigger_on_explicit_call: true
  # Note: implicit trigger still fires unless you modify code
```

## Testing Vectors

| User Message | Expected | Reason |
|--------------|----------|--------|
| "帮我参考以前做过的推荐系统案例" | True | Keyword: 参考以前 |
| "搜索我的资产库 向量检索" | True | Explicit call |
| (first message in new chat) | True | New conversation |
| "这次不用查库，直接回答" | False | Exclude: 不用查库 |
| "今天天气怎么样" | False | No domain keyword |
| "怎么优化 Milvus 索引性能" | True | Implicit: 怎么 + Milvus |
| "设计一个电商推荐系统架构" | True | Implicit: 设计 + 推荐系统 |
| "帮我看看这段代码有什么问题" | True | Implicit: 问题 + code context |
| "复盘一下上周的项目" | True | Keyword: 复盘 |

## Performance

- Pure string matching: < 1ms
- No external calls
- No LLM calls
- Can be run synchronously in request path
