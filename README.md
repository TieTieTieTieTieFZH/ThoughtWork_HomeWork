# AI Engineer 自动求职助手 Agent (MVP)

本项目是一个基于 **Agentic AI** 架构的自动求职系统原型。它利用 **LangGraph** 状态机模式，模拟了一个具备“自主规划与执行能力”的 AI Agent，能够自动搜索、筛选并整理 AI Engineer 校园招聘岗位信息。

## 🎯 核心功能

- **🧭 任务自主规划**：将“寻找 50 个岗位”的目标拆解为 `搜索 -> 抓取 -> 解析 -> 评估 -> 迭代` 的循环流程。
- **🔁 动态迭代搜索**：当收集到的岗位数量不足时，Agent 会自动调整搜索关键词（如从“AI Engineer”切换到“大模型算法实习生”）并继续执行。
- **🧠 语义化评估**：内置评估节点（支持扩展 LLM），用于判断岗位是否符合“AI 方向”及“校招/实习”要求。
- **📦 结构化输出**：自动去重并输出标准化的 `JSON` 岗位数据。
- **🧪 TDD 驱动开发**：核心逻辑均通过单元测试验证，确保 Agent 状态流转的稳定性。

## 🏗 技术架构 (LangGraph)

Agent 采用状态图（State Graph）构建，包含以下核心节点：
1. **Planner (规划者)**：生成并优化搜索 Query。
2. **Searcher (搜索者)**：模拟调用招聘网站搜索接口，获取岗位 URL。
3. **Scraper & Parser (抓取解析者)**：提取网页内容并结构化为岗位模型。
4. **Evaluator (评估者)**：判断岗位匹配度，决定是否存入结果集。
5. **Conditional Router (条件路由)**：检查是否达到 50 条目标或触发防死循环保护。

## 📁 项目结构

```text
├── src/
│   ├── agent/
│   │   ├── graph.py       # LangGraph 工作流定义
│   │   ├── nodes.py       # 业务逻辑节点实现
│   │   └── state.py       # Pydantic 模型与 TypedDict 状态定义
│   └── main.py            # 系统启动入口
├── tests/
│   └── agent/             # 针对 State, Nodes, Graph 的测试用例
├── docs/                  # 设计规范与实施计划文档
├── requirements.txt       # 项目依赖
└── jobs_output.json       # Agent 运行产出的岗位数据
```

## 🚀 快速开始

### 1. 环境准备
确保已安装 Python 3.10+。建议使用项目自带的虚拟环境：

```bash
# 激活环境 (Windows 示例)
.venv\Scripts\activate
# 安装依赖
pip install -r requirements.txt
```

### 2. 运行测试
验证 Agent 的核心逻辑：

```bash
python -m pytest tests/agent/
```

### 3. 执行 Agent
启动 Agent 开始自动化岗位采集（MVP 默认采集 5 条 mock 数据进行流程验证）：

```bash
python -m src.main
```
运行完成后，可在 `jobs_output.json` 中查看采集到的结构化岗位信息。

## ⭐ 关键 Agent 能力体现
- **防死循环机制**：设置 `iteration_count` 阈值，防止 Agent 在搜索无果时陷入无限循环。
- **状态持久化**：通过 `AgentState` 实时追踪已访问 URL 和已采集岗位，实现自动去重。
- **平台切换策略**：预留 `current_site_index` 逻辑，支持在多个招聘网站间自动切换。

---
*本项目为 AI Engineer 面试题 MVP 实现，旨在展示 Agentic 设计思路。*
