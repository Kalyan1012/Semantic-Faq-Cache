import os
import re
import time
import uuid
from dotenv import load_dotenv
from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models

load_dotenv()

NEGATION_WORDS = {"not", "no", "never", "n't", "nahi", "nahin", "mat", "na"}
PII_PATTERN = re.compile(
    r"(ORD-\d+|\b\d{10}\b|[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"
)


class SemanticCache:
    def __init__(
        self,
        threshold: float = 0.80,
        ttl_seconds: int = 86400,
        use_cloud: bool = True,
    ):
        self.threshold = threshold
        self.ttl_seconds = ttl_seconds
        self.collection_name = "faq_cache"
        self.embedder = TextEmbedding(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

        qdrant_url = os.getenv("QDRANT_URL") if use_cloud else None
        qdrant_api_key = os.getenv("QDRANT_API_KEY") if use_cloud else None

        if qdrant_url:
            self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            self.client = QdrantClient(":memory:")

        self._init_collection()

    def _init_collection(self):
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=384, distance=models.Distance.COSINE
                ),
            )

    def _embed(self, text: str) -> list[float]:
        return next(self.embedder.embed([text])).tolist()

    def _has_negation(self, text: str) -> bool:
        tokens = set(re.findall(r"\b\w+(?:'\w+)?\b", text.lower()))
        return bool(tokens & NEGATION_WORDS)

    def _contains_pii(self, text: str) -> bool:
        return bool(PII_PATTERN.search(text))

    def lookup(self, query: str) -> dict:
        start = time.perf_counter()
        vector = self._embed(query)
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=1,
        ).points

        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        if not results:
            return {
                "hit": False,
                "score": 0.0,
                "latency_ms": latency_ms,
                "reason": "empty_cache",
            }

        top = results[0]
        score = round(top.score, 4)
        payload = top.payload

        # 1. Threshold check
        if score < self.threshold:
            return {
                "hit": False,
                "score": score,
                "latency_ms": latency_ms,
                "reason": "below_threshold",
            }

        # 2. TTL check + lazy eviction from Qdrant
        if time.time() - payload["created_at"] > self.ttl_seconds:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=[top.id]),
            )
            return {
                "hit": False,
                "score": score,
                "latency_ms": latency_ms,
                "reason": "expired_ttl",
            }

        # 3. Negation guard
        if self._has_negation(query) != self._has_negation(payload["question"]):
            return {
                "hit": False,
                "score": score,
                "latency_ms": latency_ms,
                "reason": "negation_mismatch",
            }

        return {
            "hit": True,
            "score": score,
            "latency_ms": latency_ms,
            "matched_question": payload["question"],
            "answer": payload["answer"],
            "faq_id": payload.get("faq_id"),
        }

    def store(self, question: str, answer: str, faq_id: str | None = None) -> bool:
        # 4. PII / user-specific hygiene check
        if self._contains_pii(answer):
            return False

        vector = self._embed(question)
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "question": question,
                        "answer": answer,
                        "faq_id": faq_id,
                        "created_at": time.time(),
                    },
                )
            ],
        )
        return True