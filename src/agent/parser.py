from src.agent.state import JobModel, AgentState
import re


def clean_markdown(text: str) -> str:
    """去除 Markdown 中的图片链接和冗余空行，节省 Token"""
    # 移除图片: ![alt](url)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    # 移除多余的换行
    text = re.sub(r"\n\s*\n", "\n", text)
    return text.strip()


def split_job_cards(markdown_text: str) -> list[str]:
    # 1. 先进行初步清洗
    cleaned_text = clean_markdown(markdown_text)

    # 2. 移除"推荐最新"之前的内容
    if "推荐最新" in cleaned_text:
        cleaned_text = cleaned_text.split("推荐最新", 1)[1]

    # 3. 增强匹配模式
    # 由于不同爬取方式/页面结构下，公司块和职位块的顺序可能不同，甚至有时是空格分隔而不是换行。
    # 我们先匹配所有的独立链接块，然后再将相邻的 "job_detail" 和 "enterprise" 块成对组合。
    import re

    pattern = r"\[.*?\]\(https://www\.nowcoder\.com/(?:jobs/detail|enterprise)/[^\)]+\)"
    matches = re.finditer(pattern, cleaned_text, re.DOTALL)

    links = [m.group(0) for m in matches]

    cards = []
    i = 0
    while i < len(links):
        link = links[i]
        # 当遇到一个 job 块
        if "jobs/detail" in link:
            job_block = link
            ent_block = None
            # 向前或向后找紧邻的 enterprise 块
            if i + 1 < len(links) and "enterprise" in links[i + 1]:
                ent_block = links[i + 1]
                i += 2
            elif i - 1 >= 0 and "enterprise" in links[i - 1]:
                # 如果前一个是 enterprise
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

    # 过滤掉过短的无效匹配
    return [c for c in cards if len(c) > 10]


def is_ai_related_batch(cards: list[str], llm) -> list[bool]:
    """LLM一次判断所有卡片是否AI相关，返回yes/no列表"""
    prompt = f"""判断以下每个职位是否是AI相关工程师(AI Engineer)。
输出格式：每行一个yes或no，不要其他内容。

{chr(10).join(f"{i + 1}. {card}" for i, card in enumerate(cards))}
"""
    response = llm.invoke(prompt)
    lines = [
        line.strip().lower()
        for line in response.content.strip().split("\n")
        if line.strip()
    ]

    # 增加鲁棒性，处理大模型可能附带的前缀如 "1. yes"
    results = []
    for line in lines:
        if "yes" in line or "是" in line or "y" in line or "1" in line:
            results.append(True)
        elif "no" in line or "否" in line or "n" in line or "0" in line:
            results.append(False)
        else:
            # 默认返回 True 避免漏掉
            results.append(True)

    # TODO 异常情况应该让模型重试+提示词“岗位判断数不足，请重新分析”
    while len(results) < len(cards):
        results.append(True)

    return results[: len(cards)]


def parse_card_regex(card_text: str) -> JobModel:
    """用正则解析固定格式的职位信息"""
    import re

    # 提取两个链接块: [公司信息](enterprise/xxx) 和 [职位信息](jobs/detail/xxx)
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

    # 职位名称和薪资可能会粘在一行
    title_raw = job_lines[0] if job_lines else ""
    title = title_raw
    salary = ""

    # 尝试从title中分离出薪资
    # 常见薪资格式: 15-25K·14薪, 15-25K, 500-1000元/天, 薪资面议
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
            line
            in [
                "北京",
                "上海",
                "广州",
                "深圳",
                "杭州",
                "成都",
                "武汉",
                "长沙",
                "西安",
                "南京",
                "苏州",
                "天津",
                "重庆",
                "东莞",
                "宁波",
                "青岛",
                "无锡",
                "济南",
                "石家庄",
                "郑州",
                "合肥",
                "南昌",
                "福州",
                "厦门",
                "沈阳",
                "大连",
                "哈尔滨",
                "长春",
                "昆明",
                "贵阳",
                "全国",
                "海外",
                "其他",
                "珠海",
                "佛山",
                "中山",
                "惠州",
                "绍兴",
                "常州",
                "大厂",
                "保定",
                "徐州",
                "南宁",
                "大同",
                "唐山",
                "洛阳",
            ]
            or "北京/" in line
            or "/上海" in line
            or "/" in line
            and any(
                city in line
                for city in ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉"]
            )
        ):
            location = line
        elif (
            "本科" in line
            or "硕士" in line
            or "大专" in line
            or "毕业" in line
            or "不限" in line
            or "博士" in line
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
