"""OT-V1, incrément 1 — missions de cadrage : Tour 0 isolé, composition émergente, budget, rapport.

Tous les tests utilisent un **faux client LLM structuré** et des **fixtures abstraites** (aucun cas
réel, aucun banc d'essai, aucun domaine métier particulier). Ils prouvent le comportement du
mécanisme, pas la qualité des réponses d'un modèle : par exemple, « une contestation remonte quand le
cadrage en produit une », et non « le modèle conteste ce qu'il faut ».
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest
from app.db import LLMCallLog, Mission
from app.llm import LLMClient, LLMResponse, LLMUsage, StructuredCompletionUnsupportedError
from app.mission_budget import BudgetExceededError, BudgetLedger
from app.mission_schemas import (
    FORBIDDEN_CLERK_FIELDS,
    EvidenceOut,
    clerk_schema_field_names,
    parse_structured,
)
from app.observability import ObservedLLMClient
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

# --- Fixtures abstraites (aucun cas réel) -----------------------------------------------------
SIMPLE_FRAMING: dict[str, Any] = {
    "problem_understood": "situation A : un besoin simple et réversible",
    "assumed_objective": "réduire un écart mesurable",
    "constraints": ["budget faible"],
    "assumptions": ["le demandeur suppose que l'écart vient d'un seul facteur"],
    "global_unknowns": ["mesure actuelle de l'écart"],
    "dimensions": [
        {
            "name": "organisation",
            "why": "l'écart se joue dans l'organisation quotidienne",
            "presumed_criticality": "low",
            "unknowns": [],
            "suggested_angles": ["praticien de terrain"],
        }
    ],
    "contestation": {"status": "none", "target": "", "argument": ""},
    "escalation_signals": [],
    "suggested_class": "",
}

COMPLEX_FRAMING: dict[str, Any] = {
    "problem_understood": "situation B : un engagement lourd fondé sur une promesse non écrite",
    "assumed_objective": "sécuriser l'avenir sans mettre l'ensemble en péril",
    "constraints": ["décision attendue sous trois mois", "capacité financière limitée"],
    "assumptions": ["la promesse sera tenue", "ne pas agir revient à perdre"],
    "global_unknowns": [
        "ce que la contrepartie acceptera de signer",
        "calendrier réel de la contrepartie",
        "existence d'alternatives locales",
    ],
    "dimensions": [
        {
            "name": "contractuel",
            "why": "tout repose sur un engagement oral",
            "presumed_criticality": "high",
            "unknowns": ["forme d'engagement obtenable"],
            "suggested_angles": ["juriste des contrats", "sceptique / adversaire"],
        },
        {
            "name": "financier",
            "why": "l'engagement mobilise toute la capacité",
            "presumed_criticality": "medium",
            "unknowns": ["point mort du projet"],
            "suggested_angles": ["mesure et chiffres"],
        },
        {
            "name": "humain",
            "why": "des personnes clés devraient se déplacer",
            "presumed_criticality": "low",
            "unknowns": [],
            "suggested_angles": [],
        },
    ],
    "contestation": {
        "status": "raised",
        "target": "hypothèse « ne pas agir revient à perdre »",
        "argument": "la perte est probable à terme mais ni certaine ni immédiate",
    },
    "escalation_signals": ["engagement irréversible de toute la capacité financière"],
    "suggested_class": "structurante",
}

EXPERT_POSITIONS = {
    "E1": "conditionner tout engagement à un contrat écrit",
    "E2": "construire un chemin progressif plutôt qu'un engagement total",
    "E3": "attendre et vérifier le calendrier réel avant de décider",
    "E4": "s'adosser à un partenaire plutôt que porter seul le capital",
    "E5": "refuser et diversifier",
}


def expert_output(expert_id: str, kind: str = "build", with_bad_evidence: bool = False) -> dict:
    """Exposé abstrait d'un expert : options distinctes, inconnues, preuves typées."""
    evidence = [
        {
            "claim": "fait tiré de l'entrée",
            "source": "entrée du demandeur, §2",
            "status": "verified",
        },
        {"claim": "ordre de grandeur habituel", "source": "", "status": "model_knowledge"},
    ]
    if with_bad_evidence:
        # Une preuve déclarée « verified » SANS source : doit être rétrogradée par le schéma.
        evidence.append({"claim": "chiffre précis sans source", "source": "", "status": "verified"})
    return {
        "position": EXPERT_POSITIONS.get(expert_id, f"position {expert_id}"),
        "reasoning": f"raisonnement de {expert_id}",
        "assumptions": [f"hypothèse propre à {expert_id}"],
        "risks": [f"risque vu par {expert_id}"],
        "unknowns": [f"inconnue vue par {expert_id}"],
        "to_verify": [f"élément à vérifier selon {expert_id}"],
        "options": [{"label": f"option {expert_id}", "summary": "…", "kind": kind}],
        "objections": [
            {"text": f"objection de {expert_id}", "target": "hypothèse", "nature": "hypothesis"}
        ],
        "evidence": evidence,
    }


class ScriptedStructuredLLM:
    """Faux client structuré : réponses par type d'appel, enregistrement de chaque appel."""

    def __init__(
        self,
        framing: dict[str, Any],
        *,
        expert_kinds: dict[str, str] | None = None,
        relation: str = "different",
        bad_evidence_for: set[str] | None = None,
        usage: LLMUsage = LLMUsage(input_tokens=1000, output_tokens=500),
    ) -> None:
        self.framing = framing
        self.expert_kinds = expert_kinds or {}
        self.relation = relation
        self.bad_evidence_for = bad_evidence_for or set()
        self.usage = usage
        self.calls: list[dict[str, Any]] = []

    def complete(self, prompt: str) -> str:
        raise AssertionError("le chemin historique ne doit pas être utilisé par une mission")

    def complete_structured(
        self, *, system: str, prompt: str, call_type: str, max_tokens: int
    ) -> LLMResponse:
        self.calls.append(
            {"system": system, "prompt": prompt, "call_type": call_type, "max_tokens": max_tokens}
        )
        if call_type == "framing":
            payload: Any = self.framing
        elif call_type == "expert_tour0":
            expert_id = _expert_id_from_prompt(prompt)
            payload = expert_output(
                expert_id,
                kind=self.expert_kinds.get(expert_id, "build"),
                with_bad_evidence=expert_id in self.bad_evidence_for,
            )
        elif call_type == "self_qualification":
            others = [
                line.split(" : ")[0].strip("- ").strip()
                for line in prompt.splitlines()
                if line.startswith("- P")
            ]
            payload = {
                "relations": [
                    {"other_id": o, "relation": self.relation, "reason": "abstrait"} for o in others
                ]
            }
        elif call_type == "clerk":
            payload = {
                "groups": [
                    {"option_ids": ["E1-O1", "E2-O1"], "label": "groupe", "motivation": "m"}
                ],
                "disagreements": [
                    {"between": ["P1", "P3"], "nature": "fact", "description": "un fait diverge"}
                ],
            }
        else:  # pragma: no cover - garde-fou
            raise AssertionError(f"type d'appel inconnu : {call_type}")
        return LLMResponse(text=json.dumps(payload, ensure_ascii=False), usage=self.usage)


def _expert_id_from_prompt(prompt: str) -> str:
    for line in prompt.splitlines():
        if line.startswith("Identifiant : "):
            return line.split(":", 1)[1].strip()
    raise AssertionError("prompt d'expert sans identifiant")


_CURRENT_LLM: dict[str, ScriptedStructuredLLM] = {}


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    """Injecte le faux client courant (défini par `use_llm`) dans l'application."""

    def factory() -> LLMClient:
        return _CURRENT_LLM["llm"]

    return factory


@pytest.fixture
def use_llm() -> Callable[[ScriptedStructuredLLM], ScriptedStructuredLLM]:
    def _set(llm: ScriptedStructuredLLM) -> ScriptedStructuredLLM:
        _CURRENT_LLM["llm"] = llm
        return llm

    _CURRENT_LLM["llm"] = ScriptedStructuredLLM(SIMPLE_FRAMING)
    return _set


def _post_mission(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload = {"input_type": "problem", "input_text": "entrée abstraite de test"}
    payload.update(overrides)
    response = client.post("/missions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# --- Tour 0 isolé ---------------------------------------------------------------------------
def test_tour0_is_isolated_one_call_per_expert(
    client: TestClient, use_llm: Callable[..., ScriptedStructuredLLM]
) -> None:
    llm = use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING))
    mission = _post_mission(client)
    expert_calls = [c for c in llm.calls if c["call_type"] == "expert_tour0"]
    experts = mission["composition"]["experts"]
    assert len(expert_calls) == len(experts) >= 2
    ids = [_expert_id_from_prompt(c["prompt"]) for c in expert_calls]
    assert len(set(ids)) == len(ids)  # N experts = N contextes distincts
    for call in expert_calls:
        own = _expert_id_from_prompt(call["prompt"])
        for other_id, position in EXPERT_POSITIONS.items():
            if other_id != own:
                assert position not in call["prompt"]  # aucun exposé d'un autre expert
        assert "=== DOSSIER DE CADRAGE" in call["prompt"]


def test_journal_proves_isolation_after_the_fact(
    client: TestClient, use_llm: Callable[..., ScriptedStructuredLLM]
) -> None:
    use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING))
    mission = _post_mission(client)
    journal = client.get(f"/missions/{mission['id']}/journal").json()
    planned = [e for e in journal if e["step"] == "tour0" and e["entry_type"] == "call_planned"]
    assert planned
    for entry in planned:
        prompt = entry["payload"]["prompt_text"]
        assert entry["payload"]["prompt_sha256"]
        own = _expert_id_from_prompt(prompt)
        for other_id, position in EXPERT_POSITIONS.items():
            if other_id != own:
                assert position not in prompt
    closed = [e for e in journal if e["entry_type"] == "tour0_closed"]
    assert len(closed) == 1
    # L'auto-qualification n'intervient qu'après la clôture du Tour 0.
    seqs_tour0 = [e["seq"] for e in planned]
    seqs_selfq = [e["seq"] for e in journal if e["step"] == "auto_qualification"]
    assert seqs_selfq and min(seqs_selfq) > max(seqs_tour0)


# --- Composition émergente ------------------------------------------------------------------
def test_two_problems_two_compositions(
    client: TestClient, use_llm: Callable[..., ScriptedStructuredLLM]
) -> None:
    use_llm(ScriptedStructuredLLM(SIMPLE_FRAMING))
    simple = _post_mission(client)
    use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING))
    complex_ = _post_mission(client)
    simple_cells = simple["composition"]["cells"]
    complex_cells = complex_["composition"]["cells"]
    assert simple_cells != complex_cells
    assert len(simple["composition"]["experts"]) <= 2  # cas simple : ≤ 2 experts
    assert len(complex_["composition"]["experts"]) > len(simple["composition"]["experts"])
    # La profondeur suit la criticité présumée, bornée par le budget ; rien de fixe.
    by_dim = {c["dimension"]: c["depth"] for c in complex_cells}
    assert by_dim["contractuel"] >= by_dim["humain"]


def test_no_fixed_number_of_experts_is_doctrine(
    client: TestClient, use_llm: Callable[..., ScriptedStructuredLLM]
) -> None:
    use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING))
    mission = _post_mission(client)
    bounds = mission["composition"]["bounds"]
    assert "expérimentale" in bounds["max_angles_per_cell_nature"]
    assert "non doctrinale" in bounds["max_angles_per_cell_nature"]
    # Le plafond de 12 appels borne économiquement le Tour 0 (1 + N + N + 1 ≤ 12 → N ≤ 5).
    assert bounds["max_experts_by_budget"] == 5
    assert len(mission["composition"]["experts"]) <= 5
    assert mission["llm_calls_used"] <= 12


def test_ceo_preference_adds_a_contradicting_perspective_only_when_present(
    client: TestClient, use_llm: Callable[..., ScriptedStructuredLLM]
) -> None:
    use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING))
    without = _post_mission(client)
    assert not any(e["contradicts_preference"] for e in without["composition"]["experts"])
    use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING))
    with_pref = _post_mission(client, ceo_preference="je penche pour l'engagement total")
    contradictors = [e for e in with_pref["composition"]["experts"] if e["contradicts_preference"]]
    assert len(contradictors) == 1
    assert contradictors[0]["angle_title"] == "Red Team / adversaire"
    assert "préférence" in contradictors[0]["justification"]
    journal = with_pref["composition"]["journal"]
    assert any(j["event"] == "perspective_contraire_preference" for j in journal)


# --- Cadrage : contestation, inconnues, classe -----------------------------------------------
def test_contestation_surfaces_when_framing_raises_it_and_not_otherwise(
    client: TestClient, use_llm: Callable[..., ScriptedStructuredLLM]
) -> None:
    use_llm(ScriptedStructuredLLM(SIMPLE_FRAMING))
    sane = _post_mission(client)
    assert sane["report"]["contestation"]["status"] == "none"
    use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING))
    contested = _post_mission(client)
    assert contested["report"]["contestation"]["status"] == "raised"
    assert "ne pas agir" in contested["report"]["contestation"]["target"]
    md = client.get(f"/missions/{contested['id']}/report/markdown").json()["markdown"]
    assert "Contestation soulevée" in md


def test_unknowns_are_structured_and_counted(
    client: TestClient, use_llm: Callable[..., ScriptedStructuredLLM]
) -> None:
    use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING))
    mission = _post_mission(client)
    unknown = mission["report"]["epistemic"]["unknown"]
    assert len(unknown["global"]) == 3
    assert unknown["total"] >= 3 + len(mission["composition"]["experts"])
    assert any(d["dimension"] == "contractuel" for d in unknown["by_dimension"])


def test_class_is_provisional_by_default_and_escalated_by_framing(
    client: TestClient, use_llm: Callable[..., ScriptedStructuredLLM]
) -> None:
    use_llm(ScriptedStructuredLLM(SIMPLE_FRAMING))
    simple = _post_mission(client)
    assert simple["effective_class"] == "importante_provisoire"
    assert simple["class_is_provisional"] is True
    use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING))
    escalated = _post_mission(client)
    assert escalated["effective_class"] == "structurante"
    assert "escaladée" in escalated["report"]["class"]["escalation"]
    use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING))
    declared = _post_mission(client, declared_class="importante")
    assert declared["effective_class"] == "importante"  # la classe CEO n'est pas écrasée
    assert "soumise au CEO" in declared["report"]["class"]["escalation"]


# --- Cartographie : options séparées, greffier, schéma fermé --------------------------------
def test_options_stay_distinct_and_non_action_is_recognised(
    client: TestClient, use_llm: Callable[..., ScriptedStructuredLLM]
) -> None:
    use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING, expert_kinds={"E3": "wait", "E4": "integrate"}))
    mission = _post_mission(client)
    carto = mission["cartography"]
    assert carto["distinct_option_groups"] >= 3
    assert carto["non_action_option_present"] is True
    assert carto["divergence_index"] > 0
    assert all("rank" not in g and "preference" not in g for g in carto["option_groups"])


def test_clerk_called_only_on_residual_ambiguity(
    client: TestClient, use_llm: Callable[..., ScriptedStructuredLLM]
) -> None:
    llm = use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING, relation="different"))
    mission = _post_mission(client)
    assert not [c for c in llm.calls if c["call_type"] == "clerk"]
    assert mission["cartography"]["clerk_used"] is False
    llm = use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING, relation="variant"))
    mission = _post_mission(client)
    clerk_calls = [c for c in llm.calls if c["call_type"] == "clerk"]
    assert len(clerk_calls) == 1
    assert mission["cartography"]["clerk_used"] is True
    assert any(g["source"] == "greffier" for g in mission["cartography"]["option_groups"])
    assert mission["llm_calls_used"] <= 12


def test_clerk_schema_has_no_preference_ranking_or_recommendation_field() -> None:
    names = {n.lower() for n in clerk_schema_field_names()}
    assert not (names & FORBIDDEN_CLERK_FIELDS)


# --- Honnêteté des preuves ------------------------------------------------------------------
def test_evidence_verified_without_source_is_downgraded() -> None:
    ev = EvidenceOut(claim="x", source="", status="verified")
    assert ev.status == "unverified"
    parsed, error = parse_structured('{"claim": "y", "status": "verified"}', EvidenceOut)
    assert error == "" and parsed is not None and parsed.status == "unverified"


def test_report_marks_unverified_evidence(
    client: TestClient, use_llm: Callable[..., ScriptedStructuredLLM]
) -> None:
    use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING, bad_evidence_for={"E1"}))
    mission = _post_mission(client)
    unverified = mission["report"]["epistemic"]["unverified"]
    assert any(u["text"] == "chiffre précis sans source" for u in unverified)
    assert all(u["status"] in {"unverified", "model_knowledge"} for u in unverified)
    fields = mission["report"]["fourteen_fields"]
    assert "non encore délibéré" in fields["07_arguments_pour"]
    assert "aucune recommandation" in fields["10_recommandation"]["status"]


# --- Budget : tokens/coût journalisés, arrêt dur, rapport partiel -----------------------------
def test_tokens_and_cost_are_logged_per_call_and_per_mission(
    client: TestClient,
    use_llm: Callable[..., ScriptedStructuredLLM],
    session_factory: sessionmaker[Session],
) -> None:
    use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING))
    mission = _post_mission(client)
    with session_factory() as session:
        rows = list(
            session.execute(
                select(LLMCallLog).where(LLMCallLog.mission_id == mission["id"])
            ).scalars()
        )
    assert len(rows) == mission["llm_calls_used"] >= 3
    assert all(r.input_tokens == 1000 and r.output_tokens == 500 for r in rows)
    assert all(r.cost_eur is not None and r.cost_eur > 0 for r in rows)
    assert {r.call_type for r in rows} >= {"framing", "expert_tour0", "self_qualification"}
    assert mission["input_tokens"] == 1000 * len(rows)
    assert mission["cost_eur"] == pytest.approx(sum(r.cost_eur for r in rows), abs=1e-6)


def test_ledger_refuses_the_call_after_the_cap() -> None:
    ledger = BudgetLedger(
        max_calls=12, max_cost_eur=2.0, price_in_per_mtok=3, price_out_per_mtok=15
    )
    for _ in range(12):
        ledger.check_before_call(system="s", prompt="p", max_tokens=100, call_type="t")
        ledger.record(LLMUsage(input_tokens=10, output_tokens=10))
    with pytest.raises(BudgetExceededError) as exc:
        ledger.check_before_call(system="s", prompt="p", max_tokens=100, call_type="t")
    assert exc.value.reason == "max_calls_reached" and ledger.calls_used == 12


def test_hard_stop_before_exceeding_max_calls(
    client: TestClient,
    use_llm: Callable[..., ScriptedStructuredLLM],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # La composition réserve normalement les appels ; on la force à planifier plus d'experts que
    # le plafond ne permet, pour prouver que l'arrêt dur du registre s'exerce quand même.
    monkeypatch.setattr(BudgetLedger, "max_affordable_experts", lambda self, **_: 5)
    llm = use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING))
    mission = _post_mission(client, max_llm_calls=4)
    assert len(mission["composition"]["experts"]) == 5
    assert len(llm.calls) == 4  # cadrage + 3 experts ; le 5e appel est refusé
    assert mission["llm_calls_used"] == 4
    assert mission["stop_reason"] == "max_calls_reached"
    assert mission["status"] == "candidate"
    assert mission["report"]["partial"] is True
    journal = client.get(f"/missions/{mission['id']}/journal").json()
    assert any(e["entry_type"] == "budget_stop" for e in journal)
    assert any(e["entry_type"] == "expert_skipped" for e in journal)


@pytest.fixture
def expensive_output_price(monkeypatch: pytest.MonkeyPatch) -> None:
    """Barème de sortie très élevé : le plafond de 2 € est atteint en quelques appels."""
    monkeypatch.setenv("LLM_PRICE_OUTPUT_EUR_PER_MTOK", "600")


def test_hard_stop_before_exceeding_cost_cap(
    expensive_output_price: None,
    client: TestClient,
    use_llm: Callable[..., ScriptedStructuredLLM],
) -> None:
    llm = use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING))
    mission = _post_mission(client)
    assert mission["max_cost_eur"] == 2.0
    assert mission["cost_eur"] <= 2.0
    assert mission["stop_reason"] == "cost_cap_would_be_exceeded"
    # Chaque appel effectué avait, avant lancement, un coût majoré compatible avec le plafond.
    assert len(llm.calls) < 12
    refusals = mission["report"]["budget"]["refusals"]
    assert refusals and refusals[-1]["reason"] == "cost_cap_would_be_exceeded"


def test_partial_report_is_coherent_after_budget_stop(
    client: TestClient, use_llm: Callable[..., ScriptedStructuredLLM]
) -> None:
    use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING))
    # Budget trop étroit pour explorer : le cadrage a lieu, aucun expert n'est finançable.
    mission = _post_mission(client, max_llm_calls=2)
    report = mission["report"]
    assert report["partial"] is True
    assert report["stop_reason"] == "budget_insufficient_for_exploration"
    assert report["composition"]["experts_total"] == 0
    assert report["contestation"]["status"] == "raised"  # le cadrage est conservé
    assert report["epistemic"]["unknown"]["total"] >= 3
    assert report["alternatives"] == []
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "partiel" in md and "budget_insufficient_for_exploration" in md
    # Budget intermédiaire : la composition se contraint d'elle-même (aucun arrêt nécessaire).
    use_llm(ScriptedStructuredLLM(COMPLEX_FRAMING))
    mission = _post_mission(client, max_llm_calls=6)
    assert mission["stop_reason"] == "" and mission["llm_calls_used"] <= 6
    assert len(mission["composition"]["experts"]) == 2


# --- Gouvernance : rapport candidate, actions CEO, aucune exécution -------------------------
def test_report_stays_candidate_until_explicit_ceo_action(
    client: TestClient, use_llm: Callable[..., ScriptedStructuredLLM]
) -> None:
    llm = use_llm(ScriptedStructuredLLM(SIMPLE_FRAMING))
    mission = _post_mission(client)
    assert mission["status"] == "candidate"
    calls_before = len(llm.calls)
    approved = client.post(f"/missions/{mission['id']}/approve", json={"ceo_notes": "lu"}).json()
    assert approved["status"] == "approved" and approved["ceo_notes"] == "lu"
    assert len(llm.calls) == calls_before  # approuver ne déclenche aucun appel ni exécution
    again = client.post(f"/missions/{mission['id']}/reject")
    assert again.status_code == 409
    events = client.get("/observability/events", params={"phase": "otv1_inc1"}).json()
    assert {e["event_type"] for e in events} >= {"mission_report_ready", "mission_approved"}


def test_missing_mission_and_listing(client: TestClient) -> None:
    assert client.get("/missions/999").status_code == 404
    assert client.get("/missions/999/journal").status_code == 404
    assert client.get("/missions").json() == []


def test_blank_input_rejected(client: TestClient) -> None:
    assert client.post("/missions", json={"input_text": "   "}).status_code == 422


# --- Compatibilité du client historique ------------------------------------------------------
class _LegacyOnly:
    def complete(self, prompt: str) -> str:
        return "ok"


def test_observed_client_keeps_legacy_path_and_refuses_silent_fallback(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        wrapped = ObservedLLMClient(_LegacyOnly(), session, "p", "a", "op")
        assert wrapped.complete("x") == "ok"
        with pytest.raises(StructuredCompletionUnsupportedError):
            wrapped.complete_structured(system="s", prompt="p", call_type="t", max_tokens=10)
        session.commit()
        row = session.execute(select(LLMCallLog)).scalars().one()
        assert row.input_tokens is None and row.cost_eur is None and row.call_type is None


def test_mission_rows_persisted(
    client: TestClient,
    use_llm: Callable[..., ScriptedStructuredLLM],
    session_factory: sessionmaker[Session],
) -> None:
    use_llm(ScriptedStructuredLLM(SIMPLE_FRAMING))
    mission = _post_mission(client)
    with session_factory() as session:
        row = session.get(Mission, mission["id"])
        assert row is not None and row.status == "candidate"
        assert json.loads(row.report_json)["mission_id"] == mission["id"]
