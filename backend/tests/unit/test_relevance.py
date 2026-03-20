"""
Tests for RelevanceValidator — deterministic relevance validation for financial documents.
"""
import pytest

from app.services.relevance_validator import RelevanceValidator, RelevanceVerdict


class TestRelevanceValidatorRelevant:
    """Documents clearly about finance → RELEVANT."""

    def test_financial_report(self):
        text = (
            "Relatório de Resultado Trimestral: O EBITDA da companhia atingiu R$ 450M, "
            "representando uma margem EBITDA de 32%. O fluxo de caixa operacional cresceu "
            "15% em relação ao trimestre anterior, impulsionado pela redução do capex. "
            "A estrutura de capital permanece saudável com alavancagem de 2.1x."
        )
        result = RelevanceValidator.validate(text)
        assert result.verdict == RelevanceVerdict.RELEVANT
        assert result.confidence == 0.9
        assert len(result.domain_keywords_found) >= 3
        assert len(result.off_topic_keywords_found) == 0

    def test_treasury_document(self):
        text = (
            "Política de gestão de caixa e tesouraria. O objetivo é manter liquidez "
            "mínima de R$ 100M, com aplicações em CDI e operações de hedge cambial "
            "para proteger exposição ao dólar. O WACC atual é de 12.5%."
        )
        result = RelevanceValidator.validate(text)
        assert result.verdict == RelevanceVerdict.RELEVANT
        assert "wacc" in result.domain_keywords_found

    def test_english_financial_terms(self):
        text = (
            "DCF valuation model for the acquisition target. The free cash flow "
            "projections indicate a terminal value of $2.5B with a discount rate "
            "of 10%. The NPV analysis shows positive returns with ROI of 18%."
        )
        result = RelevanceValidator.validate(text)
        assert result.verdict == RelevanceVerdict.RELEVANT

    def test_budget_planning(self):
        text = (
            "Planejamento financeiro 2027: O orçamento prevê receita líquida de R$ 2B, "
            "com margem bruta de 45% e lucro líquido projetado de R$ 300M. "
            "O forecast considera cenário base com inflação IPCA de 4.5%."
        )
        result = RelevanceValidator.validate(text)
        assert result.verdict == RelevanceVerdict.RELEVANT


class TestRelevanceValidatorIrrelevant:
    """Documents clearly off-topic → IRRELEVANT."""

    def test_marketing_document(self):
        text = (
            "Estratégia de marketing digital 2026: Aumentar engajamento em social media, "
            "otimizar SEO e SEM, investir em Google Ads e Facebook Ads. "
            "Meta: 50k followers até junho, pipeline de vendas com 200 MQL por mês."
        )
        result = RelevanceValidator.validate(text)
        assert result.verdict == RelevanceVerdict.IRRELEVANT
        assert len(result.off_topic_keywords_found) > 0

    def test_devops_document(self):
        text = (
            "Guia de deploy com Kubernetes e Docker. Configuração de CI/CD pipeline "
            "com GitHub Actions. Arquitetura de microserviços com API Gateway. "
            "Sprint planning para backlog de produto com user story mapping."
        )
        result = RelevanceValidator.validate(text)
        assert result.verdict == RelevanceVerdict.IRRELEVANT

    def test_hr_document(self):
        text = (
            "Processo de recrutamento e seleção de candidatos para vagas de tecnologia. "
            "Onboarding de funcionários novos inclui treinamento de 2 semanas. "
            "Pesquisa de NPS interno e customer success com churn de clientes abaixo de 5%."
        )
        result = RelevanceValidator.validate(text)
        assert result.verdict == RelevanceVerdict.IRRELEVANT

    def test_empty_text(self):
        result = RelevanceValidator.validate("")
        assert result.verdict == RelevanceVerdict.IRRELEVANT

    def test_generic_text_no_keywords(self):
        text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 20
        result = RelevanceValidator.validate(text)
        assert result.verdict == RelevanceVerdict.IRRELEVANT
        assert result.confidence == 0.6  # no off-topic, no positive → low confidence


class TestRelevanceValidatorBorderline:
    """Mixed content → BORDERLINE."""

    def test_mixed_finance_and_sales(self):
        text = (
            "Relatório integrado: O EBITDA cresceu 10%, a margem bruta subiu para 40%, "
            "o fluxo de caixa operacional melhorou. Porém o pipeline de vendas "
            "apresentou queda de 15% nos leads qualificados. "
        )
        result = RelevanceValidator.validate(text)
        assert result.verdict == RelevanceVerdict.BORDERLINE
        assert result.confidence >= 0.5
        assert len(result.domain_keywords_found) >= 1
        assert len(result.off_topic_keywords_found) >= 1

    def test_single_financial_term(self):
        text = "O orçamento do departamento foi aprovado pela diretoria na última reunião."
        result = RelevanceValidator.validate(text)
        # 1 positive, 0 negative → borderline (positive >= 1 and off_topic <= positive)
        assert result.verdict == RelevanceVerdict.BORDERLINE


class TestRelevanceValidatorEdgeCases:
    """Edge cases and boundary conditions."""

    def test_long_text_uses_first_3000_chars(self):
        # Financial terms only in the first 3000 chars; irrelevant after
        financial_part = "O EBITDA da empresa foi de R$ 100M com WACC de 10% e capex reduzido. " * 50
        assert len(financial_part) > 3000
        irrelevant_part = "pipeline de vendas leads MQL marketing digital SEO " * 200
        text = financial_part + irrelevant_part
        result = RelevanceValidator.validate(text)
        # Should only scan first 3000 chars (financial part)
        assert result.verdict == RelevanceVerdict.RELEVANT

    def test_case_insensitive(self):
        text = "O EBITDA, ebitda, Ebitda são todos reconhecidos. WACC e wacc também. Capex e CAPEX igualmente."
        result = RelevanceValidator.validate(text)
        assert result.verdict == RelevanceVerdict.RELEVANT

    def test_domain_parameter_accepted(self):
        text = "Relatório com EBITDA, WACC e fluxo de caixa operacional."
        result = RelevanceValidator.validate(text, domain="treasury")
        assert result.verdict == RelevanceVerdict.RELEVANT

    def test_result_is_frozen_dataclass(self):
        result = RelevanceValidator.validate("EBITDA WACC capex hedge")
        with pytest.raises(AttributeError):
            result.verdict = RelevanceVerdict.IRRELEVANT
