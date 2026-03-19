from src.agent.state import JobModel, AgentState
import re


def clean_nowcoder_markdown(text: str) -> str:
    text = re.sub(r"\\", "", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\s*\((https?://[^\)]+)\)", r"\1 \2", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_job_cards(markdown_text: str) -> list[str]:
    cleaned = clean_nowcoder_markdown(markdown_text)
    lines = cleaned.split("\n")
    cards = []

    job_pattern = re.compile(r"(https://www\.nowcoder\.com/jobs/detail/\S+)")

    for i, line in enumerate(lines):
        if job_pattern.search(line):
            context_lines = []
            for j in range(max(0, i - 5), i + 1):
                if lines[j].strip() and not job_pattern.search(lines[j]):
                    context_lines.append(lines[j])

            context_lines.append(line)

            for j in range(i + 1, min(i + 4, len(lines))):
                if lines[j].strip() and not job_pattern.search(lines[j]):
                    context_lines.append(lines[j])
                else:
                    break

            card_text = " ".join(context_lines)
            card_text = re.sub(r"!\[.*?\]", "", card_text)
            card_text = re.sub(r"\s+", " ", card_text).strip()

            if card_text:
                cards.append(card_text)

    return cards


def parse_card_with_llm(card_text: str, llm) -> JobModel:
    """
    Simplified extraction without complex Pydantic parser for maximum compatibility.
    """
    prompt = f"""
    From the following job markdown, extract details into JSON format.
    Required fields: title, company, location, salary, tech_tags (list), requirements, source, job_url.
    Markdown: {card_text}
    JSON output:
    """
    from langchain_core.output_parsers import JsonOutputParser

    parser = JsonOutputParser(pydantic_object=JobModel)
    chain = llm | parser
    res = chain.invoke(prompt)
    return JobModel(**res)
