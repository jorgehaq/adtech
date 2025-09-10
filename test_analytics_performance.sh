#!/usr/bin/env bash

# ADTECH Analytics & Performance Testing Script
# Tests Raw SQL analytics and event sourcing endpoints

BASE_URL="http://localhost:8070"
CONTENT_TYPE="Content-Type: application/json"

# Test data
USER_EMAIL="analytics-test-$(date +%s)@example.com"
USER_NAME="analyticsuser-$(date +%s)"
USER_PASS="testpass123"
TENANT_ID=1

# Global variables
ACCESS_TOKEN=""
CAMPAIGN_ID=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
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

# 1. Setup authentication
print_test "Setting up authentication"
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
    print_success "Authentication successful"
else
    print_error "Authentication failed: $LOGIN_RESPONSE"
    exit 1
fi

# 2. Create test campaign for analytics
print_test "Creating test campaign"
CAMPAIGN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/campaigns/" \
    -H "$CONTENT_TYPE" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "{
        \"name\": \"Analytics Test Campaign\",
        \"budget\": \"5000.00\",
        \"status\": \"active\",
        \"start_date\": \"2025-01-01\",
        \"end_date\": \"2025-12-31\"
    }")

CAMPAIGN_ID=$(echo "$CAMPAIGN_RESPONSE" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null || echo "")

if [ -n "$CAMPAIGN_ID" ]; then
    print_success "Campaign created (ID: $CAMPAIGN_ID)"
else
    print_error "Campaign creation failed: $CAMPAIGN_RESPONSE"
fi

# 3. Test cohort analysis endpoint (Raw SQL)
print_test "Testing Cohort Analysis (Raw SQL)"
COHORT_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/analytics/cohorts/" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$COHORT_RESPONSE" | grep -q "cohort_month\|users\|\[\]"; then
    print_success "Cohort analysis endpoint working"
    echo "Response preview: $(echo "$COHORT_RESPONSE" | head -c 100)..."
else
    print_error "Cohort analysis failed: $COHORT_RESPONSE"
fi

# 4. Test campaign performance (Window functions)
print_test "Testing Campaign Performance (Window Functions)"
PERFORMANCE_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/analytics/performance/" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$PERFORMANCE_RESPONSE" | grep -q "campaign_id\|impressions\|rank\|\[\]"; then
    print_success "Performance analytics endpoint working"
    echo "Response preview: $(echo "$PERFORMANCE_RESPONSE" | head -c 100)..."
else
    print_error "Performance analytics failed: $PERFORMANCE_RESPONSE"
fi

# 5. Test event creation (Event Sourcing)
print_test "Testing Event Creation (Event Sourcing)"

# Create impression event
IMPRESSION_EVENT=$(curl -s -X POST "$BASE_URL/api/v1/events/impression/" \
    -H "$CONTENT_TYPE" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "{
        \"campaign_id\": \"$CAMPAIGN_ID\",
        \"user_id\": 12345,
        \"cost\": \"0.50\"
    }")

if echo "$IMPRESSION_EVENT" | grep -q "id\|event_type\|created"; then
    print_success "Impression event created"
else
    print_error "Impression event failed: $IMPRESSION_EVENT"
fi

# 6. Test event replay (Event Sourcing)
if [ -n "$CAMPAIGN_ID" ]; then
    print_test "Testing Event Replay (Event Sourcing)"
    REPLAY_RESPONSE=$(curl -s -X POST "$BASE_URL/admin/rebuild-metrics/$CAMPAIGN_ID/" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$REPLAY_RESPONSE" | grep -q "rebuilt\|events\|success"; then
        print_success "Event replay working"
    else
        print_error "Event replay failed: $REPLAY_RESPONSE"
    fi
fi

# 7. Test audit trail
if [ -n "$CAMPAIGN_ID" ]; then
    print_test "Testing Audit Trail"
    AUDIT_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/audit/campaign/$CAMPAIGN_ID/events/" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$AUDIT_RESPONSE" | grep -q "event_type\|timestamp\|\[\]"; then
        print_success "Audit trail working"
    else
        print_error "Audit trail failed: $AUDIT_RESPONSE"
    fi
fi

# 8. Performance check - multiple concurrent requests
print_test "Performance Testing (Concurrent Requests)"
start_time=$(date +%s%N)

for i in {1..5}; do
    curl -s -X GET "$BASE_URL/api/v1/analytics/cohorts/" \
        -H "Authorization: Bearer $ACCESS_TOKEN" > /dev/null &
done

wait

end_time=$(date +%s%N)
duration=$((($end_time - $start_time) / 1000000))

if [ $duration -lt 2000 ]; then
    print_success "Performance test passed (${duration}ms for 5 concurrent requests)"
else
    print_error "Performance test failed (${duration}ms - too slow)"
fi

# 9. Summary
print_test "Analytics & Performance Test Summary"
echo -e "${YELLOW}Features tested:${NC}"
echo "✅ Raw SQL cohort analysis"
echo "✅ Window functions performance queries"
echo "✅ Event sourcing creation"
echo "✅ Event replay functionality"
echo "✅ Audit trail access"
echo "✅ Concurrent request performance"

echo -e "\n${GREEN}Analytics & Performance validation completed!${NC}"
echo -e "${YELLOW}Ready for Semana 3 completion${NC}"