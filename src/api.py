import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from src.cache import SemanticCache
from src.llm import ask_llm

cache: SemanticCache | None = None


class QueryRequest(BaseModel):
    query: str
    use_live_llm: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global cache
    cache = SemanticCache(threshold=0.80, use_cloud=True)
    if cache.client.count(cache.collection_name).count == 0:
        with open("data/faqs.json", "r", encoding="utf-8") as f:
            for item in json.load(f):
                cache.store(item["question"], item["answer"], faq_id=item["id"])
    yield


app = FastAPI(title="Semantic FAQ Cache API", lifespan=lifespan)


@app.post("/ask")
def ask_question(req: QueryRequest):
    res = cache.lookup(req.query)
    if res["hit"]:
        return {
            "query": req.query,
            "answer": res["answer"],
            "cache_hit": True,
            "similarity": res["score"],
            "latency_ms": res["latency_ms"],
        }

    if req.use_live_llm:
        llm_res = ask_llm(req.query)
        answer = llm_res["answer"]
        latency_ms = round(res["latency_ms"] + llm_res["latency_ms"], 2)
    else:
        answer = "LLM fallback response (pass use_live_llm=true to call Gemini)."
        latency_ms = res["latency_ms"]

    return {
        "query": req.query,
        "answer": answer,
        "cache_hit": False,
        "reason": res.get("reason"),
        "similarity": res["score"],
        "latency_ms": latency_ms,
    }