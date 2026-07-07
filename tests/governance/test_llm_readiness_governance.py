"""Preuves de gouvernance : la préparation LLM ne confère AUCUNE autonomie (C0.8).

Tracabilite : docs/llm/C0-8-llm-production-readiness.md,
docs/strategy/AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md,
docs/quality/05-governance-validation.md, ADR-0010 (déterminisme des interactions LLM),
ADR-0011 (audit source unique).

Invariants prouves ici (bloquants) :
  * **LLM != decision CEO** : aucune reponse/politique ne prend ni n'applique une decision ; le CEO
    reste seul decideur metier ;
  * **LLM != application** : aucune surface d'action ;
  * **LLM != audit** : la readiness n'ecrit ni ne reecrit l'audit (source de verite unique) ;
  * **LLM != memoire** : la readiness n'ecrit pas la memoire (non probante) ;
  * **aucun LLM reel actif** : aucun provider, appel reseau, clef d'API ; aucun mode
  `LIVE_PRODUCTION` ;
  * **aucun RAG / vector store / embedding** ;
  * **E9 reste ferme** ; **aucun objet produit actif**.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import aisos.llm_readiness.contracts as contracts_module
import aisos.llm_readiness.policy as policy_module
import aisos.llm_readiness.replay as replay_module
from aisos.llm_readiness import (
    LLMReadinessMode,
    LLMReadinessPolicy,
    LLMReadinessPolicyDecisionStatus,
    LLMReadinessPurpose,
    LLMReadinessRequest,
    LLMReadinessResponse,
    LLMReadinessStatus,
    ReplayLLMReadinessClient,
)

pytestmark = pytest.mark.governance

_MODULES = (contracts_module, policy_module, replay_module)
_NOTICE = "Le LLM ne decide pas, n'applique pas et ne remplace ni le CEO ni l'audit."


def _source(module: object) -> str:
    return Path(module.__file__).read_text(encoding="utf-8")  # type: ignore[attr-defined]


def _imports(module: object) -> tuple[str, ...]:
    targets: list[str] = []
    for raw in _source(module).splitlines():
        line = raw.strip()
        if line.startswith("from "):
            targets.append(line.split()[1])
        elif line.startswith("import "):
            targets.append(line.split()[1].split(",")[0])
    return tuple(targets)


def _request(prompt: str = "resume le contexte") -> LLMReadinessRequest:
    return LLMReadinessRequest(
        id="req-1",
        organization_id="org-a",
        purpose=LLMReadinessPurpose.CONTEXT_SUMMARY,
        mode=LLMReadinessMode.REPLAY_ONLY,
        prompt=prompt,
        safety_notice="assistance controlee",
    )


def test_llm_is_not_a_ceo_decision() -> None:
    # La decision de policy est une autorisation TECHNIQUE de preparation, jamais une decision CEO.
    decision = LLMReadinessPolicy().evaluate(_request())
    assert decision.status in (
        LLMReadinessPolicyDecisionStatus.ALLOWED,
        LLMReadinessPolicyDecisionStatus.DENIED,
    )
    for name in ("ceo_outcome", "approve", "decide_business", "apply", "final_decision"):
        assert not hasattr(decision, name)


def test_llm_applies_and_decides_nothing() -> None:
    response = LLMReadinessResponse.of(
        response_id="resp-1",
        request_id="req-1",
        status=LLMReadinessStatus.PRODUCED,
        model_label="m",
        provider_label="p",
        non_decision_notice=_NOTICE,
        content="assistance",
    )
    for name in (
        "decide",
        "approve",
        "reject",
        "apply",
        "execute",
        "improve",
        "trigger_e7",
        "open_e9",
        "create_solution",
        "create_team",
    ):
        assert not hasattr(response, name)
        assert not hasattr(LLMReadinessPolicy(), name)
        assert not hasattr(ReplayLLMReadinessClient(), name)


def test_readiness_never_writes_audit_or_memory() -> None:
    subjects = (
        ReplayLLMReadinessClient(),
        LLMReadinessPolicy(),
        LLMReadinessResponse.of(
            response_id="r",
            request_id="q",
            status=LLMReadinessStatus.DECLINED,
            model_label="m",
            provider_label="p",
            non_decision_notice=_NOTICE,
        ),
    )
    for subject in subjects:
        for name in (
            "write_audit",
            "rewrite_audit",
            "append_audit",
            "write_memory",
            "store_memory",
        ):
            assert not hasattr(subject, name)


def test_response_notice_reasserts_non_decision_ceo_and_audit() -> None:
    # Invariant : une reponse ne peut JAMAIS porter une notice qui affirme que le LLM decide ou
    # remplace le CEO/audit — meme si elle contient par ailleurs les mots decide/CEO/audit.
    dangerous = (
        "reponse officielle",
        "le llm decide",
        "ne decide pas mais fait foi",
        "Le LLM décide pour le CEO et remplace l’audit.",  # noqa: RUF001
        "Le LLM valide la décision CEO.",
        "Le LLM remplace l’audit.",  # noqa: RUF001
    )
    for bad in dangerous:
        with pytest.raises(ValueError, match="non_decision_notice"):
            LLMReadinessResponse.of(
                response_id="r",
                request_id="q",
                status=LLMReadinessStatus.PRODUCED,
                model_label="m",
                provider_label="p",
                non_decision_notice=bad,
            )


def test_no_real_llm_active_no_live_mode() -> None:
    # Aucun mode d'appel reel : les modes sont surs (replay/test/disabled/declaratif).
    assert {m.value for m in LLMReadinessMode} == {
        "replay_only",
        "deterministic_test",
        "disabled",
        "provider_ready_declarative",
    }
    assert "LIVE_PRODUCTION" not in {m.name for m in LLMReadinessMode}


def test_no_network_provider_or_api_key_dependency() -> None:
    for module in _MODULES:
        for target in _imports(module):
            for forbidden in (
                "openai",
                "anthropic",
                "langchain",
                "llama_index",
                "chromadb",
                "faiss",
                "pgvector",
                "sentence_transformers",
                "httpx",
                "requests",
                "aiohttp",
                "urllib",
                "socket",
            ):
                assert forbidden not in target, f"dependance interdite : {target}"
        source = _source(module)
        for forbidden in ("os.environ", "getenv", "api_key", "API_KEY"):
            assert forbidden not in source, f"lecture de clef/secret interdite : {forbidden}"


def test_no_rag_vector_store_or_embedding() -> None:
    for module in _MODULES:
        source = _source(module).lower()
        # Aucune construction de RAG/embedding/vector store dans le code (mentions negatives en
        # prose OK
        # uniquement sous forme de gardes ; on verifie l'absence d'API d'indexation).
        for forbidden in (
            "embed(",
            "embeddings(",
            "vector_store",
            "vectorstore",
            "def retrieve",
            "rag(",
        ):
            assert forbidden not in source, f"construction interdite : {forbidden}"


def test_e9_stays_closed_no_open_e9_callable() -> None:
    for module in _MODULES:
        source = _source(module)
        assert "def open_e9" not in source
        assert "open_e9(" not in source
        assert "def trigger_e7" not in source
        assert "trigger_e7(" not in source


def test_no_active_product_object_defined() -> None:
    for module in _MODULES:
        source = _source(module)
        for name in (
            "Problem",
            "Idea",
            "Objective",
            "Solution",
            "SolutionVersion",
            "SolutionTeam",
            "ImprovementOpportunity",
            "SolutionTeamFactory",
            "ProjectTeamFactory",
            "AIOrganizationFactory",
        ):
            assert not re.search(rf"^\s*class\s+{re.escape(name)}\b", source, re.MULTILINE)


def test_module_does_not_couple_active_domain() -> None:
    for module in _MODULES:
        for target in _imports(module):
            for forbidden in (
                "aisos.evolution",
                "aisos.orchestrator",
                "aisos.councils",
                "aisos.agents",
                "aisos.infrastructure.llm",
                "aisos.access",
                "aisos.ceo_decision",
                "aisos.operational_audit",
                "aisos.operational_memory",
            ):
                assert not target.startswith(forbidden), f"couplage interdit : {target}"
