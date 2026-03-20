# AI Engineer 自动求职助手 Agent

本项目是一个基于 **Agentic AI** 架构的自动求职系统。它利用 **LangGraph** 状态机模式，构建了一个具备“自主规划与工具调用能力”的 AI Agent，能够自动搜索、抓取、筛选并整理 AI Engineer（校招/实习）岗位信息。

## 🎯 核心功能与 Agent 能力

- **🧭 自主任务规划 (Tool Calling)**：抛弃硬编码查询，Agent 根据当前收集进度和历史记录，利用 LLM（大语言模型）**自主推理**并生成最适合的下一步搜索关键词（如 "AI", "NLP", "CV"），并通过 Tool Calling 触发搜索。
- **🌐 双平台工具调用与抓取 (Firecrawl)**：Agent 能够自主调用底层爬虫工具，轮流访问 **Nowcoder（牛客网）** 和 **Yingjiesheng（应届生求职网）**，并利用 `only_main_content=True` 将招聘列表页高效、精准地结构化为 Markdown。
- **🧠 混合解析与语义评估**：
  - **Batch LLM 语义判断**：使用 LLM 批量判定抓取到的岗位是否真实符合“AI Engineer”与“校招/实习”方向，大幅提高判断准确率与效率。
  - **精准 Markdown 正则提取**：摒弃了昂贵且缓慢的 Firecrawl 原生 JSON 提取，采用极致优化的本地正则表达式处理干净的 Markdown 卡片流，快速、低成本地提取公司、薪资、地点、要求等结构化字段，避免复杂的 HTML/URL 脏数据干扰。
- **🔁 自动迭代与补足**：当收集到的岗位不足 50 条时，Agent 状态机会自动循环回规划节点，生成新的不重复短词继续在多平台间搜索，直到达成目标。
- **🧹 智能去重**：通过 `AgentState` 实时追踪已访问的 `job_url`，避免不同关键词搜出重复岗位。

## 🏗 技术架构 (LangGraph)

系统基于 **LangGraph** 状态图（State Graph）构建，包含以下核心节点：

1. **`plan_search` (规划者)**：核心思考节点。利用 `llm.bind_tools` 赋予 Agent 思考能力。Agent 分析过往 Query，结合自身 Prompt（强制生成 2-4 字极短硬核技术词，避免平台搜索拦截），决定下一个最优 Query。
2. **`search_jobs` (执行搜索)**：接收规划节点的 Query，在 Nowcoder 和 Yingjiesheng 之间交替调用 `Firecrawl` 工具执行网页抓取，并快速转换为纯净的 Markdown 文本。
3. **`scrape_and_parse` (解析与过滤)**：
   - 使用针对不同平台定制的 `BaseJobParser` 子类（`NowcoderParser`, `YingjieshengParser`）拆分 Markdown 卡片。
   - LLM 批量语义评估 (True/False)。
   - Regex 逐行精准提取详细信息，避免贪婪匹配。
   - URL 校验去重，存入结果集。
4. **`should_continue` (条件路由)**：判断 `len(collected_jobs) >= 50` 或是否达到最大安全迭代次数（`iteration_count >= 10`），决定是 `END` 还是循环回 `plan_search`。

## 📁 项目结构

```text
├── src/
│   ├── agent/
│   │   ├── graph.py       # LangGraph 状态机与工作流路由定义
│   │   ├── nodes.py       # 业务逻辑节点 (Planner, Searcher, Parser)
│   │   ├── parser.py      # Regex提取、LLM Batch判断与双平台卡片切割逻辑
│   │   ├── state.py       # 状态字典 (AgentState) 与 Pydantic 数据模型
│   │   └── tools.py       # Firecrawl 爬虫工具封装
│   └── main.py            # 系统启动入口 (Agent Invoke)
├── tests/                 # 单元测试 (基于 pytest)
├── requirements.txt       # 项目依赖
├── .env.example           # 环境变量配置参考 (Firecrawl / LLM Keys)
└── jobs_output.json       # Agent 最终输出的高质量、去重结构化数据
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

配置 `.env` 文件，填入你的 API Keys：
```env
FIRECRAWL_API_KEY=your_firecrawl_api_key
VOLC_API_KEY=your_volcengine_api_key
VOLC_MODEL=ep-xxx
VOLC_API_BASE=https://ark.cn-beijing.volces.com/api/v3
```

### 2. 执行 Agent
启动 Agent 开始自动化多平台岗位采集（目标收集 50 条符合条件的 AI 岗位）：

```bash
set PYTHONPATH=.
python -m src.main
```
运行完成后，可在 `jobs_output.json` 中查看采集到的高质量、结构化、无重复岗位信息。

## 🌟 设计亮点总结
- **解决了大模型 JSON 提取慢且贵的问题**：采用 `Firecrawl Markdown` + `LLM 仅做 Yes/No 判断` + `本地严谨 Regex 做结构化提取` 的混合架构，解析速度提升高达 ~28 倍，成本极大降低。
- **多平台智能适配**：引入策略模式 (`BaseJobParser`)，一套 Agentic 流程可无缝兼容牛客网和应届生求职网的不同 Markdown 渲染格式。
- **解决了复杂对话 Query 导致搜索失败的问题**：通过系统 Prompt 约束 Agent 自主剥离冗余修饰词（如“实习”、“校招”），只输出 "NLP"、"CV" 等硬核短词，完美适配传统招聘网站的搜索引擎。
- **真正的 Agentic 循环**：不依赖死循环硬编码，由大语言模型自己分析历史状态，自己决定下一步动作。
