# Performance Tests

This directory contains performance tests for the knowledge retrieval system.

## Test Files

- `test_ad_performance.py`: Performance tests for Autonomous Driving Knowledge Retrieval System

## Running Tests

### Run All Performance Tests
```bash
pytest tests/performance/ -v -s
```

### Run Specific Test File
```bash
pytest tests/performance/test_ad_performance.py -v -s
```

### Run Specific Test Category
```bash
# Simple query tests
pytest tests/performance/test_ad_performance.py -k "simple" -v

# Complex query tests
pytest tests/performance/test_ad_performance.py -k "complex" -v

# Multi-document tests
pytest tests/performance/test_ad_performance.py -k "multi_doc" -v

# Concurrent tests
pytest tests/performance/test_ad_performance.py -k "concurrent" -v

# Baseline tests
pytest tests/performance/test_ad_performance.py -k "baseline" -v
```

### Run with Performance Metrics
```bash
# Show test durations
pytest tests/performance/ -v -s --durations=0

# Show slowest 10 tests
pytest tests/performance/ -v --durations=10
```

## Performance Requirements

### Response Time Targets
- **Simple queries**: <= 2 seconds
- **Complex queries**: <= 4 seconds
- **Multi-document queries**: <= 4 seconds

### Optimization Targets
- **Metadata boost overhead**: < 0.5 seconds
- **Boost application**: < 0.1 seconds
- **Concurrent execution**: < 80% of sequential time
- **Performance degradation**: < 1.5x under sustained load

## Test Categories

### 1. Simple Query Performance
Tests basic single-concept queries:
- Sensor parameter queries
- Algorithm principle queries
- Regulation standard queries

### 2. Complex Query Performance
Tests multi-part and comparison queries:
- Multi-part queries (multiple questions)
- Comparison queries (A vs B)
- Aggregation queries (summarize multiple topics)

### 3. Multi-Document Performance
Tests queries requiring multiple source documents:
- Sensor comparison (2+ sensor docs)
- Algorithm comparison (2+ algorithm docs)
- Sensor fusion (3-5 sensor docs)

### 4. Metadata Boost Performance
Tests performance impact of metadata boosting:
- Boost application overhead
- Boost computation speed

### 5. Concurrent Performance
Tests system behavior under concurrent load:
- Parallel simple queries (5 concurrent)
- Parallel complex queries (3 concurrent)
- Sustained load (10 sequential queries)

### 6. Performance Baselines
Establishes baseline metrics for regression detection:
- Simple query baseline (5 runs)
- Complex query baseline (5 runs)

## Prerequisites

Before running performance tests:

1. **Knowledge Base**: Ensure AD knowledge base is ingested
   ```bash
   python scripts/ingest_documents.py --collection ad_knowledge_v01 --source demo-data-ad/
   ```

2. **Configuration**: Verify settings in `config/settings.ad_knowledge.yaml`

3. **Dependencies**: Install required packages
   ```bash
   pip install -r requirements.txt
   ```

## Interpreting Results

### Success Criteria
- All tests pass (response times within thresholds)
- No performance degradation under load
- Concurrent execution shows parallelism benefit

### Failure Investigation
If tests fail:
1. Check system resources (CPU, memory)
2. Verify knowledge base size and indexing
3. Review query complexity
4. Check for network/disk I/O bottlenecks
5. Profile slow components

### Performance Optimization
If performance is below target:
1. Enable caching (embedding cache, result cache)
2. Optimize batch sizes
3. Tune reranker parameters
4. Consider index optimization
5. Review concurrent execution settings

## Continuous Monitoring

### Baseline Tracking
Run baseline tests regularly to detect regressions:
```bash
pytest tests/performance/test_ad_performance.py -k "baseline" -v -s > performance_baseline.log
```

### Performance Trends
Track metrics over time:
- Average response time
- P95/P99 response time
- Throughput (queries/second)
- Resource utilization

### Alerting Thresholds
Set up alerts for:
- Response time > 5 seconds
- Performance degradation > 2x
- Error rate > 5%
- Resource utilization > 80%

## Related Documentation

- [Design Document](../../.kiro/specs/autonomous-driving-knowledge-retrieval/design.md)
- [Requirements Document](../../.kiro/specs/autonomous-driving-knowledge-retrieval/requirements.md)
- [Task 23 Completion Summary](../../.kiro/specs/autonomous-driving-knowledge-retrieval/TASK_23_COMPLETION_SUMMARY.md)
