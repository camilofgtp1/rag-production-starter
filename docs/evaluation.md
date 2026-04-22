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
- There's circularity here that nobody fully acknowledges: GPT-4o_mini generating an answer, evaluated by the same model for quality
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
4. Upgrade the generation model — GPT-4o follows constraints more reliably than GPT-4o_mini on complex queries

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