import enum


class FinancialDomain(str, enum.Enum):
    planning = "planning"
    reporting = "reporting"
    treasury = "treasury"
    funding = "funding"
    risk = "risk"


class DecisionState(str, enum.Enum):
    DRAFT = "DRAFT"
    CLASSIFIED = "CLASSIFIED"
    STRUCTURED = "STRUCTURED"
    ANALYZED = "ANALYZED"
    RECOMMENDED = "RECOMMENDED"
    DECIDED = "DECIDED"
    UNDER_REVIEW = "UNDER_REVIEW"
    CLOSED = "CLOSED"


class DecisionType(str, enum.Enum):
    budget_adjustment = "budget_adjustment"
    forecast_revision = "forecast_revision"
    capital_allocation = "capital_allocation"
    debt_structuring = "debt_structuring"
    liquidity_management = "liquidity_management"
    risk_hedging = "risk_hedging"
    cost_reduction = "cost_reduction"
    investment_evaluation = "investment_evaluation"


class TimeHorizon(str, enum.Enum):
    short = "short"
    medium = "medium"
    long = "long"


class FrameworkType(str, enum.Enum):
    pdca = "pdca"
    scenario_analysis = "scenario_analysis"
    game_theory = "game_theory"
    trade_off = "trade_off"
    risk_matrix = "risk_matrix"
    capital_allocation = "capital_allocation"
