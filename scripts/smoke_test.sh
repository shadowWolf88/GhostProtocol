#!/usr/bin/env bash
# Ghost Protocol — End-to-End Smoke Test
# Usage: ./scripts/smoke_test.sh [BASE_URL]
# Default: http://localhost:8000

set -euo pipefail

BASE="${1:-http://localhost:8000}"
API="$BASE/api/v1"
HANDLE="smoketest_$(date +%s)"
EMAIL="${HANDLE}@test.local"
PASSWORD="smoketest_password"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

pass() { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; exit 1; }
info() { echo -e "  ${CYAN}→${NC} $1"; }
header() { echo -e "\n${YELLOW}[ $1 ]${NC}"; }

check_jq() {
  if ! command -v jq &>/dev/null; then
    echo -e "${RED}Error: jq is required. Install with: apt install jq${NC}"
    exit 1
  fi
}

header "GHOST PROTOCOL SMOKE TEST"
info "Base URL: $BASE"
info "Handle: $HANDLE"

check_jq

# ── 1. Health check ───────────────────────────────────────────────────────────
header "1. HEALTH CHECK"
HEALTH=$(curl -sf "$BASE/health" || echo '{}')
echo "$HEALTH" | jq -e '.status == "ok"' > /dev/null && pass "Health endpoint OK" || fail "Health endpoint failed: $HEALTH"

# ── 2. Register ───────────────────────────────────────────────────────────────
header "2. REGISTRATION"
REG=$(curl -sf -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"handle\":\"$HANDLE\",\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")
TOKEN=$(echo "$REG" | jq -r '.access_token')
PLAYER_ID=$(echo "$REG" | jq -r '.player_id')
[ "$TOKEN" != "null" ] && [ -n "$TOKEN" ] && pass "Registration successful — player_id: $PLAYER_ID" || fail "Registration failed: $REG"

AUTH_HEADER="Authorization: Bearer $TOKEN"

# ── 3. Login ──────────────────────────────────────────────────────────────────
header "3. LOGIN"
LOGIN=$(curl -sf -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"handle\":\"$HANDLE\",\"password\":\"$PASSWORD\"}")
LOGIN_TOKEN=$(echo "$LOGIN" | jq -r '.access_token')
[ "$LOGIN_TOKEN" != "null" ] && pass "Login successful" || fail "Login failed: $LOGIN"

# ── 4. Player profile ─────────────────────────────────────────────────────────
header "4. PLAYER PROFILE"
PROFILE=$(curl -sf "$API/players/me" -H "$AUTH_HEADER")
CRYPTO=$(echo "$PROFILE" | jq -r '.stats.crypto')
ENERGY=$(echo "$PROFILE" | jq -r '.stats.energy')
DEVICE_COUNT=$(echo "$PROFILE" | jq '.devices | length')
[ "$CRYPTO" = "500" ] && pass "Starting crypto: 500₡" || fail "Expected 500 crypto, got $CRYPTO"
[ "$ENERGY" = "100" ] && pass "Starting energy: 100" || fail "Expected 100 energy, got $ENERGY"
[ "$DEVICE_COUNT" -ge 1 ] && pass "Starter device created" || fail "No starter device found"

# ── 5. World nodes ────────────────────────────────────────────────────────────
header "5. WORLD NODES"
NODES=$(curl -sf "$API/world/nodes" -H "$AUTH_HEADER")
NODE_COUNT=$(echo "$NODES" | jq 'length')
[ "$NODE_COUNT" -gt 0 ] && pass "World nodes seeded: $NODE_COUNT nodes" || fail "No world nodes found"
FIRST_NODE_KEY=$(echo "$NODES" | jq -r '.[0].node_key')
info "First node: $FIRST_NODE_KEY"

# ── 6. Node intel ─────────────────────────────────────────────────────────────
header "6. NODE INTELLIGENCE"
INTEL=$(curl -sf "$API/world/nodes/$FIRST_NODE_KEY/intel" -H "$AUTH_HEADER")
SUCCESS_CHANCE=$(echo "$INTEL" | jq -r '.success_chance')
echo "$INTEL" | jq -e '.success_chance > 0' > /dev/null && pass "Node intel: success_chance=$SUCCESS_CHANCE" || fail "Node intel failed: $INTEL"

# ── 7. Skills ─────────────────────────────────────────────────────────────────
header "7. SKILL TREES"
SKILLS=$(curl -sf "$API/skills/" -H "$AUTH_HEADER")
TREE_COUNT=$(echo "$SKILLS" | jq '.trees | length')
[ "$TREE_COUNT" -eq 6 ] && pass "All 6 skill trees present" || fail "Expected 6 trees, got $TREE_COUNT"

# ── 8. Heat status ────────────────────────────────────────────────────────────
header "8. HEAT STATUS"
HEAT=$(curl -sf "$API/heat/status" -H "$AUTH_HEADER")
TIER=$(echo "$HEAT" | jq -r '.threat_tier')
TOTAL=$(echo "$HEAT" | jq -r '.total_heat')
[ "$TIER" = "1" ] && pass "New player heat tier: 1 (OFF THE RADAR)" || fail "Expected tier 1, got $TIER"
pass "Total heat: $TOTAL"

# ── 9. Operation (start → advance × 4 → complete) ─────────────────────────────
header "9. FULL OPERATION CYCLE"
DEVICE_ID=$(echo "$PROFILE" | jq -r '.devices[0].id')
info "Using device: $DEVICE_ID on node: $FIRST_NODE_KEY"

OP_CREATE=$(curl -sf -X POST "$API/operations/" -H "$AUTH_HEADER" -H "Content-Type: application/json" \
  -d "{\"node_key\":\"$FIRST_NODE_KEY\",\"device_id\":\"$DEVICE_ID\",\"approach\":\"technical\"}")
OP_ID=$(echo "$OP_CREATE" | jq -r '.operation_id')
[ "$OP_ID" != "null" ] && [ -n "$OP_ID" ] && pass "Operation created: $OP_ID" || fail "Operation creation failed: $OP_CREATE"

# Advance through all 4 phases
for PHASE in recon exploit persist monetize; do
  ADVANCE=$(curl -sf -X POST "$API/operations/$OP_ID/advance" -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d '{"phase_action":"execute","parameters":{}}')
  PHASE_NAME=$(echo "$ADVANCE" | jq -r '.phase')
  SUCCESS=$(echo "$ADVANCE" | jq -r '.success')
  pass "Phase $PHASE_NAME: success=$SUCCESS"
  # Check if operation concluded
  NEXT=$(echo "$ADVANCE" | jq -r '.next_phase')
  [ "$NEXT" = "null" ] && break
done

# ── 10. Operation result ──────────────────────────────────────────────────────
header "10. OPERATION RESULT"
RESULT=$(curl -sf "$API/operations/$OP_ID/result" -H "$AUTH_HEADER")
STATUS=$(echo "$RESULT" | jq -r '.status')
CRYPTO_EARNED=$(echo "$RESULT" | jq -r '.crypto_earned')
[ "$STATUS" != "null" ] && pass "Operation result: $STATUS — +${CRYPTO_EARNED}₡" || fail "Result unavailable: $RESULT"

# ── 11. Wallet ────────────────────────────────────────────────────────────────
header "11. ECONOMY"
WALLET=$(curl -sf "$API/economy/wallet" -H "$AUTH_HEADER")
FINAL_CRYPTO=$(echo "$WALLET" | jq -r '.crypto')
pass "Wallet after operation: ${FINAL_CRYPTO}₡"

MARKET=$(curl -sf "$API/economy/market" -H "$AUTH_HEADER")
MARKET_COUNT=$(echo "$MARKET" | jq 'length')
[ "$MARKET_COUNT" -gt 0 ] && pass "Market listings: $MARKET_COUNT items" || fail "No market listings found"

# ── 12. Psych state ───────────────────────────────────────────────────────────
header "12. PSYCHOLOGICAL STATE"
PSYCH=$(curl -sf "$API/psych/state" -H "$AUTH_HEADER")
STRESS=$(echo "$PSYCH" | jq -r '.stress')
FOCUS=$(echo "$PSYCH" | jq -r '.focus')
pass "Post-op psych — stress: $STRESS, focus: $FOCUS"

# ── 13. Trace graph ───────────────────────────────────────────────────────────
header "13. TRACE GRAPH"
TRACE=$(curl -sf "$API/trace/graph" -H "$AUTH_HEADER")
TRACE_NODES=$(echo "$TRACE" | jq '.nodes | length')
pass "Trace graph: $TRACE_NODES nodes"

# ── 14. Onboarding ────────────────────────────────────────────────────────────
header "14. ONBOARDING"
ONBOARDING=$(curl -sf "$API/onboarding/state" -H "$AUTH_HEADER")
ONBOARD_STEP=$(echo "$ONBOARDING" | jq -r '.current_step')
pass "Onboarding step: $ONBOARD_STEP"

# ── 15. Duplicate registration (should fail 409) ──────────────────────────────
header "15. DUPLICATE HANDLE REJECTION"
DUP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"handle\":\"$HANDLE\",\"email\":\"dup@test.local\",\"password\":\"password123\"}")
[ "$DUP_STATUS" = "409" ] && pass "Duplicate handle rejected (409)" || fail "Expected 409, got $DUP_STATUS"

# ── Summary ───────────────────────────────────────────────────────────────────
echo -e "\n${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  ALL SMOKE TESTS PASSED${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "  Handle: $HANDLE"
echo -e "  Player ID: $PLAYER_ID"
echo -e "  Final crypto: ${FINAL_CRYPTO}₡"
echo ""
