<h1 align="center">伯乐 — 多Agent编排引擎</h1>
<p align="center">
  <em>支持 Claude Code、Codex、Cursor、Copilot、Gemini CLI 等多平台。</em>
</p>

<p align="center">
  <a href="#-安装"><img src="https://img.shields.io/badge/快速开始-blue" alt="Quick Start" /></a>
  <a href="https://github.com/LisonEvf/bole/blob/main/LICENSE"><img src="https://img.shields.io/badge/许可证-MIT-yellow" alt="License: MIT" /></a>
  <a href="https://docs.anthropic.com/en/docs/claude-code"><img src="https://img.shields.io/badge/Claude_Code-8A2BE2" alt="Claude Code" /></a>
  <a href="#codex"><img src="https://img.shields.io/badge/Codex-000000" alt="Codex" /></a>
  <a href="#vs-code--github-copilot"><img src="https://img.shields.io/badge/Copilot-24292e" alt="Copilot" /></a>
  <a href="#copilot-cli"><img src="https://img.shields.io/badge/Copilot_CLI-24292e" alt="Copilot CLI" /></a>
  <a href="#gemini-cli"><img src="https://img.shields.io/badge/Gemini_CLI-4285F4" alt="Gemini CLI" /></a>
  <a href="#opencode"><img src="https://img.shields.io/badge/OpenCode-38bdf8" alt="OpenCode" /></a>
</p>


## 简介

通用任务编排框架。根据用户任务描述，自动分析所需角色、拆解子任务、编排执行顺序和修正循环，生成主任务提示词并立即执行。

## 核心理念

- **动态角色分析** — 不预设固定角色，根据任务内容动态决定
- **MECE 任务拆解** — 互斥且穷尽，每个子任务可独立执行
- **模板化编排** — 以 TASK.md 为模板，填入动态分析结果
- **修正循环** — 开发→验证→修正→重测，最多 3 轮
- **上下文保护** — 主Agent只调度不干活，不读子Agent产出内容

## 项目结构

```
bole/
├── CLAUDE.md                         # 项目说明
├── TASK.md                           # 编排提示词模板
├── README.md                         # 本文件
├── .claude-plugin/
│   ├── marketplace.json              # 插件清单
│   ├── install.sh                    # Linux/macOS 安装脚本
│   └── install.ps1                   # Windows 安装脚本
├── scripts/
│   └── analyze-task.py               # 任务分析辅助脚本
└── skills/
    └── bole/
        └── SKILL.md                  # 主 skill 定义
```

## 安装

### 方式一：Plugin Marketplace 安装（推荐）

在 Claude Code 中执行：

```
/plugin marketplace add LisonEvf/bole
/plugin install bole
```

### 方式二：手动安装

1. Clone 仓库：

```bash
git clone https://github.com/LisonEvf/bole.git
```

2. 在 Claude Code 的 `settings.json` 中添加插件路径：

```json
{
  "plugins": [
    "/path/to/bole"
  ]
}
```

### 方式三：作为项目级插件

将 `bole` 目录放在项目根目录下，Claude Code 会自动识别 `.claude-plugin/marketplace.json`。

## 使用方式

在 Claude Code 中直接描述任务即可触发：

```
请帮我开发一个用户管理系统，需求文档在 /path/to/req.md
```

```
分析这批交易数据，生成策略回测报告
```

```
用 Vue3+FastAPI 开发一个博客系统
```

### 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `task` | 任务描述（必填） | - |
| `requirements_file` | 需求文档路径 | 可选 |
| `output_dir` | 输出目录 | 当前项目目录 |
| `batch_size` | 批量大小 | 1 |
| `max_fix_rounds` | 修正循环最大轮数 | 3 |

## 辅助脚本

```bash
# 分析任务，输出角色和子任务建议
python scripts/analyze-task.py "开发一个用户管理系统，含注册登录和个人信息管理"

# JSON 格式输出
python scripts/analyze-task.py "开发一个用户管理系统" --json
```

## 卸载

```
/plugin uninstall bole
```

或从 `settings.json` 中移除对应的插件路径。

## 执行流程

```
用户描述任务
  ↓
Step 1: 角色分析（关键词匹配 + 规则补充）
  ↓
Step 2: 任务拆解（MECE + 依赖分层）
  ↓
Step 3: 生成编排提示词（TASK.md 模板 + 动态填充）
  ↓
Step 4: 立即执行
  ├─ Phase 1: 规划（启动 planner）
  ├─ Phase 2: 批量开发/执行循环
  │   ├─ 批量执行（启动对应角色 Agent）
  │   ├─ 批量验证（启动验证角色 Agent）
  │   └─ 修正循环（最多3轮）
  └─ Phase N: 收尾（统计、日志、报告）
```

[![Star History Chart](https://api.star-history.com/svg?repos=LisonEvf/bole&type=Date)](https://star-history.com/#LisonEvf/bole&Date)
