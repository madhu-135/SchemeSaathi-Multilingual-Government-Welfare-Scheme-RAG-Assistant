# SchemeSaathi Optimization Experiments Comparison 🧪

**Evaluation Set**: 40 Questions (15 English In-Scope, 15 Tamil In-Scope, 10 Out-of-Scope)  
**Model**: `intfloat/multilingual-e5-small` (L2 Normalized Cosine Distance)

---

## 📊 Consolidated Experiments Matrix

| Experiment | Parameter Tested | Hit@3 (%) | Hit@1 (%) | Page Match (%) | Citation Rate (%) | Out-of-Scope Not-Found (%) | Avg Latency (ms) |
|---|---|---|---|---|---|---|---|
| **Baseline** | $K=4, \tau=0.80$ | **100.0%** (30/30) | 83.33% (25/30) | **100.0%** | 76.67% (23/30) | **100.0%** (10/10) | 22.8 ms |
| **Exp 1.1** | Top-$K = 2$ | **100.0%** (30/30) | 83.33% (25/30) | **100.0%** | 76.67% (23/30) | **100.0%** (10/10) | 21.4 ms |
| **Exp 1.2** | Top-$K = 3$ | **100.0%** (30/30) | 83.33% (25/30) | **100.0%** | 76.67% (23/30) | **100.0%** (10/10) | 21.3 ms |
| **Exp 1.3** | Top-$K = 5$ | **100.0%** (30/30) | 83.33% (25/30) | **100.0%** | 76.67% (23/30) | **100.0%** (10/10) | 21.2 ms |
| **Exp 2.1** | Threshold $\tau = 0.78$ | **100.0%** (30/30) | 83.33% (25/30) | **100.0%** | **90.00%** (27/30) | 60.0% (6/10) | 23.1 ms |
| **Exp 2.2** | Threshold $\tau = 0.80$ | **100.0%** (30/30) | 83.33% (25/30) | **100.0%** | 76.67% (23/30) | **100.0%** (10/10) | 22.8 ms |
| **Exp 2.3** | Threshold $\tau = 0.82$ | **100.0%** (30/30) | 83.33% (25/30) | **100.0%** | 63.33% (19/30) | **100.0%** (10/10) | 22.3 ms |

---

## 🔬 In-Depth Analysis of Results

### 1. Retrieval Hit@3: Flawless 100%
Across every single in-scope question in English and Tamil, the correct government scheme was identified in the **top 3 retrieved chunks 100% of the time**. This demonstrates the high semantic discrimination capability of the `multilingual-e5-small` embedding space when using `"query: "` and `"passage: "` prefixes.

### 2. The Cross-Lingual Citation Gap & Threshold Trade-off
- At the baseline cutoff $\tau = 0.80$, **100% of out-of-scope queries (tomatoes, Mars, batteries, recipes) are blocked without calling the LLM**.
- However, 7 in-scope questions where the query language differed from the document language (English query on Tamil-only document, or Tamil query on English-only document) achieved cosine scores between $0.76$ and $0.795$.
- Dropping the threshold to $\tau = 0.78$ increased citation inclusion to **90.0%**, but allowed 4 out-of-scope Tamil queries to pass the filter due to the higher semantic dot-product baseline of Tamil morphological suffixes.

---

## 🚀 3 Recommended Optimization Experiments

### Experiment A: Chunk Size & Semantic Header Prefixing
- **Current**: Chunks are $\sim 500$–$600$ tokens containing multiple sections (e.g., Objectives + Eligibility + Exclusion). The vector represents an average across topics.
- **Proposed**: Split into **$\sim 250$ tokens** and prepend contextual headers:
  `"[Scheme: Kalaignar Magalir Urimai | Page: 1 | Section: Eligibility Criteria] ..."`
- **Expected Impact**: Pushes specific fact matches from $0.76$ to $> 0.84$, separating in-scope and out-of-scope queries cleanly.

### Experiment B: Language-Adaptive Similarity Thresholds
- **Current**: Single scalar threshold $\tau = 0.80$.
- **Proposed**: Set dynamic thresholding based on detected query language vs document chunk language:
  - $\tau_{\text{monolingual}} = 0.80$ (Tamil $\leftrightarrow$ Tamil or English $\leftrightarrow$ English)
  - $\tau_{\text{crosslingual}} = 0.77$ (English $\leftrightarrow$ Tamil)
- **Expected Impact**: $100\%$ Citation Rate AND $100\%$ Out-of-Scope Rejection simultaneously.

### Experiment C: Embedding Model Upgrade (`multilingual-e5-base`)
- **Current**: `intfloat/multilingual-e5-small` (384 dimensions, 117M params).
- **Proposed**: Test `intfloat/multilingual-e5-base` (768 dimensions) or `paraphrase-multilingual-mpnet-base-v2`.
- **Expected Impact**: Deeper cross-lingual semantic representation and higher rank-1 retrieval precision (raising Hit@1 from $83.3\%$ to $> 95\%$).
