import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def ask_llm(question: str) -> dict:
    start = time.perf_counter()
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=(
            "You are a helpful Indian e-commerce customer support assistant. "
            "Answer the user's question concisely in 1-2 sentences.\n\n"
            f"Question: {question}"
        ),
    )
    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    usage = response.usage_metadata

    return {
        "answer": response.text.strip(),
        "input_tokens": usage.prompt_token_count if usage else 0,
        "output_tokens": usage.candidates_token_count if usage else 0,
        "latency_ms": latency_ms,
    }


if __name__ == "__main__":
    print(ask_llm("How many days does a refund take to reflect in my bank account?"))