#!/bin/bash

# Test Event Sourcing Flow
echo "🧪 Testing Event Sourcing Flow..."

PORT=${TEST_PORT:-8070}
BASE_URL="http://localhost:$PORT"

# Wait for server
for i in {1..30}; do
    if curl -s ${BASE_URL}/admin/ > /dev/null 2>&1; then
        echo "✅ Server ready!"
        break
    fi
    sleep 1
done

# Get JWT token with unique email
TIMESTAMP=$(date +%s%3N)
echo "🔑 Getting JWT token..."
TOKEN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/register/" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"event-${TIMESTAMP}@test.com\",\"username\":\"eventuser${TIMESTAMP}\",\"password\":\"testpass123\",\"tenant_id\":1,\"role\":\"user\"}")

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('access', ''))" 2>/dev/null || echo "")

if [ -n "$ACCESS_TOKEN" ]; then
    echo "✅ JWT token obtained"
    
    echo "🔄 Testing event replay..."
    REPLAY_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $ACCESS_TOKEN" ${BASE_URL}/api/v1/events/rebuild-metrics/1/)
    if echo "$REPLAY_RESPONSE" | grep -q "events_replayed"; then
        echo "✅ Event replay working"
    else
        echo "⚠️ Event replay response: $REPLAY_RESPONSE"
    fi
else
    echo "❌ Failed to get JWT token: $TOKEN_RESPONSE"
fi

echo "✅ Event sourcing tests completed!"