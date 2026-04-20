"""Unit tests for autonomous driving term recognition (Task 20).

Tests abbreviation recognition, mixed language queries, synonym equivalence,
and technical term preservation for autonomous driving terminology.

Validates Requirements: 6.1, 6.2, 6.3, 6.4
"""

import pytest
from src.core.query_engine.query_analyzer import QueryAnalyzer


class TestAbbreviationRecognition:
    """Test recognition of autonomous driving abbreviations (Requirement 6.1)."""

    def test_lidar_abbreviation_recognition(self):
        """Test LiDAR abbreviation is correctly recognized."""
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze("LiDAR的探测距离是多少？")
        
        assert "lidar" in analysis.detected_terms
        assert analysis.term_types["lidar"] == "sensor"

    def test_adas_abbreviation_recognition(self):
        """Test ADAS abbreviation is correctly recognized."""
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze("ADAS系统包含哪些功能？")
        
        assert "adas" in analysis.detected_terms
        assert analysis.term_types["adas"] == "system"

    def test_odd_abbreviation_recognition(self):
        """Test ODD abbreviation is correctly recognized."""
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze("ODD的定义是什么？")
        
        assert "odd" in analysis.detected_terms
        assert analysis.term_types["odd"] == "system"

    def test_v2x_abbreviation_recognition(self):
        """Test V2X abbreviation is correctly recognized."""
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze("V2X通信协议有哪些？")
        
        assert "v2x" in analysis.detected_terms
        assert analysis.term_types["v2x"] == "system"

    def test_slam_abbreviation_recognition(self):
        """Test SLAM abbreviation is correctly recognized."""
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze("SLAM算法的原理是什么？")
        
        assert "slam" in analysis.detected_terms
        assert analysis.term_types["slam"] == "algorithm"

    def test_multiple_abbreviations_in_one_query(self):
        """Test multiple abbreviations are recognized in a single query."""
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze("ADAS系统中的LiDAR和V2X如何配合？")
        
        assert "adas" in analysis.detected_terms
        assert "lidar" in analysis.detected_terms
        assert "v2x" in analysis.detected_terms
        assert analysis.term_types["adas"] == "system"
        assert analysis.term_types["lidar"] == "sensor"
        assert analysis.term_types["v2x"] == "system"

    def test_abbreviation_case_insensitive(self):
        """Test abbreviation recognition is case-insensitive."""
        analyzer = QueryAnalyzer()
        
        # Test lowercase
        analysis1 = analyzer.analyze("lidar的性能如何？")
        assert "lidar" in analysis1.detected_terms
        
        # Test uppercase
        analysis2 = analyzer.analyze("LIDAR的性能如何？")
        assert "lidar" in analysis2.detected_terms
        
        # Test mixed case
        analysis3 = analyzer.analyze("LiDaR的性能如何？")
        assert "lidar" in analysis3.detected_terms


class TestMixedLanguageQueries:
    """Test mixed Chinese-English query support (Requirement 6.2)."""

    def test_lidar_mixed_query(self):
        """Test mixed query: LiDAR + Chinese parameters."""
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze("LiDAR的探测距离是多少？")
        
        assert "lidar" in analysis.detected_terms
        assert "探测距离" in analysis.detected_terms
        assert analysis.term_types["lidar"] == "sensor"
        assert analysis.term_types["探测距离"] == "sensor"

    def test_camera_mixed_query(self):
        """Test mixed query: Camera + Chinese parameters."""
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze("Camera的分辨率和帧率是多少？")
        
        assert "camera" in analysis.detected_terms
        assert "分辨率" in analysis.detected_terms
        assert "帧率" in analysis.detected_terms

    def test_radar_mixed_query(self):
        """Test mixed query: Radar + Chinese parameters."""
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze("Radar的视场角是多少？")
        
        assert "radar" in analysis.detected_terms
        assert "视场角" in analysis.detected_terms

    def test_adas_mixed_query(self):
        """Test mixed query: ADAS + Chinese description."""
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze("ADAS系统的功能安全要求是什么？")
        
        assert "adas" in analysis.detected_terms
        assert "功能安全" in analysis.detected_terms
        assert analysis.term_types["adas"] == "system"
        assert analysis.term_types["功能安全"] == "regulation"

    def test_slam_mixed_query(self):
        """Test mixed query: SLAM + Chinese algorithm terms."""
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze("SLAM算法在感知模块中的应用")
        
        assert "slam" in analysis.detected_terms
        assert "感知" in analysis.detected_terms
        assert analysis.term_types["slam"] == "algorithm"
        assert analysis.term_types["感知"] == "algorithm"

    def test_multiple_english_terms_with_chinese(self):
        """Test multiple English terms mixed with Chinese."""
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze("LiDAR和Camera在ADAS系统中的融合方案")
        
        assert "lidar" in analysis.detected_terms
        assert "camera" in analysis.detected_terms
        assert "adas" in analysis.detected_terms
        # Check Chinese term also detected
        assert "融合方案" in analysis.detected_keywords

    def test_english_sentence_with_chinese_terms(self):
        """Test English terms in Chinese sentence structure."""
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze("请介绍LiDAR的calibration方法")
        
        assert "lidar" in analysis.detected_terms
        # Note: "calibration" might not be in term list, but "标定" is
        # This tests that English terms are recognized even in Chinese context

    def test_mixed_comparison_query(self):
        """Test mixed language in comparison queries."""
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze("LiDAR和激光雷达有什么区别？")
        
        assert "lidar" in analysis.detected_terms
        assert "激光雷达" in analysis.detected_terms
        assert analysis.complexity == "comparison"


class TestSynonymQueryEquivalence:
    """Test synonym query equivalence (Requirement 6.3)."""

    def test_lidar_synonym_mapping(self):
        """Test LiDAR and 激光雷达 are recognized as synonyms."""
        analyzer = QueryAnalyzer()
        
        # Test Chinese term
        synonyms_cn = analyzer.get_synonyms("激光雷达")
        assert "lidar" in synonyms_cn
        
        # Test English term
        synonyms_en = analyzer.get_synonyms("lidar")
        assert "激光雷达" in synonyms_en

    def test_camera_synonym_mapping(self):
        """Test Camera, 摄像头, and 相机 are recognized as synonyms."""
        analyzer = QueryAnalyzer()
        
        # Test Chinese term 1
        synonyms_cn1 = analyzer.get_synonyms("摄像头")
        assert "camera" in synonyms_cn1
        assert "相机" in synonyms_cn1
        
        # Test English term
        synonyms_en = analyzer.get_synonyms("camera")
        assert "摄像头" in synonyms_en
        
        # Test Chinese term 2
        synonyms_cn2 = analyzer.get_synonyms("相机")
        assert "摄像头" in synonyms_cn2
        assert "camera" in synonyms_cn2

    def test_radar_synonym_mapping(self):
        """Test Radar and 毫米波雷达 are recognized as synonyms."""
        analyzer = QueryAnalyzer()
        
        # Test Chinese term
        synonyms_cn = analyzer.get_synonyms("毫米波雷达")
        assert "radar" in synonyms_cn
        
        # Test English term
        synonyms_en = analyzer.get_synonyms("radar")
        assert "毫米波雷达" in synonyms_en

    def test_adas_synonym_mapping(self):
        """Test ADAS and 高级驾驶辅助系统 are recognized as synonyms."""
        analyzer = QueryAnalyzer()
        
        # Test abbreviation
        synonyms_abbr = analyzer.get_synonyms("adas")
        assert "高级驾驶辅助系统" in synonyms_abbr
        
        # Test full name
        synonyms_full = analyzer.get_synonyms("高级驾驶辅助系统")
        assert "adas" in synonyms_full

    def test_odd_synonym_mapping(self):
        """Test ODD and 设计运行条件 are recognized as synonyms."""
        analyzer = QueryAnalyzer()
        
        # Test abbreviation
        synonyms_abbr = analyzer.get_synonyms("odd")
        assert "设计运行条件" in synonyms_abbr
        
        # Test full name
        synonyms_full = analyzer.get_synonyms("设计运行条件")
        assert "odd" in synonyms_full

    def test_v2x_synonym_mapping(self):
        """Test V2X and 车联网 are recognized as synonyms."""
        analyzer = QueryAnalyzer()
        
        # Test abbreviation
        synonyms_abbr = analyzer.get_synonyms("v2x")
        assert "车联网" in synonyms_abbr
        
        # Test full name
        synonyms_full = analyzer.get_synonyms("车联网")
        assert "v2x" in synonyms_full

    def test_autonomous_driving_synonym_mapping(self):
        """Test autonomous driving and 自动驾驶 are recognized as synonyms."""
        analyzer = QueryAnalyzer()
        
        # Test English term
        synonyms_en = analyzer.get_synonyms("autonomous driving")
        assert "自动驾驶" in synonyms_en
        
        # Test Chinese term
        synonyms_cn = analyzer.get_synonyms("自动驾驶")
        assert "autonomous driving" in synonyms_cn

    def test_synonym_case_insensitive(self):
        """Test synonym lookup is case-insensitive."""
        analyzer = QueryAnalyzer()
        
        # Test different cases
        synonyms1 = analyzer.get_synonyms("LiDAR")
        synonyms2 = analyzer.get_synonyms("lidar")
        synonyms3 = analyzer.get_synonyms("LIDAR")
        
        assert "激光雷达" in synonyms1
        assert "激光雷达" in synonyms2
        assert "激光雷达" in synonyms3

    def test_no_synonyms_for_unknown_term(self):
        """Test that unknown terms return empty synonym list."""
        analyzer = QueryAnalyzer()
        
        synonyms = analyzer.get_synonyms("unknown_term_xyz")
        assert synonyms == []

    def test_synonym_query_detection_equivalence(self):
        """Test that synonym queries detect equivalent terms."""
        analyzer = QueryAnalyzer()
        
        # Query with Chinese term
        analysis_cn = analyzer.analyze("激光雷达的探测距离是多少？")
        assert "激光雷达" in analysis_cn.detected_terms
        
        # Query with English synonym
        analysis_en = analyzer.analyze("LiDAR的探测距离是多少？")
        assert "lidar" in analysis_en.detected_terms
        
        # Both should detect sensor type
        assert analysis_cn.term_types["激光雷达"] == "sensor"
        assert analysis_en.term_types["lidar"] == "sensor"


class TestTechnicalTermPreservation:
    """Test technical term preservation in query analysis (Requirement 6.4)."""

    def test_sensor_terms_preserved(self):
        """Test sensor technical terms are preserved accurately."""
        analyzer = QueryAnalyzer()
        
        query = "摄像头、激光雷达、毫米波雷达、超声波雷达的技术参数"
        analysis = analyzer.analyze(query)
        
        # All sensor terms should be detected
        assert "摄像头" in analysis.detected_terms
        assert "激光雷达" in analysis.detected_terms
        assert "毫米波雷达" in analysis.detected_terms
        assert "超声波" in analysis.detected_terms
        
        # All should be classified as sensor type
        assert all(
            analysis.term_types.get(term) == "sensor"
            for term in ["摄像头", "激光雷达", "毫米波雷达", "超声波"]
        )

    def test_algorithm_terms_preserved(self):
        """Test algorithm technical terms are preserved accurately."""
        analyzer = QueryAnalyzer()
        
        query = "感知、规划、控制算法的实现"
        analysis = analyzer.analyze(query)
        
        # All algorithm terms should be detected
        assert "感知" in analysis.detected_terms
        assert "规划" in analysis.detected_terms
        assert "控制" in analysis.detected_terms
        
        # All should be classified as algorithm type
        assert all(
            analysis.term_types.get(term) == "algorithm"
            for term in ["感知", "规划", "控制"]
        )

    def test_regulation_terms_preserved(self):
        """Test regulation technical terms are preserved accurately."""
        analyzer = QueryAnalyzer()
        
        query = "GB/T标准和ISO 26262功能安全标准"
        analysis = analyzer.analyze(query)
        
        # All regulation terms should be detected
        assert "gb/t" in analysis.detected_terms
        assert "iso 26262" in analysis.detected_terms
        assert "功能安全" in analysis.detected_terms
        
        # All should be classified as regulation type
        assert all(
            analysis.term_types.get(term) == "regulation"
            for term in ["gb/t", "iso 26262", "功能安全"]
        )

    def test_system_terms_preserved(self):
        """Test system technical terms are preserved accurately."""
        analyzer = QueryAnalyzer()
        
        query = "ADAS、ODD、V2X系统的定义"
        analysis = analyzer.analyze(query)
        
        # All system terms should be detected
        assert "adas" in analysis.detected_terms
        assert "odd" in analysis.detected_terms
        assert "v2x" in analysis.detected_terms
        
        # All should be classified as system type
        assert all(
            analysis.term_types.get(term) == "system"
            for term in ["adas", "odd", "v2x"]
        )

    def test_parameter_terms_preserved(self):
        """Test technical parameter terms are preserved accurately."""
        analyzer = QueryAnalyzer()
        
        query = "分辨率、帧率、视场角、探测距离的技术指标"
        analysis = analyzer.analyze(query)
        
        # All parameter terms should be detected
        assert "分辨率" in analysis.detected_terms
        assert "帧率" in analysis.detected_terms
        assert "视场角" in analysis.detected_terms
        assert "探测距离" in analysis.detected_terms
        
        # All should be classified as sensor type (parameters)
        assert all(
            analysis.term_types.get(term) == "sensor"
            for term in ["分辨率", "帧率", "视场角", "探测距离"]
        )

    def test_calibration_terms_preserved(self):
        """Test calibration technical terms are preserved accurately."""
        analyzer = QueryAnalyzer()
        
        query = "摄像头的标定方法"
        analysis = analyzer.analyze(query)
        
        # Calibration term should be detected
        assert "标定" in analysis.detected_terms
        assert analysis.term_types["标定"] == "sensor"

    def test_complex_technical_query_preservation(self):
        """Test complex query with multiple technical terms preserves all terms."""
        analyzer = QueryAnalyzer()
        
        query = "LiDAR和Camera在ADAS系统中的感知融合算法需要符合ISO 26262标准"
        analysis = analyzer.analyze(query)
        
        # Check all term types are detected
        sensor_terms = [t for t, type_ in analysis.term_types.items() if type_ == "sensor"]
        algorithm_terms = [t for t, type_ in analysis.term_types.items() if type_ == "algorithm"]
        system_terms = [t for t, type_ in analysis.term_types.items() if type_ == "system"]
        regulation_terms = [t for t, type_ in analysis.term_types.items() if type_ == "regulation"]
        
        assert len(sensor_terms) >= 2  # lidar, camera
        assert len(algorithm_terms) >= 1  # 感知
        assert len(system_terms) >= 1  # adas
        assert len(regulation_terms) >= 1  # iso 26262

    def test_term_type_accuracy(self):
        """Test that term types are accurately classified."""
        analyzer = QueryAnalyzer()
        
        # Test each term type individually
        test_cases = [
            ("摄像头的分辨率", "摄像头", "sensor"),
            ("目标检测算法", "目标检测", "algorithm"),
            ("ADAS系统", "adas", "system"),
            ("GB/T标准", "gb/t", "regulation"),
        ]
        
        for query, expected_term, expected_type in test_cases:
            analysis = analyzer.analyze(query)
            assert expected_term in analysis.detected_terms, f"Term '{expected_term}' not detected in '{query}'"
            assert analysis.term_types[expected_term] == expected_type, \
                f"Term '{expected_term}' has wrong type: {analysis.term_types.get(expected_term)} != {expected_type}"

    def test_no_term_corruption(self):
        """Test that terms are not corrupted or modified during detection."""
        analyzer = QueryAnalyzer()
        
        # Use exact terms from the term sets
        query = "激光雷达 LiDAR 摄像头 Camera 毫米波雷达 Radar"
        analysis = analyzer.analyze(query)
        
        # Check that detected terms match expected terms (case-insensitive)
        detected_lower = [t.lower() for t in analysis.detected_terms]
        
        assert "激光雷达" in detected_lower
        assert "lidar" in detected_lower
        assert "摄像头" in detected_lower
        assert "camera" in detected_lower
        assert "毫米波雷达" in detected_lower
        assert "radar" in detected_lower


class TestTermRecognitionEdgeCases:
    """Test edge cases for term recognition."""

    def test_empty_query_no_terms(self):
        """Test empty query returns no detected terms."""
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze("")
        
        assert len(analysis.detected_terms) == 0
        assert len(analysis.term_types) == 0

    def test_non_ad_query_no_terms(self):
        """Test non-AD query returns no detected terms."""
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze("今天天气怎么样？")
        
        assert len(analysis.detected_terms) == 0
        assert len(analysis.term_types) == 0

    def test_partial_term_match_not_detected(self):
        """Test that partial term matches are not incorrectly detected."""
        analyzer = QueryAnalyzer()
        
        # "雷达" alone should not match "激光雷达" or "毫米波雷达"
        # But "雷达" might match "radar" synonym
        analysis = analyzer.analyze("雷达波的传播")
        
        # Should not detect "激光雷达" or "毫米波雷达" specifically
        assert "激光雷达" not in analysis.detected_terms
        assert "毫米波雷达" not in analysis.detected_terms

    def test_term_in_longer_phrase(self):
        """Test term detection within longer phrases."""
        analyzer = QueryAnalyzer()
        
        query = "高性能激光雷达传感器的技术参数"
        analysis = analyzer.analyze(query)
        
        # Should detect "激光雷达" even though it's part of longer phrase
        assert "激光雷达" in analysis.detected_terms

    def test_multiple_occurrences_of_same_term(self):
        """Test that same term appearing multiple times is detected once."""
        analyzer = QueryAnalyzer()
        
        query = "LiDAR的优点和LiDAR的缺点"
        analysis = analyzer.analyze(query)
        
        # Should detect "lidar" (case-insensitive)
        assert "lidar" in analysis.detected_terms
        # Should only appear once in detected_terms
        assert analysis.detected_terms.count("lidar") == 1

    def test_whitespace_handling(self):
        """Test term detection with various whitespace."""
        analyzer = QueryAnalyzer()
        
        query = "  LiDAR  的  探测距离  "
        analysis = analyzer.analyze(query)
        
        assert "lidar" in analysis.detected_terms
        assert "探测距离" in analysis.detected_terms

    def test_punctuation_handling(self):
        """Test term detection with punctuation."""
        analyzer = QueryAnalyzer()
        
        query = "LiDAR、Camera、Radar的对比"
        analysis = analyzer.analyze(query)
        
        assert "lidar" in analysis.detected_terms
        assert "camera" in analysis.detected_terms
        assert "radar" in analysis.detected_terms

    def test_term_detection_with_numbers(self):
        """Test term detection in queries with numbers."""
        analyzer = QueryAnalyzer()
        
        query = "ISO 26262标准的ASIL等级"
        analysis = analyzer.analyze(query)
        
        assert "iso 26262" in analysis.detected_terms
        assert "asil" in analysis.detected_terms
        assert analysis.term_types["iso 26262"] == "regulation"
        assert analysis.term_types["asil"] == "regulation"
