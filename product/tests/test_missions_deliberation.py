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
DEFAULT_OPTIONS: dict[str, OptionSpec] = {
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


OptionSpec = tuple[str, str] | list[tuple[str, str]]


def expert_output(expert_id: str, options: dict[str, OptionSpec]) -> dict[str, Any]:
    spec = options.get(expert_id, (f"option {expert_id}", "build"))
    specs: list[tuple[str, str]] = spec if isinstance(spec, list) else [spec]
    return {
        "position": POSITIONS.get(expert_id, f"position {expert_id}"),
        "reasoning": f"raisonnement de {expert_id}",
        "assumptions": [f"hypothèse propre à {expert_id}"],
        "risks": [f"risque vu par {expert_id}"],
        "unknowns": [f"inconnue vue par {expert_id}"],
        "to_verify": [],
        "options": [
            {"label": label, "summary": f"résumé {label}", "kind": kind} for label, kind in specs
        ],
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
        options: dict[str, OptionSpec] | None = None,
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
        if isinstance(payload, dict) and "__raw__" in payload:
            # Réponse brute scriptée (troncature simulée à `max_tokens`, JSON coupé).
            return LLMResponse(
                text=payload["__raw__"],
                usage=LLMUsage(input_tokens=1000, output_tokens=max_tokens),
                stop_reason=payload.get("__stop__", "max_tokens"),
            )
        return LLMResponse(
            text=json.dumps(payload, ensure_ascii=False), usage=self.usage, stop_reason="end_turn"
        )


def families_in(prompt: str) -> list[str]:
    seen: list[str] = []
    for fid in FAMILY_RE.findall(prompt):
        if fid not in seen:
            seen.append(fid)
    return seen


def families_to_compare(prompt: str) -> list[str]:
    """Familles listées dans le bloc « à comparer » du prompt compact (pas celles des preuves)."""
    block = prompt.split("Familles stratégiques à comparer", 1)[-1].split("Preuves disponibles", 1)[
        0
    ]
    return families_in(block)


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
            for fid in families_to_compare(prompt)
        ],
        "notes": "aucun score ; la preuve prime sur la majorité",
    }


OPTION_LINE_RE = re.compile(
    r"^- (?P<id>[A-Za-z0-9_-]+) : (?P<label>.+?)(?: \[(?P<kinds>[a-z_/]+)\])?"
    r"(?: \((?:x(?P<count>\d+) formulations|(?P<opts>\d+) option).*)?$"
)
# Jugement sémantique simulé du greffier scripté : radicaux qu'il considère comme une même
# stratégie quelles que soient les natures déclarées (côté test uniquement).
CROSS_KIND_EQUIVALENT_STEMS = {"maintenance ciblee"}
# Radicaux pour lesquels le greffier scripté signale un désaccord interne (côté test uniquement).
INTERNAL_DISAGREEMENT_STEMS = {"externaliser la maintenance"}


def stem(label: str) -> str:
    """Radical d'un libellé : sans parenthèse, casse, accents ni ponctuation (greffier "
    "compétent)."""
    from app.mission_consolidation import normalize_label

    return normalize_label(re.sub(r"\(.*?\)", "", label))


def competent_clerk(label: str, prompt: str) -> dict[str, Any]:
    """Greffier scripté : regroupe par radical ; la nature est un signal (« other » rejoint la
    nature concrète du même radical ; deux natures concrètes différentes restent séparées, sauf
    radicaux jugés équivalents) ; variantes = parenthèses ; désaccord interne si > 2 membres."""
    items: list[tuple[str, str, list[str], int]] = []
    for line in prompt.splitlines():
        m = OPTION_LINE_RE.match(line.strip())
        if m:
            kinds = (m.group("kinds") or "").split("/") if m.group("kinds") else []
            count = int(m.group("count") or m.group("opts") or 1)
            items.append((m.group("id"), m.group("label"), kinds, count))
    groups: dict[tuple[str, str], list[tuple[str, str, int]]] = {}
    for oid, lab, kinds, count in items:
        s = stem(lab)
        concrete = [k for k in kinds if k and k != "other"]
        key_kind = "*" if (not concrete or s in CROSS_KIND_EQUIVALENT_STEMS) else concrete[0]
        groups.setdefault((s, key_kind), []).append((oid, lab, count))
    # « other » (clé *) rejoint la première nature concrète du même radical, s'il y en a une.
    merged: dict[tuple[str, str], list[tuple[str, str, int]]] = {}
    for (s, kk), members in groups.items():
        if kk == "*":
            host = next((k for k in groups if k[0] == s and k[1] != "*"), None)
            if host is not None:
                merged.setdefault(host, []).extend(members)
                continue
        merged.setdefault((s, kk), []).extend(members)
    families = []
    for i, ((s, kk), members) in enumerate(merged.items(), start=1):
        variants = [
            {"option_id": oid, "difference": re.search(r"\((.*?)\)", lab).group(1)}  # type: ignore[union-attr]
            for oid, lab, _count in members
            if "(" in lab
        ]
        internal = ["calendrier"] if sum(c for _o, _l, c in members) > 2 else []
        if s in INTERNAL_DISAGREEMENT_STEMS:
            internal = ["périmètre contesté"]
        families.append(
            {
                "family_id": f"F{i}",
                "label": s,
                "kind": kk if kk != "*" else "other",
                "option_ids": [oid for oid, _l, _c in members],
                "variants": variants,
                "internal_disagreements": internal,
            }
        )
    return {"families": families, "not_merged_because": []}


def compare_all(label: str, prompt: str) -> dict[str, Any]:
    return default_comparison(prompt)


def truncate_first(n_calls: int, fallback: Callable[[str, str], dict[str, Any]]) -> Any:
    """Script qui tronque les `n_calls` premiers appels puis délègue au script normal."""
    state = {"calls": 0}

    def script(label: str, prompt: str) -> dict[str, Any]:
        state["calls"] += 1
        if state["calls"] <= n_calls:
            return {"__raw__": '{"families": [{"family_id": "F1", "la', "__stop__": "max_tokens"}
        return fallback(label, prompt)

    return script


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

    def __init__(
        self,
        status: str = "found",
        reliability: str = "unknown",
        *,
        answer_found: bool | str | None = "auto",
        requires_internal_data: bool = False,
        documents: bool | None = None,
    ) -> None:
        self.status = status
        self.reliability = reliability
        # Par défaut : `found` ⇒ documents + verdict de réponse matérielle déclaré ; `None`
        # explicite = fournisseur sans verdict.
        self.answer_found: bool | None = (
            (status == "found") if answer_found == "auto" else answer_found  # type: ignore[assignment]
        )
        self.requires_internal_data = requires_internal_data
        self.documents = (status == "found") if documents is None else documents
        self.questions: list[str] = []

    def search(self, question: str, *, max_tokens: int) -> ResearchResult:
        self.questions.append(question)
        if self.documents:
            return ResearchResult(
                question=question,
                status="found" if self.status == "found" else "not_found",
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
                answer_summary=(
                    "réponse synthétique sourcée"
                    if self.answer_found
                    else "aucune source ne répond précisément à la question"
                ),
                answer_found=self.answer_found,
                requires_internal_data=self.requires_internal_data,
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
    # Même libellé, natures différentes (`build` vs `buy`) : jamais dans le même lot, jamais dans
    # la même famille. Dans une même nature, une non-fusion motivée du greffier est conservée.
    def clerk(label: str, prompt: str) -> dict[str, Any]:
        payload = competent_clerk(label, prompt)
        if "E1-O1" in prompt and "E2-O1" in prompt:
            payload["families"] = [
                {"family_id": "F1", "label": "construire A", "option_ids": ["E1-O1"]},
                {"family_id": "F2", "label": "construire A bis", "option_ids": ["E2-O1"]},
            ]
            payload["not_merged_because"] = [
                {
                    "option_ids": ["E1-O1", "E2-O1"],
                    "reason": "périmètres substantiellement différents",
                }
            ]
        return payload

    llm = use_llm(
        DeliberationLLM(
            options={
                "E1": ("option A", "build"),
                "E2": ("option A bis", "build"),
                "E3": ("option A", "buy"),
            },
            consolidation=clerk,
        )
    )
    mission = run(client, llm, "proches mais différentes non fusionnées")
    cons = mission["deliberation"]["consolidation"]
    assert cons["status"] == "ok"
    assert cons["family_count"] == 3
    assert sorted(f["kind"] for f in cons["families"]) == ["build", "build", "buy"]
    # Même libellé « option A », natures concrètes différentes : jamais fusionnées d'office ;
    # le lot (inter-natures) montre les deux au greffier, qui les laisse séparées.
    batch_prompts = [c["prompt"] for c in llm.calls if c["call_type"] == "consolidation"]
    assert len(batch_prompts) == 1
    assert "E3-O1 : option A [buy]" in batch_prompts[0]
    assert "E1-O1 : option A [build]" in batch_prompts[0]
    buy = next(f for f in cons["families"] if f["kind"] == "buy")
    assert buy["option_ids"] == ["E3-O1"]
    assert buy["source_kinds"] == ["buy"]
    assert cons["not_merged_because"] == [
        {"option_ids": ["E1-O1", "E2-O1"], "reason": "périmètres substantiellement différents"}
    ]
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "Non fusionnées E1-O1, E2-O1 : périmètres substantiellement différents" in md


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
    mission = run(client, llm, "arrêt coût en délibération", max_cost_eur=0.22)
    assert mission["max_cost_eur"] == 0.22
    assert mission["cost_eur"] <= 0.22
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
    # Trois options (un lot de consolidation) : cœur nominal = 4 appels (consolidation,
    # comparaison, synthèse, porte) ; pire cas = 7 (relance scindée + relance de comparaison).
    mission = run(client, llm, "cycle minimal sous 14 appels", max_llm_calls=14)
    assert mission["composition"]["bounds"]["budget_plan"] == "coverage_first"
    assert len(mission["composition"]["experts"]) == 3  # largeur préservée
    assert mission["stop_reason"] == ""
    assert mission["llm_calls_used"] == 14
    assert mission["deliberation"]["consolidation"]["calls"] == 1
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
    assert d["budget_request"]["minimal_deliberation_calls"] == 7  # 3 confrontations + cœur 4
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


# --- Corrections d'audit v1.2 (B1 à B5) -------------------------------------------------------
# B1 — Intégrité sémantique de la recherche : des documents ne sont pas une réponse.
FACT_P1_TO_P2 = {
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


@pytest.mark.parametrize(
    ("provider", "expected_status", "expected_provenance", "reason_fragment"),
    [
        (FakeResearchProvider(status="found"), "found", "external", "réponse matérielle"),
        (
            FakeResearchProvider(status="not_found", documents=True, answer_found=False),
            "not_found",
            "non_material",
            "aucune source ne répond matériellement",
        ),
        (
            FakeResearchProvider(status="not_found", documents=True, answer_found=None),
            "not_found",
            "non_material",
            "aucun verdict",
        ),
        (
            FakeResearchProvider(
                status="found", documents=True, answer_found=True, requires_internal_data=True
            ),
            "requires_internal_data",
            "non_material",
            "données internes",
        ),
        (FakeResearchProvider(status="not_found", documents=False), "not_found", "unavailable", ""),
        (FakeResearchProvider(status="error"), "error", "unavailable", ""),
    ],
    ids=[
        "found",
        "docs_sans_reponse",
        "docs_sans_verdict",
        "donnee_interne",
        "sans_source",
        "erreur",
    ],
)
def test_research_status_is_semantic_not_document_based(
    client: TestClient,
    use_llm: Callable[..., DeliberationLLM],
    research: Callable[[Any], Any],
    provider: FakeResearchProvider,
    expected_status: str,
    expected_provenance: str,
    reason_fragment: str,
) -> None:
    research(provider)
    llm = use_llm(DeliberationLLM(confrontation=FACT_P1_TO_P2))
    mission = run(client, llm, f"intégrité sémantique recherche ({expected_status})")
    item = mission["deliberation"]["research"][0]
    assert item["status"] == expected_status
    assert item["provenance"] == expected_provenance
    assert reason_fragment in item["reason"]
    assert item["documents_returned"] == (1 if provider.documents else 0)
    # Les documents non probants restent tracés comme résultats, jamais comme preuve `found`.
    if provider.documents and expected_status != "found":
        assert item["findings"]
        assert item["source"] == ""
        assert item["answer_summary"] == ""
    # Seule une réponse matérielle déclenche une révision sous preuve : P2 reçoit toujours OBJ-1
    # (objection adressée), mais EV-1 n'est une information nouvelle que si `found`.
    rev_p2 = next(r for r in mission["deliberation"]["revisions"] if r["label"] == "P2")
    rev_call = next(c for c in llm.calls if c["call_type"] == "revision" and c["label"] == "P2")
    if expected_status == "found":
        assert "EV-1" in rev_p2["new_information_ids"]
        assert "EV-1" in rev_call["prompt"]
    else:
        assert rev_p2["new_information_ids"] == ["OBJ-1"]
        assert "EV-1" not in rev_call["prompt"]
    assert all(e["provenance"] != "external" for e in mission["deliberation"]["evidence"]) or (
        expected_status == "found"
    )


def test_research_verdict_parsing_and_classification_rules() -> None:
    from app.mission_research import classify_research_outcome, parse_verdict

    assert parse_verdict("texte libre sans verdict") is None
    verdict = parse_verdict(
        'Les sources disent… \n{"answer_found": true, "requires_internal_data": false, '
        '"answer": "oui, établi en 2024"}'
    )
    assert verdict == {
        "answer_found": True,
        "requires_internal_data": False,
        "answer": "oui, établi en 2024",
    }
    doc = ResearchFinding(source="source-synthetique://fixture/2")
    # documents + réponse exacte → found
    ok = ResearchResult("q", "not_found", "p", findings=[doc], answer_found=True)
    assert classify_research_outcome(ok)[0] == "found"
    # documents + « aucune donnée répondant à la question » → not_found motivé
    no_answer = ResearchResult("q", "found", "p", findings=[doc], answer_found=False)
    status, reason = classify_research_outcome(no_answer)
    assert status == "not_found"
    assert "aucune source ne répond" in reason
    # documents + verdict absent → not_found (jamais `found` par défaut)
    assert (
        classify_research_outcome(ResearchResult("q", "found", "p", findings=[doc]))[0]
        == "not_found"
    )
    # donnée intrinsèquement interne → requires_internal_data
    internal = ResearchResult(
        "q", "found", "p", findings=[doc], answer_found=True, requires_internal_data=True
    )
    assert classify_research_outcome(internal)[0] == "requires_internal_data"
    # aucune source → not_found ; erreur → error ; indisponible → unavailable
    assert (
        classify_research_outcome(ResearchResult("q", "not_found", "p", answer_found=True))[0]
        == "not_found"
    )
    assert classify_research_outcome(ResearchResult("q", "error", "p", note="boom"))[0] == "error"
    assert classify_research_outcome(ResearchResult("q", "unavailable", "none"))[0] == "unavailable"


# B2 / B3 / B5 — Consolidation et comparaison robustes sur un grand Tour 0.
def large_options() -> dict[str, OptionSpec]:
    """66 options synthétiques : doublons exacts, variantes, natures distinctes, même libellé de
    nature différente, non-action ; ≥ 1 désaccord intra-famille (via le greffier scripté)."""
    kinds = {1: "build", 2: "build", 3: "build", 4: "build", 5: "build", 6: "buy", 7: "test"}
    specs: dict[str, OptionSpec] = {}
    for e in (1, 2, 3):
        rows: list[tuple[str, str]] = []
        for k in range(1, 8):
            rows.append((f"Stratégie S{k}", kinds[k]))
            rows.append((f"stratégie s{k} !", kinds[k]))  # doublon exact après normalisation
            rows.append((f"Stratégie S{k} (variante {e})", kinds[k]))  # variante
        specs[f"E{e}"] = rows
    specs["E1"] = [*specs["E1"], ("ne rien faire", "do_nothing")]
    specs["E2"] = [*specs["E2"], ("attendre un trimestre", "wait")]
    specs["E3"] = [*specs["E3"], ("Stratégie S1", "buy")]  # proche mais nature différente
    return specs


def test_large_tour0_is_consolidated_in_bounded_batches_without_truncation(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(DeliberationLLM(options=large_options(), consolidation=competent_clerk))
    mission = run(client, llm, "66 options : consolidation par lots")
    cons = mission["deliberation"]["consolidation"]
    assert cons["status"] == "ok"
    assert cons["atomic_count"] == 66
    # Précompression déterministe : « Stratégie Sk » ≡ « stratégie sk ! » (3 experts) ; le même
    # libellé de nature concrète différente (S1 build / S1 buy) n'est PAS fusionné d'office.
    assert cons["groups_after_premerge"] == 7 * 4 + 3
    assert cons["cross_kind_groups"] == 0
    assert any("formulations identiques" in n for n in cons["notes"])
    # Lots bornés inter-natures : 31 groupes → 2 lots (16 + 15) + 1 méta-passe.
    assert cons["batches"] == 2
    assert cons["calls"] == 3
    assert cons["retries"] == 0
    assert cons["parse_error"] == ""
    prompts = [c["prompt"] for c in llm.calls if c["call_type"] == "consolidation"]
    assert len(prompts) == 3
    assert all(len([ln for ln in p.splitlines() if ln.startswith("- ")]) <= 32 for p in prompts)
    assert all(len([ln for ln in p.splitlines() if ln.startswith("- ")]) <= 16 for p in prompts[:2])
    assert not any("résumé Stratégie" in p for p in prompts)  # représentation compacte
    # Aucune troncature : chaque appel est observé complet.
    done = [e for e in journal(client, mission["id"]) if e["entry_type"] == "call_done"]
    assert all(e["payload"]["truncated"] is False for e in done)
    # Familles : 5 build + 2 buy + 1 test + wait + do_nothing ; aucun repli singleton massif.
    families = cons["families"]
    assert cons["family_count"] == len(families) == 10
    assert Counter(f["kind"] for f in families) == {
        "build": 5,
        "buy": 2,
        "test": 1,
        "wait": 1,
        "do_nothing": 1,
    }
    s1_build = next(f for f in families if f["kind"] == "build" and f["label"] == "strategie s1")
    assert len(s1_build["option_ids"]) == 9  # 6 formulations identiques + 3 variantes
    assert len(s1_build["variants"]) == 3
    assert s1_build["internal_disagreements"] == ["calendrier"]
    assert s1_build["supporting_experts"] == ["E1", "E2", "E3"]
    assert s1_build["source_kinds"] == ["build"]
    assert s1_build["canonical_kind"] == "build"
    s1_buy = next(f for f in families if f["kind"] == "buy" and f["label"] == "strategie s1")
    assert s1_buy["option_ids"] == ["E3-O22"]  # même libellé, nature différente : non fusionnée
    # Traçabilité atomique → famille complète et unique.
    trace_ids = [t["option_id"] for t in cons["trace"]]
    assert sorted(trace_ids) == sorted(o["option_id"] for o in mission["cartography"]["options"])
    assert len(trace_ids) == len(set(trace_ids)) == 66
    assert cons["unconsolidated_option_ids"] == []
    # Comparaison sur les familles retenues (≤ 12 : toutes), chaque famille évaluée.
    comp = mission["deliberation"]["comparison"]
    assert comp["status"] == "ok"
    assert comp["coverage_preserved"] is True
    assert comp["retained_family_ids"] == [f["family_id"] for f in families]
    assert comp["not_compared"] == []
    for row in comp["rows"]:
        assert set(row["assessments"]) == set(comp["criteria"])
        assert all(
            not re.fullmatch(r"\d+(\.\d+)?", a["value"]) for a in row["assessments"].values()
        )
    # Budget : cœur nominal recalculé (3 + 3 appels de consolidation), tout tient sous 30.
    assert mission["llm_calls_used"] == 1 + 3 + 3 + 3 + 3 + 1 + 1 + 1 == 16
    assert mission["recommendation"]["decision_ready"] is True


def test_consolidation_truncation_retries_once_then_fails_closed(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    truncated = '{"families": [{"family_id": "F1", "label": "coup'  # coupé en plein champ
    llm = use_llm(
        DeliberationLLM(
            options=large_options(),
            consolidation=lambda label, prompt: {"__raw__": truncated, "__stop__": "max_tokens"},
        )
    )
    mission = run(client, llm, "consolidation tronquée : échec fermé")
    cons = mission["deliberation"]["consolidation"]
    assert cons["status"] == "failed"
    assert cons["parse_error"].startswith("truncated_output")
    # Une relance par lot au plus (lot scindé en deux) : 2 lots → 2 + 4 appels, jamais plus.
    assert cons["retries"] == 2
    assert cons["calls"] == 6
    entries = journal(client, mission["id"])
    retry_entries = [
        e for e in entries if e["step"] == "consolidation" and e["entry_type"] == "retry"
    ]
    assert len(retry_entries) == 2
    assert all(e["payload"]["attempt"] == 1 for e in retry_entries)
    assert [e for e in entries if e["entry_type"] == "call_done" and e["payload"]["truncated"]]
    # Aucun repli singleton : aucune famille n'est fabriquée à partir d'un lot irrécupérable.
    assert cons["family_count"] == 0
    assert len(cons["unconsolidated_option_ids"]) == 66
    # Sans matière consolidée, aucune recommandation n'est simulée ; rien n'est « prêt ».
    assert mission["recommendation"] is None
    assert mission["report"]["recommendation_produced"] is False
    assert mission["report"]["budget"]["refusals"] == []
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "Consolidation : statut **failed**" in md


def test_consolidation_retry_recovers_when_halves_fit(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    def flaky_clerk(label: str, prompt: str) -> dict[str, Any]:
        n = len([ln for ln in prompt.splitlines() if ln.startswith("- ")])
        if n >= 16:  # un lot de 16 déborde ; ses deux moitiés (8) tiennent
            return {"__raw__": '{"families": [{"family_id": "F1", "la', "__stop__": "max_tokens"}
        return competent_clerk(label, prompt)

    llm = use_llm(DeliberationLLM(options=large_options(), consolidation=flaky_clerk))
    mission = run(client, llm, "consolidation : relance compacte réussie")
    cons = mission["deliberation"]["consolidation"]
    assert cons["status"] == "ok"
    assert cons["retries"] == 1  # seul le lot de 16 groupes a débordé
    assert cons["calls"] == 2 + 2 + 1  # 2 lots, 2 moitiés, 1 méta-passe
    assert cons["unconsolidated_option_ids"] == []
    assert cons["family_count"] == 10
    assert mission["recommendation"]["gate"]["passed"] is True
    assert mission["recommendation"]["decision_ready"] is True


def test_comparison_failure_is_explicit_and_blocks_the_gate(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(
        DeliberationLLM(
            options=large_options(),
            consolidation=competent_clerk,
            comparison=lambda label, prompt: {
                "__raw__": '{"criteria": ["co',
                "__stop__": "max_tokens",
            },
        )
    )
    mission = run(client, llm, "comparaison tronquée : échec explicite")
    comp = mission["deliberation"]["comparison"]
    assert comp["status"] == "failed"
    assert comp["parse_error"].startswith("truncated_output")
    # Une relance compacte au plus, STRATIFIÉE : les 5 familles nécessaires à la couverture (une
    # par nature ; désaccord interne et multi-dimensions déjà représentés) sont conservées ; les
    # facultatives sont écartées. Aucune famille n'est « hard » (rien n'est cité dans la demande).
    assert [a["families"] for a in comp["attempts"]] == [10, 5]
    assert comp["hard_mandatory_family_ids"] == []
    assert len(comp["mandatory_family_ids"]) == 5
    assert comp["coverage_preserved"] is True
    assert len([c for c in llm.calls if c["call_type"] == "comparison"]) == 2
    assert comp["criteria"] == []
    assert comp["rows"] == []
    assert len(comp["not_compared"]) == 5
    rec = mission["recommendation"]
    assert rec["status"] == "produced"
    assert rec["gate"]["passed"] is False
    assert "upstream_stage_failed:comparaison" in rec["gate"]["integrity_failures"]
    assert rec["quality_blocked"] is True
    assert rec["decision_ready"] is False
    synthesis_prompt = next(c for c in llm.calls if c["call_type"] == "synthesis")["prompt"]
    assert "Comparaison INVALIDE" in synthesis_prompt
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "Comparaison : statut **failed**" in md


def test_partial_comparison_is_not_presented_as_valid(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    def half_comparison(label: str, prompt: str) -> dict[str, Any]:
        payload = default_comparison(prompt)
        payload["rows"] = payload["rows"][:1]  # une seule famille évaluée sur trois
        return payload

    llm = use_llm(DeliberationLLM(comparison=half_comparison))
    mission = run(client, llm, "comparaison partielle")
    comp = mission["deliberation"]["comparison"]
    assert comp["status"] == "partial"
    assert comp["missing_family_ids"] == ["F2", "F3"]
    assert [r for r in comp["rows"] if r.get("note")]  # familles non évaluées marquées
    rec = mission["recommendation"]
    assert rec["gate"]["checks"]["pipeline_integrity"] is False
    assert rec["decision_ready"] is False


# B4 — Porte qualité fail-closed sur l'intégrité du pipeline.
def test_gate_llm_verdict_cannot_override_upstream_failures(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    # Synthèse invalide : aucune recommandation produite, porte non exécutée, rien de « prêt ».
    llm = use_llm(
        DeliberationLLM(
            synthesis=lambda label, prompt: {
                "__raw__": '{"problem_understood": "x',
                "__stop__": "max_tokens",
            }
        )
    )
    mission = run(client, llm, "synthèse tronquée")
    rec = mission["recommendation"]
    assert rec["status"] == "failed"
    assert rec["error"].startswith("truncated_output")
    assert mission["report"]["recommendation_produced"] is False
    assert any(
        s["step"] == "porte_qualite" and "aucune recommandation" in s["reason"]
        for s in mission["deliberation"]["steps_skipped"]
    )
    # Confrontation invalide (sortie inexploitable pour une perspective) : veto explicite.
    llm = use_llm(
        DeliberationLLM(confrontation={"P2": {"__raw__": '{"acts": [', "__stop__": "max_tokens"}})
    )
    mission = run(client, llm, "confrontation invalide")
    rec = mission["recommendation"]
    assert rec["status"] == "produced"
    assert rec["gate"]["llm_verdict"] is True
    assert rec["gate"]["passed"] is False
    assert any(i.startswith("upstream_stage_failed:confrontation") for i in rec["gate"]["issues"])
    assert rec["quality_blocked"] is True
    assert rec["decision_ready"] is False


def test_healthy_pipeline_keeps_integrity_and_c1_to_c4_invariants(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(DeliberationLLM())
    mission = run(client, llm, "pipeline sain : intégrité établie")
    rec = mission["recommendation"]
    assert rec["gate"]["checks"]["pipeline_integrity"] is True
    assert rec["gate"]["integrity_failures"] == []
    assert rec["gate"]["passed"] is True
    assert rec["decision_ready"] is True
    assert rec["quality_blocked"] is False
    assert mission["deliberation"]["consolidation"]["status"] == "ok"
    assert mission["deliberation"]["comparison"]["status"] == "ok"
    assert not [c for c in llm.calls if c["call_type"] == "revision"]  # C1 : rien de nouveau


# --- Corrections d'audit v1.3 (B6 à B8, garde-fou épistémique) -----------------------------------
# B6 — La nature est un signal de structuration, pas une frontière non révisable.
def cross_kind_options() -> dict[str, OptionSpec]:
    """42 options : mêmes stratégies sous `other` / `do_nothing` / `build` / `simplify` / `test`,
    paraphrases, variantes, stratégies proches mais différentes, contradictoires à vocabulaire
    voisin (agir / ne rien faire, immédiat / différé, refonte / correctif, acheter / construire)."""
    return {
        "E1": [
            ("ne rien changer", "other"),
            ("Refonte complète du module", "build"),
            ("correctif minimal", "simplify"),
            ("maintenance ciblée", "simplify"),
            ("appliquer la mesure immédiatement", "build"),
            ("acheter la solution X", "buy"),
            ("Stratégie Z1", "build"),
            ("Stratégie Z2", "build"),
            ("Stratégie Z3 (variante 1)", "build"),
            ("agir maintenant", "build"),
            ("prototype", "test"),
            ("Stratégie Z4", "other"),
            ("Stratégie Z5", "integrate"),
            ("Stratégie Z6 (variante 1)", "other"),
        ],
        "E2": [
            ("ne rien changer", "do_nothing"),
            ("Refonte complète du module !", "other"),
            ("Correctif minimal", "other"),
            ("maintenance ciblée", "test"),
            ("différer la mesure", "wait"),
            ("construire la solution X", "build"),
            ("Stratégie Z1", "build"),
            ("stratégie z2 (variante 2)", "other"),
            ("Stratégie Z3", "build"),
            ("ne rien faire", "do_nothing"),
            ("prototype", "other"),
            ("Stratégie Z4", "build"),
            ("Stratégie Z5 (variante 2)", "integrate"),
            ("Stratégie Z6", "other"),
        ],
        "E3": [
            ("ne rien changer", "do_nothing"),
            ("refonte complète du module (paraphrase)", "build"),
            ("correctif minimal (paraphrase)", "simplify"),
            ("maintenance ciblée", "other"),
            ("appliquer la mesure immédiatement (variante 3)", "build"),
            ("acheter la solution X", "buy"),
            ("Stratégie Z1 (variante 3)", "other"),
            ("Stratégie Z2", "build"),
            ("Stratégie Z3", "other"),
            ("agir maintenant", "build"),
            ("prototype (variante 3)", "test"),
            ("Stratégie Z4 (variante 3)", "build"),
            ("Stratégie Z5", "integrate"),
            ("Stratégie Z6", "other"),
        ],
    }


def test_cross_kind_duplicates_are_consolidated_with_canonical_kind_and_trace(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(DeliberationLLM(options=cross_kind_options(), consolidation=competent_clerk))
    mission = run(client, llm, "42 options : consolidation inter-natures")
    cons = mission["deliberation"]["consolidation"]
    assert cons["status"] == "ok"
    assert cons["atomic_count"] == 42
    assert cons["cross_kind_groups"] >= 3  # doublons exacts `other` ↔ nature concrète
    families = {f["label"]: f for f in cons["families"]}
    # 1) doublons inter-natures regroupés, avec nature canonique et natures d'origine tracées.
    ne_rien_changer = families["ne rien changer"]
    assert ne_rien_changer["canonical_kind"] == "do_nothing"
    assert sorted(ne_rien_changer["source_kinds"]) == ["do_nothing", "other"]
    assert ne_rien_changer["supporting_experts"] == ["E1", "E2", "E3"]
    refonte = families["refonte complete du module"]
    assert refonte["canonical_kind"] == "build"
    assert sorted(refonte["source_kinds"]) == ["build", "other"]
    assert len(refonte["option_ids"]) == 3
    assert refonte["variants"] == [{"option_id": "E3-O2", "difference": "paraphrase"}]
    assert refonte["internal_disagreements"] == ["calendrier"]
    correctif = families["correctif minimal"]
    assert correctif["canonical_kind"] == "simplify"
    assert sorted(correctif["source_kinds"]) == ["other", "simplify"]
    maintenance = families["maintenance ciblee"]  # simplify / test / other jugés équivalents
    assert sorted(maintenance["source_kinds"]) == ["other", "simplify", "test"]
    assert maintenance["canonical_kind"] == "simplify"
    assert len(maintenance["option_ids"]) == 3
    assert families["strategie z4"]["canonical_kind"] == "build"  # other + build + build
    assert families["strategie z6"]["canonical_kind"] == "other"  # uniquement other
    # 2) stratégies réellement différentes séparées (vocabulaire voisin compris).
    assert "differer la mesure" in families
    assert "appliquer la mesure immediatement" in families
    assert families["differer la mesure"]["kind"] == "wait"
    assert families["appliquer la mesure immediatement"]["kind"] == "build"
    assert families["acheter la solution x"]["kind"] == "buy"
    assert families["construire la solution x"]["kind"] == "build"
    assert families["agir maintenant"]["kind"] == "build"
    assert families["ne rien faire"]["kind"] == "do_nothing"
    assert "refonte complete du module" in families
    assert "correctif minimal" in families
    # 3) aucune option perdue, trace complète ; 4) pas d'explosion du nombre de familles.
    trace_ids = [t["option_id"] for t in cons["trace"]]
    assert len(trace_ids) == len(set(trace_ids)) == 42
    assert cons["unconsolidated_option_ids"] == []
    assert cons["family_count"] == 17
    assert cons["batches"] == 2
    assert cons["calls"] == 3
    # La nature reste visible en aval : familles distinctes par nature canonique dans le rapport.
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "ne rien changer [do_nothing]" in md


def test_action_and_non_action_are_never_merged_even_if_the_clerk_tries() -> None:
    from app.mission_consolidation import (
        families_from_batch,
        kinds_compatible,
        premerge_options,
    )
    from app.mission_schemas import ConsolidationOutput

    assert kinds_compatible("build", "other")
    assert kinds_compatible("build", "buy")
    assert kinds_compatible("wait", "do_nothing")
    assert not kinds_compatible("build", "do_nothing")
    assert not kinds_compatible("wait", "test")
    options = [
        {
            "option_id": "E1-O1",
            "expert_id": "E1",
            "dimension": "d",
            "label": "agir",
            "kind": "build",
        },
        {
            "option_id": "E2-O1",
            "expert_id": "E2",
            "dimension": "d",
            "label": "ne rien faire",
            "kind": "do_nothing",
        },
        {
            "option_id": "E3-O1",
            "expert_id": "E3",
            "dimension": "d",
            "label": "agir",
            "kind": "other",
        },
    ]
    groups = premerge_options(options)
    assert [g["member_ids"] for g in groups] == [["E1-O1", "E3-O1"], ["E2-O1"]]
    assert groups[0]["source_kinds"] == ["build", "other"]
    assert groups[0]["kind"] == "build"
    notes: list[str] = []
    output = ConsolidationOutput.model_validate(
        {
            "families": [
                {
                    "family_id": "F1",
                    "label": "tout",
                    "kind": "other",
                    "option_ids": ["E1-O1", "E2-O1"],
                }
            ]
        }
    )
    families, _ = families_from_batch(output, groups, notes)
    assert [(f["kind"], f["option_ids"]) for f in families] == [
        ("build", ["E1-O1", "E3-O1"]),
        ("do_nothing", ["E2-O1"]),
    ]
    assert any("action et non-action" in n for n in notes)


# B7 — Le retry de comparaison préserve la couverture stratégique.
COVERAGE_INPUT = (
    "Nous hésitons entre la migration progressive, la refonte complète et le correctif minimal ; "
    "le reste du dossier est en annexe."
)


def coverage_options() -> dict[str, OptionSpec]:
    """15 familles attendues : 7 natures, 3 stratégies citées dans la demande, 1 minorité avec
    désaccord interne (buy, E3 seul), do_nothing, wait, et des familles `build` redondantes
    fortement soutenues."""
    return {
        "E1": [
            ("Stratégie A1", "build"),
            ("Stratégie A2", "build"),
            ("Migration progressive", "integrate"),
            ("Correctif minimal", "simplify"),
            ("ne rien faire", "do_nothing"),
            ("Prototype rapide", "test"),
            ("Stratégie A6", "build"),
            ("Stratégie A7", "build"),
        ],
        "E2": [
            ("Stratégie A1", "build"),
            ("Stratégie A2", "build"),
            ("Stratégie A3", "build"),
            ("Refonte complète", "build"),
            ("attendre le prochain cycle", "wait"),
            ("Migration progressive", "integrate"),
            ("Stratégie A8", "build"),
        ],
        "E3": [
            ("Stratégie A1", "build"),
            ("Stratégie A3", "build"),
            ("Stratégie A4", "build"),
            ("Externaliser la maintenance", "buy"),
            ("Correctif minimal", "simplify"),
            ("Stratégie A5", "build"),
        ],
    }


def test_comparison_retry_preserves_strategic_coverage(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(
        DeliberationLLM(
            options=coverage_options(),
            consolidation=competent_clerk,
            comparison=truncate_first(1, compare_all),
        )
    )
    mission = run(
        client, llm, "relance de comparaison : couverture préservée", input_text=COVERAGE_INPUT
    )
    cons = mission["deliberation"]["consolidation"]
    assert cons["family_count"] == 15
    by_label = {f["label"]: f["family_id"] for f in cons["families"]}
    comp = mission["deliberation"]["comparison"]
    # 3 familles hard (citées) + 4 retenues pour la couverture (natures do_nothing / wait / test /
    # buy ; build, integrate, simplify, multi-dimensions et désaccord interne déjà représentés par
    # les hard) : la relance passe de 12 à 7 en n'écartant que des facultatives.
    assert [a["families"] for a in comp["attempts"]] == [12, 7]
    assert len(comp["hard_mandatory_family_ids"]) == 3
    assert comp["hard_mandatory_conflict"] is False
    assert comp["status"] == "ok"
    assert comp["coverage_preserved"] is True
    central = [
        by_label["migration progressive"],
        by_label["refonte complete"],
        by_label["correctif minimal"],
    ]
    minority = by_label["externaliser la maintenance"]
    mandatory = set(comp["mandatory_family_ids"])
    coverage = comp["coverage"]
    # Les 3 stratégies citées dans la demande, la minorité matérielle, la non-action / attente et
    # une famille par nature sont obligatoires et conservées par la relance.
    assert set(central) <= mandatory
    assert all("citée dans la demande" in " ".join(coverage[f]) for f in central)
    assert minority in mandatory
    assert any("minorité matérielle" in r or "nature buy" in r for r in coverage[minority])
    assert comp["selection"][minority]["role"] == "coverage"
    assert {by_label["ne rien faire"], by_label["attendre le prochain cycle"]} <= mandatory
    retained = set(comp["retained_family_ids"])
    assert mandatory <= retained
    kinds_retained = {f["kind"] for f in cons["families"] if f["family_id"] in retained}
    assert kinds_retained == {"build", "integrate", "simplify", "do_nothing", "wait", "test", "buy"}
    # La relance n'a pas privilégié la seule majorité : la refonte complète (1 soutien, citée)
    # est conservée tandis que des `build` redondantes de même soutien sont écartées ; les
    # `build` multi-dimensions (A2, A3) restent parce que la couverture l'exige, pas par majorité.
    assert by_label["refonte complete"] in retained
    dropped = {by_label[f"strategie a{i}"] for i in (4, 5, 6, 7, 8)} - retained
    assert len(dropped) >= 2
    assert all(set(r["assessments"]) == set(comp["criteria"]) for r in comp["rows"])
    retry = next(
        e
        for e in journal(client, mission["id"])
        if e["entry_type"] == "retry" and e["step"] == "comparaison"
    )
    assert retry["payload"]["mandatory_kept"] == 7
    rec = mission["recommendation"]
    assert rec["gate"]["passed"] is True
    assert rec["decision_ready"] is True


def test_comparison_retry_that_cannot_preserve_coverage_is_not_ok(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    # Budget : après la première comparaison il reste exactement synthèse + porte ; la relance
    # (qui aurait préservé la couverture) n'est pas financée → statut != ok, porte exécutée et
    # bloquante. Appels : 1 + 3 + 3 + 3 + 1 (consolidation) + 1 (comparaison) + 1 + 1 = 14.
    llm = use_llm(
        DeliberationLLM(
            options=coverage_options(),
            consolidation=competent_clerk,
            comparison=truncate_first(1, compare_all),
        )
    )
    mission = run(
        client,
        llm,
        "relance de comparaison non finançable",
        input_text=COVERAGE_INPUT,
        max_llm_calls=14,
    )
    comp = mission["deliberation"]["comparison"]
    assert comp["status"] == "failed"
    assert [a["families"] for a in comp["attempts"]] == [12]
    assert "non financée" in comp["coverage_note"]
    entries = journal(client, mission["id"])
    assert any(
        e["entry_type"] == "retry_refused_budget" and e["step"] == "comparaison" for e in entries
    )
    rec = mission["recommendation"]
    assert rec["status"] == "produced"
    assert rec["gate"]["passed"] is False
    assert rec["decision_ready"] is False
    assert "upstream_stage_failed:comparaison" in rec["gate"]["integrity_failures"]
    assert mission["llm_calls_used"] == 14 == mission["max_llm_calls"]
    assert mission["stop_reason"] == ""  # la porte n'a pas été sacrifiée : aucun arrêt dur


def test_coverage_requirements_are_data_driven() -> None:
    from app.mission_consolidation import coverage_requirements, select_families_for_attempt

    def fam(
        i: int, kind: str, sup: list[str], dims: list[str], internal: list[str]
    ) -> dict[str, Any]:
        return {
            "family_id": f"F{i}",
            "label": ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta"][i - 1],
            "kind": kind,
            "supporting_experts": sup,
            "option_ids": [f"o{i}"],
            "internal_disagreements": internal,
            "dimensions": dims,
        }

    families = [
        fam(1, "build", ["E1", "E2", "E3"], ["d1"], []),
        fam(2, "build", ["E1", "E2"], ["d1"], []),
        fam(3, "buy", ["E3"], ["d2"], ["périmètre"]),
        fam(4, "wait", ["E2"], ["d1"], []),
        fam(5, "build", ["E1"], ["d1", "d2"], []),
        fam(6, "build", ["E1"], ["d3"], []),
        fam(7, "build", ["E2"], ["d1"], []),
    ]
    coverage = coverage_requirements(
        families, request_texts=["Faut-il retenir zeta ou alpha ?"], critical_dimensions={"d3"}
    )
    # Hard : les stratégies citées mot pour mot (« eta » n'est pas « zeta ») et le désaccord unique.
    assert coverage["hard"] == {
        "F1": ["citée dans la demande ou le cadrage"],
        "F3": ["désaccord interne unique : disparaîtrait autrement"],
        "F6": ["citée dans la demande ou le cadrage"],
    }
    reqs = {r["id"]: r["candidates"] for r in coverage["requirements"]}
    assert reqs["kind:build"][0] == "F5"  # multi-dimensions préférée, puis soutien
    assert reqs["critical_dimension:d3"] == ["F6"]
    assert reqs["non_action"] == ["F4"]
    assert reqs["minority:buy"] == ["F3"]
    assert reqs["multi_dimension"] == ["F5"]
    picked = select_families_for_attempt(families, coverage, cap=5)
    assert picked["hard_conflict"] is False
    retained = [f["family_id"] for f in picked["retained"]]
    assert retained == ["F1", "F3", "F4", "F5", "F6"]
    assert picked["selection"]["F4"]["role"] == "coverage"
    assert picked["selection"]["F5"]["reasons"] == ["stratégie multi-dimensionnelle représentée"]
    assert [d["family_id"] for d in picked["deferred"]] == ["F2", "F7"]
    assert picked["unsatisfied"] == []
    everything = select_families_for_attempt(families, coverage, cap=12)
    assert [f["family_id"] for f in everything["retained"]] == [f["family_id"] for f in families]
    assert everything["selection"]["F2"]["role"] == "optional"
    # Saturation : plus de hard que de places → conflit déclaré, aucune sélection normale.
    saturated = select_families_for_attempt(families, coverage, cap=2)
    assert saturated["hard_conflict"] is True
    assert saturated["hard_count"] == 3
    assert saturated["retained"] == []


# B8 — La porte qualité est prioritaire sur tout retry ; réserve du pire cas borné.
def reserve_options() -> dict[str, OptionSpec]:
    return {
        "E1": [("Stratégie A", "build"), ("Stratégie B", "build")],
        "E2": [("Stratégie C", "build"), ("attendre", "wait")],
        "E3": [("Stratégie D", "build")],
    }


def _reserve_llm(*, flaky_consolidation: bool) -> DeliberationLLM:
    consolidation = truncate_first(1, competent_clerk) if flaky_consolidation else competent_clerk
    return DeliberationLLM(
        options=reserve_options(),
        confrontation={"P1": {"acts": [act("P2", "critique", "solution", "objection à P2")]}},
        consolidation=consolidation,
        comparison=truncate_first(1, compare_all),
    )


def test_budget_exactly_nominal_plus_comparison_retry_plus_gate_completes(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    # 1 + 3 + 3 + 3 (confrontation) + 1 (consolidation) + 1 + 1 (comparaison + relance) + 1 + 1 = 15
    llm = use_llm(_reserve_llm(flaky_consolidation=False))
    mission = run(
        client, llm, "B8 test 1 : nominal + relance comparaison + porte", max_llm_calls=15
    )
    assert mission["llm_calls_used"] == 15 == mission["max_llm_calls"]
    assert mission["stop_reason"] == ""
    comp = mission["deliberation"]["comparison"]
    assert [a["families"] for a in comp["attempts"]] == [5, 2]
    assert comp["status"] == "ok"
    rec = mission["recommendation"]
    assert rec["gate"]["passed"] is True
    assert rec["decision_ready"] is True
    # La révision (facultative) a cédé devant le pire cas borné du cœur : aucun appel de révision.
    assert not [c for c in llm.calls if c["call_type"] == "revision"]
    reserved = [
        e
        for e in journal(client, mission["id"])
        if e["entry_type"] == "budget_reserved_for_synthesis"
    ]
    assert reserved
    assert reserved[0]["payload"]["synthesis_core_worst_case_calls"] == 7


def test_budget_insufficient_for_retry_keeps_the_gate(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    llm = use_llm(_reserve_llm(flaky_consolidation=False))
    mission = run(client, llm, "B8 test 2 : relance refusée, porte exécutée", max_llm_calls=14)
    assert mission["llm_calls_used"] == 14 == mission["max_llm_calls"]
    assert mission["stop_reason"] == ""
    comp = mission["deliberation"]["comparison"]
    assert comp["status"] == "failed"
    assert [a["families"] for a in comp["attempts"]] == [5]
    entries = journal(client, mission["id"])
    refused = next(e for e in entries if e["entry_type"] == "retry_refused_budget")
    assert refused["payload"]["reserved_for_higher_priority"] == 2  # synthèse + porte
    rec = mission["recommendation"]
    assert rec["status"] == "produced"
    assert rec["gate"]["passed"] is False
    assert rec["quality_blocked"] is True
    assert "porte_qualite" in mission["deliberation"]["steps_done"]


@pytest.mark.parametrize(
    ("max_calls", "expected_comparison_attempts", "expected_status"),
    [(17, [5, 2], "ok"), (16, [5], "failed")],
)
def test_consolidation_and_comparison_retries_in_the_same_mission(
    client: TestClient,
    use_llm: Callable[..., DeliberationLLM],
    max_calls: int,
    expected_comparison_attempts: list[int],
    expected_status: str,
) -> None:
    # 1 + 3 + 3 + 3 + [1 + 2] (consolidation + relance scindée) + [1 (+1)] + 1 + 1
    llm = use_llm(_reserve_llm(flaky_consolidation=True))
    mission = run(
        client, llm, f"B8 test 3 : deux relances sous {max_calls} appels", max_llm_calls=max_calls
    )
    cons = mission["deliberation"]["consolidation"]
    assert cons["retries"] == 1
    assert cons["calls"] == 3
    assert cons["status"] == "ok"
    comp = mission["deliberation"]["comparison"]
    assert [a["families"] for a in comp["attempts"]] == expected_comparison_attempts
    assert comp["status"] == expected_status
    # Test 4 : le plafond est atteint, mais jamais au détriment de la porte qualité.
    assert mission["llm_calls_used"] == max_calls == mission["max_llm_calls"]
    assert mission["stop_reason"] == ""
    assert "porte_qualite" in mission["deliberation"]["steps_done"]
    rec = mission["recommendation"]
    assert rec["gate"]["passed"] is (expected_status == "ok")
    assert rec["decision_ready"] is (expected_status == "ok")


def test_class_ceilings_are_unchanged_by_v13() -> None:
    from app.config import Settings
    from app.mission_budget import class_ceilings

    settings = Settings.model_construct()
    assert class_ceilings(settings, "courante") == (16, 1.5)
    assert class_ceilings(settings, "importante_provisoire") == (30, 3.0)
    assert class_ceilings(settings, "structurante") == (60, 8.0)
    assert class_ceilings(settings, "critique") == (90, 15.0)


# Garde-fou épistémique — hypothèses conditionnelles explicites.
CASE_A = "le coût serait de 10 M€ si le volume restait constant"
CASE_B = "le coût sera de 10 M€ parce que le volume restera constant"
CASE_C = "on ne connaît pas la réaction du volume à la mesure"


def test_epistemic_classifier_distinguishes_conditional_behavioural_and_unknown() -> None:
    from app.mission_deliberation import (
        CONFRONTATION_SYSTEM,
        EPISTEMIC_RULE,
        SYNTHESIS_SYSTEM,
        build_map_view,
        classify_epistemic,
        epistemic_tag,
    )

    assert classify_epistemic(CASE_A) == "conditional_calculation"
    assert classify_epistemic(CASE_B) == "behavioural_hypothesis"
    assert classify_epistemic(CASE_C) == "declared_unknown"
    assert classify_epistemic("le volume devrait baisser de 10 %") == "forecast"
    assert classify_epistemic("le volume est de 1 000 unités") == "statement"
    assert epistemic_tag(CASE_A) == "calcul conditionnel (valide sous sa condition)"
    # La règle est transmise aux instances de confrontation et de synthèse : un calcul
    # conditionnel n'est jamais requalifié en erreur ou incohérence.
    assert EPISTEMIC_RULE in CONFRONTATION_SYSTEM
    assert EPISTEMIC_RULE in SYNTHESIS_SYSTEM
    assert "ne le requalifie jamais en erreur ou en incohérence" in EPISTEMIC_RULE
    view = build_map_view(
        {
            "positions": [],
            "hypotheses": [
                {"text": CASE_A, "experts": ["E1"]},
                {"text": CASE_B, "experts": ["E2"]},
            ],
        }
    )
    assert f"{CASE_A} [calcul conditionnel (valide sous sa condition)]" in view
    assert f"{CASE_B} [hypothèse comportementale (condition présentée comme prédiction)]" in view


def test_conditional_assumptions_are_tagged_in_the_synthesis_matter(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    framing = {**THREE_DIM_FRAMING, "assumptions": [CASE_A, CASE_B, CASE_C]}
    llm = use_llm(DeliberationLLM(framing=framing))
    mission = run(client, llm, "hypothèses conditionnelles étiquetées")
    synthesis_prompt = next(c for c in llm.calls if c["call_type"] == "synthesis")["prompt"]
    assert f"{CASE_A} [calcul conditionnel (valide sous sa condition)]" in synthesis_prompt
    assert (
        f"{CASE_B} [hypothèse comportementale (condition présentée comme prédiction)]"
        in synthesis_prompt
    )
    assert (
        f"{CASE_C} [inconnue déclarée (scénario conditionnel, pas une prévision)]"
        in synthesis_prompt
    )
    confrontation_systems = {c["system"] for c in llm.calls if c["call_type"] == "confrontation"}
    assert all("Calibration épistémique" in s for s in confrontation_systems)
    assert mission["recommendation"]["status"] == "produced"


# --- Correction d'audit v1.3.1 (B9 : explosion des familles obligatoires) ----------------------
B9_FRAMING: dict[str, Any] = {
    **THREE_DIM_FRAMING,
    "problem_understood": "cas synthétique B9 : deux dimensions critiques, prolifération d'options",
    "dimensions": [
        {
            "name": "dimension alpha",
            "why": "dimension présumée critique",
            "presumed_criticality": "high",
            "unknowns": [],
            "suggested_angles": ["praticien", "mesure", "sceptique"],
        },
        {
            "name": "dimension beta",
            "why": "dimension présumée critique",
            "presumed_criticality": "high",
            "unknowns": [],
            "suggested_angles": ["utilisateur", "théoricien", "conformité"],
        },
        {
            "name": "dimension gamma",
            "why": "dimension secondaire",
            "presumed_criticality": "low",
            "unknowns": [],
            "suggested_angles": ["intégration"],
        },
    ],
}
B9_INPUT = "Nous hésitons entre le plan alpha, le plan beta et le plan gamma."


def b9_options() -> dict[str, OptionSpec]:
    """33 familles attendues : prolifération diagnostic / action / test / non-action sur deux
    dimensions critiques (E1aE3 alpha, E4aE6 beta), une dimension secondaire (E7), 5 variantes de
    non-action, 3 stratégies citées dans la demande, une minorité sérieuse avec désaccord interne
    (option omega, E7 seul), deux stratégies multi-dimensionnelles ou à deux soutiens."""
    return {
        "E1": [
            ("plan alpha", "build"),
            ("diagnostic A1", "test"),
            ("action A1", "build"),
            ("action A2", "build"),
            ("attendre T1", "wait"),
            ("action A7", "build"),
            ("diagnostic A3", "test"),
        ],
        "E2": [
            ("action A3", "build"),
            ("action A4", "build"),
            ("diagnostic A2", "test"),
            ("ne rien faire", "do_nothing"),
            ("stratégie commune", "integrate"),
        ],
        "E3": [
            ("action A5", "build"),
            ("action A6", "simplify"),
            ("attendre T2", "wait"),
            ("plan gamma", "buy"),
            ("action A8", "build"),
        ],
        "E4": [
            ("plan beta", "build"),
            ("action B1", "build"),
            ("action B2", "build"),
            ("diagnostic B1", "test"),
            ("stratégie commune", "integrate"),
        ],
        "E5": [
            ("action B3", "build"),
            ("action B4", "simplify"),
            ("geler le périmètre", "do_nothing"),
            ("attendre T3", "wait"),
            ("plan courant", "build"),
            ("action B6", "build"),
        ],
        "E6": [
            ("action B5", "build"),
            ("diagnostic B2", "test"),
            ("plan courant", "build"),
            ("action B7", "build"),
            ("action B8", "build"),
        ],
        "E7": [("option omega", "buy"), ("action G1", "build")],
    }


INTERNAL_DISAGREEMENT_STEMS.add("option omega")
NON_ACTION_LABELS = {
    "attendre t1",
    "attendre t2",
    "attendre t3",
    "ne rien faire",
    "geler le perimetre",
}


def _b9_mission(
    client: TestClient, use_llm: Callable[..., DeliberationLLM], name: str, **kw: Any
) -> tuple[dict[str, Any], DeliberationLLM]:
    llm = use_llm(
        DeliberationLLM(framing=B9_FRAMING, options=b9_options(), consolidation=competent_clerk)
    )
    mission = run(client, llm, name, declared_class="structurante", **kw)
    return mission, llm


def test_b9_stress_coverage_without_mandatory_explosion(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    mission, _ = _b9_mission(
        client, use_llm, "B9 stress : 33 familles, 2 dimensions critiques", input_text=B9_INPUT
    )
    assert len(mission["composition"]["experts"]) == 7
    cons = mission["deliberation"]["consolidation"]
    assert cons["status"] == "ok"
    assert 30 <= cons["family_count"] <= 40
    families = {f["family_id"]: f for f in cons["families"]}
    by_label = {f["label"]: f["family_id"] for f in cons["families"]}
    comp = mission["deliberation"]["comparison"]
    retained = comp["retained_family_ids"]
    # Invariant dur : jamais plus de 12 familles dans une tentative normale.
    assert len(retained) <= 12
    assert all(a["families"] <= 12 for a in comp["attempts"])
    assert comp["status"] == "ok"
    assert comp["coverage_preserved"] is True
    assert comp["hard_mandatory_conflict"] is False
    # Hard : seulement les stratégies citées et le désaccord interne unique — pas d'explosion.
    hard = set(comp["hard_mandatory_family_ids"])
    cited = {by_label["plan alpha"], by_label["plan beta"], by_label["plan gamma"]}
    assert cited <= hard
    assert hard <= cited | {by_label["option omega"]}
    assert len(comp["mandatory_family_ids"]) <= 12
    assert len(comp["mandatory_family_ids"]) < cons["family_count"] / 2
    # Couverture : représentée, jamais exhaustive.
    retained_set = set(retained)
    dims_retained = {d for fid in retained for d in families[fid]["dimensions"]}
    assert {"dimension alpha", "dimension beta"} <= dims_retained
    non_action_retained = [fid for fid in retained if families[fid]["label"] in NON_ACTION_LABELS]
    assert 1 <= len(non_action_retained) <= 3
    assert len([f for f in cons["families"] if f["label"] in NON_ACTION_LABELS]) == 5
    kinds_retained = {families[fid]["kind"] for fid in retained}
    assert kinds_retained >= {"build", "test", "wait", "do_nothing", "integrate", "simplify", "buy"}
    assert by_label["option omega"] in retained_set  # minorité sérieuse conservée
    assert families[by_label["option omega"]]["internal_disagreements"] == ["périmètre contesté"]
    # Les redondances sont écartées, et la sélection n'est pas « les plus soutenues ».
    assert len(comp["not_compared"]) >= 20
    most_supported = sorted(
        cons["families"],
        key=lambda f: (-len(f["supporting_experts"]), int(f["family_id"][1:])),
    )[:12]
    assert {f["family_id"] for f in most_supported} != retained_set
    # Observabilité : chaque famille a un rôle et une raison ; les exigences sont tracées.
    roles = {s["role"] for s in comp["selection"].values()}
    assert roles >= {"hard", "coverage", "optional", "deferred"}
    assert all(s["reasons"] for s in comp["selection"].values())
    assert len(comp["selection"]) == cons["family_count"]
    req_ids = {r["id"] for r in comp["coverage_requirements"]}
    assert {
        "critical_dimension:dimension alpha",
        "critical_dimension:dimension beta",
        "non_action",
    } <= req_ids
    assert all(r["satisfied_by"] in retained_set for r in comp["coverage_requirements"])
    assert comp["unsatisfied_requirements"] == []
    entries = journal(client, mission["id"])
    sel = next(e for e in entries if e["step"] == "comparaison" and e["entry_type"] == "selection")
    assert sel["payload"]["families_total"] == cons["family_count"]
    assert sel["payload"]["cap"] == 12
    assert sel["payload"]["hard_conflict"] is False
    assert all(set(r["assessments"]) == set(comp["criteria"]) for r in comp["rows"])
    rec = mission["recommendation"]
    assert rec["gate"]["passed"] is True
    assert rec["decision_ready"] is True
    assert mission["llm_calls_used"] <= 60


def test_b9_hard_mandatory_saturation_is_explicit_and_fail_closed(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    demanded = (
        "plan alpha, plan beta, plan gamma, action A1, action A2, action A3, action A4, action A5, "
        "action B1, action B2, action B3, action B4, action B5"
    )
    mission, llm = _b9_mission(
        client,
        use_llm,
        "B9 saturation : 13 stratégies exigées",
        input_text=f"Compare précisément : {demanded}.",
    )
    comp = mission["deliberation"]["comparison"]
    assert comp["hard_mandatory_conflict"] is True
    assert len(comp["hard_mandatory_family_ids"]) >= 13
    assert comp["status"] == "failed"
    assert "hard_mandatory_exceeds_cap" in comp["coverage_note"]
    # Aucune tentative normale n'envoie plus de 12 familles ; aucune hard supprimée en silence.
    assert comp["attempts"] == []
    assert not [c for c in llm.calls if c["call_type"] == "comparison"]
    assert comp["retained_family_ids"] == []
    assert all(
        comp["selection"][fid]["role"] == "hard" for fid in comp["hard_mandatory_family_ids"]
    )
    entries = journal(client, mission["id"])
    assert any(e["entry_type"] == "hard_mandatory_exceeds_cap" for e in entries)
    # Synthèse et porte restent exécutées ; rien n'est « prêt ».
    assert {"synthese", "porte_qualite"} <= set(mission["deliberation"]["steps_done"])
    rec = mission["recommendation"]
    assert rec["status"] == "produced"
    assert rec["gate"]["passed"] is False
    assert "upstream_stage_failed:comparaison" in rec["gate"]["integrity_failures"]
    assert rec["decision_ready"] is False
    assert rec["quality_blocked"] is True
    synthesis_prompt = next(c for c in llm.calls if c["call_type"] == "synthesis")["prompt"]
    assert "Comparaison INVALIDE" in synthesis_prompt


def test_b9_generic_shape_does_not_turn_most_families_into_mandatory(
    client: TestClient, use_llm: Callable[..., DeliberationLLM]
) -> None:
    # Forme générique : nombreuses familles, deux dimensions critiques, prolifération
    # diagnostic / action / test / non-action, > 12 candidates potentiellement importantes,
    # aucune stratégie citée dans la demande.
    mission, _ = _b9_mission(client, use_llm, "B9 forme générique sans citation")
    cons = mission["deliberation"]["consolidation"]
    comp = mission["deliberation"]["comparison"]
    assert cons["family_count"] >= 30
    candidates_in_critical_dims = [
        f for f in cons["families"] if set(f["dimensions"]) & {"dimension alpha", "dimension beta"}
    ]
    assert (
        len(candidates_in_critical_dims) > 12
    )  # l'ancienne règle les aurait toutes rendues obligatoires
    assert len(comp["hard_mandatory_family_ids"]) <= 1  # seul le désaccord interne unique
    assert len(comp["mandatory_family_ids"]) <= 12
    assert len(comp["retained_family_ids"]) <= 12
    assert comp["status"] == "ok"
    assert comp["coverage_preserved"] is True
    assert mission["recommendation"]["decision_ready"] is True
