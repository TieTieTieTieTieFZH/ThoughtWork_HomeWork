# 异步岗位详情丰富化设计文档 (Async Job Enrichment Design)

## 1. 目标 (Goal)
现有的 LangGraph 已经能够成功且精准地识别并收集 50 个 AI 相关的岗位信息（包含 Title, Company, Location, Salary, URL）。
本设计旨在引入一个**独立于主抓取循环**的后续流程，利用 Firecrawl 拉取每个岗位的详情页 Markdown，并调用 LLM 生成 `tech_tags`（技术关键词，如 LLM / CV / NLP / 推荐系统）和 `requirements`（岗位核心技能摘要）。

为了保证抓取效率不被降低，这个“丰富化”过程（Enrichment）将被**分离出主 LangGraph 循环**，在 50 个基础岗位全部收集完毕后，作为后置步骤批量/异步执行。

## 2. 架构设计 (Architecture)

### 2.1 从 LangGraph 中分离
由于已经在 `scrape_and_parse` 阶段利用主页的简要信息进行了是否为“AI岗位”的过滤，所以**没有必要**将详情页的获取放在循环内阻塞下一页的抓取。
我们将保留现有的 `build_graph` 不变，并在 `main.py` 中拿到 LangGraph 最终输出的 50 个 `collected_jobs` 状态后，再执行一个独立的批量丰富化流程。

### 2.2 批量与异步策略 (Batching & Async)
为避免 Firecrawl 的速率限制 (Rate Limits) 并减少 LLM 的调用次数，我们将采用以下分批策略：
1. **分批分组**：将 50 个岗位按 10 个一组进行切割（共 5 组）。
2. **并发爬取**：对于每组的 10 个 URL，使用 `asyncio.gather` 或 `ThreadPoolExecutor` 并发调用 Firecrawl 获取 Markdown 详情。
3. **合并 Prompt**：将这 10 个 Markdown 内容拼接为一个长 Prompt，要求模型对这 10 个岗位分别提取 `tech_tags` 和 `requirements`。
4. **结构化输出**：LLM 必须返回包含 10 个元素的对象数组，从而精准映射回原岗位列表。

## 3. 组件细节 (Component Details)

### 3.1 状态模型更新 (`src/agent/state.py`)
现有的 `JobModel` 已经预留了 `tech_tags` 和 `requirements` 字段（默认为空列表和空字符串）。无需大规模修改，但需确保解析出的内容能写回这些字段。

### 3.2 详情抓取工具 (`src/agent/tools.py`)
新增一个函数，用于获取单个详情页：
```python
def fetch_job_detail(url: str) -> str:
    """使用 Firecrawl 获取详情页 Markdown"""
    # 错误处理和重试机制，防止某一个页面失败导致整批挂掉
```

### 3.3 批量解析器 (`src/agent/parser.py`)
新增 `batch_enrich_jobs(jobs: List[JobModel]) -> List[JobModel]` 函数：
- **输入**：包含 10 个基础岗位的列表。
- **操作**：
  1. 并发获取 10 个 URL 的 Markdown。
  2. 构造 Prompt，包含这 10 个 Markdown 文本，提示词明确要求提取 `tech_tags` (如 LLM, CV, NLP 等) 和 `requirements` (简短的核心技能摘要)。
  3. 通过 `bind_tools` 或 `with_structured_output` 强制 LLM 返回包含 10 个对象的列表。
- **输出**：填充了 `tech_tags` 和 `requirements` 的岗位列表。

### 3.4 调度入口 (`src/main.py`)
```python
# 现有的 Graph 执行逻辑
final_state = graph.invoke(...)

# 新增的后处理逻辑
jobs = final_state["collected_jobs"]
enriched_jobs = []

# 按批次处理 (Chunking)
batch_size = 10
for i in range(0, len(jobs), batch_size):
    batch = jobs[i:i + batch_size]
    enriched_batch = parser.batch_enrich_jobs(batch)
    enriched_jobs.extend(enriched_batch)

# 最终保存到 jobs_output.json
save_to_json(enriched_jobs)
```

## 4. 容错与限制 (Error Handling & Limits)
- **Firecrawl 失败**：如果某个 URL 获取失败，该岗位的 `requirements` 填入 "暂无详情"，不应抛出异常阻断整个批次。
- **LLM 提取错位**：如果 LLM 返回的数量不等于 10，使用 URL 或 Title 进行键值对齐（Key-Value mapping），而不是单纯依赖列表顺序。
