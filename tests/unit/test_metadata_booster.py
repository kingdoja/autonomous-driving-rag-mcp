"""Unit tests for MetadataBooster.

Tests query type detection, boost weight application, top-K verification,
fallback mechanism, and custom boost configuration.
"""

import pytest
from src.core.query_engine.metadata_booster import MetadataBooster, MetadataBoostResult
from src.core.types import RetrievalResult


def make_chunk(chunk_id: str, score: float, doc_type: str, text: str = "sample text") -> RetrievalResult:
    """Helper to create RetrievalResult objects for testing."""
    return RetrievalResult(
        chunk_id=chunk_id,
        score=score,
        text=text,
        metadata={"doc_type": doc_type},
    )


class TestQueryTypeDetection:
    """Tests for detect_query_type()."""

    def test_sensor_query_camera(self):
        """摄像头的分辨率是多少 should be detected as sensor_query."""
        booster = MetadataBooster()
        assert booster.detect_query_type("摄像头的分辨率是多少") == "sensor_query"

    def test_sensor_query_lidar(self):
        """激光雷达探测距离 should be detected as sensor_query."""
        booster = MetadataBooster()
        assert booster.detect_query_type("激光雷达探测距离") == "sensor_query"

    def test_sensor_query_radar(self):
        """毫米波雷达视场角 should be detected as sensor_query."""
        booster = MetadataBooster()
        assert booster.detect_query_type("毫米波雷达视场角") == "sensor_query"

    def test_sensor_query_calibration(self):
        """内参标定方法 should be detected as sensor_query."""
        booster = MetadataBooster()
        assert booster.detect_query_type("内参标定方法") == "sensor_query"

    def test_algorithm_query_perception(self):
        """目标检测算法原理 should be detected as algorithm_query."""
        booster = MetadataBooster()
        assert booster.detect_query_type("目标检测算法原理") == "algorithm_query"

    def test_algorithm_query_planning(self):
        """路径规划算法 should be detected as algorithm_query."""
        booster = MetadataBooster()
        assert booster.detect_query_type("路径规划算法") == "algorithm_query"

    def test_algorithm_query_control(self):
        """PID控制参数调优 should be detected as algorithm_query."""
        booster = MetadataBooster()
        assert booster.detect_query_type("PID控制参数调优") == "algorithm_query"

    def test_regulation_query_gbt(self):
        """GB/T自动驾驶标准 should be detected as regulation_query."""
        booster = MetadataBooster()
        assert booster.detect_query_type("GB/T自动驾驶标准") == "regulation_query"

    def test_regulation_query_iso(self):
        """ISO 26262功能安全 should be detected as regulation_query."""
        booster = MetadataBooster()
        assert booster.detect_query_type("ISO 26262功能安全") == "regulation_query"

    def test_test_query_scenario(self):
        """跟车场景测试用例 should be detected as test_query."""
        booster = MetadataBooster()
        assert booster.detect_query_type("跟车场景测试用例") == "test_query"

    def test_general_query(self):
        """你好 should fall back to general."""
        booster = MetadataBooster()
        assert booster.detect_query_type("你好") == "general"

    def test_empty_query(self):
        """Empty string should return general."""
        booster = MetadataBooster()
        assert booster.detect_query_type("") == "general"

    def test_mixed_language_sensor(self):
        """LiDAR的探测距离 (mixed Chinese/English) should be sensor_query."""
        booster = MetadataBooster()
        assert booster.detect_query_type("LiDAR的探测距离") == "sensor_query"


class TestBoostWeightApplication:
    """Tests for apply_boost()."""

    def test_sensor_boost_increases_sensor_doc_score(self):
        """sensor_doc score should be multiplied by 1.5 for a sensor query."""
        booster = MetadataBooster()
        chunks = [make_chunk("c1", 0.8, "sensor_doc")]
        result = booster.apply_boost(chunks, "摄像头的分辨率是多少")
        assert pytest.approx(result[0].score) == 0.8 * 1.5

    def test_sensor_boost_decreases_algorithm_doc_score(self):
        """algorithm_doc score should be multiplied by 0.8 for a sensor query."""
        booster = MetadataBooster()
        chunks = [make_chunk("c1", 0.8, "algorithm_doc")]
        result = booster.apply_boost(chunks, "摄像头的分辨率是多少")
        assert pytest.approx(result[0].score) == 0.8 * 0.8

    def test_algorithm_boost_increases_algorithm_doc_score(self):
        """algorithm_doc score should be multiplied by 1.3 for an algorithm query."""
        booster = MetadataBooster()
        chunks = [make_chunk("c1", 0.6, "algorithm_doc")]
        result = booster.apply_boost(chunks, "路径规划算法")
        assert pytest.approx(result[0].score) == 0.6 * 1.3

    def test_regulation_boost_increases_regulation_doc_score(self):
        """regulation_doc score should be multiplied by 1.6 for a regulation query."""
        booster = MetadataBooster()
        chunks = [make_chunk("c1", 0.5, "regulation_doc")]
        result = booster.apply_boost(chunks, "ISO 26262功能安全")
        assert pytest.approx(result[0].score) == 0.5 * 1.6

    def test_general_query_no_boost(self):
        """General query should return chunks with unchanged scores."""
        booster = MetadataBooster()
        chunks = [
            make_chunk("c1", 0.9, "sensor_doc"),
            make_chunk("c2", 0.7, "algorithm_doc"),
        ]
        result = booster.apply_boost(chunks, "你好")
        assert result[0].score == 0.9
        assert result[1].score == 0.7

    def test_boost_reorders_results(self):
        """After sensor boost, sensor_doc should rank higher than algorithm_doc."""
        booster = MetadataBooster()
        # algorithm_doc starts with a higher raw score
        chunks = [
            make_chunk("algo", 0.9, "algorithm_doc"),
            make_chunk("sensor", 0.8, "sensor_doc"),
        ]
        result = booster.apply_boost(chunks, "摄像头的分辨率是多少")
        # sensor_doc: 0.8 * 1.5 = 1.2 > algorithm_doc: 0.9 * 0.8 = 0.72
        assert result[0].chunk_id == "sensor"

    def test_empty_chunks_returns_empty(self):
        """Empty input list should return an empty list."""
        booster = MetadataBooster()
        result = booster.apply_boost([], "摄像头的分辨率是多少")
        assert result == []

    def test_boost_preserves_chunk_content(self):
        """text and chunk_id must be preserved after boost."""
        booster = MetadataBooster()
        chunks = [make_chunk("my_id", 0.5, "sensor_doc", text="important content")]
        result = booster.apply_boost(chunks, "摄像头的分辨率是多少")
        assert result[0].chunk_id == "my_id"
        assert result[0].text == "important content"


class TestTopKVerification:
    """Tests for top-K verification behavior via apply_boost_with_details()."""

    def test_top_k_verified_when_enough_target_docs(self):
        """2+ sensor_docs in top-3 should yield top_k_verified=True."""
        booster = MetadataBooster()
        chunks = [
            make_chunk("s1", 0.9, "sensor_doc"),
            make_chunk("s2", 0.8, "sensor_doc"),
            make_chunk("a1", 0.7, "algorithm_doc"),
            make_chunk("a2", 0.6, "algorithm_doc"),
        ]
        result = booster.apply_boost_with_details(chunks, "摄像头的分辨率是多少")
        assert result.top_k_verified is True

    def test_top_k_not_verified_when_insufficient_target_docs(self):
        """Only 1 sensor_doc in top-3 should yield top_k_verified=False."""
        booster = MetadataBooster()
        # After boost: sensor_doc 0.4*1.5=0.6, algorithm_docs 0.9*0.8=0.72, 0.8*0.8=0.64
        # Top-3 will be: algo(0.72), algo(0.64), sensor(0.6) → only 1 sensor_doc
        chunks = [
            make_chunk("a1", 0.9, "algorithm_doc"),
            make_chunk("a2", 0.8, "algorithm_doc"),
            make_chunk("s1", 0.4, "sensor_doc"),
            make_chunk("a3", 0.3, "algorithm_doc"),
        ]
        result = booster.apply_boost_with_details(chunks, "摄像头的分辨率是多少")
        assert result.top_k_verified is False

    def test_top_k_verified_with_fewer_than_threshold_chunks(self):
        """Fewer than top_k_threshold chunks should yield top_k_verified=True."""
        booster = MetadataBooster(top_k_threshold=3)
        chunks = [
            make_chunk("s1", 0.9, "sensor_doc"),
            make_chunk("a1", 0.8, "algorithm_doc"),
        ]
        result = booster.apply_boost_with_details(chunks, "摄像头的分辨率是多少")
        assert result.top_k_verified is True

    def test_custom_top_k_threshold(self):
        """Custom top_k_threshold and top_k_min_count should be respected."""
        booster = MetadataBooster(top_k_threshold=5, top_k_min_count=3)
        # Provide 5 chunks with only 2 sensor_docs → should fail min_count=3
        chunks = [
            make_chunk("s1", 0.9, "sensor_doc"),
            make_chunk("s2", 0.85, "sensor_doc"),
            make_chunk("a1", 0.8, "algorithm_doc"),
            make_chunk("a2", 0.75, "algorithm_doc"),
            make_chunk("a3", 0.7, "algorithm_doc"),
        ]
        result = booster.apply_boost_with_details(chunks, "摄像头的分辨率是多少")
        # After boost top-5: s1=1.35, s2=1.275, a1=0.64, a2=0.6, a3=0.56
        # 2 sensor_docs in top-5 < min_count=3 → not verified
        assert result.top_k_verified is False


class TestFallbackMechanism:
    """Tests for fallback behavior via apply_boost_with_details()."""

    def test_fallback_used_when_top_k_fails(self):
        """When top-K verification fails, fallback_used=True and boosted_chunks == original_chunks."""
        booster = MetadataBooster()
        chunks = [
            make_chunk("a1", 0.9, "algorithm_doc"),
            make_chunk("a2", 0.8, "algorithm_doc"),
            make_chunk("s1", 0.4, "sensor_doc"),
            make_chunk("a3", 0.3, "algorithm_doc"),
        ]
        result = booster.apply_boost_with_details(chunks, "摄像头的分辨率是多少")
        assert result.fallback_used is True
        assert result.boosted_chunks == chunks

    def test_no_fallback_when_top_k_passes(self):
        """When top-K verification passes, fallback_used=False."""
        booster = MetadataBooster()
        chunks = [
            make_chunk("s1", 0.9, "sensor_doc"),
            make_chunk("s2", 0.8, "sensor_doc"),
            make_chunk("a1", 0.7, "algorithm_doc"),
        ]
        result = booster.apply_boost_with_details(chunks, "摄像头的分辨率是多少")
        assert result.fallback_used is False

    def test_general_query_no_boost_applied(self):
        """General query should yield boost_applied=False."""
        booster = MetadataBooster()
        chunks = [make_chunk("c1", 0.8, "sensor_doc")]
        result = booster.apply_boost_with_details(chunks, "你好")
        assert result.boost_applied is False

    def test_boost_applied_true_for_sensor_query(self):
        """Sensor query with enough sensor_docs should yield boost_applied=True."""
        booster = MetadataBooster()
        chunks = [
            make_chunk("s1", 0.9, "sensor_doc"),
            make_chunk("s2", 0.8, "sensor_doc"),
            make_chunk("a1", 0.7, "algorithm_doc"),
        ]
        result = booster.apply_boost_with_details(chunks, "摄像头的分辨率是多少")
        assert result.boost_applied is True


class TestCustomBoostConfig:
    """Tests for custom boost configuration."""

    def test_custom_boost_config_applied(self):
        """Custom config should override the default boost weights."""
        custom_config = {
            "sensor_query": {"sensor_doc": 2.0, "algorithm_doc": 0.5},
        }
        booster = MetadataBooster(boost_config=custom_config)
        chunks = [make_chunk("c1", 0.5, "sensor_doc")]
        result = booster.apply_boost(chunks, "摄像头的分辨率是多少")
        assert pytest.approx(result[0].score) == 0.5 * 2.0

    def test_boost_config_missing_doc_type_uses_1_0(self):
        """A doc_type not present in the boost config should have its score unchanged (×1.0)."""
        custom_config = {
            "sensor_query": {"sensor_doc": 1.5},  # algorithm_doc intentionally absent
        }
        booster = MetadataBooster(boost_config=custom_config)
        chunks = [make_chunk("c1", 0.7, "algorithm_doc")]
        result = booster.apply_boost(chunks, "摄像头的分辨率是多少")
        assert pytest.approx(result[0].score) == 0.7 * 1.0
