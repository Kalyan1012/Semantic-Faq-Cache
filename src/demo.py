from src.cache import SemanticCache
from src.llm import ask_llm

def main():
    cache = SemanticCache(threshold=0.80)
    print("\n=== Semantic FAQ Cache Demo (type 'exit' to quit) ===\n")

    while True:
        query = input("Ask a question: ").strip()
        if not query or query.lower() == "exit":
            break

        res = cache.lookup(query)
        if res["hit"]:
            print(
                f"[CACHE HIT | sim={res['score']} | {res['latency_ms']} ms | 0 tokens]\n"
                f"Matched: \"{res['matched_question']}\"\n"
                f"Answer:  {res['answer']}\n"
            )
        else:
            llm_res = ask_llm(query)
            total_ms = round(res["latency_ms"] + llm_res["latency_ms"], 2)
            total_tokens = llm_res["input_tokens"] + llm_res["output_tokens"]
            saved = cache.store(query, llm_res["answer"])
            print(
                f"[CACHE MISS ({res['reason']}) | sim={res['score']} | {total_ms} ms | {total_tokens} tokens | stored={saved}]\n"
                f"Answer:  {llm_res['answer']}\n"
            )

if __name__ == "__main__":
    main()