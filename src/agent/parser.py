from abc import ABC, abstractmethod
from src.agent.state import JobModel
import re
from loguru import logger


class BaseJobParser(ABC):
    """职位数据解析的抽象基类"""

    def clean_markdown(self, text: str) -> str:
        """去除 Markdown 中的图片链接和冗余空行，节省 Token"""
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"\n\s*\n", "\n", text)
        return text.strip()

    @abstractmethod
    def split_job_cards(self, markdown_text: str) -> list[str]:
        """将完整的 markdown 文本切分为独立的职位卡片列表"""
        pass

    @abstractmethod
    def parse_card_regex(self, card_text: str) -> JobModel:
        """从单个职位卡片的 markdown 文本中解析出结构化数据"""
        pass

    def is_ai_related_batch(self, cards: list[str], llm) -> list[bool]:
        """LLM一次判断所有卡片是否AI相关，返回yes/no列表"""
        if not cards:
            return []

        prompt = f"""判断以下每个职位是否是与 AI / 机器学习 / 大模型 / 数据智能 / 算法工程 相关。
输出格式：每行一个yes或no，不要其他内容。

{chr(10).join(f"{i + 1}. {card}" for i, card in enumerate(cards))}
"""
        response = llm.invoke(prompt)
        lines = [
            line.strip().lower()
            for line in response.content.strip().split("\n")
            if line.strip()
        ]

        results = []
        for line in lines:
            if "yes" in line or "是" in line or "y" in line or "1" in line:
                results.append(True)
            elif "no" in line or "否" in line or "n" in line or "0" in line:
                results.append(False)
            else:
                results.append(True)

        while len(results) < len(cards):
            results.append(True)

        return results[: len(cards)]


class NowcoderParser(BaseJobParser):
    """牛客网专用的数据解析器"""

    def split_job_cards(self, markdown_text: str) -> list[str]:
        cleaned_text = self.clean_markdown(markdown_text)

        if "推荐最新" in cleaned_text:
            cleaned_text = cleaned_text.split("推荐最新", 1)[1]

        pattern = r"\[[^\[\]]+\]\(https://www\.nowcoder\.com/(?:jobs/detail|enterprise)/[^\)]+\)"
        matches = re.finditer(pattern, cleaned_text, re.DOTALL)

        links = [m.group(0) for m in matches]

        cards = []
        i = 0
        while i < len(links):
            link = links[i]
            if "jobs/detail" in link:
                job_block = link
                ent_block = None
                if i + 1 < len(links) and "enterprise" in links[i + 1]:
                    ent_block = links[i + 1]
                    i += 2
                elif i - 1 >= 0 and "enterprise" in links[i - 1]:
                    ent_block = links[i - 1]
                    i += 1
                else:
                    i += 1

                if ent_block:
                    cards.append(job_block + "\n" + ent_block)
                else:
                    cards.append(job_block)
            else:
                i += 1

        return [c for c in cards if len(c) > 10]

    def parse_card_regex(self, card_text: str) -> JobModel:
        enterprise_match = re.search(
            r"\[([^\]]*)\]\((https://www\.nowcoder\.com/enterprise/[^)]+)\)", card_text
        )
        job_match = re.search(
            r"\[([^\]]*)\]\((https://www\.nowcoder\.com/jobs/detail/[^)]+)\)", card_text
        )

        if not enterprise_match or not job_match:
            return None

        company_block = enterprise_match.group(1)
        job_block = job_match.group(1)
        job_url = job_match.group(2)

        def clean_lines(block):
            lines = []
            for l in block.split("\n"):
                cl = l.replace("\\", "").strip()
                if cl:
                    lines.append(cl)
            return lines

        company_lines = clean_lines(company_block)
        job_lines = clean_lines(job_block)

        company = company_lines[0] if company_lines else ""
        title_raw = job_lines[0] if job_lines else ""
        title = title_raw
        salary = ""

        salary_match = re.search(
            r"(\d+-\d+K.*?|\d+-\d+元/天.*?|薪资面议.*?)(\·\d+薪)?$", title_raw
        )
        if salary_match:
            salary = salary_match.group(0)
            title = title_raw[: salary_match.start()].strip()

        location = ""
        requirements = ""
        for line in job_lines[1:]:
            if not salary and (
                "K" in line or "薪资" in line or "面议" in line or "元/天" in line
            ):
                salary = line
            elif (
                line in ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉"]
                or "北京/" in line
                or "/上海" in line
                or "全国" in line
            ):
                location = line
            elif any(
                k in line for k in ["本科", "硕士", "博士", "大专", "毕业", "不限"]
            ):
                requirements = line

        return JobModel(
            title=title,
            company=company,
            location=location,
            salary=salary,
            tech_tags=["AI"],
            requirements=requirements,
            source="牛客网",
            job_url=job_url,
        )


class YingjieshengParser(BaseJobParser):
    """应届生招聘网(yingjiesheng.com)专用的数据解析器"""

    def split_job_cards(self, markdown_text: str) -> list[str]:
        cleaned_text = self.clean_markdown(markdown_text)

        # 排除包含 k_ 的热搜链接，匹配真正的职位或公司链接，或者不以 k_ 开头的职位链接
        pattern = r"\[[^\[\]]+\]\(https?://(?:[a-zA-Z0-9-]+\.)?yingjiesheng\.com/(?:job|jobs|jobdetail)/(?!k_)[^\)]+\)"
        matches = re.finditer(pattern, cleaned_text, re.DOTALL)

        links = [m.group(0) for m in matches]
        cards = []

        for link in links:
            cards.append(link)

        if not cards:
            # Fallback
            raw_blocks = re.split(
                r"\n(?=\[?.*(?:工程师|研究员|AI|开发|模型).*\]?|\d+\.\s)", cleaned_text
            )
            cards = [
                b.strip()
                for b in raw_blocks
                if len(b.strip()) > 20
                and ("k" in b.lower() or "薪" in b or "公司" in b)
            ]

        return [c for c in cards if len(c) > 10]

    def parse_card_regex(self, card_text: str) -> JobModel:
        job_match = re.search(
            r"\[([^\]]+)\]\((https?://(?:[a-zA-Z0-9-]+\.)?yingjiesheng\.com/(?:job|jobs|jobdetail)/(?!k_)[^\)]+)\)",
            card_text,
        )

        title = "AI相关职位"
        company = "未知公司"
        job_url = "https://q.yingjiesheng.com/jobs/search/AI"
        salary = "薪资面议"
        location = "全国"
        requirements = "不限"

        if not job_match:
            title_match = re.search(r"^(.+?工程师|.+?开发|.*AI.*)", card_text, re.M)
            if title_match:
                title = title_match.group(1).strip()
        else:
            block_content = job_match.group(1)
            job_url = job_match.group(2)

            lines = [
                l.replace("\\", "").strip()
                for l in block_content.split("\n")
                if l.strip() and l.replace("\\", "").strip()
            ]

            if lines:
                title = lines[0]
            if len(lines) > 2:
                company = lines[2]
            elif len(lines) > 1:
                company = lines[1]

            salary_pattern = re.compile(
                r"(\d+(?:\.\d+)?-\d+(?:\.\d+)?(?:k|K|千|万)(?:/年|/月)?|\d+(?:k|K|千|万)(?:/年|/月)?|\d+-\d+(?:元|/月|/天)|\d+元/[天天月]|面议|.*?薪)",
                re.IGNORECASE,
            )
            for line in lines[3:]:
                if salary_pattern.search(line) and not "人" in line:
                    salary = line
                    break

            if len(lines) > 1:
                meta_line = lines[1]
                location_match = re.search(
                    r"^(.*?)(?:在校|应届|无需|\d+年|大专|本科|硕士|博士)", meta_line
                )
                if location_match and location_match.group(1).strip():
                    location = location_match.group(1).strip()
                elif len(meta_line) < 15:
                    location = meta_line

                req_match = re.search(
                    r"(本科|硕士|博士|大专|不限学历|应届生|在校生|无需经验|\d+年)",
                    meta_line,
                )
                if req_match:
                    requirements = req_match.group(1)

        search_text = block_content if 'block_content' in locals() else card_text
        
        # Fallback if properties not found via line parsing
        if salary == "薪资面议":
            salary_match = re.search(
                r"(\d+(?:\.\d+)?-\d+(?:\.\d+)?(?:k|K|千|万)(?:/年|/月)?|\d+(?:k|K|千|万)(?:/年|/月)?|\d+-\d+(?:元|/月|/天)|\d+元/[天天月]|面议)",
                search_text,
                re.IGNORECASE
            )
            if salary_match:
                salary = salary_match.group(1)

        if location == "全国":
            location_match = re.search(
                r"(北京|上海|广州|深圳|杭州|成都|武汉|南京|西安|苏州|天津|重庆)", search_text
            )
            if location_match:
                location = location_match.group(1)

        if requirements == "不限":
            req_match = re.search(
                r"(本科|硕士|博士|大专|不限学历|应届生|在校生)", search_text
            )
            if req_match:
                requirements = req_match.group(1)

        return JobModel(
            title=title,
            company=company,
            location=location,
            salary=salary,
            tech_tags=["AI"],
            requirements=requirements,
            source="应届生求职网",
            job_url=job_url,
        )


# Factory helper to get parser
def get_parser(platform: str) -> BaseJobParser:
    if platform.lower() == "yingjiesheng":
        return YingjieshengParser()
    return NowcoderParser()


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
