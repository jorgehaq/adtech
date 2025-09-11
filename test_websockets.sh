#!/usr/bin/env bash

BASE_URL="http://localhost:${TEST_PORT:-8070}"
echo "🔌 Testing WebSocket Integration..."

# Get JWT token first
TOKEN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register/" \
    -H "Content-Type: application/json" \
    -d '{"email":"ws-test@test.com","username":"wsuser","password":"testpass123","tenant_id":1,"role":"user"}')

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('access', ''))" 2>/dev/null || echo "")

if [ -n "$ACCESS_TOKEN" ]; then
    echo "✅ JWT token obtained for WebSocket auth"
    
    # Test WebSocket endpoint
    WS_TEST=$(curl -s "$BASE_URL/api/v1/realtime/test-websocket/" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if echo "$WS_TEST" | grep -q "websocket_url"; then
        echo "✅ WebSocket test endpoint working"
        echo "$WS_TEST" | python3 -m json.tool
    else
        echo "❌ WebSocket test endpoint failed"
    fi
else
    echo "❌ Failed to get JWT token"
fi

echo "✅ WebSocket integration tests completed"