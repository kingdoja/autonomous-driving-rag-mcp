# Medical Assistant Specs

本目录是 `PathoMind 医疗知识与质控助手` 的**工程真源**。

## 真源原则

- 与该项目相关的产品定义、开发规范、演示规则、agent 执行协议，以本目录为准。
- `简历/项目改造方案-医疗知识助手/` 仅保留求职展示材料。
- 当展示材料与本目录内容冲突时，以本目录为准。

## 📁 文件结构

```
docs/specs/medical-assistant/
├── README.md                          # 本文件
├── core/                              # 核心规范文档
│   ├── PRODUCT_BRIEF.md              # 产品定位、场景、求职叙事
│   ├── PRD.md                        # 功能范围、验收标准、版本边界
│   └── DEVELOPMENT_SPEC.md           # 开发、测试、发布规范
├── demo/                              # 演示相关
│   ├── DEMO_DATA_CHECKLIST.md        # demo 数据准备规范
│   ├── DEMO_DATA_SOURCES.md          # demo 数据真实公开来源清单
│   ├── DEMO_SCENARIOS.md             # 标准演示题集与回归场景
│   ├── DEMO_SCENARIO_MAPPING.md      # 标准题集到真实文档的映射
│   ├── DEMO_RUNBOOK_3MIN.md          # 3 分钟演示链路与降级策略
│   └── DEMO_MATERIALS.md             # 展示材料准备规范
├── interview/                         # 面试准备
│   ├── INTERVIEW_TALK_TRACK_1MIN.md  # 1 分钟面试讲稿
│   ├── INTERVIEW_TALK_TRACK_3MIN.md  # 3 分钟面试讲稿
│   └── NEXT_STEPS_GUIDE.md           # 下一步操作指南
├── operations/                        # 运维和执行
│   ├── AGENT_RUNBOOK.md              # agent 执行协议
│   ├── STARTUP_RUNBOOK.md            # 本地启动与验证 runbook
│   ├── EVALUATION_TROUBLESHOOTING.md # 评估问题排查指南
│   └── TASK_COMPLETION_SUMMARY.md    # 任务完成总结
├── tracking/                          # 状态跟踪
│   ├── EXECUTION_STATUS.yaml         # 当前状态真源
│   ├── CHANGELOG.md                  # 历史变更记录
│   └── SPEC_MANIFEST.yaml            # 机器可读索引
└── screenshots/                       # 截图目录
    └── README.md                     # 截图清单和拍摄指南
```

## 📖 阅读顺序

### 快速入门（5 分钟）

1. `README.md` - 本文件
2. `core/PRODUCT_BRIEF.md` - 产品定位
3. `interview/NEXT_STEPS_GUIDE.md` - 立即可做的事

### 产品和需求（15 分钟）

1. `core/PRODUCT_BRIEF.md` - 产品定位、用户、场景
2. `core/PRD.md` - 功能范围、验收标准
3. `core/DEVELOPMENT_SPEC.md` - 开发规范、项目路线

### 演示准备（30 分钟）

1. `demo/DEMO_SCENARIOS.md` - 12 题标准演示题集
2. `demo/DEMO_RUNBOOK_3MIN.md` - 3 分钟演示链路
3. `demo/DEMO_MATERIALS.md` - 展示材料准备规范
4. `interview/INTERVIEW_TALK_TRACK_1MIN.md` - 1 分钟讲稿
5. `interview/INTERVIEW_TALK_TRACK_3MIN.md` - 3 分钟讲稿

### 技术实现（1 小时）

1. `demo/DEMO_DATA_SOURCES.md` - 数据来源清单
2. `demo/DEMO_SCENARIO_MAPPING.md` - 题集到文档的映射
3. `operations/STARTUP_RUNBOOK.md` - 启动和验证
4. `operations/EVALUATION_TROUBLESHOOTING.md` - 评估问题排查

### 状态跟踪（随时查看）

1. `tracking/EXECUTION_STATUS.yaml` - 当前状态
2. `tracking/CHANGELOG.md` - 变更记录
3. `operations/TASK_COMPLETION_SUMMARY.md` - 任务完成总结

## 🎯 快速导航

### 我想...

- **了解产品定位** → `core/PRODUCT_BRIEF.md`
- **准备面试** → `interview/INTERVIEW_TALK_TRACK_1MIN.md`
- **运行演示** → `operations/STARTUP_RUNBOOK.md`
- **拍摄截图** → `demo/DEMO_MATERIALS.md`
- **查看进度** → `tracking/EXECUTION_STATUS.yaml`
- **解决问题** → `operations/EVALUATION_TROUBLESHOOTING.md`
- **了解下一步** → `interview/NEXT_STEPS_GUIDE.md`

## 更新协议

- 任何重要变更都必须同步更新：
  - `tracking/EXECUTION_STATUS.yaml`
  - `tracking/CHANGELOG.md`
- 新增 spec 文件时，必须同时更新 `tracking/SPEC_MANIFEST.yaml`
- 版本号格式统一为 `v主版本.次版本`
