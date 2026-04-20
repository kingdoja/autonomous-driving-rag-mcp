"""Run Autonomous Driving Knowledge Retrieval Evaluation.

Evaluation script for the autonomous driving knowledge retrieval system.
Tests core scenarios including sensor queries, algorithm queries, regulation queries,
and multi-document reasoning.

Usage::

    python scripts/run_ad_evaluation.py
    python scripts/run_ad_evaluation.py --verbose
    python scripts/run_ad_evaluation.py --p0-only
    python scripts/run_ad_evaluation.py --p1-only
    python scripts/run_ad_evaluation.py --output results.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.settings import load_settings
from src.core.query_engine.query_processor import QueryProcessor
from src.core.query_engine.hybrid_search import create_hybrid_search
from src.core.query_engine.dense_retriever import create_dense_retriever
from src.core.query_engine.sparse_retriever import create_sparse_retriever
from src.ingestion.storage.bm25_indexer import BM25Indexer
from src.libs.embedding.embedding_factory import EmbeddingFactory
from src.libs.vector_store.vector_store_factory import VectorStoreFactory

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_test_set(test_set_path: Path) -> Dict[str, Any]:
    """Load autonomous driving test set."""
    with test_set_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check_source_hit(results: List[Any], expected_sources: List[str]) -> bool:
    """Check if any expected source appears in results.
    
    Args:
        results: List of retrieval results
        expected_sources: List of expected source filenames
        
    Returns:
        True if at least one expected source is found in results
    """
    if not expected_sources:
        return True
    
    retrieved_sources = set()
    for result in results:
        if hasattr(result, 'metadata') and isinstance(result.metadata, dict):
            # Try both 'source' and 'source_path' keys
            source = result.metadata.get('source') or result.metadata.get('source_path', '')
        elif isinstance(result, dict):
            metadata = result.get('metadata', {})
            source = metadata.get('source') or metadata.get('source_path', '')
        else:
            continue
        
        if source:
            source_filename = Path(source).name
            retrieved_sources.add(source_filename)
    
    expected_set = set(expected_sources)
    return bool(expected_set & retrieved_sources)


def check_doc_type_hit(results: List[Any], expected_doc_types: List[str]) -> bool:
    """Check if expected document types appear in results.
    
    Args:
        results: List of retrieval results
        expected_doc_types: List of expected document types (sensor_doc, algorithm_doc, etc.)
        
    Returns:
        True if at least one expected document type is found in results
    """
    if not expected_doc_types:
        return True
    
    retrieved_doc_types = set()
    for result in results:
        if hasattr(result, 'metadata') and isinstance(result.metadata, dict):
            doc_type = result.metadata.get('doc_type') or result.metadata.get('document_type', '')
        elif isinstance(result, dict):
            metadata = result.get('metadata', {})
            doc_type = metadata.get('doc_type') or metadata.get('document_type', '')
        else:
            continue
        
        if doc_type:
            retrieved_doc_types.add(doc_type)
    
    expected_set = set(expected_doc_types)
    return bool(expected_set & retrieved_doc_types)


def check_source_diversity(results: List[Any], min_diversity: int) -> bool:
    """Check if results contain minimum number of unique sources.
    
    Args:
        results: List of retrieval results
        min_diversity: Minimum number of unique sources required
        
    Returns:
        True if number of unique sources >= min_diversity
    """
    unique_sources = set()
    for result in results:
        if hasattr(result, 'metadata') and isinstance(result.metadata, dict):
            source = result.metadata.get('source') or result.metadata.get('source_path', '')
        elif isinstance(result, dict):
            metadata = result.get('metadata', {})
            source = metadata.get('source') or metadata.get('source_path', '')
        else:
            continue
        
        if source:
            source_filename = Path(source).name
            unique_sources.add(source_filename)
    
    return len(unique_sources) >= min_diversity


def extract_top_sources(results: List[Any], top_k: int = 5) -> List[str]:
    """Extract top-k source filenames from results.
    
    Args:
        results: List of retrieval results
        top_k: Number of top sources to extract
        
    Returns:
        List of source filenames
    """
    top_sources = []
    for result in results[:top_k]:
        if hasattr(result, 'metadata') and isinstance(result.metadata, dict):
            source = result.metadata.get('source') or result.metadata.get('source_path', '')
        elif isinstance(result, dict):
            metadata = result.get('metadata', {})
            source = metadata.get('source') or metadata.get('source_path', '')
        else:
            continue
        
        if source:
            top_sources.append(Path(source).name)
    
    return top_sources


def extract_doc_types(results: List[Any], top_k: int = 5) -> List[str]:
    """Extract document types from top-k results.
    
    Args:
        results: List of retrieval results
        top_k: Number of top results to check
        
    Returns:
        List of document types
    """
    doc_types = []
    for result in results[:top_k]:
        if hasattr(result, 'metadata') and isinstance(result.metadata, dict):
            doc_type = result.metadata.get('doc_type') or result.metadata.get('document_type', '')
        elif isinstance(result, dict):
            metadata = result.get('metadata', {})
            doc_type = metadata.get('doc_type') or metadata.get('document_type', '')
        else:
            continue
        
        if doc_type:
            doc_types.append(doc_type)
    
    return doc_types


def run_evaluation(
    test_set_path: Path,
    p0_only: bool = False,
    p1_only: bool = False,
    verbose: bool = False
) -> Dict[str, Any]:
    """Run autonomous driving evaluation.
    
    Args:
        test_set_path: Path to test set JSON
        p0_only: Only evaluate P0 priority scenarios
        p1_only: Only evaluate P1 priority scenarios
        verbose: Enable verbose logging
        
    Returns:
        Evaluation results summary with metrics
    """
    # Load test set
    test_data = load_test_set(test_set_path)
    test_cases = test_data["test_cases"]
    
    if p0_only:
        test_cases = [tc for tc in test_cases if tc.get("priority") == "P0"]
    elif p1_only:
        test_cases = [tc for tc in test_cases if tc.get("priority") == "P1"]
    
    logger.info(f"Loaded {len(test_cases)} test cases")
    
    # Initialize search engine with AD config
    try:
        # Load AD knowledge config
        import os
        ad_config_path = "config/settings.ad_knowledge.yaml"
        if not os.path.exists(ad_config_path):
            logger.warning(f"AD config not found: {ad_config_path}, using default config")
            settings = load_settings()
        else:
            logger.info(f"Using AD config: {ad_config_path}")
            settings = load_settings(path=ad_config_path)
        
        # Use ad_knowledge_v01 collection
        collection_name = "ad_knowledge_v01"
        logger.info(f"Using collection: {collection_name}")
        
        # Build components
        vector_store = VectorStoreFactory.create(
            settings,
            collection_name=collection_name,
        )
        
        embedding_client = EmbeddingFactory.create(settings)
        dense_retriever = create_dense_retriever(
            settings=settings,
            embedding_client=embedding_client,
            vector_store=vector_store,
        )
        
        bm25_indexer = BM25Indexer(index_dir=f"data/db/bm25/{collection_name}")
        sparse_retriever = create_sparse_retriever(
            settings=settings,
            bm25_indexer=bm25_indexer,
            vector_store=vector_store,
        )
        sparse_retriever.default_collection = collection_name
        
        query_processor = QueryProcessor()
        search = create_hybrid_search(
            settings=settings,
            query_processor=query_processor,
            dense_retriever=dense_retriever,
            sparse_retriever=sparse_retriever,
        )
        
        logger.info(f"Initialized HybridSearch successfully")
    except Exception as exc:
        logger.error(f"Failed to initialize search engine: {exc}")
        return {"error": str(exc)}
    
    # Run evaluation
    results = []
    hit_count = 0
    retrieval_case_count = 0
    diversity_pass_count = 0
    diversity_case_count = 0
    
    for tc in test_cases:
        scenario_id = tc["scenario_id"]
        query = tc["query"]
        expected_sources = tc.get("expected_sources", [])
        expected_doc_types = tc.get("expected_doc_types", [])
        min_source_diversity = tc.get("min_source_diversity", 0)
        validation_type = tc.get("validation_type")
        
        # Skip boundary scenarios for retrieval evaluation
        if validation_type in ["response_boundary", "response_content"]:
            if verbose:
                logger.info(f"Skipping {scenario_id} (boundary/content validation)")
            continue
        
        retrieval_case_count += 1
        
        try:
            # Run search
            search_results = search.search(query=query, top_k=10)
            
            # Check source hit
            source_hit = check_source_hit(search_results, expected_sources)
            
            # Check doc type hit
            doc_type_hit = check_doc_type_hit(search_results, expected_doc_types)
            
            # Overall hit: both source and doc type must match
            hit = source_hit and doc_type_hit
            
            if hit:
                hit_count += 1
            
            # Check source diversity for multi-document scenarios
            diversity_pass = True
            if min_source_diversity > 0:
                diversity_case_count += 1
                diversity_pass = check_source_diversity(search_results, min_source_diversity)
                if diversity_pass:
                    diversity_pass_count += 1
            
            # Extract top sources and doc types
            top_sources = extract_top_sources(search_results, top_k=5)
            top_doc_types = extract_doc_types(search_results, top_k=5)
            
            result_entry = {
                "scenario_id": scenario_id,
                "query": query,
                "expected_sources": expected_sources,
                "expected_doc_types": expected_doc_types,
                "top_sources": top_sources,
                "top_doc_types": top_doc_types,
                "source_hit": source_hit,
                "doc_type_hit": doc_type_hit,
                "hit": hit,
                "num_results": len(search_results),
                "min_source_diversity": min_source_diversity,
                "diversity_pass": diversity_pass if min_source_diversity > 0 else None,
            }
            
            results.append(result_entry)
            
            if verbose or not hit:
                status = "✓" if hit else "✗"
                logger.info(f"{status} {scenario_id}: {query[:50]}...")
                logger.info(f"  Expected sources: {expected_sources}")
                logger.info(f"  Expected doc types: {expected_doc_types}")
                logger.info(f"  Top 5 sources: {top_sources}")
                logger.info(f"  Top 5 doc types: {top_doc_types}")
                if min_source_diversity > 0:
                    diversity_status = "✓" if diversity_pass else "✗"
                    logger.info(f"  {diversity_status} Diversity: {len(set(top_sources))} >= {min_source_diversity}")
            
        except Exception as exc:
            logger.error(f"Search failed for {scenario_id}: {exc}")
            results.append({
                "scenario_id": scenario_id,
                "query": query,
                "error": str(exc),
                "hit": False,
                "diversity_pass": False if min_source_diversity > 0 else None,
            })
    
    # Calculate metrics
    hit_rate = hit_count / retrieval_case_count if retrieval_case_count > 0 else 0.0
    diversity_rate = diversity_pass_count / diversity_case_count if diversity_case_count > 0 else 0.0
    
    # Determine priority mode
    priority_mode = "P0" if p0_only else ("P1" if p1_only else "All")
    
    summary = {
        "total_cases": len(test_cases),
        "retrieval_cases": retrieval_case_count,
        "hit_count": hit_count,
        "hit_rate": hit_rate,
        "diversity_cases": diversity_case_count,
        "diversity_pass_count": diversity_pass_count,
        "diversity_rate": diversity_rate,
        "priority_mode": priority_mode,
        "results": results,
    }
    
    return summary


def print_summary(summary: Dict[str, Any]) -> None:
    """Print evaluation summary with detailed metrics."""
    print("\n" + "=" * 70)
    print("Autonomous Driving Knowledge Retrieval Evaluation Summary")
    print("=" * 70)
    
    if "error" in summary:
        print(f"ERROR: {summary['error']}")
        return
    
    priority_mode = summary.get("priority_mode", "All")
    print(f"Priority Mode: {priority_mode}")
    print(f"Total Test Cases: {summary['total_cases']}")
    print(f"Retrieval Cases: {summary['retrieval_cases']}")
    print(f"Hit Count: {summary['hit_count']}")
    print(f"Hit Rate: {summary['hit_rate']:.2%}")
    
    if summary.get('diversity_cases', 0) > 0:
        print(f"\nMulti-Document Diversity:")
        print(f"  Diversity Cases: {summary['diversity_cases']}")
        print(f"  Diversity Pass Count: {summary['diversity_pass_count']}")
        print(f"  Diversity Rate: {summary['diversity_rate']:.2%}")
    
    print("=" * 70)
    
    # Print failed cases
    failed_cases = [r for r in summary['results'] if not r.get('hit', False)]
    if failed_cases:
        print(f"\nFailed Cases ({len(failed_cases)}):")
        for result in failed_cases:
            print(f"  [FAIL] {result['scenario_id']}: {result['query'][:60]}...")
            if 'error' in result:
                print(f"    Error: {result['error']}")
            else:
                print(f"    Expected sources: {result.get('expected_sources', [])}")
                print(f"    Expected doc types: {result.get('expected_doc_types', [])}")
                print(f"    Got sources: {result.get('top_sources', [])}")
                print(f"    Got doc types: {result.get('top_doc_types', [])}")
                if result.get('min_source_diversity', 0) > 0:
                    diversity_status = "PASS" if result.get('diversity_pass') else "FAIL"
                    print(f"    Diversity: {diversity_status} (min: {result['min_source_diversity']})")
    
    # Print passed cases
    passed_cases = [r for r in summary['results'] if r.get('hit', False)]
    if passed_cases:
        print(f"\nPassed Cases ({len(passed_cases)}):")
        for result in passed_cases:
            print(f"  [PASS] {result['scenario_id']}: {result['query'][:60]}...")
            if result.get('min_source_diversity', 0) > 0:
                diversity_status = "PASS" if result.get('diversity_pass') else "FAIL"
                print(f"    Diversity: {diversity_status} (sources: {len(set(result.get('top_sources', [])))})")
    
    print("\n" + "=" * 70)
    
    # Print overall assessment
    hit_rate = summary['hit_rate']
    diversity_rate = summary.get('diversity_rate', 1.0)
    
    if hit_rate >= 0.8 and diversity_rate >= 0.8:
        print("✓ EVALUATION PASSED: Hit rate >= 80% and diversity rate >= 80%")
    else:
        print("✗ EVALUATION FAILED:")
        if hit_rate < 0.8:
            print(f"  - Hit rate {hit_rate:.2%} below 80% threshold")
        if diversity_rate < 0.8:
            print(f"  - Diversity rate {diversity_rate:.2%} below 80% threshold")
    
    print("=" * 70)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run autonomous driving knowledge retrieval evaluation"
    )
    parser.add_argument(
        "--test-set",
        type=Path,
        default=Path("tests/fixtures/ad_test_set.json"),
        help="Path to test set JSON file"
    )
    parser.add_argument(
        "--p0-only",
        action="store_true",
        help="Only evaluate P0 priority scenarios"
    )
    parser.add_argument(
        "--p1-only",
        action="store_true",
        help="Only evaluate P1 priority scenarios"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Save results to JSON file"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run evaluation
    summary = run_evaluation(
        test_set_path=args.test_set,
        p0_only=args.p0_only,
        p1_only=args.p1_only,
        verbose=args.verbose
    )
    
    # Print summary
    print_summary(summary)
    
    # Save results if requested
    if args.output:
        with args.output.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {args.output}")
    
    # Exit with error code if evaluation failed
    if "error" not in summary:
        priority_mode = summary.get("priority_mode", "All")
        # Set threshold based on priority mode
        if priority_mode == "P0":
            min_hit_rate = 1.0  # 100% for P0
            min_diversity_rate = 1.0  # 100% for P0
        elif priority_mode == "P1":
            min_hit_rate = 0.6  # 60% for P1
            min_diversity_rate = 0.6  # 60% for P1
        else:
            min_hit_rate = 0.8  # 80% for all scenarios
            min_diversity_rate = 0.8  # 80% for all scenarios
        
        hit_rate = summary['hit_rate']
        diversity_rate = summary.get('diversity_rate', 1.0)
        
        if hit_rate < min_hit_rate:
            logger.error(f"Hit rate {hit_rate:.2%} below threshold {min_hit_rate:.2%}")
            sys.exit(1)
        
        if diversity_rate < min_diversity_rate:
            logger.error(f"Diversity rate {diversity_rate:.2%} below threshold {min_diversity_rate:.2%}")
            sys.exit(1)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
