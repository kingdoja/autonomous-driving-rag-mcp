# Quick Reference - 快速参考

## 🚀 立即开始

### 我现在要做什么？

**拍摄 Dashboard 截图（30 分钟）**

```bash
# 1. 启动 Dashboard
python scripts/start_dashboard.py

# 2. 打开浏览器
http://localhost:8501

# 3. 拍摄 4 张截图（Win + Shift + S）
#    - Medical Demo 首页
#    - Knowledge Base 浏览
#    - Medical Demo Evaluation 面板
#    - Query Diagnostics 查询链路

# 4. 保存到
docs/specs/medical-assistant/screenshots/
```

**练习 1 分钟讲稿（30 分钟）**

打开文件：`interview/INTERVIEW_TALK_TRACK_1MIN.md`

---

## 📚 文档快速查找

| 我想... | 查看文档 |
|---------|----------|
| 了解产品定位 | `core/PRODUCT_BRIEF.md` |
| 准备面试 | `interview/INTERVIEW_TALK_TRACK_1MIN.md` |
| 运行演示 | `operations/STARTUP_RUNBOOK.md` |
| 拍摄截图 | `demo/DEMO_MATERIALS.md` |
| 查看进度 | `tracking/EXECUTION_STATUS.yaml` |
| 解决问题 | `operations/EVALUATION_TROUBLESHOOTING.md` |
| 了解下一步 | `interview/NEXT_STEPS_GUIDE.md` |

---

## 🎤 1 分钟讲稿（背诵版）

### 定位（10 秒）
> 这是一个面向病理科和检验科的医疗知识与质控助手，不是通用聊天机器人，也不做自动诊断，而是提供知识检索、规范引用和流程辅助。

### 能力（30 秒）
> 系统支持指南、SOP、设备手册和培训资料的统一检索。我实现了 BM25 + Dense Retrieval + RRF 混合召回，并针对医疗场景做了设备名 metadata boost 优化。每次回答都带引用来源，确保可追溯。对于诊断类请求，系统会明确拒答并引导回安全范围。

### 演示（15 秒）
> 当前 demo 基于 6 份公开资料，包括 WHO 指南、Leica 设备手册等。我建立了 12 题标准演示题集和自动化评估体系，P0 场景 hit rate 达到 60% 以上，可以稳定演示。

### 价值（5 秒）
> 这个项目体现了我的医疗背景和 RAG 工程化能力的结合，也展示了我对可信 AI 和边界控制的理解。

---

## 🔧 常见问题

### Q: Dashboard 报错 "No retriever configured"？
**A**: 这是正常的，需要联网环境。不要点击 "Run Evaluation" 按钮，直接拍摄界面截图即可。

详见：`operations/EVALUATION_TROUBLESHOOTING.md`

### Q: 评估脚本运行失败？
**A**: 评估需要联网环境访问 embedding API。如果没有网络，跳过评估，重点展示评估框架的设计。

详见：`operations/EVALUATION_TROUBLESHOOTING.md`

### Q: 如何准备面试？
**A**: 
1. 练习 1 分钟讲稿（`interview/INTERVIEW_TALK_TRACK_1MIN.md`）
2. 拍摄 4 张 Dashboard 截图（`demo/DEMO_MATERIALS.md`）
3. 准备 6 个常见追问的回答

详见：`interview/NEXT_STEPS_GUIDE.md`

---

## 📊 项目当前状态

- **版本**: v0.1
- **阶段**: 求职包装层收尾阶段
- **完成度**: 评估与回归层 ✅、展示材料准备 ✅
- **下一步**: 拍摄截图、练习讲稿

详见：`tracking/EXECUTION_STATUS.yaml`

---

## 🎯 核心数据

- **数据来源**: 6 份公开资料（WHO 指南、Leica 手册、Roche 手册等）
- **数据规模**: 1137 chunks
- **Collection**: medical_demo_v01
- **标准题集**: 12 题（8 题 P0）
- **演示链路**: S1 → S2 → S4 → S7 → S12
- **评估阈值**: P0 hit rate >= 60%

---

## 📞 需要帮助？

1. **产品问题** → `core/PRODUCT_BRIEF.md`
2. **技术问题** → `operations/EVALUATION_TROUBLESHOOTING.md`
3. **面试问题** → `interview/INTERVIEW_TALK_TRACK_1MIN.md`
4. **操作问题** → `interview/NEXT_STEPS_GUIDE.md`
