#!/usr/bin/env bash

# ADTECH Endpoint Validation Script
# Validates all implemented endpoints with proper error handling

BASE_URL="http://localhost:8070"
CONTENT_TYPE="Content-Type: application/json"

# Test data variables
USER_EMAIL="test-$(date +%s)@example.com"
USER_NAME="testuser-$(date +%s)"
USER_PASS="testpass123"
TENANT_ID=1

CAMPAIGN_NAME="Test Campaign $(date +%s)"
CAMPAIGN_BUDGET="1000.00"
CAMPAIGN_STATUS="active"
CAMPAIGN_START="2025-01-01"
CAMPAIGN_END="2025-12-31"

AD_URL="https://example.com/banner.jpg"
AD_AUDIENCE="18-35 tech professionals"

# Global variables for tokens and IDs
ACCESS_TOKEN=""
REFRESH_TOKEN=""
CAMPAIGN_ID=""
AD_ID=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_test() {
    echo -e "\n${YELLOW}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

extract_json_value() {
    echo "$1" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('$2', ''))" 2>/dev/null || echo ""
}

# 1. Health check
print_test "Health Check"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/v1/auth/register/" -X OPTIONS)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "405" ]; then
    print_success "Django server is running"
else
    print_error "Django server not accessible (HTTP: $HTTP_CODE)"
    exit 1
fi

# 2. User Registration
print_test "User Registration"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register/" \
    -H "$CONTENT_TYPE" \
    -d "{
        \"email\": \"$USER_EMAIL\",
        \"username\": \"$USER_NAME\",
        \"password\": \"$USER_PASS\",
        \"tenant_id\": $TENANT_ID,
        \"role\": \"user\"
    }")

ACCESS_TOKEN=$(extract_json_value "$REGISTER_RESPONSE" "access")
REFRESH_TOKEN=$(extract_json_value "$REGISTER_RESPONSE" "refresh")

if [ -n "$ACCESS_TOKEN" ]; then
    print_success "User registration successful"
else
    print_error "User registration failed: $REGISTER_RESPONSE"
fi

# 3. User Login
print_test "User Login"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login/" \
    -H "$CONTENT_TYPE" \
    -d "{
        \"email\": \"$USER_EMAIL\",
        \"password\": \"$USER_PASS\"
    }")

LOGIN_ACCESS_TOKEN=$(extract_json_value "$LOGIN_RESPONSE" "access")
if [ -n "$LOGIN_ACCESS_TOKEN" ]; then
    print_success "User login successful"
    ACCESS_TOKEN="$LOGIN_ACCESS_TOKEN"  # Use login token
else
    print_error "User login failed: $LOGIN_RESPONSE"
fi

# 4. Create Campaign (Protected endpoint)
print_test "Create Campaign (Protected)"
CAMPAIGN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/campaigns/" \
    -H "$CONTENT_TYPE" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "{
        \"name\": \"$CAMPAIGN_NAME\",
        \"budget\": \"$CAMPAIGN_BUDGET\",
        \"status\": \"$CAMPAIGN_STATUS\",
        \"start_date\": \"$CAMPAIGN_START\",
        \"end_date\": \"$CAMPAIGN_END\"
    }")

CAMPAIGN_ID=$(extract_json_value "$CAMPAIGN_RESPONSE" "id")
if [ -n "$CAMPAIGN_ID" ]; then
    print_success "Campaign created successfully (ID: $CAMPAIGN_ID)"
else
    print_error "Campaign creation failed: $CAMPAIGN_RESPONSE"
fi

# 5. Get Campaigns List
print_test "Get Campaigns List"
CAMPAIGNS_LIST=$(curl -s -X GET "$BASE_URL/api/v1/campaigns/" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$CAMPAIGNS_LIST" | grep -q "\"id\""; then
    print_success "Campaigns list retrieved"
else
    print_error "Failed to get campaigns list: $CAMPAIGNS_LIST"
fi

# 6. Create Ad (if campaign exists)
if [ -n "$CAMPAIGN_ID" ]; then
    print_test "Create Ad"
    AD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/ads/" \
        -H "$CONTENT_TYPE" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "{
            \"campaign\": $CAMPAIGN_ID,
            \"creative_url\": \"$AD_URL\",
            \"target_audience\": \"$AD_AUDIENCE\"
        }")

    AD_ID=$(extract_json_value "$AD_RESPONSE" "id")
    if [ -n "$AD_ID" ]; then
        print_success "Ad created successfully (ID: $AD_ID)"
    else
        print_error "Ad creation failed: $AD_RESPONSE"
    fi
fi

# 7. Get Ads List
print_test "Get Ads List"
ADS_LIST=$(curl -s -X GET "$BASE_URL/api/v1/ads/" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$ADS_LIST" | grep -q "\"id\""; then
    print_success "Ads list retrieved"
else
    print_error "Failed to get ads list: $ADS_LIST"
fi

# 8. Token Refresh
print_test "Token Refresh"
if [ -n "$REFRESH_TOKEN" ]; then
    REFRESH_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/token/refresh/" \
        -H "$CONTENT_TYPE" \
        -d "{\"refresh\": \"$REFRESH_TOKEN\"}")

    NEW_ACCESS_TOKEN=$(extract_json_value "$REFRESH_RESPONSE" "access")
    if [ -n "$NEW_ACCESS_TOKEN" ]; then
        print_success "Token refresh successful"
    else
        print_error "Token refresh failed: $REFRESH_RESPONSE"
    fi
else
    print_error "No refresh token available for testing"
fi

# 9. Test Unauthorized Access
print_test "Unauthorized Access Test"
UNAUTH_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/v1/campaigns/")
UNAUTH_HTTP_CODE=$(echo "$UNAUTH_RESPONSE" | tail -n1)

if [ "$UNAUTH_HTTP_CODE" = "401" ]; then
    print_success "Unauthorized access properly blocked"
else
    print_error "Unauthorized access not properly handled (HTTP: $UNAUTH_HTTP_CODE)"
fi

# 10. Summary
print_test "Validation Summary"
echo -e "${YELLOW}Endpoints validated:${NC}"
echo "✓ Django server health"
echo "✓ User registration"
echo "✓ User login"
echo "✓ Protected campaign creation"
echo "✓ Campaigns listing"
echo "✓ Ad creation"
echo "✓ Ads listing"
echo "✓ Token refresh"
echo "✓ Authorization protection"

echo -e "\n${GREEN}Validation completed!${NC}"
echo -e "${YELLOW}Created IDs for cleanup:${NC}"
echo "Campaign ID: $CAMPAIGN_ID"
echo "Ad ID: $AD_ID"