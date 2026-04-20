import logging
from datetime import datetime, timedelta
from typing import Dict, List

from app.retrieval import qdrant_client

logger = logging.getLogger(__name__)


async def get_stale_docs(days_threshold: int = 30) -> List[str]:
    threshold_date = datetime.utcnow() - timedelta(days=days_threshold)
    all_chunks = qdrant_client.get_all_chunks()
    
    stale_doc_ids = set()
    for chunk in all_chunks:
        ingested_at = chunk.get("ingested_at")
        if ingested_at:
            try:
                ingested_date = datetime.fromisoformat(ingested_at)
                if ingested_date < threshold_date:
                    stale_doc_ids.add(chunk.get("doc_id"))
            except ValueError:
                continue
    
    return list(stale_doc_ids)


async def drift_report() -> Dict:
    all_chunks = qdrant_client.get_all_chunks()
    
    doc_ingestion_times = {}
    for chunk in all_chunks:
        doc_id = chunk.get("doc_id")
        ingested_at = chunk.get("ingested_at")
        if doc_id and ingested_at:
            if doc_id not in doc_ingestion_times:
                doc_ingestion_times[doc_id] = ingested_at
            else:
                if ingested_at < doc_ingestion_times[doc_id]:
                    doc_ingestion_times[doc_id] = ingested_at
    
    total_docs = len(doc_ingestion_times)
    
    threshold_date = datetime.utcnow() - timedelta(days=30)
    stale_count = 0
    oldest_doc = None
    newest_doc = None
    oldest_time = None
    newest_time = None
    
    for doc_id, ingested_at in doc_ingestion_times.items():
        try:
            ingested_date = datetime.fromisoformat(ingested_at)
            if ingested_date < threshold_date:
                stale_count += 1
            
            if oldest_time is None or ingested_at < oldest_time:
                oldest_time = ingested_at
                oldest_doc = {"doc_id": doc_id, "ingested_at": ingested_at}
            
            if newest_time is None or ingested_at > newest_time:
                newest_time = ingested_at
                newest_doc = {"doc_id": doc_id, "ingested_at": ingested_at}
        except ValueError:
            continue
    
    return {
        "total_docs": total_docs,
        "stale_docs": stale_count,
        "oldest_doc": oldest_doc,
        "newest_doc": newest_doc,
    }