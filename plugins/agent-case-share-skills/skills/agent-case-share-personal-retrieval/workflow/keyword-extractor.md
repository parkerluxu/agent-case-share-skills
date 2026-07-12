# Personal Retrieval Keyword Extractor

Extracts structured search keywords from user messages for querying the personal asset library.

## Input

```json
{
  "user_message": "string",
  "conversation_history": [
    {"role": "user|assistant", "content": "string"}
  ],
  "request_context": "string"
}
```

## Output

```json
{
  "keywords": ["string"],
  "domain": "string|null",
  "tech_stack": ["string"],
  "task_type": "string|null",
  "asset_types": ["string"],
  "intent_summary": "string"
}
```

## Extraction Pipeline

### 1. Domain Detection (业务领域)

Match against known domains using keyword scoring:

```python
DOMAIN_TAXONOMY = {
    "推荐系统": ["推荐系统", "推荐算法", "召回", "排序", "重排序", "推荐模型", "CTR", "CVR", "个性化推荐", "协同过滤", "矩阵分解"],
    "搜索引擎": ["搜索", "全文检索", "倒排索引", "Elasticsearch", "Solr", "向量搜索", "混合检索", "查询理解", "查询改写"],
    "电商": ["电商", "商品", "SKU", "GMV", "转化率", "下单", "购物车", "促销", "大促", "双11", "618", "商品推荐", "商品搜索"],
    "广告系统": ["广告", "DSP", "SSP", "竞价", "定向", "归因", "ROI", "CTR预估", "实时竞价", "广告投放", "广告召回"],
    "风控反欺诈": ["风控", "反欺诈", "信贷", "征信", "反洗钱", "黑产", "设备指纹", "规则引擎", "模型风控"],
    "金融量化": ["量化交易", "量化投资", "因子挖掘", "回测", "高频交易", "期权定价", "风险模型", "资产配置"],
    "数据平台": ["数据平台", "数仓", "数据湖", "OLAP", "ClickHouse", "Doris", "StarRocks", "Flink", "实时计算", "离线计算", "数据治理"],
    "AI应用": ["大模型", "LLM", "RAG", "Agent", "智能体", "Function Calling", "向量检索", "Embedding", "微调", "蒸馏", "Prompt工程"],
    "DevOps": ["DevOps", "CI/CD", "流水线", "部署", "运维", "监控", "告警", "日志", "链路追踪", "容器化", "K8s"],
    "即时通讯": ["IM", "即时通讯", "消息推送", "WebSocket", "长连接", "消息队列", "离线消息", "群聊", "单聊"],
    "直播短视频": ["直播", "短视频", "推流", "拉流", "CDN", "延迟优化", "弱网对抗", "美颜", "特效", "内容审核"],
    "社交网络": ["社交", "Feed", "动态", "推荐流", "社区", "关系链", "关注", "粉丝", "社交图谱"],
    "物流供应链": ["物流", "供应链", "仓储", "配送", "路由优化", "调度", "WMS", "TMS", "快递", "末端配送"],
    "医疗健康": ["医疗", "健康", "病历", "诊断", "药物", "临床", "电子病历", "医学影像", "智能问诊"],
    "在线教育": ["教育", "在线教育", "题库", "自适应学习", "知识图谱", "刷题", "K12", "职业教育", "智能组卷"],
}
```

**Algorithm:**
- Score each domain by counting keyword occurrences in `user_message + recent_history`
- Weight: longer keywords > shorter keywords (length^2)
- If max_score > 0 → return domain name, else `null`

### 2. Tech Stack Extraction (技术栈)

```python
TECH_STACK_PATTERNS = {
    "language": ["Python", "Go", "Golang", "Java", "TypeScript", "JavaScript", "Rust", "C++", "C#", "PHP", "Ruby", "Swift", "Kotlin", "Scala"],
    "framework": ["FastAPI", "Flask", "Django", "Spring Boot", "Spring", "Gin", "Echo", "Actix", "Axum", "NestJS", "Express", "Koa", "Hono", "Next.js", "Nuxt", "React", "Vue", "Svelte"],
    "database": ["PostgreSQL", "MySQL", "Redis", "MongoDB", "Elasticsearch", "OpenSearch", "Milvus", "Zilliz", "Pinecone", "Weaviate", "Qdrant", "Chroma", "TiDB", "ClickHouse", "Doris", "StarRocks", "Snowflake", "BigQuery", "DuckDB"],
    "message_queue": ["Kafka", "RabbitMQ", "Pulsar", "RocketMQ", "NATS", "Redis Streams"],
    "infrastructure": ["Kubernetes", "K8s", "Docker", "Helm", "Istio", "Envoy", "Prometheus", "Grafana", "Jaeger", "Zipkin", "SkyWalking", "Terraform", "Ansible", "ArgoCD", "Flux"],
    "ml_ai": ["PyTorch", "TensorFlow", "JAX", "Hugging Face", "Transformers", "LangChain", "LlamaIndex", "AutoGPT", "AutoGen", "vLLM", "TGI", "Ollama", "LM Studio", "ONNX", "TensorRT"],
    "data": ["Flink", "Spark", "Airflow", "dbt", "Pandas", "Polars", "DuckDB"],
}
```

Extract ALL matches (case-insensitive) → unique array.

### 3. Task Type Classification (任务类型)

```python
TASK_TYPE_PATTERNS = {
    "架构设计": ["架构", "设计", "系统设计", "技术选型", "方案设计", "蓝图", "顶层设计", "可行性分析"],
    "模型训练": ["训练", "微调", "fine-tune", "预训练", "蒸馏", "LoRA", "QLoRA", "全参数训练", "SFT", "RLHF", "DPO", "对齐"],
    "向量检索": ["向量检索", "向量搜索", "Embedding", "向量化", "召回", "ANN", "HNSW", "IVF", "量化", "索引构建", "检索优化"],
    "RAG系统": ["RAG", "检索增强", "知识库", "文档问答", "问答系统", "检索生成", "Rerank", "重排序", "Chunking", "分块策略"],
    "Prompt工程": ["Prompt", "提示词", "系统提示词", "Few-shot", "Chain of Thought", "CoT", "思维链", "提示工程", "Prompt模板"],
    "工作流编排": ["工作流", "Workflow", "编排", "DAG", "Airflow", "Temporal", "LangGraph", "状态机", "任务调度", "管道"],
    "部署运维": ["部署", "发布", "运维", "上线", "灰度", "蓝绿", "回滚", "容器化", "镜像构建", "CI/CD", "服务网格"],
    "性能优化": ["优化", "性能", "加速", "延迟", "吞吐", "QPS", "TPS", "内存优化", "GPU优化", "推理加速", "量化", "剪枝", "蒸馏加速"],
    "数据清洗": ["清洗", "ETL", "数据治理", "数据质量", "去重", "异常检测", "数据标注", "数据增强", "数据合成"],
    "评测体系": ["评测", "基准测试", "Benchmark", "指标", "A/B测试", "灰度实验", "在线评估", "离线评估", "对照实验"],
    "Prompt模板": ["模板", "Template", "提示词模板", "Prompt模板", "Prompt库"],
    "MCP配置": ["MCP", "Model Context Protocol", "工具调用", "Function Calling", "工具定义"],
}
```

Match best single task_type (score by keyword count + length). If none → `null`.

### 4. Asset Type Inference (资产类型偏好)

```python
ASSET_TYPE_KEYWORDS = {
    "CASE": ["案例", "复盘", "项目", "实战", "落地", "经验", "踩坑", "避坑", "案例研究", "复盘文"],
    "SKILL": ["技能", "Skill", "脚本", "工具", "可执行", "自动化", "CLI", "SDK", "技能包", "skill包"],
    "PROMPT": ["Prompt", "提示词", "提示词模板", "系统提示词", "Prompt模板", "提示词库"],
    "WORKFLOW": ["工作流", "Workflow", "流程", "Pipeline", "管道", "编排", "DAG", "任务流"],
    "TEMPLATE": ["模板", "Template", "脚手架", "Boilerplate", "Starter", "项目模板", "代码模板"],
    "MCP_CONFIG": ["MCP", "Model Context Protocol", "配置", "Config", "工具配置", "工具定义"],
    "ARTICLE": ["文章", "教程", "博客", "总结", "复盘文", "分享", "笔记", "技术分享"],
    "OTHER": ["资产", "素材", "文件", "配置文件", "脚本文件", "工具脚本"],
}
```

If matches found → return matched types. If none → default `["CASE", "SKILL", "PROMPT", "WORKFLOW"]`.

### 5. Flat Keyword List (for search API `q` parameter)

Build combined keyword list:
1. Domain keywords (top 3)
2. Tech stack (top 5)
3. Task type (if not null)
4. Asset type keywords (top 2)
5. Noun phrases from user message (regex: `[一-鿿]{2,}|[a-zA-Z]{3,}`)

Deduplicate, limit to 10.

### 6. Intent Summary

Generate one sentence:
```
"用户想要在 {domain或'通用领域'} 找 {task_type或'相关经验'}，技术栈偏向 {tech_stack前3个或'不限'}，希望复用 {asset_types} 类型的资产。"
```

## LLM-Assisted Extraction (Optional Enhancement)

If deterministic extraction yields low confidence (no domain, no task_type), call a lightweight LLM:

```prompt
从用户消息中提取搜索关键信息，输出JSON：
{
  "domain": "string|null",
  "tech_stack": ["string"],
  "task_type": "string|null",
  "asset_types": ["string"],
  "keywords": ["string"]
}

用户消息: {user_message}
对话历史: {last_3_messages}
```

Use structured output / JSON mode.

## Examples

### Example 1
**Input:** `"帮我设计一个电商推荐系统的向量检索召回层，参考我以前做过的 Milvus + Flask 方案，最好有现成的 Skill 包"`

**Output:**
```json
{
  "keywords": ["电商推荐系统", "向量检索", "召回层", "Milvus", "Flask", "Skill"],
  "domain": "推荐系统",
  "tech_stack": ["Milvus", "Flask", "Python"],
  "task_type": "向量检索",
  "asset_types": ["SKILL", "CASE"],
  "intent_summary": "用户想要在 推荐系统 找 向量检索 相关经验，技术栈偏向 Milvus, Flask, Python，希望复用 SKILL, CASE 类型的资产。"
}
```

### Example 2
**Input:** `"RAG 系统里怎么做查询改写和重排序？找找我以前的 Prompt 模板"`

**Output:**
```json
{
  "keywords": ["RAG", "查询改写", "重排序", "Rerank", "Prompt模板"],
  "domain": "AI应用",
  "tech_stack": [],
  "task_type": "RAG系统",
  "asset_types": ["PROMPT", "CASE"],
  "intent_summary": "用户想要在 AI应用 找 RAG系统 相关经验，技术栈偏向 不限，希望复用 PROMPT, CASE 类型的资产。"
}
```

### Example 3
**Input:** `"帮我优化一下这段 Python 代码的性能"`

**Output:**
```json
{
  "keywords": ["Python", "性能优化", "优化"],
  "domain": null,
  "tech_stack": ["Python"],
  "task_type": "性能优化",
  "asset_types": ["CASE", "SKILL", "PROMPT", "WORKFLOW"],
  "intent_summary": "用户想要在 通用领域 找 性能优化 相关经验，技术栈偏向 Python，希望复用 CASE, SKILL, PROMPT, WORKFLOW 类型的资产。"
}
```

## Edge Cases

- **Empty/short message**: If < 5 chars and no history → return defaults
- **Code paste**: If message contains code blocks, extract imports/function names as tech_stack hints
- **Follow-up questions**: "那召回层呢？" → infer domain/task_type from history
- **Mixed language**: Handle Chinese + English seamlessly
