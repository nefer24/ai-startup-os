"""OT-V1, incrément 2 — micro-correctif v1.3.6.1 : D18 (plancher du SDK fournisseur) et D19
(planification de l'auto-qualification cohérente avec la marge de raisonnement).

Aucun réseau ; fixtures synthétiques ; réutilisation des faux clients de `test_missions_v136`.
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from app.config import Settings, get_settings
from app.llm import AnthropicLLMClient
from app.mission_budget import (
    feasible_expert_count,
    minimal_deliberation_bound,
    self_qualification_plan,
    self_qualification_required_tokens,
)
from app.output_budget import output_budget
from app.reasoning_policy import reasoning_policy_for
from fastapi.testclient import TestClient

from tests.test_missions_deliberation import DeliberationLLM, act, competent_clerk
from tests.test_missions_output_budget import options_for
from tests.test_missions_v136 import (
    FakeAnthropic,
    _Block,
    _entries,
    _post,
    mission9_shape_framing,
    single_angle_framing,
)

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"
REQUIRED_SDK_FLOOR = (0, 78, 0)  # effort : 0.75.0 ; adaptive thinking : 0.78.0
_CURRENT: dict[str, Any] = {}


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
def fake_anthropic(monkeypatch: pytest.MonkeyPatch) -> type[FakeAnthropic]:
    import anthropic

    FakeAnthropic.recorded = []
    FakeAnthropic.script = None
    monkeypatch.setattr(anthropic, "Anthropic", FakeAnthropic)
    return FakeAnthropic


# =================================================================================================
# D18 — le plancher déclaré du SDK garantit les capacités réellement utilisées par l'adapter.
# =================================================================================================
def _declared_anthropic_floor() -> tuple[int, ...]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    deps = [d for d in data["project"]["dependencies"] if re.match(r"^anthropic\b", d)]
    assert len(deps) == 1, deps
    m = re.search(r">=\s*(\d+(?:\.\d+)*)", deps[0])
    assert m, f"borne minimale absente : {deps[0]!r}"
    parts = tuple(int(p) for p in m.group(1).split("."))
    return parts + (0,) * (3 - len(parts))


def test_d18_declared_sdk_floor_covers_adaptive_thinking_and_effort() -> None:
    assert _declared_anthropic_floor() >= REQUIRED_SDK_FLOOR


def test_d18_no_exact_pin_and_no_unjustified_upper_bound() -> None:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    dep = next(d for d in data["project"]["dependencies"] if d.startswith("anthropic"))
    assert "==" not in dep
    assert "<" not in dep


def test_d18_adapter_still_sends_thinking_and_effort_and_complete_is_untouched(
    fake_anthropic: type[FakeAnthropic],
) -> None:
    fake_anthropic.script = lambda kwargs: ([_Block("text", text='{"ok": true}')], "end_turn", 12)
    settings = Settings.model_construct()
    client = AnthropicLLMClient(
        "k",
        "modele-synthetique",
        8000,
        reasoning_policy=lambda ct: reasoning_policy_for(ct, settings),
    )
    response = client.complete_structured(
        system="s", prompt="p", call_type="self_qualification", max_tokens=2000
    )
    sent = fake_anthropic.recorded[-1]
    assert sent["thinking"] == {"type": "adaptive"}
    assert sent["output_config"] == {"effort": "low"}
    assert response.text == '{"ok": true}'
    # Chemin historique `complete()` : texte concaténé, aucun paramètre de raisonnement.
    assert client.complete("bonjour") == '{"ok": true}'
    legacy = fake_anthropic.recorded[-1]
    assert "thinking" not in legacy
    assert "output_config" not in legacy
    assert "system" not in legacy
    assert legacy["max_tokens"] == 8000


# =================================================================================================
# D19 — la taille de groupe respecte le plafond marge de raisonnement comprise.
# =================================================================================================
def test_d19_frontier_n17_with_headroom_500_does_not_choose_g3() -> None:
    plan = self_qualification_plan(17, group_max=3, output_ceiling=6000, reasoning_headroom=500)
    assert self_qualification_required_tokens(17, 3) == 5856  # 5856 + 500 > 6000
    assert plan["group_size"] == 2
    assert plan["calls"] == 9
    assert plan["required_tokens"] + plan["reasoning_headroom"] <= 6000
    assert plan["fits"] is True
    # Le budget réellement accordé pour ce groupe tient sous le plafond sans être écrêté.
    granted = output_budget(
        "self_qualification", 2 * 16, floor=1500, ceiling=6000, reasoning_headroom=500
    )
    assert granted.capped_by_ceiling is False
    assert granted.granted == plan["required_tokens"] + 500


def test_d19_frontier_n17_with_thinking_c_disabled_can_choose_g3() -> None:
    settings = Settings.model_construct(mission_reasoning_thinking_c="disabled")
    headroom = reasoning_policy_for("self_qualification", settings).headroom_tokens
    assert headroom == 0
    plan = self_qualification_plan(
        17, group_max=3, output_ceiling=6000, reasoning_headroom=headroom
    )
    assert plan["group_size"] == 3
    assert plan["calls"] == 6
    assert plan["required_tokens"] == 5856 <= 6000


@pytest.mark.parametrize("ceiling", [4000, 6000, 8000])
@pytest.mark.parametrize("headroom", [0, 250, 500, 1000])
@pytest.mark.parametrize("group_max", [1, 2, 3, 4])
def test_d19_invariant_group_size_respects_ceiling_with_headroom(
    ceiling: int, headroom: int, group_max: int
) -> None:
    for n in range(2, 41):
        plan = self_qualification_plan(
            n, group_max=group_max, output_ceiling=ceiling, reasoning_headroom=headroom
        )
        g = plan["group_size"]
        assert 1 <= g <= group_max
        assert plan["calls"] == -(-n // g)
        required = self_qualification_required_tokens(n, g)
        assert plan["required_tokens"] == required
        if plan["fits"]:
            assert required + headroom <= ceiling
            # Le groupe est le plus grand admissible : g + 1 ne tiendrait pas (ou dépasse la borne).
            if g < group_max:
                assert self_qualification_required_tokens(n, g + 1) + headroom > ceiling
            # Cohérence avec le budget de sortie réellement appliqué : jamais écrêté.
            budget = output_budget(
                "self_qualification",
                g * (n - 1),
                floor=1500,
                ceiling=ceiling,
                reasoning_headroom=headroom,
            )
            assert budget.capped_by_ceiling is False
        else:
            # État explicite : même g = 1 ne tient pas ; rien n'est réduit en silence.
            assert g == 1
            assert self_qualification_required_tokens(n, 1) + headroom > ceiling
            assert plan["reasoning_headroom"] == headroom


def test_d19_unrepresentable_width_is_not_engaged_by_the_composition_bound() -> None:
    # Plafond volontairement bas : à partir d'une certaine largeur, même une position par appel
    # ne tient plus ; la borne le déclare et `feasible_expert_count` n'engage pas cette largeur.
    kwargs: dict[str, Any] = {
        "effective_class": "structurante",
        "options_per_expert": 5,
        "batch_size": 16,
        "meta_chunk_size": 32,
        "revision_cap": 8,
        "self_qualification_group_max": 3,
        "self_qualification_ceiling": 1500,
        "self_qualification_headroom": 500,
    }
    fits = [
        n
        for n in range(2, 30)
        if minimal_deliberation_bound(n, **kwargs)["self_qualification_fits"]
    ]
    assert fits
    assert fits == list(range(2, fits[-1] + 1))
    widest = fits[-1]
    assert not minimal_deliberation_bound(widest + 1, **kwargs)["self_qualification_fits"]
    assert feasible_expert_count(1000, **kwargs) == widest


def test_d19_plan_matches_the_effective_policy_headroom_in_the_mission(
    client: TestClient, use_llm: Callable[..., Any], settings_env: Callable[[str, str], None]
) -> None:
    # 17 positions réelles (17 dimensions basses à un angle, classe critique) : avec la marge C de
    # 500, le plan choisit g = 2 (9 appels) ; raisonnement C désactivé → g = 3 (6 appels). Dans
    # les deux cas, aucune auto-qualification n'est écrêtée par le plafond.
    llm = use_llm(DeliberationLLM(framing=single_angle_framing(17, "low")))
    mission = _post(client, declared_class="critique")
    assert len(mission["composition"]["experts"]) == 17
    plan = _entries(client, mission["id"], "plan")[0]["payload"]
    assert (plan["group_size"], plan["calls"], plan["reasoning_headroom"]) == (2, 9, 500)
    planned = [
        e
        for e in _entries(client, mission["id"], "call_planned")
        if e["payload"]["call_type"] == "self_qualification"
    ]
    assert len(planned) == 9
    assert all(p["payload"]["output_budget"]["capped_by_ceiling"] is False for p in planned)
    assert all(p["payload"]["max_tokens"] <= 6000 for p in planned)
    assert len([c for c in llm.calls if c["call_type"] == "self_qualification"]) == 9
    settings_env("MISSION_REASONING_THINKING_C", "disabled")
    get_settings.cache_clear()
    llm = use_llm(DeliberationLLM(framing=single_angle_framing(17, "low")))
    mission = _post(client, declared_class="critique")
    plan = _entries(client, mission["id"], "plan")[0]["payload"]
    assert (plan["group_size"], plan["calls"], plan["reasoning_headroom"]) == (3, 6, 0)
    planned = [
        e
        for e in _entries(client, mission["id"], "call_planned")
        if e["payload"]["call_type"] == "self_qualification"
    ]
    assert len(planned) == 6
    assert all(p["payload"]["output_budget"]["capped_by_ceiling"] is False for p in planned)
    assert all(p["payload"]["output_budget"]["reasoning_headroom"] == 0 for p in planned)


def test_d19_regression_structurante_synthetic_case_still_reaches_the_gate_under_60_calls(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    framing = mission9_shape_framing()
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
    assert bounds["self_qualification_fits"] is True
    assert bounds["self_qualification_group_size"] == 3  # 15 positions : 5 496 + 500 ≤ 6 000
    # v1.3.6.2 (D21) : 15 experts (15 + 5 + 15 + 2 + 8 + 12 = 57 ≤ 59).
    assert bounds["total_required_calls"] == 57 <= bounds["remaining_calls_at_composition"]
    assert len(mission["composition"]["experts"]) == 15
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
    assert mission["deliberation"]["steelman"]["status"] in {"accepted", "accepted_partial"}
    assert [r for r in mission["deliberation"]["revisions"] if r["called"]]
    assert mission["recommendation"]["gate"]["passed"] is True
    assert [c["call_type"] for c in llm.calls].count("self_qualification") == 5
    entries = _entries(client, mission["id"], "skipped_for_deliberation_reserve")
    assert entries == []
