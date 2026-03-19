# Nowcoder Parser 深度清洗逻辑实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `parser.py` 中新增 `clean_nowcoder_markdown()` 函数并重构 `split_job_cards()`，实现 Markdown 深度清洗和纯净职位卡片提取，消除 LLM 图片引用报错并减少 Token 消耗。

**Architecture:** 采用两步清洗策略：1) 全局清洗移除噪音；2) 逐行提取职位卡片并保留上下文信息。保持与 `nodes.py` 的调用接口不变。

**Tech Stack:** Python, re (正则表达式), pytest

---

## Chunk 1: 环境准备与基线测试

**Files:**
- Modify: `src/agent/parser.py`
- Create: `tests/test_parser.py`

- [ ] **Step 1: 创建测试文件**

```python
# tests/test_parser.py
import pytest
from src.agent.parser import clean_nowcoder_markdown, split_job_cards

SAMPLE_RAW_MARKDOWN = """\
![](https://uploadfiles.nowcoder.com/images/20180815/59_1534321710941_41A541F87AE349E1D829B1B0B95C955D)

扫描二维码，进入QQ群

[求职首页](https://www.nowcoder.com/jobs/recommend/campus)

【留用实习】平台产品经理-AI平台\

薪资面议\

北京](https://www.nowcoder.com/jobs/detail/438022?deliverSource=1)

[AI Agent 优化工程师薪资面议\

杭州](https://www.nowcoder.com/jobs/detail/438175)
"""

class TestCleanNowcoderMarkdown:
    def test_removes_image_links(self):
        text = "![logo](https://example.com/logo.png) Hello"
        result = clean_nowcoder_markdown(text)
        assert "![logo]" not in result
        assert "Hello" in result

    def test_removes_markdown_link_syntax(self):
        text = "[首页](https://www.nowcoder.com/jobs/recommend/campus)"
        result = clean_nowcoder_markdown(text)
        assert "[" not in result or "](http" not in result

    def test_removes_backslash_escapes(self):
        text = "职位名\\"
        result = clean_nowcoder_markdown(text)
        assert "\\" not in result

    def test_merges_consecutive_blank_lines(self):
        text = "Line1\n\n\nLine2"
        result = clean_nowcoder_markdown(text)
        assert result.count("\n\n") <= 1


class TestSplitJobCards:
    def test_extracts_job_links_with_context(self):
        cards = split_job_cards(SAMPLE_RAW_MARKDOWN)
        assert len(cards) == 2
        for card in cards:
            assert "jobs/detail" in card

    def test_card_format_has_no_markdown_syntax(self):
        cards = split_job_cards(SAMPLE_RAW_MARKDOWN)
        for card in cards:
            assert "![*" not in card
            assert "](" not in card

    def test_card_preserves_title_and_url(self):
        cards = split_job_cards(SAMPLE_RAW_MARKDOWN)
        assert any("平台产品经理" in card for card in cards)
        assert any("438022" in card for card in cards)

    def test_empty_input_returns_empty_list(self):
        cards = split_job_cards("")
        assert cards == []
```

- [ ] **Step 2: 运行测试验证当前失败**

Run: `D:/Complie/Python/ThoughtWork/.venv/Scripts/python.exe -m pytest tests/test_parser.py -v`
Expected: FAIL — `clean_nowcoder_markdown` not defined, `split_job_cards` behavior differs

---

## Chunk 2: 实现全局清洗函数

**Files:**
- Modify: `src/agent/parser.py`

- [ ] **Step 1: 实现 `clean_nowcoder_markdown()`**

在 `parser.py` 顶部新增函数（放在 `split_job_cards` 之前）：

```python
def clean_nowcoder_markdown(text: str) -> str:
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[([^\]]*)\]\((https?://[^\)]+)\)', r'\1 \2', text)
    text = re.sub(r'\\', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
```

- [ ] **Step 2: 运行清洗测试验证**

Run: `D:/Complie/Python/ThoughtWork/.venv/Scripts/python.exe -m pytest tests/test_parser.py::TestCleanNowcoderMarkdown -v`
Expected: PASS — 所有清洗测试通过

---

## Chunk 3: 重构 split_job_cards 函数

**Files:**
- Modify: `src/agent/parser.py`

- [ ] **Step 1: 重构 `split_job_cards()` 函数**

将现有函数替换为新实现：

```python
def split_job_cards(markdown_text: str) -> list[str]:
    cleaned = clean_nowcoder_markdown(markdown_text)
    lines = cleaned.split('\n')
    cards = []
    
    job_pattern = re.compile(r'(https://www\.nowcoder\.com/jobs/detail/\S+)')
    
    for line in lines:
        if job_pattern.search(line):
            clean_line = re.sub(r'!\[.*?\]', '', line)
            clean_line = re.sub(r'\s+', ' ', clean_line).strip()
            if clean_line:
                cards.append(clean_line)
    
    return cards
```

- [ ] **Step 2: 运行所有测试验证**

Run: `D:/Complie/Python/ThoughtWork/.venv/Scripts/python.exe -m pytest tests/test_parser.py -v`
Expected: PASS — 所有测试通过

- [ ] **Step 3: 运行完整端到端测试（使用真实数据）**

Run: `D:/Complie/Python/ThoughtWork/.venv/Scripts/python.exe tests/reproduce_issue.py`
Expected: 输出显示职位卡片为纯文本格式，无 Markdown 语法

---

## Chunk 4: 集成验证与提交

**Files:**
- Modify: `src/agent/parser.py`
- Modify: `tests/test_parser.py`

- [ ] **Step 1: 使用真实 Markdown 数据测试**

在 `tests/test_parser.py` 中新增测试使用 `scraping_test_output.md` 的部分数据：

```python
def test_with_real_data():
    with open("scraping_test_output.md", "r", encoding="utf-8") as f:
        real_md = f.read()
    cards = split_job_cards(real_md)
    assert len(cards) > 0
    for card in cards:
        assert "jobs/detail" in card
        assert "![*" not in card
```

- [ ] **Step 2: 运行真实数据测试**

Run: `D:/Complie/Python/ThoughtWork/.venv/Scripts/python.exe -m pytest tests/test_parser.py::test_with_real_data -v`

- [ ] **Step 3: 提交代码**

```bash
git add src/agent/parser.py tests/test_parser.py docs/superpowers/specs/2026-03-19-nowcoder-parser-cleanup-design.md
git commit -m "feat: add deep-cleaning logic for Nowcoder markdown parsing

- Add clean_nowcoder_markdown() to remove images, link syntax, escapes
- Refactor split_job_cards() to extract pure-text job cards
- Fix LLM image input error by stripping all image references
- Reduce token overhead by removing noise (nav, footer, login form)
- Add comprehensive unit tests for both functions"
```

---

## 验证清单

- [ ] `clean_nowcoder_markdown` 测试全部通过
- [ ] `split_job_cards` 测试全部通过
- [ ] 真实数据测试通过（`scraping_test_output.md`）
- [ ] 端到端测试脚本输出纯文本卡片
- [ ] `nodes.py` 无需修改即可正常工作
- [ ] 无 Markdown 语法残留（无 `![`, `](`, `\`）
- [ ] 职位链接完整保留（`jobs/detail/`）
- [ ] 上下文信息（薪资、地点）完整保留
