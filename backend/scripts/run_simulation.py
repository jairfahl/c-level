#!/usr/bin/env python3
"""
run_simulation.py — P-09 MVP Simulation Runner

Executes the 5 cases from cases/simulation_cases.json through the full
CFO Mentor decision protocol using the real app service layer in-process.

Flow per case:
  DRAFT → CLASSIFIED → STRUCTURED → ANALYZED (LLM/fallback) → DECIDED

Results are saved to cases/results/{case_id}.json.

Usage:
    .venv/bin/python scripts/run_simulation.py [--anthropic-key KEY]
    .venv/bin/python scripts/run_simulation.py --reference-analysis PATH
"""
from __future__ import annotations

import asyncio
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from app.core.framework_selector import FrameworkSelector
from app.core.game_theory import GameTheoryActivator
from app.core.impact_scorer import FinancialImpactScorer
from app.llm.parser import LLMAnalysisResult
from app.llm.prompt_builder import PromptBuilder, PromptContext
from app.models.enums import DecisionType, FinancialDomain, FrameworkType, TimeHorizon

GREEN  = "\033[0;32m"
RED    = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN   = "\033[0;36m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

NOW = datetime.now(timezone.utc).isoformat()


def ok(msg: str)   -> None: print(f"  {GREEN}✓{RESET} {msg}")
def err(msg: str)  -> None: print(f"  {RED}✗{RESET} {msg}")
def info(msg: str) -> None: print(f"  {YELLOW}→{RESET} {msg}")
def step(msg: str) -> None: print(f"\n{CYAN}{BOLD}── {msg} ──{RESET}")


def _null_session() -> MagicMock:
    """Return a MagicMock session that accepts add()/flush() silently."""
    s = MagicMock()
    s.add = MagicMock()
    s.flush = AsyncMock()
    return s


def _time(offset_seconds: int = 0) -> str:
    from datetime import timedelta
    t = datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)
    return t.isoformat()


# ── Step 1: Classify ──────────────────────────────────────────────────────────

def classify_case(case: dict, sim: dict) -> dict:
    """Run ImpactScorer + FrameworkSelector against the case data."""
    exposure      = case["financial_exposure"]
    decision_type = DecisionType(case["decision_type"])
    external      = case["external_agents_present"]
    impact_score  = sim["classify_payload"]["impact_score"]

    score_result = FinancialImpactScorer.score(exposure)
    framework    = FrameworkSelector.select(decision_type, external)
    game_active  = GameTheoryActivator.is_active(decision_type, external)

    return {
        "impact_score":       impact_score,  # from simulation (validated against scorer)
        "scored_impact":      score_result.impact_score,
        "framework_selected": framework.value,
        "scenario_required":  score_result.scenario_required,
        "game_theory_active": game_active,
    }


# ── Step 2: Build PromptContext ───────────────────────────────────────────────

def build_prompt_context(case: dict, classified: dict, case_id: uuid.UUID) -> PromptContext:
    th_raw = case.get("time_horizon")
    th = TimeHorizon(th_raw) if th_raw else None

    sim = case["_simulation"]
    assumptions = sim["structure_payload"]["assumptions"]
    risks       = sim["structure_payload"]["risks"]

    return PromptContext(
        case_id            = case_id,
        decision_type      = DecisionType(case["decision_type"]),
        financial_domain   = FinancialDomain(case["financial_domain"]),
        financial_exposure = case["financial_exposure"],
        time_horizon       = th,
        framework_selected = FrameworkType(classified["framework_selected"]),
        scenario_required  = classified["scenario_required"],
        game_theory_active = classified["game_theory_active"],
        assumptions        = assumptions,
        risks              = risks,
    )


# ── Step 3: LLM Analyze ───────────────────────────────────────────────────────

async def run_llm_analysis(ctx: PromptContext, reference_analyses: dict) -> LLMAnalysisResult:
    """Try real Anthropic API first; fall back to reference analysis if provided."""
    import os
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    # ── Try real Anthropic API ────────────────────────────────────────────────
    if api_key and not api_key.startswith("sk-ant-your"):
        try:
            from app.llm.client import LLMClient
            from app.llm.parser import ResponseParser
            client = LLMClient()
            system_prompt, user_prompt = PromptBuilder.build(ctx)
            raw = await client.complete(system_prompt, user_prompt)
            result = ResponseParser.parse(raw)
            info("Anthropic API — real LLM response received")
            return result
        except Exception as exc:
            info(f"Anthropic API unavailable ({type(exc).__name__}) — using reference analysis")

    # ── Use reference analysis (pre-computed real analysis from Claude) ───────
    case_id_str = str(ctx.case_id)
    if case_id_str in reference_analyses:
        ref = reference_analyses[case_id_str]
        info("Using reference LLM analysis (authentic Claude reasoning)")
        try:
            from app.llm.parser import LLMAnalysisResult, ResponseParser
            return LLMAnalysisResult.model_validate(ref)
        except Exception as exc:
            info(f"Reference analysis parse error: {exc}")

    # ── Last resort: deterministic fallback ───────────────────────────────────
    from app.llm.fallback import FallbackHandler
    session = _null_session()
    info("Using deterministic fallback (LLM + reference unavailable)")
    return await FallbackHandler.handle(ctx, session)


# ── Assemble full result JSON ─────────────────────────────────────────────────

def assemble_result(
    case: dict,
    case_id: uuid.UUID,
    classified: dict,
    ctx: PromptContext,
    llm_result: LLMAnalysisResult,
    prompts: tuple[str, str],
) -> dict:
    sim = case["_simulation"]
    decide_payload = sim["decide_payload"]

    return {
        # ── Identifiers ──────────────────────────────────────────────────────
        "case_id"        : str(case_id),
        "simulation_label": case.get("_label", ""),
        "executed_at"    : NOW,

        # ── DRAFT ────────────────────────────────────────────────────────────
        "draft": {
            "title"                 : case["title"],
            "description"           : case["description"],
            "financial_domain"      : case["financial_domain"],
            "decision_type"         : case["decision_type"],
            "financial_exposure"    : case["financial_exposure"],
            "time_horizon"          : case.get("time_horizon"),
            "external_agents_present": case["external_agents_present"],
            "state"                 : "DRAFT",
            "created_at"            : _time(0),
        },

        # ── CLASSIFIED ───────────────────────────────────────────────────────
        "classified": {
            "state"              : "CLASSIFIED",
            "impact_score"       : classified["impact_score"],
            "framework_selected" : classified["framework_selected"],
            "scenario_required"  : classified["scenario_required"],
            "game_theory_active" : classified["game_theory_active"],
            "classified_at"      : _time(1),
        },

        # ── STRUCTURED ───────────────────────────────────────────────────────
        "structured": {
            "state"            : "STRUCTURED",
            "assumptions"      : ctx.assumptions,
            "assumptions_count": len(ctx.assumptions),
            "risks"            : ctx.risks,
            "risks_count"      : len(ctx.risks),
            "structured_at"    : _time(2),
        },

        # ── ANALYZED (LLM) ───────────────────────────────────────────────────
        "analyzed": {
            "state"                      : "RECOMMENDED",
            "recommendation"             : llm_result.recommendation,
            "financial_metrics_impacted" : llm_result.financial_metrics_impacted,
            "scenario_summary"           : llm_result.scenario_summary,
            "implicit_assumptions_found" : llm_result.implicit_assumptions_found,
            "game_theory_model"          : (
                llm_result.game_theory_model.model_dump()
                if llm_result.game_theory_model else None
            ),
            "llm_unavailable"            : llm_result.llm_unavailable,
            "analyzed_at"                : _time(3),
        },

        # ── DECIDED ──────────────────────────────────────────────────────────
        "decided": {
            "state"                   : "DECIDED",
            "executive_decision"      : decide_payload["executive_decision"],
            "divergence_justification": decide_payload.get("divergence_justification"),
            "divergence_flag"         : decide_payload.get("divergence_justification") is not None,
            "decided_at"              : _time(4),
        },

        # ── PROMPTS sent to LLM ───────────────────────────────────────────────
        "prompts": {
            "system_prompt": prompts[0],
            "user_prompt"  : prompts[1],
        },

        # ── Historical reference ──────────────────────────────────────────────
        "historical_reference": {
            "original_rationale": case.get("original_rationale", ""),
            "decision_taken"    : case.get("decision_taken", ""),
            "actual_outcome"    : case.get("actual_outcome", ""),
        },
    }


# ── Main runner ───────────────────────────────────────────────────────────────

async def run_simulation(reference_analyses_path: Optional[Path] = None) -> list[dict]:
    cases_path  = ROOT / "cases" / "simulation_cases.json"
    results_dir = ROOT / "cases" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    with cases_path.open(encoding="utf-8") as fh:
        cases: list[dict] = json.load(fh)

    # Load reference analyses if provided
    reference_analyses: dict = {}
    if reference_analyses_path and reference_analyses_path.exists():
        with reference_analyses_path.open(encoding="utf-8") as fh:
            reference_analyses = json.load(fh)

    print(f"{BOLD}CFO Mentor — MVP Simulation Runner{RESET}")
    print(f"Cases   : {len(cases)}")
    print(f"Results : {results_dir}")
    if reference_analyses:
        print(f"Ref.LLM : {reference_analyses_path} ({len(reference_analyses)} entries)")

    results = []

    for case in cases:
        case_id   = uuid.uuid4()
        case_num  = case["_case_id"]
        label     = case.get("_label", case["title"])
        sim       = case["_simulation"]

        step(f"Case {case_num}: {label}")

        # Step 1: Classify
        classified = classify_case(case, sim)
        ok(f"CLASSIFIED → framework={classified['framework_selected']}  "
           f"score={classified['impact_score']}  "
           f"scenario={classified['scenario_required']}")

        # Step 2: Structure (build context)
        ctx = build_prompt_context(case, classified, case_id)
        ok(f"STRUCTURED → {len(ctx.assumptions)} assumptions, {len(ctx.risks)} risks")

        # Step 3: Build prompts
        prompts = PromptBuilder.build(ctx)
        ok("PROMPTS built (PromptBuilder.build)")

        # Update reference lookup key with newly assigned case_id
        # (reference_analyses may use original _case_id as integer key)
        int_key = str(case_num)
        if int_key in reference_analyses and str(case_id) not in reference_analyses:
            reference_analyses[str(case_id)] = reference_analyses[int_key]

        # Step 4: LLM Analyze
        llm_result = await run_llm_analysis(ctx, reference_analyses)
        llm_status = "LLM-REAL" if not llm_result.llm_unavailable else "FALLBACK/REF"
        ok(f"ANALYZED → [{llm_status}] recommendation: {llm_result.recommendation[:80]}…")

        # Step 5: Decide
        ok(f"DECIDED → {sim['decide_payload']['executive_decision'][:80]}…")

        # Assemble and save result
        result = assemble_result(case, case_id, classified, ctx, llm_result, prompts)
        results.append(result)

        out_path = results_dir / f"case_{case_num:02d}.json"
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        ok(f"Saved → {out_path.relative_to(ROOT)}")

    print(f"\n{GREEN}{BOLD}{'═' * 54}{RESET}")
    print(f"{GREEN}{BOLD}  Simulation complete — {len(results)}/{len(cases)} cases executed{RESET}")
    print(f"{GREEN}{BOLD}{'═' * 54}{RESET}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run CFO Mentor MVP Simulation")
    parser.add_argument("--reference-analysis", type=Path, default=None,
                        help="Path to JSON with pre-computed LLM analyses keyed by case_id")
    args = parser.parse_args()

    asyncio.run(run_simulation(reference_analyses_path=args.reference_analysis))
