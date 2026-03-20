#!/usr/bin/env bash
# =============================================================================
# smoke_test.sh — CFO Mentor API End-to-End Smoke Test
#
# Executes the complete decision protocol flow:
#   1. POST   /financial-decision-cases     → create (DRAFT)
#   2. PUT    /{id}/classify                → CLASSIFIED
#   3. PUT    /{id}/structure               → STRUCTURED
#   4. PUT    /{id}/analyze                 → RECOMMENDED (LLM called)
#   5. PUT    /{id}/decide                  → DECIDED
#   6. GET    /{id}/state-transitions       → transitions recorded
#   7. PUT    /{id}/review                  → CLOSED
#   8. GET    /{id}                         → full case verification
#
# Usage:
#   ./scripts/smoke_test.sh [BASE_URL] [TOKEN]
#
#   BASE_URL  defaults to http://localhost:8000
#   TOKEN     defaults to $CFO_API_TOKEN env var
#
# Prerequisites:
#   - API running (uvicorn app.main:app --reload)
#   - PostgreSQL and Redis running
#   - jq installed (brew install jq / apt install jq)
#   - CFO_API_TOKEN exported, OR pass token as second argument
# =============================================================================

set -euo pipefail

# ── Config ───────────────────────────────────────────────────────────────────
BASE_URL="${1:-http://localhost:8000}"
TOKEN="${2:-${CFO_API_TOKEN:-}}"
API="${BASE_URL}/v1/financial-decision-cases"

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ── Helpers ───────────────────────────────────────────────────────────────────
pass()  { echo -e "${GREEN}✓${RESET} $1"; }
fail()  { echo -e "${RED}✗${RESET} $1"; exit 1; }
step()  { echo -e "\n${CYAN}${BOLD}── $1 ──${RESET}"; }
info()  { echo -e "  ${YELLOW}→${RESET} $1"; }

assert_eq() {
  local label="$1" expected="$2" actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    pass "$label = $actual"
  else
    fail "$label: expected '$expected', got '$actual'"
  fi
}

assert_present() {
  local label="$1" value="$2"
  if [[ -n "$value" && "$value" != "null" ]]; then
    pass "$label is present"
  else
    fail "$label is missing or null"
  fi
}

assert_gte() {
  local label="$1" min="$2" actual="$3"
  if (( actual >= min )); then
    pass "$label = $actual (≥ $min)"
  else
    fail "$label: expected ≥ $min, got $actual"
  fi
}

# ── Pre-flight checks ─────────────────────────────────────────────────────────
echo -e "${BOLD}CFO Mentor API — Smoke Test${RESET}"
echo -e "Target: ${CYAN}${BASE_URL}${RESET}\n"

command -v jq &>/dev/null || fail "jq is required. Install with: brew install jq"
[[ -n "$TOKEN" ]]         || fail "TOKEN required. Set CFO_API_TOKEN or pass as second arg."

AUTH="Authorization: Bearer ${TOKEN}"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health")
[[ "$HTTP_CODE" == "200" ]] || fail "Server not responding at ${BASE_URL}/health (HTTP ${HTTP_CODE})"
pass "Server health check (HTTP 200)"

# ── Step 1: Create Case (DRAFT) ───────────────────────────────────────────────
step "Step 1 — POST /financial-decision-cases (DRAFT)"

RESP=$(curl -s -w "\n%{http_code}" -X POST "${API}" \
  -H "${AUTH}" -H "Content-Type: application/json" \
  -d '{
    "title": "Smoke Test: Reestruturação da dívida bancária",
    "description": "Caso de teste end-to-end do protocolo decisório completo via smoke test automatizado.",
    "financial_domain": "funding",
    "financial_exposure": 45000000.00,
    "decision_type": "debt_structuring",
    "external_agents_present": true
  }')

HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | head -1)
[[ "$HTTP_CODE" == "201" ]] || fail "Expected 201, got ${HTTP_CODE}: ${BODY}"

CASE_ID=$(echo "$BODY" | jq -r '.id')
assert_present "case_id"     "$CASE_ID"
assert_eq      "state" "DRAFT" "$(echo "$BODY" | jq -r '.state')"
info "Case ID: ${CASE_ID}"

# ── Step 2: Classify (DRAFT → CLASSIFIED) ────────────────────────────────────
step "Step 2 — PUT /{id}/classify (→ CLASSIFIED)"

RESP=$(curl -s -w "\n%{http_code}" -X PUT "${API}/${CASE_ID}/classify" \
  -H "${AUTH}" -H "Content-Type: application/json" \
  -d '{"impact_score": 4}')

HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | head -1)
[[ "$HTTP_CODE" == "200" ]] || fail "Expected 200, got ${HTTP_CODE}: ${BODY}"

assert_eq "state"             "CLASSIFIED"  "$(echo "$BODY" | jq -r '.state')"
assert_eq "framework_selected" "game_theory" "$(echo "$BODY" | jq -r '.framework_selected')"
assert_eq "scenario_required"  "true"        "$(echo "$BODY" | jq -r '.scenario_required')"

# ── Step 3: Structure (CLASSIFIED → STRUCTURED) ───────────────────────────────
step "Step 3 — PUT /{id}/structure (→ STRUCTURED)"

RESP=$(curl -s -w "\n%{http_code}" -X PUT "${API}/${CASE_ID}/structure" \
  -H "${AUTH}" -H "Content-Type: application/json" \
  -d '{
    "assumptions": [
      "Selic estável em 10.5% a.a. durante o período de reestruturação",
      "Receita líquida cresce +8% ao ano com base no pipeline comercial confirmado",
      "Crédito disponível no mercado bancário nacional para captação de recursos"
    ],
    "risks": [
      "Alta de juros acima de 2pp impacta custo do serviço da dívida significativamente",
      "Downgrade de rating dificulta refinanciamento a taxas competitivas no mercado",
      "Concentração de vencimentos em 12 meses pressiona liquidez operacional da empresa"
    ]
  }')

HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | head -1)
[[ "$HTTP_CODE" == "200" ]] || fail "Expected 200, got ${HTTP_CODE}: ${BODY}"

assert_eq "state"            "STRUCTURED" "$(echo "$BODY" | jq -r '.state')"
assert_eq "assumptions_count" "3"          "$(echo "$BODY" | jq -r '.assumptions_count')"
assert_eq "risks_count"       "3"          "$(echo "$BODY" | jq -r '.risks_count')"

# ── Step 4: Analyze (STRUCTURED → RECOMMENDED) ────────────────────────────────
step "Step 4 — PUT /{id}/analyze (→ RECOMMENDED)"
info "Calling Anthropic Claude — this may take a few seconds..."

RESP=$(curl -s -w "\n%{http_code}" --max-time 60 -X PUT "${API}/${CASE_ID}/analyze" \
  -H "${AUTH}")

HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | head -1)
[[ "$HTTP_CODE" == "200" ]] || fail "Expected 200, got ${HTTP_CODE}: ${BODY}"

assert_eq      "state"        "RECOMMENDED" "$(echo "$BODY" | jq -r '.state')"
assert_present "recommendation"             "$(echo "$BODY" | jq -r '.recommendation')"
assert_gte     "financial_metrics_impacted" 1 "$(echo "$BODY" | jq '.financial_metrics_impacted | length')"

LLM_FLAG=$(echo "$BODY" | jq -r '.llm_unavailable')
if [[ "$LLM_FLAG" == "true" ]]; then
  echo -e "  ${YELLOW}⚠${RESET}  LLM unavailable — fallback used (deterministic recommendation)"
else
  pass "LLM called successfully (llm_unavailable=false)"
fi

RECOMMENDATION=$(echo "$BODY" | jq -r '.recommendation')
info "Recommendation (first 120 chars): ${RECOMMENDATION:0:120}"

# ── Step 5: Decide (RECOMMENDED → DECIDED) ───────────────────────────────────
step "Step 5 — PUT /{id}/decide (→ DECIDED)"

RESP=$(curl -s -w "\n%{http_code}" -X PUT "${API}/${CASE_ID}/decide" \
  -H "${AUTH}" -H "Content-Type: application/json" \
  -d '{
    "executive_decision": "Aprovamos a reestruturação completa conforme recomendado pelo Mentor CFO. Implementação em 3 tranches anuais conforme proposto."
  }')

HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | head -1)
[[ "$HTTP_CODE" == "200" ]] || fail "Expected 200, got ${HTTP_CODE}: ${BODY}"

assert_eq "state"          "DECIDED" "$(echo "$BODY" | jq -r '.state')"
assert_eq "divergence_flag" "false"   "$(echo "$BODY" | jq -r '.divergence_flag')"

# ── Step 6: Audit Trail ────────────────────────────────────────────────────────
step "Step 6 — GET /{id}/state-transitions (audit trail)"

RESP=$(curl -s -w "\n%{http_code}" "${API}/${CASE_ID}/state-transitions" -H "${AUTH}")

HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | head -1)
[[ "$HTTP_CODE" == "200" ]] || fail "Expected 200, got ${HTTP_CODE}: ${BODY}"

TRANSITION_COUNT=$(echo "$BODY" | jq '.transitions | length')
LAST_STATE=$(echo "$BODY" | jq -r '.transitions | last | .to_state')

assert_gte "transitions recorded" 5 "$TRANSITION_COUNT"
assert_eq  "last to_state" "DECIDED" "$LAST_STATE"

info "Transition history:"
echo "$BODY" | jq -r '.transitions[] | "    \(.from_state // "—") → \(.to_state)  (\(.transitioned_at[:19]))"'

# ── Step 7: Review (DECIDED → UNDER_REVIEW → CLOSED) ─────────────────────────
step "Step 7 — PUT /{id}/review (→ CLOSED)"

RESP=$(curl -s -w "\n%{http_code}" -X PUT "${API}/${CASE_ID}/review" \
  -H "${AUTH}" -H "Content-Type: application/json" \
  -d '{
    "outcome_summary": "Reestruturação executada com sucesso. Custo da dívida reduziu 15% conforme projetado pelo Mentor CFO.",
    "forecast_accuracy_score": 8,
    "risk_realization_rate": 20.0,
    "capital_allocation_efficiency_score": 90.0,
    "divergence_outcome_flag": false
  }')

HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | head -1)
[[ "$HTTP_CODE" == "200" ]] || fail "Expected 200, got ${HTTP_CODE}: ${BODY}"

assert_eq "state" "CLOSED" "$(echo "$BODY" | jq -r '.state')"

# ── Step 8: Full Case Read ────────────────────────────────────────────────────
step "Step 8 — GET /{id} (final state verification)"

RESP=$(curl -s -w "\n%{http_code}" "${API}/${CASE_ID}" -H "${AUTH}")

HTTP_CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | head -1)
[[ "$HTTP_CODE" == "200" ]] || fail "Expected 200, got ${HTTP_CODE}: ${BODY}"

assert_eq      "state"             "CLOSED" "$(echo "$BODY" | jq -r '.state')"
assert_present "framework_selected"         "$(echo "$BODY" | jq -r '.framework_selected')"
assert_present "recommendation"             "$(echo "$BODY" | jq -r '.recommendation')"
assert_present "executive_decision"         "$(echo "$BODY" | jq -r '.executive_decision')"

# ── Summary ───────────────────────────────────────────────────────────────────
echo -e "\n${GREEN}${BOLD}══════════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}  Smoke test PASSED — complete protocol flow verified  ${RESET}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════════════${RESET}"
echo -e "  Case ID : ${CYAN}${CASE_ID}${RESET}"
echo -e "  Flow    : DRAFT → CLASSIFIED → STRUCTURED → RECOMMENDED → DECIDED → CLOSED"
echo -e "  View    : ${BASE_URL}/v1/financial-decision-cases/${CASE_ID}"
