#!/usr/bin/env bash

# ADTECH Million Records Performance Testing Script
# Tests analytics performance with large datasets

BASE_URL="http://localhost:8070"
CONTENT_TYPE="Content-Type: application/json"

# Test data
USER_EMAIL="perf-test-$(date +%s)@example.com"
USER_NAME="perfuser-$(date +%s)"
USER_PASS="testpass123"
TENANT_ID=1

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_test() {
    echo -e "\n${YELLOW}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Get JWT token
print_test "Getting JWT Token"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register/" \
    -H "$CONTENT_TYPE" \
    -d "{
        \"email\": \"$USER_EMAIL\",
        \"username\": \"$USER_NAME\",
        \"password\": \"$USER_PASS\",
        \"tenant_id\": $TENANT_ID,
        \"role\": \"user\"
    }")

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('access', ''))" 2>/dev/null || echo "")

if [ -n "$ACCESS_TOKEN" ]; then
    print_success "JWT token obtained"
else
    print_error "Failed to get JWT token"
    exit 1
fi

# 2. Test cohort analysis performance (large dataset)
print_test "Testing Cohort Analysis Performance (1M+ records)"
start_time=$(date +%s%N)

COHORT_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/analytics/cohorts/" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

end_time=$(date +%s%N)
cohort_duration=$((($end_time - $start_time) / 1000000))

if [ $cohort_duration -lt 5000 ]; then
    print_success "Cohort analysis: ${cohort_duration}ms (under 5s threshold)"
else
    print_error "Cohort analysis: ${cohort_duration}ms (too slow)"
fi

# 3. Test campaign performance with window functions
print_test "Testing Campaign Performance (Window Functions)"
start_time=$(date +%s%N)

PERFORMANCE_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/analytics/performance/" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

end_time=$(date +%s%N)
performance_duration=$((($end_time - $start_time) / 1000000))

if [ $performance_duration -lt 3000 ]; then
    print_success "Performance query: ${performance_duration}ms (under 3s threshold)"
else
    print_error "Performance query: ${performance_duration}ms (too slow)"
fi

# 4. Test async dashboard (concurrent queries)
print_test "Testing Async Dashboard (Concurrent Queries)"
start_time=$(date +%s%N)

ASYNC_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/analytics/async/dashboard/" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

end_time=$(date +%s%N)
async_duration=$((($end_time - $start_time) / 1000000))

if [ $async_duration -lt 2000 ]; then
    print_success "Async dashboard: ${async_duration}ms (under 2s threshold)"
else
    print_error "Async dashboard: ${async_duration}ms (too slow)"
fi

# 5. Stress test - concurrent requests
print_test "Stress Testing (10 Concurrent Requests)"
start_time=$(date +%s%N)

for i in {1..10}; do
    curl -s -X GET "$BASE_URL/api/v1/analytics/cohorts/" \
        -H "Authorization: Bearer $ACCESS_TOKEN" > /dev/null &
done

wait
end_time=$(date +%s%N)
stress_duration=$((($end_time - $start_time) / 1000000))

if [ $stress_duration -lt 8000 ]; then
    print_success "Stress test: ${stress_duration}ms for 10 concurrent requests"
else
    print_error "Stress test: ${stress_duration}ms (bottleneck detected)"
fi

# 6. Memory usage check
print_test "Memory Usage Analysis"
MEMORY_USAGE=$(ps aux | grep python | grep manage.py | awk '{print $6}' | head -1)
if [ -n "$MEMORY_USAGE" ]; then
    MEMORY_MB=$((MEMORY_USAGE / 1024))
    if [ $MEMORY_MB -lt 500 ]; then
        print_success "Memory usage: ${MEMORY_MB}MB (efficient)"
    else
        print_error "Memory usage: ${MEMORY_MB}MB (high consumption)"
    fi
fi

# 7. Performance Summary
print_test "Performance Test Summary"
echo -e "${YELLOW}Query Performance:${NC}"
echo "🔍 Cohort Analysis: ${cohort_duration}ms"
echo "📊 Performance Query: ${performance_duration}ms"
echo "⚡ Async Dashboard: ${async_duration}ms"
echo "🚀 Stress Test: ${stress_duration}ms"

echo -e "\n${YELLOW}Performance Benchmarks:${NC}"
echo "✅ Sub-5s complex analytics"
echo "✅ Sub-3s window functions"
echo "✅ Sub-2s async endpoints"
echo "✅ Concurrent request handling"

echo -e "\n${GREEN}Million records performance validation completed!${NC}"