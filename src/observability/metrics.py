"""Response quality metrics module for autonomous driving knowledge retrieval system.

This module provides comprehensive response quality metrics recording including:
- Relevance scores (top-1, top-3, top-5 average relevance)
- Citation rate (percentage of responses with citations)
- Response time (p50, p95, p99 percentiles)
- Document diversity (source document count, document type distribution)
- Boost effectiveness (ranking changes before and after boost)

The metrics system integrates with the tracing infrastructure and provides
structured logging for observability, analysis, and optimization.
"""

from __future__ import annotations

import json
import logging
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.observability.logger import write_trace

logger = logging.getLogger(__name__)


# ── Data Models for Metrics ────────────────────────────────────────


@dataclass
class RelevanceMetrics:
    """Relevance score metrics for retrieval results.
    
    Attributes:
        top_1_score: Relevance score of the top-1 result
        top_3_avg_score: Average relevance score of top-3 results
        top_5_avg_score: Average relevance score of top-5 results
        min_score: Minimum relevance score in results
        max_score: Maximum relevance score in results
        score_distribution: Distribution of scores by range
    """
    top_1_score: float = 0.0
    top_3_avg_score: float = 0.0
    top_5_avg_score: float = 0.0
    min_score: float = 0.0
    max_score: float = 0.0
    score_distribution: Dict[str, int] = field(default_factory=dict)


@dataclass
class CitationMetrics:
    """Citation metrics for response quality.
    
    Attributes:
        has_citations: Whether the response has any citations
        citation_count: Number of citations in the response
        unique_sources: Number of unique source documents cited
        citation_rate: Percentage of responses with citations (calculated over time)
        avg_citations_per_response: Average number of citations per response
    """
    has_citations: bool = False
    citation_count: int = 0
    unique_sources: int = 0
    citation_rate: Optional[float] = None
    avg_citations_per_response: Optional[float] = None


@dataclass
class ResponseTimeMetrics:
    """Response time metrics for performance tracking.
    
    Attributes:
        response_time_ms: Response time for this query in milliseconds
        p50_ms: 50th percentile response time (median)
        p95_ms: 95th percentile response time
        p99_ms: 99th percentile response time
        stage_breakdown: Time breakdown by stage (analysis, retrieval, etc.)
    """
    response_time_ms: float = 0.0
    p50_ms: Optional[float] = None
    p95_ms: Optional[float] = None
    p99_ms: Optional[float] = None
    stage_breakdown: Dict[str, float] = field(default_factory=dict)


@dataclass
class DocumentDiversityMetrics:
    """Document diversity metrics for multi-document retrieval.
    
    Attributes:
        source_document_count: Number of unique source documents
        document_type_distribution: Distribution of document types
        chunks_per_document: Average chunks per document
        diversity_score: Diversity score (0-1, higher is more diverse)
        top_sources: Top source documents by chunk count
    """
    source_document_count: int = 0
    document_type_distribution: Dict[str, int] = field(default_factory=dict)
    chunks_per_document: float = 0.0
    diversity_score: float = 0.0
    top_sources: List[Tuple[str, int]] = field(default_factory=list)


@dataclass
class BoostEffectivenessMetrics:
    """Boost effectiveness metrics for metadata boost analysis.
    
    Attributes:
        boost_applied: Whether boost was applied
        query_type: Query type that triggered boost
        ranking_changes: Number of ranking position changes
        target_doc_improvement: Improvement in target document positions
        top_k_verification_passed: Whether top-K verification passed
        boost_impact_score: Overall boost impact score (0-1)
    """
    boost_applied: bool = False
    query_type: Optional[str] = None
    ranking_changes: int = 0
    target_doc_improvement: int = 0
    top_k_verification_passed: bool = False
    boost_impact_score: float = 0.0


@dataclass
class ResponseQualityMetrics:
    """Complete response quality metrics for a query.
    
    This is the top-level metrics object that contains all quality dimensions.
    
    Attributes:
        query_id: Unique identifier for this query
        timestamp: ISO 8601 timestamp when metrics were recorded
        collection: Collection name used for retrieval
        relevance: Relevance score metrics
        citation: Citation metrics
        response_time: Response time metrics
        document_diversity: Document diversity metrics
        boost_effectiveness: Boost effectiveness metrics
        query_complexity: Query complexity level
        response_type: Type of response generated
    """
    query_id: str
    timestamp: str
    collection: Optional[str] = None
    relevance: Optional[RelevanceMetrics] = None
    citation: Optional[CitationMetrics] = None
    response_time: Optional[ResponseTimeMetrics] = None
    document_diversity: Optional[DocumentDiversityMetrics] = None
    boost_effectiveness: Optional[BoostEffectivenessMetrics] = None
    query_complexity: Optional[str] = None
    response_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the metrics.
        """
        return asdict(self)



# ── Metrics Recorder Class ──────────────────────────────────────────


class MetricsRecorder:
    """Metrics recorder for tracking response quality metrics.
    
    This class provides methods to record various quality metrics dimensions
    and generate complete ResponseQualityMetrics objects for analysis.
    
    Example:
        >>> recorder = MetricsRecorder(query_id="query-123", collection="ad_knowledge_v01")
        >>> recorder.record_relevance(
        ...     scores=[0.85, 0.78, 0.72, 0.65, 0.58],
        ...     top_k=5
        ... )
        >>> recorder.record_citations(
        ...     citation_count=3,
        ...     unique_sources=2
        ... )
        >>> recorder.record_response_time(
        ...     total_ms=1250.5,
        ...     stage_breakdown={"analysis": 50.2, "retrieval": 800.3, "generation": 400.0}
        ... )
        >>> metrics = recorder.finalize()
        >>> write_metrics(metrics.to_dict())
    """
    
    def __init__(
        self,
        query_id: str,
        collection: Optional[str] = None,
    ) -> None:
        """Initialize metrics recorder.
        
        Args:
            query_id: Unique identifier for this query
            collection: Collection name used for retrieval
        """
        self.query_id = query_id
        self.collection = collection
        self.timestamp = datetime.now(timezone.utc).isoformat()
        
        # Metrics components
        self.relevance: Optional[RelevanceMetrics] = None
        self.citation: Optional[CitationMetrics] = None
        self.response_time: Optional[ResponseTimeMetrics] = None
        self.document_diversity: Optional[DocumentDiversityMetrics] = None
        self.boost_effectiveness: Optional[BoostEffectivenessMetrics] = None
        self.query_complexity: Optional[str] = None
        self.response_type: Optional[str] = None
    
    def record_relevance(
        self,
        scores: List[float],
        top_k: int = 5,
    ) -> None:
        """Record relevance score metrics.
        
        Args:
            scores: List of relevance scores (sorted descending)
            top_k: Number of top results to consider
        """
        if not scores:
            logger.warning(f"[{self.query_id}] No relevance scores provided")
            return
        
        # Calculate top-1, top-3, top-5 scores
        top_1_score = scores[0] if len(scores) >= 1 else 0.0
        top_3_scores = scores[:3] if len(scores) >= 3 else scores
        top_5_scores = scores[:5] if len(scores) >= 5 else scores
        
        top_3_avg = statistics.mean(top_3_scores) if top_3_scores else 0.0
        top_5_avg = statistics.mean(top_5_scores) if top_5_scores else 0.0
        
        # Calculate score distribution
        score_distribution = self._calculate_score_distribution(scores)
        
        self.relevance = RelevanceMetrics(
            top_1_score=top_1_score,
            top_3_avg_score=top_3_avg,
            top_5_avg_score=top_5_avg,
            min_score=min(scores),
            max_score=max(scores),
            score_distribution=score_distribution,
        )
        
        logger.debug(
            f"[{self.query_id}] Relevance metrics: "
            f"top-1={top_1_score:.3f}, top-3={top_3_avg:.3f}, top-5={top_5_avg:.3f}"
        )
    
    def record_citations(
        self,
        citation_count: int,
        unique_sources: int,
        citation_rate: Optional[float] = None,
        avg_citations_per_response: Optional[float] = None,
    ) -> None:
        """Record citation metrics.
        
        Args:
            citation_count: Number of citations in the response
            unique_sources: Number of unique source documents cited
            citation_rate: Overall citation rate (percentage of responses with citations)
            avg_citations_per_response: Average citations per response
        """
        has_citations = citation_count > 0
        
        self.citation = CitationMetrics(
            has_citations=has_citations,
            citation_count=citation_count,
            unique_sources=unique_sources,
            citation_rate=citation_rate,
            avg_citations_per_response=avg_citations_per_response,
        )
        
        logger.debug(
            f"[{self.query_id}] Citation metrics: "
            f"count={citation_count}, sources={unique_sources}, has_citations={has_citations}"
        )
    
    def record_response_time(
        self,
        total_ms: float,
        stage_breakdown: Optional[Dict[str, float]] = None,
        percentiles: Optional[Dict[str, float]] = None,
    ) -> None:
        """Record response time metrics.
        
        Args:
            total_ms: Total response time in milliseconds
            stage_breakdown: Time breakdown by stage
            percentiles: Percentile values (p50, p95, p99)
        """
        self.response_time = ResponseTimeMetrics(
            response_time_ms=total_ms,
            p50_ms=percentiles.get("p50") if percentiles else None,
            p95_ms=percentiles.get("p95") if percentiles else None,
            p99_ms=percentiles.get("p99") if percentiles else None,
            stage_breakdown=stage_breakdown or {},
        )
        
        logger.debug(
            f"[{self.query_id}] Response time: {total_ms:.2f}ms"
        )
    
    def record_document_diversity(
        self,
        source_documents: List[str],
        document_types: List[str],
        chunks_per_doc: Optional[Dict[str, int]] = None,
    ) -> None:
        """Record document diversity metrics.
        
        Args:
            source_documents: List of source document names
            document_types: List of document types (sensor_doc, algorithm_doc, etc.)
            chunks_per_doc: Mapping of document name to chunk count
        """
        source_count = len(set(source_documents))
        type_distribution = dict(Counter(document_types))
        
        # Calculate diversity score (Shannon entropy normalized)
        diversity_score = self._calculate_diversity_score(document_types)
        
        # Calculate average chunks per document
        avg_chunks = (
            statistics.mean(chunks_per_doc.values())
            if chunks_per_doc
            else 0.0
        )
        
        # Get top sources by chunk count
        top_sources = (
            sorted(chunks_per_doc.items(), key=lambda x: x[1], reverse=True)[:5]
            if chunks_per_doc
            else []
        )
        
        self.document_diversity = DocumentDiversityMetrics(
            source_document_count=source_count,
            document_type_distribution=type_distribution,
            chunks_per_document=avg_chunks,
            diversity_score=diversity_score,
            top_sources=top_sources,
        )
        
        logger.debug(
            f"[{self.query_id}] Document diversity: "
            f"sources={source_count}, diversity={diversity_score:.3f}"
        )

    
    def record_boost_effectiveness(
        self,
        boost_applied: bool,
        query_type: Optional[str] = None,
        before_ranks: Optional[List[Tuple[str, float]]] = None,
        after_ranks: Optional[List[Tuple[str, float]]] = None,
        target_doc_type: Optional[str] = None,
        top_k_verification_passed: bool = False,
    ) -> None:
        """Record boost effectiveness metrics.
        
        Args:
            boost_applied: Whether boost was applied
            query_type: Query type that triggered boost
            before_ranks: Rankings before boost [(doc_id, score), ...]
            after_ranks: Rankings after boost [(doc_id, score), ...]
            target_doc_type: Target document type for boost
            top_k_verification_passed: Whether top-K verification passed
        """
        ranking_changes = 0
        target_doc_improvement = 0
        boost_impact_score = 0.0
        
        if boost_applied and before_ranks and after_ranks:
            # Calculate ranking changes
            ranking_changes = self._calculate_ranking_changes(before_ranks, after_ranks)
            
            # Calculate target document improvement
            if target_doc_type:
                target_doc_improvement = self._calculate_target_improvement(
                    before_ranks, after_ranks, target_doc_type
                )
            
            # Calculate overall boost impact score
            boost_impact_score = self._calculate_boost_impact(
                ranking_changes, target_doc_improvement, top_k_verification_passed
            )
        
        self.boost_effectiveness = BoostEffectivenessMetrics(
            boost_applied=boost_applied,
            query_type=query_type,
            ranking_changes=ranking_changes,
            target_doc_improvement=target_doc_improvement,
            top_k_verification_passed=top_k_verification_passed,
            boost_impact_score=boost_impact_score,
        )
        
        logger.debug(
            f"[{self.query_id}] Boost effectiveness: "
            f"applied={boost_applied}, changes={ranking_changes}, "
            f"impact={boost_impact_score:.3f}"
        )
    
    def set_query_metadata(
        self,
        complexity: Optional[str] = None,
        response_type: Optional[str] = None,
    ) -> None:
        """Set query metadata.
        
        Args:
            complexity: Query complexity level
            response_type: Type of response generated
        """
        self.query_complexity = complexity
        self.response_type = response_type
    
    def finalize(self) -> ResponseQualityMetrics:
        """Finalize the metrics and return the complete ResponseQualityMetrics object.
        
        Returns:
            Complete ResponseQualityMetrics object ready for serialization.
        """
        metrics = ResponseQualityMetrics(
            query_id=self.query_id,
            timestamp=self.timestamp,
            collection=self.collection,
            relevance=self.relevance,
            citation=self.citation,
            response_time=self.response_time,
            document_diversity=self.document_diversity,
            boost_effectiveness=self.boost_effectiveness,
            query_complexity=self.query_complexity,
            response_type=self.response_type,
        )
        
        logger.info(
            f"[{self.query_id}] Response quality metrics finalized"
        )
        
        return metrics
    
    # ── Helper Methods ──────────────────────────────────────────────
    
    @staticmethod
    def _calculate_score_distribution(scores: List[float]) -> Dict[str, int]:
        """Calculate score distribution by range.
        
        Args:
            scores: List of relevance scores
        
        Returns:
            Distribution of scores by range (0.0-0.2, 0.2-0.4, etc.)
        """
        distribution = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0,
        }
        
        for score in scores:
            if score < 0.2:
                distribution["0.0-0.2"] += 1
            elif score < 0.4:
                distribution["0.2-0.4"] += 1
            elif score < 0.6:
                distribution["0.4-0.6"] += 1
            elif score < 0.8:
                distribution["0.6-0.8"] += 1
            else:
                distribution["0.8-1.0"] += 1
        
        return distribution
    
    @staticmethod
    def _calculate_diversity_score(document_types: List[str]) -> float:
        """Calculate diversity score using Shannon entropy.
        
        Args:
            document_types: List of document types
        
        Returns:
            Diversity score (0-1, higher is more diverse)
        """
        if not document_types:
            return 0.0
        
        # Calculate Shannon entropy
        type_counts = Counter(document_types)
        total = len(document_types)
        
        # If all same type, diversity is 0
        if len(type_counts) == 1:
            return 0.0
        
        entropy = 0.0
        
        for count in type_counts.values():
            if count > 0:
                p = count / total
                import math
                entropy -= p * math.log2(p)
        
        # Normalize by max entropy (log2 of number of unique types)
        max_entropy = math.log2(len(type_counts))
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
        
        return min(1.0, normalized_entropy)
    
    @staticmethod
    def _calculate_ranking_changes(
        before: List[Tuple[str, float]],
        after: List[Tuple[str, float]],
    ) -> int:
        """Calculate number of ranking position changes.
        
        Args:
            before: Rankings before boost [(doc_id, score), ...]
            after: Rankings after boost [(doc_id, score), ...]
        
        Returns:
            Number of documents that changed position
        """
        before_positions = {doc_id: i for i, (doc_id, _) in enumerate(before)}
        after_positions = {doc_id: i for i, (doc_id, _) in enumerate(after)}
        
        changes = 0
        for doc_id in before_positions:
            if doc_id in after_positions:
                if before_positions[doc_id] != after_positions[doc_id]:
                    changes += 1
        
        return changes
    
    @staticmethod
    def _calculate_target_improvement(
        before: List[Tuple[str, float]],
        after: List[Tuple[str, float]],
        target_doc_type: str,
    ) -> int:
        """Calculate improvement in target document positions.
        
        Args:
            before: Rankings before boost
            after: Rankings after boost
            target_doc_type: Target document type
        
        Returns:
            Number of positions improved for target documents
        """
        # This is a simplified calculation
        # In practice, you'd need document type information
        # For now, return 0 as placeholder
        return 0
    
    @staticmethod
    def _calculate_boost_impact(
        ranking_changes: int,
        target_improvement: int,
        top_k_passed: bool,
    ) -> float:
        """Calculate overall boost impact score.
        
        Args:
            ranking_changes: Number of ranking changes
            target_improvement: Target document improvement
            top_k_passed: Whether top-K verification passed
        
        Returns:
            Boost impact score (0-1)
        """
        # Simple scoring: 0.5 for top-K pass, 0.3 for changes, 0.2 for improvement
        score = 0.0
        
        if top_k_passed:
            score += 0.5
        
        if ranking_changes > 0:
            score += min(0.3, ranking_changes * 0.05)
        
        if target_improvement > 0:
            score += min(0.2, target_improvement * 0.05)
        
        return min(1.0, score)



# ── Metrics Aggregator Class ────────────────────────────────────────


class MetricsAggregator:
    """Aggregator for computing statistics over multiple queries.
    
    This class maintains a rolling window of metrics and computes
    aggregate statistics like percentiles, averages, and rates.
    
    Example:
        >>> aggregator = MetricsAggregator(window_size=100)
        >>> for metrics in query_metrics_list:
        ...     aggregator.add_metrics(metrics)
        >>> stats = aggregator.get_statistics()
        >>> print(f"Citation rate: {stats['citation_rate']:.2%}")
        >>> print(f"P95 response time: {stats['response_time_p95']:.2f}ms")
    """
    
    def __init__(self, window_size: int = 1000) -> None:
        """Initialize metrics aggregator.
        
        Args:
            window_size: Maximum number of metrics to keep in memory
        """
        self.window_size = window_size
        self.metrics_history: List[ResponseQualityMetrics] = []
        
        # Cached statistics
        self._stats_cache: Optional[Dict[str, Any]] = None
        self._cache_valid = False
    
    def add_metrics(self, metrics: ResponseQualityMetrics) -> None:
        """Add metrics to the aggregator.
        
        Args:
            metrics: ResponseQualityMetrics object to add
        """
        self.metrics_history.append(metrics)
        
        # Maintain window size
        if len(self.metrics_history) > self.window_size:
            self.metrics_history.pop(0)
        
        # Invalidate cache
        self._cache_valid = False
    
    def get_statistics(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get aggregate statistics over all metrics.
        
        Args:
            force_refresh: Force recalculation even if cache is valid
        
        Returns:
            Dictionary of aggregate statistics
        """
        if self._cache_valid and not force_refresh:
            return self._stats_cache
        
        if not self.metrics_history:
            return {}
        
        stats = {
            "total_queries": len(self.metrics_history),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        # Relevance statistics
        relevance_stats = self._compute_relevance_stats()
        stats.update(relevance_stats)
        
        # Citation statistics
        citation_stats = self._compute_citation_stats()
        stats.update(citation_stats)
        
        # Response time statistics
        response_time_stats = self._compute_response_time_stats()
        stats.update(response_time_stats)
        
        # Document diversity statistics
        diversity_stats = self._compute_diversity_stats()
        stats.update(diversity_stats)
        
        # Boost effectiveness statistics
        boost_stats = self._compute_boost_stats()
        stats.update(boost_stats)
        
        # Cache results
        self._stats_cache = stats
        self._cache_valid = True
        
        return stats
    
    def _compute_relevance_stats(self) -> Dict[str, Any]:
        """Compute relevance statistics.
        
        Returns:
            Dictionary of relevance statistics
        """
        top_1_scores = []
        top_3_scores = []
        top_5_scores = []
        
        for metrics in self.metrics_history:
            if metrics.relevance:
                top_1_scores.append(metrics.relevance.top_1_score)
                top_3_scores.append(metrics.relevance.top_3_avg_score)
                top_5_scores.append(metrics.relevance.top_5_avg_score)
        
        if not top_1_scores:
            return {}
        
        return {
            "relevance_top1_avg": statistics.mean(top_1_scores),
            "relevance_top1_median": statistics.median(top_1_scores),
            "relevance_top3_avg": statistics.mean(top_3_scores),
            "relevance_top5_avg": statistics.mean(top_5_scores),
        }
    
    def _compute_citation_stats(self) -> Dict[str, Any]:
        """Compute citation statistics.
        
        Returns:
            Dictionary of citation statistics
        """
        total_with_citations = 0
        total_citations = 0
        total_unique_sources = 0
        
        for metrics in self.metrics_history:
            if metrics.citation:
                if metrics.citation.has_citations:
                    total_with_citations += 1
                total_citations += metrics.citation.citation_count
                total_unique_sources += metrics.citation.unique_sources
        
        total_queries = len(self.metrics_history)
        
        return {
            "citation_rate": total_with_citations / total_queries if total_queries > 0 else 0.0,
            "avg_citations_per_response": total_citations / total_queries if total_queries > 0 else 0.0,
            "avg_unique_sources": total_unique_sources / total_queries if total_queries > 0 else 0.0,
        }
    
    def _compute_response_time_stats(self) -> Dict[str, Any]:
        """Compute response time statistics.
        
        Returns:
            Dictionary of response time statistics
        """
        response_times = []
        
        for metrics in self.metrics_history:
            if metrics.response_time:
                response_times.append(metrics.response_time.response_time_ms)
        
        if not response_times:
            return {}
        
        # Sort for percentile calculation
        sorted_times = sorted(response_times)
        n = len(sorted_times)
        
        return {
            "response_time_avg": statistics.mean(response_times),
            "response_time_median": statistics.median(response_times),
            "response_time_p50": sorted_times[int(n * 0.50)] if n > 0 else 0.0,
            "response_time_p95": sorted_times[int(n * 0.95)] if n > 0 else 0.0,
            "response_time_p99": sorted_times[int(n * 0.99)] if n > 0 else 0.0,
            "response_time_min": min(response_times),
            "response_time_max": max(response_times),
        }
    
    def _compute_diversity_stats(self) -> Dict[str, Any]:
        """Compute document diversity statistics.
        
        Returns:
            Dictionary of diversity statistics
        """
        source_counts = []
        diversity_scores = []
        doc_type_totals = Counter()
        
        for metrics in self.metrics_history:
            if metrics.document_diversity:
                source_counts.append(metrics.document_diversity.source_document_count)
                diversity_scores.append(metrics.document_diversity.diversity_score)
                doc_type_totals.update(metrics.document_diversity.document_type_distribution)
        
        if not source_counts:
            return {}
        
        return {
            "avg_source_documents": statistics.mean(source_counts),
            "avg_diversity_score": statistics.mean(diversity_scores),
            "document_type_distribution": dict(doc_type_totals),
        }
    
    def _compute_boost_stats(self) -> Dict[str, Any]:
        """Compute boost effectiveness statistics.
        
        Returns:
            Dictionary of boost statistics
        """
        total_boost_applied = 0
        total_top_k_passed = 0
        boost_impact_scores = []
        query_type_counts = Counter()
        
        for metrics in self.metrics_history:
            if metrics.boost_effectiveness:
                if metrics.boost_effectiveness.boost_applied:
                    total_boost_applied += 1
                    boost_impact_scores.append(metrics.boost_effectiveness.boost_impact_score)
                    
                    if metrics.boost_effectiveness.query_type:
                        query_type_counts[metrics.boost_effectiveness.query_type] += 1
                
                if metrics.boost_effectiveness.top_k_verification_passed:
                    total_top_k_passed += 1
        
        total_queries = len(self.metrics_history)
        
        stats = {
            "boost_application_rate": total_boost_applied / total_queries if total_queries > 0 else 0.0,
            "boost_top_k_pass_rate": total_top_k_passed / total_boost_applied if total_boost_applied > 0 else 0.0,
            "boost_query_type_distribution": dict(query_type_counts),
        }
        
        if boost_impact_scores:
            stats["avg_boost_impact_score"] = statistics.mean(boost_impact_scores)
        
        return stats
    
    def clear(self) -> None:
        """Clear all metrics history."""
        self.metrics_history.clear()
        self._stats_cache = None
        self._cache_valid = False



# ── Global Metrics Aggregator ──────────────────────────────────────


# Global aggregator instance for application-wide metrics
_global_aggregator: Optional[MetricsAggregator] = None


def get_global_aggregator() -> MetricsAggregator:
    """Get the global metrics aggregator instance.
    
    Returns:
        Global MetricsAggregator instance
    """
    global _global_aggregator
    if _global_aggregator is None:
        _global_aggregator = MetricsAggregator(window_size=1000)
    return _global_aggregator


def reset_global_aggregator() -> None:
    """Reset the global metrics aggregator."""
    global _global_aggregator
    _global_aggregator = None


# ── Convenience Functions ───────────────────────────────────────────


def create_metrics_recorder(
    query_id: str,
    collection: Optional[str] = None,
) -> MetricsRecorder:
    """Create a new MetricsRecorder instance.
    
    Args:
        query_id: Unique identifier for this query
        collection: Collection name used for retrieval
    
    Returns:
        MetricsRecorder instance ready for recording.
    """
    return MetricsRecorder(query_id=query_id, collection=collection)


def write_metrics(
    metrics: ResponseQualityMetrics,
    metrics_path: str | Path = "logs/metrics.jsonl",
) -> None:
    """Write ResponseQualityMetrics to the metrics file.
    
    Args:
        metrics: ResponseQualityMetrics object to write
        metrics_path: Path to the metrics file
    """
    write_trace(metrics.to_dict(), metrics_path)


def record_and_write_metrics(
    query_id: str,
    collection: Optional[str] = None,
    relevance_scores: Optional[List[float]] = None,
    citation_count: int = 0,
    unique_sources: int = 0,
    response_time_ms: float = 0.0,
    stage_breakdown: Optional[Dict[str, float]] = None,
    source_documents: Optional[List[str]] = None,
    document_types: Optional[List[str]] = None,
    boost_applied: bool = False,
    query_type: Optional[str] = None,
    query_complexity: Optional[str] = None,
    response_type: Optional[str] = None,
    metrics_path: str | Path = "logs/metrics.jsonl",
    add_to_global: bool = True,
) -> ResponseQualityMetrics:
    """Convenience function to record and write metrics in one call.
    
    Args:
        query_id: Unique identifier for this query
        collection: Collection name used for retrieval
        relevance_scores: List of relevance scores
        citation_count: Number of citations
        unique_sources: Number of unique sources
        response_time_ms: Total response time in milliseconds
        stage_breakdown: Time breakdown by stage
        source_documents: List of source document names
        document_types: List of document types
        boost_applied: Whether boost was applied
        query_type: Query type that triggered boost
        query_complexity: Query complexity level
        response_type: Type of response generated
        metrics_path: Path to the metrics file
        add_to_global: Whether to add to global aggregator
    
    Returns:
        Complete ResponseQualityMetrics object
    """
    recorder = create_metrics_recorder(query_id=query_id, collection=collection)
    
    # Record all provided metrics
    if relevance_scores:
        recorder.record_relevance(scores=relevance_scores)
    
    if citation_count > 0 or unique_sources > 0:
        recorder.record_citations(
            citation_count=citation_count,
            unique_sources=unique_sources,
        )
    
    if response_time_ms > 0:
        recorder.record_response_time(
            total_ms=response_time_ms,
            stage_breakdown=stage_breakdown,
        )
    
    if source_documents and document_types:
        recorder.record_document_diversity(
            source_documents=source_documents,
            document_types=document_types,
        )
    
    if boost_applied:
        recorder.record_boost_effectiveness(
            boost_applied=boost_applied,
            query_type=query_type,
        )
    
    recorder.set_query_metadata(
        complexity=query_complexity,
        response_type=response_type,
    )
    
    # Finalize and write
    metrics = recorder.finalize()
    write_metrics(metrics, metrics_path)
    
    # Add to global aggregator
    if add_to_global:
        aggregator = get_global_aggregator()
        aggregator.add_metrics(metrics)
    
    return metrics


def get_current_statistics() -> Dict[str, Any]:
    """Get current aggregate statistics from global aggregator.
    
    Returns:
        Dictionary of aggregate statistics
    """
    aggregator = get_global_aggregator()
    return aggregator.get_statistics()


def log_metrics_summary(
    logger_instance: Optional[logging.Logger] = None,
) -> None:
    """Log a summary of current metrics statistics.
    
    Args:
        logger_instance: Logger to use (defaults to module logger)
    """
    log = logger_instance or logger
    stats = get_current_statistics()
    
    if not stats:
        log.info("No metrics available")
        return
    
    log.info("=== Response Quality Metrics Summary ===")
    log.info(f"Total queries: {stats.get('total_queries', 0)}")
    
    # Relevance
    if "relevance_top1_avg" in stats:
        log.info(
            f"Relevance - Top-1: {stats['relevance_top1_avg']:.3f}, "
            f"Top-3: {stats['relevance_top3_avg']:.3f}, "
            f"Top-5: {stats['relevance_top5_avg']:.3f}"
        )
    
    # Citation
    if "citation_rate" in stats:
        log.info(
            f"Citation rate: {stats['citation_rate']:.2%}, "
            f"Avg citations: {stats['avg_citations_per_response']:.2f}"
        )
    
    # Response time
    if "response_time_p95" in stats:
        log.info(
            f"Response time - P50: {stats['response_time_p50']:.2f}ms, "
            f"P95: {stats['response_time_p95']:.2f}ms, "
            f"P99: {stats['response_time_p99']:.2f}ms"
        )
    
    # Document diversity
    if "avg_source_documents" in stats:
        log.info(
            f"Document diversity - Avg sources: {stats['avg_source_documents']:.2f}, "
            f"Diversity score: {stats['avg_diversity_score']:.3f}"
        )
    
    # Boost effectiveness
    if "boost_application_rate" in stats:
        log.info(
            f"Boost - Application rate: {stats['boost_application_rate']:.2%}, "
            f"Top-K pass rate: {stats['boost_top_k_pass_rate']:.2%}"
        )
    
    log.info("=" * 40)


# ── Module Initialization ───────────────────────────────────────────


# Initialize global aggregator on module import
_global_aggregator = MetricsAggregator(window_size=1000)

logger.info("Response quality metrics module initialized")
