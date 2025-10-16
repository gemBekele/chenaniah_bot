#!/bin/bash
# Comprehensive Bot Testing Script
# This script runs all tests in sequence and generates a complete report

set -e  # Exit on any error

echo "🤖 Chenaniah Bot Testing Suite"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if bot token is provided
if [ -z "$1" ]; then
    print_error "Please provide your bot token as the first argument"
    echo "Usage: $0 <bot_token> [api_url]"
    echo "Example: $0 123456789:ABCdefGHIjklMNOpqrsTUVwxyz http://localhost:5000"
    exit 1
fi

BOT_TOKEN="$1"
API_URL="${2:-http://localhost:5000}"

print_status "Bot Token: ${BOT_TOKEN:0:10}..."
print_status "API URL: $API_URL"

# Create results directory
RESULTS_DIR="test_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

print_status "Results will be saved to: $RESULTS_DIR"

# Function to check if services are running
check_services() {
    print_status "Checking if services are running..."
    
    # Check API server
    if curl -s "$API_URL/api/health" > /dev/null 2>&1; then
        print_success "API server is running"
    else
        print_error "API server is not running on $API_URL"
        print_warning "Please start the API server: python api_server.py"
        exit 1
    fi
    
    # Check if bot is running (this is harder to check, so we'll assume it is)
    print_warning "Assuming bot is running. If tests fail, check bot status."
}

# Function to run functional tests
run_functional_tests() {
    print_status "Running functional tests..."
    
    if python functional_tester.py --token "$BOT_TOKEN" --api-url "$API_URL"; then
        print_success "Functional tests completed"
        
        # Move results to results directory
        mv functional_test_results_*.json "$RESULTS_DIR/" 2>/dev/null || true
        mv functional_test_analysis_*.json "$RESULTS_DIR/" 2>/dev/null || true
        
        return 0
    else
        print_error "Functional tests failed"
        return 1
    fi
}

# Function to run load tests
run_load_tests() {
    print_status "Running load tests..."
    
    # Light load test
    print_status "Running light load test (10 users)..."
    if python bot_load_tester.py --token "$BOT_TOKEN" --users 10 --concurrent 3; then
        print_success "Light load test completed"
        mv bot_test_results_*.json "$RESULTS_DIR/light_load_test.json" 2>/dev/null || true
    else
        print_error "Light load test failed"
        return 1
    fi
    
    # Medium load test
    print_status "Running medium load test (25 users)..."
    if python bot_load_tester.py --token "$BOT_TOKEN" --users 25 --concurrent 5; then
        print_success "Medium load test completed"
        mv bot_test_results_*.json "$RESULTS_DIR/medium_load_test.json" 2>/dev/null || true
    else
        print_error "Medium load test failed"
        return 1
    fi
    
    # Heavy load test
    print_status "Running heavy load test (50 users)..."
    if python bot_load_tester.py --token "$BOT_TOKEN" --users 50 --concurrent 10; then
        print_success "Heavy load test completed"
        mv bot_test_results_*.json "$RESULTS_DIR/heavy_load_test.json" 2>/dev/null || true
    else
        print_error "Heavy load test failed"
        return 1
    fi
    
    return 0
}

# Function to run performance monitoring
run_performance_monitoring() {
    print_status "Running performance monitoring..."
    
    # Start performance monitoring in background
    python performance_monitor.py --api-url "$API_URL" --duration 10 --interval 15 &
    MONITOR_PID=$!
    
    # Wait for monitoring to complete
    wait $MONITOR_PID
    
    if [ $? -eq 0 ]; then
        print_success "Performance monitoring completed"
        mv performance_metrics_*.json "$RESULTS_DIR/" 2>/dev/null || true
        mv performance_analysis_*.json "$RESULTS_DIR/" 2>/dev/null || true
        return 0
    else
        print_error "Performance monitoring failed"
        return 1
    fi
}

# Function to run stress test
run_stress_test() {
    print_status "Running stress test (5 minutes)..."
    
    if python bot_load_tester.py --token "$BOT_TOKEN" --stress 5; then
        print_success "Stress test completed"
        mv bot_test_results_*.json "$RESULTS_DIR/stress_test.json" 2>/dev/null || true
        return 0
    else
        print_error "Stress test failed"
        return 1
    fi
}

# Function to generate summary report
generate_summary_report() {
    print_status "Generating summary report..."
    
    REPORT_FILE="$RESULTS_DIR/test_summary.md"
    
    cat > "$REPORT_FILE" << EOF
# Bot Testing Summary Report

**Generated on:** $(date)
**Bot Token:** ${BOT_TOKEN:0:10}...
**API URL:** $API_URL

## Test Results Overview

### Functional Tests
EOF

    # Check if functional test results exist
    if [ -f "$RESULTS_DIR/functional_test_analysis_"*.json ]; then
        echo "✅ Functional tests completed successfully" >> "$REPORT_FILE"
    else
        echo "❌ Functional tests failed or not found" >> "$REPORT_FILE"
    fi

    cat >> "$REPORT_FILE" << EOF

### Load Tests
EOF

    # Check load test results
    if [ -f "$RESULTS_DIR/light_load_test.json" ]; then
        echo "✅ Light load test (10 users) completed" >> "$REPORT_FILE"
    else
        echo "❌ Light load test failed" >> "$REPORT_FILE"
    fi

    if [ -f "$RESULTS_DIR/medium_load_test.json" ]; then
        echo "✅ Medium load test (25 users) completed" >> "$REPORT_FILE"
    else
        echo "❌ Medium load test failed" >> "$REPORT_FILE"
    fi

    if [ -f "$RESULTS_DIR/heavy_load_test.json" ]; then
        echo "✅ Heavy load test (50 users) completed" >> "$REPORT_FILE"
    else
        echo "❌ Heavy load test failed" >> "$REPORT_FILE"
    fi

    cat >> "$REPORT_FILE" << EOF

### Performance Monitoring
EOF

    # Check performance monitoring results
    if [ -f "$RESULTS_DIR/performance_analysis_"*.json ]; then
        echo "✅ Performance monitoring completed" >> "$REPORT_FILE"
    else
        echo "❌ Performance monitoring failed" >> "$REPORT_FILE"
    fi

    cat >> "$REPORT_FILE" << EOF

### Stress Test
EOF

    # Check stress test results
    if [ -f "$RESULTS_DIR/stress_test.json" ]; then
        echo "✅ Stress test (5 minutes) completed" >> "$REPORT_FILE"
    else
        echo "❌ Stress test failed" >> "$REPORT_FILE"
    fi

    cat >> "$REPORT_FILE" << EOF

## Files Generated

EOF

    # List all generated files
    ls -la "$RESULTS_DIR" >> "$REPORT_FILE"

    cat >> "$REPORT_FILE" << EOF

## Next Steps

1. Review the generated JSON files for detailed results
2. Check the performance analysis for bottlenecks
3. Identify areas for optimization
4. Re-run tests after making improvements

## Recommendations

Based on your VPS specifications (4 vCores, 8GB RAM, NVMe SSD):

- **Target concurrent users:** 20-30
- **Target API response time:** < 1 second
- **Target CPU usage:** < 60%
- **Target memory usage:** < 70%
- **Target success rate:** > 95%

If any of these targets are not met, consider:
- Database optimization
- Code performance improvements
- Resource scaling
- Architecture changes

EOF

    print_success "Summary report generated: $REPORT_FILE"
}

# Main execution
main() {
    print_status "Starting comprehensive bot testing..."
    
    # Check services
    check_services
    
    # Run tests in sequence
    print_status "Running tests in sequence..."
    
    # Functional tests
    if run_functional_tests; then
        print_success "Functional tests passed"
    else
        print_error "Functional tests failed"
        exit 1
    fi
    
    # Load tests
    if run_load_tests; then
        print_success "Load tests passed"
    else
        print_error "Load tests failed"
        exit 1
    fi
    
    # Performance monitoring
    if run_performance_monitoring; then
        print_success "Performance monitoring completed"
    else
        print_error "Performance monitoring failed"
        exit 1
    fi
    
    # Stress test
    if run_stress_test; then
        print_success "Stress test passed"
    else
        print_error "Stress test failed"
        exit 1
    fi
    
    # Generate summary report
    generate_summary_report
    
    print_success "All tests completed successfully!"
    print_status "Results saved in: $RESULTS_DIR"
    print_status "Summary report: $RESULTS_DIR/test_summary.md"
    
    # Show quick summary
    echo ""
    echo "📊 Quick Summary:"
    echo "=================="
    echo "Results directory: $RESULTS_DIR"
    echo "Total files generated: $(ls -1 "$RESULTS_DIR" | wc -l)"
    echo "Summary report: $RESULTS_DIR/test_summary.md"
    echo ""
    echo "To view the summary report:"
    echo "cat $RESULTS_DIR/test_summary.md"
    echo ""
    echo "To view detailed results:"
    echo "ls -la $RESULTS_DIR/"
}

# Run main function
main "$@"

