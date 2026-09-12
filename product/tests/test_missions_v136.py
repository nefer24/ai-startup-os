"""OT-V1, incrément 2 — correctif v1.3.6 (B15 / B16 / B17 / E1, §6-§10) : tests obligatoires A-K.

Fixtures purement synthétiques : aucun texte métier de Mission #9 n'est réutilisé ; les faux clients
de `test_missions_deliberation` sont enveloppés pour scripter les défaillances (raisonnement seul,
sortie coupée, qualification manquante). Les tests d'exécution passent par l'API HTTP réelle.
"""

from __future__ import annotations

import dataclasses
import json
import re
from collections.abc import Callable, Iterator
from types import SimpleNamespace
from typing import Any, ClassVar

import pytest
from app.config import Settings, get_settings
from app.consensus_guard import claims_superiority, consensus_as_evidence
from app.llm import AnthropicLLMClient, LLMClient, LLMResponse, LLMUsage
from app.mission_budget import (
    class_ceilings,
    deliberation_reserve,
    feasible_expert_count,
    mandatory_steelman_calls,
    minimal_deliberation_bound,
    revision_allowance,
    self_qualification_plan,
)
from app.mission_deliberation import classify_fact_source, find_discarded_alternative
from app.mission_schemas import ComparisonOutput
from app.reasoning_policy import (
    CALL_TYPE_CATEGORY,
    ReasoningPolicy,
    policy_table,
    reasoning_policy_for,
)
from app.structured_output import salvage_structured_output, salvage_truncated_json
from fastapi.testclient import TestClient

from tests.test_missions_deliberation import (
    POSITIONS,
    THREE_DIM_FRAMING,
    DeliberationLLM,
    FakeResearchProvider,
    OptionSpec,
    act,
    competent_clerk,
    default_comparison,
    default_synthesis,
    families_to_compare,
)
from tests.test_missions_output_budget import ANGLE_WORDS, options_for

# Contrats produit (réglages par défaut de `Settings`) utilisés par la borne de composition.
BATCH, META, OPTIONS_CAP, REVISION_CAP, GROUP_MAX, SELFQ_CEILING = 16, 32, 5, 8, 3, 6000
CLASSES = ["courante", "importante", "structurante", "critique"]
_CURRENT: dict[str, Any] = {}


# --- Fixtures ------------------------------------------------------------------------------------
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


def _post(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload = {"input_type": "problem", "input_text": "entrée synthétique v136"}
    payload.update(overrides)
    response = client.post("/missions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _journal(client: TestClient, mission_id: int) -> list[dict[str, Any]]:
    return list(client.get(f"/missions/{mission_id}/journal").json())


def _entries(client: TestClient, mission_id: int, entry_type: str) -> list[dict[str, Any]]:
    return [e for e in _journal(client, mission_id) if e["entry_type"] == entry_type]


def _bound(n: int, effective_class: str, *, options: int = OPTIONS_CAP) -> dict[str, Any]:
    return minimal_deliberation_bound(
        n,
        effective_class=effective_class,
        options_per_expert=options,
        batch_size=BATCH,
        meta_chunk_size=META,
        revision_cap=REVISION_CAP,
        self_qualification_group_max=GROUP_MAX,
        self_qualification_ceiling=SELFQ_CEILING,
    )


def framing_with(dims: list[tuple[str, str, list[str]]], **extra: Any) -> dict[str, Any]:
    """Cadrage synthétique : (nom, criticité, angles suggérés) par dimension."""
    return {
        **THREE_DIM_FRAMING,
        "problem_understood": "cas synthétique v136",
        "dimensions": [
            {
                "name": name,
                "why": "dimension du cas synthétique v136",
                "presumed_criticality": crit,
                "unknowns": [],
                "suggested_angles": angles,
            }
            for name, crit, angles in dims
        ],
        **extra,
    }


def single_angle_framing(n: int, crit: str = "high") -> dict[str, Any]:
    return framing_with(
        [(f"dimension v136-{i + 1}", crit, [ANGLE_WORDS[i % len(ANGLE_WORDS)]]) for i in range(n)]
    )


def objections_from_p1(n: int) -> dict[str, dict[str, Any]]:
    """P1 objecte à toutes les autres positions (une objection ouverte par position)."""
    return {
        "P1": {
            "acts": [
                act(f"P{k}", "critique", "solution", f"objection à P{k}") for k in range(2, n + 1)
            ]
        }
    }


# =================================================================================================
# A — Propriété de la réserve (B15) : une seule formule, composition ≡ exécution, promesse tenable.
# =================================================================================================
@pytest.mark.parametrize("effective_class", CLASSES)
def test_a_reserve_property_over_classes_options_widths_and_budgets(effective_class: str) -> None:
    for options in (2, 3, 4, 5):
        bounds = {n: _bound(n, effective_class, options=options) for n in range(2, 21)}
        for n, b in bounds.items():
            comps = b["reserve_components"]
            # La borne est la somme exacte de ses parties nommées.
            assert b["pre_deliberation_calls"] == n + b["self_qualification_calls"]
            assert b["total_required_calls"] == (
                b["pre_deliberation_calls"] + b["minimal_deliberation_reserve"]
            )
            assert b["minimal_deliberation_reserve"] == sum(
                comps[k]
                for k in (
                    "confrontation",
                    "steelman",
                    "revisions",
                    "consolidation",
                    "comparison",
                    "synthesis",
                    "gate",
                )
            )
            assert comps["confrontation"] == n
            assert comps["steelman"] == mandatory_steelman_calls(effective_class)
            assert comps["revisions"] == revision_allowance(n, cap=REVISION_CAP) >= 1
            assert comps["consolidation"] == b["consolidation_calls_upper_bound"]
            assert comps["core_nominal"] == comps["consolidation"] + 3
            # Même formule que les portes de dépense de l'exécution.
            assert comps == deliberation_reserve(
                n,
                effective_class=effective_class,
                consolidation_calls=b["consolidation_calls_upper_bound"],
                revision_cap=REVISION_CAP,
            )
            plan = self_qualification_plan(n, group_max=GROUP_MAX, output_ceiling=SELFQ_CEILING)
            assert b["self_qualification_calls"] == plan["calls"] == -(-n // plan["group_size"])
            assert 1 <= plan["group_size"] <= GROUP_MAX
            # Croissance : plus large coûte au moins autant.
            if n > 2:
                assert b["total_required_calls"] >= bounds[n - 1]["total_required_calls"]
        for budget in range(20, 61):
            remaining = budget - 1  # après le cadrage
            n_feasible = feasible_expert_count(
                remaining,
                effective_class=effective_class,
                options_per_expert=options,
                batch_size=BATCH,
                meta_chunk_size=META,
                revision_cap=REVISION_CAP,
                self_qualification_group_max=GROUP_MAX,
                self_qualification_ceiling=SELFQ_CEILING,
            )
            for n, b in bounds.items():
                feasible = b["total_required_calls"] <= remaining
                assert (n_feasible >= n) == feasible
                if feasible:
                    # Promesse B15 : après Tour 0, auto-qualification et confrontation, ce qui
                    # reste finance steelman requis + révisions réservées + cœur nominal.
                    comps = b["reserve_components"]
                    after = remaining - b["pre_deliberation_calls"] - comps["confrontation"]
                    assert after >= comps["steelman"] + comps["revisions"] + comps["core_nominal"]
    # Une seule position : ni auto-qualification, ni confrontation, ni steelman, ni révision.
    b1 = _bound(1, effective_class)
    assert b1["self_qualification_calls"] == 0
    assert b1["reserve_components"]["confrontation"] == 0
    assert b1["reserve_components"]["steelman"] == 0
    assert b1["reserve_components"]["revisions"] == 0
    assert b1["total_required_calls"] == 1 + b1["reserve_components"]["core_nominal"]


def test_a_class_ceilings_are_unchanged_by_v136() -> None:
    settings = Settings.model_construct()
    assert class_ceilings(settings, "structurante") == (60, 8.0)
    assert class_ceilings(settings, "critique") == (90, 15.0)
    assert class_ceilings(settings, "importante") == (30, 3.0)
    assert class_ceilings(settings, "courante") == (16, 1.5)


@pytest.mark.parametrize("n", [2, 3, 4, 5, 6])
def test_a_plan_feasible_is_a_kept_promise_at_the_exact_bound(
    client: TestClient, use_llm: Callable[..., Any], n: int
) -> None:
    # `n` dimensions critiques à un angle, classe structurante, budget = borne exacte + cadrage.
    # P1 objecte à toutes les autres positions : les révisions réservées (⌈n/2⌉) sont exécutées,
    # le steelman obligatoire aussi, la porte est atteinte — rien d'obligatoire n'est sacrifié.
    total = _bound(n, "structurante")["total_required_calls"]
    # 5 options par expert : le plan réel de consolidation coïncide avec la borne (aucun jeu).
    llm = use_llm(
        DeliberationLLM(
            framing=single_angle_framing(n),
            options=options_for(n, 5),
            confrontation=objections_from_p1(n),
            consolidation=competent_clerk,
        )
    )
    mission = _post(client, declared_class="structurante", max_llm_calls=total + 1)
    bounds = mission["composition"]["bounds"]
    assert bounds["plan_feasible"] is True
    assert bounds["total_required_calls"] == total == bounds["remaining_calls_at_composition"]
    assert len(mission["composition"]["experts"]) == n
    assert mission["status"] == "candidate"
    assert mission["stop_reason"] == ""
    assert mission["llm_calls_used"] <= total + 1
    done = mission["deliberation"]["steps_done"]
    for step in ("confrontation", "steelman", "consolidation", "comparaison", "synthese"):
        assert step in done, step
    assert "porte_qualite" in done
    st = mission["deliberation"]["steelman"]
    assert st["required"] is True
    assert st["status"] in {"accepted", "accepted_partial"}
    assert [c["call_type"] for c in llm.calls].count("steelman") == 1
    allowance = revision_allowance(n, cap=REVISION_CAP)
    assert mission["deliberation"]["reserve"]["revision_allowance"] == allowance
    revisions = mission["deliberation"]["revisions"]
    candidates = [r for r in revisions if r.get("new_information_ids")]
    called = [r for r in revisions if r["called"]]
    assert len(called) == min(len(candidates), allowance) >= 1
    assert all(r["within_reserved_allowance"] for r in called)
    entries = _journal(client, mission["id"])
    assert not [e for e in entries if e["entry_type"] == "skipped_for_deliberation_reserve"]
    # Seules des révisions AU-DELÀ de l'allocation peuvent avoir cédé.
    yielded = [e for e in entries if e["entry_type"] == "budget_reserved_for_synthesis"]
    assert len(yielded) == max(0, len(candidates) - allowance)
    assert all(e["payload"]["skipped"].startswith("révision de") for e in yielded)
    assert mission["recommendation"]["gate"]["passed"] is True


# =================================================================================================
# B — Cas synthétique de la forme de Mission #9 : 6 dimensions (5 high, 1 medium), 17 perspectives.
# =================================================================================================
def mission9_shape_framing() -> dict[str, Any]:
    names = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]
    dims: list[tuple[str, str, list[str]]] = []
    for i, name in enumerate(names):
        crit = "medium" if i == 5 else "high"
        width = 2 if i == 5 else 3
        angles = [ANGLE_WORDS[(3 * i + k) % len(ANGLE_WORDS)] for k in range(width)]
        dims.append((f"dimension v136 {name}", crit, angles))
    return framing_with(dims)


def test_b_synthetic_mission9_shape_reaches_the_gate_with_steelman_and_revision(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    framing = mission9_shape_framing()
    assert sum(len(d["suggested_angles"]) for d in framing["dimensions"]) == 17
    llm = use_llm(
        DeliberationLLM(
            framing=framing,
            options=options_for(17, 5),
            confrontation={"P1": {"acts": [act("P2", "critique", "solution", "objection à P2")]}},
            consolidation=competent_clerk,
        )
    )
    mission = _post(client, declared_class="structurante")
    assert (mission["max_llm_calls"], mission["max_cost_eur"]) == (60, 8.0)
    bounds = mission["composition"]["bounds"]
    # B15 : 17 perspectives ne sont pas finançables (17 + 6 + 17 + 2 + 8 + 12 = 62 > 59) ;
    # 16 le sont exactement (16 + 6 + 16 + 2 + 8 + 11 = 59). La largeur est réduite d'un angle
    # (jamais une dimension critique) et le plan est faisable AVANT tout Tour 0.
    assert bounds["max_experts_feasible_deliberation"] == 16
    assert bounds["experts_proposed"] == 17
    assert bounds["experts_retained"] == 16
    assert bounds["plan_feasible"] is True
    assert bounds["total_required_calls"] == 59 == bounds["remaining_calls_at_composition"]
    assert bounds["reserve_components"] == {
        "confrontation": 16,
        "steelman": 2,
        "revisions": 8,
        "consolidation": 8,
        "comparison": 1,
        "synthesis": 1,
        "gate": 1,
        "core_nominal": 11,
        "total": 37,
    }
    assert mission["composition"]["uncovered_dimensions"] == []
    assert len(mission["composition"]["experts"]) == 16
    # Traversée complète sous les plafonds, steelman fait, au moins une révision exécutée.
    assert mission["status"] == "candidate"
    assert mission["stop_reason"] == ""
    assert mission["llm_calls_used"] <= 60
    assert mission["cost_eur"] <= 8.0
    done = mission["deliberation"]["steps_done"]
    for step in (
        "confrontation",
        "steelman",
        "revision",
        "consolidation",
        "comparaison",
        "synthese",
        "porte_qualite",
    ):
        assert step in done, step
    st = mission["deliberation"]["steelman"]
    assert st["required"] is True
    assert st["status"] in {"accepted", "accepted_partial"}
    called = [r for r in mission["deliberation"]["revisions"] if r["called"]]
    assert len(called) >= 1
    assert all(r["within_reserved_allowance"] for r in called)
    cons = mission["deliberation"]["consolidation"]
    assert cons["status"] == "ok"
    assert cons["unconsolidated_option_ids"] == []
    comp = mission["deliberation"]["comparison"]
    assert comp["status"] == "ok"
    assert len(comp["retained_family_ids"]) <= 12
    rec = mission["recommendation"]
    assert rec["status"] == "produced"
    assert rec["gate"]["passed"] is True
    assert rec["decision_ready"] is True
    counts: dict[str, int] = {}
    for c in llm.calls:
        counts[c["call_type"]] = counts.get(c["call_type"], 0) + 1
    assert counts["expert_tour0"] == 16
    assert counts["self_qualification"] == 6  # groupée par 3
    assert counts["confrontation"] == 16
    assert counts["steelman"] == 1
    assert counts["revision"] >= 1
    entries = _journal(client, mission["id"])
    assert not [e for e in entries if e["entry_type"] == "skipped_for_deliberation_reserve"]
    assert not [e for e in entries if e["entry_type"] == "budget_reserved_for_synthesis"]
    assert mission["report"]["budget"]["reserved_deliberation_calls"] == 37


# =================================================================================================
# C — Politique de raisonnement (B16) : explicite par type d'appel, transmise au fournisseur,
#     journalisée ; le contenu des blocs de raisonnement ne fuit jamais.
# =================================================================================================
def test_c_policy_table_is_explicit_per_call_type_and_never_a_json_shortcut() -> None:
    settings = Settings.model_construct()
    table = policy_table(settings)
    assert set(table) == set(CALL_TYPE_CATEGORY)
    for ct in ("framing", "expert_tour0", "confrontation", "steelman", "revision", "synthesis"):
        assert table[ct]["category"] == "A"
        assert (table[ct]["thinking"], table[ct]["effort"]) == ("adaptive", "high")
        assert table[ct]["headroom_tokens"] == 0
    for ct in ("comparison", "quality_gate"):
        assert table[ct]["category"] == "B"
        assert (table[ct]["thinking"], table[ct]["effort"]) == ("adaptive", "medium")
        assert table[ct]["headroom_tokens"] == 1500
    for ct in ("self_qualification", "clerk", "consolidation"):
        assert table[ct]["category"] == "C"
        assert (table[ct]["thinking"], table[ct]["effort"]) == ("adaptive", "low")
        assert table[ct]["headroom_tokens"] == 500
    # Toutes les sorties sont du JSON : la politique n'est PAS « JSON = raisonnement désactivé ».
    assert {p["thinking"] for p in table.values()} == {"adaptive"}
    # Désactivation configurable de la seule catégorie C, jamais globale.
    disabled = policy_table(Settings.model_construct(mission_reasoning_thinking_c="disabled"))
    assert disabled["consolidation"]["thinking"] == "disabled"
    assert disabled["consolidation"]["headroom_tokens"] == 0
    assert disabled["framing"]["thinking"] == "adaptive"
    assert disabled["comparison"]["thinking"] == "adaptive"
    # Valeurs hors contrat → défauts sûrs ; type d'appel inconnu → catégorie A.
    odd = reasoning_policy_for(
        "confrontation",
        Settings.model_construct(mission_reasoning_effort_a="extreme"),
    )
    assert odd.effort == "high"
    assert reasoning_policy_for("nouveau_type", settings).category == "A"
    opts = ReasoningPolicy("x", "B", "adaptive", "medium", 1500).request_options()
    assert opts == {"thinking": {"type": "adaptive"}, "output_config": {"effort": "medium"}}


class _Block:
    def __init__(self, type_: str, **fields: str) -> None:
        self.type = type_
        for k, v in fields.items():
            setattr(self, k, v)


class FakeAnthropic:
    """Faux SDK : enregistre les paramètres de chaque `messages.create` et rend des blocs scriptés.

    `script(kwargs)` retourne (blocs, stop_reason, output_tokens). Le bloc de raisonnement porte
    un texte sentinelle qui ne doit apparaître nulle part (réponse, journal, mission).
    """

    recorded: ClassVar[list[dict[str, Any]]] = []
    script: ClassVar[Callable[[dict[str, Any]], tuple[list[Any], str, int]] | None] = None

    def __init__(self, api_key: str = "") -> None:
        self.messages = self

    def create(self, **kwargs: Any) -> Any:
        assert FakeAnthropic.script is not None
        FakeAnthropic.recorded.append(kwargs)
        content, stop_reason, output_tokens = FakeAnthropic.script(kwargs)
        return SimpleNamespace(
            content=content,
            stop_reason=stop_reason,
            usage=SimpleNamespace(input_tokens=1000, output_tokens=output_tokens),
        )


SENTINEL = "RAISONNEMENT-PRIVE-SENTINELLE-7f3a"


@pytest.fixture
def fake_anthropic(monkeypatch: pytest.MonkeyPatch) -> type[FakeAnthropic]:
    import anthropic

    FakeAnthropic.recorded = []
    FakeAnthropic.script = None
    monkeypatch.setattr(anthropic, "Anthropic", FakeAnthropic)
    return FakeAnthropic


@pytest.mark.parametrize(
    ("shape", "expected_text", "expected_blocks", "stop"),
    [
        ("thinking_only", "", {"thinking": 1}, "max_tokens"),
        ("thinking_and_text", '{"ok": true}', {"thinking": 1, "text": 1}, "end_turn"),
        ("text_only", '{"ok": true}', {"text": 1}, "end_turn"),
    ],
)
def test_c_provider_adapter_sends_the_policy_and_never_leaks_thinking(
    fake_anthropic: type[FakeAnthropic],
    shape: str,
    expected_text: str,
    expected_blocks: dict[str, int],
    stop: str,
) -> None:
    def script(kwargs: dict[str, Any]) -> tuple[list[Any], str, int]:
        blocks: list[Any] = []
        if shape != "text_only":
            blocks.append(_Block("thinking", thinking=SENTINEL))
        if shape != "thinking_only":
            blocks.append(_Block("text", text='{"ok": true}'))
        return blocks, stop, kwargs["max_tokens"] if stop == "max_tokens" else 120

    fake_anthropic.script = script
    settings = Settings.model_construct(mission_reasoning_thinking_c="disabled")
    client = AnthropicLLMClient(
        "k",
        "modele-synthetique",
        8000,
        reasoning_policy=lambda ct: reasoning_policy_for(ct, settings),
    )
    expected_options = {
        "framing": ({"type": "adaptive"}, {"effort": "high"}),
        "comparison": ({"type": "adaptive"}, {"effort": "medium"}),
        "consolidation": ({"type": "disabled"}, {"effort": "low"}),
    }
    for call_type, (thinking, output_config) in expected_options.items():
        response = client.complete_structured(
            system="s", prompt="p", call_type=call_type, max_tokens=2000
        )
        sent = fake_anthropic.recorded[-1]
        assert sent["thinking"] == thinking
        assert sent["output_config"] == output_config
        assert sent["max_tokens"] == 2000
        assert response.text == expected_text
        assert response.content_blocks == expected_blocks
        assert response.stop_reason == stop
        assert response.reasoning_policy is not None
        assert response.reasoning_policy["call_type"] == call_type
        assert response.reasoning_policy["thinking"] == thinking["type"]
        assert SENTINEL not in json.dumps(dataclasses.asdict(response), ensure_ascii=False)
    # Sans politique injectée : aucun paramètre de raisonnement envoyé (chemin historique).
    bare = AnthropicLLMClient("k", "m", 8000)
    bare.complete_structured(system="s", prompt="p", call_type="framing", max_tokens=10)
    assert "thinking" not in fake_anthropic.recorded[-1]
    assert "output_config" not in fake_anthropic.recorded[-1]


def test_c_mission_journal_carries_the_applied_policy_without_thinking_content(
    client: TestClient, use_llm: Callable[..., Any], fake_anthropic: type[FakeAnthropic]
) -> None:
    inner = DeliberationLLM()
    settings = get_settings()
    holder: dict[str, Any] = {}

    def policy(call_type: str) -> ReasoningPolicy:
        holder["call_type"] = call_type  # la politique est résolue juste avant l'appel
        return reasoning_policy_for(call_type, settings)

    def script(kwargs: dict[str, Any]) -> tuple[list[Any], str, int]:
        response = inner.complete_structured(
            system=kwargs["system"],
            prompt=kwargs["messages"][0]["content"],
            call_type=holder["call_type"],
            max_tokens=kwargs["max_tokens"],
        )
        return (
            [_Block("thinking", thinking=SENTINEL), _Block("text", text=response.text)],
            "end_turn",
            response.usage.output_tokens,
        )

    fake_anthropic.script = script
    use_llm(AnthropicLLMClient("k", "modele-synthetique", 8000, reasoning_policy=policy))
    mission = _post(client)
    assert mission["status"] == "candidate"
    assert mission["recommendation"]["status"] == "produced"
    table = policy_table(settings)
    entries = _journal(client, mission["id"])
    planned = [e for e in entries if e["entry_type"] == "call_planned"]
    done = [e for e in entries if e["entry_type"] == "call_done"]
    assert planned
    assert len(done) == len(planned) == mission["llm_calls_used"]
    for e in planned:
        ct = e["payload"]["call_type"]
        assert e["payload"]["reasoning_policy"] == table[ct]
    for e in done:
        ct = e["payload"]["call_type"]
        applied = e["payload"]["reasoning_policy_applied"]
        assert (applied["thinking"], applied["effort"], applied["category"]) == (
            table[ct]["thinking"],
            table[ct]["effort"],
            table[ct]["category"],
        )
        assert e["payload"]["content_blocks"] == {"thinking": 1, "text": 1}
    # Chaque appel réel a reçu la politique de son type ; le raisonnement n'a fui nulle part.
    assert len(fake_anthropic.recorded) == mission["llm_calls_used"]
    assert all("thinking" in k and "output_config" in k for k in fake_anthropic.recorded)
    dumped = json.dumps(entries, ensure_ascii=False) + json.dumps(mission, ensure_ascii=False)
    assert SENTINEL not in dumped
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert SENTINEL not in md
    # Le budget de sortie des étapes de catégorie B / C inclut la marge de raisonnement.
    by_type = {e["payload"]["call_type"]: e["payload"] for e in planned}
    assert by_type["comparison"]["output_budget"]["reasoning_headroom"] == 1500
    assert by_type["self_qualification"]["output_budget"]["reasoning_headroom"] == 500
    assert by_type["framing"]["output_budget"].get("reasoning_headroom", 0) == 0


# =================================================================================================
# D — Consolidation « raisonnement seul » : relance recalculée, jamais de famille inventée.
# =================================================================================================
class ThinkingOnly:
    """Vide le texte des `occurrences` choisies d'un type d'appel (bloc de raisonnement seul, à
    `max_tokens`) ; les autres réponses passent inchangées."""

    def __init__(self, inner: Any, call_type: str, occurrences: set[int] | None) -> None:
        self.inner = inner
        self.call_type = call_type
        self.occurrences = occurrences  # None = toutes
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
        if self.occurrences is not None and self.seen not in self.occurrences:
            return response
        return LLMResponse(
            text="",
            usage=LLMUsage(1000, max_tokens),
            stop_reason="max_tokens",
            content_blocks={"thinking": 1},
        )


def test_d_consolidation_thinking_only_is_retried_at_a_recalculated_limit_then_ok(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    llm = use_llm(
        ThinkingOnly(
            DeliberationLLM(options=options_for(3, 4), consolidation=competent_clerk),
            "consolidation",
            {1},
        )
    )
    mission = _post(client)
    cons = mission["deliberation"]["consolidation"]
    assert cons["status"] == "ok"
    assert cons["family_count"] == 12
    assert cons["unconsolidated_option_ids"] == []
    assert cons["calls"] == 1
    assert cons["llm_calls_spent"] == 2  # appel vide + relance recalculée
    assert cons["retries"] == 0  # aucune scission : ce n'est pas une erreur de schéma
    assert cons["salvaged_batches"] == 0
    invalid = _entries(client, mission["id"], "structured_output_invalid")
    assert len(invalid) == 1
    assert invalid[0]["payload"]["category"] == "structured_output_empty"
    assert invalid[0]["payload"]["content_blocks"] == {"thinking": 1}
    assert invalid[0]["payload"]["will_retry"] is True
    planned = _entries(client, mission["id"], "structured_output_retry_planned")
    assert len(planned) == 1
    assert planned[0]["payload"]["max_tokens"] > planned[0]["payload"]["max_tokens_initial"]
    granted = [c["max_tokens"] for c in llm.calls if c["call_type"] == "consolidation"]
    assert granted[1] > granted[0]
    assert mission["report"]["budget"]["structured_output_retries"] == 1
    assert mission["recommendation"]["gate"]["passed"] is True


def test_d_consolidation_thinking_only_twice_fails_closed_without_invention(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    use_llm(
        ThinkingOnly(
            DeliberationLLM(options=options_for(3, 4), consolidation=competent_clerk),
            "consolidation",
            None,
        )
    )
    mission = _post(client)
    cons = mission["deliberation"]["consolidation"]
    assert cons["status"] == "failed"
    assert cons["family_count"] == 0
    assert len(cons["unconsolidated_option_ids"]) == 12
    assert cons["parse_error"].startswith("structured_output_recovery_exhausted")
    assert "structured_output_empty" in cons["parse_error"]
    assert cons["llm_calls_spent"] == 2
    assert mission["report"]["budget"]["structured_output_retries"] == 1
    assert mission["recommendation"] is None
    assert mission["report"]["recommendation_produced"] is False


# =================================================================================================
# E — Comparaison coupée : récupération des lignes complètes, familles manquantes déclarées.
# =================================================================================================
def twelve_family_options() -> dict[str, OptionSpec]:
    return {
        "E1": [(f"stratégie a{k}", "build") for k in range(1, 5)],
        "E2": [(f"stratégie b{k}", "build") for k in range(1, 5)],
        "E3": [(f"stratégie c{k}", "build") for k in range(1, 5)],
    }


def truncated_rows_script(*, cut_label_fragment: str | None) -> Callable[[str, str], Any]:
    """Comparaison dont la ligne d'UNE famille est coupée en plein champ (les 11 autres sont
    complètes), à chaque tentative. `cut_label_fragment` désigne la famille coupée (par son
    libellé), sinon la dernière du bloc à comparer."""

    def script(label: str, prompt: str) -> dict[str, Any]:
        payload = default_comparison(prompt)
        ids = families_to_compare(prompt)
        cut_id = ids[-1]
        if cut_label_fragment:
            block = prompt.split("Familles stratégiques à comparer", 1)[-1]
            for line in block.splitlines():
                m = re.search(r"\b(F\d+)\b", line)
                if m and cut_label_fragment in line:
                    cut_id = m.group(1)
                    break
        complete = [r for r in payload["rows"] if r["family_id"] != cut_id]
        text = json.dumps({"criteria": payload["criteria"], "rows": complete}, ensure_ascii=False)
        assert text.endswith("]}")
        text = text[:-2] + ', {"family_id": "' + cut_id + '", "assessments": {"co'
        return {"__raw__": text, "__stop__": "max_tokens"}

    return script


@pytest.fixture
def options_cap(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[[int], None]]:
    def _set(cap: int) -> None:
        monkeypatch.setenv("MISSION_MAX_OPTIONS_PER_EXPERT", str(cap))
        get_settings.cache_clear()

    yield _set
    get_settings.cache_clear()


def test_e_truncated_comparison_salvages_eleven_complete_rows_and_declares_the_missing_one(
    client: TestClient, use_llm: Callable[..., Any], options_cap: Callable[[int], None]
) -> None:
    options_cap(8)
    llm = use_llm(
        DeliberationLLM(
            options=twelve_family_options(),
            consolidation=competent_clerk,
            comparison=truncated_rows_script(cut_label_fragment=None),
        )
    )
    mission = _post(client)
    cons = mission["deliberation"]["consolidation"]
    assert cons["family_count"] == 12
    comp = mission["deliberation"]["comparison"]
    assert len(comp["retained_family_ids"]) == 12
    # Une relance recalculée (B13) puis récupération des 11 lignes complètes : statut partiel,
    # famille manquante déclarée, aucune ligne complétée ni inventée.
    assert comp["status"] == "partial"
    assert comp["salvaged"] is True
    assert len(comp["missing_family_ids"]) == 1
    missing = comp["missing_family_ids"][0]
    evaluated = [r for r in comp["rows"] if r.get("assessments")]
    assert len(evaluated) == 11
    assert missing not in {r["family_id"] for r in evaluated}
    assert [a["families"] for a in comp["attempts"]] == [12]
    assert comp["attempts"][0]["salvaged"] is True
    assert len([c for c in llm.calls if c["call_type"] == "comparison"]) == 2
    assert mission["report"]["budget"]["structured_output_retries"] == 1
    salvaged = _entries(client, mission["id"], "structured_output_salvaged")
    assert len(salvaged) == 1
    assert salvaged[0]["payload"]["truncated_key"] == "rows"
    assert salvaged[0]["payload"]["items_kept"] == 11
    rec = mission["recommendation"]
    assert rec["status"] == "produced"
    assert any("comparaison partielle" in i and missing in i for i in rec["gate"]["issues"])
    assert rec["gate"]["checks"]["pipeline_integrity"] is True
    synthesis_prompt = next(c for c in llm.calls if c["call_type"] == "synthesis")["prompt"]
    assert missing in synthesis_prompt
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "Comparaison : statut **partial**" in md
    # La porte ne passe que si la recommandation ET les familles obligatoires ont été comparées.
    mandatory_missing = set(comp["mandatory_family_ids"]) & {missing}
    assert rec["gate"]["checks"]["recommended_family_compared"] is (not mandatory_missing)


def test_e_missing_mandatory_family_after_salvage_blocks_the_gate(
    client: TestClient, use_llm: Callable[..., Any], options_cap: Callable[[int], None]
) -> None:
    options_cap(8)
    use_llm(
        DeliberationLLM(
            options=twelve_family_options(),
            consolidation=competent_clerk,
            comparison=truncated_rows_script(cut_label_fragment="strategie c4"),
        )
    )
    mission = _post(client, input_text="Faut-il retenir la stratégie c4 ou une autre voie ?")
    comp = mission["deliberation"]["comparison"]
    by_label = {
        f["label"]: f["family_id"] for f in mission["deliberation"]["consolidation"]["families"]
    }
    cited = by_label["strategie c4"]
    assert cited in comp["hard_mandatory_family_ids"]
    assert comp["status"] == "partial"
    assert comp["missing_family_ids"] == [cited]
    rec = mission["recommendation"]
    assert rec["gate"]["checks"]["recommended_family_compared"] is False
    assert any("recommended_family_not_compared" in i and cited in i for i in rec["gate"]["issues"])
    assert rec["gate"]["passed"] is False
    assert rec["decision_ready"] is False


def test_e_salvage_is_deterministic_and_never_completes_a_value() -> None:
    raw = (
        '{"criteria": ["a", "b"], "rows": [{"family_id": "F1", "assessments": {"a": {"value": '
        '"x", "basis": "inference"}}}, {"family_id": "F2", "assessments": {"a": {"val'
    )
    result = salvage_truncated_json(raw)
    assert result.data == {
        "criteria": ["a", "b"],
        "rows": [{"family_id": "F1", "assessments": {"a": {"value": "x", "basis": "inference"}}}],
    }
    assert (result.truncated_key, result.items_kept, result.dropped_keys) == ("rows", 1, ())
    model, again = salvage_structured_output(
        LLMResponse(text=raw, usage=LLMUsage(1, 1), stop_reason="max_tokens"), ComparisonOutput
    )
    assert isinstance(model, ComparisonOutput)
    assert [r.family_id for r in model.rows] == ["F1"]
    assert again.to_dict()["salvaged"] is True
    # Valeur coupée qui n'est pas un tableau : clé abandonnée, jamais complétée.
    dropped = salvage_truncated_json('{"criteria": ["a"], "notes": "texte co')
    assert dropped.data == {"criteria": ["a"]}
    assert dropped.dropped_keys == ("notes",)
    # Aucun élément complet : la clé tronquée est vide (0 conservé) — l'exécution n'en fait rien
    # (`items_kept == 0` n'est jamais présenté comme une récupération).
    empty = salvage_truncated_json('{"rows": [{"family_id": "F')
    assert (empty.data, empty.truncated_key, empty.items_kept) == ({"rows": []}, "rows", 0)
    assert salvage_truncated_json("pas du json").data is None
    open_string = salvage_truncated_json('{"criteria": ["a')  # chaîne ouverte : 0 élément
    assert (open_string.data, open_string.items_kept) == ({"criteria": []}, 0)
    one = salvage_truncated_json('{"criteria": ["a"')  # élément fermé, tableau ouvert
    assert (one.data, one.truncated_key, one.items_kept) == ({"criteria": ["a"]}, "criteria", 1)


# =================================================================================================
# F — Steelman sous unanimité (B17) : l'alternative explicitement écartée est défendue.
# =================================================================================================
PROPOSAL_FRAMING = {
    **THREE_DIM_FRAMING,
    "explicit_proposals": [
        {
            "label": "externaliser la maintenance applicative",
            "kind": "buy",
            "proposed_by": "demandeur",
        }
    ],
}


def test_f_find_discarded_alternative_is_deterministic() -> None:
    positions = [
        {"label": "P1", "position": POSITIONS["E1"]},
        {"label": "P2", "position": POSITIONS["E2"]},
    ]
    options = [
        {
            "option_id": "E1-O1",
            "expert_id": "E1",
            "label": "option A",
            "kind": "build",
            "summary": "",
        },
        {
            "option_id": "E2-O1",
            "expert_id": "E2",
            "label": "externaliser la maintenance",
            "kind": "buy",
            "summary": "confier la maintenance à un tiers",
        },
    ]
    proposals = PROPOSAL_FRAMING["explicit_proposals"]
    found = find_discarded_alternative(
        proposals=proposals, option_groups=[], options=options, positions=positions, request_text=""
    )
    assert found is not None
    assert found["source"] == "framing"
    assert found["label"] == "externaliser la maintenance applicative"
    assert found["option_ids"] == ["E2-O1"]  # option listée, mais position non défendue
    assert found["endorsed_by"] == []
    # Défendue par une position → plus une alternative écartée.
    endorsed = [*positions, {"label": "P3", "position": "externaliser la maintenance applicative"}]
    assert (
        find_discarded_alternative(
            proposals=proposals,
            option_groups=[],
            options=options,
            positions=endorsed,
            request_text="",
        )
        is None
    )
    # Repli sans proposition de cadrage : groupe d'options fortement recoupé par la demande.
    groups = [{"label": "externaliser la maintenance", "option_ids": ["E2-O1"], "kinds": ["buy"]}]
    fallback = find_discarded_alternative(
        proposals=[],
        option_groups=groups,
        options=options,
        positions=positions,
        request_text="Faut-il externaliser la maintenance ?",
    )
    assert fallback is not None
    assert fallback["source"] == "options"
    assert (
        find_discarded_alternative(
            proposals=[],
            option_groups=groups,
            options=options,
            positions=positions,
            request_text="x",
        )
        is None
    )


def test_f_unanimous_positions_steelman_the_discarded_alternative_not_the_dominant_one(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    # Trois perspectives « identiques » (unanimité) ; la demande met une alternative sur la table
    # que personne ne défend : le steelman porte sur elle, avocat et contradicteur distincts.
    llm = use_llm(DeliberationLLM(framing=PROPOSAL_FRAMING, relation="identical"))
    mission = _post(client, declared_class="structurante")
    st = mission["deliberation"]["steelman"]
    assert st["required"] is True
    assert st["mode"] == "discarded_alternative"
    assert st["alternative"]["label"] == "externaliser la maintenance applicative"
    assert st["advocate"] != st["critic"]
    assert st["status"] in {"accepted", "accepted_partial"}
    types = [c["call_type"] for c in llm.calls]
    assert types.count("steelman") == 1
    assert types.count("steelman_challenge") == 1
    assert "steelman_recognition" not in types
    assert types.index("steelman") < types.index("steelman_challenge")
    steelman_call = next(c for c in llm.calls if c["call_type"] == "steelman")
    assert "externaliser la maintenance applicative" in steelman_call["prompt"]
    selected = _entries(client, mission["id"], "steelman_alternative_selected")
    assert len(selected) == 1
    assert selected[0]["payload"]["endorsed_by"] == []
    challenge = _entries(client, mission["id"], "alternative_challenge_result")
    assert len(challenge) == 1
    assert challenge[0]["payload"]["recognized"] == "yes"
    critiques = [
        o
        for o in mission["deliberation"]["confrontation"]["objections"]
        if o["act"] == "steelman_critique"
    ]
    assert len(critiques) == 1
    assert critiques[0]["target"].startswith("alternative écartée")
    gate = mission["recommendation"]["gate"]
    assert gate["checks"]["steelman_done_if_required"] is True
    assert gate["passed"] is True
    assert mission["llm_calls_used"] == 1 + 3 + 1 + 3 + 2 + 1 + 1 + 1 + 1
    # Témoin : même unanimité SANS alternative écartée → steelman classique de la position
    # dominante.
    llm = use_llm(DeliberationLLM(relation="identical"))
    control = _post(client, declared_class="structurante")
    st = control["deliberation"]["steelman"]
    assert "mode" not in st
    assert st["target"] == "P1"
    assert [c["call_type"] for c in llm.calls].count("steelman_recognition") == 1


# =================================================================================================
# G — La preuve prime sur la majorité (E1) : garde déterministe du consensus-comme-preuve.
# =================================================================================================
@pytest.mark.parametrize(
    ("text", "flagged"),
    [
        ("15 experts convergent donc X.", True),
        (
            "15 perspectives convergent ; indépendamment, les preuves X/Y soutiennent la "
            "recommandation.",
            False,
        ),
        (
            "Les positions convergent, sans réfutation factuelle : la stratégie est la meilleure.",
            True,
        ),
        ("La convergence des perspectives confirme que cette voie l'emporte.", True),
        ("Toutes les perspectives rejettent l'attente, ce qui justifie d'agir maintenant.", True),
        ("Plusieurs perspectives convergent vers cette hypothèse.", False),
        (
            "Plusieurs perspectives convergent, mais la recommandation repose principalement sur "
            "la mesure M et le contrat C.",
            False,
        ),
        ("La preuve P (source S, 2026) établit le coût ; la recommandation en découle.", False),
        ("Le consensus n'est pas une preuve : la décision repose sur la mesure M.", False),
    ],
)
def test_g_consensus_guard_targets_the_use_of_convergence_not_the_word(
    text: str, flagged: bool
) -> None:
    assert bool(consensus_as_evidence(text)) is flagged


def test_g_claims_superiority_is_lexical_and_narrow() -> None:
    assert claims_superiority("cette option est la meilleure stratégie") is True
    assert claims_superiority("l'option est supérieure aux autres") is True
    assert claims_superiority("tester pendant un cycle avant de décider") is False


def _synthesis_with(rationale: str, justification: str) -> Callable[[str, str], dict[str, Any]]:
    def script(label: str, prompt: str) -> dict[str, Any]:
        payload = default_synthesis(prompt)
        payload["recommendation"]["rationale"] = rationale
        payload["confidence"]["justification"] = justification
        return payload

    return script


def test_g_gate_rejects_consensus_as_evidence_even_if_the_llm_verdict_passes(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    use_llm(
        DeliberationLLM(
            synthesis=_synthesis_with(
                "15 experts convergent donc X.", "convergence forte, non réfutée, des positions"
            )
        )
    )
    mission = _post(client)
    gate = mission["recommendation"]["gate"]
    assert gate["llm_verdict"] is True
    assert gate["checks"]["no_consensus_as_evidence"] is False
    assert gate["consensus_as_evidence"] is True
    assert any(i.startswith("consensus_as_evidence") for i in gate["issues"])
    assert gate["passed"] is False
    assert mission["recommendation"]["decision_ready"] is False
    assert mission["recommendation"]["quality_blocked"] is True
    use_llm(
        DeliberationLLM(
            synthesis=_synthesis_with(
                "15 perspectives convergent ; indépendamment, les preuves X/Y soutiennent la "
                "recommandation.",
                "les preuves X et Y sont sourcées ; la convergence est un signal descriptif",
            )
        )
    )
    mission = _post(client)
    gate = mission["recommendation"]["gate"]
    assert gate["checks"]["no_consensus_as_evidence"] is True
    assert gate["consensus_as_evidence"] is False
    assert gate["passed"] is True
    # Les consignes de synthèse et de porte portent la doctrine.
    synthesis_call = next(c for c in _CURRENT["llm"].calls if c["call_type"] == "synthesis")
    assert "majorité" in synthesis_call["system"].lower()
    gate_call = next(c for c in _CURRENT["llm"].calls if c["call_type"] == "quality_gate")
    assert "convergence" in gate_call["system"].lower()


# =================================================================================================
# H — Auto-qualification proportionnée (§6) : groupée ≡ une par position ; rien n'est inventé.
# =================================================================================================
def _relations_by_expert(client: TestClient, mission_id: int) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for e in _journal(client, mission_id):
        if e["step"] == "auto_qualification" and e["entry_type"] == "result":
            out[e["actor"]] = sorted(e["payload"]["relations"], key=lambda r: r["other_id"])
    return out


def test_h_grouped_self_qualification_matches_per_position_results_with_fewer_calls(
    client: TestClient, use_llm: Callable[..., Any], settings_env: Callable[[str, str], None]
) -> None:
    framing = single_angle_framing(5, "low")
    settings_env("MISSION_SELF_QUALIFICATION_GROUP_MAX", "1")
    llm_full = use_llm(DeliberationLLM(framing=framing, relation="variant"))
    full = _post(client)
    settings_env("MISSION_SELF_QUALIFICATION_GROUP_MAX", "3")
    llm_grouped = use_llm(DeliberationLLM(framing=framing, relation="variant"))
    grouped = _post(client)
    assert len(full["composition"]["experts"]) == len(grouped["composition"]["experts"]) == 5
    calls_full = [c for c in llm_full.calls if c["call_type"] == "self_qualification"]
    calls_grouped = [c for c in llm_grouped.calls if c["call_type"] == "self_qualification"]
    assert (len(calls_full), len(calls_grouped)) == (5, 2)
    plan_full = _entries(client, full["id"], "plan")[0]["payload"]
    plan_grouped = _entries(client, grouped["id"], "plan")[0]["payload"]
    assert (plan_full["mode"], plan_full["calls"], plan_full["group_size"]) == (
        "per_position",
        5,
        1,
    )
    assert (plan_grouped["mode"], plan_grouped["calls"], plan_grouped["group_size"]) == (
        "grouped",
        2,
        3,
    )
    # Même cartographie : relations identiques position par position, mêmes indices.
    assert _relations_by_expert(client, full["id"]) == _relations_by_expert(client, grouped["id"])
    for key in (
        "divergence_index",
        "position_clusters",
        "self_qualification_coverage",
        "relations_missing_labels",
    ):
        assert full["cartography"][key] == grouped["cartography"][key], key
    assert grouped["cartography"]["relations_missing_labels"] == []
    # Chaque appel groupé est planifié pour toutes ses relations (g x (n - 1)), sous le plafond.
    planned = [
        e
        for e in _journal(client, grouped["id"])
        if e["entry_type"] == "call_planned" and e["payload"]["call_type"] == "self_qualification"
    ]
    assert [p["payload"]["number_of_required_items"] for p in planned] == [12, 8]
    assert all(p["payload"]["max_tokens"] <= 6000 for p in planned)
    assert grouped["llm_calls_used"] == full["llm_calls_used"] - 3


class DroppingQualification:
    """Retire du JSON groupé la qualification d'une position (réponse incomplète du modèle)."""

    def __init__(self, inner: Any, drop_from_id: str) -> None:
        self.inner = inner
        self.drop_from_id = drop_from_id
        self.calls = inner.calls

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
        data = json.loads(response.text)
        data["qualifications"] = [
            q for q in data.get("qualifications", []) if q["from_id"] != self.drop_from_id
        ]
        return dataclasses.replace(response, text=json.dumps(data, ensure_ascii=False))


def test_h_missing_qualification_in_a_grouped_answer_is_declared_never_invented(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    use_llm(DroppingQualification(DeliberationLLM(), "P2"))
    mission = _post(client)
    assert mission["status"] == "candidate"
    results = {
        e["actor"]: e["payload"]
        for e in _journal(client, mission["id"])
        if e["step"] == "auto_qualification" and e["entry_type"] == "result"
    }
    assert results["E1"]["relations_missing"] is False
    assert results["E3"]["relations_missing"] is False
    assert results["E2"]["relations_missing"] is True
    assert results["E2"]["relations"] == []
    assert results["E2"]["grouped_call_of"] == ["E1", "E2", "E3"]
    carto = mission["cartography"]
    assert carto["relations_missing_labels"] == ["P2"]
    assert carto["self_qualification_coverage"] == "2/3"
    assert carto["divergence_index_partial"] is True
    assert mission["recommendation"]["status"] == "produced"


# =================================================================================================
# I — Distinctivité de la composition (§7) : les angles redondants cèdent avant les angles uniques.
# =================================================================================================
def test_i_redundant_angles_are_removed_before_unique_ones_when_the_budget_reduces_width(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    # 9 angles proposés sur 3 dimensions critiques ; « praticien » est porté par les trois
    # cellules. Classe importante (30 appels) : 7 experts finançables → 2 retraits, qui sont les
    # deux doublons (jamais un angle unique, jamais une dimension).
    framing = framing_with(
        [
            ("dimension v136 un", "high", ["praticien", "mesure", "sceptique"]),
            ("dimension v136 deux", "high", ["praticien", "utilisateur", "théoricien"]),
            ("dimension v136 trois", "high", ["praticien", "conformité", "intégration"]),
        ]
    )
    use_llm(DeliberationLLM(framing=framing))
    mission = _post(client)
    bounds = mission["composition"]["bounds"]
    assert bounds["experts_proposed"] == 9
    assert bounds["max_experts_feasible_deliberation"] == 7
    assert bounds["experts_retained"] == 7
    removed = bounds["duplicate_angles_removed"]
    assert len(removed) == 2
    assert len({r["angle"] for r in removed}) == 1  # le même angle redondant, deux fois
    assert len({r["dimension"] for r in removed}) == 2  # dans deux cellules différentes
    experts = mission["composition"]["experts"]
    assert len(experts) == 7
    titles = [e["angle_title"] for e in experts]
    assert len(set(titles)) == 7  # aucun angle porté deux fois après réduction
    assert removed[0]["angle"] in titles  # une occurrence de l'angle redondant est conservée
    assert {e["dimension"] for e in experts} == {
        "dimension v136 un",
        "dimension v136 deux",
        "dimension v136 trois",
    }
    assert mission["composition"]["uncovered_dimensions"] == []
    composition = _entries(client, mission["id"], "composition_result")[0]["payload"]
    reductions = [e for e in composition["journal"] if e["event"] == "reduction_budget"]
    assert len(reductions) == 2
    assert all("angle redondant" in e["detail"] for e in reductions)
    assert [e["removed_angle"] for e in reductions] == [r["angle"] for r in removed]
    assert mission["status"] == "candidate"
    assert mission["llm_calls_used"] <= 30


def test_i_without_budget_pressure_redundant_angles_are_kept(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    framing = framing_with(
        [
            ("dimension v136 un", "high", ["praticien", "mesure"]),
            ("dimension v136 deux", "high", ["praticien", "utilisateur"]),
        ]
    )
    use_llm(DeliberationLLM(framing=framing))
    mission = _post(client, declared_class="structurante")
    bounds = mission["composition"]["bounds"]
    assert bounds["duplicate_angles_removed"] == []
    assert bounds["experts_retained"] == bounds["experts_proposed"]
    titles = [e["angle_title"] for e in mission["composition"]["experts"]]
    assert len(titles) > len(set(titles))  # le doublon est conservé sans pression budgétaire
    composition = _entries(client, mission["id"], "composition_result")[0]["payload"]
    assert not [e for e in composition["journal"] if e["event"] == "reduction_budget"]


# =================================================================================================
# J — Recherche : interne vs externe (§9). Aucun appel web pour une donnée interne.
# =================================================================================================
EXTERNAL_Q = "Quel est le tarif public de l'offre synthétique Z ?"
INTERNAL_Q = "Quelle est notre marge actuelle sur ce périmètre ?"


def fact_confrontation(
    *, external: bool = True, internal: bool = True, declared: dict[str, str] | None = None
) -> dict[str, dict[str, Any]]:
    acts: list[dict[str, Any]] = []
    if external:
        acts.append(act("P2", "critique", "fact", "le tarif diverge", fact_question=EXTERNAL_Q))
    if internal:
        acts.append(act("P3", "critique", "fact", "la marge diverge", fact_question=INTERNAL_Q))
    for a in acts:
        if declared and a["fact_question"] in declared:
            a["fact_source"] = declared[a["fact_question"]]
    return {"P1": {"acts": acts}}


def test_j_classification_is_declared_first_then_lexical_and_never_guessed_further() -> None:
    assert classify_fact_source(INTERNAL_Q) == "internal"
    assert classify_fact_source(EXTERNAL_Q) == "either"
    assert classify_fact_source(EXTERNAL_Q, declared="internal") == "internal"
    assert classify_fact_source(INTERNAL_Q, declared="external") == "external"
    assert classify_fact_source("Combien de contrats avons-nous signés en interne ?") == "internal"


def test_j_internal_question_is_an_information_request_external_one_is_researched(
    client: TestClient, use_llm: Callable[..., Any], research: Callable[[Any], Any]
) -> None:
    provider = research(FakeResearchProvider("found"))
    llm = use_llm(DeliberationLLM(confrontation=fact_confrontation()))
    mission = _post(client)
    items = {e["question"]: e for e in mission["deliberation"]["research"]}
    assert set(items) == {EXTERNAL_Q, INTERNAL_Q}
    internal = items[INTERNAL_Q]
    assert internal["status"] == "internal_data_required"
    assert internal["fact_source"] == "internal"
    assert internal["provenance"] == "internal_request"
    assert internal["provider"] == "none"
    assert internal["source"] == ""
    assert internal["requires_internal_data"] is True
    external = items[EXTERNAL_Q]
    assert external["status"] == "found"
    assert external["fact_source"] == "either"
    assert external["provenance"] == "external"
    # Le fournisseur n'a jamais été interrogé sur la donnée interne ; un seul appel de recherche.
    assert provider.questions == [EXTERNAL_Q]
    assert len([c for c in llm.calls if c["call_type"] == "research"]) == 0  # fournisseur factice
    assert mission["deliberation"]["stop"]["reason"] == "missing_internal_info"
    synthesis_prompt = next(c for c in llm.calls if c["call_type"] == "synthesis")["prompt"]
    assert "Informations INTERNES à demander" in synthesis_prompt
    assert INTERNAL_Q in synthesis_prompt
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "Informations à demander au demandeur (1)" in md
    assert INTERNAL_Q in md


def test_j_without_provider_external_is_unavailable_external_and_internal_stays_internal(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    llm = use_llm(DeliberationLLM(confrontation=fact_confrontation()))
    mission = _post(client)
    items = {e["question"]: e for e in mission["deliberation"]["research"]}
    assert items[EXTERNAL_Q]["status"] == "unavailable_external"
    assert items[EXTERNAL_Q]["provenance"] == "unavailable"
    assert items[INTERNAL_Q]["status"] == "internal_data_required"
    assert not [c for c in llm.calls if c["call_type"] == "research"]
    # L'absence externe prime dans la raison d'arrêt ; les deux restent visibles dans la synthèse.
    assert mission["deliberation"]["stop"]["reason"] == "missing_external_info"
    synthesis_prompt = next(c for c in llm.calls if c["call_type"] == "synthesis")["prompt"]
    assert "EXTERNES NON résolues" in synthesis_prompt
    assert "Informations INTERNES à demander" in synthesis_prompt
    note = mission["report"]["fourteen_fields"]["06_preuves"]["note"]
    assert "1 question(s) factuelle(s) externe(s) non résolue(s)" in note
    assert "1 information(s) interne(s) à demander au demandeur" in note


def test_j_declared_fact_source_overrides_the_lexical_fallback(
    client: TestClient, use_llm: Callable[..., Any], research: Callable[[Any], Any]
) -> None:
    provider = research(FakeResearchProvider("found"))
    use_llm(
        DeliberationLLM(
            confrontation=fact_confrontation(
                declared={EXTERNAL_Q: "internal", INTERNAL_Q: "external"}
            )
        )
    )
    mission = _post(client)
    items = {e["question"]: e for e in mission["deliberation"]["research"]}
    assert items[EXTERNAL_Q]["status"] == "internal_data_required"
    assert items[INTERNAL_Q]["status"] == "found"
    assert items[INTERNAL_Q]["fact_source"] == "external"
    assert provider.questions == [INTERNAL_Q]


# =================================================================================================
# K — Non-régression : plafonds, types d'appel couverts par la politique, promesses inchangées.
# =================================================================================================
def test_k_every_call_type_of_a_full_mission_has_an_explicit_policy(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    llm = use_llm(
        DeliberationLLM(
            framing=PROPOSAL_FRAMING,
            relation="variant",  # greffier sollicité
            confrontation={"P1": {"acts": [act("P2", "critique", "solution", "objection à P2")]}},
        )
    )
    mission = _post(client, declared_class="structurante")
    assert mission["status"] == "candidate"
    observed = {c["call_type"] for c in llm.calls}
    assert observed <= set(CALL_TYPE_CATEGORY)
    assert {"clerk", "steelman_challenge", "revision"} <= observed
    planned = _entries(client, mission["id"], "call_planned")
    assert all("reasoning_policy" in e["payload"] for e in planned)
    assert (mission["max_llm_calls"], mission["max_cost_eur"]) == (60, 8.0)
