# Evaluation

> *"You can't improve what you don't measure. But measuring the wrong thing is worse than measuring nothing at all."*

This document explains the Ragas evaluation metrics, what they actually measure, and how to think about them from a senior engineer's perspective.

---

## The Evaluation Trap

Here's the uncomfortable truth: **you can make these metrics say anything you want**.

- Want higher faithfulness? Retrieve less context. The model has less to hallucinate from.
- Want higher context recall? Retrieve more context. Include everything.
- Want higher answer relevancy? Prompt the model to restate the question.

**The metrics optimize for the prompt they're given, not for user satisfaction.**

So before we get into the mechanics: what are you actually trying to measure?

---

## What Each Metric Actually Measures

### Faithfulness

> "Does the answer stay grounded in the retrieved context?"

**What it actually tests**: The LLM's tendency to stay within bounds. It doesn't test correctness — it tests restraint.

**What it misses**:
- If the context is wrong, faithfulness can be high while being completely wrong
- A faithful answer that's based on incorrect context is still wrong
- It measures what the model didn't say, not what it said correctly

**When to care**: When you're seeing obvious hallucinations. If your users complain "the system makes things up", track this.

**When to ignore**: When correctness matters more than restraint. Faithfulness can hide inaccuracy.

### Answer Relevancy

> "Does the answer actually address the question?"

**What it actually tests**: How closely the answer matches the semantic intent of the question. Uses a secondary LLM call to assess relevance.

**What it misses**:
- An answer can be relevant to a *similar* question but wrong for the actual question
- It doesn't assess factual accuracy
- There's an inherent circularity — you're using the same LLM to generate and evaluate

**When to care**: When prompts are producing off-topic responses. If the model is answering the wrong question, this catches it.

**When to ignore**: When you need fact-based accuracy, not semantic similarity.

### Context Recall

> "Did we retrieve enough relevant context?"

**What it actually tests**: How much of the "ideal" context appears in the retrieved context. (This is actually Ground Truth dependent in the original Ragas formulation — we use a simplified version here.)

**What it misses**:
- What matters is *relevant* context, not *any* context
- Retrieval of noisy context can inflate this score
- It doesn't test whether the generation used the context properly

**When to care**: When you're debugging retrieval. If context recall is low, you know the problem is upstream.

**When to ignore**: When retrieval looks fine but answers are still bad (that's a generation problem, not retrieval).

---

## The Score Table Is Not Your Friend

| Score Range | Interpretation | Action Needed |
|-----------|--------------|--------------|
| 0.8 - 1.0 | Great | None |
| 0.6 - 0.8 | Good | Monitor |
| 0.4 - 0.6 | Fair | Review chunks/retrieval |
| < 0.4 | Poor | Investigate |

This table is misleading. Here's why:

1. **The thresholds are arbitrary.** There's no research proving 0.8 is "good enough" for production.
2. **The score distribution depends on your eval set.** Easy queries score higher than hard queries.
3. **You might not need high scores.** If your use case tolerates imperfection, lower scores might be acceptable.

**What actually matters**: Scores *relative to your baseline*. Track them over time. If scores drop, investigate. If scores are stable and acceptable, ship.

---

## How To Actually Use Evaluation

### 1. Build an Eval Set That Matters

Not all queries are equal. Your eval set should:

- Reflect real user traffic (or projections thereof)
- Include edge cases you care about
- Have ground truth answers (for some metrics)

**Practical advice**: Start with 20-50 queries that represent the 80% of traffic. Add edge cases as you discover them.

### 2. Run Periodically, Not Per-Request

Evaluation costs money and adds latency. Don't run it on every request.

- **Daily**: Sample N queries, run eval, log results
- **Weekly**: Review score trends, identify regressions
- **Before deploys**: Compare current vs. new scores

### 3. Track Scores Over Time

This is where MLflow helps. Plot scores over time. Correlate with changes:

- New chunking strategy → context recall improved
- New prompt → answer relevancy changed
- Data added → all scores changed

### 4. Don't Optimize Single Metrics

Improving one can hurt others. Retrieve more → better context recall, worse faithfulness. The system is interconnected.

---

## What To Do When Scores Are Bad

### Low Faithfulness

**Symptoms**: Model generates content not in retrieved context.

**Typical fixes** (in order):
1. **Add guardrails to prompt**: "Only answer using the provided context"
2. **Improve context retrieval**: Better chunking, better retrieval
3. **Reduce top_k**: Less context = less to hallucinate from (at cost of recall)
4. **Switch to a more obedient model**: GPT-4o-mini is good, but GPT-4o is more compliant

### Low Answer Relevancy

**Symptoms**: Answer doesn't address the question.

**Typical fixes**:
1. **Improve prompt**: "Answer the question: {question}"
2. **Add context framing**: Put the question in context before generation
3. **Check retrieval**: If context doesn't answer the question, retrieval is the problem

### Low Context Recall

**Symptoms**: Retrieved context doesn't contain needed information.

**Typical fixes**:
1. **Increase top_k**: More candidates = more chance of including relevant
2. **Revisit chunking**: Chunks might be too small or too large
3. **Tune alpha**: Try different hybrid search weights
4. **Check chunk boundaries**: Are you splitting in the wrong places?

---

## MLflow Integration

We log to MLflow for a reason: **you're not going to look at raw scores**.

```bash
mlflow ui
```

Use the UI to:
- Compare runs over time
- See score distributions
- Correlate with other parameters

If you're not going to use MLflow, just print the scores to stdout. The value is in trends, not single values.

---

## The Real Answer

Here's what senior engineers actually do about evaluation:

> **They don't obsess over metrics. They build observability into their systems and use metrics to identify problems, not to declare success.**

The score is a signal, not a destination. If your users are satisfied and your error rates are acceptable, the specific numbers matter less than consistent measurement.

If you're going to invest in evaluation, invest in:
1. A representative eval set
2. Consistent tracking over time
3. Correlation with user feedback

Not in hitting arbitrary thresholds.

---

## Cost Considerations

Every evaluation run costs OpenAI credits:
- ~$0.002 per faithfulness calculation
- ~$0.002 per answer relevancy
- ~$0.002 per context recall

A full eval run = ~$0.01 per query. At 1000 queries/month = $10/month. At 100,000 queries/month = $1000/month.

**This is fine for a starter project. It's a real cost at scale.**

At scale, consider:
- Sampling instead of full evaluation
- Using cheaper models for eval
- Running eval less frequently

---

## What We'd Add Next

If this were a production system, we'd add:

1. **Human evaluation**: LLM metrics are proxies. Periodically have humans review responses.
2. **A/B testing**: Compare retrieval strategies in production, not just in eval.
3. **User feedback loops**: Thumbs up/down on responses. Correlate with metrics.
4. **Custom metrics**: For domain-specific correctness, nothing beats domain-specific checks.

---

## The Bottom Line

- Metrics are imperfect proxies for user satisfaction
- Track trends, not absolute values
- Don't ship based on hitting thresholds — ship based on user outcomes
- Evaluation is an investment: make sure you're getting return on it (actual improvements, not just scores)