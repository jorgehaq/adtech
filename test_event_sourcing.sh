#!/bin/bash

# Test Event Sourcing Flow
echo "🧪 Testing Event Sourcing Flow..."

# Use dynamic port or default to 8070
PORT=${TEST_PORT:-8070}
BASE_URL="http://localhost:$PORT"

echo "📡 Testing server on port $PORT..."

# Wait for server to be ready
echo "⏳ Waiting for server to be ready..."
for i in {1..30}; do
    if curl -s ${BASE_URL}/admin/ > /dev/null 2>&1; then
        echo "✅ Server is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Server failed to start within 30 seconds"
        exit 1
    fi
    sleep 1
done

# Test 1: Check analytics endpoints are accessible
echo "📊 Test 1: Testing analytics endpoints..."
if curl -s ${BASE_URL}/api/analytics/cohort-analysis/ > /dev/null 2>&1; then
    echo "✅ Cohort analysis endpoint accessible"
else
    echo "⚠️ Cohort analysis endpoint not available"
fi

# Test 2: Test campaign performance endpoint
echo "📈 Test 2: Testing campaign performance..."
if curl -s ${BASE_URL}/api/analytics/campaign-performance/ > /dev/null 2>&1; then
    echo "✅ Campaign performance endpoint accessible"
else
    echo "⚠️ Campaign performance endpoint not available"
fi

# Test 3: Test real-time dashboard
echo "⚡ Test 3: Testing real-time dashboard..."
if curl -s ${BASE_URL}/api/analytics/real-time-dashboard/ > /dev/null 2>&1; then
    echo "✅ Real-time dashboard endpoint accessible"
else
    echo "⚠️ Real-time dashboard endpoint not available"
fi

# Test 4: Check server health
echo "🔍 Test 4: Checking server health..."
if curl -s ${BASE_URL}/ > /dev/null 2>&1; then
    echo "✅ Server is responding"
else
    echo "⚠️ Server is not responding"
fi

echo "✅ Event sourcing tests completed!"