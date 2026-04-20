# Monitoring Configuration for AD Knowledge Retrieval System

This directory contains monitoring and alerting configurations for the Autonomous Driving Knowledge Retrieval System.

## Overview

The monitoring stack consists of:
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and notification

## Files

### prometheus.yml
Main Prometheus configuration file that defines:
- Scrape intervals and targets
- Alert rule files
- Service discovery configuration

### alert_rules.yml
Prometheus alert rules that define when alerts should be triggered:
- Response time alerts (warning: >6s, critical: >10s)
- Error rate alerts (warning: >5%, critical: >10%)
- Citation rate alerts (warning: <70%, critical: <60%)
- Boundary refusal rate alerts (warning: >30%, critical: >50%)
- System resource alerts (CPU, memory, disk)
- Service availability alerts

### grafana_dashboard.json
Grafana dashboard configuration with panels for:
- Query throughput and response times
- Error rates and citation rates
- Query type distribution
- Document diversity scores
- System resource usage
- Top queries and refusal reasons

## Setup Instructions

### 1. Install Prometheus

```bash
# Download Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-2.45.0.linux-amd64.tar.gz
cd prometheus-2.45.0.linux-amd64

# Copy configuration
cp /path/to/config/monitoring/prometheus.yml .
cp /path/to/config/monitoring/alert_rules.yml .

# Start Prometheus
./prometheus --config.file=prometheus.yml
```

Prometheus will be available at: http://localhost:9090

### 2. Install Grafana

```bash
# Ubuntu/Debian
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana

# Start Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

Grafana will be available at: http://localhost:3000 (default credentials: admin/admin)

### 3. Configure Grafana

1. Add Prometheus as a data source:
   - Go to Configuration > Data Sources
   - Click "Add data source"
   - Select "Prometheus"
   - Set URL to `http://localhost:9090`
   - Click "Save & Test"

2. Import the dashboard:
   - Go to Dashboards > Import
   - Upload `grafana_dashboard.json`
   - Select the Prometheus data source
   - Click "Import"

### 4. Install Node Exporter (for system metrics)

```bash
# Download Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.0/node_exporter-1.6.0.linux-amd64.tar.gz
tar xvfz node_exporter-1.6.0.linux-amd64.tar.gz
cd node_exporter-1.6.0.linux-amd64

# Start Node Exporter
./node_exporter
```

Node Exporter will expose metrics at: http://localhost:9100/metrics

### 5. Install Alertmanager (optional)

```bash
# Download Alertmanager
wget https://github.com/prometheus/alertmanager/releases/download/v0.25.0/alertmanager-0.25.0.linux-amd64.tar.gz
tar xvfz alertmanager-0.25.0.linux-amd64.tar.gz
cd alertmanager-0.25.0.linux-amd64

# Configure alertmanager.yml (see example below)
# Start Alertmanager
./alertmanager --config.file=alertmanager.yml
```

Alertmanager will be available at: http://localhost:9093

## Instrumenting the Application

To expose metrics from the AD Knowledge System, add Prometheus instrumentation to your Python code:

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Define metrics
query_requests = Counter('query_requests_total', 'Total query requests', ['query_type'])
query_errors = Counter('query_errors_total', 'Total query errors', ['error_type'])
query_response_time = Histogram('query_response_time_seconds', 'Query response time')
queries_with_citations = Counter('queries_with_citations_total', 'Queries with citations')
boundary_refusals = Counter('boundary_refusals_total', 'Boundary refusals', ['refusal_type'])
document_diversity = Gauge('document_diversity_score', 'Document diversity score')
boost_applied = Counter('boost_applied_total', 'Metadata boost applications', ['query_type'])
boost_eligible = Counter('boost_eligible_queries_total', 'Boost eligible queries')

# Start metrics server
start_http_server(8001)

# Instrument your code
@query_response_time.time()
def process_query(query):
    query_requests.inc()
    try:
        # Your query processing logic
        result = your_query_function(query)
        if result.has_citations:
            queries_with_citations.inc()
        return result
    except Exception as e:
        query_errors.labels(error_type=type(e).__name__).inc()
        raise
```

## Key Metrics

### Performance Metrics
- `query_response_time_seconds`: Query response time histogram
- `retrieval_time_seconds`: Retrieval stage time
- `reranking_time_seconds`: Reranking stage time
- `generation_time_seconds`: Generation stage time

### Quality Metrics
- `queries_with_citations_total`: Number of queries with citations
- `document_diversity_score`: Average document diversity in results
- `boost_applied_total`: Number of times metadata boost was applied

### Error Metrics
- `query_errors_total`: Total query errors by type
- `database_connection_errors_total`: Database connection failures
- `boundary_refusals_total`: Boundary refusals by type

### System Metrics (from Node Exporter)
- `node_cpu_seconds_total`: CPU usage
- `node_memory_MemAvailable_bytes`: Available memory
- `node_filesystem_avail_bytes`: Available disk space

## Alert Configuration

### Alertmanager Configuration Example

Create `alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
    - match:
        severity: warning
      receiver: 'warning-alerts'

receivers:
  - name: 'default'
    email_configs:
      - to: 'team@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'alertmanager@example.com'
        auth_password: 'password'
  
  - name: 'critical-alerts'
    email_configs:
      - to: 'oncall@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'alertmanager@example.com'
        auth_password: 'password'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#critical-alerts'
        title: 'Critical Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
  
  - name: 'warning-alerts'
    email_configs:
      - to: 'team@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'alertmanager@example.com'
        auth_password: 'password'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'component']
```

## Monitoring Best Practices

1. **Set appropriate thresholds**: Adjust alert thresholds based on your SLAs and observed baseline performance

2. **Monitor trends**: Look for gradual degradation over time, not just immediate issues

3. **Use dashboards**: Regularly review Grafana dashboards to understand system behavior

4. **Alert fatigue**: Avoid too many alerts - focus on actionable metrics

5. **Document runbooks**: Create runbooks for each alert type explaining:
   - What the alert means
   - How to investigate
   - How to resolve

6. **Regular reviews**: Review and update alert rules quarterly based on system evolution

## Troubleshooting

### Prometheus not scraping metrics
- Check that the target service is running and exposing metrics
- Verify the target URL in `prometheus.yml`
- Check Prometheus logs: `tail -f prometheus.log`
- Visit Prometheus UI > Status > Targets to see scrape status

### Grafana dashboard shows no data
- Verify Prometheus data source is configured correctly
- Check that Prometheus is collecting metrics (visit Prometheus UI)
- Verify metric names match between dashboard and Prometheus

### Alerts not firing
- Check alert rules syntax: `promtool check rules alert_rules.yml`
- Verify Alertmanager is running and configured in Prometheus
- Check Prometheus UI > Alerts to see alert status

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Node Exporter](https://github.com/prometheus/node_exporter)
