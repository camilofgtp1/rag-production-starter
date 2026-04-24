# Repo Polish Automation Tasks
## rag-production-starter — Claude Code Agent Instructions

> Run these tasks in order. Each task is self-contained.
> Tools available: standard shell, `glab` (GitLab CLI), `git`, Python 3.
> Working directory: repo root of `rag-production-starter`.

---

## TASK 01 — Remove internal planning doc (done)

**What:** Delete `rag-production-starter-requirements.md` from the repo. This is an internal planning artifact and should never have been committed.

**Instructions:**
```
1. Check if the file exists:
   ls rag-production-starter-requirements.md

2. Remove it:
   git rm rag-production-starter-requirements.md

3. Commit:
   git commit -m "chore: remove internal planning doc from repo"

4. Push:
   git push origin main
```

**Verify:** `git log --oneline -3` should show the commit. File should not appear in `git ls-files`.

---

## TASK 02 — Add .gitignore (done)

**What:** Create a comprehensive `.gitignore` appropriate for a Python/FastAPI/MLflow/Docker project.

**Instructions:**

Create the file `.gitignore` with exactly this content:

```
# Environment
.env
.env.*
!.env.example

# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/
*.egg
.eggs/

# Virtual environments
.venv/
venv/
env/
ENV/

# Testing
.pytest_cache/
.coverage
htmlcov/
*.coverage
coverage.xml

# MLflow
mlflow/mlruns/
mlruns/
mlartifacts/

# Qdrant local storage
qdrant_storage/

# IDE
.idea/
.vscode/
*.swp
*.swo
.DS_Store

# Docker
*.log

# Distribution
*.tar.gz
*.zip
```

Then:
```
git add .gitignore
git commit -m "chore: add .gitignore"
git push origin main
```

**Verify:** Run `git status` — none of the ignored patterns should appear as untracked.

---

## TASK 03 — Verify .env is not tracked (done)

**What:** Confirm `.env` is not committed anywhere in git history. If it is, the OpenAI key must be rotated immediately (flag this to the user).

**Instructions:**
```
1. Check current tracking:
   git ls-files .env

2. Check full history:
   git log --all --full-history -- .env

3. If .env appears in either output:
   - Print a warning: "WARNING: .env was committed. Rotate your OpenAI API key immediately."
   - Remove from history:
     git filter-branch --force --index-filter \
       'git rm --cached --ignore-unmatch .env' \
       --prune-empty --tag-name-filter cat -- --all
   - Force push:
     git push origin --force --all

4. If .env does not appear: print "OK: .env is clean."
```

---

## TASK 04 — Verify and improve .env.example (done)

**What:** Ensure `.env.example` exists and every variable is documented with a comment explaining what it is and where to get it.

**Instructions:**

Create or overwrite `.env.example` with exactly this content:

```bash
# OpenAI API key — required for embeddings and generation
# Get it at: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-...

# Qdrant connection — use default for local Docker, or your cloud URL
# Local: http://localhost:6333
# Cloud: https://<your-cluster>.qdrant.io
QDRANT_URL=http://localhost:6333

# Qdrant API key — leave empty for local Docker, required for Qdrant Cloud
QDRANT_API_KEY=

# Name of the Qdrant collection to use
# Will be created automatically on first run if it doesn't exist
COLLECTION_NAME=rag_documents

# MLflow tracking server URI
# Local: http://localhost:5000
MLFLOW_TRACKING_URI=http://localhost:5000

# API key for the FastAPI service
# Used in X-API-Key header for all requests except /health
# For local dev, any string works. For production, use a secrets manager.
API_KEY=dev-key-change-in-production
```

Then:
```
git add .env.example
git commit -m "docs: improve .env.example with inline documentation"
git push origin main
```

---

## TASK 05 — Add GitLab CI pipeline

**What:** Create a minimal `.gitlab-ci.yml` that runs lint and tests on every push. A passing pipeline badge is a disproportionately strong trust signal.

**Instructions:**

Create `.gitlab-ci.yml` with exactly this content:

```yaml
stages:
  - lint
  - test

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip

default:
  image: python:3.11-slim
  before_script:
    - pip install -e ".[dev]" --quiet

lint:
  stage: lint
  script:
    - pip install ruff --quiet
    - ruff check app/ tests/
  allow_failure: true

test:
  stage: test
  services:
    - name: qdrant/qdrant
      alias: qdrant
  variables:
    QDRANT_URL: "http://qdrant:6333"
    OPENAI_API_KEY: "test-key-not-real"
    COLLECTION_NAME: "test_collection"
    MLFLOW_TRACKING_URI: "http://localhost:5000"
    API_KEY: "test-key"
  script:
    - pytest tests/ -v --tb=short
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

Then check if `pyproject.toml` has a `[project.optional-dependencies]` section for dev deps. If not, add this to `pyproject.toml` under `[project]`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-mock>=3.0",
    "ruff>=0.1.0",
    "httpx>=0.24.0",
]
```

Then:
```
git add .gitlab-ci.yml pyproject.toml
git commit -m "ci: add GitLab CI pipeline with lint and test stages"
git push origin main
```

**Verify:** 
```
glab ci view
```
Wait for the pipeline to complete. If it fails, review logs:
```
glab ci trace
```

---

## TASK 06 — Add CI badge to README

**What:** Add a GitLab CI pipeline status badge to the README, positioned directly under the project title.

**Instructions:**

1. Get the project path:
```
glab repo view --json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['pathWithNamespace'])"
```

Or read it directly: the project path is `camilofgtp1/rag-production-starter`.

2. The badge markdown is:
```
[![pipeline status](https://gitlab.com/camilofgtp1/rag-production-starter/badges/main/pipeline.svg)](https://gitlab.com/camilofgtp1/rag-production-starter/-/pipelines)
```

3. Open `README.md` and insert the badge on the line immediately after the title (`# rag-production-starter`), before the italic tagline. The top of the file should look like:

```markdown
# rag-production-starter

[![pipeline status](https://gitlab.com/camilofgtp1/rag-production-starter/badges/main/pipeline.svg)](https://gitlab.com/camilofgtp1/rag-production-starter/-/pipelines)

*Most RAG tutorials get you to a working demo. This is what comes after.*
```

4. Commit:
```
git add README.md
git commit -m "docs: add CI pipeline badge to README"
git push origin main
```

---

## TASK 07 — Add "Common failures this prevents" section to README

**What:** Add a section to the README that names specific, real production RAG failures this project addresses. This is the section that converts a reader into a contact — it proves the author has been in the fire, not just read about it.

**Instructions:**

Open `README.md` and insert the following section after the `## What We Deliberately Left Out` section and before the `## Documentation` section:

```markdown
## Common Failures This Prevents

These aren't hypothetical. They're the things that broke in production before this project existed.

**Retrieval that works in demos, fails on real queries**
Keyword search misses synonyms. Vector search misses product codes and exact identifiers. Neither alone is sufficient. The hybrid search with tunable alpha lets you slide the balance toward what your data actually needs — without rewriting your retrieval logic when you discover the default was wrong.

**Chunks that destroy meaning at boundaries**
Fixed-size chunking splits sentences mid-thought. You get chunks like "the threshold for triggering an alert is" and "15 percent above baseline" — two separate vectors that each retrieve nonsense in isolation. Semantic chunking respects paragraph boundaries. This one change moves eval scores more than any retrieval tuning.

**Stale documents that nobody notices**
A policy changes. The new version gets uploaded. Without versioning, the old and new vectors coexist in the index. Queries return whichever chunks score higher — sometimes old, sometimes new, always unpredictable. Document versioning with hard re-indexing on version bump fixes this silently.

**GDPR deletion requests with no implementation**
Someone asks for their data to be deleted. You grep for their name in the codebase and realize vectors aren't keyed by anything useful. Hard deletion by doc_id with a logged audit trail is the minimum you need before this becomes a legal problem, not an engineering problem.

**Evaluation theater**
Running Ragas once at project launch and calling it "evaluated." Evaluation without MLflow tracking means you have no idea if last week's chunking change improved or degraded retrieval quality. Metrics logged per run give you actual signal on what changed and why.

**The demo that doesn't survive first contact with real documents**
Sample documents are clean, short, and well-structured. Production documents are PDFs with tables, DOCX files with tracked changes, Markdown with code blocks. The ingestion pipeline handles all four formats with a single interface — so the format your client actually uses doesn't become a week-long integration project.
```

Then:
```
git add README.md
git commit -m "docs: add common failures section to README"
git push origin main
```

---

## TASK 08 — Replace chunking-strategy.md

**What:** Replace `docs/chunking-strategy.md` with improved content. The existing file is good but has some over-clean passages. The new version adds specificity and earned perspective where the original hedges.

**Instructions:**

Overwrite `docs/chunking-strategy.md` with exactly this content:

```markdown
# Chunking Strategy Guide

> *"Chunking is the hardest problem in RAG. Everything else is just plumbing."*

This document explains when to use each chunking strategy. Read the tradeoff analysis; don't just follow the recommendations.

---

## The sad state of the craft

Most RAG tutorials hand-wave chunking. They'll tell you "use 512 tokens with overlap" like it's magic. It's not.

**The actual problem**: You're compressing unstructured documents into fixed-size vectors. You're guaranteed to lose information. The question is: *which information can you afford to lose?*

That's what makes chunking hard. It's not a technical problem — it's a **domain understanding** problem. The right chunk boundaries depend entirely on what meaning your documents contain and what questions you'll ask.

When you're building a document knowledge base at scale, you need to work closely with domain experts — people who know the content, not just the format. The engineers who designed the Mercedes service manuals know that a procedure is a unit. A lawyer knows that a contract clause is a unit. You don't. Get them in the room before you finalize your chunking strategy, or you'll be refactoring your entire index in month three.

---

## Strategy Comparison

| Strategy | Best For | Worst For | Retrieval Quality | Complexity |
|----------|----------|-----------|------------------|------------|
| **Fixed** | Code, structured data, tables | Natural language, nuanced text | Medium | Low |
| **Semantic** | Most documents | Very short texts, ambiguous content | High | Medium |
| **Late** | Large documents (>10k tokens) | Small docs, simple FAQs | Highest | High |

**Our recommendation**: Start with semantic. Switch only when you have evidence that semantic isn't working for your specific data. "I read that late chunking is better" is not evidence.

---

## Fixed Chunking

```python
chunk_size=512, overlap=50
```

Splits text by token count with a sliding window. Simple, predictable, fast.

### When This Actually Works

- **Source code**: Functions and classes have predictable structure. Splitting on token boundaries is fine because the meaningful units tend to be similar sizes.
- **Semi-structured data**: JSON, YAML, configuration files. The structure provides implicit boundaries regardless of where tokens fall.
- **When you need debuggability**: Fixed chunking produces consistent outputs. When your system behaves unexpectedly at 2am, this is easier to reason about than a strategy that makes different decisions on each run.

### Why It Usually Fails for Text

- **Mid-sentence splits**: You'll separate a subject from its predicate. The embedding loses the relationship, and you won't notice until a user asks a question that should be trivially answerable.
- **No semantic awareness**: "The activation threshold is" split from "15 percent above baseline" embeds as two meaningless fragments. Both retrieve confidently. Neither helps.
- **Parameter sensitivity**: The "right" chunk size is data-dependent in ways that are genuinely hard to predict without running evals on your actual corpus.

### Practical Advice

If you're using fixed chunking, you're implicitly saying "my documents are uniform enough that it doesn't matter where I split." Ask yourself: is that actually true, or did you just not want to think about it yet?

---

## Semantic Chunking

Our default. Splits on paragraph boundaries first, then sentence boundaries, respecting a max token ceiling.

### Why This Is Usually Better

Paragraphs are **semantic units**. When someone writes a paragraph, they're making a single point. Splitting there preserves that unit intact.

Sentence splitting kicks in as a safety net when a paragraph exceeds the token limit. Ideally this doesn't happen much — if your paragraphs are consistently over 512 tokens, that's a signal your source documents weren't written with retrieval in mind, which is a different problem.

### What Could Go Wrong

- **Very short paragraphs**: Some Markdown styles use single-line paragraphs everywhere. You're back to near-fixed-chunking behavior, with the added overhead of a smarter splitter that didn't help you.
- **Code blocks in Markdown**: Semantic splitting doesn't know that a code block should stay intact. If your docs mix prose and code, you need to handle this explicitly or you'll split function signatures from their bodies.
- **Dense reference material**: Technical specs, API docs, data dictionaries. The "paragraphs as semantic units" assumption breaks when every sentence is independently meaningful.

### When to Question This Choice

Run this analysis on your actual data before committing:
1. What's the distribution of paragraph lengths?
2. How many paragraphs exceed 512 tokens?
3. Do your paragraphs actually represent coherent ideas, or is the structure decorative?

If most paragraphs are under 100 tokens, fixed chunking is fine and simpler. If many exceed 512 tokens, you're getting sentence-split fallback constantly, which is semantic chunking in name only.

---

## Late Chunking

Parent-child chunking. Large parent chunks (~1500 tokens) + small child chunks (~150 tokens). Children retrieve, parents provide context.

### The Theory

Children are small and precise — they embed tightly around specific content. Parents carry context — when the child retrieves, you use the parent for generation. Best of both worlds.

### The Reality

This sounds elegant. It's often over-engineered for the problem at hand.

**When late chunking makes sense:**
- Your documents genuinely exceed 10,000 tokens and context window matters
- You've measured that semantic chunking loses too much context on complex questions
- You have the engineering bandwidth to maintain the dual-retrieval logic when something breaks

**When it's overkill:**
- Most of your documents are under 5,000 tokens
- You're considering it because it sounds sophisticated, not because evals showed a problem
- You don't yet have eval data to compare it against

> **Don't reach for late chunking because it sounds sophisticated. Reach for it because your eval data shows semantic chunking is losing context on queries that matter to your users.**

The simplest thing that works is almost always the right answer. Save the complexity budget for problems you've actually measured.

---

## How to Actually Choose

### Step 1: Understand Your Data

Before you choose, answer these:
- What's the distribution of document lengths?
- Are there natural semantic boundaries (paragraphs, sections, procedures)?
- What does a typical query look like — conversational or exact-term?
- What do your domain experts say is "a unit" of meaning in these documents?

### Step 2: Pick a Starting Point

Most use cases → semantic
Code or structured data → fixed
Proven context loss on long documents → late

### Step 3: Measure

This is the part people skip. Run eval queries. Look at the retrieved chunks. Ask:

- Are we retrieving complete thoughts, or fragments?
- Is the retrieved content sufficient to answer the question without context from adjacent chunks?
- Where does retrieval fail — is it a chunking problem or a retrieval problem?

### Step 4: Iterate

Chunking is not a one-time decision. As your document collection grows, you'll discover edge cases that your original strategy doesn't handle. Budget time for this, or you'll discover it the hard way when your eval scores start drifting.

---

## Implementation Notes

### Token Counting

We use `tiktoken` with `cl100k_base` — the same encoder OpenAI uses for `text-embedding-3-small`. This ensures your chunk sizes match what the embedding model actually sees. If you switch embedding models, verify the tokenizer still matches.

### Overlap Tradeoffs

More overlap = more redundant storage, fewer lost-at-boundary failures.
Less overlap = leaner index, higher risk of splitting a thought across two chunks that neither retrieve correctly.

50 tokens is a reasonable default. If you're seeing boundary failures in eval — retrieved chunks that are almost right but cut off right before the relevant part — increase it. If storage is a real constraint, decrease it and verify your eval scores hold.

### The 512 Token Number

This isn't magic. It's 350-400 words — a few paragraphs, a coherent thought. It works for most natural language. The cases where it fails are worth knowing: dense reference material (too much semantic noise per chunk), very short conversational content (chunks are longer than the original documents), and structured data (token boundaries are meaningless).

---

## What Matters Most

> **Your chunking strategy should be driven by what your eval data shows, not by blog posts or what worked for someone else's corpus.**

Every dataset is different. The person who tells you "always use semantic chunking" hasn't looked at your data. Run experiments. Measure retrieval quality. Adjust.

That's the senior-engineer answer. There's no shortcut, and anyone who tells you otherwise is selling something.
```

Then:
```
git add docs/chunking-strategy.md
git commit -m "docs: improve chunking strategy guide with earned specificity"
git push origin main
```

---

## TASK 09 — Replace data-governance.md

**What:** Replace `docs/data-governance.md` with improved content. The existing file is strong — mostly needs sharper edges in a few places where it currently softens the uncomfortable parts.

**Instructions:**

Overwrite `docs/data-governance.md` with exactly this content:

```markdown
# Data Governance

> *"Governance isn't sexy. It's the thing that saves you when legal calls at 4pm on a Friday. Hope for the best, design for the testimony."*

This document covers versioning, drift detection, and GDPR deletion. These are the features that don't make demos impressive but determine whether the system is defensible when something goes wrong.

---

## Document Versioning

### What We Implemented

Every document gets a `doc_id` (stable across versions) and `version` (increments on re-ingest). When you re-ingest:

1. Check current version in Qdrant
2. If new_version > current version, delete old vectors
3. Upsert new vectors with the new version

### Why This Matters

**The obvious case**: Someone uploads v1 of a policy. Later, they upload v2. Without versioning, you have both in the index. Queries might return outdated content — and they'll return it confidently, because a stale chunk that matches the query still scores well.

**The subtle case**: You change your chunking strategy. Old chunks have different IDs and different embedding boundaries. Without re-indexing, you have a mixed index with two generations of embeddings that weren't computed the same way. Your eval scores will be inexplicably inconsistent and you'll spend a week blaming the retrieval logic before you find the real cause.

### What We Explicitly Didn't Implement

| Feature | Why We Left It Out |
|---------|-------------------|
| Version history | Extra storage cost with minimal operational value |
| Diff viewing | Useful eventually, complexity cost now |
| Rollback commands | Manual intervention is safer than automated rollback |

**The rationale**: This versioning gives you the foundation. What you build on top of it — approval workflows, content audit trails, scheduled re-indexing — depends on your compliance requirements. Keep the foundation simple so you can extend it without rewriting it.

### The Honest Assessment

This is minimum viable versioning. It works. If your compliance requirements are stricter — financial services, healthcare, anything with audit obligations — you'll need more. Specifically: immutable audit logs in a separate system, approval workflows before publishing new versions, and possibly diff storage for review. We didn't build that here because it would make this project too opinionated about your organizational processes.

---

## Drift Detection

### What We Implemented

Documents are tagged with `ingested_at` timestamps. Drift detection returns documents older than a configurable threshold (default 30 days).

```bash
GET /governance/drift?days_threshold=30
```

### Why This Threshold?

30 days is arbitrary. We chose it because it fits a monthly review cycle, it's long enough to accumulate real drift, and it's short enough to catch it before users notice. The parameter is exposed precisely because your review cycle might be different.

### What "Drift" Actually Means

**The honest definition**: Document age is not the problem. The problem is that the world changed and your document didn't.

Age is a poor proxy for this. A document ingested yesterday might already be wrong. A document from three years ago might still be accurate. But age is measurable and automatable, and semantic staleness detection is a research problem, not a product feature.

We chose the proxy consciously. The alternative — ML-based drift detection — brings false positives that route more documents to human review than the naive threshold would, for accuracy gains that rarely justify the complexity.

### What We Deliberately Avoided

**Automatic re-indexing**: If the system re-indexes without human review, incorrect or unauthorized content gets published automatically. The failure mode is worse than the problem it solves. Human review is slower and doesn't scale, but it's the right default for a system that's citing documents to users.

**ML-based drift detection**: Sounds compelling, isn't. You're still doing manual review — you've just added a model that sometimes sends you the wrong documents to review.

### Practical Advice

Drift detection gives you a list of things to review. It does not tell you what to do with them. That decision belongs to whoever owns the content, not whoever owns the infrastructure.

**Make it operational, not theoretical**:
- Run the drift report on a schedule (weekly is usually right)
- Route stale documents to content owners with a clear ask
- Define a SLA: stale documents need review within X days, not "when someone gets to it"
- Track the backlog — if it's growing, you have a process problem, not a tooling problem

---

## GDPR Deletion

### What We Implemented

Hard deletion. The vectors actually disappear from Qdrant. With logging for audit.

```bash
DELETE /governance/documents/{doc_id}
```

Returns:
```json
{
  "doc_id": "doc-123",
  "vectors_deleted": 42,
  "deleted_at": "2024-01-15T10:30:00Z"
}
```

### The Compliance Background

GDPR Article 17 (right to erasure) requires you to be able to delete personal data. "Soft delete" or tombstoning doesn't satisfy this — the data exists, you've just decided not to show it. For vector databases specifically, there's no way to reconstruct the original content from a vector, but the vector itself is derived from personal data and is subject to the same rules.

If you're operating in the EU and this system ingests any documents that could contain personal data, hard deletion by doc_id is not optional.

### What We Log and Why

```
DELETION EVENT: doc_id={doc_id} vectors_deleted={count} at={timestamp}
```

We log to stdout, not to the application database. The reasoning is uncomfortable but important: **deletion logs stored in the application database can themselves become subject to GDPR requests**. Now you have audit records that reference deleted data, and you have to decide whether the audit record itself needs to be deleted, which defeats its purpose.

By logging to stdout and routing those logs to a separate compliance system (or just your standard log aggregator), you've separated the audit trail from the data store. This is the defense-in-depth answer.

### What About Backups?

This is where it gets genuinely uncomfortable. Our implementation deletes from the live index. Backups still contain the data.

This is a real limitation, not an oversight. Solving it properly requires:
- GDPR-compliant backup retention policies (delete backups after a defined period)
- Or encrypted backups with key rotation (rotate the key for that document's data)
- Or accepting that full erasure requires manual intervention in backup restoration

We didn't solve this here because it requires operational infrastructure decisions that vary by organization. Document it, own it, and have an answer ready when someone asks.

---

## The Governance Tradeoffs We Made

| Decision | What We Gained | What We Lost |
|----------|---------------|--------------|
| Simple versioning | Easy to understand, minimal code | Granular history, rollback |
| Age-based drift detection | Easy to operationalize | Accuracy (age ≠ stale) |
| Hard deletion with logging | Compliance + audit separation | Soft-delete option |
| No automatic re-indexing | Safety from bad publishes | Operational efficiency |

### What We'd Add for a Production Deployment at Scale

1. **Audit trail in a separate system**: Application logs are not a compliance-grade audit trail. Route to a SIEM or a compliant logging service.
2. **Approval workflows**: Deletions and re-ingests should require an approval chain, especially in regulated environments.
3. **Version diffing**: Human review of content changes before publishing is worth the complexity when documents have legal or policy weight.
4. **Backup handling**: Automated GDPR-compliant backup lifecycle management. This is boring infrastructure work that nobody wants to do until it's urgent.

---

## Operationalizing Governance

### The Weekly Ritual

1. Run drift report
2. Route stale documents to content owners — specific people, not a team alias
3. Content owners review and re-ingest or explicitly mark as still valid
4. Track the backlog; if it's growing, something is wrong upstream

### When a Deletion Request Arrives

1. Verify the requester's identity through your legal team — don't act on an unauthenticated request
2. Identify the relevant doc_id (this is why good document metadata matters)
3. Run the DELETE endpoint
4. Verify deletion in logs
5. Confirm to legal in writing with the deletion timestamp

### What to Monitor

- Documents older than threshold: should trend stable or down, not up
- Deletion request rate: spikes indicate either a process problem or a data problem worth investigating
- Re-index frequency per document: a document being re-ingested frequently might indicate unstable upstream content

---

## The Bottom Line

Governance is the part that doesn't ship features, doesn't improve demo scores, and doesn't get mentioned in architecture reviews until something goes wrong. The time to add it is before you need it. The time you'll wish you had it is after you can't.

> **This starter project gives you the minimum viable foundation. The minimum viable foundation is not the same as production-grade compliance. Know the difference, be honest about it with your stakeholders, and extend accordingly.**
```

Then:
```
git add docs/data-governance.md
git commit -m "docs: sharpen data governance guide with operational specificity"
git push origin main
```

---

## TASK 10 — Replace evaluation.md

**What:** Replace `docs/evaluation.md` with improved content. The existing file is the strongest of the four — it already has real earned perspective. The improvements are targeted: a few over-hedged passages, and one section that needs a sharper close.

**Instructions:**

Overwrite `docs/evaluation.md` with exactly this content:

```markdown
# Evaluation

> *"You can't improve what you don't measure. But measuring the wrong thing is worse than measuring nothing — it gives you false confidence with extra steps."*

This document explains the Ragas metrics, what they actually measure, and how a senior engineer should think about them.

---

## The Evaluation Trap

Here's the uncomfortable truth: **you can make these metrics say anything you want**.

- Want higher faithfulness? Retrieve less context. The model has less room to hallucinate.
- Want higher context recall? Retrieve everything. Include all fifty chunks.
- Want higher answer relevancy? Prompt the model to restate the question before answering.

The metrics optimize for the prompt they're given, not for whether your users are getting useful answers.

So before the mechanics: what problem are you actually trying to detect? Because "running Ragas" is not the same as "having a feedback loop." The first is theater. The second requires knowing what signal you're looking for and acting on it when it degrades.

---

## What Each Metric Actually Measures

### Faithfulness

> "Does the answer stay grounded in the retrieved context?"

**What it actually tests**: The model's tendency to stay within bounds. Not correctness — restraint.

**What it misses**:
- If the retrieved context is wrong, faithfulness can be high while the answer is completely incorrect
- A perfectly faithful answer to incorrect context is still wrong — and it's confident about it
- It measures what the model didn't add, not whether what it kept was accurate

**When to care**: When users are reporting that the system "makes things up." This metric will tell you whether the fabrication is in retrieval (bad context) or generation (model ignoring context).

**When to ignore**: When factual accuracy matters more than grounding. A model can be 100% faithful to a stale or incorrect document.

### Answer Relevancy

> "Does the answer actually address the question that was asked?"

**What it actually tests**: Semantic proximity between the question and the answer. Uses a secondary LLM call, which means you're using the same family of model to both produce and evaluate.

**What it misses**:
- Semantic similarity to the question is not the same as answering it correctly
- There's circularity here that nobody fully acknowledges: GPT-4o-mini generating an answer, evaluated by the same model for quality
- It doesn't catch factual errors, only topical drift

**When to care**: When prompts are producing off-topic or evasive responses. If the model is answering adjacent questions instead of the actual question, this catches it.

**When to ignore**: When accuracy matters more than topical focus. A relevant answer can still be wrong.

### Context Recall

> "Did retrieval surface enough of the right context?"

**What it actually tests**: Coverage — how much of the information needed to answer the question appeared in the retrieved chunks.

**What it misses**:
- High recall doesn't mean high precision — you can retrieve a lot of irrelevant context and still score well
- It doesn't test whether the generation step used the context correctly
- The "ground truth" dependency in the original Ragas formulation is simplified here; treat scores as directional, not absolute

**When to care**: When you're debugging retrieval. Low context recall is a clean signal that the problem is upstream — wrong chunks, wrong chunk size, wrong search strategy.

**When to ignore**: When retrieval looks fine but answers are still poor. That's a generation problem. Don't tune retrieval to fix a prompting issue.

---

## The Score Table

| Score Range | Interpretation | Action |
|-------------|---------------|--------|
| 0.8 – 1.0 | Strong | Monitor |
| 0.6 – 0.8 | Acceptable | Investigate if trending down |
| 0.4 – 0.6 | Weak | Review chunking and retrieval |
| < 0.4 | Failing | Stop and investigate before proceeding |

These thresholds are directional. There's no research proving 0.8 is a universal "good enough" threshold. An internal knowledge base that helps employees find HR policies has different accuracy requirements than a system cited in a customer-facing legal document.

**What matters is relative movement, not absolute value.** Track scores over time. If they drop after a change, investigate. If they're stable and your users are satisfied, the specific number is secondary.

---

## How to Actually Use Evaluation

### 1. Build an Eval Set That Reflects Real Traffic

Not all queries are equal. A curated eval set of 20 tricky questions is less useful than 50 questions that represent what your users actually ask.

Start with this:
- Sample real queries from your first week of user traffic (or simulate if not live yet)
- Add the edge cases you know will be hard: short queries, ambiguous phrasing, questions that span multiple documents
- Include at least a few questions where the answer isn't in the corpus — you want to verify the "I don't have enough information" path works

Ground truth answers matter for some metrics. Don't skip this — questions without expected answers produce metrics that are hard to act on.

### 2. Run Periodically, Not Per-Request

Every evaluation call costs money and adds latency. Don't run it on every request in production.

A reasonable cadence:
- **Daily**: Sample N queries from production traffic, run eval, log to MLflow
- **Weekly**: Review trends, correlate with any changes deployed that week
- **Before every significant change**: Establish baseline before and after — chunking change, prompt update, embedding model switch

### 3. Track Over Time

This is why we integrated MLflow. Single scores are noise. Trends are signal.

Plot faithfulness, answer relevancy, and context recall over time. Correlate with:
- New documents ingested (corpus changes affect retrieval)
- Chunking strategy changes
- Prompt updates
- Model updates

If scores drop after a specific change, you have a starting point for investigation. If scores drift slowly without a clear cause, you have a different problem — probably corpus quality.

### 4. Don't Optimize Individual Metrics In Isolation

Improving one metric can degrade another. Retrieve more chunks → better context recall, worse faithfulness (more room to hallucinate). Tighter prompt constraints → better faithfulness, potentially worse answer relevancy (model is more likely to say "I don't know").

Optimize for overall user outcome. Pick the metric most relevant to the failure mode your users are experiencing, fix it, then verify you haven't degraded the others.

---

## What to Do When Scores Are Bad

### Low Faithfulness

**What it usually means**: The model is generating content not supported by retrieved context.

**Debug order**:
1. Check whether the prompt explicitly constrains the model to context only — our default prompt does, but verify it wasn't changed
2. Check whether retrieved context actually contains the answer — if not, it's a retrieval problem, not a faithfulness problem
3. Reduce `top_k` — less context means less surface area for hallucination (at the cost of recall)
4. Upgrade the generation model — GPT-4o follows constraints more reliably than GPT-4o-mini on complex queries

### Low Answer Relevancy

**What it usually means**: The model is producing answers that don't address the question.

**Debug order**:
1. Look at several actual responses — is the model being evasive, or is it answering a different question?
2. If evasive: the retrieval probably didn't surface good context, so the model is doing its best with what it has
3. If off-topic: review the prompt structure — make the question more prominent in the context
4. Check for very short or ambiguous queries — these reliably produce off-topic responses

### Low Context Recall

**What it usually means**: Retrieval isn't surfacing the relevant content.

**Debug order**:
1. Increase `top_k` — more candidates means more chance of including the right chunks
2. Review chunking — are you splitting content at boundaries that separate the question from its answer?
3. Tune `alpha` toward BM25 if queries contain specific terms, toward dense if they're abstract
4. Check whether the answer is actually in the corpus — it might be a gap, not a retrieval failure

---

## MLflow Integration

We log to MLflow because raw scores in a terminal window are not a feedback loop.

```bash
mlflow ui
# Open http://localhost:5000
```

Use it to compare runs, see score distributions over time, and correlate changes with metric movement. If you're not going to use MLflow, print the scores to stdout and save them somewhere. The value is in the trend, not the single measurement.

---

## Cost Considerations

Each Ragas evaluation call uses your OpenAI budget:
- ~$0.002 per faithfulness calculation
- ~$0.002 per answer relevancy
- ~$0.002 per context recall

At 1,000 queries/month with full evaluation: ~$10/month. Manageable.
At 100,000 queries/month: ~$1,000/month. Becomes a line item worth optimizing.

At scale: sample instead of evaluating everything, use a cheaper model for eval, or run eval less frequently on a curated set rather than production traffic.

---

## What We'd Add in a Production System

1. **Human evaluation on a sample**: LLM-as-judge is a useful proxy. Periodic human review of 20-50 responses is a more honest signal.
2. **A/B testing in production**: Compare retrieval strategies on live traffic, not just in eval. Users vote with their behavior.
3. **User feedback collection**: Thumbs up/down, or something more granular. Correlate with your automated metrics to see if they're measuring the same thing.
4. **Domain-specific metrics**: Ragas is general-purpose. If your documents are legal, financial, or technical, you may need metrics that check domain-specific correctness that semantic similarity won't catch.

---

## The Bottom Line

Metrics are imperfect proxies for user satisfaction. They're useful for catching regressions and identifying which component (retrieval, chunking, generation) is failing. They're not useful for declaring success.

> **The question is not "did we hit the threshold?" The question is "are our scores stable, and do our users get useful answers?"**

If the answer to the second question is yes, the first question mostly takes care of itself.
```

Then:
```
git add docs/evaluation.md
git commit -m "docs: sharpen evaluation guide with sharper close and tighter metric guidance"
git push origin main
```

---

## TASK 11 — Replace hybrid-search.md

**What:** Replace `docs/hybrid-search.md` with improved content. The existing file hedges in the right places but is slightly too even-handed — a senior engineer who's actually implemented this has more conviction about when hybrid matters and when it's complexity theater.

**Instructions:**

Overwrite `docs/hybrid-search.md` with exactly this content:

```markdown
# Hybrid Search

> *"Hybrid search is what you reach for when you're not sure whether your users speak your documents' language. Which is most of the time."*

This document explains how the hybrid search works and why we made the implementation choices we did.

---

## The Problem Hybrid Search Solves

Vector search and keyword search fail in complementary ways:

| Approach | Strength | Failure Mode |
|----------|----------|--------------|
| **Dense (vector)** | Semantic similarity, synonyms, paraphrase | Misses exact matches, unreliable with jargon and codes |
| **Sparse (BM25)** | Exact term matching, predictable | Misses semantic intent, no synonym understanding |

Hybrid search tries to get the benefits of both. But it adds complexity and a parameter to tune — which means it can also add a new failure mode if you set it wrong and don't measure.

**The question to ask before implementing this**: Do you actually know which failure mode is hurting you?

If your users ask conversational questions ("what is the return policy"), pure vector search probably works. If they search by identifier ("order SKU-12345", "API endpoint /v1/users/me"), BM25 probably works. If they do both — which is the default assumption for a general-purpose knowledge base — hybrid is the right default.

We included it because the general case is mixed queries. If you know your use case is more specific, you can simplify.

---

## How Our Implementation Works

We use **Reciprocal Rank Fusion (RRF)** to combine results.

### Why RRF and Not Learned Weights?

You could train a small model to predict the optimal blend per query type. We chose RRF for three reasons that matter in practice:

1. **No training data required.** Learned weights need query-result relevance pairs. You don't have those at the start of a project. RRF works correctly on day one.
2. **Robust to score distribution differences.** BM25 and dense search produce scores on completely different scales. RRF operates on ranks, not raw scores — it's immune to the "one signal dominates because its scores are bigger" problem that plagues naive weighted averaging.
3. **Debuggable.** When a result ranks unexpectedly, you can explain exactly why: its rank in each signal and how those combined. Learned weights are a black box.

### The Formula

```
fused_score = alpha * dense_rrf + (1 - alpha) * bm25_rrf
```

where:
```
rrf_score = 1 / (rank + 60)
```

The `60` is a standard constant. It softens the penalty for lower ranks — a result at rank 5 is still quite good, not nearly as bad as rank 5 in a linear scheme. You can tune it, but you'll rarely need to.

### What Alpha Actually Does

- **alpha = 1.0**: Pure vector search. BM25 is ignored entirely.
- **alpha = 0.0**: Pure BM25. Vectors are ignored entirely.
- **alpha = 0.5**: Equal weight to both signals. Our default.

---

## When to Tune Alpha

### Move Toward 1.0 (More Semantic) When:

- Queries are conversational or abstractly phrased
- Users rephrase the same concept in different words
- Your documents use formal language and users use casual language — or vice versa

**Example**: "What does the company say about using personal AI tools at work?" benefits from semantic understanding. The document might say "usage of third-party AI applications" and BM25 would miss the connection entirely.

### Move Toward 0.0 (More Keyword) When:

- Your domain has non-negotiable terminology: product codes, API endpoints, legal citations, identifiers
- Users search by quoting exact phrases from documents
- You're seeing vector search confidently returning semantically similar but factually wrong results

**Example**: "Clause 12.3(b) obligations" or "error code E4502" — these require exact matching. Semantic search will return documents about similar clauses or similar errors, which is worse than returning nothing.

---

## The Truth About Alpha Tuning

Here's what doesn't get said enough:

> **Most queries perform acceptably at alpha=0.5. The gains from tuning are real but marginal for typical mixed-query workloads.**

The cases where alpha matters significantly are the edges of your query distribution. The question is whether those edge cases are important enough to justify the added complexity of per-query alpha selection.

**The honest advice**:

1. **Start at 0.5.** It's a reasonable default.
2. **Don't tune without eval evidence.** Run a set of queries at 0.3, 0.5, and 0.7. If there's no meaningful difference in your metrics, don't complicate your system.
3. **Consider query classification only if you've proven it helps.** Routing keyword-heavy queries to low alpha and semantic queries to high alpha is a reasonable optimization — but it's extra code to maintain, and it requires a reliable classifier. Prove the gain first.
4. **Watch for regression.** Tuning alpha for one query type almost always affects others. Check overall eval scores, not just the queries you were optimizing.

---

## Implementation Details

### BM25

We use `rank_bm25.BM25Okapi` with simple whitespace tokenization. This is the "good enough" choice for a starter project.

**Known limitations**:
- Doesn't handle hyphenated terms well
- Case-insensitive (we lowercase everything before indexing)
- No phrase query support — "machine learning" is treated as two separate terms

For production-grade keyword search on large corpora with complex terminology, you'd want a proper inverted index — Elasticsearch or OpenSearch with a real analyzer. But for most starter use cases, BM25Okapi with whitespace tokenization gets you 80% of the benefit at 5% of the complexity.

### Why We Build BM25 In-Memory

We rebuild the BM25 index from Qdrant payloads at query time. This is the correct choice at starter scale — the alternative (maintaining a separate BM25 index) introduces synchronization problems. At large scale (millions of documents), you'd want a persistent BM25 index or a dedicated keyword search layer. You're not there yet.

### Normalization

Both BM25 and dense scores are normalized to [0,1] before fusion. This is not optional — without normalization, whichever signal produces larger raw values dominates the fusion regardless of the alpha setting. Dense cosine similarity scores might range from 0.7 to 0.95. BM25 scores might range from 0.1 to 15.0. Naive fusion would be pure BM25.

### The k=60 Constant in RRF

Higher k = rank position matters less (more forgiving of being ranked 5th vs 1st).
Lower k = rank position matters more (steep penalty for not being first).

60 is the standard value from the original RRF paper. It works well for typical retrieval workloads. You're unlikely to need to change it unless you're seeing specific rank sensitivity issues in eval.

---

## When Hybrid Search Isn't Enough

If you've implemented hybrid search and retrieval quality still isn't where it needs to be, the fix is almost never "tune alpha more."

In order of what to try:
1. **Review chunking first.** This is the most common root cause of retrieval failures that look like search strategy problems. A chunk that splits a concept across two boundaries won't be retrieved reliably regardless of how you combine BM25 and dense scores.
2. **Add reranking.** Retrieve 30-50 candidates with hybrid search, then rerank with a cross-encoder model. More expensive but substantially more accurate for ambiguous queries.
3. **Query expansion.** Rewrite the user's query before retrieval — expand abbreviations, decompose compound questions, add synonyms. This is a prompt engineering problem as much as a retrieval problem.
4. **Evaluate your corpus.** Sometimes retrieval fails because the answer isn't in the documents, not because the search is broken. Make sure you're distinguishing retrieval failures from corpus gaps.

---

## What Matters Most

Fix chunking before tuning alpha. Improve your eval set before adding reranking. Understand your failure modes before adding complexity.

Hybrid search is a good default for mixed-query workloads. It's not a solution to retrieval problems caused by other parts of the pipeline — and it's one of the first places engineers look when they should be looking elsewhere.

> **Measure first. Tune second. Add complexity only when measurement tells you to.**
```

Then:
```
git add docs/hybrid-search.md
git commit -m "docs: sharpen hybrid search guide with stronger implementation rationale"
git push origin main
```

---

## TASK 12 — Add LICENSE file

**What:** The README references MIT license but there is no `LICENSE` file in the repo. Add it.

**Instructions:**

Create `LICENSE` with exactly this content (replace `2026` with current year, `Camilo Fernandez` with actual name if different):

```
MIT License

Copyright (c) 2026 Camilo Fernandez

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Then:
```
git add LICENSE
git commit -m "chore: add MIT license file"
git push origin main
```

---

## TASK 13 — Add repo description and topics via GitLab CLI

**What:** Set the GitLab repo description and topic tags for discoverability.

**Instructions:**
```
glab repo edit \
  --description "Production-ready RAG starter: hybrid search, chunking strategies, drift detection, GDPR deletion, and evaluation. The parts the tutorials skip." \
  --topics "rag,llm,vector-search,mlops,fastapi,qdrant,ragas,mlflow,python,hybrid-search"
```

**Verify:**
```
glab repo view
```
Confirm description and topics appear correctly.

---

## TASK 14 — Tag v0.1.0 release

**What:** Create an annotated git tag and a GitLab release for v0.1.0. Shows intentional versioning and makes the project look maintained.

**Instructions:**
```
1. Create annotated tag:
   git tag -a v0.1.0 -m "v0.1.0 — initial release

   Production-ready RAG starter with:
   - Hybrid BM25 + dense search with RRF fusion
   - Three chunking strategies (fixed, semantic, late)
   - Document versioning and re-indexing
   - Drift detection and GDPR-compliant deletion
   - Ragas evaluation with MLflow tracking
   - FastAPI with API key auth
   - Docker Compose for local dev"

2. Push the tag:
   git push origin v0.1.0

3. Create GitLab release:
   glab release create v0.1.0 \
     --name "v0.1.0 — Initial Release" \
     --notes "First public release of rag-production-starter.

Production-ready RAG starter kit for teams who've outgrown tutorials.

**What's included:**
- Hybrid BM25 + dense vector search with RRF fusion and tunable alpha
- Three chunking strategies: fixed, semantic, and late (parent-child)
- Document versioning with hard re-indexing on version bump
- Age-based drift detection with configurable threshold
- GDPR-compliant hard deletion with audit logging
- Ragas evaluation (faithfulness, answer relevancy, context recall)
- MLflow tracking for evaluation trends over time
- FastAPI with API key authentication
- Full Docker Compose setup: app + Qdrant + MLflow
- Supports PDF, Markdown, plain text, and DOCX ingestion"
```

**Verify:**
```
glab release list
```

---

## TASK 15 — Verify seed_demo.py runs end-to-end

**What:** Do a clean end-to-end test of the demo. This is the most important functional check — if the demo doesn't work from a fresh clone, everything else is irrelevant.

**Instructions:**
```
1. Start infrastructure:
   docker compose up -d

2. Wait for services to be healthy (check with):
   docker compose ps

3. Copy and configure env:
   cp .env.example .env
   # Set API_KEY=dev-key (or whatever is in .env.example as default)

4. Install dependencies:
   pip install -e .

5. Run the demo:
   API_KEY=dev-key python scripts/seed_demo.py

6. Expected output should include:
   - Confirmation of documents ingested
   - A query result with answer and sources
   - Evaluation scores (faithfulness, answer_relevancy, context_recall)

7. If anything fails, fix it before proceeding.

8. Tear down:
   docker compose down
```

**If the script fails**: Fix the root cause before marking this task done. A broken demo is worse than no demo.

---

## Final Verification

After all tasks are complete, run:

```bash
# Confirm clean state
git status

# Confirm all files present
git ls-files | sort

# Confirm CI is passing
glab ci view

# Confirm release exists
glab release list

# Confirm repo metadata
glab repo view
```

The repo is ready to share when:
- CI pipeline is green
- `git status` is clean
- `python scripts/seed_demo.py` runs without errors
- All docs in `docs/` are substantive (not stubs)
- No internal files (`.env`, planning docs) are tracked
