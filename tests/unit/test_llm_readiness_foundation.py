"""Fondation de préparation LLM contrôlée (C0.8 — LLM Production Readiness réaligné).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.8),
docs/llm/C0-8-llm-production-readiness.md, docs/quality/02-unit-testing.md.

Prouve que : la fondation de readiness LLM se limite a **preparer**. Demande/reponse immuables et
declaratives (reponse scellee par empreinte, `non_decision_notice` valide), politique deterministe
(`ALLOWED`/`DENIED` = autorisation technique de preparation, refus des modes/prompts interdits et
des
verbes d'action), client **replay hors ligne** deterministe sans provider reel. Aucun appel reseau ;
aucune clef d'API ; aucune dependance OpenAI/Anthropic/LangChain/RAG/vector store ; aucun objet
produit actif ; aucune surface de pouvoir ; contrats E1..E8 et C0.1..C0.7 inchanges ; E9 reste
ferme.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

import aisos.llm_readiness.contracts as contracts_module
import aisos.llm_readiness.policy as policy_module
import aisos.llm_readiness.replay as replay_module
from aisos.llm_readiness import (
    LLMReadinessMode,
    LLMReadinessPolicy,
    LLMReadinessPolicyDecisionStatus,
    LLMReadinessPurpose,
    LLMReadinessReference,
    LLMReadinessReferenceKind,
    LLMReadinessRequest,
    LLMReadinessResponse,
    LLMReadinessStatus,
    RecordedLLMReadinessInteraction,
    ReplayLLMReadinessClient,
    compute_response_hash,
)

pytestmark = pytest.mark.unit

_NOTICE = "Le LLM ne decide pas, n'applique pas et ne remplace ni le CEO ni l'audit."


def _request(
    *,
    request_id: str = "req-1",
    mode: LLMReadinessMode = LLMReadinessMode.REPLAY_ONLY,
    prompt: str = "resume le contexte du projet FocusLife",
    safety_notice: str = "assistance controlee, non decisionnelle",
) -> LLMReadinessRequest:
    return LLMReadinessRequest(
        id=request_id,
        organization_id="org-a",
        purpose=LLMReadinessPurpose.CONTEXT_SUMMARY,
        mode=mode,
        prompt=prompt,
        context="idee a transformer en solution",
        references=(
            LLMReadinessReference(
                kind=LLMReadinessReferenceKind.MEMORY_CONTEXT, reference="memory://1"
            ),
        ),
        safety_notice=safety_notice,
    )


def _response(
    *,
    response_id: str = "resp-1",
    request_id: str = "req-1",
    status: LLMReadinessStatus = LLMReadinessStatus.PRODUCED,
    content: str = "resume non autoritaire",
    notice: str = _NOTICE,
) -> LLMReadinessResponse:
    return LLMReadinessResponse.of(
        response_id=response_id,
        request_id=request_id,
        status=status,
        model_label="deterministic-test-model",
        provider_label="replay-offline",
        non_decision_notice=notice,
        content=content,
        references=(
            LLMReadinessReference(
                kind=LLMReadinessReferenceKind.AUDIT_REFERENCE, reference="audit://ev-1"
            ),
        ),
    )


# --- Immuabilité -------------------------------------------------------------------------------


def test_request_is_immutable() -> None:
    with pytest.raises(ValidationError):
        _request().prompt = "autre"  # type: ignore[misc]


def test_response_is_immutable() -> None:
    with pytest.raises(ValidationError):
        _response().content = "autre"  # type: ignore[misc]


def test_request_and_response_are_deterministic() -> None:
    assert _request() == _request()
    assert _response() == _response()


# --- Scellage de la réponse --------------------------------------------------------------------


def test_response_content_hash_is_deterministic() -> None:
    response = _response()
    assert response.content_hash == compute_response_hash(
        response_id=response.id,
        request_id=response.request_id,
        status=response.status,
        content=response.content,
        model_label=response.model_label,
        provider_label=response.provider_label,
        non_decision_notice=response.non_decision_notice,
        references=response.references,
    )
    assert response.content_hash == _response().content_hash


def test_tampered_response_hash_is_rejected() -> None:
    with pytest.raises(ValidationError, match="empreinte"):
        LLMReadinessResponse(
            id="resp-1",
            request_id="req-1",
            status=LLMReadinessStatus.PRODUCED,
            content="c",
            model_label="m",
            provider_label="p",
            non_decision_notice=_NOTICE,
            content_hash="deadbeef",
        )


@pytest.mark.parametrize("field", ["content", "model_label", "references"])
def test_changing_sealed_field_changes_hash(field: str) -> None:
    base = _response()
    if field == "content":
        other = _response(content="autre contenu")
    elif field == "model_label":
        other = LLMReadinessResponse.of(
            response_id=base.id,
            request_id=base.request_id,
            status=base.status,
            model_label="autre-modele",
            provider_label=base.provider_label,
            non_decision_notice=base.non_decision_notice,
            content=base.content,
            references=base.references,
        )
    else:  # references
        other = LLMReadinessResponse.of(
            response_id=base.id,
            request_id=base.request_id,
            status=base.status,
            model_label=base.model_label,
            provider_label=base.provider_label,
            non_decision_notice=base.non_decision_notice,
            content=base.content,
            references=(),
        )
    assert other.content_hash != base.content_hash


# --- non_decision_notice : obligatoire et validé -----------------------------------------------


def test_non_decision_notice_is_mandatory() -> None:
    with pytest.raises(ValidationError):
        LLMReadinessResponse.of(
            response_id="resp-1",
            request_id="req-1",
            status=LLMReadinessStatus.PRODUCED,
            model_label="m",
            provider_label="p",
            non_decision_notice="",
        )


@pytest.mark.parametrize(
    "notice",
    [
        "reponse officielle",  # ni non-decision, ni ceo, ni audit
        "le llm decide et valide",  # affirme l'inverse, sans ceo/audit
        "ne decide pas mais fait foi",  # non-decision mais ni ceo ni audit
        "ne decide pas, ne remplace pas le ceo",  # manque l'audit
        "ne decide pas, ne remplace pas l'audit",  # manque le ceo
    ],
)
def test_non_conforming_notice_is_rejected(notice: str) -> None:
    with pytest.raises(ValidationError):
        LLMReadinessResponse.of(
            response_id="resp-1",
            request_id="req-1",
            status=LLMReadinessStatus.PRODUCED,
            model_label="m",
            provider_label="p",
            non_decision_notice=notice,
        )


def test_conforming_notice_is_accepted() -> None:
    response = _response(notice="Le LLM ne DECIDE pas et ne remplace ni le CEO ni l'AUDIT.")
    assert "decide" in response.non_decision_notice.lower()


@pytest.mark.parametrize(
    "notice",
    [
        "Le LLM ne decide pas, n'applique pas et ne remplace ni le CEO ni l'audit.",
        "Réponse non décisionnelle : le LLM ne remplace pas le CEO et ne remplace jamais l’audit.",  # noqa: RUF001
        "Le LLM ne décide pas et ne se substitue ni au CEO ni à l’audit.",  # noqa: RUF001
    ],
)
def test_conforming_notice_variants_are_accepted(notice: str) -> None:
    # Formulations reellement non decisionnelles (accents et apostrophes courbes tolerees).
    response = _response(notice=notice)
    assert response.non_decision_notice == notice


@pytest.mark.parametrize(
    "notice",
    [
        # Contient decide + CEO + audit mais AFFIRME l'inverse de l'invariant : doit etre refusee.
        "Le LLM décide pour le CEO et remplace l’audit.",  # noqa: RUF001
        "Le LLM valide la décision CEO.",
        "Le LLM applique la décision et fait foi dans l’audit.",  # noqa: RUF001
        "Le LLM remplace le CEO.",
        "Le LLM remplace l’audit.",  # noqa: RUF001
    ],
)
def test_dangerous_notice_is_rejected(notice: str) -> None:
    with pytest.raises(ValidationError):
        LLMReadinessResponse.of(
            response_id="resp-1",
            request_id="req-1",
            status=LLMReadinessStatus.PRODUCED,
            model_label="m",
            provider_label="p",
            non_decision_notice=notice,
        )


def test_disabled_mode_yields_denied_policy_decision() -> None:
    # DISABLED = etat sur (LLM eteint) : la policy refuse toute demande en ce mode.
    decision = LLMReadinessPolicy().evaluate(_request(mode=LLMReadinessMode.DISABLED))
    assert decision.status is LLMReadinessPolicyDecisionStatus.DENIED


# --- Politique de readiness --------------------------------------------------------------------


@pytest.mark.parametrize(
    "mode",
    [
        LLMReadinessMode.REPLAY_ONLY,
        LLMReadinessMode.DETERMINISTIC_TEST,
        LLMReadinessMode.PROVIDER_READY_DECLARATIVE,
    ],
)
def test_policy_allows_safe_modes(mode: LLMReadinessMode) -> None:
    decision = LLMReadinessPolicy().evaluate(_request(mode=mode))
    assert decision.status is LLMReadinessPolicyDecisionStatus.ALLOWED
    assert decision.reasons == ()


def test_policy_denies_disabled_mode() -> None:
    decision = LLMReadinessPolicy().evaluate(_request(mode=LLMReadinessMode.DISABLED))
    assert decision.status is LLMReadinessPolicyDecisionStatus.DENIED
    assert any("mode non autorise" in reason for reason in decision.reasons)


def test_no_live_production_mode_exists() -> None:
    names = {member.name for member in LLMReadinessMode}
    assert "LIVE_PRODUCTION" not in names
    assert "LIVE" not in names


def test_policy_denies_empty_prompt() -> None:
    decision = LLMReadinessPolicy().evaluate(_request(prompt="   "))
    assert decision.status is LLMReadinessPolicyDecisionStatus.DENIED
    assert any("prompt vide" in reason for reason in decision.reasons)


def test_policy_denies_empty_safety_notice() -> None:
    decision = LLMReadinessPolicy().evaluate(_request(safety_notice=""))
    assert decision.status is LLMReadinessPolicyDecisionStatus.DENIED
    assert any("safety_notice vide" in reason for reason in decision.reasons)


@pytest.mark.parametrize(
    "token",
    [
        "approve",
        "apply",
        "decide",
        "trigger_e7",
        "open_e9",
        "create_solution",
        "create_team",
        "rewrite_audit",
    ],
)
def test_policy_denies_forbidden_action_verbs(token: str) -> None:
    decision = LLMReadinessPolicy().evaluate(_request(prompt=f"merci de {token} maintenant"))
    assert decision.status is LLMReadinessPolicyDecisionStatus.DENIED
    assert any(token in reason for reason in decision.reasons)


def test_policy_is_deterministic() -> None:
    request = _request(prompt="please apply and decide")
    first = LLMReadinessPolicy().evaluate(request)
    second = LLMReadinessPolicy().evaluate(request)
    assert first == second


# --- Client replay déterministe / hors ligne ---------------------------------------------------


def test_replay_returns_recorded_response() -> None:
    recorded = _response()
    client = ReplayLLMReadinessClient(
        (RecordedLLMReadinessInteraction(request_id="req-1", response=recorded),)
    )
    assert client.respond(_request(request_id="req-1")) == recorded


def test_replay_is_deterministic_for_unknown_request() -> None:
    client = ReplayLLMReadinessClient()
    first = client.respond(_request(request_id="req-x"))
    second = client.respond(_request(request_id="req-x"))
    assert first == second
    assert first.status is LLMReadinessStatus.DECLINED
    assert first.content == ""


def test_replay_declined_response_is_sealed_and_non_decisional() -> None:
    response = ReplayLLMReadinessClient().respond(_request(request_id="req-y"))
    # La reponse deterministe reste scellee et non decisionnelle (notice valide a la construction).
    assert response.content_hash == compute_response_hash(
        response_id=response.id,
        request_id=response.request_id,
        status=response.status,
        content=response.content,
        model_label=response.model_label,
        provider_label=response.provider_label,
        non_decision_notice=response.non_decision_notice,
        references=response.references,
    )
    assert "audit" in response.non_decision_notice.lower()


def test_replay_client_calls_no_real_provider() -> None:
    # Aucune methode d'appel reseau/provider : le client ne fait que restituer une donnee.
    client = ReplayLLMReadinessClient()
    for name in ("connect", "http", "request", "fetch", "call_api", "generate", "complete"):
        assert not hasattr(client, name)


# --- Absence de surface de pouvoir -------------------------------------------------------------

_FORBIDDEN_POWER_METHODS = (
    "decide",
    "approve",
    "reject",
    "apply",
    "execute",
    "improve",
    "mutate",
    "delete",
    "rewrite",
    "trigger_e7",
    "open_e9",
    "create_solution",
    "create_team",
    "create_solution_team",
    "write_audit",
    "rewrite_audit",
    "write_memory",
)


def test_no_power_surface_on_request_response_policy_or_client() -> None:
    subjects = (
        _request(),
        _response(),
        LLMReadinessPolicy(),
        ReplayLLMReadinessClient(),
    )
    for subject in subjects:
        for name in _FORBIDDEN_POWER_METHODS:
            assert not hasattr(subject, name), f"surface de pouvoir interdite : {name}"


# --- Frontières de module ----------------------------------------------------------------------

_MODULES = (contracts_module, policy_module, replay_module)


def _module_source(module: object) -> str:
    return Path(module.__file__).read_text(encoding="utf-8")  # type: ignore[attr-defined]


def _imported_modules(module: object) -> tuple[str, ...]:
    targets: list[str] = []
    for raw in _module_source(module).splitlines():
        line = raw.strip()
        if line.startswith("from "):
            targets.append(line.split()[1])
        elif line.startswith("import "):
            targets.append(line.split()[1].split(",")[0])
    return tuple(targets)


def test_module_imports_no_active_domain() -> None:
    for module in _MODULES:
        for target in _imported_modules(module):
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
                "aisos.brain",
                "aisos.reasoning",
            ):
                assert not target.startswith(forbidden), f"import interdit : {target}"


def test_module_has_no_llm_provider_or_rag_dependency() -> None:
    for module in _MODULES:
        for target in _imported_modules(module):
            for forbidden in (
                "openai",
                "anthropic",
                "langchain",
                "llama_index",
                "llama-index",
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
                assert forbidden not in target, f"dependance interdite en C0.8 : {target}"


def test_module_reads_no_api_key() -> None:
    for module in _MODULES:
        source = _module_source(module)
        for forbidden in ("os.environ", "getenv", "api_key", "API_KEY", "secret"):
            assert forbidden not in source, f"lecture de secret/clef interdite : {forbidden}"


def test_module_defines_no_active_product_object() -> None:
    import re

    for module in _MODULES:
        source = _module_source(module)
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


def test_module_defines_no_open_e9_or_trigger_e7_callable() -> None:
    # E9 reste ferme : aucun callable open_e9/trigger_e7 (les tokens de policy sont des chaines).
    for module in _MODULES:
        source = _module_source(module)
        for callable_name in ("def open_e9", "open_e9(", "def trigger_e7", "trigger_e7("):
            assert callable_name not in source
