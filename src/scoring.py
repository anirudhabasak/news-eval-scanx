import json
import os
import re
from typing import Dict, Tuple

from dotenv import load_dotenv
from openai import OpenAI

from src.detectors import (
    conversion_mismatch_flags,
    has_chinese_characters,
    has_non_inr_currency_symbols,
    has_tables,
)
from src.models import EvalRequest


load_dotenv()


def _clip_score(value: float) -> float:
    return max(0.0, min(100.0, round(value, 2)))


def _simple_readability_score(text: str) -> float:
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    words = re.findall(r"\b\w+\b", text)
    if not words or not sentences:
        return 0.0
    avg_words_per_sentence = len(words) / len(sentences)
    long_word_ratio = len([w for w in words if len(w) > 10]) / max(len(words), 1)

    # Heuristic: fewer very long words and moderate sentence length increases readability.
    base = 100.0
    base -= abs(avg_words_per_sentence - 18) * 2.2
    base -= long_word_ratio * 60.0
    return _clip_score(base)


def _simple_information_retention_score(source: str, article: str) -> float:
    source_tokens = set(re.findall(r"\b[a-zA-Z]{4,}\b", source.lower()))
    article_tokens = set(re.findall(r"\b[a-zA-Z]{4,}\b", article.lower()))
    if not source_tokens:
        return 0.0
    overlap = len(source_tokens.intersection(article_tokens)) / len(source_tokens)
    return _clip_score(overlap * 100.0)


def _openai_score(source: str, article: str) -> Tuple[float, float]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")

    client = OpenAI(api_key=api_key)
    prompt = f"""
You are evaluating a generated financial news article.
Return ONLY JSON object with keys:
- information_retention_score (0-100 float)
- readability_score (0-100 float)

Evaluation criteria:
1) Information retention: how accurately and completely the article reflects source content.
2) Readability: clarity, flow, and ease of understanding for business readers.

SOURCE CONTENT:
\"\"\"{source}\"\"\"

ARTICLE:
\"\"\"{article}\"\"\"
"""
    response = client.responses.create(
        model=model,
        input=prompt,
        temperature=0,
    )
    text = response.output_text.strip()
    data = json.loads(text)
    return (
        _clip_score(float(data["information_retention_score"])),
        _clip_score(float(data["readability_score"])),
    )


def score_article(
    request: EvalRequest, article_text: str, article_label: str
) -> Dict[str, object]:
    try:
        information_retention, readability = _openai_score(
            request.source_content, article_text
        )
        scoring_source = "openai"
    except Exception:
        information_retention = _simple_information_retention_score(
            request.source_content, article_text
        )
        readability = _simple_readability_score(article_text)
        scoring_source = "heuristic_fallback"

    w = request.weights
    total_score = (
        information_retention * (w.information_retention / 100.0)
        + readability * (w.readability / 100.0)
    )
    total_score = _clip_score(total_score)

    conversion_flags = conversion_mismatch_flags(request.source_content, article_text)

    return {
        "article_label": article_label,
        "total_score": total_score,
        "subscores": {
            "information_retention": information_retention,
            "readability": readability,
        },
        "flags": {
            "has_tables": has_tables(article_text),
            "has_chinese_characters": has_chinese_characters(article_text),
            "has_non_inr_currency_symbols": has_non_inr_currency_symbols(article_text),
            "conversion_mismatch_flags": conversion_flags,
        },
        "scoring_source": scoring_source,
    }


def compare_scores(claude_score: Dict[str, object], artham_score: Dict[str, object]) -> Dict[str, object]:
    c = float(claude_score["total_score"])
    a = float(artham_score["total_score"])
    if c > a:
        winner = "claude"
    elif a > c:
        winner = "artham"
    else:
        winner = "tie"
    return {"winner": winner, "score_delta": round(abs(c - a), 2)}
