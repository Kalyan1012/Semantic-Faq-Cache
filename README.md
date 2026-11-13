
# Semantic FAQ Cache

### Low-Latency Semantic Caching API for Indian E-Commerce Support

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-API-green)
![Qdrant](https://img.shields.io/badge/Vector%20DB-Qdrant-red)
![FastEmbed](https://img.shields.io/badge/Embeddings-FastEmbed-orange)
![Gemini](https://img.shields.io/badge/LLM-Gemini-blueviolet)

## Overview

Semantic FAQ Cache is a semantic caching system designed to reduce response latency and unnecessary LLM API calls in customer support applications.

Traditional caching relies on exact keyword matching. However, customers often ask the same question in different ways.

For example:

- "Where is my order?"
- "Can you track my package?"
- "I want to know my delivery status."

Although these questions have different wording, they express similar intent.

This project uses multilingual sentence embeddings and vector similarity search to identify semantically similar questions and return previously generated answers.

It also includes an English/Hinglish negation guard to prevent incorrect cache matches when two questions have opposite meanings.

### Architecture

![Semantic FAQ Cache Architecture](docs/architecture.png)

## Key Features

### 1. Semantic Similarity Search

- Uses FastEmbed with `paraphrase-multilingual-MiniLM-L12-v2`.
- Generates 384-dimensional sentence embeddings.
- Uses cosine similarity to identify semantically similar questions.
- Stores and retrieves FAQ embeddings using Qdrant.

### 2. English and Hinglish Negation Guard

A similarity-based cache can return incorrect answers when two questions have similar wording but opposite meanings.

Example:

- "Can I cancel my order?"
- "Can I not cancel my order?"

The system includes a bilingual negation guard to identify potentially conflicting queries before accepting a cache match.

Supported keywords include:

`not`, `no`, `never`, `n't`, `nahi`, `nahin`, `mat`, `na`

### 3. TTL-Based Cache Expiration

- Cached responses have a configurable time-to-live.
- Default TTL: 24 hours.
- Expired entries are not treated as valid cache hits.

### 4. PII Filtering

The system filters common sensitive information before caching queries.

It includes patterns for:

- Order IDs: `ORD-\d+`
- 10-digit phone numbers
- Email addresses

### 5. FastAPI Integration

Provides a REST API through:

`POST /ask`

The API processes customer questions, checks the semantic cache, and uses Gemini when a suitable cache answer is unavailable.

### 6. Threshold Evaluation

The project evaluates different cosine similarity thresholds to understand the trade-off between cache hit rate and incorrect cache matches.

## Threshold Evaluation Results

The following results are from the benchmark dataset used during development.

| Threshold | Hit Rate | False Hits | Negation Catches | Avg Latency |
|---|---:|---:|---:|---:|
| 0.65 | 27% | 5 | 4 | 495.2 ms |
| 0.70 | 17% | 3 | 4 | 557.8 ms |
| 0.75 | 10% | 1 | 4 | 602.1 ms |
| **0.80** | **5%** | **0** | **4** | **632.9 ms** |
| 0.85 | 3% | 0 | 3 | 645.4 ms |

**Selected threshold: 0.80**

A higher threshold reduces the risk of incorrect cache matches, but also reduces the cache hit rate.

The threshold was selected based on the benchmark results, prioritizing avoiding false cache hits.

## Project Structure

```text
semantic-faq-cache/
│
├── data/
│   ├── faqs.json
│   └── test_set.json
│
├── docs/
│   └── architecture.png
│
├── results/
│   ├── sweep_summary.csv
│   └── request_logs.jsonl
│
├── src/
│   ├── __init__.py
│   ├── cache.py
│   ├── api.py
│   ├── llm.py
│   ├── evaluate.py
│   └── demo.py
│
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

## Quickstart

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/semantic-faq-cache.git

cd semantic-faq-cache
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Install Dependencies

This project uses `uv` for dependency management.

```bash
uv sync
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
QDRANT_URL=your_qdrant_cloud_url
QDRANT_API_KEY=your_qdrant_api_key
```

Replace the placeholder values with your actual credentials.

Never commit your `.env` file or expose API keys publicly.

### 4. Run Threshold Evaluation

```bash
uv run python -m src.evaluate
```

This evaluates the semantic cache across different similarity thresholds and generates benchmark results.

### 5. Start the FastAPI Server

```bash
uv run uvicorn src.api:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### 6. Explore the API

Open the interactive Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Use the `POST /ask` endpoint to submit customer support questions.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Core implementation |
| FastAPI | REST API |
| FastEmbed | Sentence embeddings |
| Qdrant Cloud | Vector storage and similarity search |
| Gemini | LLM fallback |
| uv | Dependency management |
| pytest | Testing |

## Key Engineering Decisions

### Why Semantic Caching?

Exact-match caching fails when users express the same intent using different words.

Semantic caching uses vector embeddings to identify similar questions, improving the possibility of reusing previously generated answers.

### Why Qdrant?

Qdrant provides vector storage and similarity search, making it suitable for retrieving semantically similar questions.

### Why FastEmbed?

FastEmbed provides lightweight ONNX-based embedding generation and supports multilingual sentence embeddings.

### Why a Negation Guard?

Cosine similarity alone cannot reliably distinguish questions with opposite intent.

The negation guard helps prevent potentially unsafe cache matches involving English and Hinglish negation terms.

### Why Threshold Evaluation?

A lower similarity threshold increases cache hits but can also increase false matches.

A higher threshold is more restrictive and can reduce incorrect matches at the cost of fewer cache hits.

Evaluating multiple thresholds helps select a suitable trade-off.

## Future Improvements

- Add automated unit and integration tests.
- Implement more robust intent and negation detection.
- Add Redis-based caching for frequently accessed responses.
- Introduce Docker-based deployment.
- Perform concurrent load testing.
- Track cache hit rate and p95/p99 latency.
- Improve PII detection and anonymization.
- Add monitoring and observability.

## Author

**Kalyan Mysker**

Computer Science Engineering Student

GitHub: [Kalyan1012](https://github.com/Kalyan1012)
