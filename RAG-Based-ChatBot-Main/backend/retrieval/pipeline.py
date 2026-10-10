import logging
import asyncio
from typing import List, Dict, Any, Optional
from backend.config import settings
from backend.embeddings.embedder import embedder
from backend.retrieval.vector_store import vector_store
from backend.retrieval.bm25 import bm25_index
from backend.retrieval.fusion import reciprocal_rank_fusion, weighted_score_fusion
from backend.retrieval.dedup import deduplicate_chunks
from backend.retrieval.reranker import reranker

logger = logging.getLogger(__name__)

class RetrievalPipeline:
    def __init__(self):
        pass

    async def retrieve(
        self,
        queries: List[str],
        doc_ids: Optional[List[str]] = None,
        top_k: int = settings.FINAL_TOP_K,
        score_threshold: float = settings.SCORE_THRESHOLD,
        fusion_method: str = settings.FUSION_METHOD,
        alpha: float = settings.FUSION_ALPHA
    ) -> List[Dict[str, Any]]:
        """
        Full hybrid retrieval pipeline:
        1. Multi-query parallel retrieval (Vector top 30 + BM25 top 30)
        2. Reciprocal Rank Fusion / Weighted fusion
        3. Deduplication (chunk_id + text similarity)
        4. Cross-encoder reranking (top ~40)
        5. Top-K selection with score threshold
        """
        if not queries:
            return []

        primary_query = queries[0]
        ranking_lists: List[List[Dict[str, Any]]] = []
        all_vector_results: List[Dict[str, Any]] = []
        all_bm25_results: List[Dict[str, Any]] = []

        # Step 7: Parallel retrieval for each generated query
        async def fetch_query_results(q: str):
            # Vector search
            qvec = await asyncio.to_thread(embedder.embed_query, q)
            v_hits = await asyncio.to_thread(
                vector_store.search,
                query_vector=qvec,
                doc_ids=doc_ids,
                limit=settings.RETRIEVAL_TOP_K
            )
            # BM25 search
            b_hits = await asyncio.to_thread(
                bm25_index.search,
                query=q,
                doc_ids=doc_ids,
                limit=settings.RETRIEVAL_TOP_K
            )
            return v_hits, b_hits

        tasks = [fetch_query_results(q) for q in queries]
        results = await asyncio.gather(*tasks)

        for v_hits, b_hits in results:
            if v_hits:
                ranking_lists.append(v_hits)
                all_vector_results.extend(v_hits)
            if b_hits:
                ranking_lists.append(b_hits)
                all_bm25_results.extend(b_hits)

        total_retrieved = len(all_vector_results) + len(all_bm25_results)
        logger.info(f"[RETRIEVAL] Retrieved candidates: {total_retrieved} (vector: {len(all_vector_results)}, bm25: {len(all_bm25_results)})")

        if not ranking_lists:
            logger.info("[RETRIEVAL] No candidates retrieved from vector or lexical stores")
            return []

        # Step 8: Hybrid Fusion
        if fusion_method == "weighted":
            fused = weighted_score_fusion(all_vector_results, all_bm25_results, alpha=alpha)
            logger.info(f"[FUSION] Weighted fusion candidates: {len(fused)}")
        else:
            fused = reciprocal_rank_fusion(ranking_lists, k=settings.RRF_K)
            logger.info(f"[RRF] Fused candidates: {len(fused)}")

        # Step 9: Deduplication
        deduped = deduplicate_chunks(fused, similarity_threshold=settings.DEDUP_SIMILARITY_THRESHOLD)

        # Step 10: Cross-Encoder Reranker on top ~15
        top_candidates = deduped[:15]
        rescored = await asyncio.to_thread(reranker.rerank, primary_query, top_candidates, 15)
        logger.info(f"[RERANK] Candidates reranked: {len(top_candidates)}")

        # Step 11: Top-K Selection & Score Thresholding
        filtered = [c for c in rescored if c.get("score", 0.0) >= score_threshold]
        logger.info(f"[THRESHOLD] Accepted: {len(filtered)} (threshold={score_threshold})")
        final_top = filtered[:top_k]
        logger.info(f"[CONTEXT] Final context chunks: {len(final_top)} (top_k={top_k})")

        return final_top

retrieval_pipeline = RetrievalPipeline()
