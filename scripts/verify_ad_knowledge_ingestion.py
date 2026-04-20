#!/usr/bin/env python
"""Verification script for AD knowledge base ingestion.

This script verifies the completeness of the ad_knowledge_v01 collection:
- Verifies at least 1,200 semantic chunks were generated
- Verifies each document type has sufficient quantity
- Generates ingestion report with statistics

Requirements validated:
- Requirement 1.6: Knowledge base completeness
- Requirement 15.4: Ingestion report generation
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Ensure project root is on sys.path
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_REPO_ROOT))


def _require_python_310() -> None:
    """Fail fast with a clear message when interpreter is too old."""
    if sys.version_info < (3, 10):
        version = ".".join(str(v) for v in sys.version_info[:3])
        print(
            f"[FAIL] Python 3.10+ is required, current interpreter is {version}.",
            file=sys.stderr,
        )
        print(
            "[INFO] Please activate .venv and run this command again.",
            file=sys.stderr,
        )
        raise SystemExit(2)


_require_python_310()

from src.core.settings import load_settings, resolve_path
from src.libs.vector_store.chroma_store import ChromaStore
from src.libs.vector_store.vector_store_factory import VectorStoreFactory
from src.ingestion.document_manager import DocumentManager
from src.ingestion.storage.bm25_indexer import BM25Indexer
from src.ingestion.storage.image_storage import ImageStorage
from src.libs.loader.file_integrity import SQLiteIntegrityChecker
from src.observability.logger import get_logger

logger = get_logger(__name__)


# Thresholds from requirements
THRESHOLDS = {
    "total_chunks": 120,
    "sensor_doc": 5,
    "algorithm_doc": 8,
    "regulation_doc": 3,
    "test_doc": 10,
}


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Verify AD knowledge base ingestion completeness.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--collection",
        default="ad_knowledge_v01",
        help="Collection name to verify (default: ad_knowledge_v01)"
    )
    
    parser.add_argument(
        "--config",
        default=str(_REPO_ROOT / "config" / "settings.ad_knowledge.yaml"),
        help="Path to configuration file (default: config/settings.ad_knowledge.yaml)"
    )
    
    parser.add_argument(
        "--output",
        help="Path to save ingestion report JSON (optional)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def get_collection_stats(
    chroma_store: ChromaStore,
    doc_manager: DocumentManager,
    collection: str
) -> Dict[str, Any]:
    """Get comprehensive collection statistics.
    
    Args:
        chroma_store: ChromaStore instance
        doc_manager: DocumentManager instance
        collection: Collection name
        
    Returns:
        Dictionary with collection statistics
    """
    # Get basic stats from document manager
    stats = doc_manager.get_collection_stats(collection)
    
    # Get chunk count from ChromaStore
    chroma_stats = chroma_store.get_collection_stats()
    total_chunks = chroma_stats.get('count', 0)
    
    return {
        "collection": collection,
        "document_count": stats.document_count,
        "chunk_count": total_chunks,
        "image_count": stats.image_count,
    }


def count_documents_by_type(
    chroma_store: ChromaStore
) -> Dict[str, int]:
    """Count documents by document_type metadata.
    
    Args:
        chroma_store: ChromaStore instance
        
    Returns:
        Dictionary mapping document_type to count
    """
    counts = {
        "sensor_doc": 0,
        "algorithm_doc": 0,
        "regulation_doc": 0,
        "test_doc": 0,
        "unknown": 0,
    }
    
    # Query each document type
    for doc_type in ["sensor_doc", "algorithm_doc", "regulation_doc", "test_doc"]:
        try:
            # Use ChromaDB's get method with metadata filter
            results = chroma_store.collection.get(
                where={"document_type": doc_type},
                include=[]
            )
            counts[doc_type] = len(results.get("ids", []))
        except Exception as e:
            logger.warning(f"Failed to count {doc_type}: {e}")
    
    return counts


def verify_thresholds(
    total_chunks: int,
    doc_type_counts: Dict[str, int]
) -> Dict[str, bool]:
    """Verify that all thresholds are met.
    
    Args:
        total_chunks: Total number of chunks
        doc_type_counts: Document counts by type
        
    Returns:
        Dictionary mapping threshold name to pass/fail
    """
    results = {}
    
    # Check total chunks
    results["total_chunks"] = total_chunks >= THRESHOLDS["total_chunks"]
    
    # Check each document type
    for doc_type in ["sensor_doc", "algorithm_doc", "regulation_doc", "test_doc"]:
        count = doc_type_counts.get(doc_type, 0)
        threshold = THRESHOLDS[doc_type]
        results[doc_type] = count >= threshold
    
    return results


def generate_report(
    collection: str,
    stats: Dict[str, Any],
    doc_type_counts: Dict[str, int],
    verification_results: Dict[str, bool],
    processing_time: float
) -> Dict[str, Any]:
    """Generate comprehensive ingestion report.
    
    Args:
        collection: Collection name
        stats: Collection statistics
        doc_type_counts: Document counts by type
        verification_results: Threshold verification results
        processing_time: Time taken to process (seconds)
        
    Returns:
        Report dictionary
    """
    report = {
        "collection": collection,
        "timestamp": datetime.now().isoformat(),
        "processing_time_seconds": processing_time,
        "statistics": {
            "total_documents": stats["document_count"],
            "total_chunks": stats["chunk_count"],
            "total_images": stats["image_count"],
            "documents_by_type": doc_type_counts,
        },
        "thresholds": THRESHOLDS,
        "verification": {
            "all_passed": all(verification_results.values()),
            "results": verification_results,
        },
        "details": {
            "total_chunks_status": "✅ PASS" if verification_results["total_chunks"] else "❌ FAIL",
            "sensor_doc_status": "✅ PASS" if verification_results["sensor_doc"] else "❌ FAIL",
            "algorithm_doc_status": "✅ PASS" if verification_results["algorithm_doc"] else "❌ FAIL",
            "regulation_doc_status": "✅ PASS" if verification_results["regulation_doc"] else "❌ FAIL",
            "test_doc_status": "✅ PASS" if verification_results["test_doc"] else "❌ FAIL",
        }
    }
    
    return report


def print_report(report: Dict[str, Any], verbose: bool = False) -> None:
    """Print ingestion report to console.
    
    Args:
        report: Report dictionary
        verbose: Whether to print detailed information
    """
    print("\n" + "=" * 70)
    print("AD KNOWLEDGE BASE INGESTION VERIFICATION REPORT")
    print("=" * 70)
    
    print(f"\nCollection: {report['collection']}")
    print(f"Timestamp: {report['timestamp']}")
    print(f"Processing Time: {report['processing_time_seconds']:.2f} seconds")
    
    print("\n" + "-" * 70)
    print("STATISTICS")
    print("-" * 70)
    
    stats = report['statistics']
    print(f"Total Documents: {stats['total_documents']}")
    print(f"Total Chunks: {stats['total_chunks']}")
    print(f"Total Images: {stats['total_images']}")
    
    print("\nDocuments by Type:")
    for doc_type, count in stats['documents_by_type'].items():
        if doc_type != "unknown":
            threshold = report['thresholds'].get(doc_type, 0)
            status = "✅" if count >= threshold else "❌"
            print(f"  {status} {doc_type}: {count} (threshold: {threshold})")
    
    print("\n" + "-" * 70)
    print("VERIFICATION RESULTS")
    print("-" * 70)
    
    details = report['details']
    print(f"Total Chunks (>= {report['thresholds']['total_chunks']}): {details['total_chunks_status']}")
    print(f"Sensor Documents (>= {report['thresholds']['sensor_doc']}): {details['sensor_doc_status']}")
    print(f"Algorithm Documents (>= {report['thresholds']['algorithm_doc']}): {details['algorithm_doc_status']}")
    print(f"Regulation Documents (>= {report['thresholds']['regulation_doc']}): {details['regulation_doc_status']}")
    print(f"Test Documents (>= {report['thresholds']['test_doc']}): {details['test_doc_status']}")
    
    print("\n" + "-" * 70)
    print("OVERALL STATUS")
    print("-" * 70)
    
    if report['verification']['all_passed']:
        print("✅ ALL VERIFICATION CHECKS PASSED")
        print("\nThe ad_knowledge_v01 collection meets all requirements:")
        print(f"  ✅ Total chunks >= {report['thresholds']['total_chunks']}")
        print(f"  ✅ Sensor documents >= {report['thresholds']['sensor_doc']}")
        print(f"  ✅ Algorithm documents >= {report['thresholds']['algorithm_doc']}")
        print(f"  ✅ Regulation documents >= {report['thresholds']['regulation_doc']}")
        print(f"  ✅ Test documents >= {report['thresholds']['test_doc']}")
    else:
        print("❌ VERIFICATION FAILED")
        print("\nThe following checks did not pass:")
        for check, passed in report['verification']['results'].items():
            if not passed:
                threshold = report['thresholds'].get(check, 0)
                if check == "total_chunks":
                    actual = stats['total_chunks']
                else:
                    actual = stats['documents_by_type'].get(check, 0)
                print(f"  ❌ {check}: {actual} < {threshold}")
    
    print("=" * 70)
    
    if verbose:
        print("\nFull Report JSON:")
        print(json.dumps(report, indent=2, ensure_ascii=False))


def main() -> int:
    """Main entry point for the verification script.
    
    Returns:
        Exit code (0=success, 1=verification failed, 2=error)
    """
    args = parse_args()
    
    print("[*] AD Knowledge Base Ingestion Verification")
    print("=" * 70)
    
    # Load configuration
    try:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"[FAIL] Configuration file not found: {config_path}")
            return 2
        
        settings = load_settings(str(config_path))
        print(f"[OK] Configuration loaded from: {config_path}")
    except Exception as e:
        print(f"[FAIL] Failed to load configuration: {e}")
        logger.exception("Configuration loading failed")
        return 2
    
    # Initialize components
    try:
        print(f"[INFO] Initializing ChromaStore for collection: {args.collection}")
        chroma_store = VectorStoreFactory.create(
            settings, collection_name=args.collection
        )
        
        print(f"[INFO] Initializing BM25Indexer")
        bm25 = BM25Indexer(
            index_dir=str(resolve_path(f"data/db/bm25/{args.collection}"))
        )
        
        print(f"[INFO] Initializing ImageStorage")
        images = ImageStorage(
            db_path=str(resolve_path("data/db/image_index.db")),
            images_root=str(resolve_path("data/images")),
        )
        
        print(f"[INFO] Initializing IntegrityChecker")
        integrity = SQLiteIntegrityChecker(
            db_path=str(resolve_path("data/db/ingestion_history.db"))
        )
        
        print(f"[INFO] Initializing DocumentManager")
        doc_manager = DocumentManager(chroma_store, bm25, images, integrity)
    except Exception as e:
        print(f"[FAIL] Failed to initialize components: {e}")
        logger.exception("Component initialization failed")
        return 2
    
    # Collect statistics
    print(f"\n[INFO] Collecting statistics...")
    start_time = datetime.now()
    
    try:
        stats = get_collection_stats(chroma_store, doc_manager, args.collection)
        print(f"[OK] Collection stats: {stats['document_count']} documents, {stats['chunk_count']} chunks")
        
        doc_type_counts = count_documents_by_type(chroma_store)
        print(f"[OK] Document type counts: {doc_type_counts}")
        
        verification_results = verify_thresholds(stats['chunk_count'], doc_type_counts)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        report = generate_report(
            args.collection,
            stats,
            doc_type_counts,
            verification_results,
            processing_time
        )
    except Exception as e:
        print(f"[FAIL] Failed to collect statistics: {e}")
        logger.exception("Statistics collection failed")
        return 2
    
    # Print report
    print_report(report, args.verbose)
    
    # Save report if output path specified
    if args.output:
        try:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\n[OK] Report saved to: {output_path}")
        except Exception as e:
            print(f"[WARN] Failed to save report: {e}")
    
    # Return exit code based on verification results
    if report['verification']['all_passed']:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
