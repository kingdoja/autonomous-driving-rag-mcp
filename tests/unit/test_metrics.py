"""Unit tests for response quality metrics module."""

import pytest
from src.observability.metrics import (
    MetricsRecorder,
    MetricsAggregator,
    RelevanceMetrics,
    CitationMetrics,
    ResponseTimeMetrics,
    DocumentDiversityMetrics,
    BoostEffectivenessMetrics,
    create_metrics_recorder,
    get_global_aggregator,
)


class TestMetricsRecorder:
    """Tests for MetricsRecorder class."""
    
    def test_create_metrics_recorder(self):
        """Test creating a metrics recorder."""
        recorder = create_metrics_recorder(
            query_id="test-query-1",
            collection="ad_knowledge_v01"
        )
        
        assert recorder.query_id == "test-query-1"
        assert recorder.collection == "ad_knowledge_v01"
        assert recorder.timestamp is not None
    
    def test_record_relevance(self):
        """Test recording relevance metrics."""
        recorder = MetricsRecorder(query_id="test-query-1")
        
        scores = [0.85, 0.78, 0.72, 0.65, 0.58, 0.45, 0.32]
        recorder.record_relevance(scores=scores, top_k=5)
        
        assert recorder.relevance is not None
        assert recorder.relevance.top_1_score == 0.85
        assert recorder.relevance.top_3_avg_score == pytest.approx((0.85 + 0.78 + 0.72) / 3)
        assert recorder.relevance.top_5_avg_score == pytest.approx((0.85 + 0.78 + 0.72 + 0.65 + 0.58) / 5)
        assert recorder.relevance.min_score == 0.32
        assert recorder.relevance.max_score == 0.85
    
    def test_record_citations(self):
        """Test recording citation metrics."""
        recorder = MetricsRecorder(query_id="test-query-1")
        
        recorder.record_citations(
            citation_count=3,
            unique_sources=2,
            citation_rate=0.85,
            avg_citations_per_response=2.5
        )
        
        assert recorder.citation is not None
        assert recorder.citation.has_citations is True
        assert recorder.citation.citation_count == 3
        assert recorder.citation.unique_sources == 2
        assert recorder.citation.citation_rate == 0.85
        assert recorder.citation.avg_citations_per_response == 2.5
    
    def test_record_response_time(self):
        """Test recording response time metrics."""
        recorder = MetricsRecorder(query_id="test-query-1")
        
        stage_breakdown = {
            "analysis": 50.2,
            "retrieval": 800.3,
            "reranking": 150.0,
            "generation": 400.0
        }
        
        recorder.record_response_time(
            total_ms=1400.5,
            stage_breakdown=stage_breakdown,
            percentiles={"p50": 1200.0, "p95": 3500.0, "p99": 5000.0}
        )
        
        assert recorder.response_time is not None
        assert recorder.response_time.response_time_ms == 1400.5
        assert recorder.response_time.p50_ms == 1200.0
        assert recorder.response_time.p95_ms == 3500.0
        assert recorder.response_time.p99_ms == 5000.0
        assert recorder.response_time.stage_breakdown == stage_breakdown
    
    def test_record_document_diversity(self):
        """Test recording document diversity metrics."""
        recorder = MetricsRecorder(query_id="test-query-1")
        
        source_documents = ["doc1", "doc2", "doc1", "doc3", "doc2"]
        document_types = ["sensor_doc", "algorithm_doc", "sensor_doc", "regulation_doc", "algorithm_doc"]
        chunks_per_doc = {"doc1": 2, "doc2": 2, "doc3": 1}
        
        recorder.record_document_diversity(
            source_documents=source_documents,
            document_types=document_types,
            chunks_per_doc=chunks_per_doc
        )
        
        assert recorder.document_diversity is not None
        assert recorder.document_diversity.source_document_count == 3
        assert recorder.document_diversity.document_type_distribution["sensor_doc"] == 2
        assert recorder.document_diversity.document_type_distribution["algorithm_doc"] == 2
        assert recorder.document_diversity.document_type_distribution["regulation_doc"] == 1
        assert recorder.document_diversity.chunks_per_document == pytest.approx((2 + 2 + 1) / 3)
    
    def test_record_boost_effectiveness(self):
        """Test recording boost effectiveness metrics."""
        recorder = MetricsRecorder(query_id="test-query-1")
        
        before_ranks = [("doc1", 0.75), ("doc2", 0.70), ("doc3", 0.65)]
        after_ranks = [("doc2", 0.85), ("doc1", 0.80), ("doc3", 0.70)]
        
        recorder.record_boost_effectiveness(
            boost_applied=True,
            query_type="sensor_query",
            before_ranks=before_ranks,
            after_ranks=after_ranks,
            target_doc_type="sensor_doc",
            top_k_verification_passed=True
        )
        
        assert recorder.boost_effectiveness is not None
        assert recorder.boost_effectiveness.boost_applied is True
        assert recorder.boost_effectiveness.query_type == "sensor_query"
        assert recorder.boost_effectiveness.top_k_verification_passed is True
        assert recorder.boost_effectiveness.ranking_changes > 0
    
    def test_finalize(self):
        """Test finalizing metrics."""
        recorder = MetricsRecorder(query_id="test-query-1", collection="ad_knowledge_v01")
        
        recorder.record_relevance(scores=[0.85, 0.78, 0.72])
        recorder.record_citations(citation_count=2, unique_sources=2)
        recorder.set_query_metadata(complexity="simple", response_type="standard")
        
        metrics = recorder.finalize()
        
        assert metrics.query_id == "test-query-1"
        assert metrics.collection == "ad_knowledge_v01"
        assert metrics.relevance is not None
        assert metrics.citation is not None
        assert metrics.query_complexity == "simple"
        assert metrics.response_type == "standard"
        
        # Test to_dict conversion
        metrics_dict = metrics.to_dict()
        assert isinstance(metrics_dict, dict)
        assert metrics_dict["query_id"] == "test-query-1"


class TestMetricsAggregator:
    """Tests for MetricsAggregator class."""
    
    def test_create_aggregator(self):
        """Test creating a metrics aggregator."""
        aggregator = MetricsAggregator(window_size=100)
        
        assert aggregator.window_size == 100
        assert len(aggregator.metrics_history) == 0
    
    def test_add_metrics(self):
        """Test adding metrics to aggregator."""
        aggregator = MetricsAggregator(window_size=10)
        
        for i in range(5):
            recorder = MetricsRecorder(query_id=f"query-{i}")
            recorder.record_relevance(scores=[0.8, 0.7, 0.6])
            recorder.record_citations(citation_count=2, unique_sources=1)
            metrics = recorder.finalize()
            aggregator.add_metrics(metrics)
        
        assert len(aggregator.metrics_history) == 5
    
    def test_window_size_limit(self):
        """Test that aggregator respects window size limit."""
        aggregator = MetricsAggregator(window_size=5)
        
        for i in range(10):
            recorder = MetricsRecorder(query_id=f"query-{i}")
            recorder.record_relevance(scores=[0.8])
            metrics = recorder.finalize()
            aggregator.add_metrics(metrics)
        
        assert len(aggregator.metrics_history) == 5
    
    def test_get_statistics(self):
        """Test getting aggregate statistics."""
        aggregator = MetricsAggregator(window_size=100)
        
        # Add some test metrics
        for i in range(10):
            recorder = MetricsRecorder(query_id=f"query-{i}")
            recorder.record_relevance(scores=[0.8, 0.7, 0.6])
            recorder.record_citations(citation_count=2 if i % 2 == 0 else 0, unique_sources=1)
            recorder.record_response_time(total_ms=1000.0 + i * 100)
            metrics = recorder.finalize()
            aggregator.add_metrics(metrics)
        
        stats = aggregator.get_statistics()
        
        assert stats["total_queries"] == 10
        assert "relevance_top1_avg" in stats
        assert "citation_rate" in stats
        assert "response_time_p95" in stats
        assert stats["citation_rate"] == 0.5  # 5 out of 10 have citations
    
    def test_clear(self):
        """Test clearing aggregator."""
        aggregator = MetricsAggregator(window_size=100)
        
        recorder = MetricsRecorder(query_id="query-1")
        recorder.record_relevance(scores=[0.8])
        metrics = recorder.finalize()
        aggregator.add_metrics(metrics)
        
        assert len(aggregator.metrics_history) > 0
        
        aggregator.clear()
        
        assert len(aggregator.metrics_history) == 0


class TestGlobalAggregator:
    """Tests for global aggregator functions."""
    
    def test_get_global_aggregator(self):
        """Test getting global aggregator."""
        aggregator = get_global_aggregator()
        
        assert aggregator is not None
        assert isinstance(aggregator, MetricsAggregator)
        
        # Should return same instance
        aggregator2 = get_global_aggregator()
        assert aggregator is aggregator2


class TestHelperMethods:
    """Tests for helper methods."""
    
    def test_calculate_score_distribution(self):
        """Test score distribution calculation."""
        scores = [0.95, 0.85, 0.75, 0.55, 0.35, 0.15]
        
        distribution = MetricsRecorder._calculate_score_distribution(scores)
        
        assert distribution["0.8-1.0"] == 2  # 0.95, 0.85
        assert distribution["0.6-0.8"] == 1  # 0.75
        assert distribution["0.4-0.6"] == 1  # 0.55
        assert distribution["0.2-0.4"] == 1  # 0.35
        assert distribution["0.0-0.2"] == 1  # 0.15
    
    def test_calculate_diversity_score(self):
        """Test diversity score calculation."""
        # Uniform distribution (high diversity)
        doc_types = ["sensor_doc", "algorithm_doc", "regulation_doc", "test_doc"]
        score = MetricsRecorder._calculate_diversity_score(doc_types)
        assert score > 0.5
        
        # All same type (low diversity)
        doc_types = ["sensor_doc", "sensor_doc", "sensor_doc"]
        score = MetricsRecorder._calculate_diversity_score(doc_types)
        assert score == 0.0
    
    def test_calculate_ranking_changes(self):
        """Test ranking changes calculation."""
        before = [("doc1", 0.75), ("doc2", 0.70), ("doc3", 0.65)]
        after = [("doc2", 0.85), ("doc1", 0.80), ("doc3", 0.70)]
        
        changes = MetricsRecorder._calculate_ranking_changes(before, after)
        
        assert changes == 2  # doc1 and doc2 changed positions
