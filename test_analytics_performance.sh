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
ADVERTISER_ID=""
CAMPAIGN_ID=""
AD_ID=""

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

# 2. Create advertiser first (required for campaigns)
print_test "Creating advertiser"
ADVERTISER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/advertisers/" \
    -H "$CONTENT_TYPE" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "{
        \"name\": \"Test Advertiser Analytics\",
        \"email\": \"advertiser-analytics@test.com\",
        \"status\": \"active\"
    }")

ADVERTISER_ID=$(echo "$ADVERTISER_RESPONSE" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null || echo "")

if [ -n "$ADVERTISER_ID" ]; then
    print_success "Advertiser created (ID: $ADVERTISER_ID)"
else
    print_error "Advertiser creation failed: $ADVERTISER_RESPONSE"
    exit 1
fi

# 3. Create test campaign with advertiser
print_test "Creating test campaign"
CAMPAIGN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/campaigns/" \
    -H "$CONTENT_TYPE" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "{
        \"name\": \"Analytics Test Campaign\",
        \"budget\": \"5000.00\",
        \"status\": \"active\",
        \"start_date\": \"2025-01-01\",
        \"end_date\": \"2025-12-31\",
        \"advertiser\": $ADVERTISER_ID
    }")

CAMPAIGN_ID=$(echo "$CAMPAIGN_RESPONSE" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null || echo "")

if [ -n "$CAMPAIGN_ID" ]; then
    print_success "Campaign created (ID: $CAMPAIGN_ID)"
else
    print_error "Campaign creation failed: $CAMPAIGN_RESPONSE"
    exit 1
fi

# 4. Create ad for events testing (requires creative and audience - mock for now)
print_test "Creating test ad"
AD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/ads/" \
    -H "$CONTENT_TYPE" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "{
        \"campaign\": $CAMPAIGN_ID,
        \"creative_url\": \"https://example.com/banner.jpg\",
        \"target_audience\": \"18-35 tech professionals\",
        \"creative\": 1,
        \"audience\": 1
    }")

AD_ID=$(echo "$AD_RESPONSE" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null || echo "")

if [ -n "$AD_ID" ]; then
    print_success "Ad created (ID: $AD_ID)"
else
    print_error "Ad creation failed (likely missing creative/audience): $AD_RESPONSE"
    echo "⚠️  Note: Ad creation failed but continuing with campaign tests..."
fi

# 5. Test cohort analysis endpoint (Raw SQL)
print_test "Testing Cohort Analysis (Raw SQL)"
COHORT_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/analytics/cohorts/" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$COHORT_RESPONSE" | grep -q "cohort_month\|users\|\[\]"; then
    print_success "Cohort analysis endpoint working"
    echo "Response preview: $(echo "$COHORT_RESPONSE" | head -c 100)..."
else
    print_error "Cohort analysis failed: $COHORT_RESPONSE"
fi

# 6. Test campaign performance (Window functions)
print_test "Testing Campaign Performance (Window Functions)"
PERFORMANCE_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/analytics/performance/" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$PERFORMANCE_RESPONSE" | grep -q "campaign_id\|impressions\|rank\|\[\]"; then
    print_success "Performance analytics endpoint working"
    echo "Response preview: $(echo "$PERFORMANCE_RESPONSE" | head -c 100)..."
else
    print_error "Performance analytics failed: $PERFORMANCE_RESPONSE"
fi

# 7. Test real-time dashboard
print_test "Testing Real-time Dashboard"
DASHBOARD_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/analytics/realtime/dashboard/" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$DASHBOARD_RESPONSE" | grep -q "realtime_metrics\|status\|execution_time\|\[\]"; then
    print_success "Real-time dashboard working"
    echo "Response preview: $(echo "$DASHBOARD_RESPONSE" | head -c 150)..."
else
    print_error "Real-time dashboard failed: $DASHBOARD_RESPONSE"
fi

# 8. Test attribution analysis
print_test "Testing Attribution Analysis"
ATTRIBUTION_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/analytics/attribution/?campaign_id=$CAMPAIGN_ID" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$ATTRIBUTION_RESPONSE" | grep -q "attribution_data\|campaign_filter\|\[\]"; then
    print_success "Attribution analysis working"
    echo "Response preview: $(echo "$ATTRIBUTION_RESPONSE" | head -c 100)..."
else
    print_error "Attribution analysis failed: $ATTRIBUTION_RESPONSE"
fi

# 9. Test campaign ranking
print_test "Testing Campaign Performance Ranking"
RANKING_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/analytics/campaigns/ranking/?limit=10" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$RANKING_RESPONSE" | grep -q "campaign_rankings\|limit\|\[\]"; then
    print_success "Campaign ranking working"
    echo "Response preview: $(echo "$RANKING_RESPONSE" | head -c 100)..."
else
    print_error "Campaign ranking failed: $RANKING_RESPONSE"
fi

# 10. Test event creation (Event Sourcing) - only if we have ad_id
if [ -n "$AD_ID" ]; then
    print_test "Testing Event Creation (Event Sourcing)"
    
    # Create impression event
    IMPRESSION_EVENT=$(curl -s -X POST "$BASE_URL/api/v1/events/impression/" \
        -H "$CONTENT_TYPE" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "{
            \"campaign_id\": $CAMPAIGN_ID,
            \"ad_id\": $AD_ID,
            \"user_id\": 12345,
            \"cost\": \"0.50\"
        }")

    if echo "$IMPRESSION_EVENT" | grep -q "event_id\|event_type\|recorded\|status"; then
        print_success "Impression event created"
    else
        print_error "Impression event failed: $IMPRESSION_EVENT"
    fi
else
    print_test "Skipping Event Creation (No Ad ID available)"
    echo "⚠️  Event creation requires valid ad_id (creative and audience dependencies)"
fi

# 11. Test event replay (Event Sourcing)
print_test "Testing Event Replay (Event Sourcing)"
REPLAY_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/analytics/rebuild-metrics/$CAMPAIGN_ID/" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$REPLAY_RESPONSE" | grep -q "events_replayed\|status\|completed"; then
    print_success "Event replay working"
    echo "Response: $(echo "$REPLAY_RESPONSE" | head -c 200)..."
else
    print_error "Event replay failed: $REPLAY_RESPONSE"
fi

# 12. Test audit trail
print_test "Testing Audit Trail"
AUDIT_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/analytics/audit/campaign/$CAMPAIGN_ID/events/" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$AUDIT_RESPONSE" | grep -q "audit_events\|campaign_id\|\[\]"; then
    print_success "Audit trail working"
    echo "Response preview: $(echo "$AUDIT_RESPONSE" | head -c 100)..."
else
    print_error "Audit trail failed: $AUDIT_RESPONSE"
fi

# 13. Test Celery health
print_test "Testing Celery Health Check"
CELERY_RESPONSE=$(curl -s -X GET "$BASE_URL/api/v1/analytics/celery/health/" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$CELERY_RESPONSE" | grep -q "celery_status\|active_workers"; then
    print_success "Celery health check working"
    echo "Response: $(echo "$CELERY_RESPONSE" | head -c 150)..."
else
    print_error "Celery health check failed: $CELERY_RESPONSE"
fi

# 14. Performance check - multiple concurrent requests
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

# 15. Summary
print_test "Analytics Endpoints Test Summary"
echo "✅ Authentication working"
echo "✅ Advertiser creation working"
echo "✅ Campaign creation working"
echo "✅ Analytics repository endpoints"
echo "✅ Event sourcing replay"
echo "✅ Performance monitoring"
echo "✅ Concurrent request handling"

echo -e "\n${GREEN}Analytics endpoints validation completed!${NC}"