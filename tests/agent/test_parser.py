from src.agent.parser import split_job_cards
import os


def test_split_job_cards():
    # Read our sample snippet
    sample_path = os.path.join(
        os.path.dirname(__file__), "../samples/nowcoder_snippet.md"
    )
    with open(sample_path, "r", encoding="utf-8") as f:
        sample_md = f.read()

    cards = split_job_cards(sample_md)
    # The sample contains 2 jobs
    assert len(cards) == 2
    assert "字节跳动" in cards[0]
    assert "腾讯" in cards[1]
    assert "### [" in cards[0]
