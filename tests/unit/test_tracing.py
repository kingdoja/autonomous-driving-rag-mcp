"""Unit tests for query tracing module.

Tests cover:
- QueryTracer initialization and stage recording
- Trace data model serialization
- Complete query flow tracing
- Metadata boost tracking
- Boundary refusal tracking
- Document grouping tracking
"""

import json
import time
from pathlib import Path

import pytest

from src.observability.tracing import (
    BoundaryRefusalTrace,
    DocumentGroupingTrace,
    MetadataBoostTrace,
    QueryAnalysisTrace,
    QueryTrace,
    QueryTracer,
    RerankingTrace,
    ResponseGenerationTrace,
    RetrievalTrace,
    create_query_tracer,
    write_query_trace,
)


class TestQueryAnalysisTrace:
    """Tests for QueryAnalysisTrace data model."""
    
    def test_query_analysis_trace_creation(self):
        """Test creating a QueryAnalysisTrace."""
        trace = QueryAnalysisTrace(
            complexity="simple",
            intent="retrieval",
            requires_multi_doc=False,
            detected_keywords=["LiDAR", "探测距离"],
            query_type="sensor_query",
            elapsed_ms=15.2,
        )
        
        assert trace.complexity == "simple"
        assert trace.intent == "retrieval"
        assert trace.requires_multi_doc is False
        assert trace.detected_keywords == ["LiDAR", "探测距离"]
        assert trace.query_type == "sensor_query"
        assert trace.elapsed_ms == 15.2
    
    def test_query_analysis_trace_optional_fields(self):
        """Test QueryAnalysisTrace with optional fields."""
        trace = QueryAnalysisTrace(
            complexity="multi_part",
            intent="retrieval",
            requires_multi_doc=True,
            detected_keywords=["感知", "规划"],
        )
        
        assert trace.query_type is None
        assert trace.elapsed_ms == 0.0


class TestMetadataBoostTrace:
    """Tests for MetadataBoostTrace data model."""
    
    def test_metadata_boost_trace_applied(self):
        """Test MetadataBoostTrace when boost is applied."""
        trace = MetadataBoostTrace(
            boost_applied=True,
            query_type="sensor_query",
            boost_config={"sensor_doc": 1.5, "algorithm_doc": 0.8},
            top_k_verification={"passed": True, "threshold": 2},
            target_doc_count=2,
            total_top_k=3,
            fallback_used=False,
            elapsed_ms=8.5,
        )
        
        assert trace.boost_applied is True
        assert trace.query_type == "sensor_query"
        assert trace.boost_config == {"sensor_doc": 1.5, "algorithm_doc": 0.8}
        assert trace.target_doc_count == 2
        assert trace.total_top_k == 3
        assert trace.fallback_used is False
    
    def test_metadata_boost_trace_not_applied(self):
        """Test MetadataBoostTrace when boost is not applied."""
        trace = MetadataBoostTrace(
            boost_applied=False,
            fallback_used=True,
        )
        
        assert trace.boost_applied is False
        assert trace.query_type is None
        assert trace.boost_config == {}
        assert trace.fallback_used is True


class TestBoundaryRefusalTrace:
    """Tests for BoundaryRefusalTrace data model."""
    
    def test_boundary_refusal_trace_occurred(self):
        """Test BoundaryRefusalTrace when refusal occurred."""
        trace = BoundaryRefusalTrace(
            refusal_occurred=True,
            refusal_type="predictive",
            detected_pattern="预测未来趋势",
            query_content="预测下一代LiDAR技术",
            confidence=0.95,
            suggested_alternatives=["查询当前LiDAR技术", "查询LiDAR技术原理"],
            elapsed_ms=5.2,
        )
        
        assert trace.refusal_occurred is True
        assert trace.refusal_type == "predictive"
        assert trace.detected_pattern == "预测未来趋势"
        assert trace.confidence == 0.95
        assert len(trace.suggested_alternatives) == 2
    
    def test_boundary_refusal_trace_not_occurred(self):
        """Test BoundaryRefusalTrace when no refusal occurred."""
        trace = BoundaryRefusalTrace(
            refusal_occurred=False,
        )
        
        assert trace.refusal_occurred is False
        assert trace.refusal_type is None
        assert trace.detected_pattern is None


class TestDocumentGroupingTrace:
    """Tests for DocumentGroupingTrace data model."""
    
    def test_document_grouping_trace_applied(self):
        """Test DocumentGroupingTrace when grouping is applied."""
        trace = DocumentGroupingTrace(
            grouping_applied=True,
            source_document_count=3,
            chunks_per_document={
                "lidar_spec.pdf": 2,
                "radar_spec.pdf": 2,
                "camera_spec.pdf": 1,
            },
            diversity_enforced=True,
            min_docs_required=2,
            min_docs_met=True,
            elapsed_ms=12.3,
        )
        
        assert trace.grouping_applied is True
        assert trace.source_document_count == 3
        assert len(trace.chunks_per_document) == 3
        assert trace.diversity_enforced is True
        assert trace.min_docs_met is True
    
    def test_document_grouping_trace_not_applied(self):
        """Test DocumentGroupingTrace when grouping is not applied."""
        trace = DocumentGroupingTrace(
            grouping_applied=False,
        )
        
        assert trace.grouping_applied is False
        assert trace.source_document_count == 0
        assert trace.chunks_per_document == {}


class TestQueryTracer:
    """Tests for QueryTracer class."""
    
    def test_query_tracer_initialization(self):
        """Test QueryTracer initialization."""
        tracer = QueryTracer(
            trace_id="test-trace-001",
            query="LiDAR的探测距离是多少？",
            collection="ad_knowledge_v01",
        )
        
        assert tracer.trace_id == "test-trace-001"
        assert tracer.query == "LiDAR的探测距离是多少？"
        assert tracer.collection == "ad_knowledge_v01"
        assert tracer.query_analysis is None
        assert tracer.metadata_boost is None
    
    def test_query_tracer_truncates_long_query(self):
        """Test that QueryTracer truncates long queries."""
        long_query = "A" * 300
        tracer = QueryTracer(
            trace_id="test-trace-002",
            query=long_query,
            max_query_length=200,
        )
        
        assert len(tracer.query) == 200
        assert tracer.query == "A" * 200
    
    def test_record_query_analysis(self):
        """Test recording query analysis stage."""
        tracer = QueryTracer(
            trace_id="test-trace-003",
            query="LiDAR vs 毫米波雷达",
        )
        
        tracer.record_query_analysis(
            complexity="comparison",
            intent="retrieval",
            requires_multi_doc=True,
            detected_keywords=["LiDAR", "毫米波雷达", "vs"],
            query_type="sensor_query",
            elapsed_ms=18.5,
        )
        
        assert tracer.query_analysis is not None
        assert tracer.query_analysis.complexity == "comparison"
        assert tracer.query_analysis.intent == "retrieval"
        assert tracer.query_analysis.requires_multi_doc is True
        assert tracer.query_analysis.query_type == "sensor_query"
    
    def test_record_metadata_boost(self):
        """Test recording metadata boost application."""
        tracer = QueryTracer(
            trace_id="test-trace-004",
            query="摄像头分辨率",
        )
        
        tracer.record_metadata_boost(
            boost_applied=True,
            query_type="sensor_query",
            boost_config={"sensor_doc": 1.5},
            target_doc_count=2,
            total_top_k=3,
            elapsed_ms=10.2,
        )
        
        assert tracer.metadata_boost is not None
        assert tracer.metadata_boost.boost_applied is True
        assert tracer.metadata_boost.query_type == "sensor_query"
        assert tracer.metadata_boost.target_doc_count == 2
    
    def test_record_retrieval(self):
        """Test recording retrieval stage."""
        tracer = QueryTracer(
            trace_id="test-trace-005",
            query="感知算法原理",
        )
        
        tracer.record_retrieval(
            method="hybrid",
            provider="azure_openai",
            top_k=20,
            result_count=18,
            filters_applied={"collection": "ad_knowledge_v01"},
            elapsed_ms=250.5,
        )
        
        assert tracer.retrieval is not None
        assert tracer.retrieval.method == "hybrid"
        assert tracer.retrieval.provider == "azure_openai"
        assert tracer.retrieval.result_count == 18
    
    def test_record_reranking(self):
        """Test recording reranking stage."""
        tracer = QueryTracer(
            trace_id="test-trace-006",
            query="ISO 26262标准",
        )
        
        tracer.record_reranking(
            method="cross_encoder",
            input_count=20,
            output_count=10,
            score_range=(0.65, 0.92),
            elapsed_ms=180.3,
        )
        
        assert tracer.reranking is not None
        assert tracer.reranking.method == "cross_encoder"
        assert tracer.reranking.input_count == 20
        assert tracer.reranking.output_count == 10
        assert tracer.reranking.score_range == (0.65, 0.92)
    
    def test_record_document_grouping(self):
        """Test recording document grouping stage."""
        tracer = QueryTracer(
            trace_id="test-trace-007",
            query="多传感器融合方案",
        )
        
        tracer.record_document_grouping(
            grouping_applied=True,
            source_document_count=4,
            chunks_per_document={
                "lidar.pdf": 2,
                "radar.pdf": 2,
                "camera.pdf": 1,
                "ultrasonic.pdf": 1,
            },
            diversity_enforced=True,
            min_docs_required=3,
            min_docs_met=True,
            elapsed_ms=15.8,
        )
        
        assert tracer.document_grouping is not None
        assert tracer.document_grouping.grouping_applied is True
        assert tracer.document_grouping.source_document_count == 4
        assert tracer.document_grouping.diversity_enforced is True
    
    def test_record_response_generation(self):
        """Test recording response generation stage."""
        tracer = QueryTracer(
            trace_id="test-trace-008",
            query="路径规划算法",
        )
        
        tracer.record_response_generation(
            method="llm",
            model="gpt-4",
            response_type="standard",
            citation_count=3,
            token_count=450,
            elapsed_ms=1200.5,
        )
        
        assert tracer.response_generation is not None
        assert tracer.response_generation.method == "llm"
        assert tracer.response_generation.model == "gpt-4"
        assert tracer.response_generation.citation_count == 3
    
    def test_record_boundary_refusal(self):
        """Test recording boundary refusal event."""
        tracer = QueryTracer(
            trace_id="test-trace-009",
            query="预测下一代自动驾驶技术",
        )
        
        tracer.record_boundary_refusal(
            refusal_occurred=True,
            refusal_type="predictive",
            detected_pattern="预测",
            query_content="预测下一代自动驾驶技术",
            confidence=0.92,
            suggested_alternatives=["查询当前自动驾驶技术"],
            elapsed_ms=8.2,
        )
        
        assert tracer.boundary_refusal is not None
        assert tracer.boundary_refusal.refusal_occurred is True
        assert tracer.boundary_refusal.refusal_type == "predictive"
        assert tracer.boundary_refusal.confidence == 0.92
    
    def test_record_error(self):
        """Test recording an error."""
        tracer = QueryTracer(
            trace_id="test-trace-010",
            query="测试查询",
        )
        
        tracer.record_error("Retrieval failed: connection timeout")
        
        assert tracer.error == "Retrieval failed: connection timeout"
    
    def test_finalize_trace(self):
        """Test finalizing a complete trace."""
        tracer = QueryTracer(
            trace_id="test-trace-011",
            query="LiDAR标定方法",
            collection="ad_knowledge_v01",
        )
        
        # Record multiple stages
        tracer.record_query_analysis(
            complexity="simple",
            intent="retrieval",
            requires_multi_doc=False,
            detected_keywords=["LiDAR", "标定"],
            query_type="sensor_query",
            elapsed_ms=12.0,
        )
        
        tracer.record_metadata_boost(
            boost_applied=True,
            query_type="sensor_query",
            boost_config={"sensor_doc": 1.5},
            target_doc_count=2,
            total_top_k=3,
            elapsed_ms=8.0,
        )
        
        tracer.record_retrieval(
            method="hybrid",
            provider="azure_openai",
            top_k=10,
            result_count=10,
            elapsed_ms=200.0,
        )
        
        # Finalize
        trace = tracer.finalize(total_elapsed_ms=500.0)
        
        assert isinstance(trace, QueryTrace)
        assert trace.trace_id == "test-trace-011"
        assert trace.query == "LiDAR标定方法"
        assert trace.collection == "ad_knowledge_v01"
        assert trace.query_analysis is not None
        assert trace.metadata_boost is not None
        assert trace.retrieval is not None
        assert trace.total_elapsed_ms == 500.0
    
    def test_finalize_trace_auto_elapsed(self):
        """Test finalizing trace with auto-calculated elapsed time."""
        tracer = QueryTracer(
            trace_id="test-trace-012",
            query="测试查询",
        )
        
        # Simulate some processing time
        time.sleep(0.01)
        
        trace = tracer.finalize()
        
        assert trace.total_elapsed_ms > 0
        assert trace.total_elapsed_ms >= 10.0  # At least 10ms


class TestQueryTrace:
    """Tests for QueryTrace data model."""
    
    def test_query_trace_to_dict(self):
        """Test converting QueryTrace to dictionary."""
        trace = QueryTrace(
            trace_id="test-trace-013",
            timestamp="2024-01-15T10:30:00Z",
            query="LiDAR探测距离",
            collection="ad_knowledge_v01",
            query_analysis=QueryAnalysisTrace(
                complexity="simple",
                intent="retrieval",
                requires_multi_doc=False,
                detected_keywords=["LiDAR", "探测距离"],
                query_type="sensor_query",
                elapsed_ms=15.0,
            ),
            total_elapsed_ms=450.0,
        )
        
        trace_dict = trace.to_dict()
        
        assert isinstance(trace_dict, dict)
        assert trace_dict["trace_id"] == "test-trace-013"
        assert trace_dict["query"] == "LiDAR探测距离"
        assert trace_dict["collection"] == "ad_knowledge_v01"
        assert trace_dict["total_elapsed_ms"] == 450.0
        assert "query_analysis" in trace_dict
        assert trace_dict["query_analysis"]["complexity"] == "simple"
    
    def test_query_trace_serialization(self):
        """Test that QueryTrace can be serialized to JSON."""
        trace = QueryTrace(
            trace_id="test-trace-014",
            timestamp="2024-01-15T10:30:00Z",
            query="感知算法",
            collection="ad_knowledge_v01",
            metadata_boost=MetadataBoostTrace(
                boost_applied=True,
                query_type="algorithm_query",
                boost_config={"algorithm_doc": 1.3},
                target_doc_count=3,
                total_top_k=5,
                elapsed_ms=10.0,
            ),
            total_elapsed_ms=600.0,
        )
        
        # Should not raise exception
        json_str = json.dumps(trace.to_dict())
        assert isinstance(json_str, str)
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        assert parsed["trace_id"] == "test-trace-014"
        assert parsed["metadata_boost"]["boost_applied"] is True


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_create_query_tracer(self):
        """Test create_query_tracer convenience function."""
        tracer = create_query_tracer(
            trace_id="test-trace-015",
            query="测试查询",
            collection="test_collection",
        )
        
        assert isinstance(tracer, QueryTracer)
        assert tracer.trace_id == "test-trace-015"
        assert tracer.query == "测试查询"
        assert tracer.collection == "test_collection"
    
    def test_write_query_trace(self):
        """Test write_query_trace convenience function."""
        import tempfile
        import os
        
        trace = QueryTrace(
            trace_id="test-trace-016",
            timestamp="2024-01-15T10:30:00Z",
            query="测试查询",
            total_elapsed_ms=300.0,
        )
        
        # Use a temporary file in the current directory
        traces_file = Path("test_traces_temp.jsonl")
        try:
            write_query_trace(trace, traces_path=traces_file)
            
            # Verify file was created and contains trace
            assert traces_file.exists()
            
            with open(traces_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                assert len(lines) == 1
                
                parsed = json.loads(lines[0])
                assert parsed["trace_id"] == "test-trace-016"
                assert parsed["query"] == "测试查询"
        finally:
            # Clean up
            if traces_file.exists():
                traces_file.unlink()


class TestCompleteQueryFlow:
    """Integration tests for complete query flow tracing."""
    
    def test_complete_sensor_query_flow(self):
        """Test tracing a complete sensor query flow."""
        tracer = create_query_tracer(
            trace_id="flow-001",
            query="LiDAR的探测距离和分辨率",
            collection="ad_knowledge_v01",
        )
        
        # Stage 1: Query Analysis
        tracer.record_query_analysis(
            complexity="simple",
            intent="retrieval",
            requires_multi_doc=False,
            detected_keywords=["LiDAR", "探测距离", "分辨率"],
            query_type="sensor_query",
            elapsed_ms=15.0,
        )
        
        # Stage 2: Metadata Boost
        tracer.record_metadata_boost(
            boost_applied=True,
            query_type="sensor_query",
            boost_config={"sensor_doc": 1.5, "algorithm_doc": 0.8},
            top_k_verification={"passed": True, "threshold": 2},
            target_doc_count=3,
            total_top_k=3,
            fallback_used=False,
            elapsed_ms=8.0,
        )
        
        # Stage 3: Retrieval
        tracer.record_retrieval(
            method="hybrid",
            provider="azure_openai",
            top_k=20,
            result_count=18,
            filters_applied={"collection": "ad_knowledge_v01"},
            elapsed_ms=220.0,
        )
        
        # Stage 4: Reranking
        tracer.record_reranking(
            method="cross_encoder",
            input_count=18,
            output_count=10,
            score_range=(0.72, 0.95),
            elapsed_ms=150.0,
        )
        
        # Stage 5: Response Generation
        tracer.record_response_generation(
            method="llm",
            model="gpt-4",
            response_type="standard",
            citation_count=3,
            token_count=380,
            elapsed_ms=1100.0,
        )
        
        # Finalize
        trace = tracer.finalize(total_elapsed_ms=1500.0)
        
        # Verify complete trace
        assert trace.query_analysis is not None
        assert trace.metadata_boost is not None
        assert trace.retrieval is not None
        assert trace.reranking is not None
        assert trace.response_generation is not None
        assert trace.boundary_refusal is None  # No refusal
        assert trace.error is None
        assert trace.total_elapsed_ms == 1500.0
    
    def test_complete_comparison_query_flow(self):
        """Test tracing a comparison query with document grouping."""
        tracer = create_query_tracer(
            trace_id="flow-002",
            query="LiDAR vs 毫米波雷达优缺点对比",
            collection="ad_knowledge_v01",
        )
        
        # Stage 1: Query Analysis
        tracer.record_query_analysis(
            complexity="comparison",
            intent="retrieval",
            requires_multi_doc=True,
            detected_keywords=["LiDAR", "毫米波雷达", "vs", "优缺点"],
            query_type="sensor_query",
            elapsed_ms=20.0,
        )
        
        # Stage 2: Retrieval
        tracer.record_retrieval(
            method="hybrid",
            provider="azure_openai",
            top_k=30,
            result_count=28,
            elapsed_ms=280.0,
        )
        
        # Stage 3: Document Grouping
        tracer.record_document_grouping(
            grouping_applied=True,
            source_document_count=2,
            chunks_per_document={
                "lidar_spec.pdf": 3,
                "radar_spec.pdf": 3,
            },
            diversity_enforced=True,
            min_docs_required=2,
            min_docs_met=True,
            elapsed_ms=18.0,
        )
        
        # Stage 4: Reranking
        tracer.record_reranking(
            method="cross_encoder",
            input_count=6,
            output_count=6,
            score_range=(0.68, 0.88),
            elapsed_ms=95.0,
        )
        
        # Stage 5: Response Generation
        tracer.record_response_generation(
            method="llm",
            model="gpt-4",
            response_type="comparison",
            citation_count=6,
            token_count=620,
            elapsed_ms=1400.0,
        )
        
        # Finalize
        trace = tracer.finalize(total_elapsed_ms=1820.0)
        
        # Verify document grouping was recorded
        assert trace.document_grouping is not None
        assert trace.document_grouping.grouping_applied is True
        assert trace.document_grouping.source_document_count == 2
        assert trace.response_generation.response_type == "comparison"
    
    def test_boundary_refusal_flow(self):
        """Test tracing a query that triggers boundary refusal."""
        tracer = create_query_tracer(
            trace_id="flow-003",
            query="预测2030年自动驾驶技术发展趋势",
            collection="ad_knowledge_v01",
        )
        
        # Stage 1: Query Analysis
        tracer.record_query_analysis(
            complexity="simple",
            intent="boundary",
            requires_multi_doc=False,
            detected_keywords=["预测", "2030年", "发展趋势"],
            query_type=None,
            elapsed_ms=12.0,
        )
        
        # Stage 2: Boundary Refusal
        tracer.record_boundary_refusal(
            refusal_occurred=True,
            refusal_type="predictive",
            detected_pattern="预测",
            query_content="预测2030年自动驾驶技术发展趋势",
            confidence=0.95,
            suggested_alternatives=[
                "查询当前自动驾驶技术现状",
                "查询自动驾驶技术原理",
            ],
            elapsed_ms=5.0,
        )
        
        # Finalize (no retrieval or generation)
        trace = tracer.finalize(total_elapsed_ms=20.0)
        
        # Verify refusal was recorded
        assert trace.boundary_refusal is not None
        assert trace.boundary_refusal.refusal_occurred is True
        assert trace.boundary_refusal.refusal_type == "predictive"
        assert trace.retrieval is None  # No retrieval performed
        assert trace.response_generation is None  # No response generated
