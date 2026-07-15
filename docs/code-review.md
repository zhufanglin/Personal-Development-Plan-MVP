# Code Review — Course Learning Planner Agent

| Field | Value |
|-------|-------|
| Review Date | 2026-07-11 |
| Review Type | 设计阶段全项目审查（无代码，纯设计评审） |
| Reviewer | 3 个并行 Agent 交叉审查 |
| Project Phase | 设计完成，编码未开始 |
| Files Reviewed | 14 个文件，3,500+ 行设计文档 + 230 行数据文件 |

---

## 目录

1. [审查摘要](#1-审查摘要)
2. [发现总览](#2-发现总览)
3. [CRITICAL 发现](#3-critical-发现)
4. [HIGH 发现](#4-high-发现)
5. [MEDIUM 发现](#5-medium-发现)
6. [LOW 发现](#6-low-发现)
7. [分维度评审](#7-分维度评审)
8. [优化建议](#8-优化建议)
9. [修复优先级路线图](#9-修复优先级路线图)

---

## 1. 审查摘要

通过对 14 个文件的交叉审查，发现 **2 个 CRITICAL、4 个 HIGH、8 个 MEDIUM、5 个 LOW** 级别问题。

**核心结论：项目存在两个严重的不兼容设计分支（4-Tool vs 6-Tool），以及课程数据与全部文档示例的零重叠问题。这两个问题必须在编码开始前解决，否则将导致不可运行的实现。**

没有 Python 源代码——项目处于纯设计阶段，这本身不是问题，但意味着所有评审聚焦于设计一致性和完整性。

---

## 2. 发现总览

| # | 发现 | 严重度 | 涉及文件 |
|---|------|--------|---------|
| **C1** | 4-Tool 与 6-Tool 架构冲突 | **CRITICAL** | tool-design.md, system-design.md, plan.md, 两个 prompt 文件 |
| **C2** | 课程数据与全部文档示例零重叠 | **CRITICAL** | courses.json vs 所有文档中的示例 |
| **H1** | 无源代码实现 | **HIGH** | src/, tests/ |
| **H2** | 两个 System Prompt 互不兼容 | **HIGH** | prompts/system_prompt.txt vs .md |
| **H3** | README 与实际文件清单不一致 | **HIGH** | README.md |
| **H4** | courses.json 与 prerequisites.json 数据冲突 | **HIGH** | data/ JSON 文件 |
| **M1** | 错误码体系：4分类 vs 8编码 | **MEDIUM** | system-design.md, tool-design.md |
| **M2** | Mermaid 图模型数量与依赖不一致 | **MEDIUM** | diagrams/, system-design.md |
| **M3** | 数据流管道：6阶段 vs 4阶段 | **MEDIUM** | system-design.md, tool-design.md |
| **M4** | Plan 称"2个异常"，实际设计有3个 | **MEDIUM** | plan.md |
| **M5** | 文档版本号不一致 | **MEDIUM** | system-design.md(1.0.0), tool-design.md(2.0.0), system_prompt.md(2.0.0) |
| **M6** | system_prompt.md 位置错误 | **MEDIUM** | prompts/system_prompt.md |
| **M7** | FSM 状态数量自相矛盾 | **MEDIUM** | system-design.md |
| **M8** | COURSE_NOT_FOUND 在不同文档中处理方式不同 | **MEDIUM** | system-design.md, plan.md, workflow.md |
| **L1** | requirements.txt 最小化但够用 | **LOW** | requirements.txt |
| **L2** | 模型文件拆分 vs 单文件 | **LOW** | plan.md, system-design.md |
| **L3** | 重复/分歧的架构图 | **LOW** | diagrams/architecture.mermaid, system-design.md |
| **L4** | 图表示例值与真实数据不匹配 | **LOW** | diagrams/react-workflow.mermaid |
| **L5** | 状态名不一致 (PREREQ_CONFLICT vs PREREQ_FAILED) | **LOW** | system-design.md, plan.md |

---

## 3. CRITICAL 发现

### C1. 4-Tool 与 6-Tool 架构冲突

这是项目最严重的设计矛盾。存在两套完全独立的 Tool 设计：

**设计 A (6-Tool)** — plan.md, system-design.md, architecture.md, workflow.md, README.md, prompts/system_prompt.txt:

| # | Tool 名称 |
|---|-----------|
| 1 | `get_course_info` |
| 2 | `check_prerequisites` |
| 3 | `generate_learning_path` |
| 4 | `create_daily_plan` |
| 5 | `assess_feasibility` |
| 6 | `recommend_resources` |

**设计 B (4-Tool)** — tool-design.md (v2.0.0), prompts/system_prompt.md (v2.0.0):

| # | Tool 名称 |
|---|-----------|
| 1 | `get_course_info` |
| 2 | `get_prerequisite` |
| 3 | `calculate_learning_time` |
| 4 | `generate_learning_plan`（编排器，内部调用前3个Tool+生成日计划+生成资源） |

**重叠的Tool: 仅 `get_course_info` 一个名称相同。** 其余 Tool 的名称、签名、职责完全不同。

**影响:**
- plan.md 的 FSM 状态机依赖 6 个 Tool 的状态转换，如果实现 4-Tool 则 FSM 失效
- system-design.md 的 §2.3 状态转换表引用 6 个 Tool，不可直接用于 4-Tool
- 开发者无法同时实现两套设计

**建议:** 在设计文档层面做出决策。要么：
- 采用 6-Tool，将 tool-design.md 和 system_prompt.md 退役或标记为 v2 Future
- 采用 4-Tool，重写 plan.md 的 FSM、system-design.md 的状态机、workflow.md 的流程、architecture.md 的组件图

### C2. 课程数据与全部文档示例零重叠

`data/courses.json` 包含 10 门大数据技术栈课程（Python, SQL, Linux, Git, Java, Hadoop, Hive, Spark, Kafka, Flink）。

但**所有其他文档**中的示例使用完全不同的课程名称：

| 文档中引用的课程 | 实际数据中是否存在 |
|-----------------|-------------------|
| "Python Programming" (20h) | ❌ 实际为 "Python" (24h) |
| "Machine Learning" (50h) | ❌ 不存在 |
| "Mathematics for ML" (30h) | ❌ 不存在 |
| "Data Structures and Algorithms" | ❌ 不存在 |
| "JavaScript Fundamentals" | ❌ 不存在 |
| "Web Development with React" | ❌ 不存在 |
| "量子计算" (错误示例) | ❌ 不存在 |
| "Spark" | ✅ 存在 (40h) |

**影响:** 所有 workflow 示例、tool-design 返回示例、plan 验收场景、Mermaid 图中的课程引用均不匹配实际数据。项目无法按文档验证。

**建议:** 将所有文档中的课程示例更新为 courses.json 中的实际课程名称和学时。

---

## 4. HIGH 发现

### H1. 无源代码实现（状态说明）

`src/` 和 `tests/` 目录为空。plan.md 的 22 个任务全部 `[ ]`。项目处于纯设计阶段。

这不是缺陷，但 README 中的 `pip install` 和 `python -m src.ui.cli` 指令无法执行。

**建议:** README 中加注 "🚧 项目处于设计阶段，代码即将实现"。

### H2. 两个互不兼容的 System Prompt 文件

| 文件 | Tool 数 | 语言 | 版本 | 行数 |
|------|--------|------|------|------|
| `prompts/system_prompt.txt` | 6 | English | 无 | 79 |
| `prompts/system_prompt.md` | 4 | Chinese | v2.0.0 | 518 |

两者在 `prompts/` 目录中共存且内容互不兼容。plan.md 的 milestone 3.1 指定 `prompt_loader.py` 加载 `system_prompt.txt`——但如果.md是v2.0.0版本，则它是设计上的"新版本"。

**建议:** 
- 保留一个版本作为权威 System Prompt
- 如果 `.md` 是规范文档而非运行时 prompt，移到 `docs/`
- 更新 `prompt_loader.py` 的加载目标

### H3. README 与实际文件清单不一致

- README 未列出 `docs/system-design.md`（1224行核心文档）
- README 未列出 `prompts/system_prompt.md`
- README 描述的 `src/` 结构无实际文件
- README 列 6 个 Tool，与 v2.0.0 的 tool-design.md (4 Tool) 不一致

**建议:** 更新 README 反映所有实际文件。标注代码目录为"待实现"。

### H4. courses.json 与 prerequisites.json 数据冲突

Java 课程在两个文件中的先修标注不同：
- `courses.json`: `"prerequisite": ["Python"]` — 硬性要求
- `prerequisites.json`: `"required": [], "recommended": ["Python"]` — 仅推荐

这导致 `get_course_info` 返回 Python 为必需先修，而 `get_prerequisite` 返回为建议先修——Agent 在不同步骤中会给出矛盾建议。

**建议:** 二选一并统一。推荐方案：Python 为 Java 的 recommended（两门都是编程语言，侧重不同）。

---

## 5. MEDIUM 发现

### M1. 错误码体系不一致

- `system-design.md` §3.4: 4 个错误分类 (NOT_FOUND / VALIDATION_ERROR / DATA_ERROR / BUSINESS_RULE)
- `tool-design.md` §7.2: 8 个具体错误码 (COURSE_NOT_FOUND / VALIDATION_ERROR / PREREQUISITE_CONFLICT / TIME_INSUFFICIENT / CIRCULAR_DEPENDENCY / MAX_RECURSION_DEPTH / DATA_CORRUPTION / INTERNAL_ERROR)

8 编码体系更完整可用。4 分类体系缺少 DETAILS。

**建议:** 统一采用 tool-design.md 的 8 错误码体系。更新 system-design.md。

### M2. Mermaid 图不一致

4 个位置包含 Mermaid 图，但模型数量、依赖边、状态名均不完全一致：
- `diagrams/architecture.mermaid` — 4 个 Model，缺少 PrerequisiteCheck
- `system-design.md` §5.1 — 5 个 Model，最完整
- `system-design.md` §5.4 — 模型聚合为单文件 schemas.py
- `plan.md` — 无模型层

**建议:** 以 `system-design.md` 内嵌图为权威版本。更新或删除 `diagrams/architecture.mermaid`。

### M3. 数据流管道描述不一致

- `system-design.md` §4: 6 阶段管道，每个 Tool 后有具体的 ReActState 快照
- `tool-design.md` §2: 4 阶段管道，generate_learning_plan 是编排器

如果采用 4-Tool，system-design.md 的整个 §4 需要重写。

**建议:** 在选定 Tool 架构后统一数据流描述。

### M4. Plan 称为"2个异常"，实际为 3 个错误场景

plan.md 第 12 行: "handle two exception scenarios (prerequisites conflict and insufficient time)"

但 FSM 实际处理 3 种错误终止场景：
1. 先修冲突 → PREREQ_CONFLICT
2. 时间不足 → TIME_INSUFFICIENT
3. 课程不存在 → COURSE_NOT_FOUND

**建议:** 更新 plan.md 描述为 3 个异常/错误场景。

### M5. 文档版本号不一致

| 文档 | 版本 |
|------|------|
| system-design.md | 1.0.0 |
| tool-design.md | 2.0.0 |
| system_prompt.md | 2.0.0 |
| architecture.md | 无 |
| workflow.md | 无 |
| plan.md | 无 |

v2.0.0 的文档（tool-design.md, system_prompt.md）恰好都是 4-Tool 设计，而 v1.0.0（system-design.md）是 6-Tool——表明存在一次未完成的 v2 迁移。

**建议:** 要么完成 v2 迁移（更新 system-design.md → 2.0.0），要么回退 v2.0.0 文档到 1.0.0。

### M6. system_prompt.md 位置错误

`prompts/system_prompt.md` (518 行) 是一份**规范文档**——包含表格、版本号、元数据——而非运行时 prompt 模板。它应位于 `docs/` 目录。

`prompts/system_prompt.txt` (79 行) 才是运行时 prompt。

**建议:** 将 `system_prompt.md` 移到 `docs/`。保留 `prompts/` 中仅放运行时加载的模板文件。

### M7. FSM 状态数量自相矛盾

`system-design.md` §2.2: "deterministic Finite State Machine (FSM) with **8 states**"

实际状态数量：
1. INIT
2. GET_COURSE_INFO
3. CHECK_PREREQUISITES
4. PREREQ_CONFLICT (Terminal)
5. ASSESS_FEASIBILITY
6. TIME_INSUFFICIENT (Terminal)
7. GENERATE_LEARNING_PATH
8. CREATE_DAILY_PLAN
9. RECOMMEND_RESOURCES
10. FINAL_ANSWER (Terminal)
11. COURSE_NOT_FOUND (Terminal, 仅 Mermaid 图中)

**共 10-11 个状态，非 8 个。**

**建议:** 修正为 "10 states" 或统一减至 8 个。

### M8. COURSE_NOT_FOUND 处理不一致

3 个文档对该错误状态的处理各不同：
- `system-design.md` §5.3 Mermaid: 有独立 COURSE_NOT_FOUND 状态
- `system-design.md` §2.3 转换表: 直接跳到 FINAL_ANSWER
- `plan.md` milestone 3.2: 未提及
- `workflow.md`: 未提及

**建议:** 统一处理——推荐在 FSM 中添加显式的 COURSE_NOT_FOUND 状态。

---

## 6. LOW 发现

| # | 发现 | 建议 |
|---|------|------|
| L1 | requirements.txt 最小化但够用 | 无需修改。已注释的 rich 可在实现时取消注释 |
| L2 | 模型文件拆分 vs 单文件 | plan.md 指定 3 文件，system-design.md 指定 1 文件。建议 MVP 使用单文件 `schemas.py`（~10个模型） |
| L3 | 重复架构图 | 保留 system-design.md 内嵌版，更新或删除 diagrams/architecture.mermaid |
| L4 | 图表示例值不匹配 | 更新 diagrams/react-workflow.mermaid 使用 courses.json 中的实际课程 |
| L5 | 状态名不一致 | plan.md 用 PREREQ_FAILED，system-design.md 用 PREREQ_CONFLICT。统一为后者（语义更明确） |

---

## 7. 分维度评审

### 7.1 Agent 架构

| 评分维度 | 评级 | 说明 |
|---------|------|------|
| ReAct 模式正确性 | ✅ 良好 | Thought→Action→Observation 循环正确定义 |
| MVP 简化合理性 | ✅ 良好 | 规则化 FSM 是合理的 MVP 简化，LLM 替换路径已设计 |
| 状态机完整性 | ⚠️ 需改进 | 状态数矛盾(8 vs 10-11)、RECOMMEND_RESOURCES 缺失于 plan、COURSE_NOT_FOUND 处理不一致 |
| 文档间一致性 | ❌ 差 | 两个 Tool 架构(4 vs 6)、FSM 定义分歧、状态名不一致 |

### 7.2 Workflow 设计

| 评分维度 | 评级 | 说明 |
|---------|------|------|
| 工作流顺序 | ✅ 良好 | Step 1→2→3→4 的依赖顺序合理，条件门控设计正确 |
| 异常分支 | ✅ 良好 | 先修冲突和时间不足的处理逻辑定义为终端状态 |
| ReAct 实现 | ⚠️ 需改进 | 声明为 ReAct 但实现为固定管道。需添加免责声明说明 MVP 简化 |
| 文档间一致性 | ⚠️ 需改进 | workflow.md 的 STEPS 列表缺少 recommend_resources 步骤 |

### 7.3 Prompt 设计

| 评分维度 | 评级 | 说明 |
|---------|------|------|
| 身份与目标 | ✅ 良好 | 身份定义清晰、专业领域明确、核心原则"诚实优于乐观" |
| Tool Calling 规则 | ✅ 良好 | 5 条规则覆盖强制使用、ReAct 格式、参数来源、预验证 |
| 幻觉预防 | ✅ 优秀 | 6 条禁令 + 6 项自检清单 + 行为边界表，是项目亮点 |
| 输出格式 | ✅ 良好 | 3 种格式（成功/先修冲突/时间不足）有完整模板 |
| 文档间一致性 | ❌ 差 | 两个 prompt 文件指向不同的 Tool 集合 |

### 7.4 Tool 设计

| 评分维度 | 评级 | 说明 |
|---------|------|------|
| API 契约完整性 | ✅ 优秀 | 完整输入/输出 Schema、错误码体系、Python 签名、JSON 示例 |
| 异常处理 | ✅ 优秀 | 3 种业务场景每种都有详细的行为规范 |
| 前向兼容性 | ✅ 良好 | Tool Registry 模式支持添加新 Tool 无需改动核心 |
| 文档间一致性 | ❌ 差 | 存在两个不兼容的 Tool 集合(4 vs 6) |

### 7.5 异常处理

| 评分维度 | 评级 | 说明 |
|---------|------|------|
| 异常类型覆盖 | ✅ 良好 | 覆盖先修冲突、时间不足、课程不存在、参数验证、内部错误 |
| 错误响应格式 | ✅ 良好 | 统一 ErrorResponse 结构(code/message/details/tool_name) |
| 可恢复性分类 | ✅ 良好 | 4xx/5xx 模拟分类合理 |
| 文档间一致性 | ⚠️ 需改进 | 错误码体系有 4分类 vs 8编码的分歧 |

### 7.6 Python 代码

| 评分维度 | 评级 | 说明 |
|---------|------|------|
| 代码存在性 | ⚠️ N/A | 无任何 Python 源代码，无法评审 |

### 7.7 项目结构

| 评分维度 | 评级 | 说明 |
|---------|------|------|
| 目录组织 | ✅ 良好 | src/agent, src/tools, src/models, src/ui 分层清晰 |
| 文档组织 | ⚠️ 需改进 | system_prompt.md 在 prompts/ 而非 docs/，README 不完整 |
| 数据与文档对齐 | ❌ 差 | courses.json 与全部文档示例不一致 |
| 文件冗余 | ⚠️ 需改进 | 重复的架构图、重复的 prompt 文件 |

---

## 8. 优化建议

### 8.1 架构层面

| # | 建议 | 优先级 |
|---|------|--------|
| 1 | **选定 Tool 架构（4-Tool 或 6-Tool）**，将另一套文档退役或标记为 Future | **P0** |
| 2 | **将所有文档示例更新为 courses.json 中的实际课程** | **P0** |
| 3 | 统一 FSM 状态列表和名称，在所有文档中传播 | P1 |
| 4 | 在每个文档中添加版本号和与相关文档的交叉引用 | P1 |
| 5 | 建立 `docs/CHANGELOG.md` 记录设计版本变更 | P2 |

### 8.2 文档层面

| # | 建议 | 优先级 |
|---|------|--------|
| 6 | 将 `prompts/system_prompt.md` 移到 `docs/`，仅保留运行时 prompt 在 `prompts/` | P1 |
| 7 | 更新 README 反映所有实际文件 + 标注"代码待实现" | P1 |
| 8 | 删除冗余的 `diagrams/architecture.mermaid`（保留 system-design.md 内嵌版） | P1 |
| 9 | 为所有文档添加版本号和最后更新日期 | P2 |
| 10 | 补充 `docs/CHANGELOG.md` | P2 |

### 8.3 数据层面

| # | 建议 | 优先级 |
|---|------|--------|
| 11 | 统一 Java 的 prereq 状态（courses.json vs prerequisites.json） | **P0** |
| 12 | 统一字段命名约定（prerequisite vs prerequisites） | P1 |
| 13 | 为 courses.json 添加 JSON Schema 验证 | P2 |

### 8.4 实现准备

| # | 建议 | 优先级 |
|---|------|--------|
| 14 | 将 plan.md 更新为与实际课程数据匹配的验收标准 | **P0** |
| 15 | 为该版本选定一个确定的 Tool 数量并更新 plan.md 的 Decision 5 | P1 |
| 16 | 开始实现前，先创建 `src/models/schemas.py` 作为所有 Pydantic 模型的单一真实来源 | P1 |

---

## 9. 修复优先级路线图

```
Phase 0: Critical Fixes (阻塞实现)
────────────────────────────────────
□ C1: 确定 Tool 架构 (4 vs 6)，退役另一套
□ C2: 统一课程名称（所有文档 → courses.json 中的实际数据）
□ H4: 统一 Java prereq 状态
□ 14: 更新 plan.md 验收标准为实际课程

Phase 1: High Priority (实现中会造成问题)
─────────────────────────────────────────
□ H2: 合并 System Prompt 文件
□ H3: 更新 README
□ M4: 纠正 plan.md 异常计数 (2→3)
□ M7: 纠正 FSM 状态计数 (8→10)
□ M8: 统一 COURSE_NOT_FOUND 处理
□ 6:  移动 system_prompt.md 到 docs/
□ 7:  更新 README 文件清单
□ 8:  清理冗余架构图
□ 11: 统一字段命名

Phase 2: Medium Priority (改进质量)
────────────────────────────────────
□ M1: 统一错误码体系
□ M2: 统一 Mermaid 图
□ M3: 统一数据流描述
□ M5: 添加版本号
□ 5:  建立 CHANGELOG.md
□ 9:  文档添加日期
□ 12: 添加 JSON Schema
□ 15: 更新 plan Decision 5

Phase 3: Low Priority (锦上添花)
─────────────────────────────────
□ L1-L5: 修复文档细节
□ 13: courses.json JSON Schema
□ 16: 创建 schemas.py
```

---

## 附录: 审查方法

本次审查使用 **3 个并行 Explore Agent**，每个负责不同的评审维度：

| Agent | 审查维度 | 产出 |
|-------|---------|------|
| Agent 1 | Agent 架构 + Workflow + Plan 一致性 | 11 项发现 |
| Agent 2 | Prompt + Tool 设计 + 数据一致性 | 未完成 |
| Agent 3 | 异常处理 + 项目结构 + 数据流 | 14 项发现 |

审查方法：交叉阅读法（Cross-Document Reading）——每份文档与其他文档交叉验证一致性，识别矛盾、遗漏和冗余。
