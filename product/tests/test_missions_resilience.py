"""OT-V1, incrément 2 — résilience aux erreurs fournisseur transitoires (B10) et état d'échec (B11).

Aucun appel réel : un faux client structuré est enveloppé dans un client « défaillant » qui lève
des exceptions imitant celles d'un SDK (code HTTP, type d'erreur, en-tête Retry-After) selon un
plan par type d'appel. Le sommeil entre tentatives est remplacé par un enregistreur.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest
from app.db import LLMCallLog, Mission
from app.llm import LLMClient, LLMResponse, StructuredCompletionUnsupportedError
from app.provider_errors import (
    LOCAL_ERROR,
    PERMANENT_PROVIDER_ERROR,
    TRANSIENT_PROVIDER_ERROR,
    UNKNOWN_ERROR,
    ProviderErrorInfo,
    classify_provider_error,
    retry_delay_seconds,
)
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from ui.mission_state import is_terminal, mission_state_summary, poll_until_terminal

from tests.test_missions_otv1 import MULTI_FRAMING, SIMPLE_FRAMING, ScriptedStructuredLLM


class _Headers(dict[str, str]):
    pass


class _Response:
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.headers = _Headers(headers or {})


class FakeProviderError(Exception):
    """Imite une erreur de SDK : `status_code`, `body.error.type`, `response.headers`."""

    def __init__(
        self,
        status_code: int | None,
        error_type: str = "",
        message: str = "",
        retry_after: str | None = None,
    ) -> None:
        super().__init__(message or error_type or f"HTTP {status_code}")
        self.status_code = status_code
        self.body = {"error": {"type": error_type, "message": message}} if error_type else None
        self.response = _Response({"retry-after": retry_after} if retry_after else {})


class FakeConnectionTimeoutError(Exception):
    """Coupure réseau sans code HTTP (le nom porte l'indice)."""


def overloaded() -> FakeProviderError:
    return FakeProviderError(529, "overloaded_error", "Overloaded")


class FlakyLLM:
    """Enveloppe un faux client : lève les exceptions planifiées avant de déléguer.

    `plan` : type d'appel → liste d'exceptions à lever aux premières tentatives de la première
    occurrence de ce type (puis délégation normale). `plan_all` : lève sur chaque occurrence.
    """

    def __init__(
        self,
        inner: ScriptedStructuredLLM,
        plan: dict[str, list[BaseException]] | None = None,
        *,
        plan_all: dict[str, BaseException] | None = None,
    ) -> None:
        self.inner = inner
        self.plan = {k: list(v) for k, v in (plan or {}).items()}
        self.plan_all = plan_all or {}
        self.attempts: list[dict[str, Any]] = []

    def complete(self, prompt: str) -> str:
        raise AssertionError("chemin historique non utilisé")

    def complete_structured(
        self, *, system: str, prompt: str, call_type: str, max_tokens: int
    ) -> LLMResponse:
        self.attempts.append({"call_type": call_type})
        if call_type in self.plan_all:
            raise self.plan_all[call_type]
        pending = self.plan.get(call_type)
        if pending:
            raise pending.pop(0)
        return self.inner.complete_structured(
            system=system, prompt=prompt, call_type=call_type, max_tokens=max_tokens
        )


_CURRENT: dict[str, Any] = {}


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    def factory() -> LLMClient:
        return _CURRENT["llm"]

    return factory


@pytest.fixture
def use_llm() -> Callable[[Any], Any]:
    def _set(llm: Any) -> Any:
        _CURRENT["llm"] = llm
        return llm

    _CURRENT["llm"] = ScriptedStructuredLLM(SIMPLE_FRAMING)
    return _set


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    recorded: list[float] = []
    monkeypatch.setattr("app.missions.provider_sleep", recorded.append)
    return recorded


def _post(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload = {"input_type": "problem", "input_text": "entrée synthétique résilience"}
    payload.update(overrides)
    response = client.post("/missions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _journal(client: TestClient, mission_id: int) -> list[dict[str, Any]]:
    return list(client.get(f"/missions/{mission_id}/journal").json())


# --- Classification -----------------------------------------------------------------------------
def test_error_classification_is_generic_and_fail_closed() -> None:
    assert classify_provider_error(overloaded()).category == TRANSIENT_PROVIDER_ERROR
    assert classify_provider_error(FakeProviderError(429, "rate_limit_error")).retryable is True
    assert classify_provider_error(FakeProviderError(503)).category == TRANSIENT_PROVIDER_ERROR
    assert classify_provider_error(FakeProviderError(500, "api_error")).retryable is True
    assert (
        classify_provider_error(FakeConnectionTimeoutError("reset")).category
        == TRANSIENT_PROVIDER_ERROR
    )
    assert classify_provider_error(TimeoutError("t")).retryable is True
    permanent = classify_provider_error(
        FakeProviderError(401, "authentication_error", "invalid x-api-key")
    )
    assert permanent.category == PERMANENT_PROVIDER_ERROR
    assert permanent.retryable is False
    assert classify_provider_error(FakeProviderError(404, "not_found_error")).retryable is False
    assert (
        classify_provider_error(FakeProviderError(400, "invalid_request_error")).retryable is False
    )
    assert classify_provider_error(FakeProviderError(403)).category == PERMANENT_PROVIDER_ERROR
    # Erreurs locales : jamais relancées, jamais confondues avec le fournisseur.
    assert classify_provider_error(ValueError("schéma")).category == LOCAL_ERROR
    assert (
        classify_provider_error(StructuredCompletionUnsupportedError("x")).category == UNKNOWN_ERROR
    )
    assert classify_provider_error(RuntimeError("?")).category == UNKNOWN_ERROR
    assert classify_provider_error(RuntimeError("?")).retryable is False
    # Le message est tronqué et aucun secret n'est extrait : seuls type, code et message.
    info = classify_provider_error(FakeProviderError(529, "overloaded_error", "x" * 1000))
    assert len(info.message) == 300
    assert set(info.to_dict()) == {
        "category",
        "retryable",
        "status_code",
        "error_type",
        "exception_type",
        "message",
        "retry_after_seconds",
    }


def test_retry_delay_is_bounded_and_honours_retry_after_within_cap() -> None:
    info = ProviderErrorInfo(TRANSIENT_PROVIDER_ERROR, True, 529, "overloaded_error", "E", "m")
    assert retry_delay_seconds(1, info, base=1.0, cap=8.0, retry_after_cap=30.0, jitter=0.0) == 1.0
    assert retry_delay_seconds(2, info, base=1.0, cap=8.0, retry_after_cap=30.0, jitter=0.0) == 2.0
    assert retry_delay_seconds(9, info, base=1.0, cap=8.0, retry_after_cap=30.0, jitter=0.0) == 8.0
    with_ra = classify_provider_error(FakeProviderError(429, "rate_limit_error", retry_after="3"))
    assert with_ra.retry_after_seconds == 3.0
    assert retry_delay_seconds(1, with_ra, base=1.0, cap=8.0, retry_after_cap=30.0) == 3.0
    huge = classify_provider_error(FakeProviderError(429, "rate_limit_error", retry_after="600"))
    assert retry_delay_seconds(1, huge, base=1.0, cap=8.0, retry_after_cap=30.0) == 30.0


# --- TEST A — surcharge puis succès --------------------------------------------------------------
def test_overload_then_success_recovers_without_duplication(
    client: TestClient,
    use_llm: Callable[..., Any],
    sleeps: list[float],
    session_factory: sessionmaker[Session],
) -> None:
    llm = use_llm(FlakyLLM(ScriptedStructuredLLM(MULTI_FRAMING), {"expert_tour0": [overloaded()]}))
    mission = _post(client)
    assert mission["status"] == "candidate"
    assert mission["failure"] is None
    # Une relance, une attente bornée, un seul résultat logique pour l'expert concerné.
    assert len(sleeps) == 1
    assert 0 < sleeps[0] <= 1.25
    experts = [e["expert_id"] for e in mission["composition"]["experts"]]
    positions = [p["expert_id"] for p in mission["cartography"]["positions"]]
    assert positions == experts  # aucune position dupliquée, aucun expert doublé
    assert mission["cartography"]["experts_answered"] == len(experts)
    tour0_attempts = [a for a in llm.attempts if a["call_type"] == "expert_tour0"]
    assert len(tour0_attempts) == len(experts) + 1  # une tentative physique de plus
    budget = mission["report"]["budget"]
    assert budget["provider_attempts"] == budget["logical_calls"] + 1
    assert budget["provider_retries"] == 1
    assert budget["provider_failures"] == 1
    assert mission["llm_calls_used"] == budget["logical_calls"]  # sémantique inchangée
    # Le journal conserve l'échec initial puis la réussite du même appel logique.
    entries = _journal(client, mission["id"])
    failed = [e for e in entries if e["entry_type"] == "call_attempt_failed"]
    assert len(failed) == 1
    payload = failed[0]["payload"]
    assert payload["attempt_number"] == 1
    assert payload["max_attempts"] == 3
    assert payload["category"] == TRANSIENT_PROVIDER_ERROR
    assert payload["retryable"] is True
    assert payload["status_code"] == 529
    assert payload["error_type"] == "overloaded_error"
    assert payload["will_retry"] is True
    assert payload["retry_delay_seconds"] == sleeps[0]
    assert payload["provider"] == "anthropic"
    assert payload["model"]
    done = next(
        e
        for e in entries
        if e["entry_type"] == "call_done"
        and e["payload"]["logical_call_id"] == payload["logical_call_id"]
    )
    assert done["payload"]["attempt_number"] == 2
    assert done["payload"]["recovered_after_retries"] == 1
    assert done["actor"] == failed[0]["actor"]
    # `llm_call_logs` trace les deux tentatives physiques (erreur puis succès), pas de doublon
    # métier.
    with session_factory() as session:
        rows = list(
            session.execute(select(LLMCallLog).where(LLMCallLog.mission_id == mission["id"]))
            .scalars()
            .all()
        )
    assert len([r for r in rows if r.status == "error"]) == 1
    assert len([r for r in rows if r.status == "success"]) == mission["llm_calls_used"]
    # La délibération s'est déroulée normalement après récupération.
    assert mission["recommendation"]["status"] == "produced"


# --- TEST B — surcharges répétées ----------------------------------------------------------------
def test_repeated_overloads_fail_closed_after_bounded_attempts(
    client: TestClient, use_llm: Callable[..., Any], sleeps: list[float]
) -> None:
    llm = use_llm(
        FlakyLLM(ScriptedStructuredLLM(MULTI_FRAMING), plan_all={"expert_tour0": overloaded()})
    )
    mission = _post(client)
    assert mission["status"] == "failed"
    assert mission["stop_reason"] == "transient_retries_exhausted"
    failure = mission["failure"]
    assert failure["reason"] == "transient_retries_exhausted"
    assert failure["step"] == "tour0"
    assert failure["actor"] == "E1"
    assert failure["attempts"] == 3
    assert failure["max_attempts"] == 3
    assert failure["category"] == TRANSIENT_PROVIDER_ERROR
    assert failure["status_code"] == 529
    assert failure["provider"] == "anthropic"
    # Borné : 3 tentatives, 2 attentes croissantes, aucune boucle.
    assert len([a for a in llm.attempts if a["call_type"] == "expert_tour0"]) == 3
    assert len(sleeps) == 2
    assert sleeps[0] <= sleeps[1]
    # Le cadrage réussi est conservé ; rien n'est présenté comme prêt.
    assert mission["framing"]["parsed"] is not None
    assert mission["composition"] is not None
    assert mission["recommendation"] is None
    assert mission["report"]["status"] == "failed"
    assert mission["report"]["partial"] is True
    assert mission["report"]["failure"]["reason"] == "transient_retries_exhausted"
    assert mission["llm_calls_used"] == 1  # seul le cadrage a réussi
    entries = _journal(client, mission["id"])
    assert len([e for e in entries if e["entry_type"] == "call_attempt_failed"]) == 3
    terminal = next(e for e in entries if e["entry_type"] == "failed_provider_call")
    assert terminal["payload"]["provider_attempts"] == 4
    assert terminal["payload"]["provider_retries"] == 2
    assert client.post(f"/missions/{mission['id']}/approve").status_code == 409


# --- TEST C / D — rate limit puis succès ; 5xx temporaire puis succès -----------------------------
@pytest.mark.parametrize(
    ("error", "expected_delay"),
    [
        (FakeProviderError(429, "rate_limit_error", "rate limited", retry_after="2"), 2.0),
        (FakeProviderError(503, "", "service unavailable"), None),
        (FakeConnectionTimeoutError("connection reset by peer"), None),
    ],
    ids=["429_retry_after", "503", "connection"],
)
def test_transient_errors_are_retried_then_succeed(
    client: TestClient,
    use_llm: Callable[..., Any],
    sleeps: list[float],
    error: BaseException,
    expected_delay: float | None,
) -> None:
    use_llm(FlakyLLM(ScriptedStructuredLLM(SIMPLE_FRAMING), {"framing": [error]}))
    mission = _post(client)
    assert mission["status"] == "candidate"
    assert len(sleeps) == 1
    if expected_delay is not None:
        assert sleeps[0] == expected_delay  # Retry-After pris en compte, borné
    failed = [
        e for e in _journal(client, mission["id"]) if e["entry_type"] == "call_attempt_failed"
    ]
    assert len(failed) == 1
    assert failed[0]["payload"]["category"] == TRANSIENT_PROVIDER_ERROR
    assert failed[0]["step"] == "cadrage"


# --- TEST E — erreur permanente -------------------------------------------------------------------
def test_permanent_error_is_never_retried(
    client: TestClient, use_llm: Callable[..., Any], sleeps: list[float]
) -> None:
    llm = use_llm(
        FlakyLLM(
            ScriptedStructuredLLM(SIMPLE_FRAMING),
            plan_all={
                "framing": FakeProviderError(401, "authentication_error", "invalid x-api-key")
            },
        )
    )
    mission = _post(client)
    assert mission["status"] == "failed"
    assert mission["stop_reason"] == "permanent_provider_error"
    assert sleeps == []
    assert len(llm.attempts) == 1
    failure = mission["failure"]
    assert failure["category"] == PERMANENT_PROVIDER_ERROR
    assert failure["retryable"] is False
    assert failure["attempts"] == 1
    assert failure["status_code"] == 401
    assert failure["step"] == "cadrage"
    assert mission["llm_calls_used"] == 0
    assert mission["cost_eur"] == 0
    failed = [
        e for e in _journal(client, mission["id"]) if e["entry_type"] == "call_attempt_failed"
    ]
    assert len(failed) == 1
    assert failed[0]["payload"]["will_retry"] is False


# --- TEST F — erreur locale (parsing / contrat) : hors du mécanisme de relance réseau -------------
def test_local_errors_do_not_enter_the_transient_retry_path(
    client: TestClient, use_llm: Callable[..., Any], sleeps: list[float]
) -> None:
    # Une sortie JSON invalide n'est PAS une erreur fournisseur : aucune relance réseau (freeze
    # v3.1 : la mission échoue honnêtement sur le cadrage, un seul appel).
    from tests.test_missions_truncation import FailureModeLLM

    llm = use_llm(FailureModeLLM(framing_mode="invalid"))
    mission = _post(client)
    assert mission["status"] == "failed"
    assert mission["stop_reason"] == "framing_failed:json_invalid"
    assert len(llm.calls) == 1
    assert sleeps == []
    assert not [
        e for e in _journal(client, mission["id"]) if e["entry_type"] == "call_attempt_failed"
    ]
    # Une exception locale de notre code n'est pas relancée non plus (catégorie locale).
    llm2 = use_llm(
        FlakyLLM(ScriptedStructuredLLM(SIMPLE_FRAMING), plan_all={"framing": ValueError("bug")})
    )
    mission = _post(client)
    assert mission["status"] == "failed"
    assert mission["stop_reason"] == "local_error"
    assert len(llm2.attempts) == 1
    assert sleeps == []
    assert mission["failure"]["category"] == LOCAL_ERROR


# --- B8 + relance fournisseur -------------------------------------------------------------------
def test_provider_retries_never_borrow_budget_or_reserves(
    client: TestClient, use_llm: Callable[..., Any], sleeps: list[float]
) -> None:
    # Budget exactement suffisant pour le cas simple (cadrage, 1 expert, comparaison, synthèse,
    # porte = 5 appels logiques). Une surcharge frappe le dernier appel admis : la relance
    # n'emprunte rien — l'appel logique était déjà admis, les tentatives échouées ne coûtent ni
    # appel ni euro — et le plafond n'est jamais dépassé.
    use_llm(
        FlakyLLM(
            ScriptedStructuredLLM(SIMPLE_FRAMING), {"quality_gate": [overloaded(), overloaded()]}
        )
    )
    mission = _post(client, max_llm_calls=5)
    assert mission["status"] == "candidate"
    assert mission["llm_calls_used"] == 5 == mission["max_llm_calls"]
    assert mission["report"]["budget"]["refusals"] == []
    assert mission["report"]["budget"]["provider_retries"] == 2
    # La porte (dernier appel admis) a bien été exécutée après ses deux relances ; avec une
    # seule
    # perspective, elle bloque légitimement (confrontation non réalisée : B4), sans rapport avec
    # B10.
    assert "porte_qualite" in mission["deliberation"]["steps_done"]
    assert "gate" in mission["recommendation"]
    assert len(sleeps) == 2


def test_total_retry_cap_per_mission_is_enforced_and_journaled(
    client: TestClient,
    use_llm: Callable[..., Any],
    sleeps: list[float],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MISSION_PROVIDER_MAX_RETRIES_TOTAL", "1")
    from app.config import get_settings

    get_settings.cache_clear()
    use_llm(
        FlakyLLM(
            ScriptedStructuredLLM(SIMPLE_FRAMING),
            {"framing": [overloaded()], "expert_tour0": [overloaded()]},
        )
    )
    mission = _post(client)
    get_settings.cache_clear()
    # Première surcharge relancée (1/1) ; la seconde ne peut plus l'être : échec explicite.
    assert mission["status"] == "failed"
    assert mission["stop_reason"] == "transient_retries_exhausted"
    assert mission["failure"]["total_retry_cap_reached"] is True
    assert mission["failure"]["retries_total_used"] == 1
    assert mission["failure"]["retries_total_max"] == 1
    assert len(sleeps) == 1
    assert mission["llm_calls_used"] == 1


# --- B11 — état d'une mission : API, résumé, interrogation bornée ---------------------------------
def _insert_mission(session_factory: sessionmaker[Session], **fields: Any) -> int:
    with session_factory() as session:
        m = Mission(input_text="x", **fields)
        session.add(m)
        session.commit()
        return int(m.id)


def test_report_endpoint_distinguishes_running_failed_completed_and_missing(
    client: TestClient, use_llm: Callable[..., Any], session_factory: sessionmaker[Session]
) -> None:
    running_id = _insert_mission(session_factory, status="running")
    failed_id = _insert_mission(
        session_factory,
        status="failed",
        stop_reason="transient_retries_exhausted",
        failure_json=json.dumps({"reason": "transient_retries_exhausted", "step": "tour0"}),
    )
    running = client.get(f"/missions/{running_id}/report/markdown")
    assert running.status_code == 409
    assert running.json()["detail"]["state"] == "running"
    failed = client.get(f"/missions/{failed_id}/report/markdown")
    assert failed.status_code == 409
    assert failed.json()["detail"]["state"] == "failed"
    assert failed.json()["detail"]["failure"]["step"] == "tour0"
    assert running.json()["detail"]["message"] != failed.json()["detail"]["message"]
    assert (
        client.get(f"/missions/{failed_id}").json()["failure"]["reason"]
        == "transient_retries_exhausted"
    )
    # Mission terminée normalement : rapport accessible (non-régression).
    use_llm(ScriptedStructuredLLM(SIMPLE_FRAMING))
    done = _post(client)
    assert client.get(f"/missions/{done['id']}/report/markdown").status_code == 200
    # Mission échouée après relances : rapport diagnostic partiel accessible et marqué échoué.
    use_llm(FlakyLLM(ScriptedStructuredLLM(MULTI_FRAMING), plan_all={"expert_tour0": overloaded()}))
    broken = _post(client)
    md = client.get(f"/missions/{broken['id']}/report/markdown")
    assert md.status_code == 200
    assert "`failed`" in md.json()["markdown"]
    assert client.get("/missions/999999/report/markdown").status_code == 404


def test_mission_state_summary_never_presents_failed_as_running() -> None:
    running = mission_state_summary({"status": "running"})
    assert running["kind"] == "running"
    assert "en cours" in running["headline"].lower()
    failed = mission_state_summary(
        {
            "status": "failed",
            "stop_reason": "transient_retries_exhausted",
            "failure": {
                "step": "tour0",
                "actor": "E7",
                "error_category": "transient_provider_error",
                "category": "transient_provider_error",
                "reason": "transient_retries_exhausted",
                "attempts": 3,
                "max_attempts": 3,
            },
        }
    )
    assert failed["kind"] == "failed"
    assert failed["headline"] == "MISSION ÉCHOUÉE"
    text = " ".join(failed["details"])
    assert "tour0 / E7" in text
    assert "Tentatives : 3 / 3" in text
    assert "épuisement des relances" in text
    assert "inutile d'attendre" in text
    assert "en cours" not in text.lower()
    permanent = mission_state_summary(
        {
            "status": "failed",
            "failure": {
                "step": "cadrage",
                "reason": "permanent_provider_error",
                "category": "permanent_provider_error",
            },
        }
    )
    assert "erreur permanente" in " ".join(permanent["details"])
    assert mission_state_summary({"status": "candidate"})["kind"] == "completed"
    assert mission_state_summary({"status": "approved"})["kind"] == "completed"
    assert is_terminal("failed")
    assert is_terminal("candidate")
    assert not is_terminal("running")


def test_polling_stops_immediately_on_failed_and_is_bounded_otherwise() -> None:
    sleeps: list[float] = []
    states = iter([{"status": "running"}, {"status": "running"}, {"status": "failed"}])
    mission, polls, terminal = poll_until_terminal(
        lambda: next(states), sleeper=sleeps.append, interval_seconds=5.0, max_polls=100
    )
    assert terminal is True
    assert polls == 3
    assert mission["status"] == "failed"
    assert sleeps == [5.0, 5.0]
    mission, polls, terminal = poll_until_terminal(
        lambda: {"status": "running"}, sleeper=sleeps.append, interval_seconds=5.0, max_polls=4
    )
    assert terminal is False
    assert polls == 4
    mission, polls, terminal = poll_until_terminal(
        lambda: {"status": "candidate"}, sleeper=sleeps.append, interval_seconds=5.0, max_polls=4
    )
    assert terminal is True
    assert polls == 1
