"""OT-V1, incrément 2 — B14-prime : budgets de sortie proportionnés, réserve de composition alignée
sur le cœur réel, plan après Tour 0, relance après troncature, observabilité des blocs, gabarit.

Fixtures purement synthétiques (aucun contenu de holdout). Les faux clients de
`test_missions_deliberation` sont réutilisés et enveloppés pour casser, tronquer ou annoter des
réponses selon un plan déterministe.
"""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from app.config import get_settings
from app.llm import LLMClient, LLMResponse, LLMUsage, count_content_blocks
from app.mission_budget import (
    consolidation_core_bound,
    feasible_expert_count,
    minimal_deliberation_bound,
)
from app.mission_report import budget_request_lines
from app.output_budget import (
    RULES,
    count_completed_items,
    fixed_output_budget,
    output_budget,
    plan_truncation_retry,
)
from fastapi.testclient import TestClient

from tests.test_missions_cost_exposure import ambiguous_timeout
from tests.test_missions_deliberation import (
    FOUR_CRITICAL_FRAMING,
    THREE_DIM_FRAMING,
    DeliberationLLM,
    OptionSpec,
    competent_clerk,
)
from tests.test_missions_resilience import FlakyLLM, overloaded

_CURRENT: dict[str, Any] = {}
ANGLE_WORDS = [
    "praticien",
    "mesure",
    "sceptique",
    "utilisateur",
    "théoricien",
    "conformité",
    "intégration",
    "performance",
    "risque",
]


def wide_framing(n_dims: int, criticalities: list[str]) -> dict[str, Any]:
    """Cadrage synthétique à `n_dims` dimensions ; trois angles suggérés par dimension."""
    dims = []
    for i in range(n_dims):
        angles = [ANGLE_WORDS[(i + k) % len(ANGLE_WORDS)] for k in range(3)]
        dims.append(
            {
                "name": f"dimension synthétique {i + 1}",
                "why": "dimension du cas synthétique W",
                "presumed_criticality": criticalities[i % len(criticalities)],
                "unknowns": [],
                "suggested_angles": angles,
            }
        )
    return {**THREE_DIM_FRAMING, "problem_understood": "cas synthétique W", "dimensions": dims}


SIXTEEN_FRAMING = wide_framing(6, ["high", "high", "high", "high", "high", "low"])


def options_for(n_experts: int, per_expert: int) -> dict[str, OptionSpec]:
    """`per_expert` options distinctes par expert (aucun doublon inter-experts)."""
    return {
        f"E{e}": [(f"stratégie {e}-{k}", "build") for k in range(1, per_expert + 1)]
        for e in range(1, n_experts + 1)
    }


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

    _CURRENT["llm"] = DeliberationLLM()
    return _set


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    recorded: list[float] = []
    monkeypatch.setattr("app.missions.provider_sleep", recorded.append)
    return recorded


@pytest.fixture
def settings_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[[str, str], None]]:
    def _set(name: str, value: str) -> None:
        monkeypatch.setenv(name, value)
        get_settings.cache_clear()

    yield _set
    get_settings.cache_clear()


class Breaking:
    """Casse la syntaxe JSON des occurrences choisies d'un type d'appel (puis délègue)."""

    def __init__(self, inner: Any, call_type: str, occurrences: set[int]) -> None:
        self.inner = inner
        self.call_type = call_type
        self.occurrences = occurrences
        self.seen = 0
        self.calls = inner.calls

    def complete(self, prompt: str) -> str:
        raise AssertionError("chemin historique non utilisé")

    def complete_structured(
        self, *, system: str, prompt: str, call_type: str, max_tokens: int
    ) -> LLMResponse:
        response = self.inner.complete_structured(
            system=system, prompt=prompt, call_type=call_type, max_tokens=max_tokens
        )
        if call_type != self.call_type:
            return response
        self.seen += 1
        if self.seen in self.occurrences:
            return dataclasses.replace(response, text=response.text[:-1] + ",}")
        return response


class NeedTokens:
    """Auto-qualification dont la réponse complète exige `need` tokens de sortie.

    Si la limite accordée est inférieure au besoin : réponse coupée à la limite avec
    `items_when_cut` éléments complets (ou vide) ; sinon réponse valide du client interne.
    """

    def __init__(self, inner: Any, *, need: int, items_when_cut: int) -> None:
        self.inner = inner
        self.need = need
        self.items_when_cut = items_when_cut
        self.calls = inner.calls
        self.granted: list[int] = []

    def complete(self, prompt: str) -> str:
        raise AssertionError("chemin historique non utilisé")

    def complete_structured(
        self, *, system: str, prompt: str, call_type: str, max_tokens: int
    ) -> LLMResponse:
        response = self.inner.complete_structured(
            system=system, prompt=prompt, call_type=call_type, max_tokens=max_tokens
        )
        if call_type != "self_qualification":
            return response
        self.granted.append(max_tokens)
        if max_tokens >= self.need:
            return response
        items = [
            json.dumps({"other_id": f"P{k + 2}", "relation": "different", "reason": "r" * 40})
            for k in range(self.items_when_cut)
        ]
        cut = '{"relations": [' + ", ".join(items)
        cut += ', {"other_id": "P9", "relation": "diff' if items else '{"other_id": "P2", "rel'
        return LLMResponse(text=cut, usage=LLMUsage(1000, max_tokens), stop_reason="max_tokens")


class WithBlocks:
    """Annote les réponses avec des métadonnées de blocs ; peut vider le texte d'un type d'appel."""

    def __init__(
        self,
        inner: Any,
        blocks: dict[str, int],
        *,
        empty_call_type: str = "",
        empty_output_tokens: int = 1500,
    ) -> None:
        self.inner = inner
        self.blocks = blocks
        self.empty_call_type = empty_call_type
        self.empty_output_tokens = empty_output_tokens
        self.calls = inner.calls

    def complete(self, prompt: str) -> str:
        raise AssertionError("chemin historique non utilisé")

    def complete_structured(
        self, *, system: str, prompt: str, call_type: str, max_tokens: int
    ) -> LLMResponse:
        response = self.inner.complete_structured(
            system=system, prompt=prompt, call_type=call_type, max_tokens=max_tokens
        )
        if call_type == self.empty_call_type:
            return LLMResponse(
                text="",
                usage=LLMUsage(1000, min(max_tokens, self.empty_output_tokens)),
                stop_reason="max_tokens",
                content_blocks={"thinking": 1},
            )
        return dataclasses.replace(response, content_blocks=dict(self.blocks))


class Costly:
    """Gonfle l'usage de sortie facturé d'un type d'appel (coût connu réaliste, texte inchangé)."""

    def __init__(self, inner: Any, call_type: str, output_tokens: int) -> None:
        self.inner = inner
        self.call_type = call_type
        self.output_tokens = output_tokens
        self.calls = inner.calls

    def complete(self, prompt: str) -> str:
        raise AssertionError("chemin historique non utilisé")

    def complete_structured(
        self, *, system: str, prompt: str, call_type: str, max_tokens: int
    ) -> LLMResponse:
        response = self.inner.complete_structured(
            system=system, prompt=prompt, call_type=call_type, max_tokens=max_tokens
        )
        if call_type != self.call_type:
            return response
        usage = LLMUsage(response.usage.input_tokens, min(max_tokens, self.output_tokens))
        return dataclasses.replace(response, usage=usage)


def _post(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload = {"input_type": "problem", "input_text": "entrée synthétique budget de sortie"}
    payload.update(overrides)
    response = client.post("/missions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _journal(client: TestClient, mission_id: int) -> list[dict[str, Any]]:
    return list(client.get(f"/missions/{mission_id}/journal").json())


def _entries(client: TestClient, mission_id: int, entry_type: str) -> list[dict[str, Any]]:
    return [e for e in _journal(client, mission_id) if e["entry_type"] == entry_type]


# --- Unité : formule, bornes, extrapolation -------------------------------------------------------
def test_output_budget_formula_is_explicit_bounded_and_documented() -> None:
    rule = RULES["self_qualification"]
    b = output_budget("self_qualification", 15, floor=1500, ceiling=4000)
    assert (rule.base_tokens, rule.per_item_tokens, rule.safety) == (64, 80, 1.5)
    assert b.required_tokens == 1896 == b.granted
    assert "64 + 80 * 15 relations" in b.formula
    assert "1896" in b.formula
    assert (b.capped_by_ceiling, b.raised_to_floor) == (False, False)
    small = output_budget("self_qualification", 2, floor=1500, ceiling=4000)
    assert (small.required_tokens, small.granted, small.raised_to_floor) == (336, 1500, True)
    huge = output_budget("clerk", 500, floor=3000, ceiling=8000)
    assert (huge.granted, huge.capped_by_ceiling) == (8000, True)
    fixed = fixed_output_budget("framing", 8000)
    assert (fixed.floor, fixed.ceiling, fixed.granted) == (8000, 8000, 8000)
    # Éléments complets d'un texte tronqué : objets du second niveau, chaînes respectées.
    text = (
        '{"relations": [{"other_id": "P2", "relation": "x", "reason": "a } b"}, {"other_id": "P3"'
    )
    assert count_completed_items(text) == 1
    assert count_completed_items("") == 0
    # Relance après troncature : extrapolation mesurée, plafond, refus à limite fixe.
    plan = plan_truncation_retry(b, output_tokens=1896, raw_text=text.replace("P3", "P4"))
    assert plan.allowed is True
    assert plan.items_completed == 1
    assert plan.max_tokens == 4000  # 1896 tokens pour 1 élément → 15 x 1896 x 1,25 > plafond
    plan_empty = plan_truncation_retry(b, output_tokens=1896, raw_text="")
    assert (plan_empty.allowed, plan_empty.max_tokens, plan_empty.items_completed) == (
        True,
        4000,
        0,
    )
    refused = plan_truncation_retry(fixed, output_tokens=8000, raw_text="{")
    assert refused.allowed is False
    assert refused.reason == "structured_output_retry_refused_output_budget"


def test_composition_bound_is_derived_from_the_options_contract_not_an_average() -> None:
    # n = 16, 5 options au plus : 80 groupes → 5 lots + 3 méta-passes → cœur 11 (= Mission #8 réel).
    core = consolidation_core_bound(16, 5, batch_size=16, meta_chunk_size=32)
    assert core == {
        "options_upper_bound": 80,
        "groups_upper_bound": 80,
        "batches_upper_bound": 5,
        "meta_passes_upper_bound": 3,
        "consolidation_calls_upper_bound": 8,
        "core_nominal_bound": 11,
    }
    # v1.3.6 (B15) : la borne inclut l'auto-qualification (ici une par position, g = 1 par
    # défaut de la fonction), le steelman obligatoire ET l'enveloppe de révision (⌈16/2⌉ = 8).
    b16 = minimal_deliberation_bound(
        16, effective_class="structurante", options_per_expert=5, batch_size=16, meta_chunk_size=32
    )
    assert b16["pre_deliberation_calls"] == 32
    assert b16["self_qualification_calls"] == 16
    assert b16["mandatory_steelman_calls"] == 2
    assert b16["revision_allowance"] == 8
    assert b16["minimal_deliberation_reserve"] == 16 + 2 + 8 + 11
    assert b16["reserve_components"]["core_nominal"] == 11
    assert b16["total_required_calls"] == 69  # > 59 : 16 experts infinançables à 60 appels
    assert (
        feasible_expert_count(
            59,
            effective_class="structurante",
            options_per_expert=5,
            batch_size=16,
            meta_chunk_size=32,
        )
        == 13
    )
    # Auto-qualification groupée par 3 (réglage produit) : 16 experts redeviennent finançables.
    assert (
        feasible_expert_count(
            59,
            effective_class="structurante",
            options_per_expert=5,
            batch_size=16,
            meta_chunk_size=32,
            self_qualification_group_max=3,
            self_qualification_ceiling=6000,
        )
        == 16
    )
    # Une seule position : ni auto-qualification, ni confrontation, ni steelman.
    b1 = minimal_deliberation_bound(
        1, effective_class="structurante", options_per_expert=5, batch_size=16, meta_chunk_size=32
    )
    assert (b1["pre_deliberation_calls"], b1["total_required_calls"]) == (1, 5)


# --- TEST C / D — faisabilité de composition par classe et densité d'options -------------------
@pytest.mark.parametrize("effective_class", ["courante", "importante", "structurante", "critique"])
@pytest.mark.parametrize("options_per_expert", [2, 3, 4, 5])
def test_feasible_expert_count_respects_the_invariant_with_equality_allowed(
    effective_class: str, options_per_expert: int
) -> None:
    settings = get_settings()
    ceiling = int(getattr(settings, f"mission_ceiling_calls_{effective_class}"))
    remaining = ceiling - 1
    n = feasible_expert_count(
        remaining,
        effective_class=effective_class,
        options_per_expert=options_per_expert,
        batch_size=16,
        meta_chunk_size=32,
    )
    assert n >= 2
    bound = minimal_deliberation_bound(
        n,
        effective_class=effective_class,
        options_per_expert=options_per_expert,
        batch_size=16,
        meta_chunk_size=32,
    )
    above = minimal_deliberation_bound(
        n + 1,
        effective_class=effective_class,
        options_per_expert=options_per_expert,
        batch_size=16,
        meta_chunk_size=32,
    )
    assert bound["total_required_calls"] <= remaining < above["total_required_calls"]
    # Cas limite exact : l'égalité est admise, un appel de moins refuse.
    exact = bound["total_required_calls"]

    def feasible(remaining_calls: int) -> int:
        return feasible_expert_count(
            remaining_calls,
            effective_class=effective_class,
            options_per_expert=options_per_expert,
            batch_size=16,
            meta_chunk_size=32,
        )

    assert feasible(exact) >= n
    assert feasible(exact - 1) < n or exact - 1 >= above["total_required_calls"]


def test_mission_with_exact_budget_is_accepted_and_one_call_less_is_refused(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    # 3 experts, 5 options au plus : 3 x 2 + 3 + cœur borné 4 = 13 appels après le cadrage.
    use_llm(DeliberationLLM())
    exact = _post(client, max_llm_calls=14)
    bounds = exact["composition"]["bounds"]
    assert bounds["total_required_calls"] == 13 == bounds["remaining_calls_at_composition"]
    assert bounds["plan_feasible"] is True
    assert len(exact["composition"]["experts"]) == 3
    assert exact["recommendation"]["status"] == "produced"
    use_llm(DeliberationLLM())
    short = _post(client, max_llm_calls=13)
    bounds = short["composition"]["bounds"]
    assert bounds["max_experts_feasible_deliberation"] == 2
    assert len(short["composition"]["experts"]) == 2  # profondeur / largeur réduites, jamais 3
    assert bounds["budget_plan"] == "coverage_first"
    assert len(short["composition"]["uncovered_dimensions"]) == 1
    assert short["recommendation"]["status"] == "produced"
    assert short["llm_calls_used"] <= 13


# --- TEST A / B — limites proportionnées à la tâche -------------------------------------------
def test_sixteen_positions_get_a_derived_self_qualification_budget_without_retry(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    llm = use_llm(DeliberationLLM(framing=SIXTEEN_FRAMING))
    mission = _post(client, declared_class="critique")
    assert len(mission["composition"]["experts"]) == 16
    assert mission["status"] == "candidate"
    planned = [
        e
        for e in _journal(client, mission["id"])
        if e["entry_type"] == "call_planned" and e["payload"]["call_type"] == "self_qualification"
    ]
    # v1.3.6 (§6) : auto-qualification groupée par 3 (6 appels : 5 x 3 + 1) ; la limite est
    # dérivée du nombre de relations à produire (3 x 15 = 45, puis 15) avec la marge de
    # raisonnement de catégorie C (500), sous le plafond relevé à 6 000.
    assert len(planned) == 6
    for p in planned[:5]:
        assert p["payload"]["number_of_required_items"] == 45
        assert "64 + 80 * 45 relations" in p["payload"]["output_budget"]["formula"]
        assert p["payload"]["max_tokens"] == 5996
    assert planned[5]["payload"]["number_of_required_items"] == 15
    assert planned[5]["payload"]["max_tokens"] == 2396
    for p in planned:
        assert p["payload"]["output_budget"]["floor"] == 1500
        assert p["payload"]["output_budget"]["ceiling"] == 6000
        assert p["payload"]["output_budget"]["reasoning_headroom"] == 500
    assert [c["max_tokens"] for c in llm.calls if c["call_type"] == "self_qualification"] == [
        5996
    ] * 5 + [2396]
    budget = mission["report"]["budget"]
    assert budget["structured_output_failures"] == 0
    assert budget["structured_output_retries"] == 0
    assert mission["cartography"]["divergence_index_partial"] is False


def test_small_team_keeps_the_historical_limit_without_inflation(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    llm = use_llm(DeliberationLLM())
    mission = _post(client)
    assert len(mission["composition"]["experts"]) == 3
    planned = next(
        e
        for e in _journal(client, mission["id"])
        if e["entry_type"] == "call_planned" and e["payload"]["call_type"] == "self_qualification"
    )
    ob = planned["payload"]["output_budget"]
    # v1.3.6 : un seul appel groupé (3 positions x 2 relations = 6) ; le plancher historique
    # (1 500) reste la base, augmentée de la seule marge de raisonnement de catégorie C (500).
    assert (ob["n_items"], ob["required_tokens"], ob["granted"]) == (6, 816, 2000)
    assert ob["raised_to_floor"] is True
    assert ob["reasoning_headroom"] == 500
    assert {c["max_tokens"] for c in llm.calls if c["call_type"] == "self_qualification"} == {2000}
    assert mission["recommendation"]["status"] == "produced"


# --- TEST E — plan réel dès la clôture du Tour 0 ----------------------------------------------
def test_real_consolidation_plan_is_computed_right_after_tour0(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    use_llm(
        DeliberationLLM(
            framing=SIXTEEN_FRAMING, options=options_for(16, 5), consolidation=competent_clerk
        )
    )
    mission = _post(client, declared_class="critique")
    entries = _journal(client, mission["id"])
    types = [e["entry_type"] for e in entries]
    closed = types.index("tour0_closed")
    planned_core = types.index("deliberation_core_planned")
    first_self_qual = next(
        i
        for i, e in enumerate(entries)
        if e["entry_type"] == "call_planned" and e["payload"]["call_type"] == "self_qualification"
    )
    assert closed < planned_core < first_self_qual
    core = entries[planned_core]["payload"]
    assert (core["options"], core["groups"], core["batches"], core["meta_passes"]) == (
        80,
        80,
        5,
        3,
    )
    assert core["core_nominal_calls"] == 11
    assert core["core_worst_calls"] == 20  # nominal + relances recalculées (8) + comparaison (1)
    assert core["minimal_cycle_calls"] == 16 + 11
    assert core["mandatory_steelman_calls"] == 2
    # v1.3.6 (B15) : réserve = confrontations 16 + steelman 2 + révisions ⌈16/2⌉ = 8 + cœur 11.
    assert core["revision_allowance"] == 8
    assert core["reserve_components"]["revisions"] == 8
    assert core["self_qualification_calls"] == 6
    assert core["self_qualification_group_size"] == 3
    assert core["reserved_deliberation_calls"] == 37
    assert mission["report"]["budget"]["reserved_deliberation_calls"] == 37
    # Toute auto-qualification est planifiée avec cette réserve connue.
    assert entries[first_self_qual]["payload"]["deliberation_reserve"] == 37


# --- TEST F — une relance B13 ne peut pas voler la confrontation ---------------------------------
def test_structured_retry_cannot_consume_the_deliberation_reserve(
    client: TestClient, use_llm: Callable[..., Any], settings_env: Callable[[str, str], None]
) -> None:
    # Auto-qualification une par position (g = 1) pour observer trois appels distincts.
    # 17 appels : borne 3 + 3 + 3 + 2 (révisions réservées) + cœur 4 = 15 ≤ 16. Après le Tour 0
    # (restant 13), la réserve vaut 3 auto-qualifications + 3 confrontations + 2 + 4 = 12.
    # E1 invalide (réserve hors E1 : 11) → relance admise (12 - 1 ≥ 11) ; E2 invalide (réserve
    # hors E2 : 10) → relance refusée (10 - 1 < 10) ; E3 : appel nominal financé par la réserve
    # elle-même (10 - 1 ≥ 9). Confrontation et porte restent finançables.
    settings_env("MISSION_SELF_QUALIFICATION_GROUP_MAX", "1")
    llm = use_llm(Breaking(DeliberationLLM(), "self_qualification", {1, 3}))
    mission = _post(client, max_llm_calls=17)
    assert mission["status"] == "candidate"
    assert mission["stop_reason"] == ""
    assert mission["recommendation"]["status"] == "produced"
    assert "porte_qualite" in mission["deliberation"]["steps_done"]
    assert "confrontation" in mission["deliberation"]["steps_done"]
    invalid = _entries(client, mission["id"], "structured_output_invalid")
    assert [p["payload"]["will_retry"] for p in invalid] == [True, False]
    assert (
        invalid[1]["payload"]["retry_refusal_reason"]
        == "structured_output_retry_refused_deliberation_reserve"
    )
    assert invalid[1]["payload"]["reserve_kind"] == "deliberation_reserve"
    assert invalid[1]["payload"]["reserved_calls_for_step"] == 10
    assert _entries(client, mission["id"], "skipped_for_deliberation_reserve") == []
    carto = mission["cartography"]
    assert carto["relations_missing_labels"] == ["P2"]
    assert carto["divergence_index_partial"] is True
    assert carto["self_qualification_coverage"] == "2/3"
    # Positions du Tour 0 conservées ; aucune relation inventée ; confrontation des trois.
    assert carto["experts_answered"] == 3
    assert len([c for c in llm.calls if c["call_type"] == "confrontation"]) == 3
    assert mission["llm_calls_used"] == 15


# --- TEST G / H — relance après troncature : limite recalculée ou refus ------------------------
def test_truncated_self_qualification_is_retried_with_a_recalculated_limit(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    llm = use_llm(NeedTokens(DeliberationLLM(), need=2500, items_when_cut=1))
    mission = _post(client)
    assert mission["status"] == "candidate"
    invalid = _entries(client, mission["id"], "structured_output_invalid")
    assert len(invalid) == 1  # un appel groupé (3 positions), première tentative coupée à 2 000
    plan = invalid[0]["payload"]["truncation_retry_plan"]
    assert plan["allowed"] is True
    assert plan["items_completed"] == 1
    # 2 000 tokens pour 1 élément complet → 6 éléments x 2 000 x 1,25 = 15 000, ramené au
    # plafond 6 000 (admissible car > limite initiale).
    assert plan["max_tokens"] == 6000
    assert invalid[0]["payload"]["retry_max_tokens"] == 6000
    retries = _entries(client, mission["id"], "structured_output_retry_planned")
    assert [r["payload"]["max_tokens"] for r in retries] == [6000]
    assert [r["payload"]["max_tokens_initial"] for r in retries] == [2000]
    results = _entries(client, mission["id"], "structured_output_retry_result")
    assert all(r["payload"]["valid"] for r in results)
    assert llm.granted == [2000, 6000]
    assert mission["report"]["budget"]["structured_output_retries"] == 1
    assert mission["cartography"]["relations_missing_labels"] == []


def test_truncated_retry_is_refused_when_no_larger_limit_is_admissible(
    client: TestClient, use_llm: Callable[..., Any], settings_env: Callable[[str, str], None]
) -> None:
    settings_env("MISSION_OUTPUT_CEILING_SELF_QUALIFICATION", "1500")  # plafond = plancher
    llm = use_llm(NeedTokens(DeliberationLLM(), need=2500, items_when_cut=1))
    mission = _post(client)
    assert mission["status"] == "candidate"  # information de second ordre : la mission continue
    invalid = _entries(client, mission["id"], "structured_output_invalid")
    assert len(invalid) == 1  # un appel groupé
    for p in invalid:
        assert p["payload"]["will_retry"] is False
        assert (
            p["payload"]["retry_refusal_reason"] == "structured_output_retry_refused_output_budget"
        )
        assert p["payload"]["truncation_retry_plan"]["allowed"] is False
    # Plafond 1 500 : la marge de raisonnement ne le franchit pas ; aucune augmentation
    # automatique, aucune relance.
    assert llm.granted == [1500]
    assert mission["report"]["budget"]["structured_output_retries"] == 0
    assert mission["cartography"]["relations_missing_labels"] == ["P1", "P2", "P3"]
    assert mission["cartography"]["divergence_index_partial"] is True
    assert mission["recommendation"]["status"] == "produced"


# --- TEST I — greffier vide : aucun faux contenu, mission poursuivie -----------------------------
def test_empty_clerk_is_exhausted_without_invented_output_and_mission_continues(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    inner = DeliberationLLM(relation="variant")  # ambiguïtés → greffier appelé
    llm = use_llm(WithBlocks(inner, {"text": 1}, empty_call_type="clerk", empty_output_tokens=3000))
    mission = _post(client)
    assert mission["status"] == "candidate"
    assert mission["cartography"]["clerk_used"] is False
    clerk_calls = [c for c in llm.calls if c["call_type"] == "clerk"]
    # Relance au plafond, une fois (3 000 + marge de raisonnement C 500, puis plafond 8 000).
    assert [c["max_tokens"] for c in clerk_calls] == [3500, 8000]
    result = _entries(client, mission["id"], "structured_output_retry_result")
    assert result[-1]["step"] == "greffier"
    assert result[-1]["payload"]["final"] == "structured_output_recovery_exhausted"
    assert result[-1]["payload"]["content_blocks"] == {"thinking": 1}
    assert all(g["source"] != "greffier" for g in mission["cartography"]["option_groups"])
    assert mission["recommendation"]["status"] == "produced"


# --- TEST J — blocs non textuels : métadonnées seulement --------------------------------------
def test_content_block_metadata_are_journaled_without_private_content(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    class _Block:
        def __init__(self, type_: str, text: str | None = None) -> None:
            self.type = type_
            if text is not None:
                self.text = text

    assert count_content_blocks([_Block("thinking"), _Block("text", "a"), _Block("text", "b")]) == {
        "thinking": 1,
        "text": 2,
    }
    assert count_content_blocks(None) == {}
    llm = use_llm(WithBlocks(DeliberationLLM(), {"thinking": 1, "text": 1}))
    mission = _post(client)
    entries = _journal(client, mission["id"])
    done = [e for e in entries if e["entry_type"] == "call_done"]
    assert done
    assert all(e["payload"]["content_blocks"] == {"thinking": 1, "text": 1} for e in done)
    assert all(e["payload"]["non_text_blocks"] == 1 for e in done)
    assert all(isinstance(e["payload"]["output_tokens_per_text_char"], float) for e in done)
    assert all(e["payload"]["text_chars"] == e["payload"]["raw_length_chars"] for e in done)
    dumped = json.dumps(entries, ensure_ascii=False)
    assert (
        "reasoning = " not in dumped
    )  # aucune interprétation automatique de la part non textuelle
    assert mission["cost_eur"] > 0
    assert llm.calls
    # Réponse sans texte à pleine limite : classée vide, blocs comptés, ratio marqué « no_text ».
    use_llm(WithBlocks(DeliberationLLM(), {"text": 1}, empty_call_type="self_qualification"))
    mission = _post(client)
    invalid = _entries(client, mission["id"], "structured_output_invalid")
    assert invalid[0]["payload"]["category"] == "structured_output_empty"
    assert invalid[0]["payload"]["content_blocks"] == {"thinking": 1}
    assert invalid[0]["payload"]["text_chars"] == 0
    assert invalid[0]["payload"]["output_tokens_per_text_char"] == "no_text"


# --- TEST K — gabarit : aucune « dimension critique » sans dimension absente -------------------
def test_budget_request_template_never_mentions_critical_dimensions_when_none_is_missing() -> None:
    delib = {
        "detected_at_step": "composition",
        "minimal_deliberation_calls": 13,
        "remaining_calls": 8,
        "additional_calls_estimate": 5,
        "advice": "relever le plafond",
    }
    lines = budget_request_lines(delib)
    assert len(lines) == 1
    assert "critique" not in lines[0]
    assert "cycle minimal estimé à 13" in lines[0]
    assert "déficit ≈ 5" in lines[0]
    assert "composition" in lines[0]
    critical = budget_request_lines(
        {"uncovered_critical_dimensions": ["d1"], "additional_calls_estimate": 3, "advice": "x"}
    )
    assert "Dimensions critiques non couvertes : d1" in critical[0]


# --- TEST L — dimension critique sacrifiée : arrêt explicite -----------------------------------
def test_high_dimension_is_never_silently_dropped_to_fit_the_budget(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    # 4 dimensions critiques ; 17 appels : 3 experts délibérables (3 x 2 + 3 + 4 = 13 ≤ 16), pas 4
    # (4 x 2 + 4 + 6 = 18 > 16) → une dimension high disparaîtrait : arrêt fail-closed, 1 appel.
    llm = use_llm(DeliberationLLM(FOUR_CRITICAL_FRAMING))
    mission = _post(client, max_llm_calls=17)
    assert mission["stop_reason"] == "critical_dimension_uncovered"
    assert [c["call_type"] for c in llm.calls] == ["framing"]
    assert mission["composition"]["bounds"]["max_experts_feasible_deliberation"] == 3
    assert len(mission["composition"]["uncovered_dimensions"]) == 1
    br = mission["deliberation"]["budget_request"]
    assert br["uncovered_critical_dimensions"] == mission["composition"]["uncovered_dimensions"]
    assert mission["recommendation"] is None


# --- TEST M / R — largeur non délibérable jamais engagée ; traversée complète sous 60 appels
@pytest.mark.parametrize("n_dims", [17, 20, 25, 30])
def test_many_dimensions_never_engage_an_unfundable_width(
    client: TestClient, use_llm: Callable[..., Any], n_dims: int
) -> None:
    llm = use_llm(DeliberationLLM(framing=wide_framing(n_dims, ["high"])))
    mission = _post(client, declared_class="structurante")
    # Toutes critiques : 16 délibérables au plus (v1.3.6 : réserve B15 complète, auto-
    # qualification groupée) → des dimensions high disparaîtraient → arrêt explicite après le
    # seul cadrage, jamais un Tour 0 large sans délibération.
    assert mission["stop_reason"] == "critical_dimension_uncovered"
    assert [c["call_type"] for c in llm.calls] == ["framing"]
    assert mission["composition"]["bounds"]["max_experts_feasible_deliberation"] == 16
    assert mission["composition"]["bounds"]["budget_plan"] == "coverage_first"


def test_structurante_mission_with_reducible_width_traverses_to_the_gate_within_60_calls(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    # 20 dimensions dont 5 critiques : profondeur réduite puis 4 dimensions low retirées
    # (journalisées) → 16 experts délibérables (v1.3.6) ; la mission traverse cadrage → Tour 0 →
    # confrontation → steelman → consolidation → comparaison → synthèse → porte sous 60 appels.
    llm = use_llm(DeliberationLLM(framing=wide_framing(20, ["high", "low", "low", "low"])))
    mission = _post(client, declared_class="structurante")
    assert mission["status"] == "candidate"
    assert mission["stop_reason"] == ""
    bounds = mission["composition"]["bounds"]
    assert bounds["plan_feasible"] is True
    assert len(mission["composition"]["experts"]) == 16
    assert len(mission["composition"]["uncovered_dimensions"]) == 4
    critical = {
        d["name"]
        for d in json.loads(json.dumps(wide_framing(20, ["high", "low", "low", "low"])))[
            "dimensions"
        ]
        if d["presumed_criticality"] == "high"
    }
    assert not critical & set(mission["composition"]["uncovered_dimensions"])
    done = mission["deliberation"]["steps_done"]
    for step in (
        "confrontation",
        "steelman",
        "consolidation",
        "comparaison",
        "synthese",
        "porte_qualite",
    ):
        assert step in done, step
    assert mission["recommendation"]["status"] == "produced"
    assert mission["recommendation"]["gate"]["passed"] is True
    assert mission["llm_calls_used"] <= 60
    assert mission["cost_eur"] <= 8.0
    assert len([c for c in llm.calls if c["call_type"] == "expert_tour0"]) == 16


# --- TEST P — B10 / B12 pendant une étape protégée par la réserve ----------------------------
def test_provider_retry_and_uncertain_cost_do_not_bypass_the_reserve(
    client: TestClient, use_llm: Callable[..., Any], sleeps: list[float]
) -> None:
    # 529 sur la première auto-qualification : B10 relance (tentative physique), aucun appel
    # logique de plus, réserve intacte, mission complète sous le même plafond.
    use_llm(FlakyLLM(DeliberationLLM(), {"self_qualification": [overloaded()]}))
    mission = _post(client, max_llm_calls=14)
    assert mission["status"] == "candidate"
    # v1.3.6 : 1 + 3 + 1 (groupée) + 3 + 0 révision demandée + 1 + 1 + 1 + 1 = 12 appels logiques.
    assert mission["llm_calls_used"] == 12
    budget = mission["report"]["budget"]
    assert budget["provider_retries"] == 1
    assert budget["structured_output_retries"] == 0
    assert budget["reserved_deliberation_calls"] == 9  # 3 confrontations + 2 révisions + cœur 4
    assert len(sleeps) == 1
    # Délai ambigu sous plafond financier serré pendant l'auto-qualification : B12 refuse la
    # relance fournisseur (connu + incertain + estimation > plafond), échec explicite, aucun
    # contournement financier ni d'appels. Le Tour 0 facture une sortie réaliste (5 000 tokens
    # par expert) et le plafond est dérivé des traces d'une mission témoin : coût connu avant la
    # première auto-qualification + estimation de cet appel (une tentative tient exactement ;
    # connu + tentative incertaine + relance ne tient pas).
    use_llm(Costly(DeliberationLLM(), "expert_tour0", 5000))
    witness = _post(client, max_llm_calls=14)
    assert witness["status"] == "candidate"
    known = 0.0
    estimate = 0.0
    worst_before = 0.0
    for e in _journal(client, witness["id"]):
        if e["entry_type"] == "call_planned":
            est = float(e["payload"]["estimated_cost_eur_upper_bound"])
            if e["payload"]["call_type"] == "self_qualification":
                estimate = est
                break
            worst_before = max(worst_before, known + est)
        if e["entry_type"] == "call_done":
            known += float(e["payload"]["cost_eur"])
    assert estimate > 0
    cap = round(known + estimate + 1e-6, 6)
    assert worst_before <= cap  # tout appel antérieur tient sous ce plafond
    use_llm(
        FlakyLLM(
            Costly(DeliberationLLM(), "expert_tour0", 5000),
            {"self_qualification": [ambiguous_timeout()]},
        )
    )
    mission = _post(client, max_llm_calls=14, max_cost_eur=cap)
    assert mission["status"] == "failed"
    assert mission["stop_reason"] == "retry_refused_uncertain_cost_budget"
    assert (
        mission["llm_calls_used"] == 4
    )  # cadrage + 3 experts ; la tentative incertaine ne compte pas
    budget = mission["report"]["budget"]
    assert budget["uncertain_attempts"] == 1
    assert budget["potential_total_cost_upper_bound_eur"] <= cap
    assert budget["potential_total_cost_upper_bound_eur"] + estimate > cap
    assert budget["reserved_deliberation_calls"] == 9
    assert budget["known_cost_eur"] == round(known, 6)
