import re
from typing import Dict, List


TABLE_PATTERNS = [
    r"\|.+\|",  # markdown table row
    r"<table[\s>]",  # html table
    r"\btabular\b",  # textual hint
]

CHINESE_CHAR_PATTERN = re.compile(r"[\u4e00-\u9fff]")
NON_INR_CURRENCY_PATTERN = re.compile(
    r"(?:(?<![A-Za-z])(USD|EUR|GBP|JPY|CNY|RMB|AUD|CAD|SGD)(?![A-Za-z]))|[$€£¥]"
)


def has_tables(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in TABLE_PATTERNS)


def has_chinese_characters(text: str) -> bool:
    return bool(CHINESE_CHAR_PATTERN.search(text))


def has_non_inr_currency_symbols(text: str) -> bool:
    if "₹" in text:
        # INR symbol alone is not a non-INR flag.
        text = text.replace("₹", "")
    return bool(NON_INR_CURRENCY_PATTERN.search(text))


def extract_number_unit_pairs(text: str) -> List[Dict[str, str]]:
    # Captures cases like: 100 million, 5.5 billion, 10 crore, 25 lakh.
    pattern = re.compile(
        r"\b(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>million|billion|crore|lakh)\b",
        flags=re.IGNORECASE,
    )
    pairs = []
    for m in pattern.finditer(text):
        pairs.append(
            {
                "value": m.group("value"),
                "unit": m.group("unit").lower(),
                "match": m.group(0),
            }
        )
    return pairs


def conversion_mismatch_flags(source_text: str, article_text: str) -> List[str]:
    source_pairs = extract_number_unit_pairs(source_text)
    article_pairs = extract_number_unit_pairs(article_text)
    if not source_pairs or not article_pairs:
        return []

    source_units = {p["unit"] for p in source_pairs}
    article_units = {p["unit"] for p in article_pairs}

    flags: List[str] = []
    if ("million" in source_units or "billion" in source_units) and (
        "crore" in article_units or "lakh" in article_units
    ):
        flags.append(
            "Source has million/billion while article uses lakh/crore; verify conversions."
        )
    if ("crore" in source_units or "lakh" in source_units) and (
        "million" in article_units or "billion" in article_units
    ):
        flags.append(
            "Source has lakh/crore while article uses million/billion; verify conversions."
        )
    return flags
