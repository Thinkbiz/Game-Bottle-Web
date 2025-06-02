#!/bin/bash
# Test API endpoints script for Game-Bottle-Web

# Set the base URL
BASE_URL="http://localhost:8000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing Game-Bottle-Web API endpoints...${NC}"
echo "============================================"

# Function to test an endpoint
test_endpoint() {
  local endpoint=$1
  local description=$2
  local expected_status=$3
  
  echo -e "${YELLOW}Testing: ${description}${NC}"
  response=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}${endpoint})
  
  if [ "$response" -eq "$expected_status" ]; then
    echo -e "${GREEN}✓ Success! Endpoint ${endpoint} returned status ${response}${NC}"
  else
    echo -e "${RED}✗ Failed! Endpoint ${endpoint} returned status ${response}, expected ${expected_status}${NC}"
  fi
  echo
}

# Test the main endpoints
test_endpoint "/" "Main game page" 200
test_endpoint "/health" "Health check endpoint" 200
test_endpoint "/leaderboard" "Leaderboard page" 200
test_endpoint "/static/css/styles.css" "Static file (CSS)" 200
test_endpoint "/favicon.ico" "Favicon" 200

# Test a non-existent endpoint
test_endpoint "/does-not-exist" "Non-existent endpoint (should return 404)" 404

echo -e "${YELLOW}All tests completed!${NC}" 