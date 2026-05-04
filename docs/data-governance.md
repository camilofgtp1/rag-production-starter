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

Every drift detection run is logged to MLflow with the threshold used and the list of stale document IDs. This creates a searchable history of when drift was detected and which documents were flagged — useful for compliance audits and for spotting patterns (e.g., the same documents repeatedly flagged means they're not being updated on schedule, not that they're genuinely stale).

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

Each governance action logs to **both stdout and MLflow**:

```
DELETION EVENT: doc_id={doc_id} vectors_deleted={count} at={timestamp}
```

The MLflow log persists the audit trail beyond container restarts:
- Deletions: doc_id, vectors_deleted, deleted_at timestamp
- Version changes: doc_id, old_version, new_version, changed_at timestamp
- Drift detection runs: days_threshold, num_stale_documents, stale_doc_ids

The reasoning is uncomfortable but important: **deletion logs stored in the application database can themselves become subject to GDPR requests**. MLflow provides a separate, queryable audit trail that survives container restarts without tying the audit data to the application's primary data store.

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
| Hard deletion with MLflow + stdout logging | Compliance audit trail + queryable history | Soft-delete option |
| No automatic re-indexing | Safety from bad publishes | Operational efficiency |

### What We'd Add for a Production Deployment at Scale

1. **SIEM integration**: MLflow is a good audit trail but not a compliance-grade one. Route MLflow events to a SIEM for tamper-evident logging.
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