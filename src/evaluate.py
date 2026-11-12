import csv
import json
import time
from pathlib import Path
from src.cache import SemanticCache
from src.llm import ask_llm

THRESHOLDS = [0.65, 0.70, 0.75, 0.80, 0.85]


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_sweep(use_live_llm: bool = False):
    faqs = load_json("data/faqs.json")
    faq_map = {item["id"]: item["answer"] for item in faqs}
    test_set = load_json("data/test_set.json")
    Path("results").mkdir(exist_ok=True)

    summary_rows = []
    all_logs = []

    for thresh in THRESHOLDS:
        cache = SemanticCache(threshold=thresh)

        # Pre-warm cache with the 30 canonical FAQs
        for item in faqs:
            cache.store(item["question"], item["answer"], faq_id=item["id"])

        hits = 0
        false_hits = 0
        negation_catches = 0
        total_latency_ms = 0.0
        llm_calls = 0

        for sample in test_set:
            query = sample["query"]
            expected_id = sample["expected_faq_id"]

            res = cache.lookup(query)

            if res["hit"]:
                hits += 1
                is_false_hit = res["faq_id"] != expected_id
                if is_false_hit:
                    false_hits += 1
                latency = res["latency_ms"]
                tokens = 0
            else:
                is_false_hit = False
                if res.get("reason") == "negation_mismatch":
                    negation_catches += 1
                llm_calls += 1

                if use_live_llm:
                    llm_res = ask_llm(query)
                    answer = llm_res["answer"]
                    latency = res["latency_ms"] + llm_res["latency_ms"]
                    tokens = llm_res["input_tokens"] + llm_res["output_tokens"]
                    time.sleep(1.5)
                else:
                    answer = faq_map.get(expected_id, "Out-of-scope support response.")
                    latency = res["latency_ms"] + 650.0
                    tokens = 140

                # Production behavior: cache valid domain answers for future repeat queries
                if expected_id != "none":
                    cache.store(query, answer, faq_id=expected_id)

            total_latency_ms += latency

            all_logs.append(
                {
                    "threshold": thresh,
                    "query": query,
                    "expected_faq_id": expected_id,
                    "hit": res["hit"],
                    "matched_faq_id": res.get("faq_id"),
                    "false_hit": is_false_hit,
                    "score": res["score"],
                    "reason": res.get("reason", "hit"),
                    "latency_ms": round(latency, 2),
                    "tokens": tokens,
                }
            )

        hit_rate = round((hits / len(test_set)) * 100, 1)
        avg_latency = round(total_latency_ms / len(test_set), 2)
        llm_reduction = round(((len(test_set) - llm_calls) / len(test_set)) * 100, 1)

        summary_rows.append(
            {
                "threshold": thresh,
                "hit_rate_pct": hit_rate,
                "false_hits": false_hits,
                "negation_catches": negation_catches,
                "llm_calls": llm_calls,
                "llm_reduction_pct": llm_reduction,
                "avg_latency_ms": avg_latency,
            }
        )
        print(
            f"Threshold {thresh:.2f} | Hit Rate: {hit_rate}% | False Hits: {false_hits} | "
            f"Negation Catches: {negation_catches} | Avg Latency: {avg_latency} ms"
        )

    with open("results/sweep_summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
        writer.writeheader()
        writer.writerows(summary_rows)

    with open("results/request_logs.jsonl", "w", encoding="utf-8") as f:
        for row in all_logs:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    run_sweep(use_live_llm=False)