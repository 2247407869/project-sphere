# Project Sphere 设计文档 (DESIGN.md)

## 1. 系统愿景
Project Sphere 旨在打造一个“主权、理性、高性能”的个人第二大脑。它不仅是一个对话机器人，更是一个具备多层记忆整合能力的 AI 助手。

## 2. 三层记忆架构 (Triple Memory Architecture)

### M1: 工作记忆 (Working Memory)
- **定义**：当前对话的 Context。
- **载体**：HTTP 请求中的 `history` 数组。
- **特性**：高实时性，由 WebDAV 自动同步。

### M2: 动态摘要 (Dynamic Summary)
- **定义**：对过往对话内容的“语义压缩”与“认知消化”。
- **逻辑**：采用“反思式递归模型”。并非机械压缩，而是在每轮归档时模拟人类睡眠时的记忆巩固（Memory Consolidation），提取当日的核心见解、情感基调与行动指南。
- **结构**：`New M2 = Consolidate(Old M2 + Today's Reflection)`。
- **时序性**：严格遵循“旧在前、新在后”的线性叙事，体现系统的持续进化。

### M3: 长期记忆 (Long-term Memory)
- **定义**：用户的“认知外显化”笔记库，存储于 Markdown 文件中。
- **定位**：专门负责承载人类大脑易遗忘的高熵信息——决策逻辑（Rationale）、偏照细节、关键 ID、长期战略等。
- **采集逻辑**：由 `MemoryPatcher` 执行，具备“重要性筛选”机制。系统会自动识别对话中的“反思价值”，而非机械地做会议记录。
- **归纳方式**：支持自动裂变（Auto-Sharding），根据信息领域自动创建新主题文件，实现笔记的有机生长。

## 3. 多模态视觉层 [New 2025.12]
- **引擎**：Gemini 3 Flash。
- **触发**：当前端传入 `images` 负载时，系统自动路由至 Gemini 视觉引擎。
- **ROI 考量**：针对视觉任务，Gemini 3 Flash 提供了一流的性能损耗比与长文本处理能力。

## 4. 技术栈
- **后端**：FastAPI + LangChain + LangGraph。
- **前端**：Vanilla HTML/JS/CSS (追求极致响应与零依赖)。
- **存储**：InfiniCloud WebDAV (个人隐私主权)。
- **模型**：DeepSeek (文本/思考) + Gemini (视觉)。

---
*Created by Antigravity on 2025-12-31*
