"""v1.3.7 — correctifs post-Mission #11 : B17 (mention ≠ défense), diversité décisionnelle,
cible du steelman, D25 `fact_source` vide, rapport terminal cohérent, taxonomie d'erreurs à trois
classes, pause récupérable / checkpoint / reprise idempotente, intégrité benchmark à la reprise,
barème de référence, pré-vol (confirmations opérateur), composition (angle du cadrage conservé).

Tous les scénarios sont **synthétiques** (positions « P-n », options « option A / B / C »,
propositions génériques « externaliser la maintenance applicative ») et **sans réseau** : faux
client structuré scriptable, faux fournisseur de recherche, erreurs de SDK imitées. Aucun texte,
aucune réponse attendue de la Mission #11 n'y figure : les tests prouvent le MÉCANISME.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from app import build_identity as bi
from app.build_identity import compute_build_identity, preflight, render_preflight
from app.config import Settings, get_settings
from app.db import Mission
from app.llm import LLMResponse, LLMUsage
from app.mission_budget import BudgetLedger
from app.mission_composition import compose
from app.mission_deliberation import (
    decisional_diversity,
    declared_stance_for,
    endorsement_of,
    find_discarded_alternative,
    is_premature_convergence,
    mention_polarity,
    orientation_groups,
    select_steelman_target,
)
from app.mission_exploration import EXPERT_SYSTEM, build_expert_prompt
from app.mission_framing import framing_summary_for_experts
from app.mission_schemas import ConfrontationOutput, ExpertOutput, FramingOutput
from app.missions import (
    RESUME_POLICY_BENCHMARK,
    RESUME_POLICY_PRODUCTION,
    checkpoint_view,
    resume_compatibility,
)
from app.provider_errors import (
    COST_KNOWN_ZERO,
    PERMANENT_PROVIDER_ERROR,
    TERMINAL_RECOVERABLE_PROVIDER_ERROR,
    TRANSIENT_PROVIDER_ERROR,
    classify_provider_error,
)
from app.structured_output import validate_with_item_tolerance
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from ui.mission_state import is_paused, is_terminal, mission_state_summary, poll_until_terminal

from tests.test_missions_deliberation import (
    THREE_DIM_FRAMING,
    DeliberationLLM,
    FakeResearchProvider,
    act,
)
from tests.test_missions_resilience import FakeProviderError, FlakyLLM
from tests.test_missions_v136 import PROPOSAL_FRAMING, _entries, _journal
from tests.test_missions_v1362 import CLEAN_SHA, OTHER_SHA, _probe, _process

_CURRENT: dict[str, Any] = {}
PROPOSAL = "externaliser la maintenance applicative"
SECRET = "sk-ant-SECRET-v137-never-persisted"


# --- Fixtures ------------------------------------------------------------------------------------
@pytest.fixture
def llm_factory() -> Callable[[], Any]:
    def factory() -> Any:
        return _CURRENT["llm"]

    return factory


@pytest.fixture
def use_llm() -> Callable[[Any], Any]:
    def _set(llm: Any) -> Any:
        _CURRENT["llm"] = llm
        return llm

    _CURRENT["llm"] = DeliberationLLM()
    return _set


@pytest.fixture
def settings_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[[str, str], None]]:
    def _set(name: str, value: str) -> None:
        monkeypatch.setenv(name, value)
        get_settings.cache_clear()

    yield _set
    get_settings.cache_clear()


@pytest.fixture
def research(monkeypatch: pytest.MonkeyPatch) -> Callable[[Any], Any]:
    def _set(provider: Any) -> Any:
        monkeypatch.setattr("app.missions.build_research_provider", lambda settings: provider)
        return provider

    return _set


@pytest.fixture(autouse=True)
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    recorded: list[float] = []
    monkeypatch.setattr("app.missions.provider_sleep", recorded.append)
    return recorded


@pytest.fixture
def git(monkeypatch: pytest.MonkeyPatch) -> Callable[[str], None]:
    """Identité simulée du processus ET du dépôt (même commit, arbre propre)."""

    def _set(commit: str) -> None:
        monkeypatch.setattr(bi, "git_probe", lambda repo_dir=None: _probe(commit, False))
        monkeypatch.setattr(bi, "_PROCESS_BUILD", _process(commit, False))

    _set(CLEAN_SHA)
    return _set


# --- Faux clients / erreurs ----------------------------------------------------------------------
class StanceLLM(DeliberationLLM):
    """Faux client dont les experts déclarent prises de position et orientation (v1.3.7)."""

    def __init__(
        self,
        *args: Any,
        stances: dict[str, list[dict[str, Any]]] | None = None,
        orientations: dict[str, dict[str, str]] | None = None,
        positions: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.stances = stances or {}
        self.orientations = orientations or {}
        self.positions = positions or {}

    def complete_structured(
        self, *, system: str, prompt: str, call_type: str, max_tokens: int
    ) -> LLMResponse:
        response = super().complete_structured(
            system=system, prompt=prompt, call_type=call_type, max_tokens=max_tokens
        )
        if call_type != "expert_tour0":
            return response
        expert_id = next(
            line.split(":", 1)[1].strip()
            for line in prompt.splitlines()
            if line.startswith("Identifiant : ")
        )
        payload = json.loads(response.text)
        if expert_id in self.positions:
            payload["position"] = self.positions[expert_id]
        if expert_id in self.stances:
            payload["proposal_stances"] = self.stances[expert_id]
        if expert_id in self.orientations:
            payload["primary_orientation"] = self.orientations[expert_id]
        return LLMResponse(
            text=json.dumps(payload, ensure_ascii=False),
            usage=response.usage,
            stop_reason=response.stop_reason,
        )


def credit_error() -> FakeProviderError:
    """Condition externe récupérable exprimée dans un 400 (sémantique fournisseur, pas HTTP)."""
    return FakeProviderError(
        400,
        "invalid_request_error",
        "Your credit balance is too low to access the API. Please purchase credits.",
    )


def spend_cap_error() -> FakeProviderError:
    return FakeProviderError(429, "rate_limit_error", "organization spend limit reached")


def permanent_error() -> FakeProviderError:
    return FakeProviderError(400, "invalid_request_error", "max_tokens: must be a positive integer")


def _post(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload = {"input_type": "problem", "input_text": "entrée synthétique v137"}
    payload.update(overrides)
    response = client.post("/missions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _get(client: TestClient, mission_id: int) -> dict[str, Any]:
    return dict(client.get(f"/missions/{mission_id}").json())


def _resume(client: TestClient, mission_id: int) -> Any:
    return client.post(f"/missions/{mission_id}/resume")


def _checkpoint_raw(session_factory: sessionmaker[Session], mission_id: int) -> str:
    with session_factory() as session:
        row = session.get(Mission, mission_id)
        assert row is not None
        return str(row.checkpoint_json)


def _paused_at_consolidation(
    use_llm: Callable[[Any], Any], inner: DeliberationLLM | None = None
) -> FlakyLLM:
    return use_llm(FlakyLLM(inner or DeliberationLLM(), plan={"consolidation": [credit_error()]}))


# =================================================================================================
# §10 — Taxonomie : transitoire / terminale récupérable / terminale (sémantique fournisseur)
# =================================================================================================
def test_taxonomy_reads_provider_semantics_not_only_http_status() -> None:
    recoverable = classify_provider_error(credit_error())
    assert recoverable.category == TERMINAL_RECOVERABLE_PROVIDER_ERROR
    assert recoverable.retryable is False
    assert recoverable.recoverable is True
    assert recoverable.cost_semantics == COST_KNOWN_ZERO  # rejet d'admission explicite
    # Même statut 400, même type : une requête INVALIDE reste permanente.
    assert classify_provider_error(permanent_error()).category == PERMANENT_PROVIDER_ERROR
    # 402 et types explicites de facturation / quota : récupérables quel que soit le message.
    assert classify_provider_error(FakeProviderError(402)).recoverable is True
    assert classify_provider_error(FakeProviderError(400, "billing_error")).recoverable is True
    assert (
        classify_provider_error(FakeProviderError(429, "enforced_spend_limit_reached")).recoverable
        is True
    )
    # 429 : plafond de dépense sans Retry-After → récupérable ; débit avec Retry-After →
    # transitoire.
    assert classify_provider_error(spend_cap_error()).recoverable is True
    throttled = FakeProviderError(429, "rate_limit_error", "spend limit", retry_after="2")
    assert classify_provider_error(throttled).category == TRANSIENT_PROVIDER_ERROR
    burst = FakeProviderError(429, "rate_limit_error", "tokens per minute exceeded")
    assert classify_provider_error(burst).category == TRANSIENT_PROVIDER_ERROR
    # 403 à vocabulaire de facturation → récupérable ; 403 ordinaire → permanent.
    billing_403 = FakeProviderError(403, "permission_error", "billing account suspended")
    assert classify_provider_error(billing_403).recoverable is True
    plain_403 = FakeProviderError(403, "permission_error", "forbidden")
    assert classify_provider_error(plain_403).category == PERMANENT_PROVIDER_ERROR
    # Drapeau explicite d'un adaptateur : prime sur la règle générique, dans les deux sens.
    flagged = permanent_error()
    flagged.recoverable_external_condition = True  # type: ignore[attr-defined]
    assert classify_provider_error(flagged).recoverable is True
    unflagged = credit_error()
    unflagged.recoverable_external_condition = False  # type: ignore[attr-defined]
    assert classify_provider_error(unflagged).category == PERMANENT_PROVIDER_ERROR


def test_transient_error_is_retried_and_mission_completes(
    client: TestClient, use_llm: Callable[..., Any], sleeps: list[float]
) -> None:
    inner = DeliberationLLM()
    flaky = use_llm(
        FlakyLLM(
            inner,
            plan={
                "steelman": [FakeProviderError(429, "rate_limit_error", "busy", retry_after="1")]
            },
        )
    )
    mission = _post(client, declared_class="structurante")
    assert mission["status"] == "candidate"
    assert mission["checkpoint"] is None
    failed = _entries(client, mission["id"], "call_attempt_failed")
    assert len(failed) == 1
    assert failed[0]["payload"]["will_retry"] is True
    assert failed[0]["payload"]["category"] == TRANSIENT_PROVIDER_ERROR
    assert sleeps == [1.0]
    assert [a["call_type"] for a in flaky.attempts].count("steelman") == 2


def test_terminal_error_fails_without_checkpoint(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    use_llm(FlakyLLM(DeliberationLLM(), plan_all={"consolidation": permanent_error()}))
    mission = _post(client)
    assert mission["status"] == "failed"
    assert mission["failure"]["category"] == PERMANENT_PROVIDER_ERROR
    assert mission["failure"]["recoverable"] is False
    assert mission["checkpoint"] is None
    assert mission["resume_available"] is False
    assert _resume(client, mission["id"]).status_code == 409
    assert _resume(client, mission["id"]).json()["detail"]["reason"] == "not_paused"


# =================================================================================================
# §8-§11 — Pause récupérable, checkpoint, rapport d'interruption
# =================================================================================================
def test_terminal_recoverable_error_pauses_with_checkpoint_not_failure(
    client: TestClient, use_llm: Callable[..., Any], session_factory: sessionmaker[Session]
) -> None:
    flaky = _paused_at_consolidation(use_llm)
    mission = _post(client)
    assert mission["status"] == "paused_recoverable"
    assert mission["stop_reason"] == "interrupted_recoverable"
    assert mission["failure"]["category"] == TERMINAL_RECOVERABLE_PROVIDER_ERROR
    assert mission["failure"]["recoverable"] is True
    assert "resume" in mission["failure"]["required_intervention"]
    assert mission["resume_available"] is True
    assert mission["recommendation"] is None
    # Aucune relance : une seule tentative sur l'appel interrompu.
    assert [a["call_type"] for a in flaky.attempts].count("consolidation") == 1
    types = [e["entry_type"] for e in _journal(client, mission["id"])]
    assert "paused_recoverable" in types
    assert "failed_provider_call" not in types
    assert "failed" not in types
    # Checkpoint : dernière étape durable, appels validés, budget, identité, intervention.
    cp = mission["checkpoint"]
    assert cp["version"] == 1
    assert cp["interrupted_step"] == "consolidation"
    assert cp["last_durable_step"] == cp["steps_done"][-1]
    assert cp["last_durable_step"].startswith("revision")
    assert "consolidation" not in cp["steps_done"]
    assert cp["calls_count"] == mission["llm_calls_used"] == cp["logical_calls_completed"]
    assert cp["ledger_at_pause"]["calls_used"] == mission["llm_calls_used"]
    assert cp["budget_at_pause"]["cost_eur"] == pytest.approx(mission["cost_eur"])
    assert cp["identity"]["model"] == get_settings().anthropic_model
    assert cp["identity"]["provider_adapter"] == "anthropic"
    assert cp["policy"] == RESUME_POLICY_PRODUCTION
    assert cp["interruption"]["category"] == TERMINAL_RECOVERABLE_PROVIDER_ERROR
    assert "calls" not in cp  # la vue API ne porte pas le contenu des appels
    raw = json.loads(_checkpoint_raw(session_factory, mission["id"]))
    assert len(raw["calls"]) == mission["llm_calls_used"]
    assert all({"key", "response", "ledger_after"} <= set(c) for c in raw["calls"])
    view = checkpoint_view(raw)
    assert view is not None
    assert view["calls_count"] == len(raw["calls"])
    # Rapport d'interruption (§7 / §11) : cause réelle, étape atteinte, reprise ; pas une cause
    # terminale, pas une délibération close, aucune étape ultérieure exercée.
    stop = mission["deliberation"]["stop"]
    assert stop["reason"] == "interrupted_recoverable"
    assert stop["terminal_failure_reason"] == ""
    assert stop["interrupted_step"] == "consolidation"
    assert stop["paused_recoverable"] is True
    assert stop["resume_possible"] is True
    assert "consolidation" not in stop["steps_done"]
    assert mission["deliberation"]["comparison"] == {}
    assert mission["deliberation"]["gate"] == {}
    report = mission["report"]
    assert report["status"] == "paused_recoverable"
    pause = report["pause"]
    assert pause["interrupted_step"] == "consolidation"
    assert pause["resume_possible"] is True
    assert pause["checkpoint"]["calls_count"] == mission["llm_calls_used"]
    assert pause["budget_consumed"]["llm_calls_used"] == mission["llm_calls_used"]
    assert pause["model"] == get_settings().anthropic_model
    md = client.get(f"/missions/{mission['id']}/report/markdown")
    assert md.status_code == 200
    text = md.json()["markdown"]
    assert "MISSION EN PAUSE RÉCUPÉRABLE" in text
    assert "## 0. Interruption récupérable" in text
    assert "Reprise possible : **oui**" in text
    assert "`consolidation`" in text
    # Ni succès ni échec : aucune action CEO possible ; l'interface ne l'attend plus.
    assert client.post(f"/missions/{mission['id']}/approve").status_code == 409
    summary = mission_state_summary(mission)
    assert summary["kind"] == "paused"
    assert any("Reprise possible : oui" in d for d in summary["details"])
    assert is_terminal("paused_recoverable")
    assert is_paused("paused_recoverable")
    _polled, polls, terminal = poll_until_terminal(
        lambda: mission, sleeper=lambda s: None, interval_seconds=0, max_polls=5
    )
    assert (polls, terminal) == (1, True)


def test_pause_during_steelman_is_reported_as_interrupted_not_not_required(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    use_llm(FlakyLLM(DeliberationLLM(), plan={"steelman": [credit_error()]}))
    mission = _post(client, declared_class="structurante")
    assert mission["status"] == "paused_recoverable"
    st = mission["deliberation"]["steelman"]
    assert st["required"] is True
    assert st["status"] == "interrupted_recoverable"
    assert st["status"] != "not_required"
    assert "steelman" not in mission["deliberation"]["steps_done"]
    stop = mission["deliberation"]["stop"]
    assert stop["interrupted_step"] == "steelman"
    assert stop["terminal_failure_reason"] == ""
    assert "steelman_interrupted_recoverable" in stop["degraded_steps"]
    assert mission["deliberation"]["research"] == []
    assert mission["deliberation"]["revisions"] == []
    text = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "**interrompu**" in text
    assert "Non requis pour cette classe" not in text


# =================================================================================================
# §8-§9, §20 — Reprise idempotente : rejeu sans double appel, budget préservé, E2E complet
# =================================================================================================
def test_e2e_pause_then_resume_replays_validated_calls_and_completes_normally(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    # Témoin : même mission sans interruption.
    control_inner = use_llm(DeliberationLLM())
    control = _post(client)
    assert control["status"] == "candidate"
    control_done = len(_entries(client, control["id"], "call_done"))
    # Mission interrompue à la consolidation (crédit), puis condition levée, puis reprise.
    inner = DeliberationLLM()
    flaky = _paused_at_consolidation(use_llm, inner)
    paused = _post(client)
    assert paused["status"] == "paused_recoverable"
    calls_before = len(inner.calls)
    attempts_before = len(flaky.attempts)
    resumed = _resume(client, paused["id"])
    assert resumed.status_code == 200, resumed.text
    mission = resumed.json()
    assert mission["id"] == paused["id"]
    assert mission["status"] == "candidate"
    assert mission["recommendation"]["status"] == "produced"
    assert mission["deliberation"]["gate"]
    assert mission["checkpoint"] is None or mission["resume_available"] is False
    assert mission["stop_reason"] == ""
    # Aucun double appel : les appels validés ont été REJOUÉS (jamais renvoyés au fournisseur).
    assert len(inner.calls) == len(control_inner.calls)
    assert len(flaky.attempts) == attempts_before + (len(control_inner.calls) - calls_before)
    replayed = _entries(client, mission["id"], "call_replayed")
    assert len(replayed) == calls_before
    assert all(e["payload"]["provider_call_made"] is False for e in replayed)
    assert all(e["payload"]["replayed_from_checkpoint"] is True for e in replayed)
    assert len(_entries(client, mission["id"], "call_done")) == control_done
    resumed_entries = _entries(client, mission["id"], "resumed")
    assert len(resumed_entries) == 1
    assert resumed_entries[0]["payload"]["calls_to_replay"] == calls_before
    assert resumed_entries[0]["payload"]["compatibility"]["compatible"] is True
    assert _entries(client, mission["id"], "checkpoint_replay_divergence") == []
    # Budget consommé préservé : identique au témoin (appels logiques, coût).
    assert mission["llm_calls_used"] == control["llm_calls_used"]
    assert mission["cost_eur"] == pytest.approx(control["cost_eur"])
    assert mission["input_tokens"] == control["input_tokens"]
    stop = mission["deliberation"]["stop"]
    assert stop["paused_recoverable"] is False
    assert stop["terminal_failure_reason"] == ""
    # Journal append-only : l'exécution d'origine reste lisible avant la reprise.
    types = [e["entry_type"] for e in _journal(client, mission["id"])]
    assert types.index("paused_recoverable") < types.index("resumed")
    assert types.count("report_ready") == 2
    # Idempotence : une mission terminée ne se reprend pas.
    assert _resume(client, mission["id"]).status_code == 409


def test_resume_replays_research_results_without_new_search(
    client: TestClient, use_llm: Callable[..., Any], research: Callable[[Any], Any]
) -> None:
    provider = research(FakeResearchProvider("found"))
    question = "Q1 synthétique : quelle norme publique s'applique ?"
    inner = DeliberationLLM(
        confrontation={
            "P1": {
                "acts": [
                    {
                        **act("P2", "critique", "fact", "départage", fact_question=question),
                        "fact_source": "external",
                    }
                ]
            }
        }
    )
    _paused_at_consolidation(use_llm, inner)
    paused = _post(client)
    assert paused["status"] == "paused_recoverable"
    assert provider.questions == [question]
    assert paused["checkpoint"]["research_count"] == 1
    resumed = _resume(client, paused["id"])
    assert resumed.status_code == 200, resumed.text
    assert provider.questions == [question]  # aucune seconde recherche
    replayed = _entries(client, paused["id"], "call_replayed")
    assert any(e["payload"]["call_type"] == "research" for e in replayed)
    assert resumed.json()["status"] == "candidate"


def test_second_recoverable_interruption_pauses_again_with_updated_checkpoint(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    use_llm(
        FlakyLLM(
            DeliberationLLM(),
            plan={"consolidation": [credit_error()], "synthesis": [spend_cap_error()]},
        )
    )
    paused = _post(client)
    assert paused["checkpoint"]["interrupted_step"] == "consolidation"
    again = _resume(client, paused["id"]).json()
    assert again["status"] == "paused_recoverable"
    assert again["checkpoint"]["interrupted_step"] == "synthese"
    assert again["checkpoint"]["resume_count"] == 1
    assert again["checkpoint"]["calls_count"] == again["llm_calls_used"]
    final = _resume(client, paused["id"]).json()
    assert final["status"] == "candidate"
    assert len(_entries(client, paused["id"], "resumed")) == 2


# =================================================================================================
# §12-§13 — Identité à la reprise : refus explicite, jamais de repli
# =================================================================================================
def _identity(settings: Settings, commit: str = CLEAN_SHA) -> Any:
    return compute_build_identity(
        settings, process=_process(commit), filesystem=_probe(commit, False)
    )


def test_resume_compatibility_matrix() -> None:
    settings = Settings(anthropic_api_key="")
    identity = _identity(settings)
    expected = {
        "process_commit": CLEAN_SHA,
        "provider_adapter": "anthropic",
        "provider_sdk_version": identity.provider_sdk_version,
        "model": settings.anthropic_model,
        "mission_config_fingerprint": identity.mission_config_fingerprint,
        "reasoning_policy_fingerprint": identity.reasoning_policy_fingerprint,
        "expected_freeze": CLEAN_SHA,
    }
    for policy in (RESUME_POLICY_BENCHMARK, RESUME_POLICY_PRODUCTION):
        same = resume_compatibility(expected, identity, settings, policy)
        assert same["compatible"] is True, same
        assert same["mismatches"] == []
        # Autre modèle : refus dans les deux politiques (aucun repli multi-modèle).
        other_model = resume_compatibility(
            {**expected, "model": "autre-modele"}, identity, settings, policy
        )
        assert other_model["compatible"] is False
        assert [m["field"] for m in other_model["mismatches"]] == ["model"]
        # Autre adaptateur fournisseur : refus dans les deux politiques.
        other_provider = resume_compatibility(
            {**expected, "provider_adapter": "autre"}, identity, settings, policy
        )
        assert other_provider["compatible"] is False
        # Autre configuration intellectuelle : refus dans les deux politiques.
        other_config = resume_compatibility(
            {**expected, "mission_config_fingerprint": "deadbeef"}, identity, settings, policy
        )
        assert other_config["compatible"] is False
    # Commit du processus différent : refus en benchmark, avertissement en production.
    other_commit = {**expected, "process_commit": OTHER_SHA, "expected_freeze": OTHER_SHA}
    bench = resume_compatibility(other_commit, identity, settings, RESUME_POLICY_BENCHMARK)
    assert bench["compatible"] is False
    assert {m["field"] for m in bench["mismatches"]} == {"process_commit", "benchmark"}
    prod = resume_compatibility(other_commit, identity, settings, RESUME_POLICY_PRODUCTION)
    assert prod["compatible"] is True
    assert [w["field"] for w in prod["warnings"]] == ["process_commit"]
    # Benchmark : un arbre modifié refuse la reprise même à commit identique (D20 / D26).
    dirty = compute_build_identity(
        settings, process=_process(CLEAN_SHA, True), filesystem=_probe(CLEAN_SHA, True)
    )
    assert (
        resume_compatibility(expected, dirty, settings, RESUME_POLICY_BENCHMARK)["compatible"]
        is False
    )
    assert (
        resume_compatibility(expected, dirty, settings, RESUME_POLICY_PRODUCTION)["compatible"]
        is True
    )


def test_resume_refused_when_model_changed_then_allowed_when_restored(
    client: TestClient, use_llm: Callable[..., Any], settings_env: Callable[[str, str], None]
) -> None:
    _paused_at_consolidation(use_llm)
    paused = _post(client)
    original_model = paused["checkpoint"]["identity"]["model"]
    settings_env("ANTHROPIC_MODEL", "autre-modele-epingle")
    refused = _resume(client, paused["id"])
    assert refused.status_code == 409, refused.text
    detail = refused.json()["detail"]
    assert detail["reason"] == "identity_mismatch"
    fields = {m["field"] for m in detail["compatibility"]["mismatches"]}
    assert "model" in fields
    assert _get(client, paused["id"])["status"] == "paused_recoverable"
    refusals = _entries(client, paused["id"], "resume_refused")
    assert len(refusals) == 1
    assert refusals[0]["payload"]["reason"] == "identity_mismatch"
    # Aucun appel, aucun repli : la mission n'a pas bougé.
    assert _get(client, paused["id"])["llm_calls_used"] == paused["llm_calls_used"]
    settings_env("ANTHROPIC_MODEL", original_model)
    ok = _resume(client, paused["id"])
    assert ok.status_code == 200, ok.text
    assert ok.json()["status"] == "candidate"


def test_benchmark_resume_requires_same_freeze_and_never_falls_back(
    client: TestClient, use_llm: Callable[..., Any], git: Callable[[str], None]
) -> None:
    _paused_at_consolidation(use_llm)
    paused = _post(client, expected_freeze=CLEAN_SHA)
    assert paused["status"] == "paused_recoverable"
    assert paused["checkpoint"]["policy"] == RESUME_POLICY_BENCHMARK
    assert paused["checkpoint"]["identity"]["expected_freeze"] == CLEAN_SHA
    # Le serveur redémarre sur un autre commit : reprise refusée (D20 / D26 jamais contournés).
    git(OTHER_SHA)
    refused = _resume(client, paused["id"])
    assert refused.status_code == 409
    fields = {m["field"] for m in refused.json()["detail"]["compatibility"]["mismatches"]}
    assert {"process_commit", "benchmark"} <= fields
    assert _get(client, paused["id"])["status"] == "paused_recoverable"
    # Même freeze, même modèle, même fournisseur, même configuration : reprise admise.
    git(CLEAN_SHA)
    ok = _resume(client, paused["id"])
    assert ok.status_code == 200, ok.text
    assert ok.json()["status"] == "candidate"
    resumed = _entries(client, paused["id"], "resumed")[0]["payload"]
    assert resumed["policy"] == RESUME_POLICY_BENCHMARK


def test_secrets_never_reach_checkpoint_journal_or_report(
    client: TestClient,
    use_llm: Callable[..., Any],
    settings_env: Callable[[str, str], None],
    session_factory: sessionmaker[Session],
) -> None:
    settings_env("ANTHROPIC_API_KEY", SECRET)
    _paused_at_consolidation(use_llm)
    paused = _post(client)
    assert paused["status"] == "paused_recoverable"
    assert SECRET not in _checkpoint_raw(session_factory, paused["id"])
    assert SECRET not in json.dumps(paused, ensure_ascii=False, default=str)
    assert SECRET not in json.dumps(_journal(client, paused["id"]), ensure_ascii=False)
    assert SECRET not in client.get(f"/missions/{paused['id']}/report/markdown").json()["markdown"]
    ok = _resume(client, paused["id"])
    assert ok.status_code == 200
    assert SECRET not in json.dumps(_journal(client, paused["id"]), ensure_ascii=False)


def test_budget_ledger_state_roundtrip_is_exact() -> None:
    ledger = BudgetLedger(
        max_calls=10, max_cost_eur=2.0, price_in_per_mtok=3.0, price_out_per_mtok=15.0
    )
    ledger.record(LLMUsage(1000, 500))
    ledger.record_uncertain_attempt(0.05, call_type="x", logical_call_id="LC-2", attempt=1)
    ledger.raise_caps(12, 3.0)
    state = ledger.dump_state()
    other = BudgetLedger(
        max_calls=1, max_cost_eur=0.1, price_in_per_mtok=3.0, price_out_per_mtok=15.0
    )
    other.load_state(json.loads(json.dumps(state)))
    assert other.snapshot() == ledger.snapshot()


# =================================================================================================
# §3 / B17 — mention ≠ analyse ≠ critique ≠ défense
# =================================================================================================
def test_mention_to_reject_or_defer_is_not_an_endorsement() -> None:
    rejecting = f"Il faut écarter l'idée d'{PROPOSAL} : trop risqué à ce stade."
    deferring = f"{PROPOSAL.capitalize()} serait prématuré ; construire d'abord un socle."
    plain = f"Nous recommandons d'{PROPOSAL} dès le prochain trimestre."
    assert mention_polarity(PROPOSAL, rejecting) == "negative"
    assert mention_polarity(PROPOSAL, deferring) == "negative"
    assert mention_polarity(PROPOSAL, plain) == "mention"
    assert mention_polarity(PROPOSAL, "position sans rapport : construire") == "absent"
    # Sans déclaration : le repli lexical est prudent (mention négative ≠ défense).
    assert endorsement_of(PROPOSAL, {"position": rejecting})["defends"] is False
    assert endorsement_of(PROPOSAL, {"position": rejecting})["evidence"] == "lexical_negative"
    assert endorsement_of(PROPOSAL, {"position": plain})["defends"] is True
    assert endorsement_of(PROPOSAL, {"position": plain})["evidence"] == "lexical_mention"
    # Avec déclaration : autoritaire, quel que soit le texte de la position.
    for stance in ("reject", "defer", "critique", "analyse", "not_addressed"):
        verdict = endorsement_of(
            PROPOSAL,
            {"position": plain, "proposal_stances": [{"proposal": PROPOSAL, "stance": stance}]},
        )
        assert verdict == {"defends": False, "evidence": "declared", "stance": stance}
    for stance in ("defend", "conditional"):
        verdict = endorsement_of(
            PROPOSAL,
            {
                "position": rejecting,
                "proposal_stances": [{"proposal": PROPOSAL, "stance": stance}],
            },
        )
        assert verdict["defends"] is True
        assert verdict["evidence"] == "declared"
    assert declared_stance_for(PROPOSAL, [{"proposal": "autre sujet", "stance": "defend"}]) is None


def test_find_discarded_alternative_uses_declared_stances_then_prudent_lexical_fallback() -> None:
    proposals = PROPOSAL_FRAMING["explicit_proposals"]
    options = [
        {"option_id": "E2-O1", "expert_id": "E2", "label": PROPOSAL, "kind": "buy", "summary": ""}
    ]
    # Toutes les positions MENTIONNENT la proposition, aucune ne la défend → candidate steelman.
    positions: list[dict[str, Any]] = [
        {"label": "P1", "position": f"écarter {PROPOSAL} : trop risqué"},
        {
            "label": "P2",
            "position": f"{PROPOSAL} mérite examen",
            "proposal_stances": [{"proposal": PROPOSAL, "stance": "analyse"}],
        },
        {
            "label": "P3",
            "position": f"nous recommandons d'{PROPOSAL}",  # texte positif…
            "proposal_stances": [{"proposal": PROPOSAL, "stance": "reject"}],  # …mais rejet déclaré
        },
    ]
    found = find_discarded_alternative(
        proposals=proposals, option_groups=[], options=options, positions=positions, request_text=""
    )
    assert found is not None
    assert found["endorsed_by"] == []
    assert found["stances"]["P1"] == {"evidence": "lexical_negative", "stance": ""}
    assert found["stances"]["P2"] == {"evidence": "declared", "stance": "analyse"}
    assert found["stances"]["P3"] == {"evidence": "declared", "stance": "reject"}
    assert sorted(found["mentioned_without_defending"]) == ["P1", "P2", "P3"]
    # Une défense déclarée (même conditionnelle) suffit : plus d'alternative écartée.
    defended: list[dict[str, Any]] = [
        *positions,
        {
            "label": "P4",
            "position": "position sans mention",
            "proposal_stances": [{"proposal": PROPOSAL, "stance": "conditional"}],
        },
    ]
    assert (
        find_discarded_alternative(
            proposals=proposals,
            option_groups=[],
            options=options,
            positions=defended,
            request_text="",
        )
        is None
    )
    # Déterminisme : même entrée, même sortie.
    again = find_discarded_alternative(
        proposals=proposals, option_groups=[], options=options, positions=positions, request_text=""
    )
    assert again == found


def test_e2e_proposal_mentioned_to_reject_is_steelmanned_as_discarded_alternative(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    # Unanimité argumentative ; chaque position PARLE de la proposition pour l'écarter (mention
    # négative sans déclaration, ou rejet déclaré malgré un texte positif) : personne ne la défend.
    use_llm(
        StanceLLM(
            framing=PROPOSAL_FRAMING,
            relation="identical",
            positions={
                "E1": f"écarter {PROPOSAL} : construire un socle interne d'abord",
                "E2": f"{PROPOSAL} est une piste que nous recommandons de reporter",
                "E3": f"nous pourrions {PROPOSAL} plus tard",
            },
            stances={"E3": [{"proposal": PROPOSAL, "stance": "defer", "reason": "trop tôt"}]},
        )
    )
    mission = _post(client, declared_class="structurante")
    st = mission["deliberation"]["steelman"]
    assert st["required"] is True
    assert st["mode"] == "discarded_alternative"
    assert st["alternative"]["label"] == PROPOSAL
    selected = _entries(client, mission["id"], "steelman_alternative_selected")[0]["payload"]
    assert selected["endorsed_by"] == []
    target = _entries(client, mission["id"], "steelman_target_selected")[0]["payload"]
    assert target["mode"] == "discarded_alternative"
    assert target["alternative_stances"]["P3"] == {"evidence": "declared", "stance": "defer"}
    assert target["alternative_stances"]["P1"]["evidence"] == "lexical_negative"
    assert target["candidates_considered"][0]["mode"] == "discarded_alternative"
    # Aucun désaccord fabriqué : la seule objection nouvelle est la critique du steelman.
    acts = list(mission["deliberation"]["confrontation"]["objections"])
    assert all(o["act"] == "steelman_critique" for o in acts)


def test_e2e_declared_defense_means_no_discarded_alternative(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    use_llm(
        StanceLLM(
            framing=PROPOSAL_FRAMING,
            relation="identical",
            stances={"E2": [{"proposal": PROPOSAL, "stance": "defend", "reason": "moins cher"}]},
        )
    )
    mission = _post(client, declared_class="structurante")
    st = mission["deliberation"]["steelman"]
    assert st["mode"] == "dominant_position"
    assert st["target"] == "P1"
    target = _entries(client, mission["id"], "steelman_target_selected")[0]["payload"]
    assert target["candidates_considered"][0] == {
        "mode": "discarded_alternative",
        "label": None,
        "found": False,
    }
    assert _entries(client, mission["id"], "steelman_alternative_selected") == []


def test_framing_dossier_and_expert_contract_carry_proposals_and_stances() -> None:
    dossier = framing_summary_for_experts(FramingOutput.model_validate(PROPOSAL_FRAMING))
    assert "Propositions explicites de la demande" in dossier
    assert PROPOSAL in dossier
    assert "portée par demandeur" in dossier
    assert "Propositions explicites" not in framing_summary_for_experts(
        FramingOutput.model_validate(THREE_DIM_FRAMING)
    )
    assert "proposal_stances" in EXPERT_SYSTEM
    assert "primary_orientation" in EXPERT_SYSTEM
    assert "n'est pas la défendre" in EXPERT_SYSTEM
    # Sorties antérieures (sans les nouveaux champs) restent valides : repli, jamais une invention.
    legacy = ExpertOutput.model_validate({"position": "p"})
    assert legacy.proposal_stances == []
    assert legacy.primary_orientation is None


# =================================================================================================
# §4 — diversité argumentative ≠ diversité décisionnelle ; §5 — cible du steelman
# =================================================================================================
def test_decisional_diversity_is_distinct_from_argumentative_divergence() -> None:
    same = [
        {"expert_id": "E1", "kind": "build", "label": "option A"},
        {"expert_id": "E2", "kind": "build", "label": "option A (variante)"},
        {"expert_id": "E3", "kind": "build", "label": ""},
    ]
    assert orientation_groups(same) == [["E1", "E2", "E3"]]
    assert decisional_diversity(same) == 0.0
    mixed = [*same[:2], {"expert_id": "E3", "kind": "wait", "label": "option C"}]
    assert orientation_groups(mixed) == [["E1", "E2"], ["E3"]]
    assert decisional_diversity(mixed) == pytest.approx(0.333, abs=1e-3)
    assert decisional_diversity(same[:1]) is None  # inconnue, jamais inventée
    assert decisional_diversity([]) is None
    # Convergence décisionnelle avérée → contrôle même avec objections / raisons divergentes.
    assert is_premature_convergence(
        effective_class="importante",
        divergence_index=0.83,
        objection_count=4,
        decisional_diversity_index=0.0,
    )
    # Diversité décisionnelle réelle après une contradiction réelle : convergence légitime, rien.
    assert not is_premature_convergence(
        effective_class="importante",
        divergence_index=0.5,
        objection_count=2,
        decisional_diversity_index=0.333,
    )
    # Classe courante : jamais concernée.
    assert not is_premature_convergence(
        effective_class="courante",
        divergence_index=0.0,
        objection_count=0,
        decisional_diversity_index=0.0,
    )
    # Sans orientation déclarée : règle historique inchangée.
    assert is_premature_convergence(
        effective_class="importante", divergence_index=0.0, objection_count=0
    )
    assert not is_premature_convergence(
        effective_class="importante", divergence_index=0.0, objection_count=1
    )


def test_steelman_target_selection_is_prioritised_and_deterministic() -> None:
    ids = ["E1", "E2", "E3"]
    alt = {"label": PROPOSAL, "kind": "buy"}
    first = select_steelman_target(
        answered_ids=ids,
        dominant=["E1", "E2"],
        orientation_clusters=[["E1", "E2"], ["E3"]],
        alternative=alt,
    )
    assert first["mode"] == "discarded_alternative"
    minority = select_steelman_target(
        answered_ids=ids,
        dominant=["E1", "E2"],
        orientation_clusters=[["E1", "E2"], ["E3"]],
        alternative=None,
    )
    assert (minority["mode"], minority["target_expert"]) == ("minority_position", "E3")
    assert [c["mode"] for c in minority["candidates_considered"]] == [
        "discarded_alternative",
        "minority_position",
    ]
    # Pas de groupe dominant d'au moins deux : pas de minorité « à risque » → position dominante.
    dominant = select_steelman_target(
        answered_ids=ids,
        dominant=["E1"],
        orientation_clusters=[["E1"], ["E2"], ["E3"]],
        alternative=None,
    )
    assert (dominant["mode"], dominant["target_expert"]) == ("dominant_position", "E1")
    # Sans orientation déclarée : règle historique (position dominante).
    legacy = select_steelman_target(
        answered_ids=ids, dominant=["E2", "E1"], orientation_clusters=[], alternative=None
    )
    assert (legacy["mode"], legacy["target_expert"]) == ("dominant_position", "E2")
    assert (
        select_steelman_target(
            answered_ids=ids, dominant=["E2", "E1"], orientation_clusters=[], alternative=None
        )
        == legacy
    )


def test_e2e_decisional_convergence_requires_steelman_without_fabricating_disagreement(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    same = {"kind": "build", "label": "option A"}
    llm = use_llm(
        StanceLLM(relation="different", orientations={"E1": same, "E2": same, "E3": same})
    )
    mission = _post(client, declared_class="importante")
    carto = mission["cartography"]
    assert carto["divergence_index"] > 0.0  # raisons divergentes…
    assert carto["decisional_diversity_index"] == 0.0  # …orientation unique
    assert carto["decisional_convergence"] is True
    assert carto["orientation_clusters"] == [["E1", "E2", "E3"]]
    st = mission["deliberation"]["steelman"]
    assert st["required"] is True
    assert st["reason"] == "convergence décisionnelle malgré la diversité des raisons"
    assert st["mode"] == "dominant_position"
    assert [c["call_type"] for c in llm.calls].count("steelman") == 1
    # Aucun faux désaccord : aucun acte de confrontation n'a été inventé.
    objections = mission["deliberation"]["confrontation"]["objections"]
    assert all(o["act"] == "steelman_critique" for o in objections)
    # Témoin : orientations réellement différentes → aucune convergence prématurée (importante).
    llm = use_llm(
        StanceLLM(
            relation="different",
            orientations={"E1": same, "E2": same, "E3": {"kind": "wait", "label": "option C"}},
        )
    )
    control = _post(client, declared_class="importante")
    assert control["cartography"]["decisional_diversity_index"] > 0.0
    assert control["deliberation"]["steelman"]["required"] is False
    assert control["deliberation"]["steelman"]["status"] == "not_required"
    assert "steelman" not in [c["call_type"] for c in llm.calls]


def test_e2e_legitimate_convergence_after_real_contradiction_is_not_flagged(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    same = {"kind": "build", "label": "option A"}
    use_llm(
        StanceLLM(
            relation="identical",
            orientations={"E1": same, "E2": same, "E3": {"kind": "wait", "label": "option C"}},
            confrontation={"P3": {"acts": [act("P1", "critique", "solution", "objection réelle")]}},
            revision={
                "P1": {
                    "decision": "maintain",
                    "reason": "objection examinée",
                    "triggered_by": ["OBJ-1"],
                }
            },
        )
    )
    mission = _post(client, declared_class="importante")
    stop = mission["deliberation"]["stop"]
    assert stop["terminal_failure_reason"] == ""
    assert stop["reason"] in {"converged", "residual_only", "no_new_information"}
    assert not any(w.startswith("checkpoint") for w in stop["warnings"])
    assert mission["deliberation"]["steelman"]["required"] is False
    objections = mission["deliberation"]["confrontation"]["objections"]
    assert len(objections) == 1  # la contradiction réelle, rien d'ajouté
    assert mission["recommendation"]["status"] == "produced"


def test_e2e_minority_orientation_is_the_steelman_target(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    same = {"kind": "build", "label": "option A"}
    use_llm(
        StanceLLM(
            relation="identical",
            orientations={"E1": same, "E2": same, "E3": {"kind": "wait", "label": "option C"}},
        )
    )
    mission = _post(client, declared_class="structurante")
    st = mission["deliberation"]["steelman"]
    assert st["mode"] == "minority_position"
    assert st["target"] == "P3"
    assert st["contradictor"] in {"P1", "P2"}
    target = _entries(client, mission["id"], "steelman_target_selected")[0]["payload"]
    assert target["reason"].startswith("orientation minoritaire")
    assert target["target"] == "P3"


# =================================================================================================
# §6 / D25 — `fact_source` vide : absence, pas un littéral inconnu
# =================================================================================================
def test_empty_fact_source_is_normalised_unknown_literal_still_rejected() -> None:
    data = {
        "acts": [
            {**act("P2", "critique", "fact", "acte 1", fact_question="q1"), "fact_source": ""},
            {
                **act("P2", "critique", "fact", "acte 2", fact_question="q2"),
                "fact_source": "public",
            },
            {**act("P2", "critique", "fact", "acte 3", fact_question="q3"), "fact_source": None},
            {
                **act("P2", "critique", "fact", "acte 4", fact_question="q4"),
                "fact_source": " internal ",
            },
            act("P2", "complement", "other", "acte 5"),
        ]
    }
    output, rejected, error = validate_with_item_tolerance(data, ConfrontationOutput)
    assert isinstance(output, ConfrontationOutput)
    assert error == ""
    assert [a.text for a in output.acts] == ["acte 1", "acte 3", "acte 4", "acte 5"]
    assert [a.fact_source for a in output.acts] == ["either", "either", "internal", "either"]
    assert len(rejected) == 1
    assert rejected[0]["index"] == 1
    assert rejected[0]["literal_received"] == "public"


# =================================================================================================
# §7 — rapport terminal cohérent sur les chemins terminaux principaux
# =================================================================================================
def test_terminal_reporting_normal_candidate(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    use_llm(DeliberationLLM())
    mission = _post(client, declared_class="structurante")
    stop = mission["deliberation"]["stop"]
    assert mission["status"] == "candidate"
    assert (stop["terminal_failure_reason"], stop["interrupted_step"]) == ("", "")
    assert stop["paused_recoverable"] is False
    st = mission["deliberation"]["steelman"]
    assert st["status"] in {"accepted", "accepted_partial"}
    assert st["status"] != "pending"
    assert mission["report"]["pause"] is None


def test_terminal_reporting_provider_failure_during_steelman(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    use_llm(FlakyLLM(DeliberationLLM(), plan_all={"steelman": permanent_error()}))
    mission = _post(client, declared_class="structurante")
    assert mission["status"] == "failed"
    stop = mission["deliberation"]["stop"]
    assert stop["terminal_failure_reason"] == "permanent_provider_error"
    assert stop["reason"] == "permanent_provider_error"
    assert stop["interrupted_step"] == "steelman"
    assert stop["paused_recoverable"] is False
    st = mission["deliberation"]["steelman"]
    assert st["required"] is True
    assert st["status"] == "interrupted_provider_failure"
    assert "steelman" not in stop["steps_done"]
    assert "steelman_interrupted_provider_failure" in stop["degraded_steps"]
    assert mission["deliberation"]["revisions"] == []
    assert mission["deliberation"]["gate"] == {}
    assert mission["recommendation"] is None
    text = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "**Cause terminale** : `permanent_provider_error`" in text
    assert "**Étape interrompue** : `steelman`" in text
    assert "**interrompu**" in text


def test_terminal_reporting_framing_failure_and_budget_stop_unchanged(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    use_llm(FlakyLLM(DeliberationLLM(), plan_all={"framing": permanent_error()}))
    failed = _post(client)
    assert failed["status"] == "failed"
    stop = failed["deliberation"]["stop"]
    assert stop["terminal_failure_reason"] == "permanent_provider_error"
    assert stop["interrupted_step"] == "cadrage"
    use_llm(DeliberationLLM())
    budget = _post(client, max_llm_calls=3, max_cost_eur=5.0)
    assert budget["status"] == "candidate"
    assert budget["deliberation"]["stop"]["terminal_failure_reason"] == "budget"
    assert budget["deliberation"]["stop"]["interrupted_step"] == ""


# =================================================================================================
# §14 / §16 — pré-vol : vérifié vs à confirmer ; barème comptabilisé vs référence datée
# =================================================================================================
def test_preflight_separates_verified_items_from_operator_confirmations(
    client: TestClient, git: Callable[[str], None]
) -> None:
    report = client.get("/benchmark/preflight").json()
    assert report["verified_by_system"]
    items = {c["item"] for c in report["operator_confirmations"]}
    assert "provider_credit_or_spend_cap" in items
    assert all(
        "non vérifiable" in c["question"] or "épinglé" in c["question"]
        for c in report["operator_confirmations"]
    )
    assert report["pricing"]["accounted_eur_per_mtok"] == {"input": 3.0, "output": 15.0}
    assert report["pricing"]["reference_usd_per_mtok"] == {"input": 2.0, "output": 10.0}
    assert report["pricing"]["reference_price_date"] == "2026-09-15"
    text = render_preflight(preflight(get_settings(), CLEAN_SHA))
    assert "À CONFIRMER" in text
    assert "Pricing" in text
    # Aucune simulation de solde : le pré-vol ne fait aucun appel fournisseur (lecture seule).
    assert "balance" not in json.dumps(report).lower()


def test_report_shows_accounted_and_reference_pricing_without_changing_accounting(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    use_llm(DeliberationLLM())
    mission = _post(client)
    pricing = mission["report"]["budget"]["pricing"]
    assert pricing["accounted_eur_per_mtok"] == {"input": 3.0, "output": 15.0}
    assert pricing["accounted_cost_eur"] == pytest.approx(mission["cost_eur"])
    assert pricing["reference_usd_per_mtok"] == {"input": 2.0, "output": 10.0}
    assert pricing["reference_price_date"] == "2026-09-15"
    expected_ref = mission["input_tokens"] * 2.0 / 1e6 + mission["output_tokens"] * 10.0 / 1e6
    assert pricing["reference_cost_usd_same_tokens"] == pytest.approx(expected_ref, abs=1e-6)
    assert pricing["conservative_margin_ratio"] == [1.5, 1.5]
    # Le coût comptabilisé reste calculé au barème 3 / 15 (inchangé).
    expected_cost = mission["input_tokens"] * 3.0 / 1e6 + mission["output_tokens"] * 15.0 / 1e6
    assert mission["cost_eur"] == pytest.approx(expected_cost, abs=1e-6)
    text = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "**Barème :** comptabilisé 3.0 / 15.0 €/Mtok" in text
    assert "référence publique 2.0 / 10.0 $/Mtok (2026-09-15)" in text


# =================================================================================================
# §18 — composition : l'angle nommé par le cadrage reste la focalisation de la fiche
# =================================================================================================
def test_framing_angle_matched_to_catalogue_keeps_its_wording_as_focus() -> None:
    framing = FramingOutput.model_validate(
        {
            **THREE_DIM_FRAMING,
            "dimensions": [
                {
                    "name": "dimension alpha",
                    "why": "synthétique",
                    "presumed_criticality": "medium",
                    "unknowns": [],
                    "suggested_angles": ["relation client B2B et contrats cadres", "mesure"],
                }
            ],
        }
    )
    result = compose(
        framing,
        effective_class="importante",
        ceo_preference="",
        max_angles_per_cell=3,
        max_experts=6,
    )
    ux = next(e for e in result.experts if e.angle_title == "Expert UX / utilisateur")
    assert ux.angle_source == "cadrage"
    assert ux.framing_angle == "relation client B2B et contrats cadres"
    assert ux.angle_of_analysis.startswith("relation client B2B et contrats cadres")
    assert "focalisation nommée par le cadrage" in ux.angle_of_analysis
    measure = next(e for e in result.experts if e.angle_title == "Expert données / mesure")
    assert measure.framing_angle == "mesure"  # le mot du cadrage est conservé tel quel
    prompt = build_expert_prompt(
        spec=ux,
        framing_dossier="dossier",
        input_type="problem",
        input_text="entrée",
        context_text="",
        ceo_preference="",
    )
    assert "relation client B2B et contrats cadres" in prompt
    journal = next(j for j in result.journal if j.get("expert_id") == ux.expert_id)
    assert journal["framing_angle"] == "relation client B2B et contrats cadres"
