"""OT-V1, incrément 2 — récupération bornée des sorties structurées invalides (B13).

Aucun appel réel. Un faux client scripté est enveloppé dans un client « déformant » qui altère la
forme (jamais le fond) des réponses selon un plan par type d'appel : code fence, texte enveloppant,
JSON cassé, champ obligatoire absent, type incorrect, troncature, plusieurs objets, réponse vide.
Les fixtures sont purement synthétiques ; aucun contenu de holdout.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest
from app.llm import LLMClient, LLMResponse, LLMUsage
from app.mission_schemas import FramingOutput
from app.structured_output import (
    STRUCTURED_OUTPUT_EMPTY,
    STRUCTURED_OUTPUT_PARSE_ERROR,
    STRUCTURED_OUTPUT_RECOVERY_EXHAUSTED,
    STRUCTURED_OUTPUT_RETRY_REFUSED_BUDGET,
    STRUCTURED_OUTPUT_SCHEMA_ERROR,
    STRUCTURED_OUTPUT_TRUNCATED,
    analyze_structured_output,
    recover_json_envelope,
)
from fastapi.testclient import TestClient
from ui.mission_state import mission_state_summary

from tests.test_missions_cost_exposure import ambiguous_timeout
from tests.test_missions_otv1 import MULTI_FRAMING, SIMPLE_FRAMING, ScriptedStructuredLLM
from tests.test_missions_resilience import overloaded
from tests.test_missions_truncation import truncate_in_string

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


def _shape(kind: str, text: str, max_tokens: int) -> tuple[str, str, int]:
    """(texte déformé, stop_reason, tokens de sortie) — la forme change, jamais le fond."""
    if kind == "fence":
        return f"```json\n{text}\n```", "end_turn", 500
    if kind == "envelope":
        return f"Voici le cadrage demandé :\n{text}\nJ'espère que cela convient.", "end_turn", 500
    if kind == "broken":
        return text[:-1] + ",}", "end_turn", 500
    if kind == "schema_missing":
        data = json.loads(text)
        data.pop("problem_understood", None)
        return json.dumps(data, ensure_ascii=False), "end_turn", 500
    if kind == "schema_type":
        data = json.loads(text)
        data["problem_understood"] = 123
        return json.dumps(data, ensure_ascii=False), "end_turn", 500
    if kind == "list_root":
        return f"[{text}]", "end_turn", 500
    if kind == "truncated":
        return truncate_in_string(json.loads(text)), "max_tokens", max_tokens
    if kind == "multi":
        return f"{text}\n{text}", "end_turn", 900
    if kind == "empty":
        return "", "end_turn", 0
    return text, "end_turn", 500


class ShapedLLM:
    """Enveloppe un faux client : applique, par type d'appel, une déformation par occurrence."""

    def __init__(self, inner: ScriptedStructuredLLM, plan: dict[str, list[str]]) -> None:
        self.inner = inner
        self.plan = {k: list(v) for k, v in plan.items()}
        self.calls: list[dict[str, Any]] = []

    def complete(self, prompt: str) -> str:
        raise AssertionError("chemin historique non utilisé")

    def complete_structured(
        self, *, system: str, prompt: str, call_type: str, max_tokens: int
    ) -> LLMResponse:
        response = self.inner.complete_structured(
            system=system, prompt=prompt, call_type=call_type, max_tokens=max_tokens
        )
        pending = self.plan.get(call_type)
        kind = pending.pop(0) if pending else "ok"
        text, stop_reason, out_tokens = _shape(kind, response.text, max_tokens)
        self.calls.append({"call_type": call_type, "prompt": prompt, "shape": kind})
        return LLMResponse(
            text=text,
            usage=LLMUsage(input_tokens=1000, output_tokens=out_tokens),
            stop_reason=stop_reason,
        )


class FailOnNth:
    """Lève `exc` à la n-ième occurrence d'un type d'appel (une seule fois), sinon délègue."""

    def __init__(self, inner: Any, *, call_type: str, nth: int, exc: BaseException) -> None:
        self.inner = inner
        self.call_type = call_type
        self.nth = nth
        self.exc: BaseException | None = exc
        self.seen = 0
        self.calls: list[dict[str, Any]] = []

    def complete(self, prompt: str) -> str:
        raise AssertionError("chemin historique non utilisé")

    def complete_structured(
        self, *, system: str, prompt: str, call_type: str, max_tokens: int
    ) -> LLMResponse:
        self.calls.append({"call_type": call_type})
        if call_type == self.call_type:
            self.seen += 1
            if self.seen == self.nth and self.exc is not None:
                exc, self.exc = self.exc, None
                raise exc
        return self.inner.complete_structured(
            system=system, prompt=prompt, call_type=call_type, max_tokens=max_tokens
        )


def _post(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload = {"input_type": "problem", "input_text": "entrée synthétique sortie structurée"}
    payload.update(overrides)
    response = client.post("/missions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _journal(client: TestClient, mission_id: int) -> list[dict[str, Any]]:
    return list(client.get(f"/missions/{mission_id}/journal").json())


def _entries(client: TestClient, mission_id: int, entry_type: str) -> list[dict[str, Any]]:
    return [e for e in _journal(client, mission_id) if e["entry_type"] == entry_type]


def _baseline(client: TestClient, use_llm: Callable[..., Any]) -> dict[str, Any]:
    use_llm(ScriptedStructuredLLM(SIMPLE_FRAMING))
    return _post(client)


def _framing_estimate(client: TestClient, mission: dict[str, Any]) -> float:
    planned = next(
        e
        for e in _journal(client, mission["id"])
        if e["entry_type"] == "call_planned" and e["step"] == "cadrage"
    )
    return float(planned["payload"]["estimated_cost_eur_upper_bound"])


# --- Unité : récupération locale déterministe et taxonomie --------------------------------------
def test_local_recovery_restores_the_envelope_and_never_the_content() -> None:
    valid = json.dumps(SIMPLE_FRAMING, ensure_ascii=False)
    assert recover_json_envelope(valid).attempted is False
    fenced = recover_json_envelope(f"```json\n{valid}\n```")
    assert (fenced.applied, fenced.method, json.loads(fenced.text)) == (
        True,
        "code_fence",
        SIMPLE_FRAMING,
    )
    wrapped = recover_json_envelope(f"Réponse :\n{valid}\nFin.")
    assert (wrapped.applied, wrapped.method, json.loads(wrapped.text)) == (
        True,
        "envelope_strip",
        SIMPLE_FRAMING,
    )
    # Accolades à l'intérieur des chaînes : le scanner respecte les chaînes et les échappements.
    tricky = json.dumps({"problem_understood": 'a } b { "c" \\" }'}, ensure_ascii=False)
    assert json.loads(recover_json_envelope(f"x {tricky} y").text) == json.loads(tricky)
    # Plusieurs objets candidats : aucune sélection locale (ce serait inventer un choix).
    multi = recover_json_envelope(f"{valid}\n{valid}")
    assert (multi.attempted, multi.applied, multi.candidates, multi.ambiguous) == (
        True,
        False,
        2,
        True,
    )
    # Objet jamais refermé (troncature) : rien n'est complété.
    cut = recover_json_envelope(valid[: len(valid) // 2])
    assert (cut.applied, cut.candidates) == (False, 0)
    # Champ manquant : la récupération locale ne l'invente jamais (le schéma tranche ensuite).
    data = dict(SIMPLE_FRAMING)
    data.pop("problem_understood")
    outcome = analyze_structured_output(
        LLMResponse(text=json.dumps(data), usage=LLMUsage(1, 1), stop_reason="end_turn"),
        FramingOutput,
    )
    assert (outcome.parse_ok, outcome.schema_ok, outcome.category) == (
        True,
        False,
        STRUCTURED_OUTPUT_SCHEMA_ERROR,
    )
    assert "problem_understood" in outcome.error


def test_taxonomy_distinguishes_empty_truncated_parse_schema_and_unknown_truncation() -> None:
    def outcome(text: str, stop_reason: str) -> Any:
        return analyze_structured_output(
            LLMResponse(text=text, usage=LLMUsage(1, 10), stop_reason=stop_reason), FramingOutput
        )

    valid = json.dumps(SIMPLE_FRAMING, ensure_ascii=False)
    assert outcome("", "end_turn").category == STRUCTURED_OUTPUT_EMPTY
    assert outcome("   \n", "end_turn").category == STRUCTURED_OUTPUT_EMPTY
    cut = outcome(valid[:40], "max_tokens")
    assert (cut.category, cut.truncated) == (STRUCTURED_OUTPUT_TRUNCATED, True)
    same_cut_unknown = outcome(valid[:40], "")
    assert (same_cut_unknown.category, same_cut_unknown.truncated) == (
        STRUCTURED_OUTPUT_PARSE_ERROR,
        None,
    )
    assert same_cut_unknown.to_journal()["truncated"] == "unknown"
    assert outcome(valid[:-1] + ",}", "end_turn").category == STRUCTURED_OUTPUT_PARSE_ERROR
    root = outcome(f"[{valid}]", "end_turn")
    assert (root.parse_ok, root.category) == (True, STRUCTURED_OUTPUT_SCHEMA_ERROR)
    ok = outcome(valid, "end_turn")
    assert (ok.valid, ok.category, bool(ok.output.problem_understood)) == (True, "", True)
    # Une sortie coupée mais malgré tout valide est acceptée et signalée tronquée (métadonnée).
    still_valid = outcome(valid, "max_tokens")
    assert (still_valid.valid, still_valid.truncated) == (True, True)
    # La vue journal est sanitisée : extraits bornés, jamais la réponse complète.
    view = outcome("x" * 5000, "end_turn").to_journal()
    assert (len(view["raw_head"]), len(view["raw_tail"])) == (120, 120)
    assert view["raw_length_chars"] == 5000
    assert "raw" not in view


# --- TEST A — JSON valide du premier coup --------------------------------------------------------
def test_valid_json_changes_nothing(client: TestClient, use_llm: Callable[..., Any]) -> None:
    mission = _baseline(client, use_llm)
    assert mission["status"] == "candidate"
    budget = mission["report"]["budget"]
    assert budget["structured_output_failures"] == 0
    assert budget["structured_output_recoveries"] == 0
    assert budget["structured_output_retries"] == 0
    assert budget["structured_output_exhausted"] == 0
    assert budget["llm_calls_used"] == budget["logical_calls"] == budget["provider_attempts"]
    assert not [
        e for e in _journal(client, mission["id"]) if "structured_output" in e["entry_type"]
    ]


# --- TEST B / C — enveloppe récupérable localement : zéro appel supplémentaire --------------------
@pytest.mark.parametrize(
    ("shape", "method"), [("fence", "code_fence"), ("envelope", "envelope_strip")]
)
def test_envelope_is_recovered_locally_without_any_new_call(
    client: TestClient, use_llm: Callable[..., Any], shape: str, method: str
) -> None:
    baseline = _baseline(client, use_llm)
    llm = use_llm(ShapedLLM(ScriptedStructuredLLM(SIMPLE_FRAMING), {"framing": [shape]}))
    mission = _post(client)
    assert mission["status"] == "candidate"
    assert [c["shape"] for c in llm.calls if c["call_type"] == "framing"] == [shape]
    assert mission["llm_calls_used"] == baseline["llm_calls_used"]
    budget = mission["report"]["budget"]
    assert budget["structured_output_recoveries"] == 1
    assert budget["structured_output_retries"] == 0
    assert budget["structured_output_failures"] == 0
    recovered = _entries(client, mission["id"], "structured_output_recovered")
    assert len(recovered) == 1
    assert recovered[0]["payload"]["local_recovery_method"] == method
    assert recovered[0]["payload"]["valid_after_recovery"] is True
    # Validation stricte : le cadrage récupéré est exactement celui de la réponse valide.
    assert mission["framing"]["parsed"] == baseline["framing"]["parsed"]


# --- TEST D / E — invalide puis relance corrective valide -----------------------------------------
@pytest.mark.parametrize(
    ("shape", "category", "parse_ok"),
    [
        ("broken", STRUCTURED_OUTPUT_PARSE_ERROR, False),
        ("schema_missing", STRUCTURED_OUTPUT_SCHEMA_ERROR, True),
        ("schema_type", STRUCTURED_OUTPUT_SCHEMA_ERROR, True),
        ("list_root", STRUCTURED_OUTPUT_SCHEMA_ERROR, True),
        ("empty", STRUCTURED_OUTPUT_EMPTY, False),
    ],
)
def test_invalid_then_corrected_uses_exactly_one_targeted_retry(
    client: TestClient,
    use_llm: Callable[..., Any],
    shape: str,
    category: str,
    parse_ok: bool,
) -> None:
    baseline = _baseline(client, use_llm)
    llm = use_llm(ShapedLLM(ScriptedStructuredLLM(SIMPLE_FRAMING), {"framing": [shape, "ok"]}))
    mission = _post(client)
    assert mission["status"] == "candidate"
    framing_calls = [c for c in llm.calls if c["call_type"] == "framing"]
    assert [c["shape"] for c in framing_calls] == [shape, "ok"]
    # Un appel logique réel de plus, visible partout ; aucun compteur historique redéfini.
    budget = mission["report"]["budget"]
    assert mission["llm_calls_used"] == baseline["llm_calls_used"] + 1
    assert budget["logical_calls"] == budget["provider_attempts"] == mission["llm_calls_used"]
    assert budget["provider_retries"] == 0
    assert budget["structured_output_retries"] == 1
    assert budget["structured_output_failures"] == 1
    assert budget["structured_output_exhausted"] == 0
    invalid = _entries(client, mission["id"], "structured_output_invalid")
    assert len(invalid) == 1
    p = invalid[0]["payload"]
    assert p["category"] == category
    assert p["parse_ok"] is parse_ok
    assert p["schema_ok"] is False
    assert p["will_retry"] is True
    assert p["retry_refusal_reason"] == ""
    assert p["structured_attempt"] == 1
    assert p["max_structured_retries"] == 1
    assert p["logical_call_id"] == "LC-1"
    assert p["estimated_retry_cost_eur"] > 0
    assert set(p) >= {
        "provider",
        "model",
        "truncated",
        "local_recovery_attempted",
        "local_recovery_applied",
        "known_cost_eur",
        "uncertain_cost_upper_bound_eur",
        "max_cost_eur",
    }
    result = _entries(client, mission["id"], "structured_output_retry_result")
    assert len(result) == 1
    assert result[0]["payload"]["valid"] is True
    assert result[0]["payload"]["final"] == "accepted"
    assert result[0]["payload"]["logical_call_id"] == "LC-2"
    # La relance est ciblée sur le contrat : demande d'origine + bloc de correction explicite.
    retry_prompt = framing_calls[1]["prompt"]
    assert retry_prompt.startswith(framing_calls[0]["prompt"])
    assert "CORRECTION DE FORMAT" in retry_prompt
    assert "obligatoires : problem_understood" in retry_prompt
    assert "n'invente aucune donnée" in retry_prompt
    if category == STRUCTURED_OUTPUT_SCHEMA_ERROR and shape != "list_root":
        assert "problem_understood" in p["error"]
    # Résultat logique unique, validé strictement, identique au cadrage valide : rien d'inventé.
    assert mission["framing"]["parsed"] == baseline["framing"]["parsed"]
    assert mission["composition"]["experts"] == baseline["composition"]["experts"]


# --- TEST F — deux échecs : aucun troisième appel, échec explicite --------------------------------
def test_two_invalid_outputs_fail_closed_without_a_third_call(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    llm = use_llm(
        ShapedLLM(ScriptedStructuredLLM(SIMPLE_FRAMING), {"framing": ["broken", "broken"]})
    )
    mission = _post(client)
    assert mission["status"] == "failed"
    assert mission["stop_reason"] == STRUCTURED_OUTPUT_RECOVERY_EXHAUSTED
    assert [c["call_type"] for c in llm.calls] == ["framing", "framing"]
    assert mission["llm_calls_used"] == 2  # deux appels réels, aucun masqué
    failure = mission["failure"]
    assert failure["reason"] == STRUCTURED_OUTPUT_RECOVERY_EXHAUSTED
    assert failure["kind"] == "structured_output"
    assert failure["step"] == "cadrage"
    assert failure["category"] == STRUCTURED_OUTPUT_PARSE_ERROR
    assert failure["attempts"] == 2
    assert failure["max_attempts"] == 2
    assert failure["structured_output_retries"] == 1
    budget = mission["report"]["budget"]
    assert budget["structured_output_failures"] == 2
    assert budget["structured_output_exhausted"] == 1
    # Aucune production aval fictive.
    assert mission["framing"]["parsed"] is None
    assert mission["composition"] is None
    assert mission["recommendation"] is None
    assert mission["report"]["status"] == "failed"
    assert mission["report"]["partial"] is True
    assert mission["deliberation"]["stop"]["reason"] == "framing_failed"
    result = _entries(client, mission["id"], "structured_output_retry_result")[0]["payload"]
    assert result["valid"] is False
    assert result["final"] == STRUCTURED_OUTPUT_RECOVERY_EXHAUSTED
    assert _entries(client, mission["id"], "failed_structured_output")
    assert client.post(f"/missions/{mission['id']}/approve").status_code == 409
    # B11 : cause intelligible, jamais « mission non terminée ».
    summary = mission_state_summary(mission)
    assert summary["kind"] == "failed"
    text = " ".join(summary["details"])
    assert "récupération bornée" in text
    assert "non parsable" in text
    assert "Tentatives : 2 / 2" in text


# --- TEST G — budget insuffisant pour la relance : fail-closed, raison explicite ------------------
def test_retry_is_refused_when_calls_or_cost_cap_would_be_violated(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    # Plafond d'appels : un seul appel autorisé → la relance corrective n'est pas finançable.
    llm = use_llm(ShapedLLM(ScriptedStructuredLLM(SIMPLE_FRAMING), {"framing": ["broken", "ok"]}))
    mission = _post(client, max_llm_calls=1)
    assert mission["status"] == "failed"
    assert mission["stop_reason"] == STRUCTURED_OUTPUT_RETRY_REFUSED_BUDGET
    assert [c["call_type"] for c in llm.calls] == ["framing"]
    assert mission["llm_calls_used"] == 1
    assert mission["failure"]["reason"] == STRUCTURED_OUTPUT_RETRY_REFUSED_BUDGET
    assert mission["failure"]["attempts"] == 1
    p = _entries(client, mission["id"], "structured_output_invalid")[0]["payload"]
    assert p["will_retry"] is False
    assert p["retry_refusal_reason"] == STRUCTURED_OUTPUT_RETRY_REFUSED_BUDGET
    assert p["remaining_calls"] == 0
    assert mission["report"]["budget"]["structured_output_retries"] == 0
    assert mission["recommendation"] is None
    # Plafond financier : connu (1er appel) + estimation de la relance > plafond CEO.
    estimate = _framing_estimate(client, mission)
    llm2 = use_llm(ShapedLLM(ScriptedStructuredLLM(SIMPLE_FRAMING), {"framing": ["broken", "ok"]}))
    mission = _post(client, max_cost_eur=round(estimate + 0.005, 6))
    assert mission["status"] == "failed"
    assert mission["stop_reason"] == STRUCTURED_OUTPUT_RETRY_REFUSED_BUDGET
    assert [c["call_type"] for c in llm2.calls] == ["framing"]
    p = _entries(client, mission["id"], "structured_output_invalid")[0]["payload"]
    assert p["retry_refusal_reason"] == STRUCTURED_OUTPUT_RETRY_REFUSED_BUDGET
    assert p["remaining_calls"] > 0
    assert p["known_cost_eur"] + p["estimated_retry_cost_eur"] > p["max_cost_eur"]
    assert mission["cost_eur"] <= mission["max_cost_eur"]


# --- TEST H — troncature observable : catégorie distincte, aucune relance à l'identique ----------
def test_observable_truncation_is_labelled_and_never_retried_blindly(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    # B14-prime (F) : le cadrage a une limite fixe (plancher = plafond) ; une sortie coupée à
    # cette limite n'est pas relancée « en espérant » une compression : refus explicite, rien
    # n'est complété localement. (La relance après troncature avec limite recalculée est testée
    # sur les étapes à cardinalité variable dans `test_missions_output_budget.py`.)
    llm = use_llm(
        ShapedLLM(ScriptedStructuredLLM(SIMPLE_FRAMING), {"framing": ["truncated", "ok"]})
    )
    mission = _post(client)
    assert mission["status"] == "failed"
    assert mission["stop_reason"] == "structured_output_retry_refused_output_budget"
    p = _entries(client, mission["id"], "structured_output_invalid")[0]["payload"]
    assert p["category"] == STRUCTURED_OUTPUT_TRUNCATED
    assert p["truncated"] is True
    assert p["stop_reason"] == "max_tokens"
    assert p["output_tokens"] == p["max_tokens"]
    assert p["local_recovery_attempted"] is True
    assert p["local_recovery_applied"] is False
    assert p["json_candidates"] == 0
    assert p["will_retry"] is False
    assert p["retry_refusal_reason"] == "structured_output_retry_refused_output_budget"
    assert p["truncation_retry_plan"]["allowed"] is False
    assert [c["call_type"] for c in llm.calls if c["call_type"] == "framing"] == ["framing"]
    assert mission["report"]["budget"]["structured_output_retries"] == 0
    assert mission["framing"]["parsed"] is None


# --- TEST I — plusieurs objets JSON : aucune sélection locale ------------------------------------
def test_multiple_json_objects_are_never_selected_locally(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    baseline = _baseline(client, use_llm)
    use_llm(ShapedLLM(ScriptedStructuredLLM(SIMPLE_FRAMING), {"framing": ["multi", "ok"]}))
    mission = _post(client)
    assert mission["status"] == "candidate"
    p = _entries(client, mission["id"], "structured_output_invalid")[0]["payload"]
    assert p["category"] == STRUCTURED_OUTPUT_PARSE_ERROR
    assert p["ambiguous_candidates"] is True
    assert p["json_candidates"] == 2
    assert p["local_recovery_applied"] is False
    assert "aucune sélection locale" in p["error"]
    assert p["will_retry"] is True
    assert mission["report"]["budget"]["structured_output_retries"] == 1
    assert mission["framing"]["parsed"] == baseline["framing"]["parsed"]


# --- TEST J — idempotence : une seule écriture métier par étape logique ---------------------------
def test_retry_never_duplicates_business_results(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    llm = use_llm(
        ShapedLLM(
            ScriptedStructuredLLM(MULTI_FRAMING),
            {"framing": ["broken", "ok"], "expert_tour0": ["schema_missing_expert", "ok"]},
        )
    )
    # `schema_missing_expert` n'est pas une déformation connue : traité comme `ok` par `_shape` ;
    # on déforme plutôt le premier exposé en JSON cassé.
    llm.plan["expert_tour0"] = ["broken", "ok"]
    mission = _post(client)
    assert mission["status"] == "candidate"
    experts = [e["expert_id"] for e in mission["composition"]["experts"]]
    positions = [p["expert_id"] for p in mission["cartography"]["positions"]]
    assert positions == experts  # une position par expert, aucun doublon
    assert len(set(positions)) == len(positions)
    assert mission["cartography"]["experts_answered"] == len(experts)
    tour0_calls = [c for c in llm.calls if c["call_type"] == "expert_tour0"]
    assert len(tour0_calls) == len(experts) + 1
    assert len([c for c in llm.calls if c["call_type"] == "framing"]) == 2
    budget = mission["report"]["budget"]
    assert budget["structured_output_retries"] == 2
    assert budget["structured_output_exhausted"] == 0
    assert mission["framing"]["parsed"] is not None
    # Le journal conserve toutes les tentatives physiques.
    assert len(_entries(client, mission["id"], "structured_output_invalid")) == 2
    assert len(_entries(client, mission["id"], "structured_output_retry_result")) == 2
    assert len(_entries(client, mission["id"], "expert_result")) == len(experts)


# --- TEST K — B10 pendant la relance B13 : mécanismes distincts, bornes cumulées -----------------
def test_provider_error_during_structured_retry_is_handled_by_b10(
    client: TestClient, use_llm: Callable[..., Any], sleeps: list[float]
) -> None:
    shaped = ShapedLLM(ScriptedStructuredLLM(SIMPLE_FRAMING), {"framing": ["broken", "ok"]})
    llm = use_llm(FailOnNth(shaped, call_type="framing", nth=2, exc=overloaded()))
    mission = _post(client)
    assert mission["status"] == "candidate"
    # 3 tentatives physiques de cadrage : invalide, 529 (B10), valide ; 2 appels logiques.
    assert [c["call_type"] for c in llm.calls if c["call_type"] == "framing"] == ["framing"] * 3
    assert len(sleeps) == 1
    budget = mission["report"]["budget"]
    assert budget["structured_output_retries"] == 1
    assert budget["provider_retries"] == 1
    assert budget["provider_attempts"] == budget["logical_calls"] + 1
    assert mission["llm_calls_used"] == budget["logical_calls"]
    attempt_failed = _entries(client, mission["id"], "call_attempt_failed")
    assert len(attempt_failed) == 1
    assert attempt_failed[0]["payload"]["logical_call_id"] == "LC-2"
    assert attempt_failed[0]["payload"]["status_code"] == 529
    assert len(_entries(client, mission["id"], "structured_output_invalid")) == 1


# --- TEST L — B12 pendant la relance B13 : exposition conservatrice, relance refusée si besoin ---
def test_ambiguous_timeout_during_structured_retry_keeps_conservative_exposure(
    client: TestClient, use_llm: Callable[..., Any], sleeps: list[float]
) -> None:
    baseline = _baseline(client, use_llm)
    estimate = _framing_estimate(client, baseline)
    # Plafond généreux : le délai ambigu crée une exposition, B10 relance, la mission aboutit.
    shaped = ShapedLLM(ScriptedStructuredLLM(SIMPLE_FRAMING), {"framing": ["broken", "ok"]})
    use_llm(FailOnNth(shaped, call_type="framing", nth=2, exc=ambiguous_timeout()))
    mission = _post(client)
    assert mission["status"] == "candidate"
    budget = mission["report"]["budget"]
    assert budget["structured_output_retries"] == 1
    assert budget["uncertain_attempts"] == 1
    assert budget["uncertain_exposures"][0]["logical_call_id"] == "LC-2"
    assert budget["uncertain_cost_upper_bound_eur"] >= round(estimate, 6)  # relance plus longue
    assert budget["potential_total_cost_upper_bound_eur"] <= mission["max_cost_eur"]
    # Plafond serré : après l'exposition, connu + incertain + relance > plafond → B10 refuse
    # (B12), aucune tentative supplémentaire, échec explicite ; B13 n'a pas relancé deux fois.
    shaped = ShapedLLM(ScriptedStructuredLLM(SIMPLE_FRAMING), {"framing": ["broken", "ok"]})
    llm = use_llm(FailOnNth(shaped, call_type="framing", nth=2, exc=ambiguous_timeout()))
    mission = _post(client, max_cost_eur=round(estimate * 1.8, 6))
    assert mission["status"] == "failed"
    assert mission["stop_reason"] == "retry_refused_uncertain_cost_budget"
    assert [c["call_type"] for c in llm.calls] == ["framing", "framing"]
    budget = mission["report"]["budget"]
    assert budget["structured_output_retries"] == 1
    assert budget["uncertain_attempts"] == 1
    assert budget["potential_total_cost_upper_bound_eur"] <= mission["max_cost_eur"]
    assert mission["failure"]["retry_allowed_by_cost"] is False
    assert len(sleeps) == 1  # une seule attente : celle du plafond généreux
