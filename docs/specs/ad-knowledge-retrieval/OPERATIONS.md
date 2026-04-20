# 自动驾驶知识检索系统 - 运维指南

## 1. 概述

本文档提供自动驾驶知识检索系统的运维指南，包括知识库更新流程、监控和告警配置、性能优化建议和故障排查指南。

## 2. 知识库更新流程

### 2.1 文档准备

#### 2.1.1 文档格式要求

**支持的格式**：
- PDF（推荐）
- DOCX
- TXT
- Markdown

**文档质量要求**：
- 文本清晰可读（避免扫描件）
- 结构化良好（有章节标题）
- 包含页码
- 文件大小 < 50MB

#### 2.1.2 文档分类

根据文档内容，分配正确的文档类型：

| 文档类型 | 标识符 | 示例 |
|---------|--------|------|
| 传感器文档 | sensor_doc | 激光雷达规格书、摄像头标定文档 |
| 算法文档 | algorithm_doc | 感知算法设计文档、规划算法报告 |
| 法规文档 | regulation_doc | GB/T 标准、ISO 26262 标准 |
| 测试文档 | test_doc | 测试场景库、测试用例、测试报告 |

#### 2.1.3 元数据准备

为每个文档准备元数据：

**传感器文档元数据**：
```json
{
  "sensor_type": "LiDAR",
  "manufacturer": "Velodyne",
  "model": "VLS-128",
  "version": "v2.0"
}
```

**算法文档元数据**：
```json
{
  "algorithm_type": "perception",
  "algorithm_name": "目标检测",
  "module": "感知模块",
  "version": "v1.5"
}
```

**法规文档元数据**：
```json
{
  "standard_number": "GB/T 40429-2021",
  "standard_name": "汽车驾驶自动化分级",
  "authority": "national"
}
```

**测试文档元数据**：
```json
{
  "test_type": "functional",
  "test_scenario": "跟车场景",
  "version": "v1.0"
}
```

### 2.2 文档摄取

#### 2.2.1 使用 CLI 工具摄取

```bash
# 摄取单个文档
python scripts/ingest_document.py \
  --file-path /path/to/激光雷达规格书.pdf \
  --collection ad_knowledge_v01 \
  --doc-type sensor_doc \
  --metadata '{"sensor_type": "LiDAR", "manufacturer": "Velodyne"}'

# 摄取多个文档
python scripts/ingest_documents.py \
  --file-paths /path/to/docs/*.pdf \
  --collection ad_knowledge_v01 \
  --doc-type sensor_doc \
  --metadata-file /path/to/metadata.json
```

#### 2.2.2 使用 Python SDK 摄取

```python
from ad_knowledge_retrieval import Client

client = Client(
    api_key="your_api_key",
    base_url="http://localhost:8000/api/v1"
)

# 摄取单个文档
result = client.ingest(
    file_paths=["/path/to/激光雷达规格书.pdf"],
    collection="ad_knowledge_v01",
    document_type="sensor_doc",
    metadata={
        "sensor_type": "LiDAR",
        "manufacturer": "Velodyne",
        "model": "VLS-128"
    }
)

print(f"摄取完成，创建了 {result.chunks_created} 个 chunks")
print(f"处理时间: {result.processing_time_seconds:.2f} 秒")

# 摄取多个文档
file_paths = [
    "/path/to/激光雷达规格书.pdf",
    "/path/to/激光雷达标定文档.pdf"
]

for file_path in file_paths:
    result = client.ingest(
        file_paths=[file_path],
        collection="ad_knowledge_v01",
        document_type="sensor_doc"
    )
    print(f"摄取 {file_path}: {result.chunks_created} chunks")
```

#### 2.2.3 批量摄取脚本

```python
import os
import json
from ad_knowledge_retrieval import Client

def batch_ingest(docs_dir, metadata_file, collection="ad_knowledge_v01"):
    """批量摄取文档"""
    client = Client(
        api_key=os.getenv("AD_KNOWLEDGE_API_KEY"),
        base_url=os.getenv("AD_KNOWLEDGE_BASE_URL")
    )
    
    # 加载元数据
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata_map = json.load(f)
    
    # 遍历文档目录
    for filename in os.listdir(docs_dir):
        if not filename.endswith('.pdf'):
            continue
        
        file_path = os.path.join(docs_dir, filename)
        metadata = metadata_map.get(filename, {})
        doc_type = metadata.pop('document_type', 'sensor_doc')
        
        try:
            result = client.ingest(
                file_paths=[file_path],
                collection=collection,
                document_type=doc_type,
                metadata=metadata
            )
            print(f"✓ {filename}: {result.chunks_created} chunks")
        except Exception as e:
            print(f"✗ {filename}: {str(e)}")

if __name__ == '__main__':
    batch_ingest(
        docs_dir="/path/to/docs",
        metadata_file="/path/to/metadata.json",
        collection="ad_knowledge_v01"
    )
```

### 2.3 增量更新

系统支持增量更新，基于 SHA256 哈希自动跳过重复文档。

#### 2.3.1 增量摄取流程

```python
# 增量摄取（默认行为）
result = client.ingest(
    file_paths=["/path/to/document.pdf"],
    collection="ad_knowledge_v01",
    document_type="sensor_doc",
    force_reingest=False  # 默认值，跳过重复文档
)

# 强制重新摄取
result = client.ingest(
    file_paths=["/path/to/document.pdf"],
    collection="ad_knowledge_v01",
    document_type="sensor_doc",
    force_reingest=True  # 强制重新摄取，即使文档已存在
)
```

#### 2.3.2 检查文档是否已摄取

```python
# 列出已摄取的文档
documents = client.list_documents(
    collection="ad_knowledge_v01",
    document_type="sensor_doc"
)

# 检查特定文档是否存在
doc_exists = any(
    doc['document_name'] == '激光雷达规格书.pdf'
    for doc in documents
)

if doc_exists:
    print("文档已存在，跳过摄取")
else:
    print("文档不存在，开始摄取")
```

### 2.4 文档更新策略

#### 2.4.1 版本管理

**方案 1：文件名包含版本号**
```
激光雷达规格书_v1.0.pdf
激光雷达规格书_v2.0.pdf
```

**方案 2：元数据包含版本号**
```python
metadata = {
    "sensor_type": "LiDAR",
    "version": "v2.0",
    "update_date": "2024-01-15"
}
```

#### 2.4.2 更新流程

1. **准备新版本文档**
2. **摄取新版本**（使用 force_reingest=True）
3. **验证摄取结果**
4. **测试查询**（确保新版本内容可检索）
5. **删除旧版本**（可选）

```python
# 更新文档
result = client.ingest(
    file_paths=["/path/to/激光雷达规格书_v2.0.pdf"],
    collection="ad_knowledge_v01",
    document_type="sensor_doc",
    metadata={"sensor_type": "LiDAR", "version": "v2.0"},
    force_reingest=True
)

# 验证
response = client.query(
    query="激光雷达的探测距离是多少？",
    collection="ad_knowledge_v01"
)

# 检查引用是否来自新版本
for citation in response.citations:
    print(f"{citation.document_name} - version: {citation.metadata.get('version')}")
```

### 2.5 文档删除

```python
# 删除特定文档
client.delete_document(
    collection="ad_knowledge_v01",
    document_name="激光雷达规格书_v1.0.pdf"
)

# 删除特定类型的所有文档
client.delete_documents(
    collection="ad_knowledge_v01",
    document_type="sensor_doc",
    confirm=True
)
```

### 2.6 摄取监控

#### 2.6.1 摄取报告

每次摄取完成后，系统生成摄取报告：

```json
{
  "ingestion_id": "ing_xyz789",
  "collection": "ad_knowledge_v01",
  "documents_processed": 5,
  "documents_skipped": 2,
  "chunks_created": 125,
  "processing_time_seconds": 320.5,
  "details": [
    {
      "file_path": "/path/to/doc1.pdf",
      "status": "success",
      "chunks_created": 25,
      "processing_time_seconds": 65.2
    },
    {
      "file_path": "/path/to/doc2.pdf",
      "status": "skipped",
      "reason": "Document already exists (SHA256 match)"
    }
  ]
}
```

#### 2.6.2 摄取日志

摄取日志记录在 `logs/ingestion.log`：

```
2024-01-15 10:00:00 INFO Starting ingestion: ing_xyz789
2024-01-15 10:00:05 INFO Processing: 激光雷达规格书.pdf
2024-01-15 10:00:10 INFO Loaded 50 pages
2024-01-15 10:00:15 INFO Split into 25 chunks
2024-01-15 10:00:20 INFO Generated embeddings
2024-01-15 10:00:25 INFO Upserted to Chroma
2024-01-15 10:00:30 INFO Completed: 激光雷达规格书.pdf (25 chunks)
2024-01-15 10:00:35 INFO Ingestion completed: ing_xyz789
```



## 3. 监控和告警配置

### 3.1 监控指标

#### 3.1.1 性能指标

**响应时间**：
- p50: 中位数响应时间（目标: < 2 秒）
- p95: 95% 响应时间（目标: < 3 秒）
- p99: 99% 响应时间（目标: < 4 秒）

**吞吐量**：
- QPS（每秒查询数）
- 并发查询数
- 请求成功率

**缓存性能**：
- 缓存命中率（目标: > 30%）
- 缓存大小
- 缓存驱逐率

#### 3.1.2 质量指标

**引用率**：
- 有引用的响应比例（目标: >= 80%）
- 平均每个响应的引用数量
- 高相关性引用比例（相关性 > 0.8）

**相关性评分**：
- top-1 平均相关性
- top-3 平均相关性
- top-5 平均相关性

**边界拒绝率**：
- 总拒绝率（目标: < 20%）
- 预测性查询拒绝率
- 实时诊断查询拒绝率
- 低相关性查询拒绝率

#### 3.1.3 系统指标

**资源使用**：
- CPU 使用率（目标: < 70%）
- 内存使用率（目标: < 80%）
- 磁盘使用率（目标: < 80%）
- 网络带宽

**数据库性能**：
- Chroma 查询延迟
- BM25 查询延迟
- 数据库连接数

**外部服务**：
- 嵌入服务响应时间
- 重排序服务响应时间
- 生成服务响应时间
- API 调用失败率

### 3.2 监控工具配置

#### 3.2.1 Prometheus 配置

**安装 Prometheus**：
```bash
# 下载 Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
tar xvfz prometheus-2.40.0.linux-amd64.tar.gz
cd prometheus-2.40.0.linux-amd64

# 配置 prometheus.yml
cat > prometheus.yml <<EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ad-knowledge-retrieval'
    static_configs:
      - targets: ['localhost:8000']
EOF

# 启动 Prometheus
./prometheus --config.file=prometheus.yml
```

**指标端点**：
```python
# src/observability/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# 查询计数器
query_counter = Counter(
    'ad_knowledge_queries_total',
    'Total number of queries',
    ['query_type', 'status']
)

# 响应时间直方图
response_time_histogram = Histogram(
    'ad_knowledge_response_time_seconds',
    'Response time in seconds',
    ['query_type']
)

# 引用率指标
citation_rate_gauge = Gauge(
    'ad_knowledge_citation_rate',
    'Citation rate (0-1)'
)

# Boost 应用率
boost_success_rate_gauge = Gauge(
    'ad_knowledge_boost_success_rate',
    'Boost success rate (0-1)'
)
```

#### 3.2.2 Grafana 配置

**安装 Grafana**：
```bash
# 下载 Grafana
wget https://dl.grafana.com/oss/release/grafana-9.3.0.linux-amd64.tar.gz
tar -zxvf grafana-9.3.0.linux-amd64.tar.gz
cd grafana-9.3.0

# 启动 Grafana
./bin/grafana-server
```

**配置数据源**：
1. 访问 http://localhost:3000
2. 登录（默认用户名/密码：admin/admin）
3. 添加 Prometheus 数据源
4. URL: http://localhost:9090

**导入仪表板**：
```json
{
  "dashboard": {
    "title": "自动驾驶知识检索系统",
    "panels": [
      {
        "title": "查询 QPS",
        "targets": [
          {
            "expr": "rate(ad_knowledge_queries_total[5m])"
          }
        ]
      },
      {
        "title": "响应时间 (p50, p95, p99)",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(ad_knowledge_response_time_seconds_bucket[5m]))",
            "legendFormat": "p50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(ad_knowledge_response_time_seconds_bucket[5m]))",
            "legendFormat": "p95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(ad_knowledge_response_time_seconds_bucket[5m]))",
            "legendFormat": "p99"
          }
        ]
      },
      {
        "title": "引用率",
        "targets": [
          {
            "expr": "ad_knowledge_citation_rate"
          }
        ]
      },
      {
        "title": "Boost 成功率",
        "targets": [
          {
            "expr": "ad_knowledge_boost_success_rate"
          }
        ]
      }
    ]
  }
}
```

### 3.3 告警规则配置

#### 3.3.1 Prometheus 告警规则

**创建告警规则文件** `alerts.yml`：
```yaml
groups:
  - name: ad_knowledge_alerts
    interval: 30s
    rules:
      # 性能告警
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(ad_knowledge_response_time_seconds_bucket[5m])) > 6
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "响应时间过高"
          description: "p95 响应时间 > 6 秒，当前值: {{ $value }}s"
      
      - alert: HighErrorRate
        expr: rate(ad_knowledge_queries_total{status="error"}[5m]) / rate(ad_knowledge_queries_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "错误率过高"
          description: "错误率 > 5%，当前值: {{ $value | humanizePercentage }}"
      
      # 质量告警
      - alert: LowCitationRate
        expr: ad_knowledge_citation_rate < 0.7
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "引用率过低"
          description: "引用率 < 70%，当前值: {{ $value | humanizePercentage }}"
      
      - alert: HighRefusalRate
        expr: rate(ad_knowledge_queries_total{status="refused"}[5m]) / rate(ad_knowledge_queries_total[5m]) > 0.3
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "边界拒绝率过高"
          description: "拒绝率 > 30%，当前值: {{ $value | humanizePercentage }}"
      
      # 系统告警
      - alert: HighCPUUsage
        expr: process_cpu_seconds_total > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU 使用率过高"
          description: "CPU 使用率 > 80%"
      
      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / process_virtual_memory_max_bytes > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率过高"
          description: "内存使用率 > 80%"
      
      - alert: DatabaseConnectionFailure
        expr: up{job="chroma"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "数据库连接失败"
          description: "无法连接到 Chroma 数据库"
```

#### 3.3.2 Alertmanager 配置

**安装 Alertmanager**：
```bash
wget https://github.com/prometheus/alertmanager/releases/download/v0.25.0/alertmanager-0.25.0.linux-amd64.tar.gz
tar xvfz alertmanager-0.25.0.linux-amd64.tar.gz
cd alertmanager-0.25.0.linux-amd64
```

**配置 alertmanager.yml**：
```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'email-notifications'

receivers:
  - name: 'email-notifications'
    email_configs:
      - to: 'ops-team@company.com'
        from: 'alertmanager@company.com'
        smarthost: 'smtp.company.com:587'
        auth_username: 'alertmanager@company.com'
        auth_password: 'password'
        headers:
          Subject: '[自动驾驶知识检索系统] {{ .GroupLabels.alertname }}'

  - name: 'slack-notifications'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#ad-knowledge-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

**启动 Alertmanager**：
```bash
./alertmanager --config.file=alertmanager.yml
```

### 3.4 日志管理

#### 3.4.1 日志配置

**日志级别**：
- DEBUG: 详细的调试信息
- INFO: 一般信息（默认）
- WARNING: 警告信息
- ERROR: 错误信息
- CRITICAL: 严重错误

**日志文件**：
```
logs/
├── app.log              # 应用日志
├── query.log            # 查询日志
├── ingestion.log        # 摄取日志
├── boost.log            # Boost 应用日志
├── boundary.log         # 边界拒绝日志
└── error.log            # 错误日志
```

**日志配置** `logging.yaml`：
```yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: detailed
    filename: logs/app.log
    maxBytes: 10485760  # 10MB
    backupCount: 10
  
  query_file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: detailed
    filename: logs/query.log
    maxBytes: 10485760
    backupCount: 10
  
  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: detailed
    filename: logs/error.log
    maxBytes: 10485760
    backupCount: 10

loggers:
  ad_knowledge_retrieval:
    level: INFO
    handlers: [console, file]
    propagate: false
  
  ad_knowledge_retrieval.query:
    level: INFO
    handlers: [query_file]
    propagate: false
  
  ad_knowledge_retrieval.error:
    level: ERROR
    handlers: [error_file]
    propagate: false

root:
  level: INFO
  handlers: [console, file]
```

#### 3.4.2 日志分析

**使用 ELK Stack**：

1. **Elasticsearch**: 存储日志
2. **Logstash**: 收集和处理日志
3. **Kibana**: 可视化日志

**Logstash 配置** `logstash.conf`：
```
input {
  file {
    path => "/path/to/logs/*.log"
    start_position => "beginning"
    codec => json
  }
}

filter {
  if [level] == "ERROR" or [level] == "CRITICAL" {
    mutate {
      add_tag => ["error"]
    }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "ad-knowledge-logs-%{+YYYY.MM.dd}"
  }
}
```



## 4. 性能优化建议

### 4.1 查询性能优化

#### 4.1.1 缓存策略

**查询结果缓存**：
```python
from functools import lru_cache
import hashlib

class QueryCache:
    def __init__(self, max_size=1000, ttl=3600):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def get_cache_key(self, query, collection):
        """生成缓存键"""
        key_str = f"{query}:{collection}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, query, collection):
        """获取缓存"""
        key = self.get_cache_key(query, collection)
        if key in self.cache:
            cached_data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return cached_data
            else:
                del self.cache[key]
        return None
    
    def set(self, query, collection, result):
        """设置缓存"""
        if len(self.cache) >= self.max_size:
            # LRU 驱逐
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        key = self.get_cache_key(query, collection)
        self.cache[key] = (result, time.time())
```

**嵌入向量缓存**：
```python
class EmbeddingCache:
    def __init__(self, max_size=10000):
        self.cache = {}
        self.max_size = max_size
    
    @lru_cache(maxsize=10000)
    def get_embedding(self, text):
        """获取文本嵌入（带缓存）"""
        return self.embedding_model.embed(text)
```

#### 4.1.2 批处理优化

**批量嵌入**：
```python
def batch_embed(texts, batch_size=32):
    """批量计算嵌入"""
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_embeddings = embedding_model.embed_batch(batch)
        embeddings.extend(batch_embeddings)
    return embeddings
```

**批量重排序**：
```python
def batch_rerank(query, chunks, batch_size=64):
    """批量重排序"""
    scores = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        batch_scores = reranker.score_batch(query, batch)
        scores.extend(batch_scores)
    return scores
```

#### 4.1.3 并行处理

**并行检索**：
```python
import asyncio

async def parallel_retrieval(query, collection):
    """并行执行 BM25 和 Dense 检索"""
    bm25_task = asyncio.create_task(bm25_search(query, collection))
    dense_task = asyncio.create_task(dense_search(query, collection))
    
    bm25_results, dense_results = await asyncio.gather(bm25_task, dense_task)
    
    # RRF 融合
    fused_results = rrf_fusion(bm25_results, dense_results)
    return fused_results
```

### 4.2 索引优化

#### 4.2.1 向量索引优化

**HNSW 参数调优**：
```python
# Chroma 配置
chroma_client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./data/db/chroma",
    anonymized_telemetry=False
))

collection = chroma_client.create_collection(
    name="ad_knowledge_v01",
    metadata={
        "hnsw:space": "cosine",
        "hnsw:construction_ef": 200,  # 构建时的搜索深度
        "hnsw:M": 16,                  # 每个节点的连接数
        "hnsw:search_ef": 100          # 搜索时的深度
    }
)
```

**参数说明**：
- `M`: 每个节点的最大连接数（推荐: 16-32）
- `construction_ef`: 构建索引时的搜索深度（推荐: 100-200）
- `search_ef`: 搜索时的深度（推荐: 50-100）

**性能影响**：
- 增加 M：提高召回率，但增加内存和构建时间
- 增加 construction_ef：提高索引质量，但增加构建时间
- 增加 search_ef：提高召回率，但增加查询时间

#### 4.2.2 BM25 索引优化

**预构建倒排索引**：
```python
from rank_bm25 import BM25Okapi

class OptimizedBM25:
    def __init__(self):
        self.index = None
        self.documents = []
    
    def build_index(self, documents):
        """预构建 BM25 索引"""
        tokenized_docs = [doc.split() for doc in documents]
        self.index = BM25Okapi(tokenized_docs)
        self.documents = documents
    
    def search(self, query, top_k=50):
        """快速搜索"""
        tokenized_query = query.split()
        scores = self.index.get_scores(tokenized_query)
        top_indices = np.argsort(scores)[-top_k:][::-1]
        return [(self.documents[i], scores[i]) for i in top_indices]
```

### 4.3 数据库优化

#### 4.3.1 连接池配置

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# 配置连接池
engine = create_engine(
    "postgresql://user:password@localhost/ad_knowledge",
    poolclass=QueuePool,
    pool_size=10,          # 连接池大小
    max_overflow=20,       # 最大溢出连接数
    pool_timeout=30,       # 获取连接超时时间
    pool_recycle=3600      # 连接回收时间
)
```

#### 4.3.2 查询优化

**使用索引**：
```sql
-- 为常用查询字段创建索引
CREATE INDEX idx_document_type ON chunks(document_type);
CREATE INDEX idx_document_name ON chunks(document_name);
CREATE INDEX idx_ingestion_date ON chunks(ingestion_date);
```

**批量操作**：
```python
def batch_upsert(chunks, batch_size=100):
    """批量插入 chunks"""
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        collection.upsert(
            ids=[c.id for c in batch],
            documents=[c.content for c in batch],
            metadatas=[c.metadata for c in batch],
            embeddings=[c.embedding for c in batch]
        )
```

### 4.4 系统资源优化

#### 4.4.1 内存优化

**限制缓存大小**：
```python
# 配置文件
CACHE_CONFIG = {
    "query_cache_size": 1000,      # 查询缓存条目数
    "embedding_cache_size": 10000, # 嵌入缓存条目数
    "max_memory_mb": 2048          # 最大内存使用（MB）
}
```

**定期清理缓存**：
```python
import gc

def cleanup_cache():
    """定期清理缓存"""
    query_cache.clear_expired()
    embedding_cache.clear_expired()
    gc.collect()

# 每小时清理一次
schedule.every(1).hours.do(cleanup_cache)
```

#### 4.4.2 CPU 优化

**多进程处理**：
```python
from multiprocessing import Pool

def process_document(file_path):
    """处理单个文档"""
    # 加载、分割、嵌入
    return chunks

def batch_process_documents(file_paths, num_workers=4):
    """多进程批量处理文档"""
    with Pool(num_workers) as pool:
        results = pool.map(process_document, file_paths)
    return results
```

**异步处理**：
```python
import asyncio

async def async_query(query, collection):
    """异步查询"""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, sync_query, query, collection)
    return result
```

### 4.5 网络优化

#### 4.5.1 压缩响应

```python
from flask import Flask, jsonify
from flask_compress import Compress

app = Flask(__name__)
Compress(app)  # 启用 gzip 压缩

@app.route('/api/v1/query', methods=['POST'])
def query():
    # 响应会自动压缩
    return jsonify(response)
```

#### 4.5.2 CDN 加速

**静态资源使用 CDN**：
```python
# 配置 CDN
CDN_URL = "https://cdn.example.com"

# 静态资源 URL
STATIC_RESOURCES = {
    "logo": f"{CDN_URL}/images/logo.png",
    "css": f"{CDN_URL}/styles/main.css",
    "js": f"{CDN_URL}/scripts/app.js"
}
```



## 5. 故障排查指南

### 5.1 常见问题诊断

#### 5.1.1 查询响应慢

**症状**：查询响应时间 > 5 秒

**可能原因**：
1. 数据库连接慢
2. 嵌入服务响应慢
3. 重排序服务响应慢
4. 缓存未命中
5. 系统资源不足

**诊断步骤**：

```bash
# 1. 检查系统资源
top
htop

# 2. 检查数据库连接
python scripts/check_db_connection.py

# 3. 检查嵌入服务
curl -X POST http://localhost:8001/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "test"}'

# 4. 检查重排序服务
curl -X POST http://localhost:8002/rerank \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "documents": ["doc1", "doc2"]}'

# 5. 查看查询日志
tail -f logs/query.log
```

**解决方案**：

1. **优化数据库查询**：
```python
# 添加索引
CREATE INDEX idx_document_type ON chunks(document_type);

# 使用连接池
engine = create_engine(..., pool_size=20)
```

2. **增加缓存**：
```python
# 增加缓存大小
CACHE_CONFIG = {
    "query_cache_size": 2000,
    "embedding_cache_size": 20000
}
```

3. **扩展资源**：
```bash
# 增加内存
# 增加 CPU 核心数
# 使用 GPU 加速
```

#### 5.1.2 引用率低

**症状**：引用率 < 70%

**可能原因**：
1. 检索结果相关性低
2. Boost 配置不当
3. 重排序效果差
4. 知识库内容不足

**诊断步骤**：

```python
# 1. 检查检索结果相关性
response = client.query(query="test query")
for citation in response.citations:
    print(f"相关性: {citation.relevance_score}")

# 2. 检查 Boost 应用情况
stats = client.get_stats(time_range="24h")
print(f"Boost 成功率: {stats['boost_stats']['boost_success_rate']}")

# 3. 检查重排序效果
# 查看 logs/query.log 中的重排序前后评分
```

**解决方案**：

1. **调整 Boost 权重**：
```python
BOOST_CONFIG = {
    "sensor_query": {
        "sensor_doc": 1.6,  # 增加权重
        "algorithm_doc": 0.7,
    }
}
```

2. **优化重排序模型**：
```python
# 使用更强的重排序模型
reranker = CrossEncoderReranker(
    model_name="BAAI/bge-reranker-large"
)
```

3. **补充知识库内容**：
```bash
# 摄取更多相关文档
python scripts/ingest_documents.py --file-paths /path/to/new/docs/*.pdf
```

#### 5.1.3 边界拒绝率高

**症状**：边界拒绝率 > 30%

**可能原因**：
1. 边界检测过于敏感
2. 用户查询不符合系统能力
3. 知识库覆盖范围不足

**诊断步骤**：

```python
# 1. 查看拒绝日志
with open('logs/boundary.log', 'r') as f:
    refusals = [line for line in f if 'REFUSAL' in line]
    print(f"拒绝数量: {len(refusals)}")

# 2. 分析拒绝类型分布
stats = client.get_stats(time_range="24h")
print(stats['boundary_stats']['refusal_type_distribution'])

# 3. 查看具体拒绝案例
for refusal in refusals[:10]:
    print(refusal)
```

**解决方案**：

1. **调整边界阈值**：
```python
# 降低低相关性阈值
LOW_RELEVANCE_THRESHOLD = 0.25  # 从 0.3 降低到 0.25

# 减少预测性模式
PREDICTIVE_PATTERNS = [
    "预测", "预计",  # 移除 "下一代", "未来趋势"
]
```

2. **改进拒绝消息**：
```python
# 提供更有用的替代建议
def generate_alternatives(query):
    # 分析查询意图
    # 生成具体的替代查询建议
    return alternatives
```

3. **用户教育**：
```markdown
# 在用户指南中明确说明系统能力边界
- 系统可以：查询现有文档中的事实性信息
- 系统不能：预测未来趋势、分析实时数据
```

#### 5.1.4 摄取失败

**症状**：文档摄取失败或部分失败

**可能原因**：
1. 文档格式不支持
2. 文档损坏
3. 内存不足
4. 嵌入服务失败

**诊断步骤**：

```bash
# 1. 查看摄取日志
tail -f logs/ingestion.log

# 2. 检查文档格式
file /path/to/document.pdf

# 3. 尝试手动加载文档
python -c "from langchain.document_loaders import PyPDFLoader; loader = PyPDFLoader('/path/to/document.pdf'); docs = loader.load(); print(len(docs))"

# 4. 检查内存使用
free -h
```

**解决方案**：

1. **转换文档格式**：
```bash
# 使用 LibreOffice 转换
libreoffice --headless --convert-to pdf document.docx
```

2. **修复损坏的 PDF**：
```bash
# 使用 Ghostscript 修复
gs -o repaired.pdf -sDEVICE=pdfwrite -dPDFSETTINGS=/prepress damaged.pdf
```

3. **分批处理大文档**：
```python
def process_large_document(file_path, chunk_size=50):
    """分批处理大文档"""
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    
    for i in range(0, len(pages), chunk_size):
        batch = pages[i:i+chunk_size]
        process_batch(batch)
```

### 5.2 错误代码参考

#### 5.2.1 客户端错误（4xx）

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 400 | 请求参数无效 | 检查请求参数格式和类型 |
| 401 | 未授权 | 提供有效的 API Key |
| 403 | 禁止访问 | 检查访问权限 |
| 404 | 资源不存在 | 检查资源 ID 是否正确 |
| 429 | 速率限制 | 降低请求频率 |

#### 5.2.2 服务器错误（5xx）

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 500 | 服务器内部错误 | 查看错误日志，联系技术支持 |
| 503 | 服务不可用 | 检查服务状态，稍后重试 |
| 504 | 请求超时 | 简化查询或增加超时时间 |

### 5.3 日志分析

#### 5.3.1 查询日志分析

```python
import re
from collections import Counter

def analyze_query_log(log_file):
    """分析查询日志"""
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    # 提取查询类型
    query_types = []
    response_times = []
    
    for line in lines:
        if 'query_type' in line:
            match = re.search(r'query_type: (\w+)', line)
            if match:
                query_types.append(match.group(1))
        
        if 'response_time' in line:
            match = re.search(r'response_time: ([\d.]+)', line)
            if match:
                response_times.append(float(match.group(1)))
    
    # 统计
    print("查询类型分布:")
    for query_type, count in Counter(query_types).most_common():
        print(f"  {query_type}: {count}")
    
    print(f"\n平均响应时间: {sum(response_times) / len(response_times):.2f}s")
    print(f"p95 响应时间: {sorted(response_times)[int(len(response_times) * 0.95)]:.2f}s")
```

#### 5.3.2 错误日志分析

```python
def analyze_error_log(log_file):
    """分析错误日志"""
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    # 提取错误类型
    error_types = []
    
    for line in lines:
        if 'ERROR' in line or 'CRITICAL' in line:
            # 提取错误消息
            match = re.search(r'ERROR - (.+)', line)
            if match:
                error_types.append(match.group(1).split(':')[0])
    
    # 统计
    print("错误类型分布:")
    for error_type, count in Counter(error_types).most_common(10):
        print(f"  {error_type}: {count}")
```

### 5.4 性能调优检查清单

#### 5.4.1 查询性能检查

- [ ] 查询缓存已启用
- [ ] 嵌入缓存已启用
- [ ] 缓存命中率 > 30%
- [ ] 响应时间 p95 < 3 秒
- [ ] 并发查询处理正常

#### 5.4.2 索引性能检查

- [ ] HNSW 参数已优化
- [ ] BM25 索引已预构建
- [ ] 数据库索引已创建
- [ ] 索引大小合理

#### 5.4.3 系统资源检查

- [ ] CPU 使用率 < 70%
- [ ] 内存使用率 < 80%
- [ ] 磁盘使用率 < 80%
- [ ] 网络带宽充足

#### 5.4.4 质量指标检查

- [ ] 引用率 >= 80%
- [ ] Boost 成功率 >= 85%
- [ ] 边界拒绝率 < 20%
- [ ] 相关性评分合理



## 6. 备份与恢复

### 6.1 数据备份策略

#### 6.1.1 备份内容

**需要备份的数据**：
1. Chroma 向量数据库
2. BM25 索引
3. 摄取历史记录
4. 配置文件
5. 日志文件（可选）

#### 6.1.2 备份脚本

```bash
#!/bin/bash
# backup.sh - 自动备份脚本

BACKUP_DIR="/backup/ad-knowledge"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"

# 创建备份目录
mkdir -p $BACKUP_PATH

# 备份 Chroma 数据库
echo "备份 Chroma 数据库..."
cp -r data/db/chroma $BACKUP_PATH/

# 备份 BM25 索引
echo "备份 BM25 索引..."
cp -r data/db/bm25 $BACKUP_PATH/

# 备份摄取历史
echo "备份摄取历史..."
cp data/db/ingestion_history.db $BACKUP_PATH/

# 备份配置文件
echo "备份配置文件..."
cp -r config $BACKUP_PATH/

# 压缩备份
echo "压缩备份..."
tar -czf $BACKUP_PATH.tar.gz -C $BACKUP_DIR backup_$TIMESTAMP

# 删除未压缩的备份
rm -rf $BACKUP_PATH

# 删除 30 天前的备份
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +30 -delete

echo "备份完成: $BACKUP_PATH.tar.gz"
```

#### 6.1.3 定时备份

```bash
# 添加到 crontab
crontab -e

# 每天凌晨 2 点备份
0 2 * * * /path/to/backup.sh >> /var/log/ad-knowledge-backup.log 2>&1
```

### 6.2 数据恢复

#### 6.2.1 恢复脚本

```bash
#!/bin/bash
# restore.sh - 数据恢复脚本

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: ./restore.sh <backup_file.tar.gz>"
    exit 1
fi

# 停止服务
echo "停止服务..."
systemctl stop ad-knowledge-retrieval

# 备份当前数据（以防恢复失败）
echo "备份当前数据..."
mv data/db data/db.backup_$(date +%Y%m%d_%H%M%S)

# 解压备份
echo "解压备份..."
tar -xzf $BACKUP_FILE -C /tmp/

# 恢复数据
echo "恢复数据..."
cp -r /tmp/backup_*/chroma data/db/
cp -r /tmp/backup_*/bm25 data/db/
cp /tmp/backup_*/ingestion_history.db data/db/
cp -r /tmp/backup_*/config ./

# 清理临时文件
rm -rf /tmp/backup_*

# 启动服务
echo "启动服务..."
systemctl start ad-knowledge-retrieval

echo "恢复完成"
```

#### 6.2.2 验证恢复

```python
# verify_restore.py - 验证恢复脚本

from ad_knowledge_retrieval import Client

client = Client(
    api_key="your_api_key",
    base_url="http://localhost:8000/api/v1"
)

# 1. 检查知识库范围
scope = client.get_scope(collection="ad_knowledge_v01")
print(f"文档数量: {scope.document_count}")
print(f"Chunk 数量: {scope.chunk_count}")

# 2. 测试查询
response = client.query(
    query="激光雷达的探测距离是多少？",
    collection="ad_knowledge_v01"
)
print(f"查询成功: {len(response.citations)} 个引用")

# 3. 检查文档列表
documents = client.list_documents(collection="ad_knowledge_v01")
print(f"文档列表: {len(documents)} 个文档")

print("恢复验证完成")
```

### 6.3 灾难恢复计划

#### 6.3.1 RTO 和 RPO

- **RTO (Recovery Time Objective)**: 4 小时
- **RPO (Recovery Point Objective)**: 24 小时

#### 6.3.2 恢复流程

1. **评估损坏程度**（15 分钟）
2. **准备恢复环境**（30 分钟）
3. **恢复数据**（2 小时）
4. **验证恢复**（1 小时）
5. **恢复服务**（30 分钟）

#### 6.3.3 应急联系人

| 角色 | 姓名 | 电话 | 邮箱 |
|------|------|------|------|
| 系统管理员 | 张三 | 138-xxxx-xxxx | zhangsan@company.com |
| 数据库管理员 | 李四 | 139-xxxx-xxxx | lisi@company.com |
| 技术负责人 | 王五 | 137-xxxx-xxxx | wangwu@company.com |

## 7. 安全最佳实践

### 7.1 访问控制

#### 7.1.1 API Key 管理

**生成 API Key**：
```python
import secrets

def generate_api_key():
    """生成安全的 API Key"""
    return secrets.token_urlsafe(32)

# 示例
api_key = generate_api_key()
print(f"API Key: {api_key}")
```

**存储 API Key**：
```python
import hashlib

def hash_api_key(api_key):
    """哈希 API Key 用于存储"""
    return hashlib.sha256(api_key.encode()).hexdigest()

# 存储哈希后的 API Key
hashed_key = hash_api_key(api_key)
# 保存到数据库
```

**验证 API Key**：
```python
def verify_api_key(provided_key, stored_hash):
    """验证 API Key"""
    provided_hash = hash_api_key(provided_key)
    return provided_hash == stored_hash
```

#### 7.1.2 基于角色的访问控制（RBAC）

```python
ROLES = {
    "admin": {
        "permissions": ["query", "ingest", "delete", "manage_users"]
    },
    "user": {
        "permissions": ["query"]
    },
    "developer": {
        "permissions": ["query", "ingest"]
    }
}

def check_permission(user_role, action):
    """检查权限"""
    return action in ROLES.get(user_role, {}).get("permissions", [])
```

### 7.2 数据加密

#### 7.2.1 传输加密

**配置 TLS/SSL**：
```python
from flask import Flask
import ssl

app = Flask(__name__)

# SSL 配置
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain('cert.pem', 'key.pem')

if __name__ == '__main__':
    app.run(ssl_context=context, host='0.0.0.0', port=443)
```

#### 7.2.2 静态数据加密

**加密敏感配置**：
```python
from cryptography.fernet import Fernet

# 生成密钥
key = Fernet.generate_key()
cipher = Fernet(key)

# 加密
encrypted_data = cipher.encrypt(b"sensitive_data")

# 解密
decrypted_data = cipher.decrypt(encrypted_data)
```

### 7.3 审计日志

#### 7.3.1 记录关键操作

```python
import logging

audit_logger = logging.getLogger('audit')

def log_query(user_id, query, collection):
    """记录查询操作"""
    audit_logger.info(f"QUERY | user={user_id} | query={query} | collection={collection}")

def log_ingest(user_id, file_path, collection):
    """记录摄取操作"""
    audit_logger.info(f"INGEST | user={user_id} | file={file_path} | collection={collection}")

def log_delete(user_id, document_name, collection):
    """记录删除操作"""
    audit_logger.warning(f"DELETE | user={user_id} | document={document_name} | collection={collection}")
```

#### 7.3.2 审计日志分析

```python
def analyze_audit_log(log_file):
    """分析审计日志"""
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    # 统计操作类型
    operations = {}
    for line in lines:
        if 'QUERY' in line:
            operations['query'] = operations.get('query', 0) + 1
        elif 'INGEST' in line:
            operations['ingest'] = operations.get('ingest', 0) + 1
        elif 'DELETE' in line:
            operations['delete'] = operations.get('delete', 0) + 1
    
    print("操作统计:")
    for op, count in operations.items():
        print(f"  {op}: {count}")
```

## 8. 维护计划

### 8.1 日常维护

#### 8.1.1 每日检查

- [ ] 检查系统健康状态
- [ ] 查看错误日志
- [ ] 监控性能指标
- [ ] 检查磁盘空间

```bash
#!/bin/bash
# daily_check.sh

echo "=== 每日健康检查 ==="

# 1. 系统健康
curl -s http://localhost:8000/api/v1/health | jq .

# 2. 错误日志
echo "最近的错误:"
tail -20 logs/error.log

# 3. 磁盘空间
echo "磁盘使用:"
df -h | grep -E "/$|/data"

# 4. 性能指标
echo "查询统计:"
curl -s http://localhost:8000/api/v1/stats?time_range=24h | jq '.data.query_stats'
```

#### 8.1.2 每周维护

- [ ] 清理过期日志
- [ ] 优化数据库
- [ ] 检查备份完整性
- [ ] 更新监控仪表板

```bash
#!/bin/bash
# weekly_maintenance.sh

echo "=== 每周维护 ==="

# 1. 清理日志
find logs/ -name "*.log" -mtime +7 -delete

# 2. 优化数据库
python scripts/optimize_database.py

# 3. 验证备份
latest_backup=$(ls -t /backup/ad-knowledge/*.tar.gz | head -1)
echo "最新备份: $latest_backup"
tar -tzf $latest_backup > /dev/null && echo "备份完整" || echo "备份损坏"

# 4. 生成周报
python scripts/generate_weekly_report.py
```

### 8.2 定期维护

#### 8.2.1 每月维护

- [ ] 更新依赖包
- [ ] 安全补丁
- [ ] 性能调优
- [ ] 容量规划

#### 8.2.2 每季度维护

- [ ] 系统升级
- [ ] 灾难恢复演练
- [ ] 安全审计
- [ ] 文档更新

## 9. 总结

本运维指南涵盖了自动驾驶知识检索系统的日常运维、监控、优化和故障排查。

**关键要点**：
1. 定期备份数据，确保数据安全
2. 监控系统性能，及时发现问题
3. 优化查询性能，提升用户体验
4. 遵循安全最佳实践，保护系统安全
5. 制定维护计划，保持系统稳定

**联系支持**：
- 技术支持：support@ad-knowledge-retrieval.com
- 紧急热线：400-xxx-xxxx
- 文档：https://docs.ad-knowledge-retrieval.com
