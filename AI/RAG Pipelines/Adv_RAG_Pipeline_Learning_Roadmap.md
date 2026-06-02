# RAG Pipeline Learning Roadmap — From Traditional to Agentic

> **Audience:** An engineer who already understands the traditional RAG loop and has hands-on experience with **Azure AI Search** (indexers, vector + semantic ranking). This roadmap takes you from a deep refresher of the classic pipeline through advanced retrieval, GraphRAG, and full **Agentic RAG** systems.
>
> **How to use this:** Each section lists *what to learn*, *why it matters*, and *credible resources*. Work top-to-bottom; the sections are ordered so each builds on the previous one. The "Build" checkpoints are where you should stop reading and write code. Wherever possible, map concepts back to the Azure primitives you already know.

---

## Section 0 — Mental Model & Foundations

**Goal:** Anchor everything in a precise mental model of the three RAG stages — **Indexing → Retrieval → Generation** — and the canonical taxonomy you'll see repeatedly in papers and vendor docs.

Learn the **Naive → Advanced → Modular RAG** taxonomy. This is the vocabulary the whole field uses: *Naive* RAG is the basic index-retrieve-generate loop; *Advanced* RAG adds pre-retrieval and post-retrieval optimizations (query rewriting, reranking); *Modular* RAG decomposes the pipeline into swappable, orchestratable modules — which is the conceptual bridge to agentic systems.

Also internalize **why RAG fails**, because the rest of the roadmap is essentially a catalog of fixes for these failure points (missing content, wrong chunking, retrieval misses, reranking gaps, context-window overflow, extraction errors, wrong format).

**Topics**
- The retrieval-augmented generation pattern and what it solves (grounding, freshness, hallucination reduction, provenance)
- The three stages and where latency/cost/quality trade-offs live in each
- Naive vs. Advanced vs. Modular RAG
- The common failure modes of production RAG

**Resources**
- Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* (the original RAG paper) — https://arxiv.org/abs/2005.11401
- Gao et al., *Retrieval-Augmented Generation for Large Language Models: A Survey* (the Naive/Advanced/Modular taxonomy) — https://arxiv.org/abs/2312.10997
- Barnett et al., *Seven Failure Points When Engineering a RAG System* — https://arxiv.org/abs/2401.05856
- Microsoft Learn, *RAG and generative AI in Azure AI Search* (maps the pattern onto Azure objects) — https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview

---

## Section 1 — The Traditional / Classic RAG Pipeline (Deep Refresher)

**Goal:** Re-derive the classic pipeline from first principles so you can reason about *why* each later optimization exists. On Azure this is the **"Classic RAG"** pattern: your app issues a single query to AI Search (hybrid + semantic ranking) and hands the flattened results to an LLM.

**Topics**
- End-to-end flow: document → loader → chunker → embedding model → vector store → retriever → prompt assembly → LLM → answer (+ citations)
- The "retriever-then-reader" framing
- Single-query orchestration and its limits (no query planning, one shot at retrieval)
- Mapping to Azure: indexer → skillset (chunk + embed) → index (vector + keyword fields) → query with `semantic` ranker

**Build checkpoint #1**
Stand up a minimal RAG app over ~50 of your own documents. Use Azure AI Search (you already know it) *or* a local stack (FAISS/Chroma + an OpenAI/Azure OpenAI embedding model) so you can later compare. Measure baseline answer quality qualitatively before optimizing anything.

**Resources**
- Microsoft Learn — Azure AI Search RAG overview (Classic vs. Agentic split) — https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview
- DeepLearning.AI — *Retrieval Augmented Generation (RAG)* course (Zain Hasan; builds progressively from a simple prototype, uses semantic search, BM25, RRF) — https://www.deeplearning.ai/courses/retrieval-augmented-generation-rag/

---

## Section 2 — The Data Ingestion Pipeline & Chunking Strategies

**Goal:** Master the ingestion side, because retrieval quality is capped by ingestion quality ("garbage in, garbage out"). This is where most real-world RAG quality is won or lost.

### 2a. Document loading & parsing
- File-type handling (PDF, DOCX, HTML, tables, scanned images via OCR, slides)
- Layout-aware parsing for tables and multi-column docs (a frequent silent failure)
- On Azure: the **skillset / "integrated vectorization"** pipeline, image verbalization skills, and incremental indexing for freshness

### 2b. Chunking strategies (by scenario)
Learn each strategy and, more importantly, *when* to reach for it:

| Strategy | How it works | Best for |
|---|---|---|
| **Fixed-size / token-based** | Split every N tokens | Hard token budgets; simplest baseline |
| **Recursive character splitting** | Split on a hierarchy of separators (¶ → sentence → word) | The default workhorse; structured prose |
| **Structure-aware** (Markdown/HTML header splitting) | Split on document structure | Docs with clear headings — often the single biggest easy win |
| **Semantic chunking** | Group sentences by embedding similarity | Long, multi-topic, messy documents |
| **Cluster / LLM-based chunking** | Group related content even when non-adjacent; LLM decides boundaries | Highest accuracy, highest cost |
| **Late chunking** | Embed the full document first, then pool per-chunk | When chunks are ambiguous without surrounding context (pronouns, headers) |
| **Hierarchical / small-to-large** | Index small chunks, retrieve, then expand to parents | Balancing retrieval precision with generation context |

**Practical guidance to internalize:** Start with recursive splitting at **~512 tokens with 10–20% overlap** as a baseline, and only move to semantic/LLM chunking if your metrics justify the extra cost. Benchmarks repeatedly show a practical sweet spot of roughly **512–1024 tokens**, with quality degrading well before very large chunks. Note the genuine debate here: some peer-reviewed benchmarks find fixed/recursive chunking matches or beats semantic chunking once embedding-model choice is controlled — so treat chunking as something you *measure*, not something you assume.

**Build checkpoint #2**
Re-ingest your corpus three ways (recursive-512, structure-aware, semantic) and compare retrieval recall. You'll feel firsthand why "it depends" is the honest answer.

**Resources**
- Firecrawl, *Best Chunking Strategies for RAG (with benchmarks)* — https://www.firecrawl.dev/blog/best-chunking-strategies-rag
- Databricks, *The Ultimate Guide to Chunking Strategies for RAG* — https://community.databricks.com/t5/technical-blog/the-ultimate-guide-to-chunking-strategies-for-rag-applications/ba-p/113089
- Adnan Masood, *Chunking Strategies for RAG: A Comprehensive Guide* (covers fixed → recursive → semantic → LLM → agentic → late → hierarchical) — https://medium.com/@adnanmasood/chunking-strategies-for-retrieval-augmented-generation-rag-a-comprehensive-guide-5522c4ea2a90
- Jina AI, *Late Chunking* — https://arxiv.org/abs/2409.04701
- Anthropic, *Contextual Retrieval* (prepend chunk-level context before embedding) — https://www.anthropic.com/news/contextual-retrieval

---

## Section 3 — Embedding Techniques

**Goal:** Understand the representation layer. The embedding model often matters as much as the chunking strategy.

**Topics**
- **Dense embeddings** (bi-encoders): how semantic similarity is captured; dimensionality vs. cost vs. quality
- **Sparse embeddings** (BM25, SPLADE): exact-term matching, where dense models fail (IDs, codes, rare jargon)
- **Multi-vector / late-interaction** (ColBERT): token-level matching for higher precision at reasonable cost
- Embedding model selection: domain fit, multilingual needs, max sequence length, cost; consult a current leaderboard (MTEB) rather than trusting defaults
- Practical caveat from benchmarks: on some domains (e.g. financial/numeric docs) **BM25 can beat state-of-the-art dense retrieval** — never assume semantic search universally wins
- On Azure: vectorizers, integrated vectorization, and choosing/deploying an embedding model in Azure OpenAI

**Resources**
- Khattab & Zaharia, *ColBERT* (late interaction) — https://arxiv.org/abs/2004.12832; *ColBERTv2* — https://arxiv.org/abs/2112.01488
- Hugging Face **MTEB** embedding leaderboard (check current standings; rankings change) — https://huggingface.co/spaces/mteb/leaderboard
- *From BM25 to Corrective RAG: Benchmarking Retrieval Strategies* (shows where BM25 still wins and how reranking dominates) — https://arxiv.org/abs/2604.01733

---

## Section 4 — Vector Stores, Indexes & ANN

**Goal:** Know what happens under the hood when you store and query vectors, so you can tune recall/latency/cost deliberately.

**Topics**
- Approximate Nearest Neighbor (ANN) algorithms: **HNSW** (graph-based) and **IVF** (cluster-based) — recall vs. speed vs. memory trade-offs
- Metadata filtering and hybrid filter+vector queries (and the pitfalls of pre- vs. post-filtering)
- Index freshness / incremental updates
- On Azure: AI Search vector index configuration, HNSW parameters, and document-level security trimming
- When to choose AI Search vs. a dedicated vector DB (Weaviate, Qdrant, pgvector, Pinecone) — and when pgvector-in-Postgres is enough

**Resources**
- Microsoft Learn — Azure AI Search vector search and configuration (start from the RAG overview and follow the vector-search links) — https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview
- DeepLearning.AI RAG course (uses Weaviate + Arize Phoenix for hands-on indexing/scaling) — https://www.deeplearning.ai/courses/retrieval-augmented-generation-rag/

---

## Section 5 — The Retrieval Pipeline: Retrievers, Hybrid Search, Query Transformation & Reranking

**Goal:** This is the heart of *Advanced RAG*. Learn to treat retrieval as a multi-stage pipeline: **fetch → fuse → transform → rerank**.

### 5a. Retriever types
- Dense, sparse, and hybrid retrievers
- **Hybrid search with Reciprocal Rank Fusion (RRF)** — combine BM25 + vector results to catch both exact tokens and semantic matches (this is what Azure's classic pattern does well)

### 5b. Query transformation (pre-retrieval)
Users write *questions*; corpora contain *answers* — and they live in different regions of embedding space. Query transformation bridges that gap:
- **HyDE** (Hypothetical Document Embeddings): generate a hypothetical answer and embed *that* instead of the raw question
- **Multi-query**: generate 3–5 paraphrases and union the results
- **Step-back prompting**: reformulate a specific question into a broader one for better context
- **Query decomposition / routing**: split multi-part questions; route to the right index/source

*Caveat:* HyDE and multi-query help recall on broad questions but provide **limited benefit for precise numeric/lookup queries** — apply them selectively.

### 5c. Reranking (post-retrieval)
- **Cross-encoder rerankers** (e.g. MS-MARCO MiniLM, Cohere Rerank): re-score query–document pairs for fine-grained relevance
- **Late-interaction reranking** (ColBERT) when cross-encoders are too expensive
- The **two-stage pattern** (cheap dense/BM25 fetch of top-k → expensive rerank to top-3) consistently delivers large recall/MRR gains over single-stage retrieval
- Addresses the **"lost in the middle"** problem by putting the strongest evidence where the LLM attends most
- *When to skip reranking:* tiny curated corpora, or hard sub-500ms latency budgets

**Build checkpoint #3**
Add hybrid search + RRF, then bolt on a cross-encoder reranker. Measure **Recall@k**, **MRR**, and **nDCG** before/after. Then add HyDE and confirm it helps your broad queries but not your lookup queries.

**Resources**
- Neo4j, *Advanced RAG Techniques for High-Performance LLM Applications* (hybrid + RRF, HyDE, query expansion, the agentic plan→route→act→verify loop) — https://neo4j.com/blog/genai/advanced-rag-techniques/
- Google Codelabs, *Advanced RAG Methods* (HyDE, step-back, reranking, lost-in-the-middle — hands-on) — https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/8-advanced-rag-methods/advanced-rag-methods
- Gao et al., *HyDE: Precise Zero-Shot Dense Retrieval without Relevance Labels* — https://arxiv.org/abs/2212.10496
- *Advanced RAG: From Naive Retrieval to Hybrid Search and Re-ranking* (cross-encoders vs. ColBERT late interaction) — https://dev.to/kuldeep_paul/advanced-rag-from-naive-retrieval-to-hybrid-search-and-re-ranking-4km3

---

## Section 6 — Augmentation & Generation

**Goal:** Turn retrieved context into grounded, citable answers. Retrieval gets the right text in front of the model; augmentation decides how it's used.

**Topics**
- Prompt/context assembly: ordering, deduplication, context compression/distillation to fit the window
- Grounded prompting: forcing the model to answer *only* from retrieved context, with inline **citations** back to chunks
- Handling "I don't know" / abstention when evidence is weak
- Context-window management and the lost-in-the-middle positioning effect
- Treat retrieved content as **untrusted input** — guard against prompt injection coming *from your documents*

**Resources**
- Microsoft Foundry — *RAG and indexes* (security at retrieval time, treating retrieved passages as untrusted, Entra ID over API keys) — https://learn.microsoft.com/en-us/azure/foundry/concepts/retrieval-augmented-generation
- Gao et al. survey, "Generation" and "Augmentation" sections — https://arxiv.org/abs/2312.10997

---

## Section 7 — Advanced RAG Retrieval Patterns

**Goal:** Add the well-known structural patterns that decouple *what you retrieve on* from *what you feed the LLM*.

**Topics**
- **Sentence-window retrieval**: embed/retrieve single sentences, then expand to a surrounding window for generation
- **Auto-merging / hierarchical retrieval**: retrieve small leaf chunks; if enough siblings match, merge up to the parent
- **Parent-document retriever** and **small-to-large** patterns
- **Contextual Retrieval**: prepend LLM-generated context to each chunk before embedding (reduces retrieval failures substantially)

**Build checkpoint #4**
Implement sentence-window and auto-merging retrieval (LlamaIndex makes these one-liners) and evaluate against your Section 5 baseline using the RAG triad (Section 10).

**Resources**
- DeepLearning.AI / LlamaIndex, *Building and Evaluating Advanced RAG Applications* (sentence-window + auto-merging retrieval, plus the RAG triad) — https://www.deeplearning.ai/short-courses/building-evaluating-advanced-rag
- Course notebooks — https://github.com/kevintsai/Building-and-Evaluating-Advanced-RAG-Applications
- Anthropic, *Contextual Retrieval* — https://www.anthropic.com/news/contextual-retrieval

---

## Section 8 — GraphRAG (Knowledge-Graph-Augmented Retrieval)

**Goal:** Go beyond flat text retrieval when your questions require connecting facts across entities, documents, and time (multi-hop reasoning, "compare X to Y," global summarization).

**Topics**
- Why flat vector retrieval struggles with relational / multi-hop questions
- The GraphRAG process: **graph-based indexing → graph-guided retrieval → graph-enhanced generation**
- Entity/relationship extraction, community detection, and local-vs-global query strategies
- Microsoft's GraphRAG: hierarchical community summaries for global "sense-making" queries where baseline RAG gives shorter, more hallucination-prone answers
- When *not* to use it (cost and indexing complexity are real)

**Resources**
- Microsoft Research, *From Local to Global: A GraphRAG Approach to Query-Focused Summarization* — https://arxiv.org/abs/2404.16130
- Microsoft GraphRAG project — https://github.com/microsoft/graphrag
- *Graph Retrieval-Augmented Generation: A Survey* (ACM TOIS; G-Indexing / G-Retrieval / G-Generation framing) — https://dl.acm.org/doi/10.1145/3777378
- *Retrieval-Augmented Generation with Graphs (GraphRAG)* survey — https://arxiv.org/abs/2501.00309

---

## Section 9 — Agentic RAG

**Goal:** The destination. Stop treating RAG as "one query + one index" and wrap retrieval in a **decision-making loop** driven by an LLM agent that can plan, route, retrieve iteratively, self-critique, and use tools.

### 9a. What makes RAG "agentic"
Four capabilities separate agentic RAG from naive RAG: the agent decides **when** to retrieve, **scores relevance** of what came back, **rewrites the query** when retrieval fails, and runs a **closed retrieval loop** until it has enough evidence. The underlying agentic design patterns are **reflection, planning, tool use, and multi-agent collaboration**.

### 9b. The taxonomy (learn these named architectures)
- **Single-agent (router)**: one agent chooses sources/tools per query
- **Multi-agent / hierarchical**: specialized agents coordinated by an orchestrator
- **Corrective RAG (CRAG)**: grade retrieved docs; if poor, correct via re-query or web search
- **Self-RAG**: model emits reflection tokens to decide when to retrieve and whether output is supported (works best when you can fine-tune the base model; approximate with structured prompting on closed APIs)
- **Adaptive RAG**: route by query complexity — answer simple ones from parametric knowledge, escalate complex ones to multi-step retrieval
- **Graph-based agentic RAG**: agents reason over a knowledge graph

### 9c. On Azure: Agentic Retrieval
Azure AI Search now ships **agentic retrieval** — a pipeline that uses an LLM to break a complex query into focused **subqueries**, runs them **in parallel**, uses **conversation history** for context-aware planning, and returns structured, citation-ready results (with optional answer synthesis). New objects: **knowledge sources**, a **knowledge agent/base**, and a **retrieve** action you call as an agent tool. Microsoft's own guidance: for *new* RAG implementations, start with agentic retrieval; keep classic RAG when you need GA features or minimal latency.

**Build checkpoint #5**
Implement a CRAG or Adaptive-RAG loop with LangGraph (relevance grading + query rewrite + conditional web search). Then prototype the same idea on Azure agentic retrieval to compare the managed vs. DIY trade-off.

**Resources**
- Singh et al., *Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG* (the canonical taxonomy: single/multi/hierarchical/corrective/adaptive/graph) — https://arxiv.org/abs/2501.09136
- Companion repo with diagrams, taxonomy, and framework links — https://github.com/asinghcsu/AgenticRAG-Survey
- Asai et al., *Self-RAG* — https://arxiv.org/abs/2310.11511
- Yan et al., *Corrective RAG (CRAG)* — https://arxiv.org/abs/2401.15884
- Jeong et al., *Adaptive-RAG* — https://arxiv.org/abs/2403.14403
- LangGraph tutorials for CRAG / Adaptive RAG / Self-RAG — https://langchain-ai.github.io/langgraph/tutorials/
- Microsoft Learn — Azure AI Search agentic retrieval (start from the RAG overview) — https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview
- *Next-Level RAG on Azure: Knowledge Bases with AI Search and Foundry* — https://itnext.io/next-level-rag-on-azure-building-knowledge-bases-with-azure-ai-search-and-foundry-6d88d60e7202

---

## Section 10 — Evaluation & Observability

**Goal:** You cannot improve what you don't measure. Evaluation is not optional — it's how you iterate efficiently in dev *and* catch regressions in production.

**Topics**
- The **RAG triad**: **Context Relevance** (are retrieved chunks relevant?), **Groundedness/Faithfulness** (is the answer supported by context?), **Answer Relevance** (does it address the question?)
- Retrieval metrics: Recall@k, Precision@k, MRR, nDCG, hit rate
- LLM-as-judge evaluation and its pitfalls (calibration, bias)
- Building a golden test set from your own corpus; synthetic Q&A generation
- Observability/tracing in production (latency, cost, drift)

**Resources**
- Es et al., *RAGAS: Automated Evaluation of RAG* — https://arxiv.org/abs/2309.15217 ; framework — https://docs.ragas.io/
- DeepLearning.AI, *Building and Evaluating Advanced RAG* (the RAG triad in depth) — https://www.deeplearning.ai/short-courses/building-evaluating-advanced-rag
- Arize **Phoenix** for tracing/eval — https://docs.arize.com/phoenix

---

## Section 11 — Production Concerns (Azure-flavored)

**Goal:** Ship it. The gap between a demo and production is mostly here.

**Topics**
- **Security**: document-level access control / security trimming at retrieval time; **Microsoft Entra ID over API keys** for prod; treating retrieved content as untrusted (prompt-injection defense in your system prompt)
- **Cost & latency**: embedding/rerank/LLM token budgets; caching; when to skip reranking; managed (agentic retrieval) vs. self-hosted trade-offs
- **Freshness**: incremental indexing and re-embedding strategy
- **Multi-source retrieval**: SharePoint, OneLake, Blob, line-of-business apps via knowledge sources
- **Governance & evaluation in CI**: regression gates on the RAG triad before deploy

**Resources**
- Microsoft Foundry — RAG security & access-control guidance — https://learn.microsoft.com/en-us/azure/foundry/concepts/retrieval-augmented-generation
- Microsoft Learn — RAG with Azure Files (framework + vector-DB choices end to end) — https://learn.microsoft.com/en-us/azure/storage/files/artificial-intelligence/retrieval-augmented-generation/overview

---

## Suggested Build Progression (Capstone Path)

1. **Classic RAG** over your own docs on Azure AI Search (baseline). *(Checkpoint 1)*
2. **Chunking bake-off** — three strategies, measured. *(Checkpoint 2)*
3. **Advanced retrieval** — hybrid + RRF + cross-encoder reranker + selective HyDE. *(Checkpoint 3)*
4. **Structural patterns** — sentence-window / auto-merging, evaluated with the RAG triad. *(Checkpoint 4)*
5. **Agentic RAG** — a CRAG/Adaptive loop in LangGraph, then the Azure agentic-retrieval equivalent. *(Checkpoint 5)*
6. *(Stretch)* **GraphRAG** for multi-hop/global questions where flat retrieval underperforms.

At each step, keep the *same* golden eval set so improvements are comparable.

---

## Master Resource List

**Foundational papers**
- RAG (Lewis et al., 2020) — https://arxiv.org/abs/2005.11401
- RAG survey / taxonomy (Gao et al., 2023) — https://arxiv.org/abs/2312.10997
- Seven Failure Points of RAG — https://arxiv.org/abs/2401.05856
- HyDE — https://arxiv.org/abs/2212.10496
- ColBERT / ColBERTv2 — https://arxiv.org/abs/2004.12832 · https://arxiv.org/abs/2112.01488
- Self-RAG — https://arxiv.org/abs/2310.11511
- Corrective RAG — https://arxiv.org/abs/2401.15884
- Adaptive-RAG — https://arxiv.org/abs/2403.14403
- Agentic RAG survey — https://arxiv.org/abs/2501.09136
- GraphRAG (Microsoft) — https://arxiv.org/abs/2404.16130
- RAGAS — https://arxiv.org/abs/2309.15217

**Courses (hands-on)**
- DeepLearning.AI — *Retrieval Augmented Generation (RAG)* — https://www.deeplearning.ai/courses/retrieval-augmented-generation-rag/
- DeepLearning.AI — *Building and Evaluating Advanced RAG* — https://www.deeplearning.ai/short-courses/building-evaluating-advanced-rag
- Google Codelabs — *Advanced RAG Methods* — https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/8-advanced-rag-methods/advanced-rag-methods

**Azure docs**
- Azure AI Search RAG overview (Classic + Agentic) — https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview
- Microsoft Foundry RAG concepts (security, agentic retrieval) — https://learn.microsoft.com/en-us/azure/foundry/concepts/retrieval-augmented-generation

**Engineering deep-dives**
- Neo4j — Advanced RAG techniques — https://neo4j.com/blog/genai/advanced-rag-techniques/
- Firecrawl — Chunking strategies (benchmarks) — https://www.firecrawl.dev/blog/best-chunking-strategies-rag
- Databricks — Chunking guide — https://community.databricks.com/t5/technical-blog/the-ultimate-guide-to-chunking-strategies-for-rag-applications/ba-p/113089
- Anthropic — Contextual Retrieval — https://www.anthropic.com/news/contextual-retrieval

**Frameworks**
- LangChain / LangGraph — https://langchain-ai.github.io/langgraph/
- LlamaIndex — https://docs.llamaindex.ai/
- RAGAS — https://docs.ragas.io/
- Arize Phoenix — https://docs.arize.com/phoenix

---

*A note on the literature: chunking, reranking, and query-transformation benchmarks frequently disagree, and "best practice" shifts with embedding models and corpora. Treat every claim here as a hypothesis to validate against your own eval set rather than a settled constant.*
