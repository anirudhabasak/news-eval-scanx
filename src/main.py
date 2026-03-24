import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from src.models import parse_eval_request
from src.scoring import compare_scores, score_article


def run_eval(payload: Dict[str, Any]) -> Dict[str, Any]:
    request = parse_eval_request(payload)

    claude_result = score_article(request, request.articles.claude, "claude")
    artham_result = score_article(request, request.articles.artham, "artham")
    comparison = compare_scores(claude_result, artham_result)

    return {
        "request_id": request.request_id,
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "context": {
            "inflow": {
                "type": request.inflow.type.value,
                "source_name": request.inflow.source_name,
                "metadata": request.inflow.metadata,
            },
            "publication_type": request.publication_type.value,
        },
        "weights_applied": {
            "information_retention": request.weights.information_retention,
            "readability": request.weights.readability,
        },
        "scores": {
            "claude": claude_result,
            "artham": artham_result,
        },
        "comparison": comparison,
        "metadata_flags": {
            "source_content_present": bool(request.source_content.strip()),
            "additional_context_present": bool(request.additional_context),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate two generated news articles against source content."
    )
    parser.add_argument("--input", required=True, help="Path to input JSON file.")
    parser.add_argument("--output", required=True, help="Path to output JSON file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    result = run_eval(payload)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Evaluation complete. Output written to {output_path}")


if __name__ == "__main__":
    main()
