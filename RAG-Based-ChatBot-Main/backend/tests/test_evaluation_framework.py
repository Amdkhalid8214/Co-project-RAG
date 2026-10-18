"""
Unit & Integration Tests for RAG Retrieval Evaluation Framework
Tests:
1. Hit Rate@K (Recall@K) calculation accuracy.
2. Mean Reciprocal Rank (MRR@K) score computation.
3. NDCG@K discounting and ideal DCG calculation.
4. Keyword evidence coverage across retrieved chunks.
5. Benchmark dataset integrity and golden evaluation dataset loading.
"""
import pytest
from backend.eval.retrieval_eval import (
    calculate_hit_rate_at_k,
    calculate_reciprocal_rank,
    calculate_ndcg_at_k,
    calculate_keyword_coverage,
    load_golden_dataset,
    evaluate_retrieval_results
)


def test_hit_rate_at_k():
    retrieved = ["doc_c", "doc_a", "doc_b"]
    # doc_a is at index 1 (rank 2)
    assert calculate_hit_rate_at_k(retrieved, ["doc_a"], k=1) == 0.0
    assert calculate_hit_rate_at_k(retrieved, ["doc_a"], k=2) == 1.0
    assert calculate_hit_rate_at_k(retrieved, ["doc_a"], k=5) == 1.0
    assert calculate_hit_rate_at_k(retrieved, ["doc_missing"], k=3) == 0.0


def test_reciprocal_rank():
    retrieved = ["doc_c", "doc_a", "doc_b"]
    # doc_c is rank 0 -> 1.0
    assert calculate_reciprocal_rank(retrieved, ["doc_c"], k=3) == 1.0
    # doc_a is rank 1 -> 1 / (1 + 1) = 0.5
    assert calculate_reciprocal_rank(retrieved, ["doc_a"], k=3) == 0.5
    # doc_b is rank 2 -> 1 / (2 + 1) = 1/3 ~ 0.3333
    assert calculate_reciprocal_rank(retrieved, ["doc_b"], k=3) == pytest.approx(1.0 / 3.0, rel=1e-3)
    # doc_x is not in top 3 -> 0.0
    assert calculate_reciprocal_rank(retrieved, ["doc_x"], k=3) == 0.0


def test_ndcg_at_k():
    retrieved = ["doc_c", "doc_a", "doc_b"]
    # Perfect retrieval: ground truth at rank 0
    assert calculate_ndcg_at_k(retrieved, ["doc_c"], k=3) == 1.0
    # Ground truth at rank 1: dcg = 1 / log2(3), idcg = 1 / log2(2) = 1.0 -> ndcg = 1 / log2(3) ~ 0.6309
    ndcg_rank1 = calculate_ndcg_at_k(retrieved, ["doc_a"], k=3)
    assert ndcg_rank1 > 0.0
    assert ndcg_rank1 < 1.0
    # Completely missing ground truth
    assert calculate_ndcg_at_k(retrieved, ["doc_none"], k=3) == 0.0


def test_keyword_coverage():
    texts = [
        "DocuChat AI uses Qwen2.5:7b with a 32k context window for reasoning.",
        "The model is deployed with vLLM or Ollama."
    ]
    kws = ["qwen2.5:7b", "32k", "ollama"]
    cov = calculate_keyword_coverage(texts, kws)
    assert cov == 1.0

    kws_partial = ["qwen2.5:7b", "32k", "unrelated_keyword_xyz"]
    cov_partial = calculate_keyword_coverage(texts, kws_partial)
    assert cov_partial == pytest.approx(2.0 / 3.0, rel=1e-3)


def test_golden_dataset_schema():
    dataset = load_golden_dataset()
    assert len(dataset) >= 5
    for item in dataset:
        assert "id" in item
        assert "query" in item
        assert "reference_answer" in item
        assert isinstance(item.get("ground_truth_chunk_ids"), list)


def test_evaluate_retrieval_results():
    cases = [
        {"id": "1", "ground_truth_chunk_ids": ["c1"], "ground_truth_keywords": ["rag"]},
        {"id": "2", "ground_truth_chunk_ids": ["c2"], "ground_truth_keywords": ["hybrid"]}
    ]
    outputs = [
        {"retrieved_ids": ["c1", "other"], "retrieved_texts": ["rag pipeline"], "latency_ms": 25.0},
        {"retrieved_ids": ["other", "c2"], "retrieved_texts": ["hybrid search"], "latency_ms": 35.0}
    ]
    summary = evaluate_retrieval_results(cases, outputs, k_list=[1, 2])
    assert summary["num_cases"] == 2
    assert summary["metrics_by_k"][1]["hit_rate"] == 0.5  # 1 hit out of 2 in top-1
    assert summary["metrics_by_k"][2]["hit_rate"] == 1.0  # 2 hits out of 2 in top-2
    assert summary["avg_latency_ms"] == 30.0
    assert summary["avg_keyword_coverage"] == 1.0
