# Nowcoder Parser 深度清洗逻辑设计

> **日期:** 2026-03-19
> **状态:** 已确认

## 1. 背景与目标

当前 `parser.py` 中的 `split_job_cards` 使用简单的正则表达式提取职位卡片，导致以下问题：

1. **噪音过载**: Markdown 包含大量图片链接（`![](url)`）、导航、页脚、登录表单等非职位信息
2. **LLM 报错**: `ERROR: Cannot read "image.png" (this model does not support image input)` — LLM 无法处理图片引用
3. **上下文缺失**: 原始正则 `(\[[\s\S]*?\]\(https://www\.nowcoder\.com/jobs/detail/.*?\))` 仅提取链接本身，丢失薪资、地点等关键上下文
4. **Token 浪费**: 大量无用数据增加了 LLM 输入 Token 消耗

## 2. 架构决策

### 数据流
```
原始 Markdown (Firecrawl 输出)
  ↓
clean_nowcoder_markdown()  — 全局清洗
  ↓
split_job_cards()          — 提取纯净职位卡片
  ↓
parse_card_with_llm()      — LLM 解析
  ↓
JobModel                   — 结构化输出
```

### 保留 Firecrawl 的理由
- **适配性**: 一套代码适配多平台，无需为每个平台编写和维护独立爬虫
- **稳定性**: Firecrawl 处理 JS 渲染，不受网站结构小变动影响
- **维护成本低**: 无需跟踪私有 API 的签名算法和 Header 校验

## 3. 函数设计

### 3.1 `clean_nowcoder_markdown(text: str) -> str`

**职责**: 全局清洗 Markdown，移除所有非文本噪音。

**清洗规则**:
| 规则 | 正则 | 替换 |
|------|------|------|
| 移除图片引用 | `!\[.*?\]\(.*?\)` | `""` |
| 移除 Markdown 链接语法 | `\[([^\]]*)\]\((https?://[^\)]+)\)` | `{text} {url}` |
| 移除反斜杠转义 | `\\` | `""` |
| 合并连续空行 | `\n{3,}` | `"\n\n"` |


### 3.2 `split_job_cards(markdown_text: str) -> list[str]`

**职责**: 从已清洗的 Markdown 中提取每个职位卡片。

**核心逻辑**:
1. 调用 `clean_nowcoder_markdown()` 全局清洗
2. 使用正则匹配每个 `jobs/detail/` 链接及其所在行
3. 提取链接所在行的**所有文本**（职位名、薪资、地点等）
4. 清理行内残留的 Markdown 痕迹

**输出格式**:
```
【留用实习】平台产品经理-AI平台 https://www.nowcoder.com/jobs/detail/438022?... 薪资面议 北京
```

### 3.3 保留 `parse_card_with_llm()` 不变

- 单一职责原则：清洗逻辑与 LLM 解析解耦
- `nodes.py` 中的调用链无需修改

## 4. 输出示例

### 输入（原始 Markdown，line 158-175）
```markdown
[【留用实习】平台产品经理-AI平台\

![](https://uploadfiles.nowcoder.com/files/20231123/6673852_1700737739113/hr%E9%99%90%E6%97%B6%E7%9B%B4%E6%8B%9B%E6%9C%802x.png)\

薪资面议\

![](https://uploadfiles.nowcoder.com/files/20231229/6673852_1703819294608/%E6%A0%87%E7%AD%BEicon%E5%85%BC%E9%A1%BE%E5%AD%A6%E4%B8%9A2x.png)兼顾学业\

![](https://uploadfiles.nowcoder.com/files/20240410/6673852_1712741084026/%E6%A0%87%E7%AD%BEiconhr2x.png)HR今日在线\

北京](https://www.nowcoder.com/jobs/detail/438022?deliverSource=1&pageSource=5001&channel=npJobTab&activityId=170&logid=5e63f71519268321d981358aadd5df25&fromSource=%E6%90%9C%E7%B4%A2)
```

### 输出（传入 LLM）
```
【留用实习】平台产品经理-AI平台 https://www.nowcoder.com/jobs/detail/438022?... 薪资面议 兼顾学业 HR今日在线 北京
```

## 5. 影响评估

### 文件变更
| 文件 | 操作 | 影响 |
|------|------|------|
| `src/agent/parser.py` | 新增 `clean_nowcoder_markdown()`，重构 `split_job_cards()` | 仅内部逻辑变更，无 API 变化 |
| `tests/test_parser.py` | 新增单元测试 | 覆盖清洗和分割逻辑 |

### 不受影响
- `src/agent/nodes.py` — 调用接口不变
- `src/agent/state.py` — 数据模型不变
- `src/agent/tools.py` — Firecrawl 调用不变

## 6. 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 正则无法匹配新的职位卡片格式 | 使用宽松的正则（`[\s\S]*?` 跨行匹配）并添加日志记录无法识别的卡片 |
| 清洗逻辑过度，丢失有用信息 | 单元测试覆盖所有已知的清洗规则，确保关键信息（薪资、地点）保留 |
| 牛客网页面结构变化 | 清洗逻辑基于文本特征而非固定结构，具有一定鲁棒性 |
