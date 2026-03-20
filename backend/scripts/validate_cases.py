#!/usr/bin/env python3
"""
validate_cases.py — P-08 Validation: Simulation Cases Schema & Engine Check

Validates every payload in cases/simulation_cases.json against:
  1. Pydantic schemas (FinancialDecisionCaseCreate, ClassifyRequest,
     StructureRequest, DecideRequest, ReviewRequest)
  2. Deterministic engine (FinancialImpactScorer, FrameworkSelector)
     — cross-checks expected_impact_score, expected_framework, expected_scenario_required

Usage:
    python scripts/validate_cases.py
    # or from backend root:
    .venv/bin/python scripts/validate_cases.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ── Bootstrap Python path so app imports work without installing the package ──
ROOT = Path(__file__).parent.parent  # backend/
sys.path.insert(0, str(ROOT))

from pydantic import ValidationError  # noqa: E402

from app.core.framework_selector import FrameworkSelector  # noqa: E402
from app.core.impact_scorer import FinancialImpactScorer  # noqa: E402
from app.schemas import (  # noqa: E402
    ClassifyRequest,
    DecideRequest,
    DecisionType,
    FinancialDecisionCaseCreate,
    FinancialDomain,
    ReviewRequest,
    StructureRequest,
    TimeHorizon,
)

# ── ANSI colours ──────────────────────────────────────────────────────────────
GREEN  = "\033[0;32m"
RED    = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN   = "\033[0;36m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def ok(msg: str)   -> None: print(f"  {GREEN}✓{RESET} {msg}")
def err(msg: str)  -> None: print(f"  {RED}✗{RESET} {msg}")
def warn(msg: str) -> None: print(f"  {YELLOW}⚠{RESET} {msg}")
def step(msg: str) -> None: print(f"\n{CYAN}{BOLD}── {msg} ──{RESET}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def validate_schema(label: str, schema_cls, payload: dict) -> bool:
    """Validate *payload* against *schema_cls*; return True on success."""
    try:
        schema_cls.model_validate(payload)
        ok(f"{label} schema valid")
        return True
    except ValidationError as exc:
        err(f"{label} schema FAILED")
        for e in exc.errors():
            print(f"      loc={e['loc']}  msg={e['msg']}")
        return False


def validate_engine(case: dict, sim: dict) -> bool:
    """Run impact scorer + framework selector and compare to expected values."""
    exposure = case["financial_exposure"]
    decision_type_str = case["decision_type"]
    external = case["external_agents_present"]

    # Impact scorer
    result = FinancialImpactScorer.score(exposure)
    expected_score = sim["expected_impact_score"]
    expected_scenario = sim["expected_scenario_required"]

    passed = True

    if result.impact_score == expected_score:
        ok(f"impact_score = {result.impact_score} (expected {expected_score})")
    else:
        err(f"impact_score = {result.impact_score}, expected {expected_score}")
        passed = False

    if result.scenario_required == expected_scenario:
        ok(f"scenario_required = {result.scenario_required} (expected {expected_scenario})")
    else:
        err(f"scenario_required = {result.scenario_required}, expected {expected_scenario}")
        passed = False

    # Framework selector
    try:
        dt = DecisionType(decision_type_str)
        framework = FrameworkSelector.select(dt, external)
        expected_fw = sim["expected_framework"]
        if framework.value == expected_fw:
            ok(f"framework_selected = {framework.value} (expected {expected_fw})")
        else:
            err(f"framework_selected = {framework.value}, expected {expected_fw}")
            passed = False
    except Exception as exc:
        err(f"FrameworkSelector raised: {exc}")
        passed = False

    return passed


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    cases_path = ROOT / "cases" / "simulation_cases.json"
    if not cases_path.exists():
        print(f"{RED}cases/simulation_cases.json not found at {cases_path}{RESET}")
        return 1

    with cases_path.open(encoding="utf-8") as fh:
        cases: list[dict] = json.load(fh)

    print(f"{BOLD}CFO Mentor — Simulation Cases Validation{RESET}")
    print(f"File : {CYAN}{cases_path}{RESET}")
    print(f"Cases: {len(cases)}\n")

    total_checks = 0
    failed_checks = 0

    for case in cases:
        case_id   = case["_case_id"]
        label     = case.get("_label", case["title"][:50])
        sim       = case.get("_simulation", {})

        step(f"Case {case_id}: {label}")

        # Build CREATE payload (strip private _-prefixed keys + _simulation)
        create_payload = {
            k: v for k, v in case.items()
            if not k.startswith("_") and k not in {
                "original_rationale", "decision_taken", "actual_outcome"
            }
        }

        checks: list[tuple[str, type, dict]] = [
            ("CREATE",   FinancialDecisionCaseCreate, create_payload),
            ("CLASSIFY", ClassifyRequest,              sim.get("classify_payload", {})),
            ("STRUCTURE",StructureRequest,             sim.get("structure_payload", {})),
            ("DECIDE",   DecideRequest,                sim.get("decide_payload", {})),
            ("REVIEW",   ReviewRequest,                sim.get("review_payload", {})),
        ]

        for check_label, schema_cls, payload in checks:
            total_checks += 1
            if not validate_schema(check_label, schema_cls, payload):
                failed_checks += 1

        # Engine check
        total_checks += 3   # score, scenario_required, framework
        engine_passed = validate_engine(case, sim)
        if not engine_passed:
            failed_checks += 1  # approximate — individual failures already counted above

    # ── Summary ───────────────────────────────────────────────────────────────
    passed = total_checks - failed_checks
    colour = GREEN if failed_checks == 0 else RED

    print(f"\n{colour}{BOLD}{'═' * 54}{RESET}")
    if failed_checks == 0:
        print(f"{GREEN}{BOLD}  All validations PASSED ({passed}/{total_checks} checks){RESET}")
    else:
        print(f"{RED}{BOLD}  FAILED: {failed_checks} check(s) out of {total_checks}{RESET}")
    print(f"{colour}{BOLD}{'═' * 54}{RESET}")

    # Constraint summary
    print(f"\n{BOLD}Constraint Verification:{RESET}")
    scores_gte4 = sum(
        1 for c in cases
        if c.get("_simulation", {}).get("expected_impact_score", 0) >= 4
    )
    ext_true = sum(1 for c in cases if c.get("external_agents_present") is True)
    constraint_ok = scores_gte4 >= 2 and ext_true >= 1

    score_sym = GREEN + "✓" + RESET if scores_gte4 >= 2 else RED + "✗" + RESET
    ext_sym   = GREEN + "✓" + RESET if ext_true >= 1   else RED + "✗" + RESET

    print(f"  {score_sym} Cases with impact_score ≥ 4 : {scores_gte4} (req ≥ 2)")
    print(f"  {ext_sym} Cases with external_agents  : {ext_true} (req ≥ 1)")

    if not constraint_ok:
        print(f"  {RED}✗{RESET} P-08 constraints NOT satisfied")

    return 0 if (failed_checks == 0 and constraint_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
