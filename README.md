# Mentor C-Level – CFO Edition

A production-ready MVP cognitive governance engine that structures executive financial decisions. This is **not a chatbot** — it is a hybrid deterministic rule engine + LLM analytical layer that enforces a Decision Protocol over financial decision cases.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                      │
│   Dashboard │ Case Wizard │ Pyramid Recommendation │ Review │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API (JWT)
┌─────────────────────────▼───────────────────────────────────┐
│                    Backend (NestJS)                          │
│  State Machine │ Protocol Engine │ LLM Layer │ Audit Trail  │
└─────────────────────────┬───────────────────────────────────┘
                          │ Prisma ORM
┌─────────────────────────▼───────────────────────────────────┐
│                  PostgreSQL 15+                              │
│  financial_decision_cases │ decisions │ audit_logs │ ...    │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology |
|---|---|
| Backend | Node.js + NestJS |
| Database | PostgreSQL 15+ |
| ORM | Prisma |
| LLM | OpenAI SDK (gpt-4o, with mock fallback) |
| Auth | JWT (passport-jwt) |
| Frontend | Next.js 14 + React 18 + TypeScript |
| Styling | TailwindCSS |
| Infrastructure | Docker + Docker Compose |

---

## Decision State Machine

```
DRAFT → CLASSIFIED → STRUCTURED → ANALYZED → RECOMMENDED → DECIDED → UNDER_REVIEW → CLOSED
```

### Protocol Rules

| Transition | Pre-condition |
|---|---|
| → STRUCTURED | Minimum **3 assumptions** must be registered |
| → ANALYZED | Minimum **3 risks** must be documented |
| → RECOMMENDED | If `impactScore >= 4`: scenario analysis required AND ≥1 metric impacted |
| → DECIDED | Recommendation must exist; divergence justification required if executive decision ≠ recommended option |
| Invalid transitions | Return **HTTP 409 Conflict** |
| Protocol violations | Return **HTTP 422 Unprocessable Entity** |

### Game Theory Trigger

Automatically triggered when `externalAgentsPresent = true` AND `impactScore >= 4`.

Generates: Players, Strategy Space, Payoff Matrix, Nash Equilibrium estimation, Strategic Risk Exposure.

---

## Quick Start (Docker)

### Prerequisites

- Docker 24+
- Docker Compose V2

### 1. Clone and configure

```bash
git clone https://github.com/jairfahl/c-level.git
cd c-level
cp .env.example .env
```

Edit `.env` and set:
```env
JWT_SECRET=your-secure-random-secret-min-32-chars
OPENAI_API_KEY=sk-...   # Optional – app works without it using structured mock data
```

### 2. Start the application

```bash
docker compose up -d
```

### 3. Run migrations and seed

```bash
docker compose exec backend npx prisma migrate deploy
docker compose exec backend npx ts-node prisma/seed.ts
```

### 4. Access

- **Frontend**: http://localhost:3000
- **API**: http://localhost:3001
- **Health check**: http://localhost:3001/health

**Default credentials**: `admin` / `admin123`

---

## Local Development (without Docker)

### Backend

```bash
cd backend
cp .env.example .env
# Edit .env with DATABASE_URL and JWT_SECRET

npm install
npx prisma generate
npx prisma migrate dev --name init
npx ts-node prisma/seed.ts
npm run start:dev
```

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:3001

npm install
npm run dev
```

---

## Database Schema

Tables: `financial_decision_cases`, `financial_assumptions`, `financial_risks`, `financial_metrics_impacted`, `decisions`, `reviews`, `state_transitions`, `audit_logs`

ENUMs:
- `FinancialDomain`: CAPEX, OPEX, REVENUE, TREASURY, RISK_MANAGEMENT, COMPLIANCE, STRATEGY, M_AND_A
- `DecisionState`: DRAFT, CLASSIFIED, STRUCTURED, ANALYZED, RECOMMENDED, DECIDED, UNDER_REVIEW, CLOSED
- `DecisionType`: INVESTMENT, DIVESTMENT, FINANCING, OPERATIONAL_CHANGE, RISK_MITIGATION, STRATEGIC_PARTNERSHIP, ACQUISITION, RESTRUCTURING

---

## API Reference

All endpoints require JWT Bearer token (except `/auth/login` and `/health`).

```
POST /auth/login                                  { username, password }
POST /financial-decision-cases                    Create case (DRAFT)
GET  /financial-decision-cases                    List all
GET  /financial-decision-cases/:id                Get with relations
PUT  /financial-decision-cases/:id/classify       DRAFT → CLASSIFIED
PUT  /financial-decision-cases/:id/structure      CLASSIFIED → STRUCTURED (≥3 assumptions)
PUT  /financial-decision-cases/:id/analyze        STRUCTURED → ANALYZED (≥3 risks)
PUT  /financial-decision-cases/:id/recommend      ANALYZED → RECOMMENDED (triggers LLM)
PUT  /financial-decision-cases/:id/decide         RECOMMENDED → DECIDED
PUT  /financial-decision-cases/:id/review         DECIDED → UNDER_REVIEW
```

---

## Non-Negotiable Principles

- No direct free-form answer generation — all LLM output is structured
- No bypassing of state machine — HTTP 409 on invalid transitions
- No missing audit logs — every action logged
- No silent failure — all errors structured
- All transitions logged
- All decisions versioned

---

## LLM Integration

Uses OpenAI `gpt-4o` for Pyramid Principle recommendations and Game Theory analysis. Falls back gracefully to structured mock data if `OPENAI_API_KEY` is absent.

---

## Security Notes

- JWT secret required at startup
- CORS restricted to configured origins
- Default admin credentials are for development only
