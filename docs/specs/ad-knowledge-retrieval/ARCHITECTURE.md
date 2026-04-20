# 自动驾驶知识检索系统 - 架构文档

## 1. 系统概述

### 1.1 系统简介

自动驾驶知识检索系统（Autonomous Driving Knowledge Retrieval System）是一个基于 RAG（Retrieval-Augmented Generation）架构的智能知识检索平台，专门为自动驾驶研发团队设计。系统通过混合检索、智能重排序和多文档推理技术，帮助工程师快速获取传感器、算法、法规和测试相关的专业知识。

### 1.2 核心特性

- **领域专注**：专门针对自动驾驶领域优化，支持传感器、算法、法规、测试四大文档类型
- **智能检索**：结合 BM25 稀疏检索和 Dense Embedding 稠密检索的混合检索策略
- **元数据增强**：针对传感器查询应用 Metadata Boost 权重提升，确保精准匹配
- **多文档推理**：支持传感器方案对比、算法方案对比、多传感器融合等复杂查询
- **术语适配**：支持中英文混合查询和自动驾驶专业术语识别（LiDAR、ADAS、ODD、V2X、SLAM）
- **边界控制**：智能识别并拒绝超出系统能力的查询（预测性分析、实时诊断）
- **高质量引用**：提供详细的文档引用，包含文档名称、章节/页码、相关性评分

### 1.3 技术栈

- **检索框架**：LangChain
- **向量数据库**：Chroma
- **稀疏检索**：BM25
- **重排序**：Cross-Encoder Reranker
- **嵌入模型**：OpenAI text-embedding-3-small / Zhipu embedding-3
- **生成模型**：OpenAI GPT-4 / Zhipu GLM-4
- **编程语言**：Python 3.10+

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                          用户查询接口                              │
│                    (CLI / API / MCP Server)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      查询处理层 (Query Layer)                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │Query Analyzer│  │Query Processor│ │Scope Provider│          │
│  │查询分析       │  │查询处理       │  │范围提供      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      检索层 (Retrieval Layer)                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │Hybrid Search │  │Metadata      │  │Document      │          │
│  │混合检索       │  │Booster       │  │Grouper       │          │
│  │(BM25+Dense)  │  │元数据增强     │  │文档分组      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      重排序层 (Reranking Layer)                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐           │
│  │         Cross-Encoder Reranker                   │           │
│  │         (精细化相关性评分)                         │           │
│  └──────────────────────────────────────────────────┘           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      响应生成层 (Response Layer)                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │Citation      │  │Response      │  │Boundary      │          │
│  │Enhancer      │  │Builder       │  │Validator     │          │
│  │引用增强       │  │响应构建       │  │边界验证      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      知识库层 (Knowledge Base)                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │Chroma Vector │  │BM25 Index    │  │Ingestion     │          │
│  │Database      │  │稀疏索引       │  │Pipeline      │          │
│  │向量数据库     │  │              │  │摄取流水线     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流图

```
用户查询 "激光雷达的探测距离是多少？"
    │
    ▼
[Query Analyzer] 分析查询复杂度和意图
    │ complexity: simple
    │ intent: retrieval
    │ query_type: sensor_query
    ▼
[Query Processor] 提取关键词和术语
    │ keywords: ["激光雷达", "探测距离"]
    │ detected_terms: ["LiDAR"]
    ▼
[Hybrid Search] 混合检索
    │ BM25 检索: 50 个候选 chunks
    │ Dense 检索: 50 个候选 chunks
    │ RRF 融合: 合并为 80 个 chunks
    ▼
[Metadata Booster] 应用权重提升
    │ 检测到 sensor_query
    │ 对 sensor_doc 类型应用 1.5x boost
    │ 重新排序后: 传感器文档优先
    ▼
[Reranker] Cross-Encoder 重排序
    │ 精细化相关性评分
    │ 选择 top-10 chunks
    ▼
[Document Grouper] 按文档分组
    │ 按来源文档分组
    │ 每个文档保留 top-3 chunks
    ▼
[Citation Enhancer] 增强引用信息
    │ 提取文档名称、章节、页码
    │ 计算权威性评分
    │ 排序引用
    ▼
[Response Builder] 构建响应
    │ 综合多个文档的信息
    │ 生成结构化答案
    │ 包含详细引用
    ▼
[Boundary Validator] 边界验证
    │ 检查相关性阈值
    │ 检测预测性查询
    │ 验证通过
    ▼
返回响应给用户
```



## 3. 核心组件详解

### 3.1 Query Analyzer（查询分析器）

**职责**：分析用户查询的复杂度和意图，路由到合适的处理流程。

**输入**：
- 原始用户查询字符串

**输出**：
- `QueryAnalysis` 对象，包含：
  - `complexity`: 查询复杂度（simple, multi_part, comparison, aggregation）
  - `intent`: 查询意图（retrieval, boundary, scope_inquiry）
  - `sub_queries`: 子查询列表（用于多部分查询）
  - `requires_multi_doc`: 是否需要多文档推理
  - `query_type`: 查询类型（sensor_query, algorithm_query, regulation_query）

**关键逻辑**：
1. **复杂度检测**：
   - Simple: 单一问题，直接检索
   - Multi-part: 包含多个子问题（"and", "以及", "还有"）
   - Comparison: 对比查询（"vs", "对比", "优缺点"）
   - Aggregation: 汇总查询（"融合方案", "技术选型"）

2. **意图分类**：
   - Retrieval: 标准知识检索
   - Boundary: 超出系统能力（预测、诊断）
   - Scope_inquiry: 查询系统范围

3. **查询类型识别**：
   - Sensor_query: 包含传感器名称或参数
   - Algorithm_query: 包含算法模块或方法
   - Regulation_query: 包含法规标准关键词

**代码位置**：`src/core/query_engine/query_analyzer.py`

### 3.2 Query Processor（查询处理器）

**职责**：预处理查询，提取关键词和过滤器，识别自动驾驶专业术语。

**输入**：
- 原始查询字符串

**输出**：
- `ProcessedQuery` 对象，包含：
  - `original_query`: 原始查询
  - `keywords`: 提取的关键词列表
  - `filters`: 元数据过滤器
  - `detected_terms`: 检测到的专业术语
  - `term_types`: 术语类型映射

**术语识别能力**：
- **传感器术语**：LiDAR, Camera, Radar, Ultrasonic, 激光雷达, 摄像头, 毫米波雷达, 超声波雷达
- **算法术语**：Perception, Planning, Control, SLAM, 感知, 规划, 控制, 目标检测, 路径规划
- **系统术语**：ADAS, ODD, V2X, MPC, PID, 自动驾驶分级, 功能安全
- **法规术语**：GB/T, ISO 26262, ASIL, 国家标准, 测试规范

**同义词映射**：
- "激光雷达" ↔ "LiDAR"
- "摄像头" ↔ "Camera"
- "毫米波雷达" ↔ "Radar"
- "感知" ↔ "Perception"
- "规划" ↔ "Planning"

**代码位置**：`src/core/query_engine/query_analyzer.py`

### 3.3 Metadata Booster（元数据增强器）⭐ 新组件

**职责**：针对特定查询类型应用元数据权重提升，确保相关文档类型优先返回。

**核心价值**：解决传感器查询时算法文档排名过高的问题，通过动态权重调整确保文档类型匹配。

**工作原理**：

1. **查询类型检测**：
```python
def detect_query_type(query: str) -> str:
    # 传感器查询检测
    if any(sensor in query for sensor in ["摄像头", "激光雷达", "LiDAR", "Camera"]):
        return "sensor_query"
    
    # 算法查询检测
    if any(algo in query for algo in ["感知", "规划", "控制", "Perception"]):
        return "algorithm_query"
    
    # 法规查询检测
    if any(reg in query for reg in ["GB/T", "ISO 26262", "国家标准"]):
        return "regulation_query"
    
    return "general"
```

2. **权重配置**：
```python
BOOST_CONFIG = {
    "sensor_query": {
        "sensor_doc": 1.5,      # 传感器文档权重提升 50%
        "algorithm_doc": 0.8,   # 算法文档权重降低 20%
    },
    "algorithm_query": {
        "algorithm_doc": 1.3,   # 算法文档权重提升 30%
        "sensor_doc": 0.9,
    },
    "regulation_query": {
        "regulation_doc": 1.6,  # 法规文档权重提升 60%
        "test_doc": 1.2,
    },
}
```

3. **权重应用**：
```python
def apply_boost(chunks: List[RetrievalResult], query_type: str) -> List[RetrievalResult]:
    boost_weights = BOOST_CONFIG.get(query_type, {})
    
    for chunk in chunks:
        doc_type = chunk.metadata.get("document_type")
        boost_factor = boost_weights.get(doc_type, 1.0)
        chunk.score *= boost_factor
    
    # 重新排序
    chunks.sort(key=lambda x: x.score, reverse=True)
    return chunks
```

4. **Top-K 验证**：
```python
def verify_top_k(chunks: List[RetrievalResult], target_doc_type: str, k: int = 3) -> bool:
    top_k_chunks = chunks[:k]
    target_count = sum(1 for c in top_k_chunks if c.metadata.get("document_type") == target_doc_type)
    return target_count >= 2  # 至少 2 个来自目标文档类型
```

**代码位置**：`src/core/query_engine/metadata_booster.py`

### 3.4 Hybrid Search（混合检索）

**职责**：结合 BM25 稀疏检索和 Dense Embedding 稠密检索，通过 RRF 融合获得最佳检索结果。

**检索策略**：

1. **BM25 稀疏检索**：
   - 基于词频和逆文档频率
   - 擅长精确关键词匹配
   - 检索 top-50 候选

2. **Dense Embedding 检索**：
   - 基于语义向量相似度
   - 擅长语义理解和同义词匹配
   - 检索 top-50 候选

3. **RRF 融合**（Reciprocal Rank Fusion）：
```python
def rrf_score(rank: int, k: int = 60) -> float:
    return 1.0 / (k + rank)

# 合并两个检索结果
for chunk_id, rank in bm25_results.items():
    final_score[chunk_id] += rrf_score(rank)

for chunk_id, rank in dense_results.items():
    final_score[chunk_id] += rrf_score(rank)
```

**代码位置**：`src/core/query_engine/hybrid_search.py`



### 3.5 Document Grouper（文档分组器）

**职责**：按来源文档分组检索结果，支持多文档推理和对比查询。

**核心功能**：

1. **按文档分组**：
```python
def group_by_document(chunks: List[RetrievalResult], top_k_per_doc: int = 3):
    grouped = defaultdict(list)
    
    for chunk in chunks:
        doc_name = chunk.metadata.get("document_name")
        grouped[doc_name].append(chunk)
    
    # 每个文档保留 top-k chunks
    for doc_name in grouped:
        grouped[doc_name] = sorted(grouped[doc_name], key=lambda x: x.score, reverse=True)[:top_k_per_doc]
    
    return grouped
```

2. **确保文档多样性**：
```python
def ensure_diversity(grouped: Dict[str, List], min_docs: int = 2):
    if len(grouped) < min_docs:
        # 警告：文档数量不足
        logger.warning(f"Only {len(grouped)} documents found, expected at least {min_docs}")
    
    return grouped
```

**应用场景**：
- 传感器方案对比：确保至少 2 个不同传感器文档
- 算法方案对比：确保至少 2 个不同算法文档
- 多传感器融合：确保 3-5 个传感器文档

**代码位置**：`src/core/query_engine/fusion.py`

### 3.6 Citation Enhancer（引用增强器）

**职责**：丰富引用信息，提供详细的元数据以便追溯和验证。

**增强内容**：

1. **基础元数据**：
   - 文档名称
   - 文档类型（sensor_doc, algorithm_doc, regulation_doc, test_doc）
   - 章节/页码引用

2. **评分信息**：
   - 相关性评分（来自 Reranker）
   - 权威性评分（基于文档类型）

3. **内容摘要**：
   - 关键句子提取
   - 支持答案的具体内容

**权威性评分规则**：
```python
DOCUMENT_AUTHORITY = {
    "regulation_doc": 1.0,    # 法规文档最高权威性
    "algorithm_doc": 0.8,     # 算法文档次之
    "sensor_doc": 0.6,        # 传感器文档
    "test_doc": 0.4,          # 测试文档最低
}
```

**引用排序**：
1. 首先按相关性评分排序（降序）
2. 相关性相近时（差异 < 10%），按权威性评分排序
3. 确保高权威性文档（法规）优先展示

**代码位置**：`src/core/response/citation_enhancer.py`

### 3.7 Response Builder（响应构建器）

**职责**：从多个文档综合信息，生成结构化响应。

**响应类型**：

1. **标准响应**（Standard Response）：
   - 单一问题的直接回答
   - 综合多个 chunks 的信息
   - 包含完整引用

2. **对比响应**（Comparison Response）：
   - 传感器方案对比
   - 算法方案对比
   - 结构化展示相似性和差异性

3. **汇总响应**（Aggregation Response）：
   - 多传感器融合方案
   - 测试场景汇总
   - 列出 3-5 个关键点，来自不同来源

**响应模板示例**：

**传感器对比模板**：
```markdown
## 传感器方案对比

针对查询 **"{query}"**，以下是不同传感器的对比：

### 1. 激光雷达 [1][2]
**技术参数:**
- 探测距离: 200m
- 分辨率: 0.1°
- 视场角: 360°

**优点:** 高精度、远距离探测、3D 点云
**缺点:** 成本高、受天气影响（雨雾）

### 2. 毫米波雷达 [3][4]
**技术参数:**
- 探测距离: 150m
- 分辨率: 1°
- 视场角: 120°

**优点:** 全天候、成本低、穿透能力强
**缺点:** 分辨率低、无法识别物体类型

**对比总结:**
激光雷达适合高精度场景，毫米波雷达适合全天候应用。实际应用中通常采用多传感器融合方案。
```

**代码位置**：`src/core/response/response_builder.py`

### 3.8 Boundary Validator（边界验证器）

**职责**：检测并处理超出系统能力的查询，确保系统可信度。

**边界类型**：

1. **预测性查询**（Predictive Query）：
   - 检测模式：["预测", "预计", "下一代", "未来趋势"]
   - 拒绝原因：系统只提供基于现有文档的事实性信息
   - 建议：改为查询当前技术的原理和实现方法

2. **实时诊断查询**（Diagnostic Query）：
   - 检测模式：["判断当前故障", "分析实时数据", "诊断问题"]
   - 拒绝原因：系统不提供实时故障诊断
   - 建议：改为查询故障排查流程和方法

3. **低相关性查询**（Low Relevance Query）：
   - 检测条件：top chunk 相关性评分 < 0.3
   - 响应：承认限制，建议使用更具体的关键词

**拒绝消息示例**：
```
查询 **"预测下一代激光雷达的发展趋势"** 涉及预测性分析请求。

自动驾驶知识检索系统当前只提供基于现有文档的事实性信息检索，
不提供预测、趋势分析或未来技术判断。

**建议改为查询：**
- 当前激光雷达的技术原理和实现方法
- 已有的激光雷达技术方案和案例
- 相关的标准和测试规范
```

**代码位置**：`src/core/response/response_builder.py`

### 3.9 Scope Provider（范围提供器）

**职责**：提供知识库范围信息，帮助用户了解系统能力和限制。

**提供信息**：
- 知识库名称（ad_knowledge_v01）
- 文档类型和数量
- 覆盖领域
- 最后更新时间

**范围响应示例**：
```markdown
## 知识库范围

当前知识库 **ad_knowledge_v01** 包含以下内容：

**文档类型:**
- 传感器文档 (5 份): 摄像头、激光雷达、毫米波雷达、超声波雷达的规格书和标定文档
- 算法文档 (8 份): 感知算法、规划算法、控制算法的设计文档和技术报告
- 法规文档 (3 份): GB/T 国家标准、ISO 26262 功能安全标准、测试规范
- 测试文档 (10 份): 测试场景库、测试用例、测试报告

**覆盖领域:**
- 传感器技术: 摄像头、激光雷达、毫米波雷达、超声波雷达
- 算法模块: 感知、规划、控制
- 法规标准: 国家标准、功能安全、测试规范
- 测试场景: 功能测试、安全测试、边界场景

**最后更新:** 2024-01-15
**总文档数:** 26 份
**总 Chunk 数:** 120+
```

**代码位置**：`src/core/query_engine/scope_provider.py`



## 4. Metadata Booster 工作原理详解

### 4.1 问题背景

在医疗知识助手系统中，当用户查询特定设备（如"组织脱水机"）时，系统可能返回大量通用流程文档，而设备手册排名较低。这是因为：

1. **语义相似度偏差**：通用文档包含更多上下文，语义相似度可能更高
2. **关键词稀释**：设备名称在手册中出现频率高，但在 BM25 中可能被稀释
3. **缺乏类型感知**：检索系统不知道用户期望的文档类型

### 4.2 解决方案：Metadata Boost

Metadata Booster 通过以下步骤解决这个问题：

#### 步骤 1：查询类型检测

```python
def detect_query_type(query: str) -> str:
    """
    检测查询类型，确定用户期望的文档类型。
    """
    # 传感器查询特征
    sensor_keywords = [
        "摄像头", "激光雷达", "LiDAR", "Camera", "Radar", "毫米波雷达",
        "超声波雷达", "Ultrasonic", "传感器", "Sensor",
        "分辨率", "帧率", "视场角", "探测距离", "标定"
    ]
    
    # 算法查询特征
    algorithm_keywords = [
        "感知", "Perception", "规划", "Planning", "控制", "Control",
        "目标检测", "车道线检测", "路径规划", "轨迹规划",
        "PID", "MPC", "SLAM", "算法"
    ]
    
    # 法规查询特征
    regulation_keywords = [
        "GB/T", "ISO 26262", "国家标准", "功能安全", "ASIL",
        "测试规范", "测试标准", "法规", "标准"
    ]
    
    # 检测逻辑
    if any(kw in query for kw in sensor_keywords):
        return "sensor_query"
    elif any(kw in query for kw in algorithm_keywords):
        return "algorithm_query"
    elif any(kw in query for kw in regulation_keywords):
        return "regulation_query"
    else:
        return "general"
```

#### 步骤 2：权重配置加载

```python
BOOST_CONFIG = {
    "sensor_query": {
        "sensor_doc": 1.5,      # 传感器文档权重 +50%
        "algorithm_doc": 0.8,   # 算法文档权重 -20%
        "regulation_doc": 1.0,  # 法规文档保持不变
        "test_doc": 0.9,        # 测试文档权重 -10%
    },
    "algorithm_query": {
        "algorithm_doc": 1.3,   # 算法文档权重 +30%
        "sensor_doc": 0.9,
        "regulation_doc": 1.1,
        "test_doc": 0.9,
    },
    "regulation_query": {
        "regulation_doc": 1.6,  # 法规文档权重 +60%
        "algorithm_doc": 1.0,
        "sensor_doc": 0.8,
        "test_doc": 1.2,        # 测试文档权重 +20%
    },
}
```

#### 步骤 3：应用权重提升

```python
def apply_boost(
    chunks: List[RetrievalResult],
    query_type: str,
    boost_config: Dict[str, Dict[str, float]]
) -> List[RetrievalResult]:
    """
    根据查询类型应用 metadata boost。
    """
    if query_type == "general":
        return chunks  # 通用查询不应用 boost
    
    boost_weights = boost_config.get(query_type, {})
    
    for chunk in chunks:
        doc_type = chunk.metadata.get("document_type")
        boost_factor = boost_weights.get(doc_type, 1.0)
        
        # 应用权重
        original_score = chunk.score
        chunk.score *= boost_factor
        
        # 记录 boost 应用情况
        chunk.metadata["boost_applied"] = True
        chunk.metadata["boost_factor"] = boost_factor
        chunk.metadata["original_score"] = original_score
    
    # 重新排序
    chunks.sort(key=lambda x: x.score, reverse=True)
    
    return chunks
```

#### 步骤 4：Top-K 验证

```python
def verify_top_k(
    chunks: List[RetrievalResult],
    target_doc_type: str,
    k: int = 3,
    min_count: int = 2
) -> bool:
    """
    验证 top-k 结果中是否有足够数量的目标文档类型。
    """
    top_k_chunks = chunks[:k]
    target_count = sum(
        1 for c in top_k_chunks 
        if c.metadata.get("document_type") == target_doc_type
    )
    
    return target_count >= min_count
```

#### 步骤 5：回退机制

```python
def apply_boost_with_fallback(
    chunks: List[RetrievalResult],
    query_type: str
) -> MetadataBoostResult:
    """
    应用 boost 并在失败时回退。
    """
    # 保存原始排序
    original_chunks = chunks.copy()
    
    # 应用 boost
    boosted_chunks = apply_boost(chunks, query_type, BOOST_CONFIG)
    
    # 验证 top-K
    target_doc_type = QUERY_TYPE_TO_DOC_TYPE.get(query_type)
    if target_doc_type and not verify_top_k(boosted_chunks, target_doc_type):
        logger.warning(f"Top-K verification failed for {query_type}, falling back to original ranking")
        return MetadataBoostResult(
            original_chunks=original_chunks,
            boosted_chunks=original_chunks,  # 回退到原始排序
            boost_applied=False,
            boost_type=query_type,
            boost_config={}
        )
    
    return MetadataBoostResult(
        original_chunks=original_chunks,
        boosted_chunks=boosted_chunks,
        boost_applied=True,
        boost_type=query_type,
        boost_config=BOOST_CONFIG[query_type]
    )
```

### 4.3 效果示例

**查询**：激光雷达的探测距离是多少？

**应用 Boost 前**：
```
1. [algorithm_doc] 感知算法设计文档 - 相关性: 0.85
2. [algorithm_doc] 多传感器融合方案 - 相关性: 0.82
3. [sensor_doc] 激光雷达规格书 - 相关性: 0.78
4. [sensor_doc] 激光雷达标定文档 - 相关性: 0.75
5. [test_doc] 传感器测试用例 - 相关性: 0.70
```

**应用 Boost 后**：
```
1. [sensor_doc] 激光雷达规格书 - 相关性: 1.17 (0.78 × 1.5)
2. [sensor_doc] 激光雷达标定文档 - 相关性: 1.13 (0.75 × 1.5)
3. [algorithm_doc] 感知算法设计文档 - 相关性: 0.68 (0.85 × 0.8)
4. [algorithm_doc] 多传感器融合方案 - 相关性: 0.66 (0.82 × 0.8)
5. [test_doc] 传感器测试用例 - 相关性: 0.63 (0.70 × 0.9)
```

**结果**：传感器文档成功排到 top-2，满足用户期望。

### 4.4 权重调优建议

1. **初始权重**：
   - 目标文档类型：1.3 - 1.6
   - 相关文档类型：0.9 - 1.1
   - 不相关文档类型：0.7 - 0.9

2. **调优策略**：
   - 监控 top-K 验证成功率
   - 如果成功率 < 80%，增加目标文档权重
   - 如果成功率 > 95%，可以适当降低权重以保持多样性

3. **A/B 测试**：
   - 对比有/无 boost 的检索质量
   - 收集用户反馈
   - 持续优化权重配置



## 5. 多文档推理流程

### 5.1 多文档推理概述

多文档推理是系统的核心能力之一，允许用户进行复杂的对比查询和汇总查询。系统通过文档分组、引用增强和结构化响应生成，实现高质量的多文档综合。

### 5.2 对比查询流程

**用户查询**：激光雷达 vs 毫米波雷达，哪个更适合自动驾驶？

#### 阶段 1：查询分析

```python
QueryAnalysis(
    complexity="comparison",
    intent="retrieval",
    sub_queries=["激光雷达特点", "毫米波雷达特点"],
    requires_multi_doc=True,
    query_type="sensor_query"
)
```

#### 阶段 2：混合检索

- BM25 检索：50 个候选 chunks
- Dense 检索：50 个候选 chunks
- RRF 融合：80 个 chunks

#### 阶段 3：Metadata Boost

```python
# 检测到 sensor_query，应用 boost
boost_config = {
    "sensor_doc": 1.5,
    "algorithm_doc": 0.8,
}

# 应用后，传感器文档优先
```

#### 阶段 4：重排序

Cross-Encoder 精细化评分，选择 top-10 chunks

#### 阶段 5：文档分组

```python
grouped_chunks = {
    "激光雷达规格书.pdf": [chunk1, chunk2, chunk3],
    "毫米波雷达规格书.pdf": [chunk4, chunk5, chunk6],
    "多传感器融合方案.pdf": [chunk7, chunk8],
}
```

#### 阶段 6：多样性验证

```python
# 确保至少 2 个不同传感器文档
assert len(grouped_chunks) >= 2
```

#### 阶段 7：引用增强

```python
citations = [
    EnhancedCitation(
        document_name="激光雷达规格书.pdf",
        document_type="sensor_doc",
        section="技术参数",
        page=5,
        relevance_score=0.92,
        authority_score=0.6,
        excerpt="探测距离: 200m, 分辨率: 0.1°",
        sensor_type="LiDAR"
    ),
    EnhancedCitation(
        document_name="毫米波雷达规格书.pdf",
        document_type="sensor_doc",
        section="性能指标",
        page=3,
        relevance_score=0.89,
        authority_score=0.6,
        excerpt="探测距离: 150m, 分辨率: 1°",
        sensor_type="Radar"
    ),
]
```

#### 阶段 8：结构化响应生成

```markdown
## 传感器方案对比

针对查询 **"激光雷达 vs 毫米波雷达，哪个更适合自动驾驶？"**，以下是详细对比：

### 1. 激光雷达 (LiDAR) [1][2]

**技术参数:**
- 探测距离: 200m
- 分辨率: 0.1°
- 视场角: 360°
- 点云密度: 高

**优点:**
- 高精度 3D 点云数据
- 远距离探测能力
- 可直接用于建图和定位

**缺点:**
- 成本高（$5000-$10000）
- 受天气影响（雨雾降低性能）
- 功耗较大

**适用场景:** 高级别自动驾驶（L4/L5），需要高精度环境感知

### 2. 毫米波雷达 (Radar) [3][4]

**技术参数:**
- 探测距离: 150m
- 分辨率: 1°
- 视场角: 120°
- 速度测量: 精确

**优点:**
- 全天候工作（不受雨雾影响）
- 成本低（$100-$500）
- 功耗小
- 穿透能力强

**缺点:**
- 分辨率低，无法识别物体类型
- 无法提供 3D 点云
- 对静止物体检测能力弱

**适用场景:** 低级别自动驾驶（L2/L3），辅助驾驶系统（ADAS）

### 对比总结

**选型建议:**
- **L4/L5 自动驾驶**: 推荐激光雷达作为主传感器，配合毫米波雷达和摄像头
- **L2/L3 辅助驾驶**: 推荐毫米波雷达 + 摄像头方案，成本可控
- **最佳实践**: 多传感器融合，发挥各自优势，提高系统鲁棒性

**引用来源:**
[1] 激光雷达规格书.pdf - 技术参数 (p.5)
[2] 激光雷达标定文档.pdf - 性能分析 (p.12)
[3] 毫米波雷达规格书.pdf - 性能指标 (p.3)
[4] 多传感器融合方案.pdf - 传感器对比 (p.8)
```

### 5.3 汇总查询流程

**用户查询**：多传感器融合方案有哪些？

#### 阶段 1：查询分析

```python
QueryAnalysis(
    complexity="aggregation",
    intent="retrieval",
    sub_queries=[],
    requires_multi_doc=True,
    query_type="sensor_query"
)
```

#### 阶段 2-4：检索、Boost、重排序

（同对比查询）

#### 阶段 5：文档分组

```python
grouped_chunks = {
    "激光雷达规格书.pdf": [chunk1, chunk2],
    "摄像头规格书.pdf": [chunk3, chunk4],
    "毫米波雷达规格书.pdf": [chunk5, chunk6],
    "多传感器融合方案.pdf": [chunk7, chunk8, chunk9],
    "感知算法设计文档.pdf": [chunk10],
}
```

#### 阶段 6：多样性验证

```python
# 确保 3-5 个不同传感器文档
assert 3 <= len(grouped_chunks) <= 5
```

#### 阶段 7：汇总响应生成

```markdown
## 多传感器融合方案

针对查询 **"多传感器融合方案有哪些？"**，以下是主流融合方案汇总：

### 融合传感器组合

1. **激光雷达 + 摄像头 + 毫米波雷达** [1][2][3]
   - 作用：激光雷达提供 3D 点云，摄像头提供视觉信息，毫米波雷达提供速度测量
   - 优势：互补性强，鲁棒性高
   - 应用：L4/L5 自动驾驶

2. **摄像头 + 毫米波雷达** [4][5]
   - 作用：摄像头识别物体类型，毫米波雷达测量距离和速度
   - 优势：成本可控，全天候
   - 应用：L2/L3 辅助驾驶

3. **激光雷达 + 摄像头** [6]
   - 作用：激光雷达提供深度信息，摄像头提供纹理和颜色
   - 优势：高精度感知
   - 应用：城市自动驾驶

### 融合策略

**数据层融合** [7]
- 在原始数据层面融合传感器数据
- 优点：信息损失最小
- 缺点：计算复杂度高

**特征层融合** [8]
- 提取各传感器特征后融合
- 优点：平衡性能和计算量
- 缺点：需要特征对齐

**决策层融合** [9]
- 各传感器独立决策后融合
- 优点：计算效率高，模块化
- 缺点：信息损失较大

### 性能提升

根据文档 [10]，多传感器融合相比单一传感器可以：
- 提高目标检测准确率 15-25%
- 降低误检率 30-40%
- 提升恶劣天气下的鲁棒性 50%+

**引用来源:**
[1] 激光雷达规格书.pdf (p.15)
[2] 摄像头规格书.pdf (p.8)
[3] 毫米波雷达规格书.pdf (p.12)
[4] 多传感器融合方案.pdf (p.3-5)
[5] 感知算法设计文档.pdf (p.20)
...
```

### 5.4 多文档推理关键技术

1. **文档多样性保证**：
   - 对比查询：至少 2 个不同文档
   - 汇总查询：3-5 个不同文档
   - 避免单一文档主导

2. **引用完整性**：
   - 每个关键点都有引用支持
   - 引用包含文档名称、章节、页码
   - 引用按相关性和权威性排序

3. **结构化展示**：
   - 对比查询：并列展示，清晰对比
   - 汇总查询：分类列举，逻辑清晰
   - 总结建议：综合分析，给出建议

4. **质量控制**：
   - 验证引用内容确实支持答案
   - 检查文档多样性
   - 确保响应连贯性



## 6. 边界控制机制

### 6.1 边界控制概述

边界控制是确保系统可信度的关键机制。系统通过识别超出能力范围的查询，主动拒绝并提供有用的替代建议，避免生成不可靠的答案。

### 6.2 边界类型

#### 6.2.1 预测性查询（Predictive Query）

**定义**：要求系统预测未来技术趋势或发展方向的查询。

**检测模式**：
```python
PREDICTIVE_PATTERNS = [
    "预测", "预计", "预期", "预判", "预估",
    "下一代", "未来趋势", "发展方向", "演进路线",
    "最可能", "会发生", "概率", "前景",
]
```

**示例查询**：
- "预测下一代激光雷达的发展趋势"
- "未来自动驾驶会采用什么传感器方案？"
- "预计 2025 年 L4 自动驾驶的普及率"

**拒绝消息**：
```
查询 **"预测下一代激光雷达的发展趋势"** 涉及预测性分析请求。

自动驾驶知识检索系统当前只提供基于现有文档的事实性信息检索，
不提供预测、趋势分析或未来技术判断。

**建议改为查询：**
- 当前激光雷达的技术原理和实现方法
- 已有的激光雷达技术方案和案例
- 相关的标准和测试规范
- 激光雷达的技术演进历史（基于已有文档）
```

#### 6.2.2 实时诊断查询（Diagnostic Query）

**定义**：要求系统分析实时数据或诊断当前故障的查询。

**检测模式**：
```python
DIAGNOSTIC_PATTERNS = [
    "判断当前故障", "分析实时数据", "诊断问题",
    "是否故障", "什么问题", "如何修复",
    "当前状态", "实时监控", "故障原因",
]
```

**示例查询**：
- "判断当前激光雷达是否故障"
- "分析实时传感器数据异常原因"
- "如何修复摄像头标定偏差？"

**拒绝消息**：
```
查询 **"判断当前激光雷达是否故障"** 涉及实时诊断请求。

自动驾驶知识检索系统当前只提供知识检索和文档引用，
不提供实时故障诊断或问题分析。

**建议改为查询：**
- 激光雷达常见故障类型和特征
- 激光雷达故障排查流程和方法
- 激光雷达测试和验证规范
- 激光雷达维护保养指南
```

#### 6.2.3 低相关性查询（Low Relevance Query）

**定义**：检索结果相关性过低，无法生成可靠答案的查询。

**检测条件**：
```python
LOW_RELEVANCE_THRESHOLD = 0.3

def is_low_relevance(chunks: List[RetrievalResult]) -> bool:
    if not chunks:
        return True
    
    top_chunk_score = chunks[0].score
    return top_chunk_score < LOW_RELEVANCE_THRESHOLD
```

**示例场景**：
- 查询内容不在知识库覆盖范围内
- 查询使用了错误的术语或表述
- 查询过于模糊或宽泛

**响应消息**：
```
查询 **"量子计算在自动驾驶中的应用"** 的检索结果相关度较低（最高相关度: 0.25）。

当前知识库中可能没有直接相关的资料。

**建议：**
- 尝试使用更具体的关键词或术语
- 确认相关资料是否已经完成导入（ingest）
- 如果问题涉及特定传感器或算法，请包含名称
- 尝试将复杂问题拆分为多个简单问题

**当前知识库覆盖范围：**
- 传感器技术（摄像头、激光雷达、毫米波雷达、超声波雷达）
- 算法模块（感知、规划、控制）
- 法规标准（GB/T、ISO 26262、测试规范）
- 测试场景（功能测试、安全测试、边界场景）
```

### 6.3 边界检测流程

```python
def validate_query_and_response(
    query: str,
    analysis: QueryAnalysis,
    chunks: List[RetrievalResult]
) -> BoundaryCheck:
    """
    完整的边界检测流程。
    """
    # 1. 检测预测性查询
    if any(pattern in query for pattern in PREDICTIVE_PATTERNS):
        return BoundaryCheck(
            is_valid=False,
            boundary_type="predictive",
            refusal_message=generate_predictive_refusal(query),
            suggested_alternatives=generate_predictive_alternatives(query),
            confidence=0.9,
            detected_pattern="predictive"
        )
    
    # 2. 检测实时诊断查询
    if any(pattern in query for pattern in DIAGNOSTIC_PATTERNS):
        return BoundaryCheck(
            is_valid=False,
            boundary_type="diagnostic",
            refusal_message=generate_diagnostic_refusal(query),
            suggested_alternatives=generate_diagnostic_alternatives(query),
            confidence=0.85,
            detected_pattern="diagnostic"
        )
    
    # 3. 检测低相关性
    if is_low_relevance(chunks):
        return BoundaryCheck(
            is_valid=False,
            boundary_type="low_relevance",
            refusal_message=generate_low_relevance_message(query, chunks),
            suggested_alternatives=generate_query_refinement_suggestions(query),
            confidence=0.95,
            detected_pattern="low_relevance"
        )
    
    # 4. 通过验证
    return BoundaryCheck(
        is_valid=True,
        boundary_type=None,
        refusal_message=None,
        suggested_alternatives=[],
        confidence=1.0,
        detected_pattern=None
    )
```

### 6.4 边界日志记录

系统记录所有边界拒绝事件，用于分析和优化：

```python
@dataclass
class BoundaryRefusalLog:
    timestamp: datetime
    query: str
    boundary_type: str
    detected_pattern: str
    confidence: float
    user_feedback: Optional[str] = None

# 记录拒绝事件
def log_boundary_refusal(
    query: str,
    boundary_check: BoundaryCheck
):
    log = BoundaryRefusalLog(
        timestamp=datetime.now(),
        query=query,
        boundary_type=boundary_check.boundary_type,
        detected_pattern=boundary_check.detected_pattern,
        confidence=boundary_check.confidence
    )
    
    # 保存到数据库或日志文件
    save_refusal_log(log)
```

### 6.5 边界控制优化

1. **模式更新**：
   - 定期审查拒绝日志
   - 识别新的边界模式
   - 更新检测规则

2. **阈值调优**：
   - 监控拒绝率（目标：< 20%）
   - 如果拒绝率过高，降低检测敏感度
   - 如果假阴性过多，提高检测敏感度

3. **用户反馈**：
   - 收集用户对拒绝消息的反馈
   - 识别误判案例（假阳性）
   - 优化替代建议的质量

4. **A/B 测试**：
   - 测试不同的拒绝消息模板
   - 评估替代建议的有效性
   - 持续改进用户体验

### 6.6 边界控制最佳实践

1. **优先假阳性**：
   - 宁可误拒绝，也不生成不可靠答案
   - 保护系统可信度

2. **提供替代方案**：
   - 不仅拒绝，还要引导
   - 建议用户如何重新表述查询

3. **透明沟通**：
   - 清楚说明拒绝原因
   - 解释系统能力边界

4. **持续学习**：
   - 从拒绝日志中学习
   - 识别知识库缺口
   - 指导知识库扩展方向



## 7. 数据模型

### 7.1 核心数据结构

#### QueryAnalysis

```python
@dataclass
class QueryAnalysis:
    """查询分析结果"""
    complexity: Literal["simple", "multi_part", "comparison", "aggregation"]
    intent: Literal["retrieval", "boundary", "scope_inquiry"]
    sub_queries: List[str]
    requires_multi_doc: bool
    detected_keywords: List[str]
    query_type: Optional[str]  # "sensor_query" | "algorithm_query" | "regulation_query"
```

#### ProcessedQuery

```python
@dataclass
class ProcessedQuery:
    """处理后的查询"""
    original_query: str
    keywords: List[str]
    filters: Dict[str, Any]
    detected_terms: List[str]  # 检测到的专业术语
    term_types: Dict[str, str]  # 术语类型映射
```

#### RetrievalResult

```python
@dataclass
class RetrievalResult:
    """检索结果"""
    chunk_id: str
    content: str
    score: float
    metadata: Dict[str, Any]  # 包含 document_name, document_type, section, page 等
```

#### MetadataBoostResult

```python
@dataclass
class MetadataBoostResult:
    """Metadata Boost 结果"""
    original_chunks: List[RetrievalResult]
    boosted_chunks: List[RetrievalResult]
    boost_applied: bool
    boost_type: Optional[str]  # "sensor_query" | "algorithm_query" | "regulation_query"
    boost_config: Dict[str, float]
```

#### EnhancedCitation

```python
@dataclass
class EnhancedCitation:
    """增强的引用信息"""
    document_name: str
    document_type: Literal["sensor_doc", "algorithm_doc", "regulation_doc", "test_doc"]
    section: Optional[str]
    page: Optional[int]
    relevance_score: float
    authority_score: float
    excerpt: str
    chunk_id: str
    sensor_type: Optional[str]  # 传感器类型（如果是传感器文档）
    algorithm_type: Optional[str]  # 算法类型（如果是算法文档）
```

#### BoundaryCheck

```python
@dataclass
class BoundaryCheck:
    """边界检查结果"""
    is_valid: bool
    boundary_type: Optional[Literal["diagnostic", "predictive", "low_relevance"]]
    refusal_message: Optional[str]
    suggested_alternatives: List[str]
    confidence: float
    detected_pattern: Optional[str]
```

#### Response

```python
@dataclass
class Response:
    """系统响应"""
    query: str
    answer: str
    citations: List[EnhancedCitation]
    response_type: Literal["standard", "comparison", "aggregation", "refusal"]
    metadata: Dict[str, Any]  # 包含响应时间、检索统计等
```

### 7.2 文档元数据结构

#### 传感器文档元数据

```python
{
    "document_name": "激光雷达规格书.pdf",
    "document_type": "sensor_doc",
    "sensor_type": "LiDAR",
    "manufacturer": "Velodyne",
    "model": "VLS-128",
    "section": "技术参数",
    "page": 5,
    "ingestion_date": "2024-01-15",
    "sha256": "abc123...",
}
```

#### 算法文档元数据

```python
{
    "document_name": "感知算法设计文档.pdf",
    "document_type": "algorithm_doc",
    "algorithm_type": "perception",
    "algorithm_name": "目标检测",
    "module": "感知模块",
    "section": "算法原理",
    "page": 12,
    "ingestion_date": "2024-01-15",
    "sha256": "def456...",
}
```

#### 法规文档元数据

```python
{
    "document_name": "GB_T自动驾驶分级标准.pdf",
    "document_type": "regulation_doc",
    "standard_number": "GB/T 40429-2021",
    "standard_name": "汽车驾驶自动化分级",
    "authority": "national",  # national | industry | enterprise
    "section": "分级定义",
    "page": 8,
    "ingestion_date": "2024-01-15",
    "sha256": "ghi789...",
}
```

#### 测试文档元数据

```python
{
    "document_name": "功能测试场景库.pdf",
    "document_type": "test_doc",
    "test_type": "functional",  # functional | safety | boundary
    "test_scenario": "跟车场景",
    "section": "场景定义",
    "page": 15,
    "ingestion_date": "2024-01-15",
    "sha256": "jkl012...",
}
```

## 8. 接口定义

### 8.1 查询接口

```python
def query_knowledge_base(
    query: str,
    collection: str = "ad_knowledge_v01",
    top_k: int = 10,
    enable_boost: bool = True,
    enable_boundary_check: bool = True
) -> Response:
    """
    查询知识库的主接口。
    
    Args:
        query: 用户查询字符串
        collection: 知识库名称
        top_k: 返回的最大结果数量
        enable_boost: 是否启用 Metadata Boost
        enable_boundary_check: 是否启用边界检查
    
    Returns:
        Response 对象，包含答案和引用
    """
    pass
```

### 8.2 摄取接口

```python
def ingest_documents(
    file_paths: List[str],
    collection: str = "ad_knowledge_v01",
    document_type: str = "sensor_doc",
    metadata: Optional[Dict[str, Any]] = None,
    force_reingest: bool = False
) -> IngestionReport:
    """
    摄取文档到知识库。
    
    Args:
        file_paths: 文档文件路径列表
        collection: 目标知识库名称
        document_type: 文档类型（sensor_doc, algorithm_doc, regulation_doc, test_doc）
        metadata: 额外的元数据
        force_reingest: 是否强制重新摄取（忽略 SHA256 检查）
    
    Returns:
        IngestionReport 对象，包含摄取统计信息
    """
    pass
```

### 8.3 评估接口

```python
def run_evaluation(
    test_set_path: str,
    collection: str = "ad_knowledge_v01",
    output_path: Optional[str] = None
) -> EvaluationReport:
    """
    运行评估测试集。
    
    Args:
        test_set_path: 测试集 JSON 文件路径
        collection: 知识库名称
        output_path: 评估报告输出路径
    
    Returns:
        EvaluationReport 对象，包含通过率、引用率等指标
    """
    pass
```

## 9. 性能优化

### 9.1 缓存策略

1. **查询缓存**：
   - 缓存相同查询的结果
   - TTL: 1 小时
   - 缓存命中率目标: > 30%

2. **嵌入缓存**：
   - 缓存查询的嵌入向量
   - 减少重复的嵌入计算
   - 使用 LRU 缓存策略

3. **文档缓存**：
   - 缓存热门文档的 chunks
   - 减少数据库访问
   - 内存限制: 500MB

### 9.2 批处理优化

1. **批量嵌入**：
   - 批量计算多个查询的嵌入
   - 批大小: 32
   - 减少 API 调用次数

2. **批量重排序**：
   - 批量处理 Cross-Encoder 重排序
   - 批大小: 64
   - 提高 GPU 利用率

### 9.3 索引优化

1. **向量索引**：
   - 使用 HNSW 索引加速向量检索
   - 参数: M=16, ef_construction=200
   - 检索速度提升 10x

2. **BM25 索引**：
   - 预构建倒排索引
   - 增量更新策略
   - 检索速度: < 50ms

### 9.4 并行处理

1. **检索并行化**：
   - BM25 和 Dense 检索并行执行
   - 使用 asyncio 或多线程
   - 响应时间减少 30%

2. **文档处理并行化**：
   - 多个文档的 chunk 提取并行
   - 使用进程池
   - 摄取速度提升 3x

## 10. 监控与可观测性

### 10.1 关键指标

1. **性能指标**：
   - 响应时间（p50, p95, p99）
   - 吞吐量（QPS）
   - 缓存命中率

2. **质量指标**：
   - 引用率
   - 相关性评分分布
   - 边界拒绝率

3. **系统指标**：
   - CPU/内存使用率
   - 数据库连接数
   - API 调用次数

### 10.2 日志记录

1. **查询日志**：
   - 记录所有查询和响应
   - 包含查询分析结果
   - 包含检索统计信息

2. **Boost 日志**：
   - 记录 boost 应用情况
   - 记录 top-K 验证结果
   - 用于 boost 效果分析

3. **边界日志**：
   - 记录所有拒绝事件
   - 包含检测模式和置信度
   - 用于边界规则优化

### 10.3 告警规则

1. **性能告警**：
   - 响应时间 p95 > 6 秒
   - 错误率 > 5%
   - CPU 使用率 > 80%

2. **质量告警**：
   - 引用率 < 70%
   - 边界拒绝率 > 30%
   - 低相关性查询比例 > 20%

3. **系统告警**：
   - 数据库连接失败
   - API 调用失败率 > 10%
   - 磁盘空间 < 10%

## 11. 安全与隐私

### 11.1 数据安全

1. **访问控制**：
   - API 密钥认证
   - 基于角色的访问控制（RBAC）
   - 查询日志审计

2. **数据加密**：
   - 传输加密（TLS 1.3）
   - 静态数据加密（AES-256）
   - 密钥管理（KMS）

### 11.2 隐私保护

1. **查询脱敏**：
   - 移除查询中的敏感信息
   - 匿名化用户标识
   - 遵守数据保护法规

2. **数据保留**：
   - 查询日志保留 90 天
   - 评估数据保留 1 年
   - 定期清理过期数据

## 12. 扩展性设计

### 12.1 水平扩展

1. **无状态服务**：
   - 查询服务无状态设计
   - 支持多实例部署
   - 负载均衡

2. **数据库分片**：
   - 按 collection 分片
   - 支持多个 Chroma 实例
   - 分布式查询

### 12.2 垂直扩展

1. **资源配置**：
   - 支持 GPU 加速（嵌入、重排序）
   - 内存优化（缓存大小可配置）
   - CPU 核心数可配置

2. **模型升级**：
   - 支持更大的嵌入模型
   - 支持更强的生成模型
   - 模型热更新

## 13. 总结

自动驾驶知识检索系统通过以下核心技术实现高质量的知识检索：

1. **Metadata Booster**：确保文档类型匹配，传感器查询优先返回传感器文档
2. **多文档推理**：支持复杂的对比查询和汇总查询，提供结构化响应
3. **边界控制**：主动识别并拒绝超出能力的查询，保护系统可信度
4. **术语适配**：支持中英文混合查询和自动驾驶专业术语识别
5. **高质量引用**：提供详细的文档引用，便于追溯和验证

系统架构清晰、模块化设计、易于扩展和维护，为自动驾驶研发团队提供可靠的知识检索服务。
