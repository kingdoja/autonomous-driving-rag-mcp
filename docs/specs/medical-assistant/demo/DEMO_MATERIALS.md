# Demo Materials

## 目标

为 `PathoMind 医疗知识与质控助手` 准备完整的展示材料，支持面试演示、GitHub 展示和简历附件。

## 材料清单

### 1. Dashboard 截图

#### 必需截图

1. **Medical Demo 首页**
   - 路径：Dashboard → Medical Demo (🩺)
   - 展示内容：产品定位、核心场景、快速入口
   - 用途：说明产品定位和能力范围
   - 文件名：`screenshot_01_medical_demo_overview.png`

2. **Knowledge Base 浏览**
   - 路径：Dashboard → Knowledge Base (🔍)
   - 展示内容：已导入的 6 份公开资料、文档列表、chunk 统计
   - 用途：说明数据来源和知识库规模
   - 文件名：`screenshot_02_knowledge_base.png`

3. **Medical Demo Evaluation 面板**
   - 路径：Dashboard → Medical Demo Evaluation (🏥)
   - 展示内容：Demo Overview、评估结果、Hit Rate、场景通过情况
   - 用途：说明评估体系和演示就绪度
   - 文件名：`screenshot_03_medical_evaluation.png`

4. **Query Diagnostics 查询链路**
   - 路径：Dashboard → Query Diagnostics (🔎)
   - 展示内容：S4 设备查询的检索链路、top-k 结果、引用来源
   - 用途：说明混合检索和引用追溯能力
   - 文件名：`screenshot_04_query_diagnostics.png`

#### 可选截图

5. **Ingestion Center 导入中心**
   - 路径：Dashboard → Ingestion Center (📥)
   - 展示内容：文档导入界面、配置选项
   - 用途：说明数据摄取能力
   - 文件名：`screenshot_05_ingestion_center.png`

6. **Evaluation Panel 通用评估**
   - 路径：Dashboard → General Evaluation (📏)
   - 展示内容：通用评估配置、历史记录
   - 用途：说明评估框架的通用性
   - 文件名：`screenshot_06_general_evaluation.png`

### 2. 演示 GIF（可选）

#### 推荐 GIF 场景

1. **3 分钟演示流程**
   - 内容：S1 → S2 → S4 → S7 → S12 完整演示链路
   - 时长：30-60 秒（加速播放）
   - 用途：GitHub README 快速展示
   - 文件名：`demo_flow_3min.gif`

2. **Medical Evaluation 运行**
   - 内容：点击 Run Evaluation → 显示结果 → 查看场景详情
   - 时长：15-20 秒
   - 用途：说明评估自动化能力
   - 文件名：`demo_evaluation_run.gif`

### 3. 1 分钟讲稿

#### 面试场景 1 分钟讲稿

**定位（10 秒）**

> 这是一个面向病理科和检验科的医疗知识与质控助手，不是通用聊天机器人，也不做自动诊断，而是提供知识检索、规范引用和流程辅助。

**能力（30 秒）**

> 系统支持指南、SOP、设备手册和培训资料的统一检索。我实现了 BM25 + Dense Retrieval + RRF 混合召回，并针对医疗场景做了设备名 metadata boost 优化。每次回答都带引用来源，确保可追溯。对于诊断类请求，系统会明确拒答并引导回安全范围。

**演示（15 秒）**

> 当前 demo 基于 6 份公开资料，包括 WHO 指南、Leica 设备手册等。我建立了 12 题标准演示题集和自动化评估体系，P0 场景 hit rate 达到 60% 以上，可以稳定演示。

**价值（5 秒）**

> 这个项目体现了我的医疗背景和 RAG 工程化能力的结合，也展示了我对可信 AI 和边界控制的理解。

---

**总时长：60 秒**

### 4. 技术亮点卡片

#### 用于简历或 GitHub README

**技术栈**

- 混合检索：BM25 + Dense Retrieval + RRF Fusion + Reranking
- 向量数据库：ChromaDB
- Embedding：OpenAI text-embedding-3-small
- LLM：Azure OpenAI GPT-4o
- 可观测性：Streamlit Dashboard + JSONL Trace + 自动化评估

**核心能力**

1. 多源文档摄取（PDF、图文混合）
2. 医疗术语混合检索（关键词 + 语义）
3. 引用式回答（可追溯来源）
4. 边界拒答（诊断类请求明确拒绝）
5. 自动化评估（12 题标准题集 + 回归测试）

**工程亮点**

- 设备名 metadata boost 优化检索精度
- 低 token 配置支持快速 ingest（关闭 refine/enrich LLM）
- 专用医疗评估面板（Demo Readiness Indicator）
- 3 分钟固定演示链路（S1 → S2 → S4 → S7 → S12）

### 5. 简历项目描述模板

#### 简历一句话

> 将通用 RAG 底座垂直改造为病理/检验科医疗知识与质控助手，实现混合检索、引用追溯和边界拒答，支持 MCP 协议接入外部 Agent。

#### 简历详细描述（3-4 条）

- 设计图文资料摄取链路，完成文档解析、语义切分、元数据增强与增量入库，支持 WHO 指南、设备说明书和培训资料的统一检索
- 实现 BM25 + Dense Retrieval + RRF 混合召回与重排，针对医疗场景优化设备名 metadata boost，提升术语和规范编号检索准确性
- 建立 12 题标准演示题集和自动化评估体系，实现 P0 场景 hit rate 60%+ 的稳定演示基线，并通过 Dashboard 可视化评估结果
- 实现诊断类请求的边界拒答逻辑，确保系统明确知识检索范围，不输出高风险医疗决策建议

## 截图拍摄指南

### 准备工作

1. 确保 `medical_demo_v01` collection 已导入 6 份资料（1137 chunks）
2. 启动 Dashboard：`python scripts/start_dashboard.py`
3. 运行一次医疗评估：Dashboard → Medical Demo Evaluation → Run Evaluation (P0 Only)
4. 运行一次 S4 查询：使用 `scripts/query.py` 或 Dashboard Query Diagnostics

### 截图要求

- 分辨率：至少 1920x1080
- 格式：PNG（保留清晰度）
- 内容：避免包含敏感信息（API key、本地路径等）
- 标注：可选添加箭头或高亮说明关键区域

### 截图存放位置

- 真源位置：`docs/specs/medical-assistant/screenshots/`
- 展示位置：`简历/项目改造方案-医疗知识助手/screenshots/`

### 截图命名规范

```
screenshot_[序号]_[页面名称].png
```

例如：
- `screenshot_01_medical_demo_overview.png`
- `screenshot_02_knowledge_base.png`
- `screenshot_03_medical_evaluation.png`

## GIF 录制指南（可选）

### 工具推荐

- Windows：ScreenToGif（免费、轻量）
- macOS：Kap（免费、开源）
- 跨平台：OBS Studio（功能强大）

### 录制要求

- 帧率：10-15 fps（GIF 文件大小可控）
- 分辨率：1280x720（适合 GitHub 展示）
- 时长：15-60 秒
- 文件大小：< 10 MB（GitHub 友好）

### 录制流程

1. 准备好演示环境（Dashboard 已启动、数据已导入）
2. 打开录制工具，选择录制区域
3. 执行演示操作（避免停顿和失误）
4. 停止录制，导出为 GIF
5. 可选：使用 ezgif.com 压缩 GIF 文件

## 使用场景

### 面试演示

- 使用 1 分钟讲稿快速介绍
- 展示 Dashboard Medical Demo Evaluation 页面
- 现场运行 S4 设备查询演示
- 展示评估结果和 Demo Readiness Indicator

### GitHub README

- 在 README 顶部添加 1-2 张核心截图
- 可选添加 3 分钟演示流程 GIF
- 在 Features 部分引用技术亮点卡片
- 在 Demo 部分链接到 3 分钟讲稿

### 简历附件

- 使用简历项目描述模板
- 附上 Medical Demo Overview 和 Evaluation 截图
- 可选附上技术架构图（如果有）

## 更新协议

- 每次重要功能更新后，更新对应截图
- 每次评估基线变化后，更新评估结果截图
- 保持展示材料与真源 spec 口径一致

## 注意事项

- 所有截图和 GIF 不得包含真实患者数据
- 所有展示材料必须符合 `PRODUCT_BRIEF.md` 的产品边界
- 不得在展示材料中宣称自动诊断或高风险医疗决策能力
- 展示材料应强调"知识检索"、"规范引用"、"培训辅助"定位
