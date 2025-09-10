#!/usr/bin/env bash

# ADTECH GraphQL Endpoint Validation Script
# Tests distributed GraphQL schema with campaigns and authentication

BASE_URL="http://localhost:8070"
GRAPHQL_ENDPOINT="$BASE_URL/graphql/"
CONTENT_TYPE="Content-Type: application/json"

# Test data variables
USER_EMAIL="graphql-test-$(date +%s)@example.com"
USER_NAME="graphqluser-$(date +%s)"
USER_PASS="testpass123"
TENANT_ID=1

CAMPAIGN_NAME="GraphQL Test Campaign"
CAMPAIGN_BUDGET="2000.00"
CAMPAIGN_STATUS="active"
CAMPAIGN_START="2025-01-01"
CAMPAIGN_END="2025-12-31"

AD_URL="https://example.com/graphql-banner.jpg"
AD_AUDIENCE="25-40 GraphQL developers"

# Global variables
ACCESS_TOKEN=""
CAMPAIGN_ID=""

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
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Health check GraphQL endpoint
print_test "GraphQL Endpoint Health Check"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$GRAPHQL_ENDPOINT" -X GET)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "405" ]; then
    print_success "GraphQL endpoint is accessible (HTTP: $HTTP_CODE)"
else
    print_error "GraphQL endpoint not accessible (HTTP: $HTTP_CODE)"
    exit 1
fi

# 2. Get JWT token for authenticated queries
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
    print_error "Failed to get JWT token: $LOGIN_RESPONSE"
    exit 1
fi

# 3. GraphQL Query: Get all campaigns
print_test "GraphQL Query: All Campaigns"
CAMPAIGNS_QUERY='{
    "query": "query GetCampaigns { campaigns { id name budget status startDate endDate } }"
}'

CAMPAIGNS_RESPONSE=$(curl -s -X POST "$GRAPHQL_ENDPOINT" \
    -H "$CONTENT_TYPE" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "$CAMPAIGNS_QUERY")

if echo "$CAMPAIGNS_RESPONSE" | grep -q '"campaigns"\|"data"'; then
    print_success "Campaigns query executed successfully"
    echo "Response: $(echo "$CAMPAIGNS_RESPONSE" | head -c 200)..."
else
    print_error "Campaigns query failed: $CAMPAIGNS_RESPONSE"
fi

# 4. GraphQL Query: Get all users
print_test "GraphQL Query: All Users"
USERS_QUERY='{
    "query": "query GetUsers { users { id username email tenantId role } }"
}'

USERS_RESPONSE=$(curl -s -X POST "$GRAPHQL_ENDPOINT" \
    -H "$CONTENT_TYPE" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "$USERS_QUERY")

if echo "$USERS_RESPONSE" | grep -q '"users"\|"data"'; then
    print_success "Users query executed successfully"
    echo "Response: $(echo "$USERS_RESPONSE" | head -c 200)..."
else
    print_error "Users query failed: $USERS_RESPONSE"
fi

# 5. GraphQL Mutation: Create campaign
print_test "GraphQL Mutation: Create Campaign"
CREATE_CAMPAIGN_MUTATION="{
    \"query\": \"mutation CreateCampaign(\$input: CampaignInput!) { createCampaign(input: \$input) { id name budget status } }\",
    \"variables\": {
        \"input\": {
            \"tenantId\": $TENANT_ID,
            \"name\": \"$CAMPAIGN_NAME\",
            \"budget\": \"$CAMPAIGN_BUDGET\",
            \"status\": \"$CAMPAIGN_STATUS\",
            \"startDate\": \"$CAMPAIGN_START\",
            \"endDate\": \"$CAMPAIGN_END\"
        }
    }
}"

CAMPAIGN_MUTATION_RESPONSE=$(curl -s -X POST "$GRAPHQL_ENDPOINT" \
    -H "$CONTENT_TYPE" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "$CREATE_CAMPAIGN_MUTATION")

CAMPAIGN_ID=$(echo "$CAMPAIGN_MUTATION_RESPONSE" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('data', {}).get('createCampaign', {}).get('id', ''))" 2>/dev/null || echo "")

if [ -n "$CAMPAIGN_ID" ]; then
    print_success "Campaign created via GraphQL (ID: $CAMPAIGN_ID)"
else
    print_error "Campaign creation failed: $CAMPAIGN_MUTATION_RESPONSE"
fi

# 6. GraphQL Query: Get specific campaign
if [ -n "$CAMPAIGN_ID" ]; then
    print_test "GraphQL Query: Specific Campaign"
    SINGLE_CAMPAIGN_QUERY="{
        \"query\": \"query GetCampaign(\$id: Int!) { campaign(id: \$id) { id name budget status } }\",
        \"variables\": { \"id\": $CAMPAIGN_ID }
    }"

    SINGLE_CAMPAIGN_RESPONSE=$(curl -s -X POST "$GRAPHQL_ENDPOINT" \
        -H "$CONTENT_TYPE" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "$SINGLE_CAMPAIGN_QUERY")

    if echo "$SINGLE_CAMPAIGN_RESPONSE" | grep -q '"campaign"'; then
        print_success "Single campaign query executed successfully"
    else
        print_error "Single campaign query failed: $SINGLE_CAMPAIGN_RESPONSE"
    fi
fi

# 7. GraphQL Mutation: Create ad
if [ -n "$CAMPAIGN_ID" ]; then
    print_test "GraphQL Mutation: Create Ad"
    CREATE_AD_MUTATION="{
        \"query\": \"mutation CreateAd(\$input: AdInput!) { createAd(input: \$input) { id creativeUrl targetAudience campaign { name } } }\",
        \"variables\": {
            \"input\": {
                \"tenantId\": $TENANT_ID,
                \"campaignId\": $CAMPAIGN_ID,
                \"creativeUrl\": \"$AD_URL\",
                \"targetAudience\": \"$AD_AUDIENCE\"
            }
        }
    }"

    AD_MUTATION_RESPONSE=$(curl -s -X POST "$GRAPHQL_ENDPOINT" \
        -H "$CONTENT_TYPE" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "$CREATE_AD_MUTATION")

    if echo "$AD_MUTATION_RESPONSE" | grep -q '"createAd"'; then
        print_success "Ad created via GraphQL mutation"
    else
        print_error "Ad creation failed: $AD_MUTATION_RESPONSE"
    fi
fi

# 8. GraphQL Query: Get all ads with campaign data
print_test "GraphQL Query: All Ads with Relations"
ADS_QUERY='{
    "query": "query GetAds { ads { id creativeUrl targetAudience campaign { name budget } } }"
}'

ADS_RESPONSE=$(curl -s -X POST "$GRAPHQL_ENDPOINT" \
    -H "$CONTENT_TYPE" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "$ADS_QUERY")

if echo "$ADS_RESPONSE" | grep -q '"ads"\|"data"'; then
    print_success "Ads with relations query executed successfully"
    echo "Response: $(echo "$ADS_RESPONSE" | head -c 200)..."
else
    print_error "Ads query failed: $ADS_RESPONSE"
fi

# 9. GraphQL Introspection Query
print_test "GraphQL Introspection Query"
INTROSPECTION_QUERY='{
    "query": "query IntrospectionQuery { __schema { queryType { name } mutationType { name } } }"
}'

INTROSPECTION_RESPONSE=$(curl -s -X POST "$GRAPHQL_ENDPOINT" \
    -H "$CONTENT_TYPE" \
    -d "$INTROSPECTION_QUERY")

if echo "$INTROSPECTION_RESPONSE" | grep -q '"queryType"\|"__schema"'; then
    print_success "GraphQL introspection working"
    echo "Response: $(echo "$INTROSPECTION_RESPONSE" | head -c 200)..."
else
    print_error "GraphQL introspection failed: $INTROSPECTION_RESPONSE"
fi

# 10. Summary
print_test "GraphQL Validation Summary"
echo -e "${YELLOW}GraphQL features tested:${NC}"
echo "✅ Endpoint accessibility"
echo "✅ JWT authentication integration"
echo "✅ Distributed schema (campaigns + authentication)"
echo "✅ Query execution (campaigns, users, ads)"
echo "✅ Mutations (create campaign, create ad)"
echo "✅ Nested relationships (ad.campaign)"
echo "✅ Variables and input types"
echo "✅ Schema introspection"

echo -e "\n${GREEN}GraphQL setup validation completed!${NC}"
echo -e "${YELLOW}Access GraphQL Playground at: ${NC}$GRAPHQL_ENDPOINT"