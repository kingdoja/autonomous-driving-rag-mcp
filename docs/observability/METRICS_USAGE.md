# Response Quality Metrics Usage Guide

本文档介绍如何使用响应质量指标记录模块 (`src/observability/metrics.py`)。

## 概述

响应质量指标模块提供了全面的查询响应质量跟踪能力，包括：

- **相关性评分**：top-1, top-3, top-5 平均相关性
- **引用率**：有引用的响应比例
- **响应时间**：p50, p95, p99 百分位数
- **文档多样性**：来源文档数量、文档类型分布
- **Boost 效果**：boost 前后的排序变化

## 快速开始

### 基本用法

```python
from src.observability.metrics import create_metrics_recorder

# 创建 metrics recorder
recorder = create_metrics_recorder(
    query_id="query-123",
    collection="ad_knowledge_v01"
)

# 记录相关性评分
recorder.record_relevance(
    scores=[0.85, 0.78, 0.72, 0.65, 0.58]
)

# 记录引用信息
recorder.record_citations(
    citation_count=3,
    unique_sources=2
)

# 记录响应时间
recorder.record_response_time(
    total_ms=1250.5,
    stage_breakdown={
        "analysis": 50.2,
        "retrieval": 800.3,
        "reranking": 150.0,
        "generation": 250.0
    }
)

# 记录文档多样性
recorder.record_document_diversity(
    source_documents=["doc1", "doc2", "doc1", "doc3"],
    document_types=["sensor_doc", "algorithm_doc", "sensor_doc", "regulation_doc"],
    chunks_per_doc={"doc1": 2, "doc2": 1, "doc3": 1}
)

# 记录 boost 效果
recorder.record_boost_effectiveness(
    boost_applied=True,
    query_type="sensor_query",
    top_k_verification_passed=True
)

# 设置查询元数据
recorder.set_query_metadata(
    complexity="simple",
    response_type="standard"
)

# 完成并获取指标
metrics = recorder.finalize()

# 写入指标文件
from src.observability.metrics import write_metrics
write_metrics(metrics, metrics_path="logs/metrics.jsonl")
```

### 便捷函数

使用 `record_and_write_metrics` 一次性记录所有指标：

```python
from src.observability.metrics import record_and_write_metrics

metrics = record_and_write_metrics(
    query_id="query-123",
    collection="ad_knowledge_v01",
    relevance_scores=[0.85, 0.78, 0.72],
    citation_count=3,
    unique_sources=2,
    response_time_ms=1250.5,
    stage_breakdown={"analysis": 50.2, "retrieval": 800.3, "generation": 400.0},
    source_documents=["doc1", "doc2", "doc3"],
    document_types=["sensor_doc", "algorithm_doc", "regulation_doc"],
    boost_applied=True,
    query_type="sensor_query",
    query_complexity="simple",
    response_type="standard",
    metrics_path="logs/metrics.jsonl",
    add_to_global=True
)
```

## 聚合统计

### 使用 MetricsAggregator

```python
from src.observability.metrics import MetricsAggregator

# 创建聚合器
aggregator = MetricsAggregator(window_size=1000)

# 添加指标
for metrics in query_metrics_list:
    aggregator.add_metrics(metrics)

# 获取统计信息
stats = aggregator.get_statistics()

print(f"总查询数: {stats['total_queries']}")
print(f"引用率: {stats['citation_rate']:.2%}")
print(f"P95 响应时间: {stats['response_time_p95']:.2f}ms")
print(f"平均文档多样性: {stats['avg_diversity_score']:.3f}")
```

### 使用全局聚合器

```python
from src.observability.metrics import get_global_aggregator, get_current_statistics

# 获取全局聚合器
aggregator = get_global_aggregator()

# 获取当前统计信息
stats = get_current_statistics()

# 打印统计摘要
from src.observability.metrics import log_metrics_summary
log_metrics_summary()
```

输出示例：
```
=== Response Quality Metrics Summary ===
Total queries: 100
Relevance - Top-1: 0.823, Top-3: 0.756, Top-5: 0.698
Citation rate: 85.00%, Avg citations: 2.35
Response time - P50: 1200.50ms, P95: 3450.20ms, P99: 4850.75ms
Document diversity - Avg sources: 2.45, Diversity score: 0.678
Boost - Application rate: 45.00%, Top-K pass rate: 92.00%
========================================
```

## 指标详解

### 1. 相关性指标 (RelevanceMetrics)

```python
@dataclass
class RelevanceMetrics:
    top_1_score: float          # Top-1 结果的相关性评分
    top_3_avg_score: float      # Top-3 结果的平均相关性评分
    top_5_avg_score: float      # Top-5 结果的平均相关性评分
    min_score: float            # 最低相关性评分
    max_score: float            # 最高相关性评分
    score_distribution: Dict    # 评分分布 (0.0-0.2, 0.2-0.4, ...)
```

**用途**：评估检索结果的相关性质量

### 2. 引用指标 (CitationMetrics)

```python
@dataclass
class CitationMetrics:
    has_citations: bool                    # 是否有引用
    citation_count: int                    # 引用数量
    unique_sources: int                    # 唯一来源文档数量
    citation_rate: Optional[float]         # 引用率（百分比）
    avg_citations_per_response: Optional[float]  # 平均每个响应的引用数
```

**用途**：跟踪引用质量和来源多样性

### 3. 响应时间指标 (ResponseTimeMetrics)

```python
@dataclass
class ResponseTimeMetrics:
    response_time_ms: float           # 响应时间（毫秒）
    p50_ms: Optional[float]           # 50th 百分位数
    p95_ms: Optional[float]           # 95th 百分位数
    p99_ms: Optional[float]           # 99th 百分位数
    stage_breakdown: Dict[str, float] # 各阶段时间分解
```

**用途**：监控系统性能和识别瓶颈

### 4. 文档多样性指标 (DocumentDiversityMetrics)

```python
@dataclass
class DocumentDiversityMetrics:
    source_document_count: int              # 来源文档数量
    document_type_distribution: Dict        # 文档类型分布
    chunks_per_document: float              # 平均每个文档的 chunk 数
    diversity_score: float                  # 多样性评分 (0-1)
    top_sources: List[Tuple[str, int]]      # Top 来源文档
```

**用途**：评估多文档推理的质量

### 5. Boost 效果指标 (BoostEffectivenessMetrics)

```python
@dataclass
class BoostEffectivenessMetrics:
    boost_applied: bool                # 是否应用了 boost
    query_type: Optional[str]          # 触发 boost 的查询类型
    ranking_changes: int               # 排序位置变化数量
    target_doc_improvement: int        # 目标文档位置改进
    top_k_verification_passed: bool    # Top-K 验证是否通过
    boost_impact_score: float          # Boost 影响评分 (0-1)
```

**用途**：评估 metadata boost 的有效性

## 集成到查询流水线

### 在 HybridSearch 中集成

```python
from src.observability.metrics import create_metrics_recorder
from src.observability.tracing import create_query_tracer

class HybridSearch:
    def search(self, query: str, collection: str, top_k: int = 10):
        query_id = f"query-{uuid.uuid4()}"
        
        # 创建 tracer 和 metrics recorder
        tracer = create_query_tracer(query_id, query, collection)
        metrics_recorder = create_metrics_recorder(query_id, collection)
        
        start_time = time.monotonic()
        
        try:
            # 查询分析
            analysis = self.analyzer.analyze(query)
            tracer.record_query_analysis(...)
            
            # 检索
            results = self._retrieve(query, collection, top_k)
            
            # 记录相关性
            scores = [r.score for r in results]
            metrics_recorder.record_relevance(scores=scores)
            
            # Metadata boost
            if self.should_apply_boost(analysis):
                boosted_results = self.booster.apply_boost(results, analysis)
                metrics_recorder.record_boost_effectiveness(
                    boost_applied=True,
                    query_type=analysis.query_type,
                    top_k_verification_passed=True
                )
            
            # 重排序
            reranked = self.reranker.rerank(results, query)
            
            # 响应生成
            response = self.response_builder.build(query, reranked)
            
            # 记录引用
            metrics_recorder.record_citations(
                citation_count=len(response.citations),
                unique_sources=len(set(c.document_name for c in response.citations))
            )
            
            # 记录文档多样性
            doc_names = [c.document_name for c in response.citations]
            doc_types = [c.document_type for c in response.citations]
            metrics_recorder.record_document_diversity(
                source_documents=doc_names,
                document_types=doc_types
            )
            
            # 记录响应时间
            total_time = (time.monotonic() - start_time) * 1000
            metrics_recorder.record_response_time(total_ms=total_time)
            
            # 完成并写入
            metrics = metrics_recorder.finalize()
            write_metrics(metrics)
            
            return response
            
        except Exception as e:
            tracer.record_error(str(e))
            raise
```

## 监控和告警

### 设置告警阈值

```python
from src.observability.metrics import get_current_statistics

def check_quality_thresholds():
    stats = get_current_statistics()
    
    alerts = []
    
    # 检查引用率
    if stats.get("citation_rate", 0) < 0.80:
        alerts.append(f"Citation rate below threshold: {stats['citation_rate']:.2%}")
    
    # 检查响应时间
    if stats.get("response_time_p95", 0) > 4000:
        alerts.append(f"P95 response time above 4s: {stats['response_time_p95']:.2f}ms")
    
    # 检查 boost 效果
    if stats.get("boost_top_k_pass_rate", 0) < 0.80:
        alerts.append(f"Boost top-K pass rate below 80%: {stats['boost_top_k_pass_rate']:.2%}")
    
    return alerts
```

### Dashboard 集成

```python
import streamlit as st
from src.observability.metrics import get_current_statistics

def render_metrics_dashboard():
    st.title("Response Quality Metrics Dashboard")
    
    stats = get_current_statistics()
    
    # 显示关键指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Queries", stats.get("total_queries", 0))
    
    with col2:
        st.metric("Citation Rate", f"{stats.get('citation_rate', 0):.1%}")
    
    with col3:
        st.metric("P95 Response Time", f"{stats.get('response_time_p95', 0):.0f}ms")
    
    with col4:
        st.metric("Avg Diversity", f"{stats.get('avg_diversity_score', 0):.2f}")
    
    # 显示详细图表
    st.subheader("Response Time Distribution")
    # ... 绘制响应时间分布图
    
    st.subheader("Document Type Distribution")
    # ... 绘制文档类型分布图
```

## 最佳实践

### 1. 始终记录关键指标

确保每个查询都记录以下核心指标：
- 相关性评分
- 引用数量
- 响应时间
- 文档多样性

### 2. 使用全局聚合器

将指标添加到全局聚合器以便实时监控：

```python
metrics = recorder.finalize()
write_metrics(metrics)

# 添加到全局聚合器
from src.observability.metrics import get_global_aggregator
aggregator = get_global_aggregator()
aggregator.add_metrics(metrics)
```

### 3. 定期检查统计信息

设置定时任务定期检查和记录统计信息：

```python
import schedule

def log_hourly_stats():
    from src.observability.metrics import log_metrics_summary
    log_metrics_summary()

schedule.every().hour.do(log_hourly_stats)
```

### 4. 设置合理的窗口大小

根据查询量调整聚合器的窗口大小：

```python
# 低流量系统
aggregator = MetricsAggregator(window_size=100)

# 高流量系统
aggregator = MetricsAggregator(window_size=10000)
```

### 5. 结合 Tracing 使用

同时使用 metrics 和 tracing 获得完整的可观测性：

```python
from src.observability.tracing import create_query_tracer
from src.observability.metrics import create_metrics_recorder

tracer = create_query_tracer(query_id, query, collection)
metrics_recorder = create_metrics_recorder(query_id, collection)

# ... 执行查询流程 ...

# 完成并写入
trace = tracer.finalize()
metrics = metrics_recorder.finalize()

write_query_trace(trace)
write_metrics(metrics)
```

## 故障排查

### 问题：指标未记录

**解决方案**：
1. 检查是否调用了 `finalize()` 方法
2. 确认 `write_metrics()` 被调用
3. 检查日志文件路径是否正确

### 问题：统计信息不准确

**解决方案**：
1. 检查聚合器窗口大小是否合适
2. 确认指标是否添加到全局聚合器
3. 尝试强制刷新缓存：`get_statistics(force_refresh=True)`

### 问题：性能影响

**解决方案**：
1. 减小聚合器窗口大小
2. 异步写入指标文件
3. 批量处理指标记录

## 参考

- [Tracing 使用指南](./TRACING_USAGE.md)
- [Dashboard 配置](../dashboard/README.md)
- [告警配置](./ALERTING.md)
