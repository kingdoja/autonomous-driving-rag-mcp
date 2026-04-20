# 自动驾驶知识检索系统 - API 参考文档

## 1. 概述

本文档提供自动驾驶知识检索系统的完整 API 参考，包括查询接口、摄取接口、评估接口和管理接口。

### 1.1 基础信息

- **API 版本**: v1
- **基础 URL**: `http://localhost:8000/api/v1`
- **认证方式**: API Key（Header: `X-API-Key`）
- **内容类型**: `application/json`
- **字符编码**: UTF-8

### 1.2 通用响应格式

所有 API 响应遵循统一格式：

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123",
    "execution_time_ms": 1250
  }
}
```

错误响应格式：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_QUERY",
    "message": "查询字符串不能为空",
    "details": { ... }
  },
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

## 2. 查询接口

### 2.1 标准查询

**端点**: `POST /query`

**描述**: 查询知识库并获取答案和引用。

**请求体**:

```json
{
  "query": "激光雷达的探测距离是多少？",
  "collection": "ad_knowledge_v01",
  "top_k": 10,
  "enable_boost": true,
  "enable_boundary_check": true,
  "filters": {
    "document_type": "sensor_doc"
  }
}
```

**参数说明**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| query | string | 是 | - | 用户查询字符串 |
| collection | string | 否 | ad_knowledge_v01 | 知识库名称 |
| top_k | integer | 否 | 10 | 返回的最大结果数量 |
| enable_boost | boolean | 否 | true | 是否启用 Metadata Boost |
| enable_boundary_check | boolean | 否 | true | 是否启用边界检查 |
| filters | object | 否 | {} | 元数据过滤器 |

**响应示例**:

```json
{
  "success": true,
  "data": {
    "query": "激光雷达的探测距离是多少？",
    "answer": "根据激光雷达规格书 [1]，Velodyne VLS-128 激光雷达的探测距离为 200 米，分辨率为 0.1°。该激光雷达采用 128 线设计，可提供高精度的 3D 点云数据 [2]。\n\n不同型号的激光雷达探测距离有所不同：\n- VLS-128: 200m\n- HDL-64E: 120m\n- VLP-16: 100m",
    "response_type": "standard",
    "citations": [
      {
        "document_name": "激光雷达规格书.pdf",
        "document_type": "sensor_doc",
        "sensor_type": "LiDAR",
        "section": "技术参数",
        "page": 5,
        "relevance_score": 0.92,
        "authority_score": 0.6,
        "excerpt": "Velodyne VLS-128 激光雷达探测距离: 200m, 分辨率: 0.1°",
        "chunk_id": "chunk_001"
      },
      {
        "document_name": "激光雷达标定文档.pdf",
        "document_type": "sensor_doc",
        "sensor_type": "LiDAR",
        "section": "性能分析",
        "page": 12,
        "relevance_score": 0.88,
        "authority_score": 0.6,
        "excerpt": "128 线激光雷达可提供高精度的 3D 点云数据，适用于 L4/L5 自动驾驶",
        "chunk_id": "chunk_002"
      }
    ],
    "query_analysis": {
      "complexity": "simple",
      "intent": "retrieval",
      "query_type": "sensor_query",
      "requires_multi_doc": false
    },
    "retrieval_stats": {
      "total_chunks_retrieved": 80,
      "chunks_after_boost": 80,
      "chunks_after_rerank": 10,
      "boost_applied": true,
      "boost_type": "sensor_query"
    }
  },
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123",
    "execution_time_ms": 1250
  }
}
```

### 2.2 对比查询

**端点**: `POST /query/compare`

**描述**: 执行对比查询，返回结构化的对比结果。

**请求体**:

```json
{
  "query": "激光雷达 vs 毫米波雷达，哪个更适合自动驾驶？",
  "collection": "ad_knowledge_v01",
  "comparison_items": ["激光雷达", "毫米波雷达"],
  "top_k": 10
}
```

**参数说明**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| query | string | 是 | - | 对比查询字符串 |
| collection | string | 否 | ad_knowledge_v01 | 知识库名称 |
| comparison_items | array | 否 | [] | 对比项列表（可选，系统会自动检测） |
| top_k | integer | 否 | 10 | 每个对比项的最大结果数量 |

**响应示例**:

```json
{
  "success": true,
  "data": {
    "query": "激光雷达 vs 毫米波雷达，哪个更适合自动驾驶？",
    "answer": "## 传感器方案对比\n\n### 1. 激光雷达 (LiDAR) [1][2]\n\n**技术参数:**\n- 探测距离: 200m\n- 分辨率: 0.1°\n- 视场角: 360°\n\n**优点:** 高精度、远距离探测、3D 点云\n**缺点:** 成本高、受天气影响\n\n### 2. 毫米波雷达 (Radar) [3][4]\n\n**技术参数:**\n- 探测距离: 150m\n- 分辨率: 1°\n- 视场角: 120°\n\n**优点:** 全天候、成本低\n**缺点:** 分辨率低\n\n**对比总结:**\n激光雷达适合高精度场景，毫米波雷达适合全天候应用。",
    "response_type": "comparison",
    "comparison_result": {
      "items": [
        {
          "name": "激光雷达",
          "type": "LiDAR",
          "parameters": {
            "探测距离": "200m",
            "分辨率": "0.1°",
            "视场角": "360°"
          },
          "advantages": ["高精度", "远距离探测", "3D 点云"],
          "disadvantages": ["成本高", "受天气影响"],
          "citations": ["[1]", "[2]"]
        },
        {
          "name": "毫米波雷达",
          "type": "Radar",
          "parameters": {
            "探测距离": "150m",
            "分辨率": "1°",
            "视场角": "120°"
          },
          "advantages": ["全天候", "成本低"],
          "disadvantages": ["分辨率低"],
          "citations": ["[3]", "[4]"]
        }
      ],
      "summary": "激光雷达适合高精度场景，毫米波雷达适合全天候应用。"
    },
    "citations": [ ... ]
  },
  "metadata": { ... }
}
```



### 2.3 范围查询

**端点**: `GET /scope`

**描述**: 查询知识库的覆盖范围和统计信息。

**请求参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| collection | string | 否 | ad_knowledge_v01 | 知识库名称 |

**响应示例**:

```json
{
  "success": true,
  "data": {
    "collection_name": "ad_knowledge_v01",
    "document_types": ["sensor_doc", "algorithm_doc", "regulation_doc", "test_doc"],
    "document_count": 26,
    "chunk_count": 125,
    "coverage_areas": [
      "传感器技术（摄像头、激光雷达、毫米波雷达、超声波雷达）",
      "算法模块（感知、规划、控制）",
      "法规标准（GB/T、ISO 26262、测试规范）",
      "测试场景（功能测试、安全测试、边界场景）"
    ],
    "statistics": {
      "sensor_doc": 5,
      "algorithm_doc": 8,
      "regulation_doc": 3,
      "test_doc": 10
    },
    "last_updated": "2024-01-15T08:00:00Z"
  },
  "metadata": { ... }
}
```

## 3. 摄取接口

### 3.1 摄取文档

**端点**: `POST /ingest`

**描述**: 摄取文档到知识库。

**请求体**:

```json
{
  "file_paths": [
    "/path/to/激光雷达规格书.pdf",
    "/path/to/摄像头规格书.pdf"
  ],
  "collection": "ad_knowledge_v01",
  "document_type": "sensor_doc",
  "metadata": {
    "sensor_type": "LiDAR",
    "manufacturer": "Velodyne",
    "model": "VLS-128"
  },
  "force_reingest": false
}
```

**参数说明**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| file_paths | array | 是 | - | 文档文件路径列表 |
| collection | string | 否 | ad_knowledge_v01 | 目标知识库名称 |
| document_type | string | 是 | - | 文档类型（sensor_doc, algorithm_doc, regulation_doc, test_doc） |
| metadata | object | 否 | {} | 额外的元数据 |
| force_reingest | boolean | 否 | false | 是否强制重新摄取（忽略 SHA256 检查） |

**响应示例**:

```json
{
  "success": true,
  "data": {
    "ingestion_id": "ing_xyz789",
    "collection": "ad_knowledge_v01",
    "documents_processed": 2,
    "documents_skipped": 0,
    "chunks_created": 45,
    "processing_time_seconds": 120.5,
    "details": [
      {
        "file_path": "/path/to/激光雷达规格书.pdf",
        "status": "success",
        "chunks_created": 25,
        "sha256": "abc123...",
        "processing_time_seconds": 65.2
      },
      {
        "file_path": "/path/to/摄像头规格书.pdf",
        "status": "success",
        "chunks_created": 20,
        "sha256": "def456...",
        "processing_time_seconds": 55.3
      }
    ]
  },
  "metadata": { ... }
}
```

### 3.2 检查摄取状态

**端点**: `GET /ingest/{ingestion_id}`

**描述**: 检查摄取任务的状态。

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ingestion_id | string | 是 | 摄取任务 ID |

**响应示例**:

```json
{
  "success": true,
  "data": {
    "ingestion_id": "ing_xyz789",
    "status": "completed",
    "progress": 100,
    "documents_processed": 2,
    "chunks_created": 45,
    "started_at": "2024-01-15T09:00:00Z",
    "completed_at": "2024-01-15T09:02:00Z"
  },
  "metadata": { ... }
}
```

### 3.3 列出已摄取文档

**端点**: `GET /documents`

**描述**: 列出知识库中的所有文档。

**请求参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| collection | string | 否 | ad_knowledge_v01 | 知识库名称 |
| document_type | string | 否 | - | 过滤文档类型 |
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 20 | 每页数量 |

**响应示例**:

```json
{
  "success": true,
  "data": {
    "documents": [
      {
        "document_name": "激光雷达规格书.pdf",
        "document_type": "sensor_doc",
        "sensor_type": "LiDAR",
        "chunk_count": 25,
        "ingestion_date": "2024-01-15T09:00:00Z",
        "sha256": "abc123..."
      },
      {
        "document_name": "摄像头规格书.pdf",
        "document_type": "sensor_doc",
        "sensor_type": "Camera",
        "chunk_count": 20,
        "ingestion_date": "2024-01-15T09:00:00Z",
        "sha256": "def456..."
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_pages": 2,
      "total_documents": 26
    }
  },
  "metadata": { ... }
}
```

## 4. 评估接口

### 4.1 运行评估

**端点**: `POST /evaluation/run`

**描述**: 运行评估测试集。

**请求体**:

```json
{
  "test_set_path": "/path/to/ad_test_set.json",
  "collection": "ad_knowledge_v01",
  "output_path": "/path/to/evaluation_report.json"
}
```

**参数说明**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| test_set_path | string | 是 | - | 测试集 JSON 文件路径 |
| collection | string | 否 | ad_knowledge_v01 | 知识库名称 |
| output_path | string | 否 | - | 评估报告输出路径 |

**响应示例**:

```json
{
  "success": true,
  "data": {
    "evaluation_id": "eval_123",
    "test_set": "ad_test_set.json",
    "collection": "ad_knowledge_v01",
    "total_scenarios": 20,
    "passed_scenarios": 17,
    "failed_scenarios": 3,
    "pass_rate": 0.85,
    "citation_rate": 0.88,
    "average_response_time_ms": 1350,
    "scenario_breakdown": {
      "sensor_query": {
        "total": 5,
        "passed": 5,
        "pass_rate": 1.0
      },
      "algorithm_query": {
        "total": 5,
        "passed": 4,
        "pass_rate": 0.8
      },
      "regulation_query": {
        "total": 3,
        "passed": 3,
        "pass_rate": 1.0
      },
      "comparison_query": {
        "total": 4,
        "passed": 3,
        "pass_rate": 0.75
      },
      "boundary_query": {
        "total": 3,
        "passed": 2,
        "pass_rate": 0.67
      }
    },
    "failed_scenarios_details": [
      {
        "scenario_id": "S8",
        "query": "感知算法的实时性能如何？",
        "expected_doc_types": ["algorithm_doc"],
        "actual_doc_types": ["sensor_doc", "test_doc"],
        "reason": "未返回算法文档"
      }
    ]
  },
  "metadata": { ... }
}
```

### 4.2 获取评估报告

**端点**: `GET /evaluation/{evaluation_id}`

**描述**: 获取评估报告详情。

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| evaluation_id | string | 是 | 评估任务 ID |

**响应示例**:

```json
{
  "success": true,
  "data": {
    "evaluation_id": "eval_123",
    "status": "completed",
    "pass_rate": 0.85,
    "citation_rate": 0.88,
    "report_url": "/reports/eval_123.json",
    "created_at": "2024-01-15T10:00:00Z",
    "completed_at": "2024-01-15T10:05:00Z"
  },
  "metadata": { ... }
}
```

## 5. 管理接口

### 5.1 健康检查

**端点**: `GET /health`

**描述**: 检查系统健康状态。

**响应示例**:

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "components": {
      "database": {
        "status": "healthy",
        "response_time_ms": 5
      },
      "embedding_service": {
        "status": "healthy",
        "response_time_ms": 120
      },
      "reranker_service": {
        "status": "healthy",
        "response_time_ms": 80
      }
    },
    "uptime_seconds": 86400
  },
  "metadata": { ... }
}
```

### 5.2 获取统计信息

**端点**: `GET /stats`

**描述**: 获取系统统计信息。

**请求参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| time_range | string | 否 | 24h | 时间范围（1h, 24h, 7d, 30d） |

**响应示例**:

```json
{
  "success": true,
  "data": {
    "time_range": "24h",
    "query_stats": {
      "total_queries": 1250,
      "successful_queries": 1180,
      "failed_queries": 70,
      "success_rate": 0.944,
      "average_response_time_ms": 1350,
      "p50_response_time_ms": 1200,
      "p95_response_time_ms": 2500,
      "p99_response_time_ms": 3800
    },
    "query_type_distribution": {
      "sensor_query": 450,
      "algorithm_query": 380,
      "regulation_query": 220,
      "test_query": 150,
      "general": 50
    },
    "boost_stats": {
      "boost_applied_count": 1050,
      "boost_success_rate": 0.92,
      "top_k_verification_success_rate": 0.88
    },
    "boundary_stats": {
      "total_refusals": 120,
      "refusal_rate": 0.096,
      "refusal_type_distribution": {
        "predictive": 50,
        "diagnostic": 30,
        "low_relevance": 40
      }
    },
    "citation_stats": {
      "citation_rate": 0.88,
      "average_citations_per_response": 3.2
    }
  },
  "metadata": { ... }
}
```



## 6. 错误码

### 6.1 客户端错误（4xx）

| 错误码 | HTTP 状态 | 说明 | 解决方案 |
|--------|-----------|------|----------|
| INVALID_QUERY | 400 | 查询字符串无效或为空 | 提供有效的查询字符串 |
| INVALID_COLLECTION | 400 | 知识库名称无效 | 检查知识库名称是否正确 |
| INVALID_DOCUMENT_TYPE | 400 | 文档类型无效 | 使用有效的文档类型（sensor_doc, algorithm_doc, regulation_doc, test_doc） |
| INVALID_PARAMETERS | 400 | 请求参数无效 | 检查请求参数格式和类型 |
| UNAUTHORIZED | 401 | 未提供或无效的 API Key | 提供有效的 API Key |
| FORBIDDEN | 403 | 无权访问该资源 | 检查访问权限 |
| NOT_FOUND | 404 | 资源不存在 | 检查资源 ID 是否正确 |
| RATE_LIMIT_EXCEEDED | 429 | 超过速率限制 | 降低请求频率或联系管理员 |

### 6.2 服务器错误（5xx）

| 错误码 | HTTP 状态 | 说明 | 解决方案 |
|--------|-----------|------|----------|
| INTERNAL_ERROR | 500 | 服务器内部错误 | 联系技术支持 |
| DATABASE_ERROR | 500 | 数据库连接或查询错误 | 检查数据库状态 |
| EMBEDDING_SERVICE_ERROR | 500 | 嵌入服务错误 | 检查嵌入服务状态 |
| RERANKER_SERVICE_ERROR | 500 | 重排序服务错误 | 检查重排序服务状态 |
| SERVICE_UNAVAILABLE | 503 | 服务暂时不可用 | 稍后重试 |
| TIMEOUT | 504 | 请求超时 | 简化查询或增加超时时间 |

### 6.3 错误响应示例

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_QUERY",
    "message": "查询字符串不能为空",
    "details": {
      "field": "query",
      "constraint": "non_empty"
    }
  },
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

## 7. 认证与授权

### 7.1 API Key 认证

所有 API 请求需要在 HTTP Header 中包含 API Key：

```
X-API-Key: your_api_key_here
```

**获取 API Key**：
1. 联系系统管理员申请 API Key
2. 妥善保管 API Key，不要泄露
3. 定期轮换 API Key

### 7.2 速率限制

不同级别的 API Key 有不同的速率限制：

| 级别 | 每分钟请求数 | 每天请求数 |
|------|-------------|-----------|
| 基础 | 60 | 5000 |
| 标准 | 300 | 20000 |
| 高级 | 1000 | 100000 |

超过速率限制时，API 返回 429 错误，响应头包含：

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705315200
```

## 8. SDK 和客户端库

### 8.1 Python SDK

**安装**:

```bash
pip install ad-knowledge-retrieval-sdk
```

**使用示例**:

```python
from ad_knowledge_retrieval import Client

# 初始化客户端
client = Client(
    api_key="your_api_key_here",
    base_url="http://localhost:8000/api/v1"
)

# 标准查询
response = client.query(
    query="激光雷达的探测距离是多少？",
    collection="ad_knowledge_v01",
    top_k=10
)

print(response.answer)
for citation in response.citations:
    print(f"[{citation.document_name}] {citation.excerpt}")

# 对比查询
comparison = client.compare(
    query="激光雷达 vs 毫米波雷达",
    collection="ad_knowledge_v01"
)

print(comparison.answer)

# 范围查询
scope = client.get_scope(collection="ad_knowledge_v01")
print(f"文档数量: {scope.document_count}")
print(f"覆盖领域: {scope.coverage_areas}")

# 摄取文档
ingestion = client.ingest(
    file_paths=["/path/to/document.pdf"],
    collection="ad_knowledge_v01",
    document_type="sensor_doc",
    metadata={"sensor_type": "LiDAR"}
)

print(f"摄取完成，创建了 {ingestion.chunks_created} 个 chunks")
```

### 8.2 JavaScript SDK

**安装**:

```bash
npm install ad-knowledge-retrieval-sdk
```

**使用示例**:

```javascript
const { Client } = require('ad-knowledge-retrieval-sdk');

// 初始化客户端
const client = new Client({
  apiKey: 'your_api_key_here',
  baseUrl: 'http://localhost:8000/api/v1'
});

// 标准查询
const response = await client.query({
  query: '激光雷达的探测距离是多少？',
  collection: 'ad_knowledge_v01',
  topK: 10
});

console.log(response.answer);
response.citations.forEach(citation => {
  console.log(`[${citation.documentName}] ${citation.excerpt}`);
});

// 对比查询
const comparison = await client.compare({
  query: '激光雷达 vs 毫米波雷达',
  collection: 'ad_knowledge_v01'
});

console.log(comparison.answer);

// 范围查询
const scope = await client.getScope({
  collection: 'ad_knowledge_v01'
});

console.log(`文档数量: ${scope.documentCount}`);
console.log(`覆盖领域: ${scope.coverageAreas}`);
```

## 9. 集成指南

### 9.1 集成步骤

1. **获取 API Key**：
   - 联系系统管理员申请 API Key
   - 选择合适的速率限制级别

2. **安装 SDK**（可选）：
   - Python: `pip install ad-knowledge-retrieval-sdk`
   - JavaScript: `npm install ad-knowledge-retrieval-sdk`

3. **初始化客户端**：
   - 配置 API Key 和 Base URL
   - 测试连接（调用健康检查接口）

4. **摄取文档**：
   - 准备文档文件（PDF 格式）
   - 为文档添加元数据标签
   - 调用摄取接口

5. **测试查询**：
   - 执行简单查询测试
   - 验证响应格式和引用质量
   - 测试对比查询和范围查询

6. **集成到应用**：
   - 在应用中调用查询接口
   - 处理响应和错误
   - 实现缓存和重试逻辑

### 9.2 最佳实践

1. **查询优化**：
   - 使用具体的关键词和术语
   - 避免过于宽泛的查询
   - 对于复杂问题，拆分为多个简单查询

2. **错误处理**：
   - 实现重试逻辑（指数退避）
   - 处理速率限制错误
   - 记录错误日志用于分析

3. **性能优化**：
   - 实现客户端缓存
   - 批量处理多个查询
   - 使用异步请求

4. **安全性**：
   - 不要在客户端代码中硬编码 API Key
   - 使用环境变量或密钥管理服务
   - 定期轮换 API Key

### 9.3 集成示例：Web 应用

```python
from flask import Flask, request, jsonify
from ad_knowledge_retrieval import Client
import os

app = Flask(__name__)

# 初始化客户端
client = Client(
    api_key=os.getenv("AD_KNOWLEDGE_API_KEY"),
    base_url=os.getenv("AD_KNOWLEDGE_BASE_URL")
)

@app.route('/api/search', methods=['POST'])
def search():
    """搜索接口"""
    try:
        data = request.json
        query = data.get('query')
        
        if not query:
            return jsonify({"error": "查询不能为空"}), 400
        
        # 调用知识检索系统
        response = client.query(
            query=query,
            collection="ad_knowledge_v01",
            top_k=10
        )
        
        # 返回结果
        return jsonify({
            "answer": response.answer,
            "citations": [
                {
                    "document": c.document_name,
                    "section": c.section,
                    "page": c.page,
                    "excerpt": c.excerpt
                }
                for c in response.citations
            ]
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

### 9.4 集成示例：命令行工具

```python
import click
from ad_knowledge_retrieval import Client
import os

@click.group()
def cli():
    """自动驾驶知识检索命令行工具"""
    pass

@cli.command()
@click.argument('query')
@click.option('--collection', default='ad_knowledge_v01', help='知识库名称')
@click.option('--top-k', default=10, help='返回结果数量')
def query(query, collection, top_k):
    """查询知识库"""
    client = Client(
        api_key=os.getenv("AD_KNOWLEDGE_API_KEY"),
        base_url=os.getenv("AD_KNOWLEDGE_BASE_URL")
    )
    
    response = client.query(
        query=query,
        collection=collection,
        top_k=top_k
    )
    
    click.echo(f"\n答案:\n{response.answer}\n")
    click.echo("引用:")
    for i, citation in enumerate(response.citations, 1):
        click.echo(f"[{i}] {citation.document_name} - {citation.section} (p.{citation.page})")

@cli.command()
@click.argument('file_path')
@click.option('--collection', default='ad_knowledge_v01', help='知识库名称')
@click.option('--doc-type', required=True, help='文档类型')
def ingest(file_path, collection, doc_type):
    """摄取文档"""
    client = Client(
        api_key=os.getenv("AD_KNOWLEDGE_API_KEY"),
        base_url=os.getenv("AD_KNOWLEDGE_BASE_URL")
    )
    
    result = client.ingest(
        file_paths=[file_path],
        collection=collection,
        document_type=doc_type
    )
    
    click.echo(f"摄取完成！")
    click.echo(f"创建了 {result.chunks_created} 个 chunks")
    click.echo(f"处理时间: {result.processing_time_seconds:.2f} 秒")

if __name__ == '__main__':
    cli()
```

## 10. 版本历史

### v1.0.0 (2024-01-15)

**新功能**:
- 标准查询接口
- 对比查询接口
- 范围查询接口
- 文档摄取接口
- 评估接口
- Metadata Boost 功能
- 边界控制功能

**改进**:
- 优化检索性能
- 增强引用质量
- 改进错误处理

**已知问题**:
- 暂不支持图片查询
- 暂不支持实时更新

## 11. 支持与反馈

### 11.1 技术支持

- **邮箱**: support@ad-knowledge-retrieval.com
- **文档**: https://docs.ad-knowledge-retrieval.com
- **GitHub**: https://github.com/ad-knowledge-retrieval

### 11.2 反馈渠道

- **Bug 报告**: https://github.com/ad-knowledge-retrieval/issues
- **功能请求**: https://github.com/ad-knowledge-retrieval/discussions
- **社区论坛**: https://community.ad-knowledge-retrieval.com

### 11.3 SLA

- **可用性**: 99.9%
- **响应时间**: p95 < 3 秒
- **支持响应**: 工作日 24 小时内

