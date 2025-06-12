#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
        exit 1
    fi
}

# Function to test endpoint
test_endpoint() {
    local url=$1
    local expected_status=$2
    local response=$(curl -s -o /dev/null -w "%{http_code}" $url)
    if [ "$response" -eq "$expected_status" ]; then
        print_status 0 "Endpoint $url returned $response"
    else
        print_status 1 "Endpoint $url returned $response (expected $expected_status)"
    fi
}

echo "Starting Docker Compose OAuth integration tests..."

# Check if Docker Compose is running
if ! docker-compose ps | grep -q "Up"; then
    echo "Starting Docker Compose services..."
    docker-compose up -d
    sleep 10  # Wait for services to start
fi

# Test basic endpoints
echo -e "\nTesting basic endpoints..."
test_endpoint "http://localhost:3000" 200
test_endpoint "http://localhost:3000/api/health" 200

# Test OAuth endpoints
echo -e "\nTesting OAuth endpoints..."
test_endpoint "http://localhost:3000/oauth2/sign_in" 302
test_endpoint "http://localhost:3000/oauth2/callback" 302

# Test protected endpoints
echo -e "\nTesting protected endpoints..."
test_endpoint "http://localhost:3000/admin" 302
test_endpoint "http://localhost:3000/api/protected" 302

# Test CORS
echo -e "\nTesting CORS configuration..."
response=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Origin: http://disallowed-origin.com" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Authorization" \
    -X OPTIONS http://localhost:3000/api/health)
if [ "$response" -eq "403" ]; then
    print_status 0 "CORS blocked disallowed origin"
else
    print_status 1 "CORS allowed disallowed origin"
fi

# Test service health
echo -e "\nTesting service health..."
test_endpoint "http://localhost:3000/oauth2/health" 200
test_endpoint "http://localhost:8000/health" 200

# Test service logs
echo -e "\nChecking service logs..."
for service in backend frontend nginx oauth2-proxy; do
    if docker-compose logs $service | grep -q "error"; then
        print_status 1 "Found errors in $service logs"
    else
        print_status 0 "No errors in $service logs"
    fi
done

echo -e "\nAll tests completed!"
