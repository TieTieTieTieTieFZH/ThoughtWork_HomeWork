import pytest
from src.agent.parser import clean_nowcoder_markdown, split_job_cards

SAMPLE_RAW_MARKDOWN = """\
![](https://uploadfiles.nowcoder.com/images/20180815/59_1534321710941_41A541F87AE349E1D829B1B0B95C955D)

扫描二维码，进入QQ群

[求职首页](https://www.nowcoder.com/jobs/recommend/campus)

[【留用实习】平台产品经理-AI平台\\
薪资面议\\
北京](https://www.nowcoder.com/jobs/detail/438022?deliverSource=1)

[AI Agent 优化工程师薪资面议\\

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
        assert "![*" not in result
        assert "](http" not in result

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
