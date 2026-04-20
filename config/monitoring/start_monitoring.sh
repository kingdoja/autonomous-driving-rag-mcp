#!/bin/bash
# Quick start script for AD Knowledge Monitoring Stack
# This script starts the monitoring services using Docker Compose

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AD Knowledge Monitoring Stack${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Error: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${YELLOW}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

# Navigate to monitoring directory
cd "$(dirname "$0")"

echo "Starting monitoring services..."
echo ""

# Start services
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    docker compose up -d
fi

echo ""
echo -e "${GREEN}Monitoring services started successfully!${NC}"
echo ""
echo "Access the services at:"
echo "  - Prometheus:    http://localhost:9090"
echo "  - Grafana:       http://localhost:3000 (admin/admin)"
echo "  - Alertmanager:  http://localhost:9093"
echo "  - Node Exporter: http://localhost:9100/metrics"
echo "  - cAdvisor:      http://localhost:8080"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Log in to Grafana (http://localhost:3000)"
echo "2. The AD Knowledge dashboard should be automatically loaded"
echo "3. Configure Alertmanager email settings in alertmanager.yml"
echo "4. Instrument your application to expose metrics (see README.md)"
