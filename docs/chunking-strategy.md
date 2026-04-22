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