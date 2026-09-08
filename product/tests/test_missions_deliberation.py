"""OT-V1, incrément 2 — délibération probante → recommandation décisionnelle.

Tous les tests utilisent un **faux client LLM structuré** scriptable par type d'appel et des
**fixtures purement synthétiques** (dimensions alpha / beta / gamma, positions « P-n », options
« option A / A bis / C », questions « Q1 synthétique »). Aucun cas réel, aucun problème scellé,
aucun domaine métier. Ils prouvent le comportement du **mécanisme** (adressage des actes,
steelman ≠ strawman, recherche déclenchée par un fait, révision sous preuve et non sous
insistance, consolidation traçable, minorités conservées, budget dur, gouvernance), jamais la
qualité des réponses d'un modèle.

Chaque scénario enregistre ses appels par type et son coût (rapport `OTV1_SCENARIO_REPORT`).
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from app.db import LLMCallLog
from app.llm import LLMClient, LLMResponse, LLMUsage
from app.mission_deliberation import (
    COMPARISON_SYSTEM,
    REVISION_SYSTEM,
    STEELMAN_SYSTEM,
    is_premature_convergence,
    strawman_flags,
)
from app.mission_research import ResearchFinding, ResearchResult, UnavailableResearchProvider
from app.mission_schemas import (
    FORBIDDEN_COMPARISON_FIELDS,
    SteelmanOutput,
    comparison_schema_field_names,
)
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

# --- Fixtures abstraites -------------------------------------------------------------------------
THREE_DIM_FRAMING: dict[str, Any] = {
    "problem_understood": "cas synthétique D : trois dimensions de faible criticité",
    "assumed_objective": "objectif synthétique D",
    "constraints": ["contrainte C1"],
    "assumptions": ["hypothèse H1"],
    "global_unknowns": ["inconnue U1"],
    "dimensions": [
        {
            "name": "dimension alpha",
            "why": "première dimension du cas synthétique D",
            "presumed_criticality": "low",
            "unknowns": [],
            "suggested_angles": ["praticien"],
        },
        {
            "name": "dimension beta",
            "why": "deuxième dimension du cas synthétique D",
            "presumed_criticality": "low",
            "unknowns": [],
            "suggested_angles": ["mesure"],
        },
        {
            "name": "dimension gamma",
            "why": "troisième dimension du cas synthétique D",
            "presumed_criticality": "low",
            "unknowns": [],
            "suggested_angles": ["sceptique"],
        },
    ],
    "contestation": {"status": "none", "target": "", "argument": ""},
    "escalation_signals": [],
    "suggested_class": "",
}

FOUR_CRITICAL_FRAMING: dict[str, Any] = {
    **THREE_DIM_FRAMING,
    "problem_understood": "cas synthétique K : quatre dimensions présumées critiques",
    "dimensions": [
        {
            "name": f"dimension {name}",
            "why": "dimension présumée critique du cas synthétique K",
            "presumed_criticality": "high",
            "unknowns": [],
            "suggested_angles": [angle],
        }
        for name, angle in (
            ("kappa", "praticien"),
            ("lambda", "mesure"),
            ("mu", "sceptique"),
            ("nu", "utilisateur"),
        )
    ],
}

DEFAULT_USAGE = LLMUsage(input_tokens=1000, output_tokens=500)
POSITIONS = {
    "E1": "position synthétique un : construire",
    "E2": "position synthétique deux : acheter",
    "E3": "position synthétique trois : attendre",
}
DEFAULT_OPTIONS: dict[str, tuple[str, str]] = {
    "E1": ("option A", "build"),
    "E2": ("option B", "buy"),
    "E3": ("option C", "wait"),
}
GOOD_STEELMAN: dict[str, Any] = {
    "target": "P1",
    "steelman": (
        "Sous sa meilleure forme, la position visée soutient que construire est le seul moyen "
        "de garder la maîtrise du résultat, parce que les alternatives dépendent d'un tiers "
        "dont les priorités ne sont pas alignées ; elle accepte un coût initial plus élevé en "
        "échange d'une réversibilité maîtrisée."
    ),
    "strengths": ["maîtrise du résultat", "réversibilité maîtrisée"],
    "failure_scenarios": [
        "le coût initial dépasse la capacité",
        "le délai fait manquer l'objectif",
    ],
    "critique": "La position sous-estime le délai : le coût du retard n'est pas chiffré.",
}
STRAWMAN_SHORT: dict[str, Any] = {
    "target": "P1",
    "steelman": "P1 veut construire, c'est naïf.",
    "strengths": [],
    "failure_scenarios": [],
    "critique": "P1 veut construire, c'est naïf.",
}

LABEL_RE = re.compile(r"Ta position(?: initiale)? \((P\d+)\)")
STEELMAN_RE = re.compile(r"Tu es (P\d+)\. Position visée : (P\d+)\.")
FAMILY_RE = re.compile(r"\b(F\d+)\b")

ScriptValue = dict[str, Any] | Callable[[str, str], dict[str, Any]]


def expert_output(expert_id: str, options: dict[str, tuple[str, str]]) -> dict[str, Any]:
    label, kind = options.get(expert_id, (f"option {expert_id}", "build"))
    return {
        "position": POSITIONS.get(expert_id, f"position {expert_id}"),
        "reasoning": f"raisonnement de {expert_id}",
        "assumptions": [f"hypothèse propre à {expert_id}"],
        "risks": [f"risque vu par {expert_id}"],
        "unknowns": [f"inconnue vue par {expert_id}"],
        "to_verify": [],
        "options": [{"label": label, "summary": f"résumé {label}", "kind": kind}],
        "objections": [],
        "evidence": [
            {"claim": "fait tiré de l'entrée", "source": "entrée §1", "status": "verified"},
            {"claim": "ordre de grandeur habituel", "source": "", "status": "model_knowledge"},
        ],
    }


def act(
    target: str,
    kind: str = "critique",
    nature: str = "solution",
    text: str = "objection motivée synthétique",
    *,
    fact_question: str = "",
) -> dict[str, Any]:
    return {
        "act": kind,
        "target": target,
        "nature": nature,
        "text": text,
        "depends_on_fact": bool(fact_question),
        "fact_question": fact_question,
    }


NONE_ACT = {"acts": [], "convergence_note": "rien de substantiel à opposer"}


class DeliberationLLM:
    """Faux client structuré : scripts par type d'appel et par label de position."""

    def __init__(
        self,
        framing: dict[str, Any] | None = None,
        *,
        options: dict[str, tuple[str, str]] | None = None,
        relation: str = "different",
        confrontation: dict[str, dict[str, Any]] | None = None,
        steelman: dict[str, Any] | None = None,
        recognition: dict[str, Any] | None = None,
        revision: dict[str, dict[str, Any]] | None = None,
        consolidation: ScriptValue | None = None,
        comparison: ScriptValue | None = None,
        synthesis: ScriptValue | None = None,
        gate: dict[str, Any] | None = None,
        usage: LLMUsage | None = None,
    ) -> None:
        self.framing = framing or THREE_DIM_FRAMING
        self.options = options or DEFAULT_OPTIONS
        self.relation = relation
        self.confrontation = confrontation or {}
        self.steelman = steelman or GOOD_STEELMAN
        self.recognition = recognition or {"recognized": "yes", "missing_points": []}
        self.revision = revision or {}
        self.consolidation = consolidation
        self.comparison = comparison
        self.synthesis = synthesis
        self.gate = gate or {
            "passed": True,
            "checks": {
                "conclusion_follows_options": True,
                "evidence_labeled": True,
                "minorities_preserved": True,
                "steelman_done_if_required": True,
                "no_forced_consensus": True,
                "honest_about_gaps": True,
            },
            "issues": [],
        }
        self.usage = usage or DEFAULT_USAGE
        self.calls: list[dict[str, Any]] = []

    def complete(self, prompt: str) -> str:
        raise AssertionError("le chemin historique ne doit pas être utilisé par une mission")

    @staticmethod
    def _label(prompt: str) -> str:
        m = LABEL_RE.search(prompt)
        return m.group(1) if m else ""

    def _resolve(self, script: ScriptValue | None, prompt: str, default: dict[str, Any]) -> Any:
        if script is None:
            return default
        if callable(script):
            return script(self._label(prompt), prompt)
        return script

    def complete_structured(
        self, *, system: str, prompt: str, call_type: str, max_tokens: int
    ) -> LLMResponse:
        label = self._label(prompt)
        self.calls.append(
            {
                "system": system,
                "prompt": prompt,
                "call_type": call_type,
                "max_tokens": max_tokens,
                "label": label,
            }
        )
        payload: Any
        if call_type == "framing":
            payload = self.framing
        elif call_type == "expert_tour0":
            expert_id = next(
                line.split(":", 1)[1].strip()
                for line in prompt.splitlines()
                if line.startswith("Identifiant : ")
            )
            payload = expert_output(expert_id, self.options)
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
            payload = {"groups": [], "disagreements": []}
        elif call_type == "confrontation":
            payload = self.confrontation.get(label, NONE_ACT)
        elif call_type == "steelman":
            payload = self.steelman
        elif call_type == "steelman_recognition":
            payload = self.recognition
        elif call_type == "revision":
            payload = self.revision.get(
                label, {"decision": "maintain", "reason": "rien de nouveau", "triggered_by": []}
            )
        elif call_type == "consolidation":
            payload = self._resolve(self.consolidation, prompt, {"families": []})
        elif call_type == "comparison":
            payload = self._resolve(self.comparison, prompt, default_comparison(prompt))
        elif call_type == "synthesis":
            payload = self._resolve(self.synthesis, prompt, default_synthesis(prompt))
        elif call_type == "quality_gate":
            payload = self.gate
        else:  # pragma: no cover - garde-fou
            raise AssertionError(f"type d'appel inconnu : {call_type}")
        return LLMResponse(
            text=json.dumps(payload, ensure_ascii=False), usage=self.usage, stop_reason="end_turn"
        )


def families_in(prompt: str) -> list[str]:
    seen: list[str] = []
    for fid in FAMILY_RE.findall(prompt):
        if fid not in seen:
            seen.append(fid)
    return seen


def default_comparison(prompt: str) -> dict[str, Any]:
    criteria = ["résultat attendu", "coût", "délai", "risque", "réversibilité"]
    return {
        "criteria": criteria,
        "rows": [
            {
                "family_id": fid,
                "assessments": {
                    c: {"value": f"appréciation qualitative {fid}", "basis": "inference"}
                    for c in criteria
                },
            }
            for fid in families_in(prompt)
        ],
        "notes": "aucun score ; la preuve prime sur la majorité",
    }


def default_synthesis(prompt: str) -> dict[str, Any]:
    fams = families_in(prompt) or ["F1"]
    return {
        "problem_understood": "problème compris (synthèse synthétique)",
        "objective": "objectif (synthèse synthétique)",
        "constraints": ["contrainte C1"],
        "assumptions": [{"text": "hypothèse H1", "status": "unverified"}],
        "options": [{"family_id": f, "label": f"famille {f}", "kind": "other"} for f in fams],
        "evidence": [
            {
                "claim": "fait tiré de l'entrée",
                "source": "entrée §1",
                "reliability": "n/a",
                "provenance": "ceo_input",
            }
        ],
        "advantages": ["avantage synthétique"],
        "disadvantages": ["inconvénient synthétique"],
        "risks": ["risque synthétique"],
        "recommendation": {
            "kind": "test",
            "family_id": fams[0],
            "statement": "conduire un test borné avant tout engagement",
            "rationale": "la preuve disponible ne départage pas les familles",
        },
        "confidence": {"level": "medium", "justification": "positions stables, preuves partielles"},
        "residual_disagreements": [],
        "change_conditions": ["une preuve externe contraire"],
        "next_action": "lancer le test",
        "information_insufficient": False,
    }


class FakeResearchProvider:
    """Fournisseur de recherche factice : statut piloté ; ne fabrique jamais de source."""

    name = "fake_external"

    def __init__(self, status: str = "found", reliability: str = "unknown") -> None:
        self.status = status
        self.reliability = reliability
        self.questions: list[str] = []

    def search(self, question: str, *, max_tokens: int) -> ResearchResult:
        self.questions.append(question)
        if self.status == "found":
            return ResearchResult(
                question=question,
                status="found",
                provider=self.name,
                findings=[
                    ResearchFinding(
                        source="source-synthetique://fixture/1",
                        title="titre synthétique",
                        date="2026-01-01",
                        excerpt="extrait synthétique cité",
                        reliability=self.reliability,
                    )
                ],
                usage=LLMUsage(input_tokens=300, output_tokens=200),
                answer_summary="réponse synthétique sourcée",
            )
        return ResearchResult(
            question=question,
            status="error" if self.status == "error" else "not_found",
            provider=self.name,
            note="aucune source citée" if self.status != "error" else "TimeoutError: synthétique",
            usage=LLMUsage(input_tokens=300, output_tokens=50),
        )


# --- Fixtures pytest -----------------------------------------------------------------------------
_CURRENT: dict[str, DeliberationLLM] = {}
SCENARIOS: list[dict[str, Any]] = []


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    def factory() -> LLMClient:
        return _CURRENT["llm"]

    return factory


@pytest.fixture
def use_llm() -> Callable[[DeliberationLLM], DeliberationLLM]:
    def _set(llm: DeliberationLLM) -> DeliberationLLM:
        _CURRENT["llm"] = llm
        return llm

    _CURRENT["llm"] = DeliberationLLM()
    return _set


@pytest.fixture
def research(monkeypatch: pytest.MonkeyPatch) -> Callable[[Any], Any]:
    def _set(provider: Any) -> Any:
        monkeypatch.setattr("app.missions.build_research_provider", lambda settings: provider)
        return provider

    return _set


@pytest.fixture(scope="module", autouse=True)
def scenario_report() -> Iterator[None]:
    yield
    path = os.environ.get("OTV1_SCENARIO_REPORT")
    if path:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(SCENARIOS, fh, ensure_ascii=False, indent=2)


def run(client: TestClient, llm: DeliberationLLM, name: str, **overrides: Any) -> dict[str, Any]:
    payload = {"input_type": "problem", "input_text": "entrée synthétique D"}
    payload.update(overrides)
    response = client.post("/missions", json=payload)
    assert response.status_code == 201, response.text
    mission: dict[str, Any] = response.json()
    SCENARIOS.append(
        {
            "scenario": name,
            "effective_class": mission["effective_class"],
            "calls_by_type": dict(Counter(c["call_type"] for c in llm.calls)),
            "llm_calls_used": mission["llm_calls_used"],
            "max_llm_calls": mission["max_llm_calls"],
            "cost_eur": mission["cost_eur"],
            "max_cost_eur": mission["max_cost_eur"],
            "stop_reason": mission["stop_reason"],
            "deliberation_stop": (mission.get("deliberation") or {}).get("stop", {}).get("reason"),
            "recommendation": (mission.get("recommendation") or {}).get("status"),
        }
    )
    return mission


def journal(client: TestClient, mission_id: int) -> list[dict[str, Any]]:
    return list(client.get(f"/missions/{mission_id}/journal").json())


# --- 1. Trois alternatives réelles restent trois familles -----------------------------------------
def test_three_real_alternatives_stay_three_families(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(DeliberationLLM())
    mission = run(client, llm, "trois alternatives réelles")
    assert mission["status"] == "candidate"
    assert mission["stop_reason"] == ""
    cons = mission["deliberation"]["consolidation"]
    assert cons["atomic_count"] == 3
    assert cons["family_count"] == 3
    assert {f["kind"] for f in cons["families"]} == {"build", "buy", "wait"}
    rec = mission["recommendation"]
    assert rec["status"] == "produced"
    assert len(rec["options"]) == 3
    assert rec["families_count"] == 3
    fields = mission["report"]["fourteen_fields"]
    assert len(fields["05_options_examinees"]) == 3
    assert mission["cartography"]["non_action_option_present"] is True


# --- 2. Confrontation : actes adressés, `none` légitime, aucun désaccord fabriqué ----------------
def test_confrontation_acts_target_identifiable_positions_and_none_is_legitimate(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(
        DeliberationLLM(
            confrontation={
                "P1": {"acts": [act("P2", "critique", "solution", "critique motivée de P2")]},
                "P2": NONE_ACT,
                "P3": {"acts": [act("P1", "refute", "hypothesis", "réfutation motivée de P1")]},
            }
        )
    )
    mission = run(client, llm, "désaccord motivé adressé")
    objections = mission["deliberation"]["confrontation"]["objections"]
    assert [(o["from"], o["target"], o["act"]) for o in objections] == [
        ("P1", "P2", "critique"),
        ("P3", "P1", "refute"),
    ]
    assert all(o["target_expert"] for o in objections)  # cible identifiable, résolue
    assert all(o["status"] in {"open", "addressed"} for o in objections)
    # Chaque expert n'a vu, dans la carte, que les positions des autres (anonymisées).
    for call in [c for c in llm.calls if c["call_type"] == "confrontation"]:
        carte = call["prompt"].split("=== CARTE ===", 1)[1]
        assert f"- {call['label']} (" not in carte
        assert all(f"- {other} (" in carte for other in {"P1", "P2", "P3"} - {call["label"]})
    # `none` n'a rien enregistré ; la note de convergence est journalisée.
    entries = [e for e in journal(client, mission["id"]) if e["step"] == "confrontation"]
    p2 = next(e for e in entries if e["entry_type"] == "result" and e["actor"] == "E2")
    assert p2["payload"]["acts_registered"] == []
    assert "rien de substantiel" in p2["payload"]["convergence_note"]
    # Seuls les destinataires d'une objection sont révisés ; les autres ne sont pas appelés.
    revisions = {r["label"]: r for r in mission["deliberation"]["revisions"]}
    assert revisions["P1"]["called"] is True
    assert revisions["P2"]["called"] is True
    assert revisions["P3"]["called"] is False
    assert [c["label"] for c in llm.calls if c["call_type"] == "revision"] == ["P1", "P2"]


# --- 3 & 4. Steelman reconnu vs strawman refusé ---------------------------------------------------
def test_steelman_required_for_structurante_is_recognized_and_kept_separate(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(DeliberationLLM(recognition={"recognized": "yes", "missing_points": []}))
    mission = run(client, llm, "steelman reconnu (structurante)", declared_class="structurante")
    st = mission["deliberation"]["steelman"]
    assert st["required"] is True
    assert st["reason"] == "classe structurante/critique"
    assert st["status"] == "accepted"
    assert st["target"] == "P1"
    assert st["contradictor"] == "P3"
    assert st["strawman_flags"] == []
    # Trois objets séparés : steelman, forces/scénarios, critique.
    assert st["steelman"] != st["critique"]
    assert st["strengths"]
    assert st["failure_scenarios"]
    call_types = [c["call_type"] for c in llm.calls]
    assert call_types.index("steelman") < call_types.index("steelman_recognition")
    steelman_call = next(c for c in llm.calls if c["call_type"] == "steelman")
    roles = STEELMAN_RE.search(steelman_call["prompt"])
    assert roles is not None
    assert roles.groups() == ("P3", "P1")
    recog = next(c for c in llm.calls if c["call_type"] == "steelman_recognition")
    assert recog["label"] == "P1"
    # La critique issue du steelman est adressée au tenant, qui la traite en révision.
    crit = next(
        o
        for o in mission["deliberation"]["confrontation"]["objections"]
        if o["act"] == "steelman_critique"
    )
    assert crit["from"] == "P3"
    assert crit["target"] == "P1"
    assert crit["status"] == "open"
    rev_p1 = next(r for r in mission["deliberation"]["revisions"] if r["label"] == "P1")
    assert rev_p1["called"] is True
    assert "STEELMAN" in rev_p1["new_information_ids"]
    gate = mission["recommendation"]["gate"]
    assert gate["checks"]["steelman_done_if_required"] is True
    assert mission["recommendation"]["ceo_decision_mandatory_by_class"] is True


@pytest.mark.parametrize(
    ("steelman", "recognition", "expected_flags"),
    [
        (STRAWMAN_SHORT, {"recognized": "yes"}, True),  # détecté par les contrôles déterministes
        (
            GOOD_STEELMAN,
            {"recognized": "no", "missing_points": ["déformé"]},
            False,
        ),  # par le tenant
    ],
)
def test_strawman_is_detected_and_refused(
    client: TestClient,
    use_llm: Callable[..., DeliberationLLM],
    steelman: dict[str, Any],
    recognition: dict[str, Any],
    expected_flags: bool,
) -> None:
    llm = use_llm(DeliberationLLM(steelman=steelman, recognition=recognition))
    mission = run(client, llm, "strawman refusé", declared_class="structurante")
    st = mission["deliberation"]["steelman"]
    assert st["status"] == "rejected_strawman"
    assert bool(st["strawman_flags"]) is expected_flags
    crit = [
        o
        for o in mission["deliberation"]["confrontation"]["objections"]
        if o["act"] == "steelman_critique"
    ]
    assert crit
    assert crit[0]["status"] == "inadmissible_strawman"
    # Une critique issue d'un strawman n'est ni un désaccord résiduel ni une cause de révision.
    assert not any(
        d["id"] == crit[0]["id"] for d in mission["deliberation"]["residual_disagreements"]
    )
    assert [c["label"] for c in llm.calls if c["call_type"] == "revision"] == []
    gate = mission["recommendation"]["gate"]
    assert gate["passed"] is False
    assert gate["checks"]["steelman_done_if_required"] is False
    assert any("steelman requis" in issue for issue in gate["issues"])


def test_strawman_flags_are_deterministic_rules() -> None:
    good = SteelmanOutput(**GOOD_STEELMAN)
    assert strawman_flags(good) == []
    short = SteelmanOutput(**STRAWMAN_SHORT)
    flags = strawman_flags(short)
    assert "steelman trop court pour restituer une position" in flags
    assert "aucune force attribuée à la position visée" in flags
    assert "le steelman est identique à la critique" in flags
    assert "vocabulaire dépréciatif dans le steelman" in flags
    assert "homme de paille" in STEELMAN_SYSTEM


# --- 5, 14, 15. Recherche : déclenchée par un fait, honnête quand indisponible / sans source ------
FACT_CONFRONTATION = {
    "P1": {
        "acts": [
            act(
                "P2",
                "critique",
                "fact",
                "le fait F1 contredit P2",
                fact_question="Q1 synthétique : le fait F1 est-il établi ?",
            )
        ]
    },
    "P3": {
        "acts": [
            act(
                "P2",
                "critique",
                "fact",
                "même fait, autre formulation",
                fact_question="q1 synthétique : le fait F1 est-il établi ?",  # doublon (casse)
            )
        ]
    },
}


def test_factual_disagreement_triggers_research_and_unavailable_provider_stays_honest(
    client: TestClient,
    use_llm: Callable[..., DeliberationLLM],
    session_factory: sessionmaker[Session],
) -> None:
    llm = use_llm(DeliberationLLM(confrontation=FACT_CONFRONTATION))
    mission = run(client, llm, "fait contesté, recherche indisponible")
    research = mission["deliberation"]["research"]
    assert len(research) == 1  # question dédoublonnée
    item = research[0]
    assert item["status"] == "unavailable"
    assert item["provider"] == "none"
    assert item["source"] == ""
    assert item["provenance"] == "unavailable"
    assert item["reliability"] == "unknown"
    # Aucun appel, aucun coût pour une recherche indisponible.
    assert not [c for c in llm.calls if c["call_type"] == "research"]
    with session_factory() as session:
        rows = list(
            session.execute(select(LLMCallLog).where(LLMCallLog.mission_id == mission["id"]))
            .scalars()
            .all()
        )
    assert len(rows) == mission["llm_calls_used"]
    assert not any(r.call_type == "research" for r in rows)
    # L'inconnue reste déclarée : la recommandation est produite mais l'arrêt le dit.
    assert mission["deliberation"]["stop"]["reason"] == "missing_external_info"
    synthesis_prompt = next(c for c in llm.calls if c["call_type"] == "synthesis")["prompt"]
    assert "NON résolues" in synthesis_prompt
    assert "Q1 synthétique" in synthesis_prompt
    # Sans preuve nouvelle, P2 maintient (rien à changer sous simple objection factuelle ouverte).
    rev_p2 = next(r for r in mission["deliberation"]["revisions"] if r["label"] == "P2")
    assert rev_p2["decision"] == "maintain"
    assert rev_p2["revised_position"] == POSITIONS["E2"]
    note = mission["report"]["fourteen_fields"]["06_preuves"]["note"]
    assert note.startswith("0 preuve(s) externe(s)")
    assert "1 question(s) factuelle(s)" in note
    assert UnavailableResearchProvider().search("x", max_tokens=0).status == "unavailable"


@pytest.mark.parametrize("status", ["not_found", "error"])
def test_research_without_citation_never_invents_a_source(
    client: TestClient,
    use_llm: Callable[..., DeliberationLLM],
    research: Callable[[Any], Any],
    status: str,
) -> None:
    provider = research(FakeResearchProvider(status=status))
    llm = use_llm(DeliberationLLM(confrontation=FACT_CONFRONTATION))
    mission = run(client, llm, f"recherche {status}")
    item = mission["deliberation"]["research"][0]
    assert provider.questions == ["Q1 synthétique : le fait F1 est-il établi ?"]
    assert item["status"] == status
    assert item["source"] == ""
    assert item["findings"] == []
    assert item["provenance"] == "unavailable"
    assert item["reliability"] == "unknown"
    # L'appel réseau est compté et facturé, même sans résultat.
    assert mission["llm_calls_used"] == len(llm.calls) + 1
    assert mission["deliberation"]["stop"]["reason"] == "missing_external_info"
    rev_p2 = next(r for r in mission["deliberation"]["revisions"] if r["label"] == "P2")
    assert rev_p2["decision"] == "maintain"
    evidence = mission["deliberation"]["evidence"]
    assert all(e["provenance"] != "external" for e in evidence)


# --- 6 & 7. T09 : une preuve change une position ; l'insistance ne la change pas ------------------
def test_external_evidence_changes_position_with_trace(
    client: TestClient,
    use_llm: Callable[..., DeliberationLLM],
    research: Callable[[Any], Any],
    session_factory: sessionmaker[Session],
) -> None:
    research(FakeResearchProvider(status="found", reliability="unknown"))
    llm = use_llm(
        DeliberationLLM(
            confrontation=FACT_CONFRONTATION,
            revision={
                "P2": {
                    "decision": "modify",
                    "revised_position": "position deux révisée : acheter sous condition",
                    "reason": "la preuve EV-1 établit le fait F1",
                    "triggered_by": ["OBJ-1", "EV-1"],
                }
            },
        )
    )
    mission = run(client, llm, "preuve externe change une position")
    item = mission["deliberation"]["research"][0]
    assert item["status"] == "found"
    assert item["provenance"] == "external"
    assert item["source"] == "source-synthetique://fixture/1"
    assert item["date"] == "2026-01-01"
    assert item["excerpt"] == "extrait synthétique cité"
    assert item["reliability"] == "unknown"  # jamais inventée
    # La preuve a été soumise au destinataire et a déclenché une révision tracée.
    rev_call = next(c for c in llm.calls if c["call_type"] == "revision" and c["label"] == "P2")
    assert "EV-1" in rev_call["prompt"]
    assert "source-synthetique://fixture/1" in rev_call["prompt"]
    # Preuve ciblée : P1 et P3 (auteurs des objections) ne reçoivent pas EV-1 ; seul P2 est révisé.
    assert [c["label"] for c in llm.calls if c["call_type"] == "revision"] == ["P2"]
    assert item["positions"] == ["P2"]
    assert item["objection_ids"] == ["OBJ-1", "OBJ-2"]
    rev = next(r for r in mission["deliberation"]["revisions"] if r["label"] == "P2")
    assert rev["decision"] == "modify"
    assert rev["triggered_by"] == ["OBJ-1", "EV-1"]
    assert rev["previous_position"] == POSITIONS["E2"]
    assert rev["revised_position"] == "position deux révisée : acheter sous condition"
    assert rev["unexplained_change"] is False
    assert mission["deliberation"]["positions_after"]["P2"] == rev["revised_position"]
    # Le Tour 0 est immuable : la position initiale est conservée dans la cartographie.
    p2 = next(p for p in mission["cartography"]["positions"] if p["label"] == "P2")
    assert p2["position"] == POSITIONS["E2"]
    # L'objection traitée n'est plus résiduelle ; la recherche a été comptée et facturée.
    obj = next(
        o for o in mission["deliberation"]["confrontation"]["objections"] if o["id"] == "OBJ-1"
    )
    assert obj["status"] == "addressed"
    assert mission["deliberation"]["stop"]["reason"] in {"converged", "residual_only"}
    with session_factory() as session:
        rows = list(
            session.execute(select(LLMCallLog).where(LLMCallLog.mission_id == mission["id"]))
            .scalars()
            .all()
        )
    research_rows = [r for r in rows if r.call_type == "research"]
    assert len(research_rows) == 1
    assert (research_rows[0].cost_eur or 0.0) > 0
    assert mission["llm_calls_used"] == len(rows)
    # La preuve externe figure, étiquetée, dans la matière de synthèse et le rapport.
    assert any(e["provenance"] == "external" for e in mission["deliberation"]["evidence"])
    assert "1 preuve(s) externe(s)" in mission["report"]["fourteen_fields"]["06_preuves"]["note"]


def test_repetition_without_new_evidence_does_not_change_position(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(
        DeliberationLLM(
            confrontation={
                "P1": {"acts": [act("P2", "critique", "solution", "P2 a tort, j'insiste")]},
            },
            revision={
                "P2": {
                    "decision": "maintain",
                    "revised_position": "",
                    "reason": "aucune preuve ni argument nouveau : simple insistance",
                    "triggered_by": [],
                }
            },
        )
    )
    mission = run(client, llm, "insistance sans preuve")
    revisions = {r["label"]: r for r in mission["deliberation"]["revisions"]}
    assert revisions["P2"]["called"] is True
    assert revisions["P2"]["decision"] == "maintain"
    assert revisions["P2"]["revised_position"] == POSITIONS["E2"]
    assert revisions["P1"]["called"] is False
    assert revisions["P3"]["called"] is False
    assert mission["deliberation"]["positions_after"]["P2"] == POSITIONS["E2"]
    # Le désaccord reste ouvert et conservé jusqu'à la recommandation.
    residual = mission["deliberation"]["residual_disagreements"]
    assert len(residual) == 1
    assert residual[0]["between"] == ["P1", "P2"]
    assert mission["deliberation"]["stop"]["reason"] == "residual_only"
    assert any(
        d["description"] == "P2 a tort, j'insiste"
        for d in mission["recommendation"]["residual_disagreements"]
    )
    assert "jamais sous simple insistance" in REVISION_SYSTEM


# --- 8 & 9. Consolidation : synonymes fusionnés avec trace ; proches-mais-différentes séparées ----
def test_synonym_options_are_consolidated_into_one_family_with_trace(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(
        DeliberationLLM(
            options={
                "E1": ("option A", "build"),
                "E2": ("option A bis", "build"),
                "E3": ("option C", "wait"),
            },
            consolidation={
                "families": [
                    {
                        "family_id": "F1",
                        "label": "construire (A / A bis)",
                        "kind": "build",
                        "option_ids": ["E1-O1", "E2-O1"],
                        "variants": [{"option_id": "E2-O1", "difference": "périmètre réduit"}],
                        "internal_disagreements": ["calendrier"],
                    },
                    {
                        "family_id": "F2",
                        "label": "attendre",
                        "kind": "wait",
                        "option_ids": ["E3-O1"],
                    },
                ],
                "not_merged_because": [],
            },
        )
    )
    mission = run(client, llm, "synonymes consolidés")
    cons = mission["deliberation"]["consolidation"]
    assert cons["atomic_count"] == 3
    assert cons["family_count"] == 2
    f1 = next(f for f in cons["families"] if f["label"].startswith("construire"))
    assert f1["option_ids"] == ["E1-O1", "E2-O1"]
    assert f1["variants"] == [{"option_id": "E2-O1", "difference": "périmètre réduit"}]
    assert f1["internal_disagreements"] == ["calendrier"]  # désaccord intra-famille conservé
    assert f1["supporting_experts"] == ["E1", "E2"]
    trace = {t["option_id"]: t for t in cons["trace"]}
    assert trace["E1-O1"]["role"] == "member"
    assert trace["E2-O1"]["role"] == "variant"
    assert trace["E3-O1"]["family_id"] != trace["E1-O1"]["family_id"]
    assert len(mission["recommendation"]["options"]) == 2


def test_close_but_different_options_are_not_merged(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    # Le greffier tente de fusionner une option `build` et une option `buy` : natures différentes,
    # la fusion est refusée et scindée ; sa non-fusion motivée est conservée telle quelle.
    llm = use_llm(
        DeliberationLLM(
            consolidation={
                "families": [
                    {
                        "family_id": "F1",
                        "label": "obtenir la capacité",
                        "kind": "build",
                        "option_ids": ["E1-O1", "E2-O1"],
                    }
                ],
                "not_merged_because": [
                    {"option_ids": ["E2-O1", "E3-O1"], "reason": "acheter ≠ attendre"}
                ],
            }
        )
    )
    mission = run(client, llm, "proches mais différentes non fusionnées")
    cons = mission["deliberation"]["consolidation"]
    assert cons["family_count"] == 3
    kinds = sorted(f["kind"] for f in cons["families"])
    assert kinds == ["build", "buy", "wait"]
    assert any("scindée" in n for n in cons["notes"])
    assert cons["not_merged_because"] == [
        {"option_ids": ["E2-O1", "E3-O1"], "reason": "acheter ≠ attendre"}
    ]
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "Non fusionnées E2-O1, E3-O1 : acheter ≠ attendre" in md


# --- 10. Minorité conservée même si la synthèse l'oublie ------------------------------------------
def test_minority_disagreement_is_preserved_even_if_synthesis_drops_it(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    def forgetful_synthesis(label: str, prompt: str) -> dict[str, Any]:
        payload = default_synthesis(prompt)
        payload["residual_disagreements"] = []  # la synthèse « oublie » la minorité
        return payload

    llm = use_llm(
        DeliberationLLM(
            confrontation={
                "P3": {"acts": [act("P1", "critique", "solution", "objection minoritaire")]}
            },
            synthesis=forgetful_synthesis,
        )
    )
    mission = run(client, llm, "minorité conservée")
    rec = mission["recommendation"]
    assert [d["description"] for d in rec["residual_disagreements"]] == ["objection minoritaire"]
    assert rec["gate"]["checks"]["minorities_preserved"] is True
    assert rec["gate"]["checks"]["no_forced_consensus"] is True
    fields = mission["report"]["fourteen_fields"]
    assert fields["12_desaccords_residuels"][0]["description"] == "objection minoritaire"
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "objection minoritaire" in md


# --- 11 & 12. Convergence sans opposition artificielle ; contrôle de convergence prématurée -------
def test_convergence_without_artificial_opposition_on_courante(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(DeliberationLLM())
    mission = run(client, llm, "convergence courante", declared_class="courante")
    assert mission["max_llm_calls"] == 16
    assert mission["max_cost_eur"] == 1.5
    assert mission["deliberation"]["confrontation"]["objections"] == []
    assert mission["deliberation"]["steelman"]["required"] is False
    assert all(r["called"] is False for r in mission["deliberation"]["revisions"])
    assert not [c for c in llm.calls if c["call_type"] in {"revision", "steelman"}]
    assert mission["deliberation"]["stop"]["reason"] == "no_new_information"
    assert mission["recommendation"]["status"] == "produced"
    assert mission["recommendation"]["residual_disagreements"] == []
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "aucun acte substantiel" in md
    assert mission["llm_calls_used"] <= 16


def test_premature_convergence_on_important_class_triggers_steelman_control(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(DeliberationLLM(relation="identical"))
    mission = run(client, llm, "convergence prématurée (importante)")
    assert mission["cartography"]["divergence_index"] == 0.0
    st = mission["deliberation"]["steelman"]
    assert st["required"] is True
    assert st["reason"] == "convergence prématurée"
    assert st["status"] == "accepted"
    assert st["contradictor"] == "P3"  # hors du tenant, angle critique
    assert [c["call_type"] for c in llm.calls].count("steelman") == 1
    assert is_premature_convergence(
        effective_class="importante_provisoire", divergence_index=0.0, objection_count=0
    )
    assert not is_premature_convergence(
        effective_class="courante", divergence_index=0.0, objection_count=0
    )
    assert not is_premature_convergence(
        effective_class="critique", divergence_index=0.3, objection_count=0
    )


# --- 13. Recommandation test / attente quand l'information manque ---------------------------------
def test_recommendation_can_be_wait_when_information_is_insufficient(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    def waiting_synthesis(label: str, prompt: str) -> dict[str, Any]:
        payload = default_synthesis(prompt)
        payload["recommendation"] = {
            "kind": "wait",
            "family_id": "",
            "statement": "attendre la levée de l'inconnue U1",
            "rationale": "aucune preuve ne départage",
        }
        payload["information_insufficient"] = True
        payload["next_action"] = "mesurer U1 avant de décider"
        return payload

    llm = use_llm(DeliberationLLM(synthesis=waiting_synthesis))
    mission = run(client, llm, "recommandation attendre")
    rec = mission["recommendation"]
    assert rec["recommendation"]["kind"] == "wait"
    assert rec["information_insufficient"] is True
    assert rec["decision_ready"] is False
    fields = mission["report"]["fourteen_fields"]
    assert fields["10_recommandation"]["kind"] == "wait"
    assert fields["14_prochaine_action"][0] == "mesurer U1 avant de décider"
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "Information suffisante pour décider : False" in md


# --- 14. Structurante / critique : retour au CEO, désaccord de valeurs escaladé, aucune exécution -
def test_structurante_recommendation_returns_to_ceo_without_execution(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(
        DeliberationLLM(
            confrontation={"P2": {"acts": [act("P1", "critique", "value", "appétence au risque")]}}
        )
    )
    mission = run(client, llm, "structurante retour CEO", declared_class="critique")
    rec = mission["recommendation"]
    assert rec["requires_ceo_decision"] is True
    assert rec["ceo_decision_mandatory_by_class"] is True
    assert rec["ceo_arbitration_required"] is True  # désaccord de valeurs → CEO
    assert mission["deliberation"]["stop"]["reason"] == "ceo_decision_needed"
    assert mission["status"] == "candidate"
    fields = mission["report"]["fourteen_fields"]
    assert any("arbitrage CEO" in a for a in fields["14_prochaine_action"])
    # Aucune exécution : seuls des événements de rapport ; approuver n'appelle rien.
    events = client.get("/observability/events", params={"phase": "otv1_inc1"}).json()
    assert {e["event_type"] for e in events} == {"mission_report_ready"}
    calls_before = len(llm.calls)
    approved = client.post(f"/missions/{mission['id']}/approve").json()
    assert approved["status"] == "approved"
    assert len(llm.calls) == calls_before
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "arbitrage de valeurs requis" in md
    assert "ne décident pas" in md


# --- 15, 16. Budget dur : arrêt explicite, cycle minimal financé, délibération non entamée --------
def test_cost_cap_mid_deliberation_stops_explicitly_without_retry(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(DeliberationLLM())
    mission = run(client, llm, "arrêt coût en délibération", max_cost_eur=0.25)
    assert mission["max_cost_eur"] == 0.25
    assert mission["cost_eur"] <= 0.25
    assert mission["stop_reason"] == "cost_cap_would_be_exceeded"
    assert mission["report"]["partial"] is True
    assert mission["recommendation"] is None
    d = mission["deliberation"]
    assert d["stop"]["reason"] == "budget"
    assert "comparaison" in d["steps_done"]
    assert "synthese" not in d["steps_done"]
    assert {s["step"] for s in d["steps_skipped"]} >= {"porte_qualite"}
    refusals = mission["report"]["budget"]["refusals"]
    assert len(refusals) == 1
    assert refusals[0]["call_type"] == "synthesis"
    assert len([e for e in journal(client, mission["id"]) if e["entry_type"] == "budget_stop"]) == 1
    status = mission["report"]["fourteen_fields"]["10_recommandation"]["status"]
    assert "interrompue" in status
    assert "cost_cap_would_be_exceeded" in status


def test_minimal_cycle_is_financed_and_optional_steps_yield_to_synthesis(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(
        DeliberationLLM(
            confrontation={"P1": {"acts": [act("P2", "critique", "solution", "objection à P2")]}}
        )
    )
    mission = run(client, llm, "cycle minimal sous 14 appels", max_llm_calls=14)
    assert mission["composition"]["bounds"]["budget_plan"] == "coverage_first"
    assert len(mission["composition"]["experts"]) == 3  # largeur préservée
    assert mission["stop_reason"] == ""
    assert mission["llm_calls_used"] == 14
    assert mission["recommendation"]["status"] == "produced"
    assert mission["recommendation"]["gate"]["passed"] is True
    rev_p2 = next(r for r in mission["deliberation"]["revisions"] if r["label"] == "P2")
    assert rev_p2["called"] is False
    assert rev_p2["budget_reserved"] is True
    assert not [c for c in llm.calls if c["call_type"] == "revision"]
    reserved = [
        e
        for e in journal(client, mission["id"])
        if e["entry_type"] == "budget_reserved_for_synthesis"
    ]
    assert len(reserved) == 1
    assert reserved[0]["payload"]["skipped"] == "révision de P2"
    # Le désaccord non révisé reste résiduel : rien n'est lissé faute de budget.
    assert mission["deliberation"]["residual_disagreements"][0]["description"] == "objection à P2"


def test_deliberation_is_not_started_when_budget_cannot_afford_a_minimal_cycle(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(DeliberationLLM())
    mission = run(client, llm, "délibération non entamée (9 appels)", max_llm_calls=9)
    assert mission["llm_calls_used"] == 7  # cadrage + 3 exposés + 3 auto-qualifications
    assert mission["stop_reason"] == "deliberation_budget_insufficient"
    assert mission["report"]["partial"] is True
    assert mission["recommendation"] is None
    d = mission["deliberation"]
    assert d["steps_done"] == []
    assert {s["step"] for s in d["steps_skipped"]} == {
        "confrontation",
        "steelman",
        "recherche",
        "revision",
        "consolidation",
        "comparaison",
        "synthese",
        "porte_qualite",
    }
    assert d["budget_request"]["minimal_deliberation_calls"] == 7
    assert d["budget_request"]["additional_calls_estimate"] == 5
    assert not [
        c
        for c in llm.calls
        if c["call_type"] not in {"framing", "expert_tour0", "self_qualification"}
    ]
    # Le rapport de situation du Tour 0 reste exploitable et honnête.
    fields = mission["report"]["fourteen_fields"]
    assert len(fields["05_options_examinees"]) == 3
    assert "aucune recommandation" in fields["10_recommandation"]["status"]
    assert fields["10_recommandation"]["budget_request"]["additional_calls_estimate"] == 5


# --- 17. Dimension critique non couverte : arrêt explicite + demande de budget --------------------
def test_critical_dimension_uncovered_stops_with_budget_request(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(DeliberationLLM(FOUR_CRITICAL_FRAMING))
    mission = run(client, llm, "dimension critique non couverte", max_llm_calls=5)
    assert mission["stop_reason"] == "critical_dimension_uncovered"
    assert mission["llm_calls_used"] == 1  # le cadrage seulement : rien n'est dépensé pour rien
    assert [c["call_type"] for c in llm.calls] == ["framing"]
    uncovered = mission["composition"]["uncovered_dimensions"]
    assert len(uncovered) == 3
    br = mission["deliberation"]["budget_request"]
    assert br["uncovered_critical_dimensions"] == uncovered
    assert br["additional_calls_estimate"] == 3 * 3
    assert mission["recommendation"] is None
    assert mission["report"]["partial"] is True
    fields = mission["report"]["fourteen_fields"]
    assert any("dimension critique non couverte" in a for a in fields["14_prochaine_action"])
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "Demande de budget" in md
    assert "critical_dimension_uncovered" in md


# --- 18. Comparaison sans score ; preuves étiquetées ; journal complet ----------------------------
def test_comparison_has_no_scores_and_evidence_is_labeled_by_provenance(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    names = {n.lower() for n in comparison_schema_field_names()}
    assert not (names & FORBIDDEN_COMPARISON_FIELDS)
    assert "Aucun score numérique" in COMPARISON_SYSTEM
    assert "la preuve prime sur la majorité" in COMPARISON_SYSTEM
    llm = use_llm(DeliberationLLM())
    mission = run(client, llm, "comparaison et provenance")
    comp = mission["deliberation"]["comparison"]
    assert comp["criteria"][:2] == ["résultat attendu", "coût"]
    assert {r["family_id"] for r in comp["rows"]} == {"F1", "F2", "F3"}
    for row in comp["rows"]:
        for assessment in row["assessments"].values():
            assert assessment["basis"] in {
                "evidence",
                "inference",
                "hypothesis",
                "unknown",
                "ceo_input",
                "model_knowledge",
            }
            assert not re.fullmatch(r"\d+(\.\d+)?", assessment["value"])
    evidence = mission["deliberation"]["evidence"]
    assert {e["provenance"] for e in evidence} == {"ceo_input", "model_knowledge"}
    assert all(e["source"] for e in evidence if e["provenance"] == "ceo_input")
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "| Famille | résultat attendu | coût |" in md


def test_journal_traces_every_deliberation_call_with_prompt_fingerprint(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(
        DeliberationLLM(
            confrontation={"P1": {"acts": [act("P2", "critique", "solution", "objection à P2")]}}
        )
    )
    mission = run(client, llm, "journal complet")
    entries = journal(client, mission["id"])
    planned = [e for e in entries if e["entry_type"] == "call_planned"]
    assert len(planned) == len(llm.calls) == mission["llm_calls_used"]
    assert all(e["payload"]["prompt_sha256"] and e["payload"]["prompt_text"] for e in planned)
    steps = [e["step"] for e in entries]
    order = ["cadrage", "composition", "tour0", "auto_qualification", "confrontation", "revision"]
    order += ["consolidation", "comparaison", "synthese", "porte_qualite", "rapport"]
    positions = [steps.index(s) for s in order]
    assert positions == sorted(positions)
    done = [e for e in entries if e["entry_type"] == "call_done"]
    assert all(
        e["payload"]["cost_eur"] > 0 and e["payload"]["stop_reason"] == "end_turn" for e in done
    )
    assert mission["deliberation"]["steps_done"] == [
        "confrontation",
        "revision",
        "consolidation",
        "comparaison",
        "synthese",
        "porte_qualite",
    ]
    # Rapport : 14 champs présents et recommandation explicitement réservée au CEO.
    fields = mission["report"]["fourteen_fields"]
    assert len(fields) == 14
    assert fields["10_recommandation"]["requires_ceo_decision"] is True
    assert mission["report"]["recommendation_produced"] is True


# --- Corrections d'audit v1.1 (C1 à C4) -------------------------------------------------------
# C1 — Révision : une preuve n'atteint que les positions qu'elle concerne.
def test_targeted_evidence_reaches_only_the_concerned_position(
    client: TestClient,
    use_llm: Callable[..., DeliberationLLM],
    research: Callable[[Any], Any],
) -> None:
    research(FakeResearchProvider(status="found"))
    llm = use_llm(
        DeliberationLLM(
            confrontation={
                "P1": {
                    "acts": [
                        act(
                            "P2",
                            "critique",
                            "fact",
                            "le fait F1 contredit P2",
                            fact_question="Q1 synthétique : le fait F1 est-il établi ?",
                        )
                    ]
                }
            }
        )
    )
    mission = run(client, llm, "preuve ciblée (P2 seul)")
    item = mission["deliberation"]["research"][0]
    assert item["status"] == "found"
    assert item["positions"] == ["P2"]
    assert item["raised_by"] == "P1"
    assert item["objection_ids"] == ["OBJ-1"]
    # Seule P2 est éligible à révision ; P1 et P3 ne sont pas appelés pour cette seule preuve.
    revision_calls = [c for c in llm.calls if c["call_type"] == "revision"]
    assert [c["label"] for c in revision_calls] == ["P2"]
    assert "EV-1" in revision_calls[0]["prompt"]
    revisions = {r["label"]: r for r in mission["deliberation"]["revisions"]}
    assert revisions["P2"]["called"] is True
    assert "EV-1" in revisions["P2"]["new_information_ids"]
    assert revisions["P1"]["called"] is False
    assert revisions["P1"]["new_information_ids"] == []
    assert revisions["P3"]["called"] is False
    assert revisions["P3"]["new_information_ids"] == []
    # La preuve reste visible de la synthèse (étiquetée externe), sans diffusion en révision.
    assert any(e["provenance"] == "external" for e in mission["deliberation"]["evidence"])


def test_tour0_fact_objection_evidence_targets_its_author(
    client: TestClient,
    use_llm: Callable[..., DeliberationLLM],
    research: Callable[[Any], Any],
) -> None:
    from app.mission_deliberation import material_fact_questions
    from app.mission_schemas import ConfrontationOutput

    # Objection factuelle du Tour 0 : la position concernée est celle de son auteur.
    cartography = {
        "disagreements": [
            {
                "source": "E3",
                "between": ["P3"],
                "nature": "fact",
                "description": "le fait F2 diverge",
                "target": "Q2 synthétique ?",
            }
        ]
    }
    labels = {"E1": "P1", "E2": "P2", "E3": "P3"}
    confrontations: dict[str, ConfrontationOutput | None] = {
        "E1": ConfrontationOutput.model_validate(
            {"acts": [act("P2", "critique", "fact", "F1", fact_question="Q1 synthétique ?")]}
        ),
        "E3": ConfrontationOutput.model_validate(
            {"acts": [act("P1", "critique", "fact", "F1 bis", fact_question="q1 SYNTHÉTIQUE ?")]}
        ),
    }
    questions = material_fact_questions(confrontations, cartography, labels, cap=3)
    assert [q["question"] for q in questions] == ["Q1 synthétique ?", "Q2 synthétique ?"]
    assert questions[0]["positions"] == ["P2", "P1"]  # cibles réunies, dédoublonnées
    assert questions[0]["raised_by_all"] == ["P1", "P3"]
    assert questions[1]["positions"] == ["P3"]
    assert questions[1]["raised_by"] == "P3"


# C2 — Intégrité des cibles de confrontation.
def test_confrontation_target_integrity(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(
        DeliberationLLM(
            confrontation={
                "P1": {
                    "acts": [
                        act("P2", "critique", "solution", "cible valide"),
                        act(
                            "P99",
                            "critique",
                            "fact",
                            "cible inexistante",
                            fact_question="Q-fantôme : ne doit jamais être recherchée",
                        ),
                        act("P1", "refute", "solution", "cible = soi-même"),
                        act("", "third_way", "solution", "voie tierce sans cible"),
                        act("P42", "third_way", "solution", "voie tierce à cible invalide"),
                    ]
                }
            }
        )
    )
    mission = run(client, llm, "intégrité des cibles")
    objections = mission["deliberation"]["confrontation"]["objections"]
    assert [(o["act"], o["target"], o["text"]) for o in objections] == [
        ("critique", "P2", "cible valide"),
        ("third_way", "", "voie tierce sans cible"),
        ("third_way", "", "voie tierce à cible invalide"),
    ]
    assert all(o["target_expert"] for o in objections if o["act"] != "third_way")
    # Les actes invalides sont journalisés comme rejetés, sans objection ouverte.
    entries = journal(client, mission["id"])
    rejected = [e for e in entries if e["entry_type"] == "act_rejected"]
    assert [(e["payload"]["act"], e["payload"]["target"]) for e in rejected] == [
        ("critique", "P99"),
        ("refute", "P1"),
    ]
    result = next(
        e for e in entries if e["step"] == "confrontation" and e["entry_type"] == "result"
    )
    assert result["payload"]["acts_rejected"] == 2
    assert result["payload"]["acts_registered"] == ["OBJ-1", "OBJ-2", "OBJ-3"]
    # Ni recherche (la question fantôme est écartée), ni résiduel, ni synthèse pour P99.
    assert mission["deliberation"]["research"] == []
    assert any(s["step"] == "recherche" for s in mission["deliberation"]["steps_skipped"])
    residual = mission["deliberation"]["residual_disagreements"]
    assert all("P99" not in d["between"] for d in residual)
    assert all(d["description"] != "cible inexistante" for d in residual)
    outputs = mission["deliberation"]["confrontation"]["outputs"]
    assert [a["target"] for a in outputs["E1"]["acts"]] == ["P2", "", ""]
    synthesis_prompt = next(c for c in llm.calls if c["call_type"] == "synthesis")["prompt"]
    assert "P99" not in synthesis_prompt
    assert "cible inexistante" not in synthesis_prompt
    # Seule la cible valide est révisée.
    assert [c["label"] for c in llm.calls if c["call_type"] == "revision"] == ["P2"]


# C3 — Observabilité canonique de la recherche.
@pytest.mark.parametrize("status", ["found", "not_found"])
def test_research_call_has_the_canonical_audit_chain(
    client: TestClient,
    use_llm: Callable[..., DeliberationLLM],
    research: Callable[[Any], Any],
    session_factory: sessionmaker[Session],
    status: str,
) -> None:
    from app.mission_exploration import prompt_fingerprint

    provider = research(FakeResearchProvider(status=status))
    llm = use_llm(DeliberationLLM(confrontation=FACT_CONFRONTATION))
    mission = run(client, llm, f"chaîne d'audit recherche ({status})")
    entries = [e for e in journal(client, mission["id"]) if e["step"] == "recherche"]
    kinds = [e["entry_type"] for e in entries]
    assert kinds == ["call_planned", "call_done", "result"]
    planned, done, result = entries
    question = "Q1 synthétique : le fait F1 est-il établi ?"
    assert provider.questions == [question]
    assert planned["actor"] == "Recherche"
    assert planned["payload"]["call_type"] == "research"
    assert planned["payload"]["provider"] == "fake_external"
    assert planned["payload"]["prompt_text"] == question
    assert planned["payload"]["prompt_sha256"] == prompt_fingerprint("recherche ciblée", question)
    assert planned["payload"]["max_tokens"] == 4000
    assert planned["payload"]["estimated_cost_eur_upper_bound"] > 0
    assert done["payload"]["provider"] == "fake_external"
    assert done["payload"]["input_tokens"] == 300
    assert done["payload"]["stop_reason"] == status
    assert done["payload"]["findings_count"] == (1 if status == "found" else 0)
    assert done["payload"]["cost_eur"] > 0
    assert result["payload"]["status"] == status
    assert result["payload"]["source"] == (
        "source-synthetique://fixture/1" if status == "found" else ""
    )
    # Cohérence avec `llm_call_logs` et le registre de budget.
    with session_factory() as session:
        rows = list(
            session.execute(select(LLMCallLog).where(LLMCallLog.mission_id == mission["id"]))
            .scalars()
            .all()
        )
    research_rows = [r for r in rows if r.call_type == "research"]
    assert len(research_rows) == 1
    row = research_rows[0]
    assert row.provider == "fake_external"
    assert row.input_tokens == done["payload"]["input_tokens"]
    assert row.output_tokens == done["payload"]["output_tokens"]
    assert row.cost_eur == pytest.approx(done["payload"]["cost_eur"])
    assert row.status == "success"
    assert len(rows) == mission["llm_calls_used"] == len(llm.calls) + 1
    assert (
        done["payload"]["budget"]["llm_calls_used"]
        == len(
            [
                c
                for c in llm.calls
                if c["call_type"]
                in {"framing", "expert_tour0", "self_qualification", "confrontation"}
            ]
        )
        + 1
    )
    assert mission["cost_eur"] == pytest.approx(sum(r.cost_eur or 0.0 for r in rows), abs=1e-6)


def test_unavailable_research_provider_has_no_call_chain_and_no_cost(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(DeliberationLLM(confrontation=FACT_CONFRONTATION))
    mission = run(client, llm, "recherche indisponible : zéro appel")
    entries = [e for e in journal(client, mission["id"]) if e["step"] == "recherche"]
    assert [e["entry_type"] for e in entries] == ["result"]
    assert entries[0]["payload"]["status"] == "unavailable"
    assert mission["llm_calls_used"] == len(llm.calls)


# C4 — La porte qualité conditionne réellement `decision_ready`.
def test_decision_ready_requires_sufficient_information_and_a_passed_gate(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    # (a) synthèse correcte + porte passée + information suffisante → prête.
    llm = use_llm(DeliberationLLM())
    ok = run(client, llm, "decision_ready : porte passée")
    rec = ok["recommendation"]
    assert rec["gate"]["passed"] is True
    assert rec["information_insufficient"] is False
    assert rec["decision_ready"] is True
    assert rec["quality_blocked"] is False
    assert rec["quality_gate_status"] == "passed"

    # (b) information insuffisante + porte passée → non prête.
    def waiting(label: str, prompt: str) -> dict[str, Any]:
        payload = default_synthesis(prompt)
        payload["information_insufficient"] = True
        payload["recommendation"]["kind"] = "wait"
        return payload

    llm = use_llm(DeliberationLLM(synthesis=waiting))
    insufficient = run(client, llm, "decision_ready : information insuffisante")
    rec = insufficient["recommendation"]
    assert rec["gate"]["passed"] is True
    assert rec["decision_ready"] is False
    assert rec["quality_blocked"] is False
    # (c) information suffisante + porte échouée → non prête, proposition conservée pour audit.
    llm = use_llm(
        DeliberationLLM(
            gate={"passed": False, "checks": {"evidence_labeled": False}, "issues": ["source ?"]}
        )
    )
    failed = run(client, llm, "decision_ready : porte échouée")
    rec = failed["recommendation"]
    assert rec["status"] == "produced"
    assert rec["recommendation"]["kind"] == "test"
    assert rec["gate"]["passed"] is False
    assert rec["information_insufficient"] is False
    assert rec["decision_ready"] is False
    assert rec["quality_blocked"] is True
    assert rec["quality_gate_status"] == "failed"
    fields = failed["report"]["fourteen_fields"]["10_recommandation"]
    assert fields["decision_ready"] is False
    assert fields["quality_blocked"] is True
    md = client.get(f"/missions/{failed['id']}/report/markdown").json()["markdown"]
    assert "Prête pour décision (decision_ready) : False — bloquée par la porte qualité" in md
    gate_entry = next(
        e
        for e in journal(client, failed["id"])
        if e["step"] == "porte_qualite" and e["entry_type"] == "result"
    )
    assert gate_entry["payload"]["decision_ready"] is False
    assert gate_entry["payload"]["quality_blocked"] is True


def test_rejected_strawman_blocks_decision_ready_but_keeps_the_recommendation(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(DeliberationLLM(steelman=STRAWMAN_SHORT))
    mission = run(client, llm, "strawman → decision_ready false", declared_class="structurante")
    rec = mission["recommendation"]
    assert mission["deliberation"]["steelman"]["status"] == "rejected_strawman"
    assert rec["status"] == "produced"  # conservée pour audit
    assert rec["gate"]["passed"] is False
    assert rec["gate"]["checks"]["steelman_done_if_required"] is False
    assert rec["decision_ready"] is False
    assert rec["quality_blocked"] is True
