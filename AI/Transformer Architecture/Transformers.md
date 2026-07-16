<h1 align="center">Transformers — DeepLearning.AI Notes</h1>

<hr style="border:none;height:3px;background:linear-gradient(to right, #00bcd4, #673ab7);">

> **Question**
>REQUIREMENT:
>I want you to explain every essential component in the transformer architecture diagram.
Explain details with good diagrams: Tokenization, Input & Positional Encoding, Self-Attention, Multi-Head Attention and Embeddings.

**Data-flow order** (which is exactly bottom-to-top in your Image 1): tokenization → embeddings → positional encoding → self-attention → multi-head attention → the full architecture. 

---
**Transformer Actual**
![alt text](images/transformers.png)


# 0. Orientation — the pipeline

Before the components, the mental model a senior engineer carries (maps to your Image 3):

- **Text is never fed to the model.** It's turned into numbers in stages: `text → tokens → token IDs → embeddings (+ position) → attention layers → output probabilities`.
- **Encoder** = *understands* input (bidirectional). **Decoder** = *generates* output (left-to-right, masked).
- **Three families**, and this is a favorite interview fork:
  - **Encoder-only** (BERT) → understanding tasks: classification, embeddings, retrieval.
  - **Decoder-only** (GPT, Llama, Claude, most LLMs) → generation.
  - **Encoder-decoder** (T5, original Transformer, your Image 1) → sequence-to-sequence: translation, summarization.
- **Production note (Azure):** the GPT models behind Azure OpenAI are **decoder-only**. The full encoder-decoder in your Image 1 is the *original* 2017 design — worth knowing, but most LLM work today is the right-hand (decoder) tower.

**Transformer Simplified**
![alt text](images/simplified_transformer.png)
---

# 1. Tokenization

### Definition
> **Tokenization** = splitting raw text into discrete units (**tokens**) and mapping each to an integer **ID** from a fixed **vocabulary**. It is the boundary between human text and model math.


### The three approaches (and why subword won)
- **Word-level** → huge vocabulary, can't handle unseen words (`OOV` problem). ❌
- **Character-level** → tiny vocab, but sequences become very long and semantics are weak. ❌
- **Subword (BPE / WordPiece / SentencePiece)** → **the standard.** Frequent words stay whole; rare words break into reusable pieces.

![alt text](images/tokenization.png)

![alt text](images/image.png)

### Why it matters in production
- **Cost & context = tokens, not words.** Billing and context-window limits are per token (~4 chars / ~0.75 words in English). Non-English and code often tokenize *worse* (more tokens per word) → higher cost, faster context exhaustion.
- **Rule of thumb:** ~750 words ≈ 1,000 tokens for English prose.

### Interview Q&A
> **Scenario:** *A client complains their Azure OpenAI bill is high for a summarization feature, mostly on German legal text.*
- **Q: Why is German more expensive than English here?**
  **A:** Tokenizers are trained mostly on English, so German (long compound words) and specialized legal terms fragment into more subword tokens per word. More tokens → more cost and faster context-limit hits. I'd measure the actual token-per-word ratio, consider trimming boilerplate before sending, and evaluate whether a model with a tokenizer better suited to the language reduces token count.

---

# 2. Embeddings

### Definition
> An **embedding** is a lookup table that turns each token ID into a **dense vector** (e.g. 768 or 1536 floats) representing a token's *meaning* in a continuous space. The token ID is just an index; the embedding is the actual signal the model reasons over. This vector is the token's meaning, expressed as geometry.

### Key distinctions (high-value in interviews)
- **One-hot vs embedding:** one-hot is sparse, huge, and carries *no* similarity ("king" and "queen" are equally unrelated). Embeddings are dense and place **similar meanings close together**.
- **Static token embedding vs contextual embedding — critical:**
  - The **input embedding** (lookup table) is *static* — "bank" has one vector regardless of sentence.
  - After passing through attention layers, the representation becomes **contextual** — "bank" (river) and "bank" (money) end up in *different* places. **Attention is what makes embeddings context-aware.**
- **Distinction — two different things called "embeddings"**:
  - Token embeddings = internal input layer of the LLM (what we're describing here).
  - Sentence/document embeddings = the vector for a whole chunk, used in RAG for similarity search in a vector DB. Same idea, different granularity. (This is the bridge to your RAG background — cosine similarity in a vector store is exactly "meaning as distance.")
  
  ![alt text](images/embeddings.png)
  
  ### When & why (use-case)
- **Similarity/search/RAG:** embed documents and queries, compare by **cosine similarity** → semantic search, retrieval, clustering, dedup, recommendations. This is the backbone of your RAG systems.
- **Distinction to state cleanly:** *token embeddings* (inside an LLM) vs *sentence/document embeddings* (from a dedicated embedding model like `text-embedding-3-large`). RAG uses the latter.

### Interview Q&A
> **Scenario:** *Your RAG retrieval returns irrelevant chunks even though keywords match.*
- **Q: How could embeddings be the culprit?**
  **A:** Keyword overlap ≠ semantic match. If chunks are too long, one embedding averages many topics and blurs meaning; if the embedding model is weak or domain-mismatched (e.g. general model on medical text), similar-meaning terms won't land close. I'd right-size chunks, use a domain-appropriate embedding model, and evaluate retrieval (recall@k) *separately* from generation.

---

# 3. Input & Positional Encoding

### The problem it solves
 - Self-attention looks at all tokens simultaneously, so by itself it has no sense of word order — "dog bites man" and "man bites dog" would look identical. Recurrence encoded order for free; the Transformer threw recurrence away, so order must be injected manually.

### Definition 
- Positional encoding (PE) adds a position-dependent vector to each token embedding, so the final input carries both meaning and position.

Input to encoder = Token Embedding + Positional Encoding (element-wise addition, same dimension)

### How it works
- Add a **position vector** to each token embedding (same dimension), **element-wise**:
  `input = token_embedding (meaning) + positional_encoding (order)`
- **Sinusoidal (original Transformer)** — fixed sine/cosine waves of varying frequency:

```
PE(pos, 2i)   = sin( pos / 10000^(2i / d_model) )
PE(pos, 2i+1) = cos( pos / 10000^(2i / d_model) )
```

![alt text](images/positional_encoding.png)

![alt text](images/image-1.png)

### Distinction: sinusoidal vs learned vs RoPE
- **Sinusoidal (fixed):** no parameters; can extrapolate to longer sequences; original design.
- **Learned absolute:** positions are trainable embeddings; simple, used by BERT/GPT-2; poor at extrapolating beyond trained length.
- **RoPE (Rotary Position Embedding) — what modern LLMs use (Llama, most 2023+ models):** rotates Q/K by position so attention depends on *relative* distance. 
It is a technique used in modern Large Language Models (LLMs) to encode word order. Instead of simply adding a position value to a word's meaning, RoPE acts like a compass by geometrically rotating the model's Query and Key vectors in multi-dimensional space based on their position in the sequence.
**Better long-context generalization** — this is the answer that signals you're current.

### Interview Q&A
> **Scenario:** *A model trained on 4k-token inputs degrades badly at 16k tokens.*
- **Q: What's likely happening and how do positional schemes relate?**
  **A:** The model is seeing positions it never trained on. With learned absolute positions it can't represent them at all. This is why long-context models use RoPE (often with scaling tricks like NTK/YaRN) — relative position generalizes better. Practically, I'd either use a model natively trained for that context length or apply a validated context-extension method rather than assuming it "just works."

---

# 4. Self-Attention *( the heart of the Transformer )*

### Definition
 **Self-attention** is a machine learning mechanism that allows a model to evaluate the relationships between all words (or tokens) within the same sequence. It lets every token look at every other token in the sequence and build a new representation as a **relevance-weighted blend** of them. It's how the model figures out *which words matter to which*.

**Definition:** A mechanism where every token builds a new representation of itself as a weighted blend of all other tokens, where the weights encode relevance. It answers, for each word: "which other words should I pay attention to, and how much?"

### The Q / K / V intuition
Each token projects into three learned vectors:

**Calculate Q, K, and V vectors**: 
- Every word's embedding is transformed into three distinct vectors using trained weight matrices:
- Query (Q): Represents the word the model is currently focusing on.
- Key (K): Represents all other words in the sentence being evaluated as reference points.
- Value (V): The actual content or meaning of the word | the actual content I'll hand over if you attend to me

| Vector | Role | Plain-English question |
|---|---|---|
| **Query (Q)** | what I'm looking for | Represents the word the model is currently focusing on - "what's relevant to *me*?" |
| **Key (K)** | what I offer | Represents all other words in the sentence being evaluated as reference points - "here's what *I'm* about" |
| **Value (V)** | my actual content | The actual content or meaning of the word - "here's my information to share" |

**Mechanism (say it in 4 steps):**
1. **Q · Kᵀ → raw relevance Score** = each token's Query · every token's Key (dot product → relevance).
2. **÷ √dₖ → Scale** (keeps gradients stable — large dimensions blow up dot products).
3. **Softmax →** scores become weights summing to 1.
4. **· V → Weighted sum of Values** → the token's new, context-aware representation.

### The formula (memorize this exactly)

```
Attention(Q, K, V) = softmax( Q · Kᵀ / √d_k ) · V
```

![alt text](images/image-3.png)

Here's the graphic in your attached arc style — **amber = strong attention, gray = weaker learned links**. "taught" attends most to its subject "teacher" and object "student":

![alt text](images/self-attention.png)

![alt text](images/image-2.png)

### Two variants you must distinguish
- **Full (bidirectional) self-attention** — encoder: every token sees every other token. Used for *understanding*.
- **Masked (causal) self-attention** — decoder: a token can only see tokens *before* it (future positions masked to −∞ before softmax). This is what makes generation left-to-right and prevents "cheating" by peeking at the answer.

### The cost caveat (senior signal)
> Attention is **O(n²)** in sequence length — every token attends to every token. Doubling context ≈ 4× the compute. This is *the* reason long-context and efficient-attention work (FlashAttention, RoPE, KV-caching, sparse/sliding-window attention) exists.

### Interview Q&A
> **Scenario:** *A teammate asks why the decoder needs "masking" but the encoder doesn't.*
- **Q: Explain the difference and why it matters.**
  **A:** The encoder reads the whole input at once, so bidirectional attention is fine — understanding benefits from seeing both sides. The decoder *generates* one token at a time; if it could see future tokens during training it would trivially cheat, and it wouldn't match inference where the future doesn't exist yet. Causal masking enforces that each position only attends to itself and earlier positions, keeping training and generation consistent.

---

# 5. Multi-Head Attention

### Definition
> Instead of computating attention **once**, run **h times parallel**, each head has its *own* learned Q/K/V projections, then **concatenate** and **linearly project** the results.

### Why (the core intuition)
- One head = **one relationship lens**. One point of view. A single head is forced to average all relationship types together.
Multiple heads let the model attend to **different relationship types simultaneously**:
  - one head → subject-verb links,
  - another → coreference ("it" → "animal"),
  - another → long-range topic.
- Analogy: reading a sentence with several experts — a grammarian, a fact-checker, a tone-reader — each annotating in parallel, then merging notes.
- Each head works in a **smaller subspace** (`d_model / h`), so total cost ≈ one full-size attention — you get diversity *for free*.
- **One-liner:** Multi-head attention lets the model attend to information from different representation subspaces at once.

![alt text](images/image-4.png)

### Interview Q&A
> **Scenario:** *Someone proposes "just use one big attention head instead of many small ones — simpler."*
- **Q: Why is multi-head usually better?**
  **A:** A single head must average all relationship types into one attention pattern, so competing signals (syntax vs coreference vs topic) blur together. Splitting into heads lets each specialize in a different subspace and pattern, then the results are combined — richer representations at essentially the same compute. Empirically it's why the original paper used multi-head; collapsing to one head measurably hurts quality.

---

# 6. Full architecture — every component (your Image 1)

Reading **bottom-to-top**, here's every box and what it does. The stack repeats **N times** (e.g. 12, 24, 96 layers).

### Shared bottom (both towers)
- **Input / Output Embedding** — token IDs → dense vectors (Section 2).
- **Positional Encoding (⊕)** — add order to meaning (Section 3).

### Encoder layer (left tower) — *understands the input*
- **Multi-Head Attention** — full/bidirectional self-attention over the input (Sections 4–5).
- **Add & Norm** — two mechanisms bundled:
  - **Add = residual connection** (`x + sublayer(x)`) → lets gradients flow through deep stacks; without it, deep Transformers won't train.
  - **Norm = layer normalization** → stabilizes activations, speeds/steadies training.
- **Feed Forward (FFN)** — a per-token 2-layer MLP (expand → non-linearity → contract). **This is where most parameters live** and where a lot of "knowledge" is stored; attention mixes tokens, the FFN *processes* each one.
- Another **Add & Norm**.

### Decoder layer (right tower) — *generates the output*
- **Masked Multi-Head Attention** — causal self-attention; can't see future tokens (Section 4).
- **Add & Norm.**
- **Multi-Head Attention (cross-attention)** — **the bridge**: Queries come from the decoder, **Keys & Values come from the encoder output**. This is how the output attends to the input (e.g. each generated word looks at the source sentence in translation).
- **Add & Norm** → **Feed Forward** → **Add & Norm.**

### Top (output head)
- **Linear** — projects the final vector to **vocabulary size** (one score/logit per possible token).
- **Softmax** — logits → **probability distribution** over the vocabulary → **Output Probabilities**. Decoding (greedy / top-k / top-p / temperature) picks the next token from this.### The three families — when to use each (production framing)

| Family | Uses | Best for | Real models |
|---|---|---|---|
| **Encoder-only** | Encoder + bidirectional attn | understanding: classification, **embeddings/retrieval** | BERT, `text-embedding-3` |
| **Decoder-only** | decoder stack, masked attention, **no cross-attention** | **generation, chat, most LLMs** | GPT-4o, Llama, Claude |
| **Encoder-decoder** | both towers + cross-attention | seq-to-seq: translation, summarization | T5, original Transformer |

### **The three components that trip people up**

- **Add & Norm** = Residual + LayerNorm. **Residuals** let gradients flow through very deep stacks (no vanishing); **LayerNorm** keeps activations stable. Without these, you can't train a deep Transformer at all.
- **Masked (causal) attention**. During generation, a token must not see the future — otherwise it's cheating by peeking at the answer. The mask sets future positions to −∞ before softmax. **This is the single feature that makes generation possible.**
- **Cross-attention** is the only place the decoder reads the encoder. Remove it and you have a decoder-only model.

**Key realization for interviews:** decoder-only LLMs (what you'll use on Azure OpenAI) **drop the encoder and cross-attention entirely** — they're just the masked-attention → FFN block stacked deep. The full two-tower diagram is the *original* design; know it, but don't assume every LLM has an encoder.

### Interview Q&A
> **Scenario:** *A client wants (a) semantic search over their knowledge base and (b) a chatbot that answers from it. An architect suggests "one big model for both."*

**Q1 — How do the architecture families guide your design?**
  - **A:** These are two different jobs. Search needs an **encoder-style embedding model** to turn documents and queries into vectors for similarity — that's understanding, not generation. The chatbot needs a **decoder-only generative LLM**. So I'd use an embedding model for retrieval and a separate generative model for answering — i.e. RAG: embed + retrieve, then generate grounded on the results. Forcing one model to do both is the wrong tool for at least one of the tasks.

**Q2 (follow-up) —  Why don't decoder-only LLMs have cross-attention if the encoder-decoder does?**
  - **A:** Cross-attention exists to let a *separate* output sequence attend to a *separate* encoded input. A decoder-only LLM has no separate input sequence — the prompt and the generation are one continuous stream, so causal self-attention over that single stream already lets generated tokens attend to the prompt. No second tower means no bridge needed.


>**Scenario:** You're explaining to a stakeholder why your Azure-hosted chatbot has a token limit and why long documents cost more — grounding it in the architecture.

**Q3 — "Why is there a hard context limit at all?"**
  - Self-attention is O(n²): every token attends to every other, so doubling the input roughly quadruples attention compute and memory. The limit is where quality, latency, and cost stay acceptable — not an arbitrary cap.

**Q4 — "The same paragraph costs different amounts on different days — why?"**
  - Billing is per token, and tokenization is subword — rare words, code, and other languages fragment into more tokens than plain English. Same visible text, different token count. I'd measure real usage with tiktoken, not word count.

**Q5 — "Why does the model sometimes lose track of instructions early in a long prompt?"**
  - Two forces: attention weight spreads thinner across many tokens, and models show a "lost in the middle" bias — strongest recall at the start and end of context. Mitigation: put critical instructions at the top or bottom, and for long docs use RAG to feed only relevant chunks instead of the whole thing.
---

That's the full bottom-to-top path with every component in your Image 1 covered, formulas where they matter, and a scenario Q&A per section.

Natural next steps from here, whenever you want them: **the FFN / MoE internals**, **decoding strategies** (greedy vs top-k vs top-p vs temperature — high-yield for product roles), **KV-cache** (why inference is fast and why context costs memory), or moving up the stack into **RAG architecture** and **evaluation**.

<hr style="border:none;height:3px;background:linear-gradient(to right, #00bcd4, #673ab7);">

> **Question**