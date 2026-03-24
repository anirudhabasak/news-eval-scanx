from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class InflowType(str, Enum):
    LODR = "LODR"
    NEWS_STREAMER = "NEWS_STREAMER"


class PublicationType(str, Enum):
    FIRST_PUBLISH = "FIRST_PUBLISH"
    UPDATE = "UPDATE"


@dataclass
class Inflow:
    type: InflowType
    source_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Articles:
    claude: str
    artham: str


@dataclass
class ScoreWeights:
    information_retention: float = 60.0
    readability: float = 40.0

    def normalized(self) -> "ScoreWeights":
        total = self.information_retention + self.readability
        if total <= 0:
            return ScoreWeights()
        return ScoreWeights(
            information_retention=(self.information_retention / total) * 100.0,
            readability=(self.readability / total) * 100.0,
        )


@dataclass
class EvalRequest:
    request_id: str
    inflow: Inflow
    publication_type: PublicationType
    source_content: str
    articles: Articles
    weights: ScoreWeights = field(default_factory=ScoreWeights)
    additional_context: Optional[Dict[str, Any]] = None


def parse_eval_request(payload: Dict[str, Any]) -> EvalRequest:
    inflow = payload["inflow"]
    weights = payload.get("weights", {})
    return EvalRequest(
        request_id=payload["request_id"],
        inflow=Inflow(
            type=InflowType(inflow["type"]),
            source_name=inflow["source_name"],
            metadata=inflow.get("metadata", {}),
        ),
        publication_type=PublicationType(payload["publication_type"]),
        source_content=payload["source_content"],
        articles=Articles(
            claude=payload["articles"]["claude"],
            artham=payload["articles"]["artham"],
        ),
        weights=ScoreWeights(
            information_retention=float(
                weights.get("information_retention", 60.0)
            ),
            readability=float(weights.get("readability", 40.0)),
        ).normalized(),
        additional_context=payload.get("additional_context"),
    )
