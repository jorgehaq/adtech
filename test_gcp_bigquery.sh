#!/usr/bin/env bash

BASE_URL="https://adtech-backend-qacvmnzoda-uc.a.run.app"
echo "🌐 Testing BigQuery on GCP: $BASE_URL"

# 1. Login with existing user
echo "🔐 Logging in..."
TOKEN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login/" \
    -H "Content-Type: application/json" \
    -d '{"username":"bquser","password":"testpass123"}')

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('access', ''))" 2>/dev/null || echo "")

if [ -z "$ACCESS_TOKEN" ]; then
    echo "⚠️  Login failed, trying register with unique email..."
    TIMESTAMP=$(date +%s)
    TOKEN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register/" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"bq-test-${TIMESTAMP}@test.com\",\"username\":\"bquser${TIMESTAMP}\",\"password\":\"testpass123\",\"tenant_id\":1,\"role\":\"user\"}")
    
    ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('access', ''))" 2>/dev/null || echo "")
fi

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Failed to get JWT token"
    echo "Response: $TOKEN_RESPONSE"
    exit 1
fi

echo "✅ JWT token obtained"

# Continue with rest of tests...