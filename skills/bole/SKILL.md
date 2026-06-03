---
name: bole
description: 动态多Agent编排引擎。根据用户任务自动分析所需角色、拆解子任务、编排执行顺序和修正循环，生成主任务提示词并按参数执行（可等待用户确认）。当用户描述一个需要多步骤多角色协作的复杂任务时触发，如"开发一个XX系统"、"分析XX数据并生成报告"、"重构XX项目"等复杂工程任务。
version: 1.0
metadata:
  tags: [orchestration, multi-agent, dynamic, task-decomposition]
  category: orchestration
---

# 动态多Agent编排引擎

## 设计原则

**人与人沟通时，身份本身就是上下文** — "后端工程师"四个字就隐含了 RESTful、数据库、并发等专业知识。但 LLM 子Agent 没有"社会身份直觉"，只靠显式文本推理。因此，给子Agent 的角色描述必须包含充分的专业背景，否则它会在基础概念上反复确认或做出外行决策。

规则：**每个子Agent 的启动提示词中，必须包含对应角色的专业背景卡（professional context card）。**

## 总流程

用户给出任务 → **角色分析** → **任务拆解** → **生成编排提示词** → **执行或等待确认（由 auto_execute 控制）**

---

## Step 1：角色分析

根据任务内容，分析需要哪些角色。不要预设固定角色，而是根据任务特征动态决定。

### 分析维度

| 维度 | 问题 | 对应角色倾向 |
|------|------|-------------|
| 任务类型 | 开发/分析/重构/测试/文档？ | 决定核心角色 |
| 技术栈 | 前端/后端/数据/DevOps？ | 决定专业角色 |
| 质量要求 | 需要测试/安全审查/性能优化？ | 决定验证角色 |
| 复杂度 | 模块数量、依赖关系 | 决定角色粒度 |
| 交付物 | 代码/报告/文档/配置？ | 决定产出角色 |

### 角色模板库（按需取用，不限于此）

**设计类**：architect（架构师）、planner（规划师）、designer（设计师）
**开发类**：frontend-dev、backend-dev、fullstack-dev、data-engineer、devops
**验证类**：tester-functional、tester-performance、tester-security、reviewer
**分析类**：analyst（数据分析师）、researcher（研究员）
**文档类**：doc-writer、api-doc-generator

**规则**：
- 每个角色至少对应一个子Agent；可根据瓶颈增加该角色的 Agent 数量（见”动态调整机制”中扩缩策略）。
- 角色数量 = 基于复杂度分级的函数：复杂度等级 1 -> 3 角色；等级 2 -> 4-5 角色；等级 3 -> 6-8 角色。复杂度按模块数和外部依赖数计算：complexity = ceil((modules + external_dependencies)/2)。
- 同一角色可处理多个同类子任务（如一个 tester 测多个模块），且同一角色可由多个 Agent 并行承担以缓解瓶颈。

### 专业背景卡（Professional Context Card）

确定角色后，必须为每个角色生成一份专业背景卡，作为子Agent启动提示词的前置上下文。**背景卡的作用是让 LLM 立刻”进入角色”，减少不必要的概念确认和方向偏移。**

格式：

```
## 你的角色背景

你是一名{角色名称}，你具备以下专业背景：
- 核心技能：{3-5项关键技术能力}
- 工作原则：{2-3条该角色的职业行为准则}
- 产出标准：{该角色交付物的质量要求}
- 常见陷阱：{该角色容易犯的典型错误，提醒避免}

当前项目上下文：
- 技术栈：{根据任务推断}
- 项目目标：{任务概要}
- 你的职责范围：{本次任务中该角色负责的具体范围}
```

示例 — backend-dev 的背景卡：

```
## 你的角色背景

你是一名后端开发工程师（backend-dev），你具备以下专业背景：
- 核心技能：RESTful API 设计、关系型/NoSQL 数据库建模、并发处理、认证授权、错误处理
- 工作原则：接口先于实现设计；数据一致性优先于性能；安全是默认项不是可选项
- 产出标准：可运行的代码 + 接口文档 + 错误码定义；代码需通过 lint 检查
- 常见陷阱：忽略边界校验；硬编码配置；同步阻塞 IO；未处理异常扩散

当前项目上下文：
- 技术栈：FastAPI + PostgreSQL
- 项目目标：用户管理系统
- 你的职责范围：用户注册/登录 API、JWT 认证、用户信息 CRUD
```

---

## Step 2：任务拆解

### 拆解原则

1. **MECE**（互斥且穷尽）：子任务之间不重叠，合起来覆盖完整任务
2. **可独立执行**：每个子任务有明确的输入、输出、验收标准
3. **可排序**：子任务之间有明确的依赖关系

在执行前检测任务依赖图的循环；若发现环，则标记为 `invalid-dependencies` 并自动提出拆分建议或请求用户确认如何解环（默认不盲目修改任务结构）。

### 拆解模板

对每个子任务生成以下信息：

```
子任务ID: T-{序号}
名称: {简短描述}
角色: {对应角色}
依赖: [T-{依赖的任务ID列表}]
输入: {需要的文件/数据/上下文}
输出: {产出物路径和格式}
验收标准: {PASS/FAIL 判定条件}
执行步骤:
  1. {具体步骤}
  2. {具体步骤}
  ...
```

### 批量分组

将子任务按依赖关系分层，无依赖的并行执行：

```
Layer 0（可并行）: [T-1, T-2]    ← 无依赖
Layer 1（可并行）: [T-3, T-4]    ← 依赖 Layer 0
Layer 2:          [T-5]          ← 依赖 Layer 1
...
```

---

## Step 3：生成编排提示词

以 TASK.md 为模板框架，填入动态分析结果，生成完整的主任务提示词。

### 提示词结构

```markdown
## 核心原则
（继承 TASK.md 核心原则，按需调整）

## 初始化
- 确认任务描述，记为 TASK_DESC
- 确认输出目录，记为 OUTPUT_DIR
- 确认批量大小，记为 BATCH_SIZE：每次并行启动的子任务数量（针对同一 Layer）。默认 1；若为 3，则同一 Layer 同时运行 3 个子任务。
- 创建日志文件 {OUTPUT_DIR}/main-log.md：在创建或写入失败时重试 2 次（间隔 5s）；若仍失败，则根据参数 `output_error_policy` 采取 'abort' 或 'use-temp'（切换到临时目录并通知用户）。
- 探测并缓存 Agent ID 路径：在 `{OUTPUT_DIR}/agents/` 下创建 JSON 索引文件 `agents-index.json`，条目格式 {"agent_id": "<id>", "role": "<role>", "path": "agents/<id>.json"}。写入失败时重试 3 次并记录错误。

## 角色定义
（Step 1 的角色分析结果，每个角色必须附带专业背景卡）
{角色1}: {subagent_type}
  职责: {职责描述}
  背景卡: {Professional Context Card，见 Step 1 格式}

{角色2}: {subagent_type}
  职责: {职责描述}
  背景卡: {...}
...

## 任务计划
（Step 2 的子任务列表和分层）

## Phase 1: {首个Phase名称}
启动 {角色} 子Agent...
  先注入该角色的专业背景卡（Professional Context Card），再给出具体任务指令。
  注入方式：将背景卡作为子Agent prompt 的开头部分，确保它在任何任务指令之前。
{具体指令}

## Phase 2: {主执行Phase}
### 批量开发/执行循环
对每一层任务：
  Step 1: 批量执行（启动对应角色Agent）
  Step 2: 批量验证（启动验证角色Agent）
  Step 3: 修正循环（最多3轮）：对单个子任务的修正限制为最多 3 次重试；每个 Layer 的子任务各自独立计数。全局重试上限另设参数 `max_fix_rounds`。
    - 收集 FAIL 报告
    - resume 执行 Agent 修正
    - resume 验证 Agent 重测

  简要执行伪代码（按 Layer 进行）：

  ```pseudo
  for each layer in layers:
    for each task in layer:
      attempts = 0
      while attempts <= max_fix_rounds and not task.passed:
        start task with up to BATCH_SIZE parallelism
        validate task
        if failed:
          attempts += 1
          apply fixes
        else:
          mark task passed
    send layer completion summary
  ```
  Step 4: 状态更新 + 反馈

## Phase N: 收尾
统计、日志、报告

## 日志格式规范
（继承 TASK.md 日志规范）

## 关键规则
（继承 TASK.md 关键规则）
```

---

## Step 4：执行策略与确认

生成提示词后，按参数 `auto_execute` 决定是否自动启动：如果 `auto_execute=true` 则生成提示词后立即执行；如果 `auto_execute=false`（默认），则生成并向用户展示 TASK.md，等待用户发送确认命令 `CONFIRM_EXECUTE` 再行执行。始终在每个 Layer 完成时发送进度摘要。

### 执行时的优先级步骤

1. 验证阶段（Validation）：检查 `Agent ID` 可用性、`OUTPUT_DIR` 可写性、`requirements_file` 可读性等；验证失败按策略处理（参见参数 `error_policy` / `output_error_policy`）。

2. 执行阶段（Execution）：按 Layer 原子执行（每个 Layer 内子任务并行，Layer 之间顺序执行）。每个子任务有独立的修正重试计数（最多 `max_fix_rounds` 次）。

3. 出错与容错策略（On-agent-failure policy）：优先级顺序：重试 N 次 → 启动备用 Agent → 暂停该 Layer 并通知用户 → 根据 `fault_tolerance_policy` 决定跳过或回滚。若子Agent 在 `heartbeat_timeout` 秒内无响应，则标记为 `failed`；自动重试 `retry_count` 次；若仍失败，尝试备用 Agent 或上报并跳过，取决于 `fault_tolerance_policy`。

### 记忆与日志

- 每个子Agent的详细执行步骤写入记忆（memory 系统），用于审计与可重放。
- 主日志写入 `{OUTPUT_DIR}/main-log.md`（见日志写入错误处理策略）。
- 进度实时反馈给用户：在每个 Layer 完成时发送摘要（包含已完成任务列表、失败数、当前整体状态）到用户指定的通信渠道（参数：`status_channel`，可选：`console`, `email`, `webhook`），默认 `console`；默认每 5 分钟汇报一次，或在每个 Layer 完成时即时汇报。

---

## 动态调整机制

执行过程中根据实际情况动态调整：

| 情况 | 调整策略 |
|------|----------|
| 子任务实际比预期复杂 | 拆分为更细粒度的子任务 |
| 某角色瓶颈 | 增加该角色 Agent 数量（通过启动额外 Agent 并行处理相同角色任务），并遵循冗余与故障转移策略（见 On-agent-failure policy）。 |
| 验证发现新问题类型 | 增加对应验证角色 |
| 子Agent返回格式异常 | 暂停并报错，不继续循环 |
| 子Agent循环重复输出 | 立即终止，报错 |
| Agent ID 获取失败 | 重试 3 次（指数退避），若仍失败，切换到备用 ID 池或将任务退回到 `waiting_for_admin` 并通知用户，说明故障原因。 |

---

## 使用方式

用户直接描述任务即可触发，例如：

- "开发一个用户管理系统，需求文档在 /path/to/req.md"
- "分析这批交易数据，生成策略报告"
- "重构 XX 项目，提高测试覆盖率到80%"
- "用 Vue3+FastAPI 开发一个博客系统"

### 参数

- `task`: 任务描述（必填）
- `requirements_file`: 需求文档路径（可选）
- `output_dir`: 输出目录（默认：当前项目目录）
- `batch_size`: 批量大小（默认：1）
- `max_fix_rounds`: 修正循环最大轮数（默认：3）

新增/补充参数：

- `auto_execute`: 是否自动执行（布尔，默认：false）。如果为 `true`，则生成提示词后立即执行；如果为 `false`，生成 TASK.md 并等待用户发送 `CONFIRM_EXECUTE` 再执行。
- `status_channel`: 进度反馈渠道（可选）：`console`、`email`、`webhook`。默认 `console`。
- `output_error_policy`: 输出目录写入错误处理策略（可选）：`abort` | `use-temp`。默认 `abort`。
- `heartbeat_timeout`: 子Agent 心跳超时时间（秒），默认 300。
- `retry_count`: 子Agent 操作重试次数，默认 2（在 heartbeat 超时或临时错误时使用）。
- `fault_tolerance_policy`: 故障容忍策略（可选）：`abort` | `skip` | `escalate`（默认 `escalate`）。
- `error_policy`: 当 `requirements_file` 指定但不可读取时的处理策略：`abort` | `ask` | `proceed-with-heuristics`（默认 `ask`）。

行为说明：如果 `requirements_file` 指定但不可读取，系统将依据 `error_policy` 抉择：立即中止并报错（`abort`）；或向用户询问上传/修改（`ask`）；或根据启发式继续执行并记录不确定性（`proceed-with-heuristics`）。
