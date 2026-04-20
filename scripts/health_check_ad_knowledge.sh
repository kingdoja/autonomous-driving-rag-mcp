#!/bin/bash
# Health check script for Autonomous Driving Knowledge Retrieval System
# This script performs comprehensive health checks on the AD knowledge system

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COLLECTION_NAME="ad_knowledge_v01"
CONFIG_FILE="config/settings.ad_knowledge.yaml"
HEALTH_LOG="./logs/health_check_$(date +%Y%m%d_%H%M%S).log"

# Health check results
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$HEALTH_LOG"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $1" | tee -a "$HEALTH_LOG"
    ((PASSED_CHECKS++))
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $1" | tee -a "$HEALTH_LOG"
    ((FAILED_CHECKS++))
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $1" | tee -a "$HEALTH_LOG"
    ((WARNING_CHECKS++))
}

check() {
    ((TOTAL_CHECKS++))
}

# Check Python environment
check_python_environment() {
    log "Checking Python environment..."
    check
    
    if [ -z "$VIRTUAL_ENV" ]; then
        warning "Virtual environment not activated"
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
            success "Virtual environment activated"
        else
            error "Virtual environment not found"
            return 1
        fi
    else
        success "Virtual environment is active: $VIRTUAL_ENV"
    fi
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    local deps=("chromadb" "langchain" "openai" "pytest" "streamlit")
    
    for dep in "${deps[@]}"; do
        check
        python -c "import $dep" 2>/dev/null
        if [ $? -eq 0 ]; then
            local version=$(python -c "import $dep; print($dep.__version__)" 2>/dev/null || echo "unknown")
            success "$dep installed (version: $version)"
        else
            error "$dep not installed"
        fi
    done
}

# Check configuration files
check_configuration() {
    log "Checking configuration files..."
    
    # Check main config
    check
    if [ -f "$CONFIG_FILE" ]; then
        success "Configuration file exists: $CONFIG_FILE"
        
        # Validate YAML syntax
        check
        python -c "import yaml; yaml.safe_load(open('$CONFIG_FILE'))" 2>/dev/null
        if [ $? -eq 0 ]; then
            success "Configuration file has valid YAML syntax"
        else
            error "Configuration file has invalid YAML syntax"
        fi
    else
        error "Configuration file not found: $CONFIG_FILE"
    fi
    
    # Check .env file
    check
    if [ -f ".env" ]; then
        success ".env file exists"
        
        # Check API keys
        source .env
        check
        if [ -n "$OPENAI_API_KEY" ]; then
            success "OPENAI_API_KEY is set"
        else
            error "OPENAI_API_KEY not set in .env"
        fi
    else
        error ".env file not found"
    fi
}

# Check database files
check_databases() {
    log "Checking database files..."
    
    # Check Chroma database
    check
    if [ -d "./data/db/chroma" ]; then
        local chroma_size=$(du -sh ./data/db/chroma | cut -f1)
        success "Chroma database exists (size: $chroma_size)"
    else
        error "Chroma database directory not found"
    fi
    
    # Check BM25 index
    check
    if [ -d "./data/db/bm25/$COLLECTION_NAME" ]; then
        local bm25_size=$(du -sh "./data/db/bm25/$COLLECTION_NAME" | cut -f1)
        success "BM25 index exists for $COLLECTION_NAME (size: $bm25_size)"
    else
        error "BM25 index not found for $COLLECTION_NAME"
    fi
    
    # Check ingestion history
    check
    if [ -f "./data/db/ingestion_history.db" ]; then
        local history_size=$(du -sh ./data/db/ingestion_history.db | cut -f1)
        success "Ingestion history database exists (size: $history_size)"
    else
        warning "Ingestion history database not found"
    fi
}

# Check collection status
check_collection() {
    log "Checking collection status..."
    
    check
    python scripts/check_collection_status.py --collection "$COLLECTION_NAME" 2>&1 | tee -a "$HEALTH_LOG"
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        success "Collection $COLLECTION_NAME is accessible"
    else
        error "Collection $COLLECTION_NAME is not accessible"
    fi
}

# Check query functionality
check_query_functionality() {
    log "Checking query functionality..."
    
    # Test sensor query
    check
    log "Testing sensor query..."
    timeout 10s python scripts/query.py \
        --config "$CONFIG_FILE" \
        --query "激光雷达" \
        --collection "$COLLECTION_NAME" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        success "Sensor query test passed"
    else
        error "Sensor query test failed"
    fi
    
    # Test algorithm query
    check
    log "Testing algorithm query..."
    timeout 10s python scripts/query.py \
        --config "$CONFIG_FILE" \
        --query "感知算法" \
        --collection "$COLLECTION_NAME" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        success "Algorithm query test passed"
    else
        error "Algorithm query test failed"
    fi
}

# Check response time
check_response_time() {
    log "Checking response time..."
    
    check
    local start_time=$(date +%s)
    python scripts/query.py \
        --config "$CONFIG_FILE" \
        --query "测试查询" \
        --collection "$COLLECTION_NAME" > /dev/null 2>&1
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [ $duration -le 4 ]; then
        success "Response time: ${duration}s (target: ≤4s)"
    elif [ $duration -le 6 ]; then
        warning "Response time: ${duration}s (target: ≤4s, acceptable: ≤6s)"
    else
        error "Response time: ${duration}s (exceeds acceptable limit of 6s)"
    fi
}

# Check disk space
check_disk_space() {
    log "Checking disk space..."
    
    check
    local available_space=$(df -h . | awk 'NR==2 {print $4}')
    local usage_percent=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ $usage_percent -lt 80 ]; then
        success "Disk space available: $available_space (usage: ${usage_percent}%)"
    elif [ $usage_percent -lt 90 ]; then
        warning "Disk space available: $available_space (usage: ${usage_percent}%)"
    else
        error "Disk space critical: $available_space (usage: ${usage_percent}%)"
    fi
}

# Check log files
check_logs() {
    log "Checking log files..."
    
    check
    if [ -d "./logs" ]; then
        local log_count=$(ls -1 ./logs/*.jsonl 2>/dev/null | wc -l)
        local log_size=$(du -sh ./logs 2>/dev/null | cut -f1)
        success "Log directory exists (files: $log_count, size: $log_size)"
    else
        warning "Log directory not found"
    fi
}

# Check system resources
check_system_resources() {
    log "Checking system resources..."
    
    # Check memory
    check
    if command -v free &> /dev/null; then
        local mem_usage=$(free | awk 'NR==2 {printf "%.0f", $3/$2 * 100}')
        if [ $mem_usage -lt 80 ]; then
            success "Memory usage: ${mem_usage}%"
        elif [ $mem_usage -lt 90 ]; then
            warning "Memory usage: ${mem_usage}%"
        else
            error "Memory usage critical: ${mem_usage}%"
        fi
    else
        warning "Cannot check memory usage (free command not available)"
    fi
    
    # Check CPU
    check
    if command -v top &> /dev/null; then
        local cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
        if [ $(echo "$cpu_usage < 80" | bc) -eq 1 ]; then
            success "CPU usage: ${cpu_usage}%"
        elif [ $(echo "$cpu_usage < 90" | bc) -eq 1 ]; then
            warning "CPU usage: ${cpu_usage}%"
        else
            error "CPU usage critical: ${cpu_usage}%"
        fi
    else
        warning "Cannot check CPU usage (top command not available)"
    fi
}

# Generate health report
generate_report() {
    log ""
    log "=========================================="
    log "Health Check Summary"
    log "=========================================="
    log "Total checks: $TOTAL_CHECKS"
    success "Passed: $PASSED_CHECKS"
    warning "Warnings: $WARNING_CHECKS"
    error "Failed: $FAILED_CHECKS"
    log ""
    
    local health_percentage=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        if [ $WARNING_CHECKS -eq 0 ]; then
            success "System health: EXCELLENT (${health_percentage}%)"
        else
            warning "System health: GOOD (${health_percentage}%) - Some warnings detected"
        fi
    elif [ $FAILED_CHECKS -le 2 ]; then
        warning "System health: FAIR (${health_percentage}%) - Minor issues detected"
    else
        error "System health: POOR (${health_percentage}%) - Critical issues detected"
    fi
    
    log ""
    log "Health check log: $HEALTH_LOG"
    log "=========================================="
    
    # Return exit code based on health
    if [ $FAILED_CHECKS -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# Main health check flow
main() {
    log "=========================================="
    log "AD Knowledge System Health Check"
    log "=========================================="
    log "Collection: $COLLECTION_NAME"
    log "Config: $CONFIG_FILE"
    log "Time: $(date +'%Y-%m-%d %H:%M:%S')"
    log ""
    
    # Run all health checks
    check_python_environment
    check_dependencies
    check_configuration
    check_databases
    check_collection
    check_query_functionality
    check_response_time
    check_disk_space
    check_logs
    check_system_resources
    
    # Generate report
    generate_report
}

# Run main function
main
