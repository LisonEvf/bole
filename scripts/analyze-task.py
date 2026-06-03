"""
任务分析辅助脚本 — 解析任务描述，输出角色和子任务建议。
供主Agent在 Step 1/2 阶段参考使用。
"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import re
import sys
from dataclasses import dataclass, field


@dataclass
class Role:
    name: str
    subagent_type: str
    description: str


@dataclass
class SubTask:
    id: str
    name: str
    role: str
    dependencies: list[str] = field(default_factory=list)
    inputs: str = ""
    outputs: str = ""
    acceptance: str = ""
    steps: list[str] = field(default_factory=list)


# 角色识别关键词映射
ROLE_KEYWORDS: dict[str, dict] = {
    "planner": {
        "keywords": ["需求", "规划", "设计", "架构", "方案", "分析", "计划", "requirement", "plan", "design", "architect"],
        "description": "规划师 — 读取需求、设计方案、制定计划",
        "subagent_type": "planner",
    },
    "backend-dev": {
        "keywords": ["后端", "接口", "API", "服务", "server", "backend", "数据库", "database", "模型", "model"],
        "description": "后端开发 — 实现后端接口、数据模型、业务逻辑",
        "subagent_type": "backend-dev",
    },
    "frontend-dev": {
        "keywords": ["前端", "页面", "UI", "组件", "界面", "frontend", "web", "Vue", "React", "HTML", "CSS"],
        "description": "前端开发 — 实现页面、组件、交互逻辑",
        "subagent_type": "frontend-dev",
    },
    "data-engineer": {
        "keywords": ["数据", "ETL", "pipeline", "数据处理", "data", "清洗", "转换", "爬虫", "抓取"],
        "description": "数据工程师 — 数据采集、清洗、转换、存储",
        "subagent_type": "data-engineer",
    },
    "analyst": {
        "keywords": ["分析", "统计", "报告", "可视化", "图表", "analysis", "report", "chart", "BI"],
        "description": "分析师 — 数据分析、统计建模、生成报告",
        "subagent_type": "analyst",
    },
    "tester-functional": {
        "keywords": ["测试", "验证", "QA", "test", "unit test", "集成测试", "功能测试"],
        "description": "功能测试 — 验证功能正确性、边界条件、异常处理",
        "subagent_type": "tester-functional",
    },
    "tester-performance": {
        "keywords": ["性能", "压力", "并发", "延迟", "吞吐", "performance", "load", "benchmark"],
        "description": "性能测试 — 验证响应时间、吞吐量、资源占用",
        "subagent_type": "tester-performance",
    },
    "tester-security": {
        "keywords": ["安全", "漏洞", "注入", "XSS", "CSRF", "权限", "security", "auth"],
        "description": "安全测试 — 验证认证授权、输入校验、漏洞扫描",
        "subagent_type": "tester-security",
    },
    "reviewer": {
        "keywords": ["审查", "review", "code review", "代码质量", "重构"],
        "description": "代码审查 — 检查代码质量、设计模式、最佳实践",
        "subagent_type": "reviewer",
    },
    "doc-writer": {
        "keywords": ["文档", "README", "API文档", "doc", "说明", "使用手册"],
        "description": "文档编写 — 生成项目文档、API文档、使用指南",
        "subagent_type": "doc-writer",
    },
    "devops": {
        "keywords": ["部署", "CI/CD", "Docker", "K8s", "运维", "deploy", "container", "pipeline"],
        "description": "DevOps — 构建部署流水线、容器化、环境配置",
        "subagent_type": "devops",
    },
}


def analyze_roles(task_desc: str) -> list[Role]:
    """根据任务描述关键词匹配角色"""
    task_lower = task_desc.lower()
    matched: dict[str, Role] = {}

    for role_name, role_info in ROLE_KEYWORDS.items():
        for kw in role_info["keywords"]:
            if kw.lower() in task_lower:
                matched[role_name] = Role(
                    name=role_name,
                    subagent_type=role_info["subagent_type"],
                    description=role_info["description"],
                )
                break

    # 确保至少有 planner 和一个执行角色
    if "planner" not in matched:
        matched["planner"] = Role(
            name="planner",
            subagent_type="planner",
            description="规划师 — 读取需求、设计方案、制定计划",
        )

    # 如果有开发任务但没有测试角色，自动添加功能测试
    dev_roles = {"backend-dev", "frontend-dev", "data-engineer"}
    if dev_roles & set(matched.keys()) and "tester-functional" not in matched:
        matched["tester-functional"] = Role(
            name="tester-functional",
            subagent_type="tester-functional",
            description="功能测试 — 验证功能正确性",
        )

    return list(matched.values())


def suggest_subtasks(roles: list[Role], task_desc: str) -> list[SubTask]:
    """根据角色和任务描述生成子任务建议"""
    role_names = {r.name for r in roles}
    tasks: list[SubTask] = []
    idx = 0

    # Phase 1: 规划
    if "planner" in role_names:
        idx += 1
        tasks.append(SubTask(
            id=f"T-{idx}",
            name="需求分析与计划制定",
            role="planner",
            dependencies=[],
            inputs="需求文档路径",
            outputs="dev-plan.md, 项目基础框架",
            acceptance="计划文档生成，包含所有子任务清单",
            steps=[
                "读取需求文档",
                "分析技术栈和模块划分",
                "产出 dev-plan.md（任务清单）",
                "产出项目基础框架文件",
            ],
        ))

    # Phase 2: 执行层（根据角色动态生成）
    planner_dep = [f"T-{idx}"] if "planner" in role_names else []

    for role in roles:
        if role.name == "planner":
            continue
        idx += 1
        tasks.append(SubTask(
            id=f"T-{idx}",
            name=f"{role.description.split('—')[0].strip()}执行",
            role=role.name,
            dependencies=planner_dep.copy(),
            inputs="dev-plan.md 中的对应任务",
            outputs="对应产出物",
            acceptance="按验收标准判定 PASS/FAIL",
            steps=[
                "读取 dev-plan.md 中分配的任务",
                "按 api-design-guide 或技术规范执行",
                "写入产出文件",
                "自检并标记完成",
            ],
        ))

    return tasks


def main():
    if len(sys.argv) < 2:
        print("用法: python analyze-task.py <任务描述> [--json]")
        sys.exit(1)

    task_desc = " ".join(sys.argv[1:]) if "--json" not in sys.argv else " ".join([a for a in sys.argv[1:] if a != "--json"])
    output_json = "--json" in sys.argv

    roles = analyze_roles(task_desc)
    subtasks = suggest_subtasks(roles, task_desc)

    if output_json:
        result = {
            "task": task_desc,
            "roles": [{"name": r.name, "subagent_type": r.subagent_type, "description": r.description} for r in roles],
            "subtasks": [
                {
                    "id": t.id, "name": t.name, "role": t.role,
                    "dependencies": t.dependencies, "inputs": t.inputs,
                    "outputs": t.outputs, "acceptance": t.acceptance,
                    "steps": t.steps,
                }
                for t in subtasks
            ],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=== 角色分析 ===")
        for r in roles:
            print(f"  {r.name} ({r.subagent_type}): {r.description}")
        print()
        print("=== 子任务建议 ===")
        for t in subtasks:
            deps = f"依赖: {', '.join(t.dependencies)}" if t.dependencies else "无依赖"
            print(f"  {t.id} [{t.role}] {t.name} ({deps})")
            for i, s in enumerate(t.steps, 1):
                print(f"    {i}. {s}")
            print()


if __name__ == "__main__":
    main()
