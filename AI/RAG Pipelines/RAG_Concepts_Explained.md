# RAG Concepts — Explained (Primary Learning & Interview Reference)

> A framework-agnostic deep dive into every core concept behind Retrieval-Augmented Generation. Examples are in **Python 3** and kept library-light so the *idea* is clear, not the SDK. Read it top-to-bottom once; thereafter use the **Interview Rapid-Fire** section at the end as a pre-interview checkpoint.

**Conventions in this doc**
- "LLM" = the generator model. "Embedding model" = the encoder that turns text into vectors.
- Code is illustrative. Imports are shown once per concept; assume `import numpy as np` is available everywhere.

---

## 1. What RAG Is and the Problem It Solves

A bare LLM answers from **parametric knowledge** — everything baked into its weights at training time. That has three hard limits:

1. **Staleness** — it doesn't know anything after its cutoff.
2. **No private knowledge** — it has never seen your internal docs.
3. **Hallucination** — when unsure, it confidently makes things up.

**Retrieval-Augmented Generation** fixes this by fetching relevant text from an external store *at query time* and putting it into the prompt as context. The model then answers from that context (**non-parametric knowledge**) instead of guessing.

The mental model is **"open-book exam"**: instead of memorizing everything, the model looks up the relevant page before answering.

**Why RAG over fine-tuning?**
- Fine-tuning teaches *behavior/style*; RAG supplies *facts*.
- RAG knowledge updates instantly (re-index a doc) — no retraining.
- RAG gives **provenance** (you can cite the source chunk).
- They're complementary, not exclusive.

---

## 2. The Three Stages (The Spine of Everything)

Every RAG system, no matter how fancy, is built from three stages:

```
INDEXING (offline)        RETRIEVAL (online)         GENERATION (online)
documents                 user query                 query + context
   │                          │                           │
 load/parse               embed query                 build prompt
   │                          │                           │
 chunk                    search index (top-k)         LLM answers
   │                          │                           │
 embed                    (optional: rerank)          (cite sources)
   │                          │
 store in index ───────────►  retrieved chunks ──────►  answer
```

- **Indexing** happens offline/periodically. Quality here caps everything downstream — *garbage in, garbage out*.
- **Retrieval** finds the right context. This is where most quality is won or lost.
- **Generation** turns context into a grounded answer.

The **Naive → Advanced → Modular** taxonomy is just how much machinery you add around these three stages:
- **Naive RAG**: index → retrieve top-k → stuff into prompt. One shot.
- **Advanced RAG**: add pre-retrieval (query rewriting) and post-retrieval (reranking) optimizations.
- **Modular RAG**: swappable, orchestratable components — the conceptual bridge to Agentic RAG.

---

## 3. Ingestion — Loading & Parsing

Before chunking you must extract clean text. This is unglamorous and the source of many silent failures.

- **PDFs**: text-based PDFs extract cleanly; scanned PDFs need **OCR**. Multi-column layouts and tables frequently get mangled into nonsense word order.
- **HTML**: strip boilerplate (nav, footers) or you index junk.
- **Tables**: a table flattened to a text blob loses its structure. Consider converting to Markdown tables or serializing row-by-row.
- **Images/diagrams**: use a vision model to generate a text description ("verbalization") and index that.

**Key principle:** preserve structure (headings, tables, lists) for as long as possible — it's useful signal for chunking and for the LLM later.

```python
# Minimal idea: normalize text before chunking
def clean_text(raw: str) -> str:
    import re
    raw = re.sub(r"\s+\n", "\n", raw)      # trailing whitespace
    raw = re.sub(r"\n{3,}", "\n\n", raw)   # collapse blank lines
    return raw.strip()
```

---

## 4. Chunking Strategies

**Why chunk at all?** Embedding models have a max input length, retrieval works better on focused passages, and you don't want to blow the LLM's context window. But chunking is lossy: split badly and you fragment a single idea across chunks, or merge unrelated ideas into one.

**The central trade-off:** *small chunks* = precise retrieval but missing context; *large chunks* = rich context but noisy retrieval and wasted tokens.

### 4.1 Fixed-size / token-based
Split every N tokens. Simple, predictable, guarantees chunks fit your model. Blind to meaning — will cut a sentence in half.

```python
def fixed_chunks(text: str, size: int = 512, overlap: int = 64):
    words = text.split()
    step = size - overlap
    return [" ".join(words[i:i + size]) for i in range(0, len(words), step)]
```

**Overlap** (the `overlap` param) repeats a slice of the previous chunk so an idea straddling a boundary survives in at least one chunk. 10–20% is typical.

### 4.2 Recursive character splitting
Split on a *hierarchy* of separators — paragraph → sentence → word — only descending when a piece is still too big. This respects natural boundaries far better than fixed-size and is the **default workhorse**. (LangChain's `RecursiveCharacterTextSplitter` is the canonical implementation.)

### 4.3 Structure-aware splitting
Split on the document's own structure: Markdown headers, HTML tags, code functions. For well-structured docs this is often the **single biggest easy win** because each chunk is already a coherent unit, and you can attach the heading path as metadata.

### 4.4 Semantic chunking
Embed sentences, then start a new chunk when the embedding similarity to the running chunk drops below a threshold — i.e., split where the *topic* changes, not where a character count is hit.

```python
def semantic_split(sentences, embed_fn, threshold=0.7):
    # embed_fn(list[str]) -> np.ndarray of shape (n, d)
    embs = embed_fn(sentences)
    chunks, current = [], [sentences[0]]
    for i in range(1, len(sentences)):
        sim = cosine(embs[i], embs[i - 1])
        if sim < threshold:          # topic shift -> cut here
            chunks.append(" ".join(current)); current = []
        current.append(sentences[i])
    chunks.append(" ".join(current))
    return chunks

def cosine(a, b):
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
```

**Reality check:** semantic chunking costs an embedding call per sentence and several benchmarks find it *doesn't* reliably beat plain recursive chunking once you control for the embedding model. Use it for long, messy, multi-topic documents — and always measure.

### 4.5 LLM-based / agentic chunking
Ask an LLM to decide chunk boundaries (e.g., "split this into self-contained sections"). Highest quality, highest cost. Reserve for high-value corpora.

### 4.6 Practical defaults
Start with **recursive splitting, ~512 tokens, 10–20% overlap**. A practical working range is **~512–1024 tokens**; quality tends to degrade with very large chunks. Then measure and adjust per corpus.

---

## 5. Embeddings

An **embedding** maps text to a vector such that semantically similar texts land close together. "Closeness" is measured by a **similarity metric**.

### 5.1 Similarity metrics
- **Cosine similarity** — angle between vectors; ignores magnitude. The default for text.
- **Dot product** — cosine × magnitudes; used when embeddings are normalized (then it equals cosine).
- **Euclidean (L2) distance** — straight-line distance; smaller = closer.

```python
def cosine(a, b):
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
```

### 5.2 Dense embeddings (bi-encoders)
A neural encoder produces a single fixed-length vector (e.g., 384–3072 dims). Captures **meaning/semantics**, so "car" and "automobile" land near each other. This is what people mean by "vector search." The encoder is a **bi-encoder**: query and document are embedded *independently*, which is what makes precomputing document vectors possible.

### 5.3 Sparse embeddings
High-dimensional vectors where most entries are zero, with weights on actual terms.
- **BM25** — the classic keyword-relevance scoring (a refined TF-IDF). Excellent at **exact matches**: product codes, error IDs, names, rare jargon.
- **SPLADE** — a learned sparse representation that adds term expansion.

**Why you still need sparse:** dense models can miss exact tokens. On some domains (e.g., financial/numeric documents) BM25 *beats* state-of-the-art dense retrieval. Never assume semantic search always wins.

### 5.4 Multi-vector / late interaction (ColBERT)
Instead of one vector per chunk, store **one vector per token** and compute fine-grained token-level similarity at query time ("late interaction"). More precise than a single vector, far cheaper than a cross-encoder. The cost is storage (many vectors per chunk).

### 5.5 Choosing an embedding model
Consider: domain fit, language(s), max sequence length, output dimensionality (cost/storage), and current benchmark standing (the **MTEB** leaderboard — but verify on *your* data). The embedding model choice often matters as much as the chunking strategy.

---

## 6. Vector Stores & Approximate Nearest Neighbor (ANN) Search

Once everything is a vector, retrieval = "find the k vectors most similar to the query vector." Doing this exactly (comparing against every vector) is **O(N)** and too slow at scale. **ANN** algorithms trade a little recall for huge speedups.

### 6.1 Brute force (exact) — the baseline to understand
```python
def brute_force_topk(query_vec, doc_vecs, k=5):
    sims = doc_vecs @ query_vec            # assumes normalized vectors
    idx = np.argsort(-sims)[:k]
    return idx, sims[idx]
```

### 6.2 HNSW (Hierarchical Navigable Small World)
A multi-layer graph you greedily traverse toward the query. Fast, high recall, the most common production choice. Key tunables:
- `M` — edges per node (higher = better recall, more memory)
- `efConstruction` / `efSearch` — how hard it works while building / searching (higher = better recall, slower)

### 6.3 IVF (Inverted File Index)
Cluster vectors first; at query time only search the few nearest clusters (`nprobe` of them). Memory-efficient; recall depends on `nprobe`. Often combined with **PQ (Product Quantization)** to compress vectors (`IVF-PQ`).

### 6.4 The trade-off triangle
Every ANN setup balances **recall ↔ latency ↔ memory**. You tune toward whichever your use case can least afford to lose.

```python
# FAISS sketch (pip install faiss-cpu)
import faiss
d = 384
index = faiss.IndexHNSWFlat(d, 32)   # 32 = M
index.hnsw.efSearch = 64
index.add(doc_vecs.astype("float32"))
D, I = index.search(query_vec.reshape(1, -1).astype("float32"), k=5)
```

---

## 7. Indexing & Metadata

The **index** stores vectors plus **metadata** (source, title, date, section, access tags). Metadata enables:
- **Filtering**: "only docs from 2024," "only this product line." Combine filters with vector search (**hybrid filter+vector**).
- **Security trimming**: filter out chunks the user isn't allowed to see — *at retrieval time*.
- **Provenance**: cite the exact source.

**Pre- vs. post-filtering gotcha:** filtering *before* ANN can break the graph traversal and hurt recall; filtering *after* may leave you with too few results. Know which your store does.

```python
chunk = {
    "id": "doc42#chunk7",
    "text": "...",
    "vector": vec,
    "metadata": {"source": "handbook.pdf", "section": "PTO", "year": 2024,
                 "acl": ["hr", "managers"]},
}
```

---

## 8. Retrieval — Retriever Types & Fusion

### 8.1 The three retriever families
- **Dense retriever** — vector similarity; great at semantics, weak at exact tokens.
- **Sparse retriever** — BM25/SPLADE; great at exact tokens, weak at paraphrase.
- **Hybrid retriever** — run both and **fuse** the results. Best of both worlds and the strong default.

### 8.2 Reciprocal Rank Fusion (RRF)
The standard way to merge ranked lists from different retrievers without needing comparable scores. It uses only the *rank* of each item in each list:

```python
def rrf(rank_lists, k=60):
    # rank_lists: list of lists of doc_ids, each ordered best->worst
    scores = {}
    for lst in rank_lists:
        for rank, doc_id in enumerate(lst):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores, key=scores.get, reverse=True)
```

`k` (commonly 60) dampens the influence of top ranks so a doc that appears in *several* lists can outrank one that's #1 in a single list. RRF is robust precisely because it ignores raw scores (which live on incomparable scales).

### 8.3 Maximal Marginal Relevance (MMR)
Top-k by pure similarity often returns near-duplicates. **MMR** balances relevance against **diversity** so the context isn't five copies of the same sentence:

```python
def mmr(query_vec, cand_vecs, cand_ids, k=5, lam=0.7):
    selected, selected_idx = [], []
    remaining = list(range(len(cand_ids)))
    sim_q = cand_vecs @ query_vec
    while len(selected) < k and remaining:
        best, best_score = None, -1e9
        for i in remaining:
            redundancy = max([cand_vecs[i] @ cand_vecs[j] for j in selected_idx], default=0.0)
            score = lam * sim_q[i] - (1 - lam) * redundancy
            if score > best_score:
                best, best_score = i, score
        selected.append(cand_ids[best]); selected_idx.append(best); remaining.remove(best)
    return selected
```

`lam=1` → pure relevance; `lam=0` → pure diversity.

---

## 9. Query Transformation (Pre-Retrieval)

**The core insight:** users write *questions*, but your corpus contains *answers*, and they sit in different regions of embedding space. Transform the query before retrieving to bridge that gap.

### 9.1 HyDE (Hypothetical Document Embeddings)
Ask the LLM to *write a hypothetical answer* to the question, then embed and search with **that**. The fake answer looks more like a real document than the question does, so it retrieves better.

```python
def hyde(query, llm, embed_fn):
    hypothetical = llm(f"Write a short passage that answers: {query}")
    return embed_fn([hypothetical])[0]   # search with this vector
```

### 9.2 Multi-query
Generate 3–5 paraphrases of the question, retrieve for each, and union (often via RRF). Improves recall when the user's phrasing is just one of many ways to ask.

### 9.3 Step-back prompting
Turn a narrow question into a broader one ("What's our PTO policy for remote hires after 2023?" → "What is the PTO policy?"), retrieve the general context, then answer the specific question. Helps when the specific answer needs surrounding principle.

### 9.4 Decomposition & routing
- **Decomposition**: split a multi-part question into sub-questions, retrieve for each, combine.
- **Routing**: classify the query and send it to the right index/tool (docs vs. SQL vs. web).

**Gotcha:** HyDE and multi-query boost recall on broad/ambiguous questions but give **little benefit on precise lookup/numeric queries** — apply selectively.

---

## 10. Reranking (Post-Retrieval)

First-stage retrieval optimizes for **speed over a huge corpus**, so it returns a *candidate* set with some noise. A **reranker** re-scores those candidates with a slower but far more accurate model, then you keep the top few.

### 10.1 Bi-encoder vs. cross-encoder (the key distinction)
- **Bi-encoder** (your retriever): embeds query and doc *separately* → fast, precomputable, less accurate.
- **Cross-encoder** (your reranker): feeds query **and** doc *together* through the model → sees their interaction → much more accurate, but can't be precomputed (must run per pair at query time).

```python
# Cross-encoder rerank (pip install sentence-transformers)
from sentence_transformers import CrossEncoder
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query, candidates, top_n=3):
    pairs = [(query, c["text"]) for c in candidates]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return [c for c, _ in ranked[:top_n]]
```

### 10.2 The two-stage pattern
**Retrieve top-k (e.g. 50) cheaply → rerank → keep top-3.** This consistently beats single-stage retrieval by a wide margin and is the standard advanced-RAG recipe.

### 10.3 "Lost in the middle"
LLMs attend most to the **start and end** of their context and can miss facts buried in the middle. Reranking helps by placing the strongest evidence where the model actually looks. Practical move: put the best chunk first (or first *and* last).

### 10.4 When to skip reranking
Tiny curated corpora (vector sim is already precise), or hard sub-500ms latency budgets.

---

## 11. Augmentation & Generation

Retrieval gets the right text in front of the model; **augmentation** decides how it's presented, and **generation** produces the answer.

### 11.1 Prompt assembly
```python
def build_prompt(query, chunks):
    context = "\n\n".join(f"[{i+1}] {c['text']}" for i, c in enumerate(chunks))
    return f"""Answer the question using ONLY the context below.
If the answer isn't in the context, say "I don't know."
Cite sources by their bracket number.

Context:
{context}

Question: {query}
Answer:"""
```

Key choices live here: ordering (best first), deduplication, **context compression** (summarize chunks to fit the window), and how many chunks to include (more is not always better — noise hurts).

### 11.2 Grounding, citations, abstention
- **Grounding**: instruct the model to use *only* the provided context.
- **Citations**: have it reference chunk IDs so answers are traceable.
- **Abstention**: explicitly allow "I don't know" — this is how you cut hallucinations when retrieval comes up empty.

### 11.3 Retrieved content is untrusted input
A document can contain text like "ignore previous instructions…" — a **prompt injection** delivered through your own corpus. Defend in the system prompt and treat retrieved text as data, not instructions.

---

## 12. Advanced Retrieval Patterns

These decouple **what you search on** from **what you feed the LLM** — small, precise units for retrieval; richer units for generation.

- **Sentence-window retrieval**: embed/retrieve single sentences (precise), then expand to a window of surrounding sentences before generation (context).
- **Parent-document / small-to-large**: index small child chunks; on a hit, return the larger parent chunk.
- **Auto-merging (hierarchical)**: index a tree of chunks; if enough sibling leaves are retrieved, merge up to the parent automatically.
- **Contextual retrieval**: before embedding each chunk, prepend an LLM-generated sentence situating it in the whole document ("This chunk is from the 2024 handbook, PTO section…"). Substantially reduces retrieval failures from ambiguous chunks.
- **Late chunking**: embed the *whole* document first so every token's embedding carries full-document context, *then* pool into chunk vectors. Helps when chunks are meaningless in isolation (pronouns, dangling references).

---

## 13. GraphRAG

Flat vector retrieval struggles with **multi-hop** questions ("How is A connected to C?") and **global** questions ("Summarize the main themes across all docs"), because the answer isn't in any single chunk — it's in the *relationships*.

**GraphRAG** builds a **knowledge graph** (entities = nodes, relationships = edges) from your corpus, then retrieves subgraphs / paths / community summaries instead of (or alongside) text chunks. Three stages mirror normal RAG:
- **Graph indexing**: extract entities & relations (often with an LLM), build the graph, optionally cluster into communities and pre-summarize them.
- **Graph-guided retrieval**: traverse the graph for nodes/paths/subgraphs relevant to the query.
- **Graph-enhanced generation**: feed structured relational context to the LLM.

**Use it for:** multi-hop reasoning, "connect the dots" questions, and global summarization. **Cost:** graph construction is expensive and complex — don't reach for it unless flat RAG demonstrably falls short.

---

## 14. Agentic RAG

The leap: stop treating RAG as **"one query → one retrieval → one answer"** and wrap retrieval in a **decision-making loop** run by an LLM agent. The model stops being a passive consumer of chunks and becomes an active researcher.

### 14.1 The four capabilities that make RAG "agentic"
1. **Decide *whether* to retrieve** — simple questions can be answered from parametric knowledge; only retrieve when needed.
2. **Grade relevance** — score retrieved docs; discard the weak ones.
3. **Rewrite the query** — when retrieval fails, reformulate and try again.
4. **Loop** — repeat retrieve → grade → refine until evidence is sufficient (or give up gracefully).

The underlying agent design patterns: **reflection, planning, tool use, multi-agent collaboration**.

### 14.2 The taxonomy (know these names)
- **Single-agent / router**: one agent picks the source or tool per query.
- **Multi-agent / hierarchical**: specialist agents under an orchestrator.
- **Corrective RAG (CRAG)**: grade retrieved docs; if poor → correct via query rewrite or **web search fallback**.
- **Self-RAG**: the model emits "reflection tokens" deciding when to retrieve and whether its own output is supported by evidence (best when you can fine-tune; approximate via structured prompting on closed APIs).
- **Adaptive RAG**: route by query complexity — trivial → answer directly; moderate → single retrieval; complex → multi-step.

### 14.3 A CRAG-style loop in pseudocode
```python
def agentic_rag(query, retriever, llm, web_search, max_loops=3):
    for _ in range(max_loops):
        docs = retriever(query)
        graded = [d for d in docs if grade_relevance(llm, query, d) > 0.5]

        if len(graded) >= 2:                      # enough good evidence
            return generate(llm, query, graded)

        if len(graded) == 0:                      # retrieval failed
            query = rewrite_query(llm, query)     # ...try a better query
            if still_failing():                   # ...or fall back to web
                graded = web_search(query)
                return generate(llm, query, graded)
    return generate(llm, query, graded or [])     # graceful degradation

def grade_relevance(llm, query, doc):
    ans = llm(f"Is this relevant to '{query}'? Answer 0-1.\n{doc['text']}")
    return float(ans.strip())
```

**Trade-off:** agentic loops dramatically improve hard/multi-step questions but add **latency and token cost** (multiple LLM calls per answer). Use complexity routing so you only pay for it when needed.

---

## 15. Evaluation

You cannot improve what you don't measure. RAG eval splits cleanly into **retrieval quality** and **generation quality**.

### 15.1 Retrieval metrics
- **Recall@k** — fraction of relevant docs that appear in the top-k. (Did we *find* the evidence?)
- **Precision@k** — fraction of top-k that are relevant. (Is the context *clean*?)
- **MRR (Mean Reciprocal Rank)** — 1/rank of the first relevant doc, averaged. (Is the best doc *near the top*?)
- **nDCG** — rewards putting more-relevant docs higher; handles graded relevance.
- **Hit Rate** — was at least one relevant doc retrieved?

```python
def recall_at_k(retrieved_ids, relevant_ids, k):
    top = set(retrieved_ids[:k])
    return len(top & set(relevant_ids)) / len(relevant_ids)

def mrr(retrieved_ids, relevant_ids):
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0
```

### 15.2 The RAG Triad (generation quality)
Three LLM-judged metrics covering the whole pipeline:
1. **Context Relevance** — are the retrieved chunks relevant to the question? *(diagnoses retrieval)*
2. **Groundedness / Faithfulness** — is the answer actually supported by the retrieved context (vs. hallucinated)? *(diagnoses generation)*
3. **Answer Relevance** — does the answer address the question? *(diagnoses the final output)*

If an answer is bad, the triad tells you *which stage* to fix.

### 15.3 LLM-as-judge & test sets
- Build a **golden set** of question→relevant-chunk→ideal-answer triples from your own corpus (can be LLM-generated, then human-reviewed).
- Frameworks like **RAGAS** automate the triad and more.
- Watch LLM-judge **pitfalls**: position bias, verbosity bias, and the need for calibration.

### 15.4 Put eval in CI
Gate deploys on triad/retrieval-metric thresholds so a chunking or prompt change can't silently regress quality.

---

## 16. Production Concerns

- **Security**: filter chunks by access tags at retrieval time (security trimming); prefer identity-based auth over static API keys; never index secrets you can't access-control.
- **Prompt injection**: retrieved/3rd-party content is untrusted; sanitize and instruct the model to ignore embedded instructions.
- **Cost**: tokens dominate — embedding (one-time-ish), reranking (per query), generation (per query). Cache aggressively; skip reranking when it doesn't pay.
- **Latency**: two-stage retrieval + agentic loops add round-trips; budget them. Stream the answer.
- **Caching**: cache embeddings, retrieval results for repeated queries, and even generations (semantic cache).
- **Freshness**: incremental indexing; decide a re-embedding policy when the embedding model changes (you must re-embed *everything* — vectors from different models aren't comparable).
- **Observability**: trace each stage (latency, cost, retrieved IDs) so you can debug a bad answer to its root stage.

---

## 17. Common Failure Modes (and the Fix)

| Failure | Symptom | Fix |
|---|---|---|
| Missing content | Answer just isn't in the corpus | Improve coverage; allow "I don't know" |
| Bad chunking | Relevant idea split/diluted | Better chunk strategy & size; structure-aware splitting |
| Retrieval miss | Right doc exists but isn't retrieved | Hybrid search, query transformation, better embeddings |
| Ranking gap | Relevant doc retrieved but ranked low | Add a reranker |
| Context overflow | Too many chunks, model ignores some | Fewer/better chunks; reranking; compression |
| Not extracted | Answer in context but model misses it | Lost-in-the-middle → reorder; prompt tuning |
| Wrong format | Answer correct but malformed | Output formatting instructions / structured output |
| Hallucination | Confident but unsupported answer | Grounding prompt, abstention, faithfulness eval |

---

## 18. Interview Rapid-Fire (Self-Quiz Before You Walk In)

Cover the answer, recall it, then check.

- **What are RAG's three stages?** Indexing, Retrieval, Generation.
- **RAG vs. fine-tuning?** RAG = facts + freshness + provenance, no retraining; fine-tuning = behavior/style. Complementary.
- **Bi-encoder vs. cross-encoder?** Bi-encoder embeds query & doc separately (fast, used for retrieval); cross-encoder processes them together (accurate, used for reranking, can't precompute).
- **Why hybrid search?** Dense catches semantics, sparse/BM25 catches exact tokens; fuse with RRF.
- **What is RRF and why use ranks not scores?** Reciprocal Rank Fusion merges ranked lists using `1/(k+rank)`; ranks are comparable across retrievers, raw scores are not.
- **HyDE in one line?** Generate a hypothetical answer, embed *that* instead of the question, because answers resemble documents more than questions do.
- **Chunking default?** Recursive, ~512 tokens, 10–20% overlap; measure before going semantic.
- **HNSW vs. IVF?** HNSW = navigable graph (fast, high recall, more memory); IVF = cluster-and-probe (memory-efficient, recall via `nprobe`).
- **Cosine vs. dot vs. L2?** Cosine = angle (default); dot = cosine when normalized; L2 = distance.
- **"Lost in the middle"?** LLMs under-attend to the middle of long context; reorder so key evidence is at the ends.
- **The RAG triad?** Context Relevance, Groundedness/Faithfulness, Answer Relevance — they localize which stage failed.
- **Recall@k vs. MRR?** Recall@k = did we find the relevant docs in top-k; MRR = how high the first relevant doc ranks.
- **MMR solves what?** Redundant near-duplicate results — it trades relevance for diversity.
- **What makes RAG "agentic"?** The model decides *whether* to retrieve, *grades* results, *rewrites* failed queries, and *loops*.
- **CRAG vs. Self-RAG vs. Adaptive RAG?** CRAG = grade + correct (web fallback); Self-RAG = reflection tokens decide retrieval/support; Adaptive = route by query complexity.
- **When GraphRAG?** Multi-hop / "connect the dots" / global-summary questions where the answer lives in relationships, not a single chunk.
- **Two biggest prod risks?** Prompt injection via retrieved content; cost/latency from rerankers + agentic loops.
- **Why re-embed everything when you swap embedding models?** Vectors from different models live in different spaces and aren't comparable.

---

## Glossary (Quick Reference)

- **ANN** — Approximate Nearest Neighbor search (HNSW, IVF).
- **BM25** — classic keyword relevance scoring (sparse).
- **Bi-encoder / Cross-encoder** — separate vs. joint encoding of query+doc.
- **Chunk** — a unit of text that gets embedded and retrieved.
- **CRAG** — Corrective RAG (grade + correct retrieval).
- **Embedding** — vector representation of text.
- **Grounding** — answering only from provided context.
- **HyDE** — Hypothetical Document Embeddings (query transformation).
- **MMR** — Maximal Marginal Relevance (relevance + diversity).
- **MRR / nDCG / Recall@k** — retrieval ranking metrics.
- **Parametric vs. non-parametric knowledge** — in the weights vs. retrieved at runtime.
- **RAG Triad** — Context Relevance, Groundedness, Answer Relevance.
- **Reranker** — second-stage model that re-scores candidates (usually a cross-encoder).
- **RRF** — Reciprocal Rank Fusion (merge ranked lists).
- **Self-RAG** — model self-evaluates when to retrieve and whether output is supported.
- **Sparse / Dense / Multi-vector** — keyword / semantic / per-token retrieval.

---

*Companion file: see the RAG Pipeline Learning Roadmap for the ordered study path and curated external resources. This document is the "what & why"; the roadmap is the "in what order, and where to go deeper."*
