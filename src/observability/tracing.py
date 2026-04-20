"""Query tracing module for autonomous driving knowledge retrieval system.

This module provides comprehensive query tracing capabilities including:
- Complete query flow tracking (analysis, retrieval, reranking, generation)
- Metadata boost application tracking (query type, boost weights, top-K verification)
- Boundary refusal event tracking (refusal type, detected patterns, query content)
- Document grouping tracking (source document count, chunks per document)

The tracing system integrates with the existing TraceContext infrastructure
and provides structured logging for observability and debugging.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.observability.logger import get_trace_logger, write_trace

logger = logging.getLogger(__name__)


# ── Data Models for Tracing ────────────────────────────────────────


@dataclass
class QueryAnalysisTrace:
    """Trace data for query analysis stage.
    
    Attributes:
        complexity: Query complexity level (simple, multi_part, comparison, aggregation)
        intent: Query intent (retrieval, boundary, scope_inquiry)
        requires_multi_doc: Whether query requires multiple documents
        detected_keywords: Keywords detected in the query
        query_type: Detected query type (sensor_query, algorithm_query, etc.)
        elapsed_ms: Time taken for analysis in milliseconds
    """
    complexity: str
    intent: str
    requires_multi_doc: bool
    detected_keywords: List[str]
    query_type: Optional[str] = None
    elapsed_ms: float = 0.0


@dataclass
class MetadataBoostTrace:
    """Trace data for metadata boost application.
    
    Attributes:
        boost_applied: Whether boost was applied
        query_type: Detected query type (sensor_query, algorithm_query, regulation_query)
        boost_config: Boost weights applied (e.g., {"sensor_doc": 1.5})
        top_k_verification: Top-K verification result
        target_doc_count: Number of target document type in top-K
        total_top_k: Total number of results in top-K
        fallback_used: Whether fallback to standard retrieval was used
        elapsed_ms: Time taken for boost application in milliseconds
    """
    boost_applied: bool
    query_type: Optional[str] = None
    boost_config: Dict[str, float] = field(default_factory=dict)
    top_k_verification: Optional[Dict[str, Any]] = None
    target_doc_count: int = 0
    total_top_k: int = 0
    fallback_used: bool = False
    elapsed_ms: float = 0.0


@dataclass
class BoundaryRefusalTrace:
    """Trace data for boundary refusal events.
    
    Attributes:
        refusal_occurred: Whether a refusal occurred
        refusal_type: Type of refusal (predictive, diagnostic, low_relevance)
        detected_pattern: Pattern that triggered the refusal
        query_content: The query that was refused (truncated for privacy)
        confidence: Confidence score of the refusal decision
        suggested_alternatives: Alternative query suggestions provided
        elapsed_ms: Time taken for boundary validation in milliseconds
    """
    refusal_occurred: bool
    refusal_type: Optional[str] = None
    detected_pattern: Optional[str] = None
    query_content: Optional[str] = None
    confidence: float = 0.0
    suggested_alternatives: List[str] = field(default_factory=list)
    elapsed_ms: float = 0.0


@dataclass
class DocumentGroupingTrace:
    """Trace data for document grouping.
    
    Attributes:
        grouping_applied: Whether document grouping was applied
        source_document_count: Number of unique source documents
        chunks_per_document: Mapping of document name to chunk count
        diversity_enforced: Whether diversity enforcement was applied
        min_docs_required: Minimum number of documents required
        min_docs_met: Whether minimum document requirement was met
        elapsed_ms: Time taken for document grouping in milliseconds
    """
    grouping_applied: bool
    source_document_count: int = 0
    chunks_per_document: Dict[str, int] = field(default_factory=dict)
    diversity_enforced: bool = False
    min_docs_required: int = 0
    min_docs_met: bool = False
    elapsed_ms: float = 0.0


@dataclass
class RetrievalTrace:
    """Trace data for retrieval stage.
    
    Attributes:
        method: Retrieval method (dense, sparse, hybrid)
        provider: Provider name (e.g., azure_openai, bm25)
        top_k: Number of results requested
        result_count: Number of results returned
        filters_applied: Filters applied during retrieval
        elapsed_ms: Time taken for retrieval in milliseconds
    """
    method: str
    provider: Optional[str] = None
    top_k: int = 0
    result_count: int = 0
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    elapsed_ms: float = 0.0


@dataclass
class RerankingTrace:
    """Trace data for reranking stage.
    
    Attributes:
        method: Reranking method (cross_encoder, etc.)
        input_count: Number of chunks before reranking
        output_count: Number of chunks after reranking
        score_range: Score range after reranking (min, max)
        elapsed_ms: Time taken for reranking in milliseconds
    """
    method: str
    input_count: int = 0
    output_count: int = 0
    score_range: Optional[tuple[float, float]] = None
    elapsed_ms: float = 0.0


@dataclass
class ResponseGenerationTrace:
    """Trace data for response generation stage.
    
    Attributes:
        method: Generation method (llm, template, etc.)
        model: Model used for generation
        response_type: Type of response (standard, comparison, aggregation)
        citation_count: Number of citations included
        token_count: Number of tokens generated (if available)
        elapsed_ms: Time taken for generation in milliseconds
    """
    method: str
    model: Optional[str] = None
    response_type: str = "standard"
    citation_count: int = 0
    token_count: Optional[int] = None
    elapsed_ms: float = 0.0


@dataclass
class QueryTrace:
    """Complete trace for a query execution.
    
    This is the top-level trace object that contains all stages of query processing.
    
    Attributes:
        trace_id: Unique identifier for this trace
        timestamp: ISO 8601 timestamp when trace was created
        query: The original query string (truncated for privacy)
        collection: Collection name used for retrieval
        query_analysis: Query analysis trace data
        metadata_boost: Metadata boost trace data
        retrieval: Retrieval trace data
        reranking: Reranking trace data (if applied)
        document_grouping: Document grouping trace data (if applied)
        response_generation: Response generation trace data
        boundary_refusal: Boundary refusal trace data (if occurred)
        total_elapsed_ms: Total time for complete query processing
        error: Error message if query failed
    """
    trace_id: str
    timestamp: str
    query: str
    collection: Optional[str] = None
    query_analysis: Optional[QueryAnalysisTrace] = None
    metadata_boost: Optional[MetadataBoostTrace] = None
    retrieval: Optional[RetrievalTrace] = None
    reranking: Optional[RerankingTrace] = None
    document_grouping: Optional[DocumentGroupingTrace] = None
    response_generation: Optional[ResponseGenerationTrace] = None
    boundary_refusal: Optional[BoundaryRefusalTrace] = None
    total_elapsed_ms: float = 0.0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the trace.
        """
        return asdict(self)


# ── Query Tracer Class ──────────────────────────────────────────────


class QueryTracer:
    """Query tracer for tracking complete query execution flow.
    
    This class provides methods to record each stage of query processing
    and generate a complete trace for observability and debugging.
    
    Example:
        >>> tracer = QueryTracer(trace_id="query-123", query="LiDAR探测距离")
        >>> tracer.record_query_analysis(
        ...     complexity="simple",
        ...     intent="retrieval",
        ...     requires_multi_doc=False,
        ...     detected_keywords=["LiDAR", "探测距离"],
        ...     query_type="sensor_query",
        ...     elapsed_ms=15.2
        ... )
        >>> tracer.record_metadata_boost(
        ...     boost_applied=True,
        ...     query_type="sensor_query",
        ...     boost_config={"sensor_doc": 1.5},
        ...     target_doc_count=2,
        ...     total_top_k=3,
        ...     elapsed_ms=8.5
        ... )
        >>> trace = tracer.finalize(total_elapsed_ms=250.0)
        >>> write_trace(trace.to_dict())
    """
    
    def __init__(
        self,
        trace_id: str,
        query: str,
        collection: Optional[str] = None,
        max_query_length: int = 200,
    ) -> None:
        """Initialize query tracer.
        
        Args:
            trace_id: Unique identifier for this trace
            query: The original query string
            collection: Collection name used for retrieval
            max_query_length: Maximum length of query to store (for privacy)
        """
        self.trace_id = trace_id
        self.query = query[:max_query_length] if len(query) > max_query_length else query
        self.collection = collection
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.start_time = time.monotonic()
        
        # Stage traces
        self.query_analysis: Optional[QueryAnalysisTrace] = None
        self.metadata_boost: Optional[MetadataBoostTrace] = None
        self.retrieval: Optional[RetrievalTrace] = None
        self.reranking: Optional[RerankingTrace] = None
        self.document_grouping: Optional[DocumentGroupingTrace] = None
        self.response_generation: Optional[ResponseGenerationTrace] = None
        self.boundary_refusal: Optional[BoundaryRefusalTrace] = None
        self.error: Optional[str] = None
    
    def record_query_analysis(
        self,
        complexity: str,
        intent: str,
        requires_multi_doc: bool,
        detected_keywords: List[str],
        query_type: Optional[str] = None,
        elapsed_ms: float = 0.0,
    ) -> None:
        """Record query analysis stage.
        
        Args:
            complexity: Query complexity level
            intent: Query intent
            requires_multi_doc: Whether query requires multiple documents
            detected_keywords: Keywords detected in the query
            query_type: Detected query type (sensor_query, algorithm_query, etc.)
            elapsed_ms: Time taken for analysis in milliseconds
        """
        self.query_analysis = QueryAnalysisTrace(
            complexity=complexity,
            intent=intent,
            requires_multi_doc=requires_multi_doc,
            detected_keywords=detected_keywords,
            query_type=query_type,
            elapsed_ms=elapsed_ms,
        )
        logger.debug(
            f"[{self.trace_id}] Query analysis: complexity={complexity}, "
            f"intent={intent}, query_type={query_type}"
        )
    
    def record_metadata_boost(
        self,
        boost_applied: bool,
        query_type: Optional[str] = None,
        boost_config: Optional[Dict[str, float]] = None,
        top_k_verification: Optional[Dict[str, Any]] = None,
        target_doc_count: int = 0,
        total_top_k: int = 0,
        fallback_used: bool = False,
        elapsed_ms: float = 0.0,
    ) -> None:
        """Record metadata boost application.
        
        Args:
            boost_applied: Whether boost was applied
            query_type: Detected query type
            boost_config: Boost weights applied
            top_k_verification: Top-K verification result
            target_doc_count: Number of target document type in top-K
            total_top_k: Total number of results in top-K
            fallback_used: Whether fallback to standard retrieval was used
            elapsed_ms: Time taken for boost application in milliseconds
        """
        self.metadata_boost = MetadataBoostTrace(
            boost_applied=boost_applied,
            query_type=query_type,
            boost_config=boost_config or {},
            top_k_verification=top_k_verification,
            target_doc_count=target_doc_count,
            total_top_k=total_top_k,
            fallback_used=fallback_used,
            elapsed_ms=elapsed_ms,
        )
        logger.debug(
            f"[{self.trace_id}] Metadata boost: applied={boost_applied}, "
            f"query_type={query_type}, target_docs={target_doc_count}/{total_top_k}"
        )
    
    def record_retrieval(
        self,
        method: str,
        provider: Optional[str] = None,
        top_k: int = 0,
        result_count: int = 0,
        filters_applied: Optional[Dict[str, Any]] = None,
        elapsed_ms: float = 0.0,
    ) -> None:
        """Record retrieval stage.
        
        Args:
            method: Retrieval method (dense, sparse, hybrid)
            provider: Provider name
            top_k: Number of results requested
            result_count: Number of results returned
            filters_applied: Filters applied during retrieval
            elapsed_ms: Time taken for retrieval in milliseconds
        """
        self.retrieval = RetrievalTrace(
            method=method,
            provider=provider,
            top_k=top_k,
            result_count=result_count,
            filters_applied=filters_applied or {},
            elapsed_ms=elapsed_ms,
        )
        logger.debug(
            f"[{self.trace_id}] Retrieval: method={method}, "
            f"provider={provider}, results={result_count}/{top_k}"
        )
    
    def record_reranking(
        self,
        method: str,
        input_count: int,
        output_count: int,
        score_range: Optional[tuple[float, float]] = None,
        elapsed_ms: float = 0.0,
    ) -> None:
        """Record reranking stage.
        
        Args:
            method: Reranking method
            input_count: Number of chunks before reranking
            output_count: Number of chunks after reranking
            score_range: Score range after reranking (min, max)
            elapsed_ms: Time taken for reranking in milliseconds
        """
        self.reranking = RerankingTrace(
            method=method,
            input_count=input_count,
            output_count=output_count,
            score_range=score_range,
            elapsed_ms=elapsed_ms,
        )
        logger.debug(
            f"[{self.trace_id}] Reranking: method={method}, "
            f"input={input_count}, output={output_count}"
        )
    
    def record_document_grouping(
        self,
        grouping_applied: bool,
        source_document_count: int = 0,
        chunks_per_document: Optional[Dict[str, int]] = None,
        diversity_enforced: bool = False,
        min_docs_required: int = 0,
        min_docs_met: bool = False,
        elapsed_ms: float = 0.0,
    ) -> None:
        """Record document grouping stage.
        
        Args:
            grouping_applied: Whether document grouping was applied
            source_document_count: Number of unique source documents
            chunks_per_document: Mapping of document name to chunk count
            diversity_enforced: Whether diversity enforcement was applied
            min_docs_required: Minimum number of documents required
            min_docs_met: Whether minimum document requirement was met
            elapsed_ms: Time taken for document grouping in milliseconds
        """
        self.document_grouping = DocumentGroupingTrace(
            grouping_applied=grouping_applied,
            source_document_count=source_document_count,
            chunks_per_document=chunks_per_document or {},
            diversity_enforced=diversity_enforced,
            min_docs_required=min_docs_required,
            min_docs_met=min_docs_met,
            elapsed_ms=elapsed_ms,
        )
        logger.debug(
            f"[{self.trace_id}] Document grouping: applied={grouping_applied}, "
            f"docs={source_document_count}, diversity={diversity_enforced}"
        )
    
    def record_response_generation(
        self,
        method: str,
        model: Optional[str] = None,
        response_type: str = "standard",
        citation_count: int = 0,
        token_count: Optional[int] = None,
        elapsed_ms: float = 0.0,
    ) -> None:
        """Record response generation stage.
        
        Args:
            method: Generation method (llm, template, etc.)
            model: Model used for generation
            response_type: Type of response (standard, comparison, aggregation)
            citation_count: Number of citations included
            token_count: Number of tokens generated (if available)
            elapsed_ms: Time taken for generation in milliseconds
        """
        self.response_generation = ResponseGenerationTrace(
            method=method,
            model=model,
            response_type=response_type,
            citation_count=citation_count,
            token_count=token_count,
            elapsed_ms=elapsed_ms,
        )
        logger.debug(
            f"[{self.trace_id}] Response generation: method={method}, "
            f"type={response_type}, citations={citation_count}"
        )
    
    def record_boundary_refusal(
        self,
        refusal_occurred: bool,
        refusal_type: Optional[str] = None,
        detected_pattern: Optional[str] = None,
        query_content: Optional[str] = None,
        confidence: float = 0.0,
        suggested_alternatives: Optional[List[str]] = None,
        elapsed_ms: float = 0.0,
    ) -> None:
        """Record boundary refusal event.
        
        Args:
            refusal_occurred: Whether a refusal occurred
            refusal_type: Type of refusal (predictive, diagnostic, low_relevance)
            detected_pattern: Pattern that triggered the refusal
            query_content: The query that was refused (truncated for privacy)
            confidence: Confidence score of the refusal decision
            suggested_alternatives: Alternative query suggestions provided
            elapsed_ms: Time taken for boundary validation in milliseconds
        """
        self.boundary_refusal = BoundaryRefusalTrace(
            refusal_occurred=refusal_occurred,
            refusal_type=refusal_type,
            detected_pattern=detected_pattern,
            query_content=query_content[:100] if query_content else None,
            confidence=confidence,
            suggested_alternatives=suggested_alternatives or [],
            elapsed_ms=elapsed_ms,
        )
        if refusal_occurred:
            logger.info(
                f"[{self.trace_id}] Boundary refusal: type={refusal_type}, "
                f"pattern={detected_pattern}, confidence={confidence:.2f}"
            )
    
    def record_error(self, error: str) -> None:
        """Record an error that occurred during query processing.
        
        Args:
            error: Error message
        """
        self.error = error
        logger.error(f"[{self.trace_id}] Query error: {error}")
    
    def finalize(self, total_elapsed_ms: Optional[float] = None) -> QueryTrace:
        """Finalize the trace and return the complete QueryTrace object.
        
        Args:
            total_elapsed_ms: Total elapsed time in milliseconds. If None,
                calculated from start_time.
        
        Returns:
            Complete QueryTrace object ready for serialization.
        """
        if total_elapsed_ms is None:
            total_elapsed_ms = (time.monotonic() - self.start_time) * 1000.0
        
        trace = QueryTrace(
            trace_id=self.trace_id,
            timestamp=self.timestamp,
            query=self.query,
            collection=self.collection,
            query_analysis=self.query_analysis,
            metadata_boost=self.metadata_boost,
            retrieval=self.retrieval,
            reranking=self.reranking,
            document_grouping=self.document_grouping,
            response_generation=self.response_generation,
            boundary_refusal=self.boundary_refusal,
            total_elapsed_ms=total_elapsed_ms,
            error=self.error,
        )
        
        logger.info(
            f"[{self.trace_id}] Query trace finalized: "
            f"total_time={total_elapsed_ms:.2f}ms, error={self.error is not None}"
        )
        
        return trace


# ── Convenience Functions ───────────────────────────────────────────


def create_query_tracer(
    trace_id: str,
    query: str,
    collection: Optional[str] = None,
) -> QueryTracer:
    """Create a new QueryTracer instance.
    
    Args:
        trace_id: Unique identifier for this trace
        query: The original query string
        collection: Collection name used for retrieval
    
    Returns:
        QueryTracer instance ready for recording.
    """
    return QueryTracer(trace_id=trace_id, query=query, collection=collection)


def write_query_trace(
    trace: QueryTrace,
    traces_path: str | Path = "logs/traces.jsonl",
) -> None:
    """Write a QueryTrace to the traces file.
    
    Args:
        trace: QueryTrace object to write
        traces_path: Path to the traces file
    """
    write_trace(trace.to_dict(), traces_path)


def log_query_trace(
    trace: QueryTrace,
    logger_name: str = "modular-rag.trace",
) -> None:
    """Log a QueryTrace using the trace logger.
    
    Args:
        trace: QueryTrace object to log
        logger_name: Name of the logger to use
    """
    trace_logger = get_trace_logger(name=logger_name)
    trace_logger.info(
        "Query trace",
        extra=trace.to_dict(),
    )
