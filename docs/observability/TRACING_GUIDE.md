# Query Tracing Guide - 查询追踪使用指南

## 概述

查询追踪模块 (`src/observability/tracing.py`) 提供了完整的查询处理流程追踪功能，用于监控、调试和性能分析。

## 快速开始

### 基本使用

```python
from src.observability.tracing import create_query_tracer, write_query_trace

# 1. 创建追踪器
tracer = create_query_tracer(
    trace_id="query-12345",
    query="LiDAR的探测距离是多少？",
    collection="ad_knowledge_v01"
)

# 2. 记录各个阶段
tracer.record_query_analysis(
    complexity="simple",
    intent="retrieval",
    requires_multi_doc=False,
    detected_keywords=["LiDAR", "探测距离"],
    query_type="sensor_query",
    elapsed_ms=15.0
)

tracer.record_retrieval(
    method="hybrid",
    provider="azure_openai",
    top_k=20,
    result_count=18,
    elapsed_ms=220.0
)

# 3. 完成追踪
trace = tracer.finalize(total_elapsed_ms=500.0)

# 4. 写入日志
write_query_trace(trace)
```

## 追踪阶段

### 1. 查询分析 (Query Analysis)

记录查询的复杂度、意图和类型识别：

```python
tracer.record_query_analysis(
    complexity="simple",           # simple, multi_part, comparison, aggregation
    intent="retrieval",            # retrieval, boundary, scope_inquiry
    requires_multi_doc=False,      # 是否需要多文档
    detected_keywords=["LiDAR"],   # 检测到的关键词
    query_type="sensor_query",     # sensor_query, algorithm_query, regulation_query
    elapsed_ms=15.0                # 耗时（毫秒）
)
```

### 2. 元数据权重提升 (Metadata Boost)

记录 metadata boost 的应用情况：

```python
tracer.record_metadata_boost(
    boost_applied=True,                          # 是否应用 boost
    query_type="sensor_query",                   # 查询类型
    boost_config={"sensor_doc": 1.5},           # boost 配置
    top_k_verification={"passed": True},         # top-K 验证结果
    target_doc_count=2,                          # 目标文档数量
    total_top_k=3,                               # 总 top-K
    fallback_used=False,                         # 是否使用回退
    elapsed_ms=8.0
)
```

### 3. 检索 (Retrieval)

记录检索阶段的信息：

```python
tracer.record_retrieval(
    method="hybrid",                             # dense, sparse, hybrid
    provider="azure_openai",                     # 提供商
    top_k=20,                                    # 请求的结果数量
    result_count=18,                             # 实际返回的结果数量
    filters_applied={"collection": "ad_v01"},    # 应用的过滤器
    elapsed_ms=220.0
)
```

### 4. 重排序 (Reranking)

记录重排序阶段的信息：

```python
tracer.record_reranking(
    method="cross_encoder",                      # 重排序方法
    input_count=20,                              # 输入 chunk 数量
    output_count=10,                             # 输出 chunk 数量
    score_range=(0.65, 0.92),                    # 评分范围 (min, max)
    elapsed_ms=180.0
)
```

### 5. 文档分组 (Document Grouping)

记录文档分组情况（用于多文档查询）：

```python
tracer.record_document_grouping(
    grouping_applied=True,                       # 是否应用分组
    source_document_count=3,                     # 来源文档数量
    chunks_per_document={                        # 每个文档的 chunk 数量
        "lidar_spec.pdf": 2,
        "radar_spec.pdf": 2,
        "camera_spec.pdf": 1
    },
    diversity_enforced=True,                     # 是否强制多样性
    min_docs_required=2,                         # 最小文档要求
    min_docs_met=True,                           # 是否满足最小文档要求
    elapsed_ms=15.0
)
```

### 6. 响应生成 (Response Generation)

记录响应生成阶段的信息：

```python
tracer.record_response_generation(
    method="llm",                                # llm, template
    model="gpt-4",                               # 使用的模型
    response_type="standard",                    # standard, comparison, aggregation
    citation_count=3,                            # 引用数量
    token_count=450,                             # token 数量（可选）
    elapsed_ms=1200.0
)
```

### 7. 边界拒绝 (Boundary Refusal)

记录边界拒绝事件：

```python
tracer.record_boundary_refusal(
    refusal_occurred=True,                       # 是否发生拒绝
    refusal_type="predictive",                   # predictive, diagnostic, low_relevance
    detected_pattern="预测",                      # 检测到的模式
    query_content="预测下一代技术",               # 查询内容（截断）
    confidence=0.95,                             # 置信度
    suggested_alternatives=[                     # 建议的替代查询
        "查询当前技术现状",
        "查询技术原理"
    ],
    elapsed_ms=5.0
)
```

### 8. 错误记录 (Error)

记录查询处理过程中的错误：

```python
tracer.record_error("Retrieval failed: connection timeout")
```

## 完整流程示例

### 示例 1: 传感器查询完整流程

```python
from src.observability.tracing import create_query_tracer, write_query_trace
import time

# 创建追踪器
tracer = create_query_tracer(
    trace_id="query-001",
    query="LiDAR的探测距离和分辨率是多少？",
    collection="ad_knowledge_v01"
)

# 查询分析
tracer.record_query_analysis(
    complexity="simple",
    intent="retrieval",
    requires_multi_doc=False,
    detected_keywords=["LiDAR", "探测距离", "分辨率"],
    query_type="sensor_query",
    elapsed_ms=15.0
)

# Metadata Boost
tracer.record_metadata_boost(
    boost_applied=True,
    query_type="sensor_query",
    boost_config={"sensor_doc": 1.5, "algorithm_doc": 0.8},
    target_doc_count=3,
    total_top_k=3,
    elapsed_ms=8.0
)

# 检索
tracer.record_retrieval(
    method="hybrid",
    provider="azure_openai",
    top_k=20,
    result_count=18,
    elapsed_ms=220.0
)

# 重排序
tracer.record_reranking(
    method="cross_encoder",
    input_count=18,
    output_count=10,
    score_range=(0.72, 0.95),
    elapsed_ms=150.0
)

# 响应生成
tracer.record_response_generation(
    method="llm",
    model="gpt-4",
    response_type="standard",
    citation_count=3,
    token_count=380,
    elapsed_ms=1100.0
)

# 完成追踪
trace = tracer.finalize(total_elapsed_ms=1500.0)

# 写入日志
write_query_trace(trace)
```

### 示例 2: 对比查询流程（含文档分组）

```python
tracer = create_query_tracer(
    trace_id="query-002",
    query="LiDAR vs 毫米波雷达优缺点对比",
    collection="ad_knowledge_v01"
)

# 查询分析
tracer.record_query_analysis(
    complexity="comparison",
    intent="retrieval",
    requires_multi_doc=True,
    detected_keywords=["LiDAR", "毫米波雷达", "vs", "优缺点"],
    query_type="sensor_query",
    elapsed_ms=20.0
)

# 检索
tracer.record_retrieval(
    method="hybrid",
    provider="azure_openai",
    top_k=30,
    result_count=28,
    elapsed_ms=280.0
)

# 文档分组
tracer.record_document_grouping(
    grouping_applied=True,
    source_document_count=2,
    chunks_per_document={
        "lidar_spec.pdf": 3,
        "radar_spec.pdf": 3
    },
    diversity_enforced=True,
    min_docs_required=2,
    min_docs_met=True,
    elapsed_ms=18.0
)

# 重排序
tracer.record_reranking(
    method="cross_encoder",
    input_count=6,
    output_count=6,
    score_range=(0.68, 0.88),
    elapsed_ms=95.0
)

# 响应生成
tracer.record_response_generation(
    method="llm",
    model="gpt-4",
    response_type="comparison",
    citation_count=6,
    token_count=620,
    elapsed_ms=1400.0
)

# 完成追踪
trace = tracer.finalize(total_elapsed_ms=1820.0)
write_query_trace(trace)
```

### 示例 3: 边界拒绝流程

```python
tracer = create_query_tracer(
    trace_id="query-003",
    query="预测2030年自动驾驶技术发展趋势",
    collection="ad_knowledge_v01"
)

# 查询分析
tracer.record_query_analysis(
    complexity="simple",
    intent="boundary",
    requires_multi_doc=False,
    detected_keywords=["预测", "2030年", "发展趋势"],
    elapsed_ms=12.0
)

# 边界拒绝
tracer.record_boundary_refusal(
    refusal_occurred=True,
    refusal_type="predictive",
    detected_pattern="预测",
    query_content="预测2030年自动驾驶技术发展趋势",
    confidence=0.95,
    suggested_alternatives=[
        "查询当前自动驾驶技术现状",
        "查询自动驾驶技术原理"
    ],
    elapsed_ms=5.0
)

# 完成追踪（无检索和生成）
trace = tracer.finalize(total_elapsed_ms=20.0)
write_query_trace(trace)
```

## 输出格式

追踪数据以 JSON Lines 格式输出到 `logs/traces.jsonl`：

```json
{
  "trace_id": "query-001",
  "timestamp": "2024-01-15T10:30:00.123456Z",
  "query": "LiDAR的探测距离是多少？",
  "collection": "ad_knowledge_v01",
  "query_analysis": {
    "complexity": "simple",
    "intent": "retrieval",
    "requires_multi_doc": false,
    "detected_keywords": ["LiDAR", "探测距离"],
    "query_type": "sensor_query",
    "elapsed_ms": 15.0
  },
  "metadata_boost": {
    "boost_applied": true,
    "query_type": "sensor_query",
    "boost_config": {"sensor_doc": 1.5},
    "target_doc_count": 2,
    "total_top_k": 3,
    "elapsed_ms": 8.0
  },
  "retrieval": {
    "method": "hybrid",
    "provider": "azure_openai",
    "top_k": 20,
    "result_count": 18,
    "elapsed_ms": 220.0
  },
  "total_elapsed_ms": 500.0
}
```

## 分析追踪数据

### 使用 Python 分析

```python
import json
from pathlib import Path

# 读取追踪数据
traces_file = Path("logs/traces.jsonl")
traces = []

with open(traces_file, "r", encoding="utf-8") as f:
    for line in f:
        traces.append(json.loads(line))

# 分析平均响应时间
avg_time = sum(t["total_elapsed_ms"] for t in traces) / len(traces)
print(f"Average response time: {avg_time:.2f}ms")

# 分析 boost 应用率
boost_applied = sum(1 for t in traces if t.get("metadata_boost", {}).get("boost_applied"))
boost_rate = boost_applied / len(traces) * 100
print(f"Boost application rate: {boost_rate:.1f}%")

# 分析拒绝率
refusals = sum(1 for t in traces if t.get("boundary_refusal", {}).get("refusal_occurred"))
refusal_rate = refusals / len(traces) * 100
print(f"Refusal rate: {refusal_rate:.1f}%")
```

### 使用 jq 分析

```bash
# 查看所有查询类型
cat logs/traces.jsonl | jq -r '.query_analysis.query_type' | sort | uniq -c

# 查看平均响应时间
cat logs/traces.jsonl | jq '.total_elapsed_ms' | awk '{sum+=$1; count++} END {print sum/count}'

# 查看 boost 应用情况
cat logs/traces.jsonl | jq 'select(.metadata_boost.boost_applied == true) | .query_analysis.query_type' | sort | uniq -c

# 查看拒绝类型分布
cat logs/traces.jsonl | jq -r 'select(.boundary_refusal.refusal_occurred == true) | .boundary_refusal.refusal_type' | sort | uniq -c
```

## 最佳实践

### 1. 使用唯一的 trace_id

```python
import uuid

trace_id = f"query-{uuid.uuid4()}"
tracer = create_query_tracer(trace_id=trace_id, query=query)
```

### 2. 记录所有关键阶段

确保记录查询处理的所有关键阶段，即使某些阶段失败也要记录：

```python
try:
    # 执行检索
    results = retriever.retrieve(query)
    tracer.record_retrieval(...)
except Exception as e:
    tracer.record_error(f"Retrieval failed: {e}")
```

### 3. 使用自动耗时计算

让 `finalize()` 自动计算总耗时：

```python
# 不需要手动计算
trace = tracer.finalize()  # 自动计算从创建到完成的耗时
```

### 4. 定期清理日志文件

追踪日志会持续增长，建议定期归档或清理：

```bash
# 归档旧日志
mv logs/traces.jsonl logs/traces-$(date +%Y%m%d).jsonl

# 或使用 logrotate
```

### 5. 监控关键指标

定期监控以下指标：
- 平均响应时间
- Boost 应用率
- 拒绝率
- 错误率
- 文档多样性（多文档查询）

## 故障排查

### 问题 1: 追踪文件未创建

**原因**: logs 目录不存在

**解决**:
```python
from pathlib import Path
Path("logs").mkdir(exist_ok=True)
```

### 问题 2: JSON 序列化错误

**原因**: 追踪数据包含不可序列化的对象

**解决**: 确保所有记录的数据都是基本类型（str, int, float, bool, list, dict）

### 问题 3: 追踪数据过大

**原因**: 查询内容或其他字段过长

**解决**: 使用 `max_query_length` 参数限制查询长度：
```python
tracer = QueryTracer(
    trace_id=trace_id,
    query=query,
    max_query_length=100  # 限制为 100 字符
)
```

## 参考

- 模块源码: `src/observability/tracing.py`
- 单元测试: `tests/unit/test_tracing.py`
- 完成总结: `.kiro/specs/autonomous-driving-knowledge-retrieval/TASK_26_COMPLETION_SUMMARY.md`
