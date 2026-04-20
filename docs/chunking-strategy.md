# Chunking Strategy Guide

> *"Chunking is the hardest problem in RAG. Everything else is just plumbing."*

This document explains when to use each chunking strategy. Read the tradeoff analysis; don't just follow the recommendations.

---

## The Uncomfortable Truth

Most RAG tutorials hand-wave chunking. They'll tell you "use 512 tokens with overlap" like it's magic. It's not.

**The actual problem**: You're compressing unstructured documents into fixed-size vectors. You're guaranteed to lose information. The question is: *which information can you afford to lose?*

That's what makes chunking hard. It's not a technical problem — it's a **domain understanding** problem. The right chunk boundaries depend entirely on what meaning your documents contain and what questions you'll ask.

---

## Strategy Comparison

| Strategy | Best For | Worst For | Retrieval Quality | Complexity |
|----------|----------|-----------|------------------|------------|
| **Fixed** | Code, structured data, tables | Natural language, nuanced text | Medium | Low |
| **Semantic** | Most documents | Very short texts, ambiguous content | High | Medium |
| **Late** | Large documents (>10k tokens) | Small docs, simple FAQs | Highest | High |

**Our recommendation**: Start with semantic. Switch only when you have evidence that semantic isn't working for your specific data.

---

## Fixed Chunking

```python
chunk_size=512, overlap=50
```

Splits text by token count with a sliding window. Simple, predictable, fast.

### When This Actually Works

- **Source code**: Functions and classes have predictable structure. Splitting on token boundaries is fine because the meaningful units (functions, classes) tend to be similar sizes.
- **Semi-structured data**: JSON, YAML, configuration files. The structure provides implicit boundaries regardless of where tokens fall.
- **When you need debugging**: Fixed chunking produces consistent outputs. When your system behaves unexpectedly, this is easier to diagnose.

### Why It Usually Fails for Text

- **Mid-sentence splits**: You'll separate a subject from its predicate. The embedding loses the relationship.
- **No semantic awareness**: "The cat sat on the mat" split as "The cat sat" + "on the mat" loses the complete thought.
- **Parameter sensitivity**: The "right" chunk size is data-dependent in ways that are hard to predict.

### Practical Advice

If you're using fixed chunking, you're implicitly saying "my documents are uniform enough that it doesn't matter where I split." Ask yourself: is that true?

---

## Semantic Chunking

Our default. Splits on paragraph boundaries first, then sentence boundaries, respecting a max token ceiling.

### Why This Is Usually Better

Paragraphs are **semantic units**. When someone writes a paragraph, they're making a single point. Splitting there preserves that unit intact.

We then fall back to sentence splitting if a paragraph exceeds your token limit. This is a safety net — ideally paragraphs are short enough that this doesn't matter.

### What Could Go Wrong

- **Very short paragraphs**: If your source has single-line paragraphs (some Markdown styles), you're back to near-fixed-chunking behavior.
- **Paragraphs that are actually lists**: A paragraph that's really a list of items might need different treatment.
- **Code blocks in Markdown**: Semantic splitting doesn't understand "this code block should stay together."

### When to Question This Choice

Run this analysis on your data:
1. What are your average paragraph lengths?
2. How many paragraphs exceed 512 tokens?
3. Do your paragraphs represent coherent ideas?

If most paragraphs are under 100 tokens, fixed chunking might be fine. If many exceed 512 tokens, you need to handle that case (our code does, but it's a compromise).

---

## Late Chunking

Parent-child chunking. Large parent chunks (~1500 tokens) + small child chunks (~150 tokens).

### The Theory

- **Children** get embedded and retrieved. Small size = precise matching.
- **Parents** provide context. Large size = more complete information.
- At generation time, you fetch the parent and use it for context.

### The Reality

This sounds elegant. It's often over-engineered.

**When late chunking makes sense:**
- Your documents genuinely exceed 10,000 tokens
- You need to retrieve very specific information but also provide full context
- You've measured that retrieval precision matters more than recall

**When it's overkill:**
- Most of your documents are under 5,000 tokens
- The complexity increase isn't justified by your eval metrics
- You don't have the engineering bandwidth to handle the dual-retrieval logic

### Practical Advice

> **Don't reach for late chunking because it sounds sophisticated. Reach for it because your eval data shows semantic chunking is losing too much context.**

The simplest thing that works almost always beats the clever thing.

---

## How to Actually Choose

### Step 1: Understand Your Data

Before you choose, answer:
- What's the distribution of document lengths?
- Are there natural semantic boundaries (paragraphs, sections)?
- What's the typical query complexity?

### Step 2: Pick a Starting Point

Most use cases → semantic
Code/structured data → fixed
Proven context loss → late

### Step 3: Measure

This is the important part. Run eval queries and examine the retrieved chunks. Ask:

- Are we retrieving complete thoughts?
- Is the retrieved content sufficient to answer the question?
- Where does retrieval fail, and is it chunking-related?

### Step 4: Iterate

Chunking is not "set and forget." As your document collection grows, you'll discover edge cases. Plan to revisit this decision.

---

## Implementation Notes

### Token Counting

We use `tiktoken` with `cl100k_base` (the same encoder used by OpenAI embeddings). This ensures your chunk sizes match what the embedding model sees.

### Overlap Tradeoffs

More overlap = more redundant storage, fewer boundary issues.
Less overlap = efficiency, higher risk of losing context at boundaries.

50 tokens overlap is a reasonable default. If you're seeing boundary issues in eval, increase it. If storage is a concern, decrease it.

### The 512 Token Number

This isn't magic. It's a practical balance:
- Smaller chunks = more precise retrieval but less context
- Larger chunks = more context but potential noise

512 tokens is roughly 350-400 words. A few paragraphs. For most natural language, this captures a coherent thought without overwhelming the embedding.

---

## What Matters Most

If you take one thing away from this document:

> **Your chunking strategy should be driven by what your eval data tells you, not by blog posts or tutorials.**

Every dataset is different. The person who tells you "always use X chunking" hasn't looked at your data. Run experiments. Measure retrieval quality. Adjust.

That's the senior-engineer answer. There's no shortcut.
