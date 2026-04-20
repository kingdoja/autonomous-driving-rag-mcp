# AD Scenarios Integration Tests

## Overview

This test suite validates end-to-end scenarios for the Autonomous Driving Knowledge Retrieval System against the `ad_knowledge_v01` collection.

## Test Coverage

### Core Scenarios (6 scenarios)

1. **S1: Sensor Parameter Query** (传感器参数查询)
   - Tests sensor document prioritization
   - Validates metadata boost application
   - Requirements: 2.1, 2.2, 2.4

2. **S2: Algorithm Principle Query** (算法原理查询)
   - Tests algorithm document retrieval
   - Validates algorithm type detection
   - Requirements: 3.1, 3.2, 3.3

3. **S3: Regulation Standard Query** (法规标准查询)
   - Tests regulation document retrieval
   - Validates document authority ranking
   - Requirements: 4.1, 4.2, 4.3, 4.4

4. **S4: Sensor Comparison Query** (传感器方案对比)
   - Tests multi-document retrieval
   - Validates comparison structure
   - Requirements: 5.1, 5.4

5. **S5: Multi-Sensor Fusion Query** (多传感器融合)
   - Tests aggregation from 3-5 documents
   - Validates citation completeness
   - Requirements: 5.3

6. **S6: Predictive Query Refusal** (预测查询拒绝)
   - Tests boundary validation
   - Validates refusal messages
   - Requirements: 8.1, 8.2, 8.4

### Test Structure

```
tests/integration/test_ad_scenarios.py
├── TestADScenarios (12 tests)
│   ├── test_s1_sensor_parameter_query
│   ├── test_s1_lidar_detection_range_query (variant)
│   ├── test_s2_algorithm_principle_query
│   ├── test_s2_planning_algorithm_query (variant)
│   ├── test_s3_regulation_standard_query
│   ├── test_s3_national_standard_query (variant)
│   ├── test_s4_sensor_comparison_query
│   ├── test_s4_algorithm_comparison_query (variant)
│   ├── test_s5_multi_sensor_fusion_query
│   ├── test_s6_predictive_query_refusal
│   ├── test_s6_diagnostic_query_refusal (variant)
│   └── test_all_scenarios_return_results (sanity check)
└── TestADScenariosRegression (1 test)
    └── test_ad_scenarios_regression_summary
```

## Prerequisites

1. **Collection**: `ad_knowledge_v01` must be indexed with AD documents
2. **Configuration**: `config/settings.ad_knowledge.yaml` must be configured
3. **Environment**: `.env` file with API keys must be present

## Running Tests

### Run all AD scenario tests
```bash
pytest tests/integration/test_ad_scenarios.py -v
```

### Run specific scenario
```bash
pytest tests/integration/test_ad_scenarios.py -v -k "test_s1"
```

### Run only retrieval tests (skip boundary tests)
```bash
pytest tests/integration/test_ad_scenarios.py -v -k "not refusal"
```

### Run regression summary
```bash
pytest tests/integration/test_ad_scenarios.py::TestADScenariosRegression -v
```

## Expected Results

### Thresholds

- **Sensor Doc Ratio**: >= 67% (2/3 of top-3 for sensor queries)
- **Citation Rate**: >= 80%
- **Refusal Accuracy**: 100% (all boundary scenarios must refuse)
- **Multi-Doc Count**: >= 2 documents for comparison queries

### Success Criteria

✅ All retrieval scenarios return results  
✅ Sensor queries prioritize sensor documents  
✅ Algorithm queries return algorithm documents  
✅ Regulation queries return regulation documents  
✅ Comparison queries retrieve from multiple documents  
✅ Fusion queries aggregate from 3-5 documents  
✅ Predictive queries are refused correctly  
✅ Responses include citations  

## Test Helpers

The test suite includes helper functions for validation:

- `_check_sensor_doc_prioritization()`: Validates sensor doc ratio in top-k
- `_check_citation_present()`: Checks for citation markers
- `_check_refusal_response()`: Validates boundary refusal messages
- `_check_multi_document_retrieval()`: Validates multi-doc retrieval
- `_check_comparison_structure()`: Validates comparison response structure
- `_check_aggregation_structure()`: Validates aggregation response structure

## Troubleshooting

### No results returned
- Verify collection is indexed: Check `data/db/chroma/ad_knowledge_v01/`
- Verify configuration: Check `config/settings.ad_knowledge.yaml`
- Run ingestion: `python scripts/ingest_documents.py --collection ad_knowledge_v01`

### Sensor doc prioritization fails
- Check metadata boost configuration in settings
- Verify documents have `doc_type: sensor_doc` metadata
- Check query analyzer is detecting sensor queries

### Citation rate low
- Verify ResponseBuilder is using CitationEnhancer
- Check that documents have proper metadata (source, page, section)
- Review response generation prompts

### Refusal tests fail
- Verify BoundaryValidator is enabled in settings
- Check predictive/diagnostic patterns in configuration
- Review refusal message templates

## Integration with CI/CD

Add to `.github/workflows/tests.yml`:

```yaml
- name: Run AD Scenario Tests
  run: |
    pytest tests/integration/test_ad_scenarios.py -v --tb=short
```

## Related Files

- Test implementation: `tests/integration/test_ad_scenarios.py`
- Configuration: `config/settings.ad_knowledge.yaml`
- Requirements: `.kiro/specs/autonomous-driving-knowledge-retrieval/requirements.md`
- Design: `.kiro/specs/autonomous-driving-knowledge-retrieval/design.md`
- Tasks: `.kiro/specs/autonomous-driving-knowledge-retrieval/tasks.md`

## Notes

- Tests are marked with `@pytest.mark.integration`
- Some tests require ResponseBuilder (marked with `@pytest.mark.skipif`)
- Variant tests provide additional coverage for different query types
- Sanity check test is informational only (does not fail)
