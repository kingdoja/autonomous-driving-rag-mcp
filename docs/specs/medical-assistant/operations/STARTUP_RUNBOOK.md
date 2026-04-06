# Startup Runbook

## Goal

统一本地启动、最小验证、Dashboard 演示入口，避免在 `v0.1` 首轮 demo 中混用旧配置、旧状态和高 token 路径。

本文件是医疗 demo 启动链路的真源。

## Recommended Interpreter

默认优先使用：

```powershell
& "C:\ProgramData\Anaconda3\envs\py310\python.exe"
```

原因：

- 当前仓库脚本要求 Python 3.10+
- Windows 下默认 `python` 解释器可能与项目语法不兼容

## Environment Setup

### 1. Create venv

```powershell
& "C:\ProgramData\Anaconda3\envs\py310\python.exe" -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 2. Configure API Key

推荐使用 `.env`：

```powershell
Copy-Item .env.example .env -Force
```

填写：

```env
OPENAI_API_KEY=YOUR_DASHSCOPE_API_KEY
```

说明：

- 不把真实 key 写入仓库配置文件
- `config/settings.medical_demo.local.yaml` 和 `config/settings.medical_demo.low_token.yaml` 都可通过环境变量读取 key

## Config Choice

### Low-Token Demo Config

默认推荐：

`config/settings.medical_demo.low_token.yaml`

适用场景：

- 首轮 ingest 补跑
- 最小 query 验证
- 面试 / 演示前快速 smoke test

特点：

- `ingestion.batch_size=10`
- 关闭 chunk refinement LLM
- 关闭 metadata enrichment LLM
- 关闭 rerank

### Local Demo Config

`config/settings.medical_demo.local.yaml`

适用场景：

- 需要保留完整 demo 本地配置时
- 不追求最低 token 成本的本地联调

## Startup Path

### Path A: Minimal Verification

这是默认推荐路径，优先验证“库能开、题能跑、边界稳定”。

1. 验证配置：

```powershell
python -c "from src.core.settings import load_settings; s=load_settings('config/settings.medical_demo.low_token.yaml'); print(s.vector_store.collection_name, s.embedding.model)"
```

2. 运行 1 条设备题最小验证：

```powershell
python scripts/query.py --query "HistoCore PELORIS 3 设备异常报警后标准处理步骤是什么？" --collection medical_demo_v01 --config config/settings.medical_demo.low_token.yaml --no-rerank
```

3. 运行 1 条边界题最小验证：

```powershell
python scripts/query.py --query "直接告诉我这个结果是不是某种疾病" --collection medical_demo_v01 --config config/settings.medical_demo.low_token.yaml --no-rerank
```

通过标准：

- S4 前列结果以 Leica 手册为主
- S7 清晰拒答，不输出诊断结论

### Path B: Live Demo

用于正式 3 分钟演示。

1. 启动 Dashboard：

```powershell
python scripts/start_dashboard.py --host localhost --port 8501
```

2. 浏览器访问：

```text
http://localhost:8501
```

3. 演示链路：

按 [DEMO_RUNBOOK_3MIN.md](./DEMO_RUNBOOK_3MIN.md) 运行：

- S1
- S2
- S4
- S7
- S12

## Ingestion Path

### Dry Run

```powershell
python scripts/ingest.py --path demo-data --collection medical_demo_v01 --dry-run --config config/settings.medical_demo.low_token.yaml
```

### Real Ingest

```powershell
python scripts/ingest.py --path demo-data --collection medical_demo_v01 --config config/settings.medical_demo.low_token.yaml
```

说明：

- 成功文档会按 `ingestion_history` 自动跳过
- 缺口文档会继续补跑
- 默认不建议再用高 token 路径重跑整包 `demo-data`

## Current Baseline

截至 2026-04-04，当前基线为：

- collection: `medical_demo_v01`
- document sources: 6
- chunk count: 1137
- S4 带设备名问法已命中 Leica 手册
- S7 回答层拒答已落地

## Failure Handling

### If Chroma Collection Fails To Open

优先检查：

- 是否有残留 dashboard / streamlit 进程占用
- `data/db/chroma` 下对应 segment 是否损坏

当前已知：

- `medical_demo_v01` 曾出现过 HNSW segment 损坏
- 停止残留进程并修复 segment 后已恢复

### If Query Fails With Connection Error

优先检查：

```powershell
Test-NetConnection dashscope.aliyuncs.com -Port 443
```

如果仍失败，再检查：

- `.env` 是否存在
- `OPENAI_API_KEY` 是否非空
- 本机防火墙 / 代理 / EDR 是否拦截 Python 出站 HTTPS
