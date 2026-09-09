"""OT-V1, incrément 2 — comptabilité conservatrice du coût des tentatives fournisseur (B12).

Aucun appel réel. Un faux client structuré est enveloppé dans un client « défaillant » (voir
`test_missions_resilience`) ; le sommeil entre tentatives est enregistré, jamais exécuté. Les
plafonds financiers des scénarios sont dérivés de l'estimation pré-appel réelle du cadrage
(`call_planned.estimated_cost_eur_upper_bound`), jamais d'une constante devinée.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from app.llm import LLMClient, LLMUsage
from app.mission_budget import BudgetExceededError, BudgetLedger
from app.provider_errors import (
    COST_KNOWN,
    COST_KNOWN_ZERO,
    COST_UNCERTAIN,
    TRANSIENT_PROVIDER_ERROR,
    classify_provider_error,
)
from fastapi.testclient import TestClient
from ui.mission_state import mission_state_summary

from tests.test_missions_otv1 import MULTI_FRAMING, SIMPLE_FRAMING, ScriptedStructuredLLM
from tests.test_missions_resilience import (
    FakeConnectionTimeoutError,
    FakeProviderError,
    FlakyLLM,
    overloaded,
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


def ambiguous_timeout() -> FakeConnectionTimeoutError:
    return FakeConnectionTimeoutError("read timed out after request was sent")


class _UsageBearingError(Exception):
    """Exception exposant un usage réel (réponse partielle facturée)."""

    def __init__(self) -> None:
        super().__init__("stream interrupted")
        self.status_code = 500
        self.usage = LLMUsage(input_tokens=1000, output_tokens=200)


def _post(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload = {"input_type": "problem", "input_text": "entrée synthétique exposition"}
    payload.update(overrides)
    response = client.post("/missions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _journal(client: TestClient, mission_id: int) -> list[dict[str, Any]]:
    return list(client.get(f"/missions/{mission_id}/journal").json())


def _failed_attempts(client: TestClient, mission_id: int) -> list[dict[str, Any]]:
    return [e for e in _journal(client, mission_id) if e["entry_type"] == "call_attempt_failed"]


def _framing_estimate(client: TestClient, use_llm: Callable[..., Any]) -> float:
    """Borne pré-appel réelle du cadrage, lue dans le journal d'une mission de référence."""
    use_llm(ScriptedStructuredLLM(SIMPLE_FRAMING))
    mission = _post(client, max_llm_calls=1)
    planned = next(
        e
        for e in _journal(client, mission["id"])
        if e["entry_type"] == "call_planned" and e["step"] == "cadrage"
    )
    estimate = float(planned["payload"]["estimated_cost_eur_upper_bound"])
    assert estimate > 0
    return estimate


# --- D. Sémantique de coût : rejet explicite / ambigu / usage connu -------------------------------
def test_cost_semantics_distinguish_rejected_ambiguous_and_known() -> None:
    # Rejets explicites avant traitement : aucun coût engagé (contrat formalisé dans le module).
    for exc in (
        overloaded(),
        FakeProviderError(429, "rate_limit_error"),
        FakeProviderError(503, "", "service unavailable"),
        FakeProviderError(408),
        FakeProviderError(401, "authentication_error"),
        FakeProviderError(400, "invalid_request_error"),
        FakeProviderError(404, "not_found_error"),
        FakeProviderError(None, "overloaded_error"),
    ):
        assert classify_provider_error(exc).cost_semantics == COST_KNOWN_ZERO, exc
    # Échecs ambigus : la requête a pu être traitée, le coût réel est inconnu.
    for exc in (
        ambiguous_timeout(),
        TimeoutError("t"),
        ConnectionError("reset"),
        FakeProviderError(500, "api_error"),
        FakeProviderError(502),
        FakeProviderError(504),
        RuntimeError("?"),
        ValueError("adapter"),
    ):
        assert classify_provider_error(exc).cost_semantics == COST_UNCERTAIN, exc
    # Usage réel exposé : données réelles, jamais une borne.
    known = classify_provider_error(_UsageBearingError())
    assert known.cost_semantics == COST_KNOWN
    assert (known.usage_input_tokens, known.usage_output_tokens) == (1000, 200)
    assert known.category == TRANSIENT_PROVIDER_ERROR


def test_ledger_counts_uncertain_exposure_against_the_cap_without_double_counting() -> None:
    ledger = BudgetLedger(
        max_calls=10, max_cost_eur=1.0, price_in_per_mtok=3, price_out_per_mtok=15
    )
    # Sans exposition, cet appel (≈ 0,915 €) serait admis sous 1 € ; avec 0,30 € d'exposition il
    # ne l'est plus : la borne potentielle, pas le seul coût connu, fait foi.
    big_prompt = "p" * 900_000
    assert ledger.estimate_call_cost_eur("s", big_prompt, 1000) <= 1.0
    exposure = ledger.record_uncertain_attempt(
        0.3, call_type="x", logical_call_id="LC-1", attempt=1
    )
    assert exposure == {
        "id": "LC-1#1",
        "logical_call_id": "LC-1",
        "attempt": 1,
        "call_type": "x",
        "upper_bound_eur": 0.3,
        "reconciled": False,
    }
    assert ledger.known_cost_eur == 0.0
    assert ledger.uncertain_cost_upper_bound_eur == 0.3
    assert ledger.potential_total_cost_upper_bound_eur == 0.3
    assert ledger.remaining_cost_eur == 0.7
    assert ledger.calls_used == 0  # aucune tentative échouée n'est un appel logique
    # Règle de relance : égalité autorisée, dépassement refusé.
    assert ledger.retry_allowed_by_cost(0.7) is True
    assert ledger.retry_allowed_by_cost(0.700001) is False
    # Tout appel suivant (obligatoire ou non) est vérifié contre la borne potentielle.
    with pytest.raises(BudgetExceededError) as excinfo:
        ledger.check_before_call(system="s", prompt=big_prompt, max_tokens=1000, call_type="y")
    detail = excinfo.value.detail
    assert excinfo.value.reason == "cost_cap_would_be_exceeded"
    assert detail["known_cost_eur"] == 0.0
    assert detail["uncertain_cost_upper_bound_eur"] == 0.3
    assert detail["potential_total_cost_upper_bound_eur"] == 0.3
    # Un succès ensuite est du coût connu ; la borne reste une exposition distincte (non
    # additionnée deux fois, non transformée en coût connu).
    cost = ledger.record(LLMUsage(input_tokens=100_000, output_tokens=10_000))
    assert cost == 0.45
    assert ledger.known_cost_eur == 0.45
    assert ledger.uncertain_cost_upper_bound_eur == 0.3
    assert ledger.potential_total_cost_upper_bound_eur == 0.75
    assert ledger.calls_used == 1
    # Un usage réel exposé par une tentative échouée : coût connu, sans appel logique.
    assert ledger.record_failed_attempt_usage(LLMUsage(1000, 200)) == 0.006
    assert ledger.calls_used == 1
    snap = ledger.snapshot()
    assert snap["cost_eur"] == snap["known_cost_eur"] == 0.456
    assert snap["uncertain_attempts"] == 1
    assert snap["uncertain_exposures"][0]["id"] == "LC-1#1"
    assert snap["potential_total_cost_upper_bound_eur"] == 0.756


# --- TEST A — 529 explicite : aucune exposition -------------------------------------------------
def test_explicit_overload_creates_no_uncertain_exposure(
    client: TestClient, use_llm: Callable[..., Any], sleeps: list[float]
) -> None:
    use_llm(FlakyLLM(ScriptedStructuredLLM(MULTI_FRAMING), {"expert_tour0": [overloaded()]}))
    mission = _post(client)
    assert mission["status"] == "candidate"
    assert len(sleeps) == 1
    budget = mission["report"]["budget"]
    assert budget["uncertain_cost_upper_bound_eur"] == 0.0
    assert budget["uncertain_attempts"] == 0
    assert budget["uncertain_exposures"] == []
    assert budget["potential_total_cost_upper_bound_eur"] == budget["known_cost_eur"]
    assert budget["known_cost_eur"] == mission["cost_eur"] > 0
    failed = _failed_attempts(client, mission["id"])
    assert len(failed) == 1
    p = failed[0]["payload"]
    assert p["cost_semantics"] == COST_KNOWN_ZERO
    assert p["attempt_uncertain_upper_bound_eur"] == 0.0
    assert p["retry_allowed_by_cost"] is True
    assert p["retry_refusal_reason"] == ""
    assert p["max_cost_eur"] == mission["max_cost_eur"]


# --- TEST B — délai ambigu puis succès : exposition + coût connu ----------------------------------
def test_ambiguous_timeout_then_success_records_exposure_and_known_cost_separately(
    client: TestClient, use_llm: Callable[..., Any], sleeps: list[float]
) -> None:
    estimate = _framing_estimate(client, use_llm)
    use_llm(FlakyLLM(ScriptedStructuredLLM(SIMPLE_FRAMING), {"framing": [ambiguous_timeout()]}))
    mission = _post(client)
    assert mission["status"] == "candidate"
    assert len(sleeps) == 1
    budget = mission["report"]["budget"]
    assert budget["uncertain_attempts"] == 1
    assert budget["uncertain_cost_upper_bound_eur"] == round(estimate, 6)
    assert budget["known_cost_eur"] == mission["cost_eur"] > 0
    assert budget["potential_total_cost_upper_bound_eur"] == round(
        budget["known_cost_eur"] + budget["uncertain_cost_upper_bound_eur"], 6
    )
    assert budget["potential_total_cost_upper_bound_eur"] <= mission["max_cost_eur"]
    assert budget["uncertain_exposures"] == [
        {
            "id": "LC-1#1",
            "logical_call_id": "LC-1",
            "attempt": 1,
            "call_type": "framing",
            "upper_bound_eur": round(estimate, 6),
            "reconciled": False,
        }
    ]
    # `llm_calls_used` inchangé : appels logiques réussis seulement.
    assert mission["llm_calls_used"] == budget["logical_calls"]
    failed = _failed_attempts(client, mission["id"])
    assert len(failed) == 1
    p = failed[0]["payload"]
    assert p["cost_semantics"] == COST_UNCERTAIN
    assert p["attempt_uncertain_upper_bound_eur"] == round(estimate, 6)
    assert p["attempt_known_cost_eur"] == 0.0
    assert p["known_cost_eur"] == 0.0  # rien de facturé connu au moment de l'échec
    assert p["uncertain_cost_upper_bound_eur"] == round(estimate, 6)
    assert p["estimated_retry_cost_eur"] == estimate
    assert p["retry_allowed_by_cost"] is True
    assert p["will_retry"] is True
    assert p["exposure_id"] == "LC-1#1"
    # Le rapport distingue coût connu, exposition et borne ; il n'affirme jamais une facture.
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert f"connu {budget['known_cost_eur']:.4f} €" in md
    assert f"exposition incertaine ≤ {budget['uncertain_cost_upper_bound_eur']:.4f} €" in md
    assert (
        f"borne supérieure potentielle ≤ {budget['potential_total_cost_upper_bound_eur']:.4f} €"
        in md
    )
    assert f"plafond CEO {mission['max_cost_eur']:.2f} €" in md
    assert "pas un coût facturé" in md


# --- TEST C — délai ambigu et budget insuffisant : aucune relance, fail-closed --------------------
def test_ambiguous_timeout_near_cap_refuses_retry_and_fails_closed(
    client: TestClient, use_llm: Callable[..., Any], sleeps: list[float]
) -> None:
    estimate = _framing_estimate(client, use_llm)
    cap = round(estimate * 1.5, 6)  # une tentative tient, connu + incertain + relance ne tient pas
    llm = use_llm(
        FlakyLLM(ScriptedStructuredLLM(SIMPLE_FRAMING), {"framing": [ambiguous_timeout()]})
    )
    mission = _post(client, max_cost_eur=cap)
    assert mission["status"] == "failed"
    assert mission["stop_reason"] == "retry_refused_uncertain_cost_budget"
    assert sleeps == []
    assert len(llm.attempts) == 1
    failure = mission["failure"]
    assert failure["reason"] == "retry_refused_uncertain_cost_budget"
    assert failure["retry_refusal_reason"] == "retry_refused_uncertain_cost_budget"
    assert failure["category"] == TRANSIENT_PROVIDER_ERROR
    assert failure["retryable"] is True  # relançable en soi : c'est le plafond qui l'interdit
    assert failure["attempts"] == 1
    assert failure["cost_semantics"] == COST_UNCERTAIN
    assert failure["known_cost_eur"] == 0.0
    assert failure["uncertain_cost_upper_bound_eur"] == round(estimate, 6)
    assert failure["potential_total_cost_upper_bound_eur"] == round(estimate, 6)
    assert failure["estimated_retry_cost_eur"] == estimate
    assert failure["max_cost_eur"] == cap
    assert failure["retry_allowed_by_cost"] is False
    # Aucun dépassement : la borne potentielle reste sous le plafond ; rien n'est prêt.
    budget = mission["report"]["budget"]
    assert budget["potential_total_cost_upper_bound_eur"] <= cap
    assert budget["known_cost_eur"] == mission["cost_eur"] == 0.0
    assert mission["llm_calls_used"] == 0
    assert mission["recommendation"] is None
    assert mission["report"]["status"] == "failed"
    assert mission["deliberation"]["stop"]["reason"] == "budget"
    p = _failed_attempts(client, mission["id"])[0]["payload"]
    assert p["will_retry"] is False
    assert p["retry_allowed_by_cost"] is False
    assert p["retry_refusal_reason"] == "retry_refused_uncertain_cost_budget"
    # L'interface explique la cause financière sans présenter la mission comme en cours.
    summary = mission_state_summary(mission)
    assert summary["kind"] == "failed"
    assert "plafond CEO" in " ".join(summary["details"])


# --- TEST D — plusieurs délais ambigus : expositions distinctes, arrêt au plafond, pas de boucle --
def test_multiple_ambiguous_timeouts_add_distinct_exposures_until_the_cap(
    client: TestClient, use_llm: Callable[..., Any], sleeps: list[float]
) -> None:
    estimate = _framing_estimate(client, use_llm)
    cap = round(estimate * 2.5, 6)  # 1re relance : 2e ≤ cap ; 2e relance : 3e > cap
    llm = use_llm(
        FlakyLLM(
            ScriptedStructuredLLM(SIMPLE_FRAMING),
            {"framing": [ambiguous_timeout(), ambiguous_timeout(), ambiguous_timeout()]},
        )
    )
    mission = _post(client, max_cost_eur=cap)
    assert mission["status"] == "failed"
    assert mission["stop_reason"] == "retry_refused_uncertain_cost_budget"
    assert len(llm.attempts) == 2
    assert len(sleeps) == 1
    budget = mission["report"]["budget"]
    assert budget["uncertain_attempts"] == 2
    assert budget["uncertain_cost_upper_bound_eur"] == round(2 * estimate, 6)
    assert [e["id"] for e in budget["uncertain_exposures"]] == ["LC-1#1", "LC-1#2"]
    assert budget["potential_total_cost_upper_bound_eur"] <= cap
    assert budget["potential_total_cost_upper_bound_eur"] + estimate > cap
    failed = _failed_attempts(client, mission["id"])
    assert [p["payload"]["retry_allowed_by_cost"] for p in failed] == [True, False]
    assert [p["payload"]["will_retry"] for p in failed] == [True, False]
    assert failed[1]["payload"]["uncertain_cost_upper_bound_eur"] == round(2 * estimate, 6)
    assert mission["failure"]["attempts"] == 2


# --- TEST E — erreur permanente : aucune borne artificielle ------------------------------------
def test_permanent_error_has_no_uncertain_exposure(
    client: TestClient, use_llm: Callable[..., Any], sleeps: list[float]
) -> None:
    use_llm(
        FlakyLLM(
            ScriptedStructuredLLM(SIMPLE_FRAMING),
            plan_all={"framing": FakeProviderError(401, "authentication_error", "bad key")},
        )
    )
    mission = _post(client)
    assert mission["status"] == "failed"
    assert mission["stop_reason"] == "permanent_provider_error"
    assert sleeps == []
    budget = mission["report"]["budget"]
    assert budget["uncertain_cost_upper_bound_eur"] == 0.0
    assert budget["uncertain_attempts"] == 0
    assert budget["potential_total_cost_upper_bound_eur"] == 0.0
    assert mission["failure"]["cost_semantics"] == COST_KNOWN_ZERO
    assert mission["failure"]["retry_refusal_reason"] == "not_retryable"


# --- TEST F — 503 explicite (rejet) vs passerelle (ambigu) : politique formalisée -----------------
@pytest.mark.parametrize(
    ("error", "semantics"),
    [
        (FakeProviderError(503, "", "service unavailable"), COST_KNOWN_ZERO),
        (FakeProviderError(502, "", "bad gateway"), COST_UNCERTAIN),
        (FakeProviderError(504, "", "gateway timeout"), COST_UNCERTAIN),
        (FakeProviderError(500, "api_error", "internal"), COST_UNCERTAIN),
    ],
    ids=["503_rejected", "502_ambiguous", "504_ambiguous", "500_ambiguous"],
)
def test_server_side_errors_follow_the_formalised_cost_policy(
    client: TestClient,
    use_llm: Callable[..., Any],
    sleeps: list[float],
    error: BaseException,
    semantics: str,
) -> None:
    estimate = _framing_estimate(client, use_llm)
    use_llm(FlakyLLM(ScriptedStructuredLLM(SIMPLE_FRAMING), {"framing": [error]}))
    mission = _post(client)
    assert mission["status"] == "candidate"
    assert len(sleeps) == 1
    budget = mission["report"]["budget"]
    p = _failed_attempts(client, mission["id"])[0]["payload"]
    assert p["cost_semantics"] == semantics
    expected = round(estimate, 6) if semantics == COST_UNCERTAIN else 0.0
    assert budget["uncertain_cost_upper_bound_eur"] == expected
    assert budget["uncertain_attempts"] == (1 if semantics == COST_UNCERTAIN else 0)


# --- Usage réel exposé par l'exception : coût connu, pas de borne ---------------------------------
def test_failed_attempt_with_reported_usage_is_known_cost_not_exposure(
    client: TestClient, use_llm: Callable[..., Any], sleeps: list[float]
) -> None:
    use_llm(FlakyLLM(ScriptedStructuredLLM(SIMPLE_FRAMING), {"framing": [_UsageBearingError()]}))
    mission = _post(client)
    assert mission["status"] == "candidate"
    assert len(sleeps) == 1
    budget = mission["report"]["budget"]
    p = _failed_attempts(client, mission["id"])[0]["payload"]
    assert p["cost_semantics"] == COST_KNOWN
    assert p["attempt_known_cost_eur"] == 0.006  # 1000 tokens à 3 €/M + 200 tokens à 15 €/M
    assert p["attempt_uncertain_upper_bound_eur"] == 0.0
    assert budget["uncertain_cost_upper_bound_eur"] == 0.0
    # Le coût de la tentative échouée est dans le coût connu, sans appel logique supplémentaire.
    success_cost = sum(
        e["payload"]["cost_eur"]
        for e in _journal(client, mission["id"])
        if e["entry_type"] == "call_done"
    )
    assert budget["known_cost_eur"] == round(success_cost + 0.006, 6)
    assert mission["llm_calls_used"] == budget["logical_calls"]


# --- TEST G — budget exact : égalité autorisée, puis exposition déduite des appels suivants -------
def test_retry_allowed_when_bound_equals_cap_and_exposure_binds_later_calls(
    client: TestClient, use_llm: Callable[..., Any], sleeps: list[float]
) -> None:
    estimate = _framing_estimate(client, use_llm)
    cap = estimate * 2  # connu (0) + incertain (e) + relance (e) == plafond → autorisé
    use_llm(FlakyLLM(ScriptedStructuredLLM(SIMPLE_FRAMING), {"framing": [ambiguous_timeout()]}))
    mission = _post(client, max_cost_eur=cap)
    assert len(sleeps) == 1
    p = _failed_attempts(client, mission["id"])[0]["payload"]
    assert p["retry_allowed_by_cost"] is True
    assert p["potential_total_cost_upper_bound_eur"] + p["estimated_retry_cost_eur"] == cap
    # Le cadrage a réussi ; la borne potentielle ne dépasse jamais le plafond.
    assert mission["framing"]["parsed"] is not None
    assert mission["llm_calls_used"] >= 1
    budget = mission["report"]["budget"]
    assert budget["potential_total_cost_upper_bound_eur"] <= cap
    # Les appels suivants (étapes obligatoires comprises) sont vérifiés contre connu + incertain :
    # l'exposition n'est jamais ignorée, aucun appel ne franchit le plafond.
    assert mission["status"] == "candidate"
    assert mission["stop_reason"] == "cost_cap_would_be_exceeded"
    refusal = budget["refusals"][-1]
    assert refusal["reason"] == "cost_cap_would_be_exceeded"
    assert refusal["uncertain_cost_upper_bound_eur"] == round(estimate, 6)
    assert (
        refusal["potential_total_cost_upper_bound_eur"] + refusal["estimated_call_cost_eur"] > cap
    )
    assert mission["recommendation"] is None or not mission["recommendation"].get("decision_ready")


# --- B8 — réserve en appels intacte, exposition financière déduite --------------------------------
def test_b8_reserve_holds_with_ambiguous_failures_on_the_last_admitted_call(
    client: TestClient, use_llm: Callable[..., Any], sleeps: list[float]
) -> None:
    # Budget en appels exactement suffisant (5) ; deux délais ambigus sur la porte qualité : les
    # relances n'empruntent aucun appel (B8), l'exposition est comptée et reste sous le plafond.
    use_llm(
        FlakyLLM(
            ScriptedStructuredLLM(SIMPLE_FRAMING),
            {"quality_gate": [ambiguous_timeout(), ambiguous_timeout()]},
        )
    )
    mission = _post(client, max_llm_calls=5)
    assert mission["status"] == "candidate"
    assert mission["llm_calls_used"] == 5 == mission["max_llm_calls"]
    assert "porte_qualite" in mission["deliberation"]["steps_done"]
    assert len(sleeps) == 2
    budget = mission["report"]["budget"]
    assert budget["refusals"] == []
    assert budget["uncertain_attempts"] == 2
    gate_estimate = next(
        e["payload"]["estimated_cost_eur_upper_bound"]
        for e in _journal(client, mission["id"])
        if e["entry_type"] == "call_planned" and e["payload"]["call_type"] == "quality_gate"
    )
    assert budget["uncertain_cost_upper_bound_eur"] == round(2 * gate_estimate, 6)
    assert budget["potential_total_cost_upper_bound_eur"] <= mission["max_cost_eur"]
    assert budget["potential_total_cost_upper_bound_eur"] == round(
        budget["known_cost_eur"] + budget["uncertain_cost_upper_bound_eur"], 6
    )
