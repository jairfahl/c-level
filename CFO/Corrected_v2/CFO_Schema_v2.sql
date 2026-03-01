-- ============================================================
--  CFO MENTOR – Database Schema v2
--  PostgreSQL 15+
--  Mentor C-Level | Março 2026
-- ============================================================

-- ============================================================
--  EXTENSÕES
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()


-- ============================================================
--  ENUM TYPES
-- ============================================================

CREATE TYPE financial_domain AS ENUM (
  'planning',
  'reporting',
  'treasury',
  'funding',
  'risk'
);

CREATE TYPE decision_state AS ENUM (
  'DRAFT',
  'CLASSIFIED',
  'STRUCTURED',
  'ANALYZED',
  'RECOMMENDED',
  'DECIDED',
  'UNDER_REVIEW',
  'CLOSED'
);

CREATE TYPE decision_type AS ENUM (
  'budget_adjustment',
  'forecast_revision',
  'capital_allocation',
  'debt_structuring',
  'liquidity_management',
  'risk_hedging',
  'cost_reduction',
  'investment_evaluation'
);

-- [v2] ENUM corrigido – substituiu VARCHAR(10)
CREATE TYPE time_horizon_type AS ENUM (
  'short',
  'medium',
  'long'
);

-- [v2] NOVO – seleção automática de framework analítico
CREATE TYPE framework_type AS ENUM (
  'pdca',
  'scenario_analysis',
  'game_theory',
  'trade_off',
  'risk_matrix',
  'capital_allocation'
);


-- ============================================================
--  TABELA PRINCIPAL: financial_decision_cases
-- ============================================================
CREATE TABLE financial_decision_cases (
  id                      UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
  title                   TEXT            NOT NULL,
  description             TEXT            NOT NULL,
  financial_domain        financial_domain NOT NULL,
  impact_score            INT             CHECK (impact_score BETWEEN 1 AND 5),
  financial_exposure      NUMERIC(18,2)   NOT NULL CHECK (financial_exposure > 0),
  time_horizon            time_horizon_type,                          -- [v2] ENUM
  external_agents_present BOOLEAN         NOT NULL DEFAULT FALSE,
  decision_type           decision_type   NOT NULL,
  framework_selected      framework_type,                             -- [v2] NOVO
  scenario_required       BOOLEAN         GENERATED ALWAYS AS          -- [v2] NOVO
                            (impact_score >= 4) STORED,
  state                   decision_state  NOT NULL DEFAULT 'DRAFT',
  created_at              TIMESTAMP       NOT NULL DEFAULT NOW(),
  updated_at              TIMESTAMP       NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  financial_decision_cases                       IS 'Caso decisório financeiro – entidade central do Mentor CFO.';
COMMENT ON COLUMN financial_decision_cases.impact_score          IS '1=baixo … 5=crítico. Calculado com base em financial_exposure.';
COMMENT ON COLUMN financial_decision_cases.scenario_required     IS 'Gerado automaticamente: true quando impact_score >= 4.';
COMMENT ON COLUMN financial_decision_cases.framework_selected    IS 'Selecionado automaticamente pela engine determinística na transição CLASSIFIED→STRUCTURED.';


-- ============================================================
--  PREMISSAS
-- ============================================================
CREATE TABLE financial_assumptions (
  id                UUID  PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_case_id  UUID  NOT NULL REFERENCES financial_decision_cases(id) ON DELETE CASCADE,
  text              TEXT  NOT NULL,
  is_implicit       BOOLEAN NOT NULL DEFAULT FALSE,   -- [v2] flag para premissas capturadas pelo LLM
  created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMENT ON COLUMN financial_assumptions.is_implicit IS 'true = premissa implícita identificada pelo Mentor, não declarada originalmente pelo executivo.';


-- ============================================================
--  RISCOS
-- ============================================================
CREATE TABLE financial_risks (
  id                UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_case_id  UUID    NOT NULL REFERENCES financial_decision_cases(id) ON DELETE CASCADE,
  text              TEXT    NOT NULL,
  materialized      BOOLEAN NOT NULL DEFAULT FALSE,
  created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMENT ON COLUMN financial_risks.materialized IS 'Atualizado na revisão pós-decisão: true se o risco se concretizou.';


-- ============================================================
--  MÉTRICAS IMPACTADAS
-- ============================================================
CREATE TABLE financial_metrics_impacted (
  id                UUID  PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_case_id  UUID  NOT NULL REFERENCES financial_decision_cases(id) ON DELETE CASCADE,
  metric_name       TEXT  NOT NULL,
  created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);


-- ============================================================
--  DECISÕES
-- ============================================================
CREATE TABLE decisions (
  id                  UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_case_id    UUID    NOT NULL REFERENCES financial_decision_cases(id) ON DELETE CASCADE,
  recommendation      TEXT    NOT NULL,
  executive_decision  TEXT,
  divergence_flag     BOOLEAN NOT NULL DEFAULT FALSE,
  created_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMENT ON COLUMN decisions.divergence_flag IS 'true = decisão executiva diferiu da recomendação do Mentor.';


-- ============================================================
--  REVISÕES PÓS-DECISÃO
-- ============================================================
CREATE TABLE reviews (
  id                                   UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_case_id                     UUID          NOT NULL REFERENCES financial_decision_cases(id) ON DELETE CASCADE,
  outcome_summary                      TEXT,
  forecast_accuracy_score              INT           CHECK (forecast_accuracy_score BETWEEN 1 AND 10),
  risk_realization_rate                NUMERIC(5,2)  CHECK (risk_realization_rate BETWEEN 0 AND 100),
  capital_allocation_efficiency_score  NUMERIC(5,2)  CHECK (capital_allocation_efficiency_score BETWEEN 0 AND 100),
  divergence_outcome_flag              BOOLEAN       NOT NULL DEFAULT FALSE,  -- [v2] NOVO
  created_at                           TIMESTAMP     NOT NULL DEFAULT NOW()
);

COMMENT ON COLUMN reviews.divergence_outcome_flag IS '[v2] true = a divergência do executivo resultou em pior resultado que a recomendação do Mentor.';


-- ============================================================
--  TRANSIÇÕES DE ESTADO  [v2 NOVA]
-- ============================================================
CREATE TABLE state_transitions (
  id                UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_case_id  UUID          NOT NULL REFERENCES financial_decision_cases(id) ON DELETE CASCADE,
  from_state        decision_state,
  to_state          decision_state NOT NULL,
  transitioned_at   TIMESTAMP     NOT NULL DEFAULT NOW(),
  triggered_by      TEXT
);

COMMENT ON TABLE state_transitions IS '[v2] Trilha completa de transições de estado para auditoria. Ausente no schema original.';


-- ============================================================
--  AUDIT LOGS  [v2 NOVA]
-- ============================================================
CREATE TABLE audit_logs (
  id                UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_case_id  UUID      REFERENCES financial_decision_cases(id) ON DELETE CASCADE,
  action            TEXT      NOT NULL,
  payload           JSONB,
  created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  audit_logs         IS '[v2] Log imutável de todas as ações do sistema. INSERT ONLY.';
COMMENT ON COLUMN audit_logs.action  IS 'Ex: CASE_CREATED, STATE_TRANSITION, LLM_CALLED, LLM_FALLBACK, DIVERGENCE_RECORDED.';

-- Garantir que audit_logs seja INSERT ONLY (sem UPDATE/DELETE)
CREATE RULE audit_logs_no_update AS ON UPDATE TO audit_logs DO INSTEAD NOTHING;
CREATE RULE audit_logs_no_delete AS ON DELETE TO audit_logs DO INSTEAD NOTHING;


-- ============================================================
--  HEURÍSTICAS FINANCEIRAS  [v2 NOVA]
-- ============================================================
CREATE TABLE financial_heuristics (
  id                UUID             PRIMARY KEY DEFAULT gen_random_uuid(),
  decision_type     decision_type    NOT NULL,
  financial_domain  financial_domain NOT NULL,
  heuristic_key     TEXT             NOT NULL,
  heuristic_value   JSONB            NOT NULL,
  source_case_id    UUID             REFERENCES financial_decision_cases(id) ON DELETE SET NULL,
  active            BOOLEAN          NOT NULL DEFAULT TRUE,
  created_at        TIMESTAMP        NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMP        NOT NULL DEFAULT NOW(),
  UNIQUE (decision_type, financial_domain, heuristic_key)
);

COMMENT ON TABLE  financial_heuristics              IS '[v2] Registro de heurísticas aprendidas pós-decisão. Manual no MVP; automatizado em fase futura.';
COMMENT ON COLUMN financial_heuristics.heuristic_key IS 'Ex: high_risk_liquidity_indicators, implicit_covenants_debt_structuring.';


-- ============================================================
--  FUNÇÃO: atualizar updated_at automaticamente
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_fdc_updated_at
  BEFORE UPDATE ON financial_decision_cases
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_heuristics_updated_at
  BEFORE UPDATE ON financial_heuristics
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================================
--  ÍNDICES
-- ============================================================
CREATE INDEX idx_fdc_domain    ON financial_decision_cases(financial_domain);
CREATE INDEX idx_fdc_state     ON financial_decision_cases(state);
CREATE INDEX idx_fdc_type      ON financial_decision_cases(decision_type);
CREATE INDEX idx_fdc_created   ON financial_decision_cases(created_at DESC);

CREATE INDEX idx_assump_case   ON financial_assumptions(decision_case_id);
CREATE INDEX idx_risks_case    ON financial_risks(decision_case_id);
CREATE INDEX idx_metrics_case  ON financial_metrics_impacted(decision_case_id);
CREATE INDEX idx_decisions_case ON decisions(decision_case_id);
CREATE INDEX idx_reviews_case  ON reviews(decision_case_id);
CREATE INDEX idx_st_case       ON state_transitions(decision_case_id);
CREATE INDEX idx_st_time       ON state_transitions(transitioned_at DESC);
CREATE INDEX idx_al_case       ON audit_logs(decision_case_id);
CREATE INDEX idx_al_action     ON audit_logs(action);
CREATE INDEX idx_al_created    ON audit_logs(created_at DESC);
CREATE INDEX idx_heur_type     ON financial_heuristics(decision_type, financial_domain);

-- ============================================================
--  FIM DO SCHEMA
-- ============================================================
