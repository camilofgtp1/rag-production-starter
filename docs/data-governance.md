# Data Governance

> *"Governance isn't sexy. It's the thing that saves you when you're testifying in court. Hope for the best, plan for the testimony."*

This document explains the governance features: versioning, drift detection, and GDPR deletion. These are the parts that don't contribute to cool demos but matter when things go wrong.

---

## Document Versioning

### What We Implemented

Every document gets a `doc_id` (stable across versions) and `version` (increments on re-ingest). When you re-ingest:

1. Check current version in Qdrant
2. If new_version > current version, delete old vectors
3. Upsert new vectors

### Why This Matters

**The obvious case**: Someone uploads v1 of a policy. Later, they upload v2. Without versioning, you have both in the index. Queries might return outdated content.

**The subtle case**: You change your chunking strategy. The old chunks have different IDs. Without re-indexing, you have inconsistent embeddings.

### What We Explicitly Didn't Do

| Feature | Why We Left It Out |
|---------|-------------------|
| Version history | Extra storage for minimal value |
| Diff viewing | Complexity without clear benefit |
| Rollback commands | Manual intervention is safer |

**The rationale**: Versioning provides the foundation. What you do with versions is operational. Keep the foundation simple; build operational tools as needed.

### The Honest Assessment

This is the minimum viable versioning. It works. It's simple. If your compliance requirements are stricter (they might be), you'll need more.

---

## Drift Detection

### What We Implemented

Documents are tagged with `ingested_at` timestamps. Drift detection returns documents older than a threshold (default 30 days).

```bash
GET /governance/drift?days_threshold=30
```

### Why This Threshold?

30 days is arbitrary. Here's why we chose it anyway:

- **Weekly review cycle**: Most organizations do content reviews weekly or monthly. 30 days is long enough to accumulate issues, short enough to catch them.
- **It's tunable**: If 30 days doesn't fit your review cycle, the parameter is exposed.

### What "Drift" Actually Means

**The honest definition**: Document age isn't the problem. The problem is that the world changed and your document is stale.

Age is a proxy for this. It's a poor proxy — a document from yesterday might be outdated, a document from 2 years ago might still be accurate.

### What We Deliberately Avoided

**Automatic re-indexing**: Why?

- If the system re-indexes without human review, bad content gets published automatically
- The "right" behavior depends on your content update process
- Automated fixes hide problems rather than fixing them

**ML-based drift detection**: Why?

- False positives. The model guesses "this document is stale" and you're back to manual review
- Adds significant complexity
- It's solving a problem that's usually easier to solve with process

### Practical Advice

Drift detection gives you a **list of things to review**. It doesn't tell you what to do. That's intentional — the review is a human decision.

**Operationalize it**: 
- Run the drift report weekly
- Route stale docs to content owners for review
- Create a SLA: stale docs need review within X days

---

## GDPR Deletion

### What We Implemented

Hard deletion — the vectors actually disappear. With logging for audit.

```bash
DELETE /governance/documents/{doc_id}
```

Returns confirmation:
```json
{
  "doc_id": "doc-123",
  "vectors_deleted": 42,
  "deleted_at": "2024-01-15T10:30:00Z"
}
```

### The Compliance Background

GDPR Article 17 ("Right to Erasure") requires you be able to delete personal data. "Soft delete" or tombstoning doesn't satisfy this — the data still exists in any meaningful sense.

For vector databases, this means deleting the vectors. There is no way to reconstruct them without the original document.

### What We Log And Why

```
DELETION EVENT: doc_id={doc_id} vectors_deleted={count} at={timestamp}
```

We log to stdout (Python logger). We don't store in the database. Here's the reasoning:

- **Stored deletion logs can be subject to GDPR too**. Now you have deletion logs that reference deleted data.
- **Audit trails should be separate from the application database**. This is a defense-in-depth approach.
- **We log enough to reconstruct what happened**, not enough to recover what was deleted.

### What About Backups?

This is where it gets uncomfortable. Backups contain the deleted data. Our implementation doesn't handle this.

**Practical approach for backups**:
- Implement GDPR-compliant backup retention (delete old backups after retention period)
- Or: back up to encrypted storage that supports key rotation
- Or: accept that full erasure requires additional operational processes

**We didn't solve this** because it requires operational infrastructure beyond the application code.

---

## The Governance Tradeoffs We Made

| Decision | What We Gained | What We Lost |
|----------|---------------|--------------|
| Simple versioning | Easy to understand, minimal code | Granular version history |
| Age-based drift detection | Easy to operationalize | Accuracy (age != stale) |
| Hard deletion with logging | Compliance + audit | Soft-delete option |
| No automatic re-indexing | Safety from bad publishes | Operational efficiency |

### What We'd Do Differently If Scaling

If this were for a larger organization with stricter compliance:

1. **Audit trail in separate system**: SIEM, compliant logging service
2. **Approval workflows**: Deletion requires approval chain
3. **Version diffing**: Human review of changes before publishing
4. **Backup handling**: Automated GDPR-compliant backup management

---

## Operationalizing Governance

### The Weekly Ritual

1. Run drift report
2. Route stale docs to content owners
3. Content owners review and re-ingest or confirm as valid
4. Repeat

### On Call

If a GDPR deletion request comes in:

1. Verify identity (you're trusting a legal request — verify it)
2. Run the DELETE endpoint
3. Verify deletion in logs
4. Confirm to legal/compliance

### What to Monitor

- Number of documents older than threshold (should trend down or stable, not up)
- Deletion request rate (spikes might indicate issues)
- Re-index frequency (high rate might indicate unstable source content)

---

## The Bottom Line

Governance is the unsexy but essential part. It doesn't make the demo better. It makes the compliance conversation shorter.

> **The time to add governance is when you don't need it. The time to need it is when it's too late to add it.**

This starter project gives you the minimal foundation. Extend it as your compliance requirements demand.