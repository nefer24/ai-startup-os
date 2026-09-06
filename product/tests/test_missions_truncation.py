"""OT-V1, incrément 1 — classe de panne « sortie structurée tronquée / JSON invalide ».

Reproduit techniquement l'échec observé en évaluation : le fournisseur coupe la sortie à
`max_tokens` (`stop_reason == "max_tokens"`), le JSON se termine en plein champ texte
(« Unterminated string »), et le cadrage échoue. Vérifie que le système :

* distingue `truncated_output` (limite de sortie atteinte) de `json_invalid` (format réellement
  invalide) ;
* n'enchaîne pas sur un cadrage fictif : la mission est `failed`, le rapport partiel, la réponse
  brute conservée ;
* respecte toujours les plafonds de mission (12 appels, 2,00 €) avec les nouvelles marges de sortie.

Fixtures purement synthétiques ; aucun cas réel, aucun banc d'essai.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest
from app.config import Settings
from app.llm import LLMClient, LLMResponse, LLMUsage
from app.mission_budget import BudgetLedger
from app.mission_exploration import EXPERT_SYSTEM
from app.mission_framing import FRAMING_SYSTEM
from app.mission_schemas import FramingOutput, parse_structured
from fastapi.testclient import TestClient

FRAMING_OK: dict[str, Any] = {
    "problem_understood": "cas synthétique T : texte long pour éprouver la troncature " * 8,
    "assumed_objective": "objectif synthétique T",
    "constraints": ["contrainte C1"],
    "assumptions": ["hypothèse H1"],
    "global_unknowns": ["inconnue U1", "inconnue U2", "inconnue U3"],
    "dimensions": [
        {
            "name": "dimension alpha",
            "why": "dimension synthétique",
            "presumed_criticality": "medium",
            "unknowns": ["inconnue U-alpha"],
            "suggested_angles": ["praticien"],
        }
    ],
    "contestation": {"status": "none", "target": "", "argument": ""},
    "escalation_signals": [],
    "suggested_class": "",
}

EXPERT_OK: dict[str, Any] = {
    "position": "position synthétique",
    "reasoning": "raisonnement synthétique",
    "assumptions": ["hypothèse E"],
    "risks": ["risque E"],
    "unknowns": ["inconnue E"],
    "to_verify": ["à vérifier E"],
    "options": [{"label": "option E", "summary": "…", "kind": "test"}],
    "objections": [],
    "evidence": [],
}


def truncate_in_string(payload: dict[str, Any], keep_ratio: float = 0.6) -> str:
    """Coupe un JSON sérialisé en plein champ texte, comme le ferait une limite de sortie."""
    text = json.dumps(payload, ensure_ascii=False)
    cut = int(len(text) * keep_ratio)
    # S'assurer que la coupe tombe à l'intérieur d'une chaîne (nombre impair de guillemets avant).
    while text[:cut].count('"') % 2 == 0 and cut < len(text) - 1:
        cut += 1
    return text[:cut]


class FailureModeLLM:
    """Faux client structuré : mode de panne configurable par type d'appel."""

    def __init__(
        self,
        *,
        framing_mode: str = "ok",
        expert_mode: str = "ok",
        max_tokens_hit: int | None = None,
    ) -> None:
        self.framing_mode = framing_mode
        self.expert_mode = expert_mode
        self.max_tokens_hit = max_tokens_hit
        self.calls: list[dict[str, Any]] = []

    def complete(self, prompt: str) -> str:
        raise AssertionError("chemin historique non utilisé")

    def _respond(self, mode: str, payload: dict[str, Any], max_tokens: int) -> LLMResponse:
        if mode == "truncated":
            return LLMResponse(
                text=truncate_in_string(payload),
                usage=LLMUsage(input_tokens=1200, output_tokens=max_tokens),
                stop_reason="max_tokens",
            )
        if mode == "invalid":
            # JSON complet mais syntaxiquement faux (virgule finale), arrêt normal du modèle.
            text = json.dumps(payload, ensure_ascii=False)[:-1] + ",}"
            return LLMResponse(
                text=text,
                usage=LLMUsage(input_tokens=1200, output_tokens=300),
                stop_reason="end_turn",
            )
        return LLMResponse(
            text=json.dumps(payload, ensure_ascii=False),
            usage=LLMUsage(input_tokens=1200, output_tokens=400),
            stop_reason="end_turn",
        )

    def complete_structured(
        self, *, system: str, prompt: str, call_type: str, max_tokens: int
    ) -> LLMResponse:
        self.calls.append({"call_type": call_type, "max_tokens": max_tokens})
        if call_type == "framing":
            return self._respond(self.framing_mode, FRAMING_OK, max_tokens)
        if call_type == "expert_tour0":
            return self._respond(self.expert_mode, EXPERT_OK, max_tokens)
        if call_type == "self_qualification":
            return self._respond("ok", {"relations": []}, max_tokens)
        return self._respond("ok", {"groups": [], "disagreements": []}, max_tokens)


_CURRENT: dict[str, FailureModeLLM] = {}


@pytest.fixture
def llm_factory() -> Callable[[], LLMClient]:
    def factory() -> LLMClient:
        return _CURRENT["llm"]

    return factory


@pytest.fixture
def use_llm() -> Callable[[FailureModeLLM], FailureModeLLM]:
    def _set(llm: FailureModeLLM) -> FailureModeLLM:
        _CURRENT["llm"] = llm
        return llm

    _CURRENT["llm"] = FailureModeLLM()
    return _set


def _post(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/missions", json={"input_type": "problem", "input_text": "entrée synthétique T"}
    )
    assert response.status_code == 201, response.text
    return response.json()


# --- Classification : tronqué vs invalide vs complet -----------------------------------------
def test_truncated_json_is_reported_as_unterminated_string() -> None:
    text = truncate_in_string(FRAMING_OK)
    parsed, error = parse_structured(text, FramingOutput)
    assert parsed is None
    assert "Unterminated string" in error


def test_framing_truncated_at_max_tokens_fails_mission_honestly(
    client: TestClient, use_llm: Callable[..., FailureModeLLM]
) -> None:
    llm = use_llm(FailureModeLLM(framing_mode="truncated"))
    mission = _post(client)
    assert mission["status"] == "failed"
    assert mission["stop_reason"] == "framing_failed:truncated_output"
    assert mission["report"]["partial"] is True
    assert mission["report"]["status"] == "failed"
    assert mission["report"]["framing_error"].startswith("truncated_output")
    assert "Unterminated string" in mission["report"]["framing_error"]
    # Aucun expert n'est consulté sur un cadrage fictif ; le budget n'est pas dépensé pour rien.
    assert [c["call_type"] for c in llm.calls] == ["framing"]
    assert mission["llm_calls_used"] == 1
    # La réponse brute, la raison d'arrêt et les tokens sont conservés pour prouver la cause.
    framing = mission["framing"]
    assert framing["stop_reason"] == "max_tokens"
    assert framing["output_tokens"] == framing["max_tokens"] == 8000
    assert framing["raw"]
    assert framing["parsed"] is None
    journal = client.get(f"/missions/{mission['id']}/journal").json()
    failed = next(e for e in journal if e["entry_type"] == "framing_failed")
    assert failed["payload"]["kind"] == "truncated_output"
    done = next(e for e in journal if e["entry_type"] == "call_done")
    assert done["payload"]["truncated"] is True
    assert done["payload"]["stop_reason"] == "max_tokens"
    # Une mission `failed` n'accepte aucune action CEO.
    assert client.post(f"/missions/{mission['id']}/approve").status_code == 409


def test_framing_invalid_json_without_truncation_is_classified_json_invalid(
    client: TestClient, use_llm: Callable[..., FailureModeLLM]
) -> None:
    use_llm(FailureModeLLM(framing_mode="invalid"))
    mission = _post(client)
    assert mission["status"] == "failed"
    assert mission["stop_reason"] == "framing_failed:json_invalid"
    assert mission["report"]["framing_error"].startswith("json_invalide")
    assert "truncated" not in mission["report"]["framing_error"]
    assert mission["framing"]["stop_reason"] == "end_turn"


def test_complete_json_keeps_normal_behaviour(
    client: TestClient, use_llm: Callable[..., FailureModeLLM]
) -> None:
    llm = use_llm(FailureModeLLM())
    mission = _post(client)
    assert mission["status"] == "candidate"
    assert mission["stop_reason"] == ""
    assert mission["report"]["partial"] is False
    assert mission["report"]["framing_error"] == ""
    assert mission["report"]["epistemic"]["unknown"]["total"] >= 3
    assert {c["call_type"] for c in llm.calls} >= {"framing", "expert_tour0"}
    journal = client.get(f"/missions/{mission['id']}/journal").json()
    assert all(
        e["payload"]["truncated"] is False for e in journal if e["entry_type"] == "call_done"
    )


def test_expert_truncation_is_labelled_and_mission_continues(
    client: TestClient, use_llm: Callable[..., FailureModeLLM]
) -> None:
    use_llm(FailureModeLLM(expert_mode="truncated"))
    mission = _post(client)
    assert mission["status"] == "candidate"  # le cadrage est valide ; seuls les exposés ont échoué
    positions = mission["cartography"]["positions"]
    assert positions
    assert all(p["parse_error"].startswith("truncated_output") for p in positions)
    assert mission["cartography"]["experts_answered"] == 0
    assert mission["report"]["alternatives"] == []


# --- Marges de sortie et budget --------------------------------------------------------------
def test_output_limits_leave_margin_and_budget_defaults_unchanged() -> None:
    settings = Settings.model_construct()
    assert settings.mission_max_llm_calls == 12
    assert settings.mission_max_cost_eur == 2.0
    assert settings.mission_max_tokens_framing >= 8000
    assert settings.mission_max_tokens_expert >= 6000


def test_worst_case_upper_bounds_fit_in_two_euros() -> None:
    """Même avec les marges de sortie élargies, une mission complète tient sous le plafond CEO."""
    settings = Settings.model_construct()
    ledger = BudgetLedger(
        max_calls=settings.mission_max_llm_calls,
        max_cost_eur=settings.mission_max_cost_eur,
        price_in_per_mtok=settings.llm_price_input_eur_per_mtok,
        price_out_per_mtok=settings.llm_price_output_eur_per_mtok,
    )
    long_prompt = "x" * 12_000  # entrée + dossier généreux (≈ 4 000 tokens estimés)
    plan = (
        [(FRAMING_SYSTEM, settings.mission_max_tokens_framing)]
        + [(EXPERT_SYSTEM, settings.mission_max_tokens_expert)] * 5
        + [("s", settings.mission_max_tokens_self_qualification)] * 5
        + [("c", settings.mission_max_tokens_clerk)]
    )
    assert len(plan) == 12
    total_upper_bound = sum(
        ledger.estimate_call_cost_eur(system, long_prompt, max_tokens)
        for system, max_tokens in plan
    )
    assert total_upper_bound < settings.mission_max_cost_eur
    # Et l'estimation avant appel reste bloquante : un 13e appel est refusé.
    for system, max_tokens in plan:
        ledger.check_before_call(
            system=system, prompt=long_prompt, max_tokens=max_tokens, call_type="t"
        )
        ledger.record(LLMUsage(input_tokens=4000, output_tokens=max_tokens // 2))
    assert ledger.remaining_calls == 0
    assert ledger.cost_eur <= settings.mission_max_cost_eur


def test_format_instruction_is_the_only_prompt_change() -> None:
    """La consigne ajoutée est purement de format ; le contenu intellectuel est inchangé."""
    for system in (FRAMING_SYSTEM, EXPERT_SYSTEM):
        assert "en JSON compact" in system
        assert "sans indentation" in system
    # Les règles intellectuelles restent présentes telles quelles.
    assert "Fais émerger les DIMENSIONS pertinentes" in FRAMING_SYSTEM
    assert "Ne conteste jamais par principe" in FRAMING_SYSTEM
    assert "N'invente JAMAIS une citation" in EXPERT_SYSTEM
