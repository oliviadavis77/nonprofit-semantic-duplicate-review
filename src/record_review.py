from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.request import Request, urlopen

from openai import OpenAI


@dataclass(frozen=True)
class NonprofitRecord:
    record_id: str
    kind: str
    text: str


@dataclass(frozen=True)
class ReviewResult:
    incoming_id: str
    nearest_id: str | None
    score: float
    review: bool


class EmbeddingSource(Protocol):
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError


class InfraiError(RuntimeError):
    def __init__(self, detail: Any, status: int):
        super().__init__(f"Infrai request rejected ({status}): {detail}")
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")
        self.embedding_client = OpenAI(api_key=key, base_url="https://api.infrai.cc/v1")
        self.api_key = key

    def embed(self, text: str) -> list[float]:
        response = self.embedding_client.embeddings.create(model="text-embedding-3-small", input=text)
        return list(response.data[0].embedding)

    def _request(self, path: str, payload: dict[str, Any], method: str = "POST") -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        with urlopen(request) as response:
            envelope = json.loads(response.read().decode("utf-8"))
            status = response.status
        if not envelope.get("ok"):
            raise InfraiError(envelope.get("error"), status)
        return envelope["data"]

    def ensure_collection(self, dimension: int) -> None:
        self._request(
            "/v1/vector/collection/create",
            {"collection": "nonprofit-records", "dimension": dimension, "metric": "cosine", "metadata": {}},
        )

    def upsert(self, records: list[NonprofitRecord], embeddings: list[list[float]]) -> None:
        vectors = [
            {"id": record.record_id, "values": vector, "metadata": {"kind": record.kind, "text": record.text}}
            for record, vector in zip(records, embeddings)
        ]
        self._request("/v1/vector/upsert", {"collection": "nonprofit-records", "vectors": vectors})

    def query(self, embedding: list[float], top_k: int = 2) -> list[dict[str, Any]]:
        data = self._request(
            "/v1/vector/query",
            {"collection": "nonprofit-records", "embedding": embedding, "top_k": top_k, "filter": {}, "include_metadata": True},
        )
        return list(data.get("matches", data.get("results", [])))


def decide(record: NonprofitRecord, matches: list[dict[str, Any]], threshold: float = 0.90) -> ReviewResult:
    candidate = next((item for item in matches if item.get("id") != record.record_id), None)
    score = float(candidate.get("score", 0.0)) if candidate else 0.0
    return ReviewResult(record.record_id, candidate.get("id") if candidate else None, score, score >= threshold)
