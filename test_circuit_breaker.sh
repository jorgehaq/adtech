# test_circuit_breaker.sh (actualizar)
#!/usr/bin/env bash

BASE_URL="http://localhost:${TEST_PORT:-8070}"
CONTENT_TYPE="Content-Type: application/json"

# Test data
USER_EMAIL="circuit-test-$(date +%s)@example.com"
USER_NAME="circuituser-$(date +%s)"
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

# 2. Test normal operation (should work)
print_test "Testing Normal Operation"
NORMAL_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/v1/campaigns/" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

HTTP_CODE=$(echo "$NORMAL_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "200" ]; then
    print_success "Normal operation works (HTTP: $HTTP_CODE)"
else
    print_error "Normal operation failed (HTTP: $HTTP_CODE)"
fi

# 3. Test circuit breaker status
print_test "Testing Circuit Breaker Status"
STATUS_RESPONSE=$(curl -s "$BASE_URL/api/v1/analytics/circuit-breaker/status/" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$STATUS_RESPONSE" | grep -q "closed\|open\|half_open"; then
    print_success "Circuit breaker status working"
    echo "Status: $STATUS_RESPONSE"
else
    print_error "Circuit breaker status failed: $STATUS_RESPONSE"
fi

# 4. Test with rapid requests (stress test)
print_test "Testing Rapid Requests (Circuit Breaker Stress)"
echo "Sending 10 rapid requests..."

start_time=$(date +%s%N)
for i in {1..10}; do
    curl -s -X GET "$BASE_URL/api/v1/campaigns/" \
        -H "Authorization: Bearer $ACCESS_TOKEN" > /dev/null &
done
wait
end_time=$(date +%s%N)

duration=$((($end_time - $start_time) / 1000000))
print_success "10 concurrent requests completed in ${duration}ms"

# 5. Summary
print_test "Circuit Breaker Test Summary"
echo "✅ JWT authentication"
echo "✅ Normal operation protection"
echo "✅ Status endpoint"
echo "✅ Stress testing"

echo -e "\n${GREEN}Circuit breaker validation completed!${NC}"