"""
core/feedback_loop.py  —  BKL-004
Feedback Loop E08 -> E01.

Processa revisão pós-decisão, extrai sinais de calibração,
persiste em SQLite e gera relatório de ajuste para o classifier.
"""

from __future__ import annotations
import json, sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from models.decision import Decision, ImpactLevel, ConfidenceLevel

DB_PATH = Path(__file__).parent.parent / "db" / "decisions.db"


class CalibrationSignal(str, Enum):
    SUPERESTIMACAO_CONFIANCA = "SUPERESTIMACAO_CONFIANCA"
    SUBESTIMACAO_CONFIANCA   = "SUBESTIMACAO_CONFIANCA"
    DIVERGENCIA_PIOROU       = "DIVERGENCIA_PIOROU"
    DIVERGENCIA_MELHOROU     = "DIVERGENCIA_MELHOROU"
    PREMISSA_INVALIDA        = "PREMISSA_INVALIDA"
    RISCO_SUBESTIMADO        = "RISCO_SUBESTIMADO"


@dataclass
class FeedbackRecord:
    decision_id: str
    registro_id: str
    data_revisao: str
    tipo_decisao: str
    impacto_classificado: str
    nivel_confianca_e06: str
    desvio_magnitude: str
    desvio_direcao: str
    houve_divergencia: bool
    divergencia_piorou: str
    premissas_invalidadas: list[str]
    riscos_materializados: list[str]
    signals: list[str]
    ajustes_recomendados: list[str]
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class FeedbackLoop:
    """
    Processa E08 e retroalimenta o classificador (E01).

    Uso:
        loop = FeedbackLoop()
        record = loop.process(decision)   # após E08 preenchida
        report = loop.calibration_report()
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def process(self, decision: Decision) -> FeedbackRecord | None:
        if not decision.revisao or not decision.registro:
            return None

        rev = decision.revisao
        reg = decision.registro
        clf = decision.classificacao
        rec = decision.recomendacao

        signals: list[CalibrationSignal] = []
        ajustes: list[str] = []

        confianca = rec.nivel_confianca.value if rec else "DESCONHECIDO"
        magnitude = rev.desvio.magnitude

        # ── Calibração de confiança ───────────
        if confianca == ConfidenceLevel.ALTO.value and magnitude == "SIGNIFICATIVO":
            signals.append(CalibrationSignal.SUPERESTIMACAO_CONFIANCA)
            ajustes.append(
                f"Reduzir threshold ALTO para tipo "
                f"{clf.tipo_decisao.value if clf else 'DESCONHECIDO'}. "
                "Confiança ALTA mas desvio SIGNIFICATIVO.")

        if confianca == ConfidenceLevel.BAIXO.value and magnitude == "DESPREZIVEL":
            signals.append(CalibrationSignal.SUBESTIMACAO_CONFIANCA)
            ajustes.append(
                f"Revisar penalização BAIXO para tipo "
                f"{clf.tipo_decisao.value if clf else 'DESCONHECIDO'}. "
                "Confiança BAIXA mas desvio DESPREZIVEL.")

        # ── Divergência executiva ─────────────
        if reg.divergencia.existe:
            piorou = rev.impacto_da_divergencia.a_divergencia_piorou_o_resultado
            if piorou == "true":
                signals.append(CalibrationSignal.DIVERGENCIA_PIOROU)
                ajustes.append(
                    "Reforçar peso da recomendação analítica. "
                    "Divergência gerou resultado inferior ao recomendado.")
            elif piorou == "false":
                signals.append(CalibrationSignal.DIVERGENCIA_MELHOROU)
                ajustes.append(
                    "Investigar por que julgamento executivo superou recomendação analítica. "
                    "Possível gap em frameworks ou premissas do sistema.")

        # ── Premissas invalidadas ─────────────
        for p in rev.premissas_invalidadas:
            signals.append(CalibrationSignal.PREMISSA_INVALIDA)
            ajustes.append(
                f"Premissa invalidada em produção: '{p}'. "
                "Verificar recorrência em decisões do mesmo tipo.")

        # ── Riscos subestimados ───────────────
        if rev.riscos_que_se_materializaram and decision.riscos:
            mat = set(rev.riscos_que_se_materializaram)
            for r in decision.riscos.riscos:
                if r.id in mat and r.probabilidade.value == "BAIXA":
                    signals.append(CalibrationSignal.RISCO_SUBESTIMADO)
                    ajustes.append(
                        f"Risco {r.id} (prob BAIXA) materializou. "
                        f"Revisar critérios de probabilidade para categoria {r.categoria.value}.")

        record = FeedbackRecord(
            decision_id=decision.id,
            registro_id=reg.registro_id,
            data_revisao=rev.data_revisao.isoformat(),
            tipo_decisao=clf.tipo_decisao.value if clf else "DESCONHECIDO",
            impacto_classificado=clf.impacto.value if clf else "DESCONHECIDO",
            nivel_confianca_e06=confianca,
            desvio_magnitude=magnitude,
            desvio_direcao=rev.desvio.direcao,
            houve_divergencia=reg.divergencia.existe,
            divergencia_piorou=rev.impacto_da_divergencia.a_divergencia_piorou_o_resultado or "INDETERMINADO",
            premissas_invalidadas=rev.premissas_invalidadas,
            riscos_materializados=rev.riscos_que_se_materializaram,
            signals=[s.value for s in signals],
            ajustes_recomendados=ajustes,
        )
        self._persist(record)
        return record

    def calibration_report(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT signals, premissas_invalidadas, riscos_materializados, "
                "desvio_magnitude, nivel_confianca_e06, houve_divergencia, divergencia_piorou "
                "FROM feedback_records ORDER BY created_at DESC"
            ).fetchall()

        if not rows:
            return {"status": "SEM_DADOS", "total_revisoes": 0}

        total = len(rows)
        signal_count: dict[str, int] = {}
        superest = subest = div_pior = 0
        premissas: list[str] = []
        riscos: list[str] = []

        for row in rows:
            signals = json.loads(row[0])
            for s in signals:
                signal_count[s] = signal_count.get(s, 0) + 1
            if CalibrationSignal.SUPERESTIMACAO_CONFIANCA.value in signals:
                superest += 1
            if CalibrationSignal.SUBESTIMACAO_CONFIANCA.value in signals:
                subest += 1
            if CalibrationSignal.DIVERGENCIA_PIOROU.value in signals:
                div_pior += 1
            premissas.extend(json.loads(row[1]))
            riscos.extend(json.loads(row[2]))

        alertas: list[str] = []
        taxa_super = round(superest / total * 100, 1)
        taxa_div   = round(div_pior / total * 100, 1)

        if taxa_super > 30:
            alertas.append(
                f"SUPERESTIMAÇÃO SISTEMÁTICA ({taxa_super}%): reduzir threshold "
                "de confiança ALTO no classifier.py.")
        if taxa_div > 40:
            alertas.append(
                f"DIVERGÊNCIA PREJUDICIAL ({taxa_div}%): reforçar enforcement "
                "do protocolo para decisões onde executivo divergiu.")
        if premissas:
            from collections import Counter
            for premissa, count in Counter(premissas).most_common(3):
                if count >= 2:
                    alertas.append(
                        f"PREMISSA RECORRENTE INVÁLIDA ({count}x): '{premissa}'. "
                        "Adicionar ao tensionamento padrão do prompt E03.")

        return {
            "status": "DADOS_DISPONIVEIS",
            "total_revisoes": total,
            "taxa_superestimacao_pct": taxa_super,
            "taxa_subestimacao_pct": round(subest / total * 100, 1),
            "taxa_divergencia_prejudicial_pct": taxa_div,
            "sinais": signal_count,
            "premissas_recorrentes": premissas,
            "riscos_materializados_recorrentes": riscos,
            "alertas_calibracao": alertas,
            "acao_recomendada": (
                "Revisar classifier.py e prompts afetados"
                if alertas else "Nenhuma ação de calibração necessária."
            )
        }

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT NOT NULL,
                    registro_id TEXT NOT NULL,
                    data_revisao TEXT,
                    tipo_decisao TEXT,
                    impacto_classificado TEXT,
                    nivel_confianca_e06 TEXT,
                    desvio_magnitude TEXT,
                    desvio_direcao TEXT,
                    houve_divergencia INTEGER,
                    divergencia_piorou TEXT,
                    premissas_invalidadas TEXT,
                    riscos_materializados TEXT,
                    ajustes_recomendados TEXT,
                    signals TEXT,
                    created_at TEXT
                )
            """)
            conn.commit()

    def _persist(self, r: FeedbackRecord):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO feedback_records VALUES
                (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                r.decision_id, r.registro_id, r.data_revisao,
                r.tipo_decisao, r.impacto_classificado, r.nivel_confianca_e06,
                r.desvio_magnitude, r.desvio_direcao, int(r.houve_divergencia),
                r.divergencia_piorou,
                json.dumps(r.premissas_invalidadas, ensure_ascii=False),
                json.dumps(r.riscos_materializados, ensure_ascii=False),
                json.dumps(r.ajustes_recomendados, ensure_ascii=False),
                json.dumps(r.signals, ensure_ascii=False),
                r.created_at,
            ))
            conn.commit()
