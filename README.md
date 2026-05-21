
# DSN X BCT LLM Agent Challenge — Hackathon 3.0

**Team:** Solo submission  
**Track:** Both Task A (User Modeling) and Task B (Recommendation)  
**Live Demo:** 
- Task A: [mytwinn.streamlit.app](https://mytwinn.streamlit.app)
- Task B: [mytwinn02.streamlit.app](https://mytwinn02.streamlit.app)

---

## Overview

This repository contains two LLM-powered agentic systems built for the DSN X BCT Hackathon 3.0. Both systems are built in Python without relying on pre-built agent orchestration frameworks — every agent decision, tool call, and coordination logic is written and controlled deliberately.

---

## Task A — Review Simulation Agent

### What it does
Given a user ID and optionally a product ID or description, the system:
1. Loads the user's Amazon review history
2. Builds a behavioral profile (tone, vocabulary, rating patterns)
3. Simulates what that user would write about an unseen product
4. Returns a predicted star rating + written review in the user's voice

### Architecture
```
User ID + Product Details
        ↓
Supervisor Agent
        ↓
User Modeling Agent → builds behavioral profile from review history
        ↓
Review Simulation Agent → generates review in user's voice
        ↓
Engagement Agent → presents results + computes RMSE metrics
        ↓
Output: Simulated Rating + Review
```

### Dataset
- Amazon Digital Music Reviews (5-core subset)
- Source: [UCSD Recommender Systems Datasets](https://cseweb.ucsd.edu/~jmcauley/datasets/amazon_v2/)

### Running Locally
```bash
cd task_a
pip install -r requirements.txt

# Set environment variables in .env
# Required: GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY, PINECONE_API_KEY
# Dataset: place Digital_Music_5.json.gz in task_a/data/

uvicorn main:app --host 0.0.0.0 --port 8001
streamlit run app.py
```

### API Endpoints
- `POST /simulate` — simulate reviews for a user
- `GET /sample-users` — get random quality user IDs
- `GET /search-product?description=` — find product by text description
- `GET /user/{user_id}` — get user behavioral profile

---

## Task B — Recommendation Agent

### What it does
Given a user ID (or a cold-start user with no history), the system:
1. Loads the user's Yelp review history
2. Builds a preference profile (categories, price, location, dining style)
3. Conducts a multi-turn conversation to refine context
4. Semantically searches a Pinecone index of 33,000+ businesses
5. Re-ranks candidates using LLM reasoning
6. Returns top 5 recommendations with personalized explanations

### Architecture
```
User ID + Conversation
        ↓
Supervisor Agent
        ↓
User Modeling Agent → builds preference profile
        ↓
Retrieval Agent → semantic search via Pinecone (sentence-transformers)
        ↓
Ranking Agent → LLM re-ranks with explicit reasoning trace
        ↓
Engagement Agent → Pidgin-flavored conversational response
        ↓
Output: Ranked Recommendations + Reasoning Trace
```

### Key Features
- **Cold-start handling** — builds profile from conversation when no history exists
- **Multi-turn** — refines recommendations based on follow-up messages
- **Reasoning trace** — agent's thinking is visible in the UI
- **Nigerian Pidgin** — culturally contextualized responses
- **Conversational UI** — chat interface with live profile and recommendation panels

### Dataset
- Yelp Reviews (enriched with price range metadata, 60,000 records)
- 33,395 unique businesses indexed in Pinecone

### Running Locally
```bash
cd task_b
pip install -r requirements.txt

# Set environment variables in .env
# Required: GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY, PINECONE_API_KEY
# Embedding model: sentence-transformers/all-MiniLM-L6-v2 (auto-downloads)
# Dataset: place reviews_enriched_price.jsonl in task_b/data/

uvicorn main:app --host 0.0.0.0 --port 8002
streamlit run app.py
```

### API Endpoints
- `POST /chat` — send message and get recommendations
- `GET /sample-users` — get random quality user IDs
- `GET /user/{user_id}` — get user preference profile

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM Inference | Groq (llama-3.3-70b-versatile) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Vector Search | Pinecone |
| Database | Supabase |
| Backend | FastAPI |
| Frontend | Streamlit |
| Deployment | Render (API) + Streamlit Cloud (UI) |
| Containerization | Docker |

---

## Project Structure

```
dsn-bct-hackathon/
├── task_a/                    # Task A: Review Simulation
│   ├── src/
│   │   ├── agents/
│   │   │   ├── supervisor/    # Orchestrates pipeline
│   │   │   ├── user_modeling/ # Builds behavioral profiles
│   │   │   ├── review_simulation/ # Generates reviews
│   │   │   └── engagement/    # Presents results + metrics
│   │   └── dataset_loader.py  # HuggingFace dataset download
│   ├── main.py                # FastAPI backend
│   ├── app.py                 # Streamlit frontend
│   ├── config.py              # Environment configuration
│   └── Dockerfile
├── task_b/                    # Task B: Recommendation
│   ├── src/
│   │   ├── agents/
│   │   │   ├── supervisor/    # Orchestrates pipeline
│   │   │   ├── user_modeling/ # Builds preference profiles
│   │   │   ├── retrieval/     # Semantic search via Pinecone
│   │   │   ├── ranking/       # LLM re-ranking with reasoning
│   │   │   └── engagement/    # Pidgin conversational responses
│   │   ├── indexer.py         # Indexes businesses into Pinecone
│   │   └── dataset_loader.py  # HuggingFace dataset download
│   ├── main.py                # FastAPI backend
│   ├── app.py                 # Streamlit frontend
│   ├── config.py              # Environment configuration
│   └── Dockerfile
├── shared/
│   └── utils/                 # Shared utilities
└── docs/                      # Solution paper
```

---

## Environment Variables

Create `.env` files in both `task_a/` and `task_b/` with:

```
GROQ_API_KEY=
PINECONE_API_KEY=
PINECONE_INDEX_NAME=
SUPABASE_URL=
SUPABASE_KEY=
HF_TOKEN=
HF_DATASET_REPO=
```

---

## Docker

```bash
# Task A
cd task_a
docker build -t twinn-review .
docker run -p 8001:8001 --env-file .env twinn-review

# Task B
cd task_b
docker build -t twinn-recommend .
docker run -p 8002:8002 --env-file .env twinn-recommend
```

---

## Models Used

- **LLM:** `llama-3.3-70b-versatile` via Groq API
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- **Framework:** Custom Python agents (no LangChain/LangGraph)

---

## Disclosure

- Public pre-trained models used: Groq LLaMA 3.3, sentence-transformers
- Additional dataset used: Amazon Digital Music Reviews (5-core)
- All datasets used with appropriate academic licensing
```
