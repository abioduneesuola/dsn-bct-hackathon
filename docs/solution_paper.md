Here's the full solution paper:

---

# DSN X BCT LLM Agent Challenge 3.0
## Solution Paper: LLM-Powered User Modeling and Intelligent Recommendation

**Submission:** Team Trailblazers  
**Tasks:** Task A (User Modeling) and Task B (Recommendation)  
**Live Demo:** Task A — mytwinn01.streamlit.app | Task B — mytwinn02.streamlit.app  
**Repository:** github.com/abioduneesuola/dsn-bct-hackathon

---

## 1. Introduction and Problem Statement

Online review platforms generate some of the richest behavioural data available on the web. Every rating, every written review, and every interaction pattern is a signal. It is a window into how a person thinks, what they value, and what they are likely to choose next. Yet, most AI systems still treat users as static profiles, averaging their behaviour into a single vector and losing the nuance that makes each person distinct.

This submission addresses that gap through two interconnected systems. 

The first is a review simulation agent that models individual users deeply enough to write in their voice, predicting not just star ratings, but the specific tone, vocabulary, and contextual references that characterize how that person communicates. 
The second is a conversational recommendation agent that goes beyond pattern matching to reason explicitly about a user before making suggestions; handling cold-start users, multi-turn refinement, and cross-domain recommendations across restaurant and book domains.

We built both systems in Python without relying on pre-built orchestration frameworks such as LangChain or LangGraph. Every agent decision, tool call, and coordination logic we designed deliberately. This choice was intentional: it produces systems that are transparent, debuggable, and easier to reason about, and it demonstrates our deeper understanding of agentic design than just wrapping existing abstractions.

---

## 2. Architecture Overview

Both tasks share the same foundational architecture: a multi-agent system where all the agents' activities are coordinated by a Supervisor Agent. Each agent has a single, well-defined responsibility and communicates through structured Python dictionaries rather than message queues or framework-managed state.

The general pattern is:

```
User Input
    ↓
Supervisor Agent — receives input, routes to appropriate agents
    ↓
User Modeling Agent — builds or retrieves behavioural profile
    ↓
Core Task Agent — simulation or retrieval/ranking
    ↓
Engagement Agent — formats output, adds cultural personality
    ↓
Output
```

All user profiles and interaction logs are persisted in Supabase. Semantic indexes live in Pinecone. LLM inference runs through Groq using the llama-3.3-70b-versatile model. The decision to avoid framework abstractions means that every prompt, every JSON parsing step, and every fallback behaviour is explicitly coded and visible in the repository.

---

## 3. Task A — Review Simulation Agent

### 3.1 Dataset

We used the Amazon Digital Music Reviews dataset (5-core subset) for Task A. The 5-core constraint ensures every user and product in the dataset has at least five interactions, providing sufficient signal for behavioural modeling. We then applied a quality filter in the workflow to retain only reviews with at least 50 legible characters, giving our data an extra layer of refinement.

### 3.2 User Modeling

When a user ID is submitted, the User Modeling Agent scans the dataset for all reviews written by that user. It extracts:

- **Tone** — enthusiastic, critical, balanced, casual, or formal
- **Vocabulary level** — simple, moderate, or sophisticated
- **Rating pattern** — generous, harsh, or balanced
- **Topics** — the themes and categories the user cares about
- **Writing style** — a two-sentence description of how they write
- **Common phrases** — three to five words or short phrases they frequently use
- **Average rating** — their historical mean score

This extraction is performed by the LLM in a single structured call with a system prompt that enforces JSON output. A retry mechanism handles cases where the LLM returns malformed JSON. Profiles are cached in Supabase so returning users do not require re-extraction.

### 3.3 Review Simulation

The Review Simulation Agent takes the user's behavioural profile and an unseen product, fetches context about that product from other users' reviews, and prompts the LLM to write a review in the target user's voice. The simulation prompt provides:

- The full behavioural profile of the target user
- The product's format and style metadata
- A sample of other users' reviews of the same product
- The average rating that product has received

This context enrichment was a deliberate design decision by us. When we first started experimenting, we discovered that without product context, the agent reproduced the user's general writing style, but applied it generically — a heavy metal fan described every product as 'brutal' and 'amazing.'
Adding actual product reviews perfectly guides the agent as to what the product actually is, thereby producing reviews that are both faithful to the user's voice, and specific to the product.

### 3.4 Product Input Modes

Three product input modes are supported: random unseen products drawn from the dataset, direct product ID entry for known items, and natural language description search where the agent scans 100 sample products and uses the LLM to match the description to the closest available item.

### 3.5 Evaluation

Rating accuracy is evaluated using Root Mean Square Error between simulated and actual ratings. Across test runs, RMSE consistently fell between 0.0 and 0.5, with most simulations achieving high confidence classifications. Review text quality is evaluated through the presented output, which displays simulated and actual reviews side by side for human comparison.

---

## 4. Task B — Recommendation Agent

### 4.1 Datasets

We used two datasets for Task B. The primary dataset is an enriched Yelp reviews data (about 7 million records), from which we sampled 60,000 records, covering 33,395 unique businesses. We also augmented it with price range metadata from the same Yelp website. We did this through data merging and cleaning. The secondary dataset is the Goodreads reviews corpus combined with the Goodreads book genres dataset, enabling cross-domain book recommendations. We stored 2.36 million books with titles and author names in Supabase for metadata lookup, some of which also have genre tags.

### 4.2 Semantic Indexing

Businesses and books are indexed into separate Pinecone indexes, using the sentence-transformers/all-MiniLM-L6-v2 model, which produces 384-dimensional dense embeddings. Each business is represented by a concatenation of its name, categories, city, state, and price range, enriched with a summary of its top-rated reviews. This enrichment ensures that semantic search retrieves businesses based on what they actually offer, not just their categorical labels.

### 4.3 User Modeling

The User Modeling Agent reads a user's Yelp review history and extracts a preference profile covering favorite categories, price preference, preferred cities, dining style, average rating given, and a natural language personality description. It also generates a search query string that represents what this user would enjoy next. This query is used directly as the Pinecone search input.

For cold-start users with no review history, the agent conducts a multi-turn conversation to elicit preferences conversationally, asking one question at a time about cuisine type, location, budget, and occasion. Once sufficient context is gathered, it constructs a temporary profile and proceeds to retrieval.

### 4.4 Retrieval and Ranking

The Retrieval Agent embeds the user's search query using the same sentence-transformers model used during indexing, ensuring semantic consistency between queries and documents. It retrieves the top 20 candidate businesses from Pinecone.

The Ranking Agent takes these candidates and the full user profile and prompts the LLM to reason explicitly before ranking. The reasoning trace, i.e. the agent's step-by-step thinking, is visible in the interface as a dedicated panel. This explicit reasoning is the core of the agentic workflow that reasons before recommending, as required by the task specification.

### 4.5 Multi-Turn Conversation

The Supervisor Agent maintains full conversation history across turns. When a user refines their request — asking for cheaper options, a different cuisine, or a different location — the conversation history is passed to the retrieval and ranking agents, allowing them to adjust recommendations contextually without losing prior context.

### 4.6 Cross-Domain Recommendation

After restaurant recommendations are delivered, users can request book recommendations through a dedicated panel. The book retrieval uses the same embedding model to search the Goodreads index using a query derived from the user's dining preferences and personality description. This cross-domain mapping — from restaurant taste to literary taste — demonstrates that the user model generalises beyond the domain in which it was built.

### 4.7 Nigerian Contextualization

All conversational responses are generated with explicit Nigerian Pidgin English instructions. The engagement agent uses words and phrases rich in localised context throughout conversations. This contextualization was a deliberate product decision we made. We are meeting users in the language and cultural register they are most comfortable with, and maybe even getting bonus points from the project brief!

---

## 5. Experiments and Ablation

**Model selection:** In our initial experiments, we used a few models, including gpt-oss-120b via Groq, but this model was unavailable a lot in the environment. We then switched to llama-3.3-70b-versatile which produced consistent, high-quality outputs.

**JSON parsing reliability:** Our early versions of the profile building and ranking agents frequently failed, due to malformed JSON from the LLM. We applied three mitigations to solve this: a system prompt explicitly instructing the model to output only valid JSON with no inner quotes, a start/end bracket extraction that finds the JSON object even when wrapped in explanatory text, and a three-attempt retry loop. Together, these eliminated JSON parsing failures entirely.

**Embedding model selection:** We initially used Cohere's embed-english-v3.0 model for 1024-dimensional embeddings. We later exhausted our limits during development, so we switched to sentence-transformers/all-MiniLM-L6-v2 running locally and on the server. This model produces 384-dimensional embeddings, requiring us to create new Pinecone indexes, but it delivered comparable semantic quality at zero ongoing cost.

**Lazy model loading:** Loading sentence-transformers at server startup caused out-of-memory crashes on the deployment server. We adjusted the scripts to move the model loading activity inside a lazy initialization function that only runs on the first actual request, resolving the issue without requiring a more expensive server tier for the task.

**Dataset quality filtering:** The raw datasets from the source also contained users with very short reviews, providing insufficient signal for behavioural modelling. We enforced a minimum review length of 50 legible characters and a minimum of five qualifying reviews, reducing the user pool but dramatically improving data quality. This was not a big problem, because the data pool is still large enough.

**Product context enrichment:** Early Task A simulations produced reviews that accurately captured user tone but were generically applied to every product. Adding other users' actual reviews of the target product as context grounded the simulation in product-specific details, producing reviews that are both behaviourally faithful and contextually relevant.

---

## 6. Nigerian Contextualization

The competition brief encouraged us to incline towards building a system contextualized to behave and sound like Nigerians. In our work, we addressed this at multiple levels.

At the language level, we made the engagement agents for both tasks use Nigerian Pidgin English consistently throughout conversations. The prompts in the agent's workflow specify concrete Pidgin vocabulary, and instruct the model to use it not occasionally but consistently. Test conversations confirm natural Pidgin usage; including culturally specific analogies, such as comparing Python to jollof rice, and describing progress as moving like a danfo driver in Lagos traffic.

At the product level, Task B's default user selection draws from a pool of real Yelp users whose review histories inform recommendations. Cold-start users can specify Nigerian cities and the system handles them without geographic bias, as long as these locations are represented in the data. The recommendation agent will correctly handle requests specifying Lagos, Abuja, or other Nigerian cities as location context.

At the architectural level, the entire system was built with the assumption that users may be on low-bandwidth mobile connections. The Streamlit frontend is lightweight, and the API responses are compact. We can also integrate the system into other apps for easier access to users.

---

## 7. Deployment and Reproducibility

Both tasks are deployed as independent services:

- **Task A API:** Render web service (FastAPI, port 8001)
- **Task A UI:** Streamlit Community Cloud
- **Task B API:** Render web service (FastAPI, port 8002, possible higher disk requirements for sentence-transformers memory requirements)
- **Task B UI:** Streamlit Community Cloud

Datasets are hosted on HuggingFace Datasets and downloaded automatically at server startup if not present locally. This ensures reproducibility without requiring large files in the repository.

Docker containers are provided for both tasks. Each Dockerfile installs dependencies from the task-specific requirements.txt and starts the FastAPI server on the appropriate port.

Environment variables required for local execution are documented in the README. All API keys are loaded from .env files which are excluded from the repository via .gitignore.

---

## 8. Limitations and Future Work

**Book metadata completeness:** Author names required us to do a separate join between the books dataset and the authors dataset. We performed this join, and all 2.36 million book records now include author names. Book titles are available, but cover art and ISBN metadata were not included in the indexed records.

**Goodreads cold-start:** Book recommendations for cold-start users default to a less-refined query than returning users. A future improvement would conduct a brief conversational exchange to elicit literary preferences before querying the books index.

**Dataset scale:** The Yelp sample we took contains 60,000 random reviews across 33,395 businesses. The full Yelp dataset contains significantly more. A production deployment would benefit from indexing the complete dataset for broader geographic and categorical coverage.

**Rating simulation variance:** RMSE performance varies across users. Users with highly consistent rating patterns produce lower RMSE scores. Users who rate unpredictably — giving both one-star and five-star reviews across similar products — are inherently harder to simulate accurately. A confidence-weighted ensemble approach could improve performance on these edge cases.

**WhatsApp integration:** The architecture was designed to support WhatsApp as an added interface. The FastAPI backend is ready to receive webhook messages. Full WhatsApp Business API integration requires Meta approval, although we couldn't complete it within the competition timeline.

**Localised Nigerian dataset:** Our current system uses Amazon and Yelp datasets which are predominantly Western in origin. Working with a Nigeria-specific review dataset — covering local restaurants, markets, and services — would significantly improve the relevance and cultural accuracy of both user modeling and recommendations.

**LLM for Pidgin contextualization:** The current Pidgin implementation relies on prompting a general-purpose model with Pidgin vocabulary instructions. A model specifically trained on Nigerian Pidgin text would produce more authentic and nuanced Pidgin outputs than prompt engineering alone can achieve.

**Higher-dimensional embeddings:** Our current system uses 384-dimensional embeddings from all-MiniLM-L6-v2 due to API credit constraints. Upgrading to a higher-dimensional model or a multilingual model trained on African languages would improve semantic search precision, particularly for cross-domain recommendations.

**Speech-to-speech interaction:** We designed this architecture with voice interaction in mind. Integrating a speech-to-speech pipeline would transform both interfaces into fully voice-driven experiences, dramatically improving accessibility for users who prefer speaking over typing.

---

## 9. User Guide

### Task A — Twinn Review (mytwinn.streamlit.app)

**Getting started:**
Click **Get Random Users** in the left sidebar to populate a list of Amazon reviewer IDs from the dataset. Each ID represents a real reviewer whose history will be used to build a behavioural profile. Click any ID to select it, or paste a known ID directly into the User ID field.

**Product input:**
Three modes are available via the radio button below the User ID field. Random products automatically selects unseen items from the dataset. Enter Product ID accepts a known Amazon ASIN directly. Describe a product accepts natural language such as a classic rock guitar album and the system finds the closest matching product in the dataset.

**Running a simulation:**
Click Run Simulation. The system will build the user's behavioural profile, select or find the product, and simulate reviews. This typically takes 15-30 seconds.

**Interpreting results:**
The right panel shows three metrics. RMSE measures how close the simulated star rating is to the actual rating — lower is better, with 0.0 being perfect. Reviews Simulated shows how many products were processed. High Confidence shows how many simulations the agent rated as high confidence.

The behavioural profile section shows the extracted user characteristics — tone describes how they write emotionally, vocabulary level describes their language complexity, and rating pattern describes whether they tend to rate generously or harshly.

Each review card shows the simulated review alongside the actual review written by the real user, allowing direct comparison. The delta (Δ) value shows the absolute difference between simulated and actual star ratings.

---

### Task B — Twinn Recommend (mytwinn02.streamlit.app)

**Getting started:**
Click **↻ Get Random Users** in the left sidebar to populate user IDs from the Yelp dataset. Click any user to load their profile and start a session, or use the manual entry field to paste a specific user ID. To test cold-start behaviour, click New Session — this creates a random UUID with no history, and the system will ask questions to understand your preferences conversationally.

**Having a conversation:**
Type naturally in the chat input at the bottom. The system will ask clarifying questions if it needs more context. Once it has enough information — typically after two to three exchanges — it will trigger the recommendation pipeline and return results. You can refine recommendations by saying things like show me cheaper options or what about Italian instead.

**The right panel has three tabs:**

The **Reasoning tab** shows the agent's step-by-step thinking as it processes your request. Each arrow represents one decision the agent made — from analyzing your profile to searching the knowledge base to ranking candidates. This transparency is intentional and demonstrates the agentic workflow.

The **Top Picks tab** shows the five recommended businesses. Each card shows the business name, city, price range, category tags, and a personalized reason why it was recommended for this specific user. The reason is generated by the LLM based on the user's actual profile.

The **Book Picks tab** is the cross-domain feature. Click **✦ Find Books For Me** to retrieve book recommendations based on your taste profile. The system queries a separate Goodreads index using your dining and lifestyle preferences to infer what genres and authors you might enjoy. Each book card shows the title, author in italics, genre tag, average rating, and a snippet from reader reviews. Click the button again to get a different set of recommendations from the same personalized pool.

**Starting over:**
Click **✦ New Session** in the sidebar to reset the conversation, recommendations, and book picks while keeping the same user ID. This is useful for testing different conversation paths with the same user.

---

## 10. Conclusion

Both systems demonstrate that LLM-based user modeling and recommendation can go significantly beyond pattern matching. By building agents that reason explicitly, converse naturally, and adapt to individual behavioural signals, it becomes possible to treat each user as the dynamic, context-sensitive agent they actually are — rather than a static average of their past behaviour.

Our decision to build these agents without pre-built orchestration frameworks, to deploy on accessible infrastructure, to contextualize for Nigerian users, and to make the agent's reasoning visible in the interface, reflects a conviction that the best AI systems are not just technically capable but transparent, culturally aware, and genuinely useful to the people they serve.
