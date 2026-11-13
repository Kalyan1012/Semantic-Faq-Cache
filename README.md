
<div align="center">

# Semantic FAQ Cache

**Low-latency semantic caching API for Indian e-commerce support using FastEmbed, Qdrant Cloud, and FastAPI—with English/Hinglish negation guards.**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST_API-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Qdrant Cloud](https://img.shields.io/badge/Qdrant-Vector_DB-DC244C?style=flat-square)](https://qdrant.tech)
[![FastEmbed](https://img.shields.io/badge/FastEmbed-ONNX_CPU-00C853?style=flat-square)](https://github.com/qdrant/fastembed)
[![Gemini](https://img.shields.io/badge/Gemini-LLM_Fallback-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev)

</div>

---

## Overview

LLM-powered customer support bots repeatedly answer identical FAQ questions phrased in different ways, wasting tokens and adding latency. At the same time, naive vector caching introduces dangerous false positives—for example, matching *"Can I not cancel my order after it has been shipped?"* to *"Can I cancel my order after it has been shipped?"* at **98.16% cosine similarity**.

This project implements a semantic caching service with:

- **Multilingual Vector Search:** Encodes queries into 384-dimensional embeddings via `FastEmbed` (`paraphrase-multilingual-MiniLM-L12-v2`) and queries **Qdrant Cloud** using cosine similarity.
- **Bilingual Negation Guard:** Intercepts opposite-intent queries across English (`not`, `no`, `never`, `n't`) and Hinglish (`nahi`, `nahin`, `mat`, `na`) even when vector similarity exceeds `0.95`.
- **Cache Hygiene Controls:** Blocks responses containing PII/user-specific identifiers (`ORD-\d+`, 10-digit phone numbers, emails) from being cached and enforces a 24-hour TTL.
- **FastAPI Service + Reproducible Threshold Sweep:** Exposes `POST /ask` backed by Qdrant Cloud while running isolated in-memory threshold evaluations (`0.65` to `0.85`).

---

## Threshold Evaluation Results (100-Query Benchmark)

Evaluated against **30 canonical FAQs** and **100 labelled test queries** (60 paraphrases + 40 out-of-scope and negation traps):

| Cosine Threshold | Hit Rate | False Hits | Negation Catches | Avg Latency (ms) |
| :---: | :---: | :---: | :---: | :---: |
| `0.65` | 27.0% | 5 | 4 | 495.2 ms |
| `0.70` | 17.0% | 3 | 4 | 557.8 ms |
| `0.75` | 10.0% | 1 | 4 | 602.1 ms |
| **`0.80` (Selected)** | **5.0%** | **0** | **4** | **632.9 ms** |
| `0.85` | 3.0% | 0 | 3 | 645.4 ms |

> **Design Trade-off:** At `0.80`, the cache achieves **zero false hits** on cold-start adversarial traffic while blocking opposite-intent negation traps. In production, repeated user traffic populates common phrasings over time, raising hit rates without sacrificing answer accuracy.

---

## Project Structure

```text
semantic-faq-cache/
├── data/
│   ├── faqs.json            # 30 canonical Indian e-commerce FAQs
│   └── test_set.json        # 100 labelled evaluation queries
├── docs/
│   └── architecture.png     # System architecture diagram
├── results/
│   ├── sweep_summary.csv    # Threshold sweep metrics (0.65 - 0.85)
│   └── request_logs.jsonl   # Per-query similarity, guard reason, and latency logs
├── src/
│   ├── cache.py             # SemanticCache (FastEmbed + Qdrant + Guards)
│   ├── api.py               # FastAPI service (POST /ask)
│   ├── llm.py               # Gemini LLM fallback wrapper
│   ├── evaluate.py          # Isolated threshold benchmark script
│   └── demo.py              # Interactive CLI demo
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## Quickstart

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/semantic-faq-cache.git
cd semantic-faq-cache
```

### 2. Install Dependencies

This project uses `uv` for dependency management.

```bash
uv sync
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cat << 'EOF' > .env
GEMINI_API_KEY=your_gemini_api_key
QDRANT_URL=https://your-cluster-url.aws.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
EOF
```

Replace the placeholder values with your actual API credentials.

**Never commit your `.env` file or expose your API keys publicly.**

### 4. Run the Threshold Benchmark

The evaluation script uses an isolated in-memory Qdrant instance to ensure reproducible threshold testing.

```bash
uv run python -m src.evaluate
```

Evaluates cache performance across similarity thresholds from `0.65` to `0.85`.

### 5. Start the FastAPI Server

The API connects to Qdrant Cloud for vector storage and retrieval.

```bash
uv run uvicorn src.api:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### 6. Explore the Interactive API Documentation

Open the following URL in your browser:

**http://127.0.0.1:8000/docs**

Use the Swagger UI to test the `POST /ask` endpoint interactively.

---

## Tech Stack

| Technology | Purpose |
| :--- | :--- |
| Python 3.12 | Core programming language |
| FastAPI | REST API development |
| FastEmbed | Local CPU-based text embeddings |
| Qdrant Cloud | Vector database and semantic retrieval |
| ONNX Runtime | Efficient CPU inference |
| Gemini | LLM fallback for cache misses |
| uv | Dependency and environment management |

---

## Key Engineering Decisions

- **Local Embedding Generation:** Avoids sending customer queries to an external embedding API.
- **Vector Similarity Search:** Retrieves semantically similar questions rather than relying on exact string matching.
- **Negation-Aware Retrieval:** Prevents potentially dangerous cache hits between queries with opposite intent.
- **Threshold Calibration:** Evaluates multiple similarity cutoffs to balance cache hit rate and false positives.
- **TTL-Based Expiration:** Prevents outdated cached responses from being served indefinitely.
- **PII Filtering:** Reduces the risk of storing user-specific information in shared cache entries.

---

## Future Improvements

- Add Docker support for containerized deployment.
- Implement concurrent request and load testing.
- Introduce monitoring for cache hit rate and p95 latency.
- Compare semantic caching performance against traditional Redis caching.
- Improve multilingual intent detection beyond keyword-based negation checks.
- Evaluate precision, recall and F1-score across different similarity thresholds.

---

<div align="center">

**Built with Python, FastAPI, Qdrant, FastEmbed and Gemini.**

</div>
