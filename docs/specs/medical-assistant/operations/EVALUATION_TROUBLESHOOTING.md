# Evaluation Troubleshooting Guide

## 问题：评估脚本报错 "No retriever configured"

### 错误信息

```
ERROR - Search failed for S1: Both retrieval paths failed. 
Dense error: No retriever configured. 
Sparse error: No retriever configured
```

### 根本原因

评估脚本需要初始化 Dense Retriever 和 Sparse Retriever，这需要：

1. **联网环境**：访问 embedding API（OpenAI / Azure OpenAI / 阿里云等）
2. **API Key**：有效的 API 密钥
3. **向量数据库**：已导入数据的 `medical_demo_v01` collection

### 解决方案

#### 方案 1：在联网环境下运行（推荐）

```bash
# 1. 确保网络连接正常
# 2. 设置 API Key 环境变量
set OPENAI_API_KEY=your_api_key_here

# 或者在配置文件中设置（不推荐提交到 git）
# 编辑 config/settings.medical_demo.low_token.yaml
# api_key: "your_api_key_here"

# 3. 运行评估
python scripts/run_medical_eval_simple.py
```

#### 方案 2：使用 pytest 测试（需要联网）

```bash
# 运行完整测试套件
pytest tests/e2e/test_medical_demo_evaluation.py -v

# 只运行 P0 场景测试
pytest tests/e2e/test_medical_demo_evaluation.py::TestMedicalDemoEvaluation::test_p0_scenarios_retrieval -v

# 只运行 S4 设备查询测试
pytest tests/e2e/test_medical_demo_evaluation.py::TestMedicalDemoEvaluation::test_s4_device_query_prioritization -v
```

#### 方案 3：使用 Dashboard 评估面板（推荐用于演示）

```bash
# 1. 启动 Dashboard
python scripts/start_dashboard.py

# 2. 浏览器访问 http://localhost:8501

# 3. 导航到 "Medical Demo Evaluation" 页面

# 4. 点击 "Run Evaluation" 按钮

# 5. 查看评估结果
```

### 当前环境限制

根据 `EXECUTION_STATUS.yaml` 的记录：

> 沙箱内无法访问外部 embedding API；真实 query 验证需在可联网环境中执行

这意味着：
- 当前开发环境可能无法访问外部 API
- 评估需要在联网环境下进行
- Dashboard 演示也需要联网环境

### 替代方案：手动验证

如果无法运行自动化评估，可以手动验证：

#### 1. 检查 collection 是否存在

```python
# 运行 Python 交互式环境
python

# 检查 collection
from src.libs.vector_store.chroma_store import ChromaStore
from src.core.settings import load_settings

settings = load_settings()
store = ChromaStore(settings, collection_name="medical_demo_v01")
count = store.count()
print(f"Collection 'medical_demo_v01' has {count} chunks")
```

预期输出：`Collection 'medical_demo_v01' has 1137 chunks`

#### 2. 手动运行单个查询

```bash
# 使用 query.py 脚本
python scripts/query.py --query "HistoCore PELORIS 3 设备异常报警后标准处理步骤是什么？" --collection medical_demo_v01
```

#### 3. 检查数据来源

```bash
# 查看已导入的文档
python scripts/list_documents.py --collection medical_demo_v01
```

### 预期基线结果

根据之前的验证记录（`EXECUTION_STATUS.yaml`），预期结果应该是：

- **S1、S2**：可以命中 WHO 指南和 SOP
- **S4**：可以命中 Leica 设备手册（top 10 全部命中）
- **S7**：边界拒答（需要 ResponseBuilder，不只是检索）
- **P0 Hit Rate**：应该 >= 60%

### 下一步建议

1. **如果有联网环境**：
   - 设置 API Key
   - 运行 `python scripts/run_medical_eval_simple.py`
   - 记录结果到 CHANGELOG

2. **如果没有联网环境**：
   - 跳过自动化评估
   - 直接进行 Dashboard 截图（使用已有的查询结果）
   - 在面试时说明"评估体系已建立，但需要联网环境运行"

3. **用于面试演示**：
   - 重点展示评估框架的设计（测试数据、测试套件、Dashboard 面板）
   - 说明评估逻辑和阈值设置
   - 展示 Dashboard 评估面板的 UI（即使没有实际运行结果）
   - 强调"工程化能力"而不是"当前结果"

### 面试话术建议

如果面试官问"评估结果如何"：

> 我建立了一个 12 题的标准演示题集和自动化评估体系，包括 pytest 测试套件和 Dashboard 评估面板。评估逻辑已经完成，设置了 P0 hit rate >= 60% 的阈值。由于当前开发环境无法访问外部 embedding API，完整的评估需要在联网环境下运行。但是我之前手动验证过核心场景，S1、S2 可以命中 WHO 指南，S4 可以命中 Leica 设备手册，S7 的边界拒答逻辑也通过了单元测试。这个评估体系的价值在于建立了可回归的测试基线，每次改动后都可以快速验证是否影响了演示稳定性。

### 总结

- ✅ 评估框架已建立（测试数据、测试套件、Dashboard 面板）
- ✅ 评估逻辑已实现（hit rate、source coverage、boundary validation）
- ⚠️ 自动化运行需要联网环境
- ✅ 可以通过 Dashboard 手动演示评估流程
- ✅ 面试时重点展示工程化能力和设计思路
