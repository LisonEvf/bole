# Bole — 伯乐多Agent编排引擎

## 项目定位

通用任务编排框架，根据任务描述动态分析角色、拆解子任务、编排执行流程。

## 核心文件

- `TASK.md` — 编排提示词模板（主Agent的行为规范）
- `skills/bole/SKILL.md` — skill 定义（角色分析 + 任务拆解 + 编排生成）
- `scripts/analyze-task.py` — 任务分析辅助脚本

## 工作流程

1. 用户描述任务
2. SKILL.md 定义的分析流程被触发
3. 动态确定角色 → 拆解子任务 → 生成编排提示词
4. 以 TASK.md 模板格式生成具体提示词
5. 立即执行

## 关键约束

- 主Agent 只调度不干活
- 子Agent 详细执行步骤写入 memory
- 实时日志记录到 `{OUTPUT_DIR}/main-log.md`
- 修正循环最多 3 轮
- Agent ID 必须准确收集和复用
