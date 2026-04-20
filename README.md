# 🔍 Modular RAG MCP Server

> 可插拔、可观测的模块化 RAG 知识检索系统，基于 MCP 协议提供工具服务，支持多领域知识库构建。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/Tests-89%20passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 项目简介

本项目是一个通用的 RAG（检索增强生成）知识检索系统框架，采用模块化架构设计，支持快速适配到不同的垂直领域。

**当前已实现两个完整场景**：
- 🚗 **自动驾驶研发知识检索** - 接入算法文档、测试规范、传感器手册、法规标准
- 🏥 **医疗知识与质控助手** - 接入临床指南、SOP、设备手册、培训材料

通过 MCP（Model Context Protocol）协议暴露为工具服务，可被 AI Agent、研发工具或 IDE 直接调用。

## 核心特性

### 🎯 全链路可插拔架构

每个核心组件都定义了抽象接口，支持"乐高积木式"替换：

```yaml
llm:
  provider: openai   # 可换 azure / ollama / deepseek
embedding:
  provider: openai   # 可换 azure / local
reranker:
  provider: cross_encoder  # 可换 llm_reranker
vector_store:
  provider: chroma   # 可换 qdrant / weaviate
```

### 🔎 混合检索引擎

BM25 稀疏检索与 Dense Embedding 稠密检索双路并行，通过 RRF（倒数排名融合）算法合并结果：

- **BM25** - 擅长精确关键词匹配（如标准编号 "ISO 26262-3"）
- **Dense Embedding** - 擅长语义理解（如 "感知模块如何处理遮挡"）
- **Cross-Encoder Reranker** - 精排提升准确率

### 🎨 多模态支持

采用 Image-to-Text 策略，利用 Vision LLM 自动生成图片描述并缝合进文本块，实现"搜文字出图"能力。

### 🔧 MCP 协议服务化

将知识检索能力封装为 MCP 工具，外部 AI Agent 或研发工具可直接调用：

```python
# 外部 Agent 调用示例
result = mcp_client.call("query_knowledge_hub", {
    "query": "激光雷达的外参标定步骤",
    "collection": "ad_knowledge_v01"
})
# 返回：带引用的结构化回答
```

### 📊 可观测性

- **Streamlit Dashboard** - 六页面管理平台（系统总览/数据浏览/摄取管理/查询追踪/评估面板）
- **全链路追踪** - Ingestion 与 Query 两条链路的每个中间状态透明可见
- **评估体系** - 集成 Ragas + 自定义指标，支持 golden test set 回归测试

### 🧪 三层测试体系

- **Unit Tests** - 独立模块逻辑测试
- **Integration Tests** - 模块间交互测试
- **E2E Tests** - 完整链路测试（MCP Client / Dashboard）

## 系统架构

```
用户查询
    │
    ▼
┌─────────────────┐
│  Query Analyzer  │  复杂度检测 / 意图分类 / 领域术语识别
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────────┐
│  BM25  │ │ Dense Embed  │  双路并行检索
└────────┘ └──────────────┘
    │              │
    └──────┬───────┘
           ▼
    ┌─────────────┐
    │  RRF Fusion │  倒数排名融合，平衡精确率与召回率
    └──────┬──────┘
           ▼
    ┌──────────────────┐
    │ Metadata Booster │  查询类型感知权重提升
    └──────┬───────────┘
           ▼
    ┌──────────────┐
    │   Reranker   │  Cross-Encoder 精排
    └──────┬───────┘
           ▼
    ┌──────────────────┐
    │ Response Builder │  多文档综合 / 对比分析
    └──────┬───────────┘
           ▼
    ┌──────────────────┐
    │ Boundary Validator│  拒绝预测性查询 / 超范围请求
    └──────┬───────────┘
           ▼
    引用式回答 + MCP 工具服务 + Streamlit Dashboard
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 OPENAI_API_KEY
```

### 3. 摄取文档（以自动驾驶场景为例）

```bash
python scripts/ingest.py \
  --collection ad_knowledge_v01 \
  --source demo-data-ad/ \
  --config config/settings.ad_knowledge.yaml
```

### 4. 查询

```bash
python scripts/query.py \
  --collection ad_knowledge_v01 \
  --query "激光雷达的外参标定步骤是什么？"
```

### 5. 启动 Dashboard

```bash
python scripts/start_dashboard.py
# 访问 http://localhost:8501
```

## 使用场景示例

### 🚗 自动驾驶场景

**传感器参数查询**
```
Q: 激光雷达 Hesai AT128 的水平视场角和角分辨率是多少？

A: Hesai AT128 激光雷达的水平视场角为 360°，垂直视场角为 ±25°，
   水平角分辨率为 0.1°。[1]

[1] lidar_spec_hesai_at128.txt · 相关性 0.94
```

**传感器方案对比**
```
Q: 激光雷达和毫米波雷达在自动驾驶中各有什么优缺点？

A: ## 传感器方案对比

   ### 激光雷达 [1][2]
   - 探测距离：200m，角分辨率 0.1°
   - 优点：高精度三维点云，目标识别准确
   - 缺点：成本高，受雨雪天气影响

   ### 毫米波雷达 [3]
   - 探测距离：150m，全天候工作
   - 优点：成本低，穿透雨雾能力强
   - 缺点：分辨率低，无法识别目标形状
```

### 🏥 医疗场景

**设备操作查询**
```
Q: 组织脱水机的日常维护步骤是什么？

A: 组织脱水机的日常维护包括：
   1. 每日检查试剂液位，确保充足
   2. 清洁试剂槽和废液槽
   3. 检查加热模块温度是否正常
   4. 记录运行日志 [1]

[1] manual_histocore_peloris3_user_manual_zh-cn.pdf · 第 45 页
```

## 测试

```bash
# 单元测试
pytest tests/unit/ -v

# 集成测试
pytest tests/integration/

# 端到端测试
pytest tests/e2e/

# 运行所有测试
pytest tests/ -v
```

## 项目结构

```
src/
├── core/
│   ├── query_engine/
│   │   ├── query_analyzer.py      # 查询分析 + 领域术语识别
│   │   ├── hybrid_search.py       # BM25 + Dense 混合检索
│   │   ├── fusion.py              # RRF 融合 + 文档分组
│   │   ├── metadata_booster.py    # 查询类型感知权重提升
│   │   └── scope_provider.py      # 知识库范围感知
│   └── response/
│       ├── response_builder.py    # 多文档综合 + 对比响应
│       └── citation_enhancer.py   # 引用元数据增强
├── ingestion/                     # 五阶段摄取流水线
├── libs/                          # 可插拔组件（LLM/Embedding/Reranker）
├── mcp_server/                    # MCP 协议服务
└── observability/                 # Dashboard + 评估 + Trace
```

## 技术栈

| 层次 | 技术 |
|------|------|
| 编排框架 | LangChain |
| 向量数据库 | Chroma |
| 稀疏检索 | BM25 (rank-bm25) |
| 重排序 | Cross-Encoder (sentence-transformers) |
| LLM | OpenAI GPT-4o-mini / Azure / Ollama |
| Embedding | OpenAI text-embedding-3-small |
| 服务协议 | MCP (Model Context Protocol) |
| 可视化 | Streamlit |
| 评估 | Ragas + 自定义指标 |

## 核心技术亮点

### 1. 混合检索引擎

BM25 稀疏检索与 Dense Embedding 稠密检索双路并行，通过 RRF（倒数排名融合）算法合并结果。BM25 擅长精确关键词匹配（如标准编号 "ISO 26262-3"），Dense 擅长语义理解（如 "感知模块如何处理遮挡"），两者互补。

### 2. Metadata Boost — 查询类型感知的权重提升

检测查询意图后，对目标文档类型动态加权：

```python
BOOST_CONFIG = {
    "sensor_query":     {"sensor_doc": 1.5, "algorithm_doc": 0.8},
    "regulation_query": {"regulation_doc": 1.6, "test_doc": 1.2},
    "algorithm_query":  {"algorithm_doc": 1.3},
}
```

确保传感器查询的 top-3 结果中至少 2 个来自传感器文档，避免通用文档稀释结果。

### 3. 五阶段 Ingestion Pipeline

```
Load → Split → Transform → Embed → Upsert
```

基于 SHA256 哈希增量去重，支持 PDF、图片（自动生成描述）、纯文本多格式，处理完成生成摄取报告。

## 扩展指南

本项目设计为通用框架，可快速适配到新的垂直领域：

1. **准备领域文档** - 放入 `demo-data-{domain}/` 目录
2. **配置领域参数** - 复制并修改 `config/settings.yaml`
3. **定义术语词典** - 在 `query_analyzer.py` 中添加领域术语
4. **配置 Metadata Boost** - 根据文档类型调整权重
5. **摄取并测试** - 运行 ingestion 和 query 脚本

详细文档请参考 [README_FULL.md](README_FULL.md)

## 贡献指南

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## License

MIT

---

**更多技术细节和架构说明，请参阅 [README_FULL.md](README_FULL.md)**
