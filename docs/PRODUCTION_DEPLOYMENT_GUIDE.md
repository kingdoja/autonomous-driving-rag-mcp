# Production Deployment Guide - AD Knowledge Retrieval System

## Overview

This guide provides comprehensive instructions for deploying the Autonomous Driving Knowledge Retrieval System to production environment.

**Last Updated:** 2026-04-20  
**Version:** 1.0  
**Collection:** ad_knowledge_v01

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Deployment Process](#deployment-process)
3. [Production Smoke Tests](#production-smoke-tests)
4. [24-Hour Monitoring Plan](#24-hour-monitoring-plan)
5. [Alerting System Verification](#alerting-system-verification)
6. [Rollback Procedures](#rollback-procedures)
7. [Post-Deployment Verification](#post-deployment-verification)

## Pre-Deployment Checklist

Before deploying to production, ensure all the following items are completed:

### Code Quality
- [ ] All unit tests passing (100%)
- [ ] All integration tests passing (100%)
- [ ] Property-based tests passing (if applicable)
- [ ] Code review completed and approved
- [ ] No critical or high-severity security vulnerabilities

### Performance
- [ ] Evaluation pass rate >= 80%
- [ ] Response time <= 4 seconds (p95)
- [ ] Citation rate >= 80%
- [ ] Performance tests passing under expected load

### Documentation
- [ ] Architecture documentation complete
- [ ] API reference documentation complete
- [ ] User guide complete
- [ ] Operations manual complete
- [ ] Runbooks for common issues prepared

### Infrastructure
- [ ] Production environment configured
- [ ] Database backups configured
- [ ] Monitoring and alerting configured
- [ ] Log aggregation configured
- [ ] Disaster recovery plan documented

### Data
- [ ] Knowledge base ingested and verified
- [ ] Collection contains >= 120 chunks
- [ ] Document metadata properly tagged
- [ ] Ingestion report reviewed and approved

## Deployment Process

### Step 1: Backup Current State

```bash
# Create backup directory
BACKUP_DIR="./backups/production_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup Chroma database
cp -r ./data/db/chroma "$BACKUP_DIR/"

# Backup BM25 index
cp -r ./data/db/bm25/ad_knowledge_v01 "$BACKUP_DIR/"

# Backup ingestion history
cp ./data/db/ingestion_history.db "$BACKUP_DIR/"

# Backup configuration
cp config/settings.ad_knowledge.yaml "$BACKUP_DIR/"

echo "Backup completed: $BACKUP_DIR"
```

### Step 2: Run Pre-Deployment Tests

```bash
# Run unit tests
python -m pytest tests/unit/ -v

# Run integration tests
python -m pytest tests/integration/test_ad_scenarios.py -v

# Run evaluation
python scripts/run_ad_evaluation.py \
    --config config/settings.ad_knowledge.yaml \
    --collection ad_knowledge_v01
```

### Step 3: Deploy Configuration

```bash
# Validate configuration
python -c "import yaml; yaml.safe_load(open('config/settings.ad_knowledge.yaml'))"

# Deploy configuration (already in place)
echo "Configuration validated and ready"
```

### Step 4: Run Production Smoke Tests

```bash
# Run smoke tests
python scripts/production_smoke_tests_simple.py \
    --config config/settings.ad_knowledge.yaml \
    --collection ad_knowledge_v01
```

**Expected Results:**
- Collection Accessibility: PASS
- Sensor Query: PASS
- Algorithm Query: PASS
- Comparison Query: PASS
- Response Time: PASS (< 6s acceptable, < 4s excellent)
- Error Handling: PASS

**Pass Criteria:**
- All tests must pass OR
- Pass rate >= 80% with acceptable warnings

### Step 5: Start Monitoring

```bash
# Start 24-hour monitoring in background
nohup bash scripts/monitor_production.sh ./logs/production_monitoring.log > /dev/null 2>&1 &

# Save monitoring PID
echo $! > ./logs/monitor.pid

echo "Monitoring started. Check logs: tail -f ./logs/production_monitoring.log"
```

### Step 6: Verify Alerting System

```bash
# Check Prometheus
curl -s http://localhost:9090/-/healthy

# Check Grafana
curl -s http://localhost:3000/api/health

# Verify alert rules
cat config/monitoring/alert_rules.yml
```

### Step 7: Run Health Check

```bash
# Run comprehensive health check
bash scripts/health_check_ad_knowledge.sh
```

## Production Smoke Tests

### Test Suite

The production smoke test suite includes:

1. **Collection Accessibility Test**
   - Verifies collection exists and is accessible
   - Checks collection contains expected number of chunks
   - Expected duration: < 5s

2. **Sensor Query Test**
   - Tests sensor-specific query: "激光雷达的探测距离是多少？"
   - Verifies sensor documents are prioritized
   - Expected duration: < 10s

3. **Algorithm Query Test**
   - Tests algorithm query: "PointPillars 算法的原理是什么？"
   - Verifies algorithm documents are returned
   - Expected duration: < 10s

4. **Comparison Query Test**
   - Tests multi-document comparison: "激光雷达和毫米波雷达的优缺点对比"
   - Verifies multiple documents are retrieved
   - Expected duration: < 15s

5. **Response Time Test**
   - Tests general query response time
   - Target: <= 4s (excellent), <= 6s (acceptable)
   - Expected duration: < 10s

6. **Error Handling Test**
   - Tests system behavior with invalid queries
   - Verifies graceful error handling
   - Expected duration: < 15s

### Running Smoke Tests

```bash
# Run smoke tests
python scripts/production_smoke_tests_simple.py \
    --config config/settings.ad_knowledge.yaml \
    --collection ad_knowledge_v01

# Check results
cat logs/production_smoke_test_*.json
```

### Interpreting Results

- **READY**: All tests passed, proceed with deployment
- **REVIEW**: Most tests passed (>= 80%), review failures before proceeding
- **NOT_READY**: Multiple tests failed (< 80%), do not proceed

## 24-Hour Monitoring Plan

### Monitoring Objectives

Monitor the system for 24 hours after deployment to:
1. Verify system stability under production load
2. Detect performance degradation
3. Identify error patterns
4. Validate alerting system
5. Collect baseline metrics

### Monitoring Schedule

**Automated Monitoring:**
- Check interval: Every 5 minutes
- Duration: 24 hours
- Metrics collected: System resources, query performance, error rates

**Manual Reviews:**
- Hour 1: Intensive monitoring (every 15 minutes)
- Hours 2-8: Regular monitoring (every hour)
- Hours 9-24: Periodic monitoring (every 2 hours)

### Key Metrics to Monitor

#### Performance Metrics
- **Response Time**
  - Target: p50 <= 2s, p95 <= 4s, p99 <= 6s
  - Alert: p95 > 6s (warning), p95 > 10s (critical)

- **Throughput**
  - Target: >= 10 queries/minute
  - Alert: < 5 queries/minute (warning)

#### Quality Metrics
- **Error Rate**
  - Target: < 1%
  - Alert: > 5% (warning), > 10% (critical)

- **Citation Rate**
  - Target: >= 80%
  - Alert: < 70% (warning), < 60% (critical)

#### System Metrics
- **CPU Usage**
  - Target: < 70%
  - Alert: > 80% (warning), > 90% (critical)

- **Memory Usage**
  - Target: < 70%
  - Alert: > 80% (warning), > 90% (critical)

- **Disk Usage**
  - Target: < 70%
  - Alert: > 80% (warning), > 90% (critical)

### Monitoring Commands

```bash
# Check monitoring status
tail -f ./logs/production_monitoring.log

# View Grafana dashboard
open http://localhost:3000

# Check Prometheus metrics
open http://localhost:9090

# Run manual health check
bash scripts/health_check_ad_knowledge.sh

# Test query manually
python scripts/query.py \
    --config config/settings.ad_knowledge.yaml \
    --query "测试查询" \
    --collection ad_knowledge_v01
```

### Hourly Monitoring Checklist

Every hour during the first 8 hours:

- [ ] Check monitoring log for errors
- [ ] Verify response times are within limits
- [ ] Check error rate is < 5%
- [ ] Review system resource usage
- [ ] Check for any alerts
- [ ] Test a sample query manually

### 24-Hour Report

After 24 hours, the monitoring script will generate a final report including:

- Total queries processed
- Success/failure rates
- Average/max/min response times
- Error patterns
- System resource trends
- Overall assessment

## Alerting System Verification

### Alert Rules

The following alert rules are configured:

#### Performance Alerts
- **Slow Response Time (Warning)**
  - Condition: p95 response time > 6s
  - Action: Log warning, notify team

- **Slow Response Time (Critical)**
  - Condition: p95 response time > 10s
  - Action: Page on-call engineer

#### Error Alerts
- **High Error Rate (Warning)**
  - Condition: Error rate > 5%
  - Action: Log warning, notify team

- **High Error Rate (Critical)**
  - Condition: Error rate > 10%
  - Action: Page on-call engineer

#### Quality Alerts
- **Low Citation Rate (Warning)**
  - Condition: Citation rate < 70%
  - Action: Log warning, notify team

- **Low Citation Rate (Critical)**
  - Condition: Citation rate < 60%
  - Action: Notify team lead

#### System Alerts
- **High CPU Usage (Warning)**
  - Condition: CPU usage > 80%
  - Action: Log warning

- **High CPU Usage (Critical)**
  - Condition: CPU usage > 90%
  - Action: Page on-call engineer

- **High Memory Usage (Warning)**
  - Condition: Memory usage > 80%
  - Action: Log warning

- **High Memory Usage (Critical)**
  - Condition: Memory usage > 90%
  - Action: Page on-call engineer

### Verifying Alerts

```bash
# Check Prometheus alert rules
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | select(.type=="alerting")'

# Check active alerts
curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts'

# Test alert (simulate high error rate)
# This should trigger a warning alert
for i in {1..100}; do
    python scripts/query.py --config config/settings.ad_knowledge.yaml --query "" --collection ad_knowledge_v01 || true
done

# Check if alert was triggered
curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.alertname=="HighErrorRate")'
```

### Alert Notification Channels

Configure the following notification channels in Alertmanager:

1. **Email**: team@example.com (all alerts)
2. **Slack**: #ad-knowledge-alerts (critical alerts)
3. **PagerDuty**: On-call engineer (critical alerts)

## Rollback Procedures

### When to Rollback

Rollback immediately if:
- Error rate > 10% for more than 5 minutes
- Response time p95 > 10s for more than 5 minutes
- System crashes or becomes unresponsive
- Data corruption detected
- Critical security vulnerability discovered

### Rollback Steps

```bash
# 1. Stop monitoring
kill $(cat ./logs/monitor.pid)

# 2. Run rollback script
bash scripts/rollback_ad_knowledge.sh <BACKUP_DIR>

# Example:
bash scripts/rollback_ad_knowledge.sh ./backups/production_20260420_120000

# 3. Verify rollback
bash scripts/health_check_ad_knowledge.sh

# 4. Test queries
python scripts/query.py \
    --config config/settings.ad_knowledge.yaml \
    --query "测试查询" \
    --collection ad_knowledge_v01

# 5. Notify team
echo "Rollback completed. System restored to backup state."
```

### Post-Rollback Actions

1. Investigate root cause of failure
2. Document lessons learned
3. Fix issues in development environment
4. Re-test thoroughly
5. Plan new deployment

## Post-Deployment Verification

### Immediate Verification (First Hour)

- [ ] All smoke tests passing
- [ ] Response time within limits
- [ ] No critical errors in logs
- [ ] Monitoring system operational
- [ ] Alerting system functional
- [ ] Sample queries returning correct results

### Short-Term Verification (First 8 Hours)

- [ ] Error rate < 5%
- [ ] Response time stable
- [ ] No memory leaks detected
- [ ] No performance degradation
- [ ] Citation rate >= 80%
- [ ] User feedback positive

### Long-Term Verification (24 Hours)

- [ ] System stable for 24 hours
- [ ] All metrics within acceptable ranges
- [ ] No unexpected alerts
- [ ] Performance consistent
- [ ] Resource usage stable
- [ ] Ready for full production traffic

### Verification Commands

```bash
# Run full evaluation
python scripts/run_ad_evaluation.py \
    --config config/settings.ad_knowledge.yaml \
    --collection ad_knowledge_v01

# Check system health
bash scripts/health_check_ad_knowledge.sh

# Review monitoring report
cat ./logs/production_monitoring.log | grep "Hourly Monitoring Report"

# Check for errors
grep -i "error\|exception\|failed" ./logs/*.log | tail -50
```

## Success Criteria

The production deployment is considered successful if:

1. **All smoke tests pass** (or >= 80% with acceptable warnings)
2. **24-hour monitoring shows:**
   - Error rate < 5%
   - Response time p95 < 6s
   - Citation rate >= 80%
   - No critical alerts
   - System resources < 80%

3. **User acceptance:**
   - Positive feedback from initial users
   - No critical issues reported
   - System meets performance expectations

## Troubleshooting

### Common Issues

#### High Response Time
- **Symptoms**: Queries taking > 6s
- **Possible Causes**: High load, inefficient queries, resource constraints
- **Solutions**:
  - Check system resources (CPU, memory)
  - Review slow query logs
  - Consider scaling resources
  - Optimize query processing

#### High Error Rate
- **Symptoms**: Error rate > 5%
- **Possible Causes**: Invalid queries, system errors, configuration issues
- **Solutions**:
  - Review error logs
  - Check configuration
  - Verify collection accessibility
  - Test queries manually

#### Low Citation Rate
- **Symptoms**: Citation rate < 70%
- **Possible Causes**: Poor retrieval quality, missing metadata
- **Solutions**:
  - Review retrieval results
  - Check metadata completeness
  - Adjust boost weights
  - Re-ingest documents if needed

### Getting Help

- **Documentation**: Check docs/specs/ad-knowledge-retrieval/
- **Logs**: Review ./logs/*.log files
- **Health Check**: Run bash scripts/health_check_ad_knowledge.sh
- **Team Contact**: team@example.com
- **On-Call**: PagerDuty escalation

## Appendix

### Deployment Checklist Summary

```
Pre-Deployment:
☐ All tests passing
☐ Documentation complete
☐ Monitoring configured
☐ Backup created

Deployment:
☐ Configuration deployed
☐ Smoke tests passed
☐ Monitoring started
☐ Alerting verified

Post-Deployment:
☐ Health check passed
☐ Sample queries working
☐ 24-hour monitoring active
☐ Team notified

Verification:
☐ Hour 1: Intensive monitoring
☐ Hour 8: Short-term verification
☐ Hour 24: Long-term verification
☐ Final report generated
```

### Key Files and Locations

- **Configuration**: `config/settings.ad_knowledge.yaml`
- **Deployment Script**: `scripts/deploy_production.sh`
- **Smoke Tests**: `scripts/production_smoke_tests_simple.py`
- **Monitoring Script**: `scripts/monitor_production.sh`
- **Health Check**: `scripts/health_check_ad_knowledge.sh`
- **Rollback Script**: `scripts/rollback_ad_knowledge.sh`
- **Logs**: `./logs/`
- **Backups**: `./backups/`

### Contact Information

- **Development Team**: dev-team@example.com
- **Operations Team**: ops-team@example.com
- **On-Call Engineer**: PagerDuty
- **Emergency Contact**: emergency@example.com

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-20  
**Next Review**: 2026-05-20
