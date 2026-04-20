"""Performance tests for Autonomous Driving Knowledge Retrieval System.

This module tests the performance characteristics of the AD knowledge retrieval
system, including:
- Simple query response time (<= 2 seconds)
- Complex query response time (<= 4 seconds)
- Multi-document query response time (<= 4 seconds)
- Metadata boost impact on performance
- Concurrent query processing capability

Requirements validated:
- 12.1: Response time performance
- 12.2: Multi-document retrieval optimization
- 12.3: Performance under load
"""

import concurrent.futures
import time
from typing import List, Tuple

import pytest

from src.core.query_engine.hybrid_search import HybridSearch, create_hybrid_search
from src.core.query_engine.metadata_booster import MetadataBooster
from src.core.query_engine.query_analyzer import QueryAnalyzer
from src.core.settings import Settings


class TestADPerformance:
    """Performance tests for AD knowledge retrieval system."""
    
    @pytest.fixture
    def hybrid_search(self) -> HybridSearch:
        """Create HybridSearch instance for testing.
        
        Returns:
            Configured HybridSearch instance.
        """
        return create_hybrid_search()
    
    @pytest.fixture
    def metadata_booster(self) -> MetadataBooster:
        """Create MetadataBooster instance for testing.
        
        Returns:
            Configured MetadataBooster instance.
        """
        return MetadataBooster()
    
    @pytest.fixture
    def query_analyzer(self) -> QueryAnalyzer:
        """Create QueryAnalyzer instance for testing.
        
        Returns:
            Configured QueryAnalyzer instance.
        """
        return QueryAnalyzer()
    
    # Simple Query Performance Tests
    
    def test_simple_sensor_query_response_time(self, hybrid_search: HybridSearch):
        """Test simple sensor query response time <= 2 seconds.
        
        Validates: Requirement 12.1 - Response time performance
        """
        query = "摄像头的分辨率是多少？"
        
        start_time = time.time()
        result = hybrid_search.search(query, top_k=10)
        elapsed_time = time.time() - start_time
        
        # Verify response time
        assert elapsed_time <= 2.0, (
            f"Simple query took {elapsed_time:.2f}s, expected <= 2.0s"
        )
        
        # Verify results returned
        assert len(result.results) > 0, "Should return results"
    
    def test_simple_algorithm_query_response_time(self, hybrid_search: HybridSearch):
        """Test simple algorithm query response time <= 2 seconds.
        
        Validates: Requirement 12.1 - Response time performance
        """
        query = "目标检测算法的原理是什么？"
        
        start_time = time.time()
        result = hybrid_search.search(query, top_k=10)
        elapsed_time = time.time() - start_time
        
        # Verify response time
        assert elapsed_time <= 2.0, (
            f"Simple query took {elapsed_time:.2f}s, expected <= 2.0s"
        )
        
        # Verify results returned
        assert len(result.results) > 0, "Should return results"
    
    def test_simple_regulation_query_response_time(self, hybrid_search: HybridSearch):
        """Test simple regulation query response time <= 2 seconds.
        
        Validates: Requirement 12.1 - Response time performance
        """
        query = "ISO 26262 功能安全标准的要求是什么？"
        
        start_time = time.time()
        result = hybrid_search.search(query, top_k=10)
        elapsed_time = time.time() - start_time
        
        # Verify response time
        assert elapsed_time <= 2.0, (
            f"Simple query took {elapsed_time:.2f}s, expected <= 2.0s"
        )
        
        # Verify results returned
        assert len(result.results) > 0, "Should return results"
    
    # Complex Query Performance Tests
    
    def test_complex_multi_part_query_response_time(self, hybrid_search: HybridSearch):
        """Test complex multi-part query response time <= 4 seconds.
        
        Validates: Requirement 12.1 - Response time performance
        """
        query = "激光雷达的探测距离是多少？它的标定方法有哪些？在什么场景下使用？"
        
        start_time = time.time()
        result = hybrid_search.search(query, top_k=10)
        elapsed_time = time.time() - start_time
        
        # Verify response time
        assert elapsed_time <= 4.0, (
            f"Complex query took {elapsed_time:.2f}s, expected <= 4.0s"
        )
        
        # Verify results returned
        assert len(result.results) > 0, "Should return results"
    
    def test_complex_comparison_query_response_time(self, hybrid_search: HybridSearch):
        """Test complex comparison query response time <= 4 seconds.
        
        Validates: Requirement 12.1 - Response time performance
        """
        query = "激光雷达和毫米波雷达的优缺点对比，分别适用于什么场景？"
        
        start_time = time.time()
        result = hybrid_search.search(query, top_k=10)
        elapsed_time = time.time() - start_time
        
        # Verify response time
        assert elapsed_time <= 4.0, (
            f"Complex comparison query took {elapsed_time:.2f}s, expected <= 4.0s"
        )
        
        # Verify results returned
        assert len(result.results) > 0, "Should return results"
    
    def test_complex_aggregation_query_response_time(self, hybrid_search: HybridSearch):
        """Test complex aggregation query response time <= 4 seconds.
        
        Validates: Requirement 12.1 - Response time performance
        """
        query = "自动驾驶系统中感知、规划、控制三个模块的算法分别有哪些？"
        
        start_time = time.time()
        result = hybrid_search.search(query, top_k=10)
        elapsed_time = time.time() - start_time
        
        # Verify response time
        assert elapsed_time <= 4.0, (
            f"Complex aggregation query took {elapsed_time:.2f}s, expected <= 4.0s"
        )
        
        # Verify results returned
        assert len(result.results) > 0, "Should return results"
    
    # Multi-Document Query Performance Tests
    
    def test_multi_doc_sensor_comparison_response_time(self, hybrid_search: HybridSearch):
        """Test multi-document sensor comparison query response time <= 4 seconds.
        
        Validates: Requirement 12.2 - Multi-document retrieval optimization
        """
        query = "对比摄像头、激光雷达、毫米波雷达的技术参数和应用场景"
        
        start_time = time.time()
        result = hybrid_search.search(query, top_k=15)
        elapsed_time = time.time() - start_time
        
        # Verify response time
        assert elapsed_time <= 4.0, (
            f"Multi-doc query took {elapsed_time:.2f}s, expected <= 4.0s"
        )
        
        # Verify results returned
        assert len(result.results) > 0, "Should return results"
        
        # Verify multi-document diversity
        doc_sources = set()
        for r in result.results:
            source = r.metadata.get("source_path", "")
            if source:
                doc_sources.add(source)
        
        assert len(doc_sources) >= 2, (
            f"Multi-doc query should return results from >= 2 documents, got {len(doc_sources)}"
        )
    
    def test_multi_doc_algorithm_comparison_response_time(self, hybrid_search: HybridSearch):
        """Test multi-document algorithm comparison query response time <= 4 seconds.
        
        Validates: Requirement 12.2 - Multi-document retrieval optimization
        """
        query = "对比基于规则的规划算法和基于学习的规划算法"
        
        start_time = time.time()
        result = hybrid_search.search(query, top_k=15)
        elapsed_time = time.time() - start_time
        
        # Verify response time
        assert elapsed_time <= 4.0, (
            f"Multi-doc algorithm query took {elapsed_time:.2f}s, expected <= 4.0s"
        )
        
        # Verify results returned
        assert len(result.results) > 0, "Should return results"
    
    def test_multi_doc_fusion_query_response_time(self, hybrid_search: HybridSearch):
        """Test multi-document sensor fusion query response time <= 4 seconds.
        
        Validates: Requirement 12.2 - Multi-document retrieval optimization
        """
        query = "多传感器融合方案中摄像头、激光雷达、毫米波雷达分别的作用"
        
        start_time = time.time()
        result = hybrid_search.search(query, top_k=15)
        elapsed_time = time.time() - start_time
        
        # Verify response time
        assert elapsed_time <= 4.0, (
            f"Multi-doc fusion query took {elapsed_time:.2f}s, expected <= 4.0s"
        )
        
        # Verify results returned
        assert len(result.results) > 0, "Should return results"
    
    # Metadata Boost Performance Tests
    
    def test_metadata_boost_performance_impact(
        self, 
        hybrid_search: HybridSearch,
        metadata_booster: MetadataBooster,
        query_analyzer: QueryAnalyzer
    ):
        """Test that metadata boost application has minimal performance impact.
        
        Validates: Requirement 12.2 - Multi-document retrieval optimization
        """
        query = "激光雷达的探测距离和分辨率"
        
        # Measure without boost
        start_time = time.time()
        result_no_boost = hybrid_search.search(query, top_k=10)
        time_no_boost = time.time() - start_time
        
        # Measure with boost (simulate boost application)
        start_time = time.time()
        result_with_boost = hybrid_search.search(query, top_k=10)
        analysis = query_analyzer.analyze(query)
        boosted = metadata_booster.apply_boost(
            result_with_boost.results,
            analysis,
            boost_config={"sensor_doc": 1.5}
        )
        time_with_boost = time.time() - start_time
        
        # Verify boost overhead is minimal (< 0.5 seconds)
        boost_overhead = time_with_boost - time_no_boost
        assert boost_overhead <= 0.5, (
            f"Boost overhead {boost_overhead:.2f}s exceeds 0.5s threshold"
        )
        
        # Verify both return results
        assert len(result_no_boost.results) > 0, "Should return results without boost"
        assert len(boosted) > 0, "Should return results with boost"
    
    def test_boost_application_speed(self, metadata_booster: MetadataBooster):
        """Test that boost application itself is fast (< 0.1 seconds).
        
        Validates: Requirement 12.2 - Multi-document retrieval optimization
        """
        from src.core.types import RetrievalResult
        
        # Create sample results
        results = [
            RetrievalResult(
                chunk_id=f"chunk_{i}",
                score=0.8 - (i * 0.05),
                text=f"Sample text {i}",
                metadata={
                    "source_path": f"sensor_doc_{i % 3}.pdf",
                    "doc_type": "sensor_doc" if i % 2 == 0 else "algorithm_doc"
                }
            )
            for i in range(20)
        ]
        
        # Create mock analysis
        from dataclasses import dataclass
        
        @dataclass
        class MockAnalysis:
            complexity: str = "simple"
            intent: str = "retrieval"
            detected_keywords: List[str] = None
            
            def __post_init__(self):
                if self.detected_keywords is None:
                    self.detected_keywords = ["激光雷达", "探测距离"]
        
        analysis = MockAnalysis()
        
        # Measure boost application time
        start_time = time.time()
        boosted = metadata_booster.apply_boost(
            results,
            analysis,
            boost_config={"sensor_doc": 1.5, "algorithm_doc": 1.2}
        )
        elapsed_time = time.time() - start_time
        
        # Verify boost is fast
        assert elapsed_time <= 0.1, (
            f"Boost application took {elapsed_time:.2f}s, expected <= 0.1s"
        )
        
        # Verify results returned
        assert len(boosted) > 0, "Should return boosted results"
    
    # Concurrent Query Performance Tests
    
    def test_concurrent_simple_queries(self, hybrid_search: HybridSearch):
        """Test concurrent processing of simple queries.
        
        Validates: Requirement 12.3 - Performance under load
        """
        queries = [
            "摄像头的分辨率",
            "激光雷达的探测距离",
            "毫米波雷达的视场角",
            "超声波雷达的应用场景",
            "目标检测算法原理",
        ]
        
        def execute_query(query: str) -> Tuple[str, float, int]:
            """Execute a single query and measure time.
            
            Args:
                query: Query string
                
            Returns:
                Tuple of (query, elapsed_time, result_count)
            """
            start_time = time.time()
            result = hybrid_search.search(query, top_k=10)
            elapsed_time = time.time() - start_time
            return query, elapsed_time, len(result.results)
        
        # Execute queries concurrently
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(execute_query, q) for q in queries]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        total_time = time.time() - start_time
        
        # Verify all queries completed
        assert len(results) == len(queries), "All queries should complete"
        
        # Verify individual query times
        for query, elapsed, count in results:
            assert elapsed <= 3.0, (
                f"Query '{query}' took {elapsed:.2f}s under load, expected <= 3.0s"
            )
            assert count > 0, f"Query '{query}' should return results"
        
        # Verify total time shows parallelism benefit
        # If sequential, would take sum of all times
        # With parallelism, should be closer to max individual time
        sequential_estimate = sum(elapsed for _, elapsed, _ in results)
        assert total_time < sequential_estimate * 0.8, (
            f"Concurrent execution took {total_time:.2f}s, "
            f"expected < {sequential_estimate * 0.8:.2f}s (80% of sequential)"
        )
    
    def test_concurrent_complex_queries(self, hybrid_search: HybridSearch):
        """Test concurrent processing of complex queries.
        
        Validates: Requirement 12.3 - Performance under load
        """
        queries = [
            "激光雷达和毫米波雷达的优缺点对比",
            "感知算法、规划算法、控制算法的原理",
            "多传感器融合方案中各传感器的作用",
        ]
        
        def execute_query(query: str) -> Tuple[str, float, int]:
            """Execute a single query and measure time."""
            start_time = time.time()
            result = hybrid_search.search(query, top_k=15)
            elapsed_time = time.time() - start_time
            return query, elapsed_time, len(result.results)
        
        # Execute queries concurrently
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(execute_query, q) for q in queries]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        total_time = time.time() - start_time
        
        # Verify all queries completed
        assert len(results) == len(queries), "All queries should complete"
        
        # Verify individual query times
        for query, elapsed, count in results:
            assert elapsed <= 5.0, (
                f"Complex query '{query}' took {elapsed:.2f}s under load, expected <= 5.0s"
            )
            assert count > 0, f"Query '{query}' should return results"
    
    def test_sustained_load_performance(self, hybrid_search: HybridSearch):
        """Test performance under sustained load (10 queries).
        
        Validates: Requirement 12.3 - Performance under load
        """
        queries = [
            "摄像头分辨率",
            "激光雷达探测距离",
            "毫米波雷达视场角",
            "目标检测算法",
            "路径规划算法",
            "ISO 26262 标准",
            "功能测试场景",
            "传感器标定方法",
            "多传感器融合",
            "自动驾驶分级",
        ]
        
        execution_times = []
        
        # Execute queries sequentially to measure sustained performance
        for query in queries:
            start_time = time.time()
            result = hybrid_search.search(query, top_k=10)
            elapsed_time = time.time() - start_time
            execution_times.append(elapsed_time)
            
            # Verify results returned
            assert len(result.results) > 0, f"Query '{query}' should return results"
        
        # Calculate statistics
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        
        # Verify average performance
        assert avg_time <= 3.0, (
            f"Average query time {avg_time:.2f}s under sustained load, expected <= 3.0s"
        )
        
        # Verify no query took excessively long
        assert max_time <= 5.0, (
            f"Max query time {max_time:.2f}s under sustained load, expected <= 5.0s"
        )
        
        # Verify performance consistency (no severe degradation)
        # Last 3 queries should not be significantly slower than first 3
        first_three_avg = sum(execution_times[:3]) / 3
        last_three_avg = sum(execution_times[-3:]) / 3
        degradation_ratio = last_three_avg / first_three_avg if first_three_avg > 0 else 1.0
        
        assert degradation_ratio <= 1.5, (
            f"Performance degraded by {degradation_ratio:.2f}x, expected <= 1.5x"
        )
    
    # Performance Regression Tests
    
    def test_performance_baseline_simple_query(self, hybrid_search: HybridSearch):
        """Establish performance baseline for simple queries.
        
        This test serves as a baseline for detecting performance regressions.
        
        Validates: Requirement 12.1 - Response time performance
        """
        query = "激光雷达的探测距离"
        
        # Run query multiple times to get stable measurement
        times = []
        for _ in range(5):
            start_time = time.time()
            result = hybrid_search.search(query, top_k=10)
            elapsed_time = time.time() - start_time
            times.append(elapsed_time)
            
            # Verify results
            assert len(result.results) > 0, "Should return results"
        
        # Calculate statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        # Log baseline metrics
        print(f"\nPerformance Baseline - Simple Query:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Min: {min_time:.3f}s")
        print(f"  Max: {max_time:.3f}s")
        
        # Verify baseline meets requirements
        assert avg_time <= 2.0, f"Baseline average {avg_time:.2f}s exceeds 2.0s"
        assert max_time <= 3.0, f"Baseline max {max_time:.2f}s exceeds 3.0s"
    
    def test_performance_baseline_complex_query(self, hybrid_search: HybridSearch):
        """Establish performance baseline for complex queries.
        
        This test serves as a baseline for detecting performance regressions.
        
        Validates: Requirement 12.1 - Response time performance
        """
        query = "激光雷达和毫米波雷达的优缺点对比，分别适用于什么场景？"
        
        # Run query multiple times to get stable measurement
        times = []
        for _ in range(5):
            start_time = time.time()
            result = hybrid_search.search(query, top_k=15)
            elapsed_time = time.time() - start_time
            times.append(elapsed_time)
            
            # Verify results
            assert len(result.results) > 0, "Should return results"
        
        # Calculate statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        # Log baseline metrics
        print(f"\nPerformance Baseline - Complex Query:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Min: {min_time:.3f}s")
        print(f"  Max: {max_time:.3f}s")
        
        # Verify baseline meets requirements
        assert avg_time <= 4.0, f"Baseline average {avg_time:.2f}s exceeds 4.0s"
        assert max_time <= 5.0, f"Baseline max {max_time:.2f}s exceeds 5.0s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
