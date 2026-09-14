"""OT-V1, incrément 2 — correctif v1.3.6.2 : identité du build (D20) et robustesse du pipeline
décisionnel (D21 catégorie A / synthèse, D22 familles, D23-D24 interne / externe, D25 tolérance
par élément, §7 raison d'arrêt). Tests §9 (1-30), §10 (cas synthétique de bout en bout), §11
(pré-vol).

Fixtures purement synthétiques : aucun texte métier de Mission #10, aucun mot propre à un cas ;
les faux clients de `test_missions_deliberation` sont réutilisés ; l'identité Git est simulée par
un `GitProbe` injecté (jamais un SHA inventé par le code). Aucun réseau.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from app import build_identity as bi
from app.build_identity import (
    BENCHMARK_BUILD_DIRTY,
    BENCHMARK_BUILD_MISMATCH,
    BENCHMARK_BUILD_UNAVAILABLE,
    GIT_STATUS_OK,
    GIT_STATUS_UNAVAILABLE,
    MISSION_CONFIG_FIELDS,
    GitProbe,
    benchmark_check,
    canonical_json,
    commits_match,
    compute_build_identity,
    git_probe,
    is_secret_setting,
    mission_config_snapshot,
)
from app.config import Settings, get_settings
from app.mission_budget import SYNTHESIS_RECOVERY_CALLS, deliberation_reserve
from app.mission_consolidation import conservative_merge_families, finalize_families
from app.mission_deliberation import (
    CONFRONTATION_SYSTEM,
    CONSOLIDATION_SYSTEM,
    SYNTHESIS_SYSTEM,
    classify_fact_source,
    internal_data_markers,
    select_research_questions,
)
from app.mission_schemas import (
    COMPARISON_MAX_CRITERIA,
    ComparisonOutput,
    ConfrontationOutput,
    ConsolidationOutput,
)
from app.output_budget import fixed_output_budget
from app.preflight import main as preflight_main
from app.reasoning_policy import policy_table
from app.structured_output import validate_with_item_tolerance
from fastapi.testclient import TestClient
from ui.api_client import SolutionPlansAPIClient

from tests.test_missions_deliberation import (
    DeliberationLLM,
    FakeResearchProvider,
    act,
    competent_clerk,
    default_comparison,
    default_synthesis,
)
from tests.test_missions_output_budget import ANGLE_WORDS, options_for
from tests.test_missions_v136 import _entries, _journal, _post, framing_with

CLEAN_SHA = "a" * 39 + "1"
OTHER_SHA = "b" * 39 + "2"
A_CALL_TYPES = ("framing", "expert_tour0", "confrontation", "steelman", "revision", "synthesis")
FORBIDDEN_CASE_WORDS = ("warehouse", "sku", "commercial", "logisti", "entrepot")
_CURRENT: dict[str, Any] = {}


# --- Fixtures ------------------------------------------------------------------------------------
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
def research(monkeypatch: pytest.MonkeyPatch) -> Callable[[Any], Any]:
    def _set(provider: Any) -> Any:
        monkeypatch.setattr("app.missions.build_research_provider", lambda settings: provider)
        return provider

    return _set


@pytest.fixture
def git(monkeypatch: pytest.MonkeyPatch) -> Callable[..., GitProbe]:
    """Identité Git simulée : le code ne lit que ce que la sonde rapporte (jamais d'invention)."""

    def _set(
        commit: str | None = CLEAN_SHA, *, dirty: bool | None = False, detail: str = ""
    ) -> GitProbe:
        probe = GitProbe(
            commit,
            dirty,
            "product/increment-2" if commit else "",
            GIT_STATUS_OK if commit else GIT_STATUS_UNAVAILABLE,
            detail,
        )
        monkeypatch.setattr(bi, "git_probe", lambda repo_dir=None: probe)
        return probe

    return _set


def _planned_by_type(client: TestClient, mission_id: int) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for e in _entries(client, mission_id, "call_planned"):
        out.setdefault(e["payload"]["call_type"], []).append(e["payload"])
    return out


def _truncated_then(fallback: Callable[[str], dict[str, Any]], *, n: int = 1) -> Any:
    """Script : les `n` premières réponses sont coupées à `max_tokens`, puis la réponse valide."""
    state = {"calls": 0}

    def script(label: str, prompt: str) -> dict[str, Any]:
        state["calls"] += 1
        if state["calls"] <= n:
            return {"__raw__": '{"problem_understood": "x', "__stop__": "max_tokens"}
        return fallback(prompt)

    return script


# =================================================================================================
# §9.1 — Identité du build (D20) : 7 tests.
# =================================================================================================
def test_01_build_identity_is_computed_never_invented_and_fingerprinted(
    git: Callable[..., GitProbe],
) -> None:
    git(CLEAN_SHA)
    settings = Settings.model_construct()
    identity = compute_build_identity(settings)
    assert identity.git_commit_full == CLEAN_SHA
    assert identity.git_commit_short == CLEAN_SHA[:7]
    assert identity.git_dirty is False
    assert identity.git_identity_status == GIT_STATUS_OK
    assert identity.provider_adapter == "anthropic"
    assert identity.provider_sdk_version
    assert identity.provider_sdk_version != "unknown"
    assert re.fullmatch(r"\d+\.\d+\.\d+", identity.python_version)
    assert re.fullmatch(r"[0-9a-f]{64}", identity.reasoning_policy_fingerprint)
    assert re.fullmatch(r"[0-9a-f]{64}", identity.mission_config_fingerprint)
    assert identity.created_at.endswith("+00:00")
    assert identity.label == f"{CLEAN_SHA[:7]} CLEAN"
    # Sonde indisponible : aucun SHA, statut explicite, libellé UNAVAILABLE — jamais une valeur
    # plausible fabriquée.
    git(None, dirty=None, detail="not a git repository")
    missing = compute_build_identity(settings)
    assert (missing.git_commit_full, missing.git_commit_short, missing.git_dirty) == (
        None,
        None,
        None,
    )
    assert missing.git_identity_status == GIT_STATUS_UNAVAILABLE
    assert missing.git_detail == "not a git repository"
    assert missing.label == "UNAVAILABLE"
    # Vérification de freeze : forme courte (≥ 7) ou complète ; jamais un préfixe trop court.
    assert commits_match(CLEAN_SHA, CLEAN_SHA[:7]) is True
    assert commits_match(CLEAN_SHA, CLEAN_SHA.upper()) is True
    assert commits_match(CLEAN_SHA, OTHER_SHA[:7]) is False
    assert commits_match(CLEAN_SHA, CLEAN_SHA[:6]) is False
    assert commits_match(None, CLEAN_SHA) is False
    assert benchmark_check(identity, CLEAN_SHA[:12])["verdict"] == "MATCH"
    assert benchmark_check(identity, OTHER_SHA)["reason"] == BENCHMARK_BUILD_MISMATCH
    assert benchmark_check(missing, CLEAN_SHA)["reason"] == BENCHMARK_BUILD_UNAVAILABLE
    assert benchmark_check(missing, "")["verdict"] == "NO_EXPECTED_FREEZE"


def test_01b_real_git_probe_reads_the_repository_and_never_invents_outside_one(
    tmp_path: Path,
) -> None:
    here = git_probe()
    assert here.status == GIT_STATUS_OK
    assert here.commit is not None
    assert re.fullmatch(r"[0-9a-f]{40}", here.commit)
    assert here.dirty in {True, False}
    outside = git_probe(tmp_path)
    assert outside.status == GIT_STATUS_UNAVAILABLE
    assert (outside.commit, outside.dirty) == (None, None)
    assert outside.detail


def test_02_mission_with_matching_expected_freeze_starts_and_persists_the_identity(
    client: TestClient, use_llm: Callable[..., Any], git: Callable[..., GitProbe]
) -> None:
    git(CLEAN_SHA)
    llm = use_llm(DeliberationLLM())
    mission = _post(client, expected_freeze=CLEAN_SHA[:7])
    build = mission["build_identity"]
    assert build["git_commit_full"] == CLEAN_SHA
    assert build["git_identity_status"] == GIT_STATUS_OK
    assert build["git_dirty"] is False
    assert mission["recommendation"]["status"] == "produced"
    assert len(llm.calls) == mission["llm_calls_used"] > 0
    # Journal : première entrée `created` avec l'identité (vue compacte) et le verdict benchmark.
    created = _entries(client, mission["id"], "created")[0]["payload"]
    assert created["build_identity"]["git_commit_short"] == CLEAN_SHA[:7]
    assert "mission_config" not in created["build_identity"]
    assert created["benchmark"]["verdict"] == "MATCH"
    assert created["benchmark"]["expected_freeze"] == CLEAN_SHA[:7]
    assert created["benchmark"]["enforced"] is True
    assert created["benchmark"]["warnings"] == []
    # Rapport, GET, statut produit : la même identité partout.
    assert mission["report"]["build"]["git_commit_full"] == CLEAN_SHA
    fetched = client.get(f"/missions/{mission['id']}").json()
    assert fetched["build_identity"]["git_commit_full"] == CLEAN_SHA
    assert fetched["build_identity"]["created_at"] == build["created_at"]
    status = client.get("/product/status").json()
    assert status["build"]["git_commit_full"] == CLEAN_SHA
    assert status["build_label"] == f"{CLEAN_SHA[:7]} CLEAN"
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert f"**Build :** `{CLEAN_SHA[:7]}` CLEAN" in md


def test_03_wrong_expected_freeze_refuses_the_mission_before_any_llm_call(
    client: TestClient, use_llm: Callable[..., Any], git: Callable[..., GitProbe]
) -> None:
    git(OTHER_SHA)
    llm = use_llm(DeliberationLLM())
    response = client.post(
        "/missions",
        json={
            "input_type": "problem",
            "input_text": "entrée synthétique v1362",
            "expected_freeze": CLEAN_SHA,
        },
    )
    assert response.status_code == 409, response.text
    detail = response.json()["detail"]
    assert detail["reason"] == BENCHMARK_BUILD_MISMATCH
    assert detail["benchmark"]["verdict"] == "MISMATCH"
    assert detail["benchmark"]["running_commit"] == OTHER_SHA
    assert detail["benchmark"]["expected_freeze"] == CLEAN_SHA
    assert detail["build"]["git_commit_short"] == OTHER_SHA[:7]
    assert (detail["llm_calls_used"], detail["cost_eur"]) == (0, 0.0)
    assert llm.calls == []
    # Aucune mission créée : rien à consommer, rien à auditer par erreur.
    assert client.get("/missions/1").status_code == 404
    # Le freeze attendu peut aussi venir de la configuration (opérateur), même effet.
    get_settings.cache_clear()


@pytest.mark.parametrize(
    ("commit", "dirty", "expected", "strict_env", "reason"),
    [
        (CLEAN_SHA, True, CLEAN_SHA, "", BENCHMARK_BUILD_DIRTY),
        (None, None, CLEAN_SHA, "", BENCHMARK_BUILD_UNAVAILABLE),
        (CLEAN_SHA, True, "", "true", BENCHMARK_BUILD_DIRTY),
        (None, None, "", "true", BENCHMARK_BUILD_UNAVAILABLE),
    ],
)
def test_04_dirty_or_unavailable_build_is_blocked_in_benchmark_mode(
    client: TestClient,
    use_llm: Callable[..., Any],
    git: Callable[..., GitProbe],
    settings_env: Callable[[str, str], None],
    commit: str | None,
    dirty: bool | None,
    expected: str,
    strict_env: str,
    reason: str,
) -> None:
    git(commit, dirty=dirty, detail="" if commit else "git indisponible")
    if strict_env:
        settings_env("MISSION_BENCHMARK_STRICT", strict_env)
    llm = use_llm(DeliberationLLM())
    payload: dict[str, Any] = {"input_type": "problem", "input_text": "entrée synthétique v1362"}
    if expected:
        payload["expected_freeze"] = expected
    response = client.post("/missions", json=payload)
    assert response.status_code == 409, response.text
    detail = response.json()["detail"]
    assert detail["reason"] == reason
    assert detail["llm_calls_used"] == 0
    assert llm.calls == []
    # Hors benchmark (ni freeze ni strict), le même build est accepté : signalé, pas bloqué.
    if strict_env:
        settings_env("MISSION_BENCHMARK_STRICT", "false")
    mission = _post(client)
    created = _entries(client, mission["id"], "created")[0]["payload"]
    assert created["benchmark"]["enforced"] is False
    if dirty:
        assert created["benchmark"]["warnings"] == ["build_dirty_outside_benchmark"]
        assert mission["build_identity"]["git_dirty"] is True
    else:
        assert mission["build_identity"]["git_identity_status"] == GIT_STATUS_UNAVAILABLE
        assert mission["build_identity"]["git_commit_full"] is None


def test_05_persisted_identity_is_immutable_even_if_the_running_build_changes(
    client: TestClient, use_llm: Callable[..., Any], git: Callable[..., GitProbe]
) -> None:
    git(CLEAN_SHA)
    use_llm(DeliberationLLM())
    mission = _post(client)
    assert mission["build_identity"]["git_commit_full"] == CLEAN_SHA
    # Le processus « change » de build (nouvelle sonde) : la mission garde son identité d'origine,
    # le statut produit reflète le build courant.
    git(OTHER_SHA, dirty=True)
    fetched = client.get(f"/missions/{mission['id']}").json()
    assert fetched["build_identity"]["git_commit_full"] == CLEAN_SHA
    assert fetched["build_identity"]["git_dirty"] is False
    assert fetched["report"]["build"]["git_commit_short"] == CLEAN_SHA[:7]
    status = client.get("/product/status").json()
    assert status["build"]["git_commit_full"] == OTHER_SHA
    assert status["build_label"] == f"{OTHER_SHA[:7]} DIRTY"
    # Une nouvelle mission porte le nouveau build : deux missions, deux identités distinctes.
    use_llm(DeliberationLLM())
    later = _post(client)
    assert later["build_identity"]["git_commit_full"] == OTHER_SHA
    assert later["build_identity"]["git_dirty"] is True
    assert client.get(f"/missions/{mission['id']}").json()["build_identity"]["git_commit_full"] == (
        CLEAN_SHA
    )


def test_06_config_fingerprint_is_deterministic_config_sensitive_and_secret_free(
    git: Callable[..., GitProbe],
) -> None:
    git(CLEAN_SHA)
    base = Settings.model_construct(anthropic_api_key="sk-secret-synthetique-ne-doit-pas-fuir")
    a = compute_build_identity(base)
    b = compute_build_identity(Settings.model_construct(anthropic_api_key="autre-secret"))
    # Déterministe et insensible aux secrets : même code + même configuration ⇒ même empreinte.
    assert a.mission_config_fingerprint == b.mission_config_fingerprint
    assert a.reasoning_policy_fingerprint == b.reasoning_policy_fingerprint
    # Sensible à un réglage structurant (plafond de recherche, marge de raisonnement).
    c = compute_build_identity(Settings.model_construct(mission_max_research_tasks=5))
    assert c.mission_config_fingerprint != a.mission_config_fingerprint
    d = compute_build_identity(Settings.model_construct(mission_reasoning_headroom_tokens_a=1000))
    assert d.mission_config_fingerprint != a.mission_config_fingerprint
    assert d.reasoning_policy_fingerprint != a.reasoning_policy_fingerprint
    # Sérialisation canonique : ordre des clés indifférent.
    assert canonical_json({"b": 1, "a": [2, {"d": 3, "c": 4}]}) == canonical_json(
        {"a": [2, {"c": 4, "d": 3}], "b": 1}
    )
    # Jamais de secret, de clé, de jeton, ni de contenu utilisateur dans l'identité.
    dumped = canonical_json(a.to_dict())
    assert "sk-secret-synthetique" not in dumped
    assert "anthropic_api_key" not in a.mission_config
    assert not [f for f in MISSION_CONFIG_FIELDS if is_secret_setting(f)]
    assert is_secret_setting("anthropic_api_key")
    assert is_secret_setting("research_api_token")
    assert not is_secret_setting("mission_max_tokens_synthesis")  # budget, pas un secret
    assert "mission_max_tokens_synthesis" in mission_config_snapshot(base)
    snapshot = mission_config_snapshot(base)
    assert snapshot["pipeline"]["synthesis_recovery_calls"] == SYNTHESIS_RECOVERY_CALLS
    assert snapshot["mission_output_ceiling_synthesis"] == 16000
    assert snapshot["mission_reasoning_headroom_tokens_synthesis"] == 4000
    assert snapshot["mission_comparison_max_criteria"] == COMPARISON_MAX_CRITERIA


def test_07_preflight_endpoint_cli_and_ui_client_report_the_running_build(
    client: TestClient,
    git: Callable[..., GitProbe],
    settings_env: Callable[[str, str], None],
    capsys: pytest.CaptureFixture[str],
) -> None:
    git(CLEAN_SHA)
    ok = client.get("/benchmark/preflight", params={"expected_freeze": CLEAN_SHA[:7]}).json()
    assert ok["verdict"] == "MATCH"
    assert ok["reason"] == ""
    assert ok["running_commit"] == CLEAN_SHA
    assert ok["build_label"] == f"{CLEAN_SHA[:7]} CLEAN"
    assert ok["class_ceilings"]["structurante"] == {"max_llm_calls": 60, "max_cost_eur": 8.0}
    assert ok["reasoning_policy"]["synthesis"]["headroom_tokens"] == 4000
    bad = client.get("/benchmark/preflight", params={"expected_freeze": OTHER_SHA}).json()
    assert (bad["verdict"], bad["reason"]) == ("MISMATCH", BENCHMARK_BUILD_MISMATCH)
    none = client.get("/benchmark/preflight").json()
    assert none["verdict"] == "NO_EXPECTED_FREEZE"
    # Le freeze attendu configuré côté opérateur est repris par défaut.
    settings_env("MISSION_EXPECTED_FREEZE", OTHER_SHA)
    assert client.get("/benchmark/preflight").json()["verdict"] == "MISMATCH"
    # Commande de pré-vol : verdict lisible, code de retour non nul sur MISMATCH, sortie JSON.
    assert preflight_main(["--expected", CLEAN_SHA]) == 0
    text = capsys.readouterr().out
    assert "Verdict        : MATCH" in text
    assert f"Running commit : {CLEAN_SHA}" in text
    assert "Working tree   : CLEAN" in text
    assert preflight_main(["--expected", OTHER_SHA]) == 1
    assert BENCHMARK_BUILD_MISMATCH in capsys.readouterr().out
    assert preflight_main(["--expected", CLEAN_SHA, "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["verdict"] == "MATCH"
    git(CLEAN_SHA, dirty=True)
    assert preflight_main(["--expected", CLEAN_SHA]) == 1
    assert "DIRTY" in capsys.readouterr().out
    # Client UI : l'interface interroge le serveur qui tourne, pas la copie locale de l'opérateur.
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["expected"] = request.url.params.get("expected_freeze")
        return httpx.Response(
            200,
            json={"verdict": "MISMATCH", "reason": BENCHMARK_BUILD_MISMATCH, "running_commit": "x"},
        )

    http = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://testserver")
    ui = SolutionPlansAPIClient(base_url="http://testserver", client=http)
    result = ui.benchmark_preflight(CLEAN_SHA[:7])
    assert (seen["path"], seen["expected"]) == ("/benchmark/preflight", CLEAN_SHA[:7])
    assert result["verdict"] == "MISMATCH"


# =================================================================================================
# §9.2 — Catégorie A : marge explicite, plafond, relance unique de la synthèse (D21) : 5 tests.
# =================================================================================================
def test_08_category_a_keeps_strong_reasoning_and_gets_an_explicit_configurable_headroom(
    settings_env: Callable[[str, str], None],
) -> None:
    table = policy_table(Settings.model_construct())
    for ct in A_CALL_TYPES:
        assert table[ct]["category"] == "A"
        assert (table[ct]["thinking"], table[ct]["effort"]) == ("adaptive", "high")
    assert {table[ct]["headroom_tokens"] for ct in A_CALL_TYPES if ct != "synthesis"} == {2000}
    assert table["synthesis"]["headroom_tokens"] == 4000  # pas identique pour toute la catégorie
    # Formule de l'étape à cardinalité fixe : granted = min(plafond, texte + marge).
    b = fixed_output_budget("framing", 8000, ceiling=12000, reasoning_headroom=2000)
    assert (b.required_tokens, b.reasoning_headroom, b.granted, b.ceiling) == (
        8000,
        2000,
        10000,
        12000,
    )
    assert b.capped_by_ceiling is False
    capped = fixed_output_budget("synthesis", 8000, ceiling=9000, reasoning_headroom=4000)
    assert (capped.granted, capped.ceiling, capped.capped_by_ceiling) == (9000, 9000, True)
    legacy = fixed_output_budget("framing", 8000)
    assert (legacy.granted, legacy.ceiling, legacy.reasoning_headroom) == (8000, 8000, 0)
    # Configurable, jamais figé dans le code.
    settings_env("MISSION_REASONING_HEADROOM_TOKENS_A", "1000")
    settings_env("MISSION_REASONING_HEADROOM_TOKENS_SYNTHESIS", "3000")
    live = policy_table(get_settings())
    assert live["framing"]["headroom_tokens"] == 1000
    assert live["synthesis"]["headroom_tokens"] == 3000
    assert (live["framing"]["thinking"], live["framing"]["effort"]) == ("adaptive", "high")


def test_09_every_category_a_call_is_granted_text_plus_headroom_under_an_explicit_ceiling(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    use_llm(
        DeliberationLLM(
            confrontation={"P1": {"acts": [act("P2", "critique", "solution", "objection à P2")]}}
        )
    )
    mission = _post(client, declared_class="structurante")
    assert mission["recommendation"]["status"] == "produced"
    planned = _planned_by_type(client, mission["id"])
    expected = {
        "framing": (8000, 2000, 10000, 12000),
        "expert_tour0": (6000, 2000, 8000, 10000),
        "confrontation": (4000, 2000, 6000, 8000),
        "steelman": (4000, 2000, 6000, 8000),
        "revision": (3000, 2000, 5000, 6000),
        "synthesis": (8000, 4000, 12000, 16000),
    }
    for ct, (text, headroom, granted, ceiling) in expected.items():
        assert planned.get(ct), ct
        for p in planned[ct]:
            ob = p["output_budget"]
            assert (ob["required_tokens"], ob["reasoning_headroom"]) == (text, headroom), ct
            assert (ob["granted"], ob["ceiling"]) == (granted, ceiling), ct
            # Invariant : granted ≥ texte + marge tant que le plafond le permet ; le plafond
            # laisse la place d'UNE relance recalculée.
            assert ob["granted"] >= ob["required_tokens"] + ob["reasoning_headroom"]
            assert ob["ceiling"] > ob["granted"]
            assert p["max_tokens"] == granted
    # La journalisation porte la marge et la politique, jamais le contenu du raisonnement.
    dumped = json.dumps(_journal(client, mission["id"]), ensure_ascii=False)
    assert "thinking_content" not in dumped


def test_10_truncated_synthesis_gets_exactly_one_recalculated_retry_financed_by_its_reserve(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    llm = use_llm(DeliberationLLM(synthesis=_truncated_then(default_synthesis)))
    mission = _post(client)
    assert mission["recommendation"]["status"] == "produced"
    assert mission["recommendation"]["salvaged"] is False
    assert mission["recommendation"]["gate"]["checks"]["synthesis_complete"] is True
    calls = [c for c in llm.calls if c["call_type"] == "synthesis"]
    assert [c["max_tokens"] for c in calls] == [12000, 16000]  # limite recalculée, sous plafond
    assert calls[0]["system"] == calls[1]["system"] == SYNTHESIS_SYSTEM  # contrat 14 champs
    assert calls[1]["prompt"] != calls[0]["prompt"]  # consignes de réparation, pas à l'identique
    assert mission["report"]["budget"]["structured_output_retries"] == 1
    invalid = _entries(client, mission["id"], "structured_output_invalid")
    assert len(invalid) == 1
    p = invalid[0]["payload"]
    assert p["category"] == "structured_output_truncated"
    assert p["will_retry"] is True
    assert p["truncation_retry_plan"]["allowed"] is True
    planned = _entries(client, mission["id"], "structured_output_retry_planned")
    assert len(planned) == 1
    assert planned[0]["step"] == "synthese"
    assert planned[0]["payload"]["financed_by_reserve_component"] == "synthesis_recovery"
    assert planned[0]["payload"]["max_tokens"] == 16000
    assert mission["stop_reason"] == ""
    assert mission["deliberation"]["stop"]["terminal_failure_reason"] == ""


def test_11_synthesis_failing_twice_is_terminal_named_and_never_looped(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    llm = use_llm(DeliberationLLM(synthesis=_truncated_then(default_synthesis, n=5)))
    mission = _post(client)
    rec = mission["recommendation"]
    assert rec["status"] == "failed"
    assert rec["error"].startswith(
        "structured_output_recovery_exhausted: structured_output_truncated"
    )
    assert len([c for c in llm.calls if c["call_type"] == "synthesis"]) == 2  # jamais 3
    assert mission["report"]["budget"]["structured_output_retries"] == 1
    stop = mission["deliberation"]["stop"]
    assert stop["terminal_failure_reason"] == "synthesis_structured_output_failed"
    assert stop["reason"] == "synthesis_structured_output_failed"
    assert mission["report"]["recommendation_produced"] is False
    assert any(
        s["step"] == "porte_qualite" and "aucune recommandation" in s["reason"]
        for s in mission["deliberation"]["steps_skipped"]
    )
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "**Cause terminale** : `synthesis_structured_output_failed`" in md


def test_12_synthesis_recovery_is_one_reserve_component_shared_by_composition_and_runtime(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    # Option C (B15) : la relance de synthèse est une composante nommée de la réserve unique —
    # même formule à la composition, dans le plan réel après le Tour 0 et aux portes de dépense.
    reserve = deliberation_reserve(
        3, effective_class="importante", consolidation_calls=1, revision_cap=8
    )
    assert reserve["synthesis_recovery"] == SYNTHESIS_RECOVERY_CALLS == 1
    assert reserve["core_nominal"] == 1 + 3 + SYNTHESIS_RECOVERY_CALLS
    assert reserve["total"] == sum(
        reserve[k]
        for k in (
            "confrontation",
            "steelman",
            "revisions",
            "consolidation",
            "comparison",
            "synthesis",
            "synthesis_recovery",
            "gate",
        )
    )
    use_llm(DeliberationLLM())
    mission = _post(client)
    bounds = mission["composition"]["bounds"]
    assert bounds["reserve_components"]["synthesis_recovery"] == 1
    assert bounds["reserve_components"] == reserve
    core = _entries(client, mission["id"], "deliberation_core_planned")[0]["payload"]
    assert core["reserve_components"]["synthesis_recovery"] == 1
    assert core["reserved_deliberation_calls"] == reserve["total"]
    assert mission["report"]["budget"]["reserved_deliberation_calls"] == reserve["total"]
    # Réserve non consommée quand la synthèse est valide du premier coup : un appel de moins que
    # le plan réservé, aucune relance facturée.
    assert mission["report"]["budget"]["structured_output_retries"] == 0
    # Une mission au budget exact (14 appels après cadrage) reste délibérable et complète.
    use_llm(DeliberationLLM())
    exact = _post(client, max_llm_calls=15)
    assert exact["composition"]["bounds"]["plan_feasible"] is True
    assert exact["recommendation"]["status"] == "produced"
    assert exact["llm_calls_used"] <= 15


# =================================================================================================
# §9.3 — Tolérance par élément (D25) : 3 tests.
# =================================================================================================
def _acts_with_one_invalid() -> dict[str, dict[str, Any]]:
    acts = [
        act("P2", "critique", "solution", "objection 1 à P2"),
        act("P3", "complement", "hypothesis", "complément à P3"),
        {**act("P2", "critique", "fact", "acte hors contrat"), "act": "bogus"},
        act("P3", "critique", "value", "objection de valeur à P3"),
        act("P2", "defend", "solution", "défense"),
    ]
    return {"P1": {"acts": acts}}


def test_13_one_invalid_act_is_rejected_alone_and_the_perspective_is_kept(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    use_llm(DeliberationLLM(confrontation=_acts_with_one_invalid()))
    mission = _post(client)
    outputs = mission["deliberation"]["confrontation"]["outputs"]
    assert outputs["E1"] is not None  # la perspective n'est pas déclarée « sortie invalide »
    assert [a["text"] for a in outputs["E1"]["acts"]] == [
        "objection 1 à P2",
        "complément à P3",
        "objection de valeur à P3",
        "défense",
    ]
    rejected = _entries(client, mission["id"], "item_rejected")
    assert len(rejected) == 1
    p = rejected[0]["payload"]
    assert rejected[0]["step"] == "confrontation"
    assert p["call_type"] == "confrontation"
    assert p["perspective_id"] == "E1"
    assert (p["field"], p["index"]) == ("acts", 2)
    assert p["error_field"] == "act"
    assert p["literal_received"] == "bogus"
    assert "bogus" in p["validation_error"]
    assert "thinking" not in json.dumps(p)
    assert mission["report"]["budget"]["structured_output_items_rejected"] == 1
    assert "structured_items_rejected:1" in mission["deliberation"]["stop"]["warnings"]
    # Aucune relance dépensée pour un seul élément hors contrat ; la mission va au bout.
    assert mission["report"]["budget"]["structured_output_retries"] == 0
    assert mission["recommendation"]["status"] == "produced"
    assert len(mission["deliberation"]["confrontation"]["objections"]) >= 3


def test_14_item_tolerance_generalizes_to_families_and_comparison_rows_only() -> None:
    # Confrontation : l'élément invalide est retiré, le littéral conservé tel quel (aucun
    # reclassement en une autre catégorie sémantique).
    data = {"acts": _acts_with_one_invalid()["P1"]["acts"], "convergence_note": ""}
    out, rejected, error = validate_with_item_tolerance(data, ConfrontationOutput)
    assert out is not None
    assert error == ""
    assert isinstance(out, ConfrontationOutput)
    assert [a.act for a in out.acts] == ["critique", "complement", "critique", "defend"]
    assert rejected == [
        {
            "field": "acts",
            "index": 2,
            "validation_error": rejected[0]["validation_error"],
            "error_field": "act",
            "literal_received": "bogus",
        }
    ]
    # Familles : une famille sans libellé est rejetée seule.
    cons = {
        "families": [
            {"label": "famille A", "kind": "build", "option_ids": ["O1"]},
            {"kind": "buy", "option_ids": ["O2"]},
            {"label": "famille C", "kind": "wait", "option_ids": ["O3"]},
        ]
    }
    out_c, rej_c, err_c = validate_with_item_tolerance(cons, ConsolidationOutput)
    assert isinstance(out_c, ConsolidationOutput)
    assert err_c == ""
    assert [f.label for f in out_c.families] == ["famille A", "famille C"]
    assert [(r["index"], r["error_field"]) for r in rej_c] == [(1, "label")]
    # Lignes de comparaison : une ligne sans famille est rejetée seule.
    comp = {
        "criteria": ["c1"],
        "rows": [
            {"family_id": "F1", "assessments": {"c1": {"value": "v", "basis": "inference"}}},
            {"assessments": {"c1": {"value": "v", "basis": "inference"}}},
        ],
    }
    out_r, rej_r, err_r = validate_with_item_tolerance(comp, ComparisonOutput)
    assert isinstance(out_r, ComparisonOutput)
    assert err_r == ""
    assert [r.family_id for r in out_r.rows] == ["F1"]
    assert [r["index"] for r in rej_r] == [1]
    # Une erreur hors des listes déclarées reste une erreur de schéma entière (pas de tolérance).
    out_x, rej_x, err_x = validate_with_item_tolerance(
        {"acts": "pas une liste"}, ConfrontationOutput
    )
    assert (out_x, rej_x) == (None, [])
    assert err_x


def test_15_all_items_invalid_is_still_a_schema_failure_not_an_empty_success() -> None:
    data = {"acts": [{**act("P2"), "act": "bogus"}, {**act("P3"), "nature": "bogus"}]}
    out, rejected, error = validate_with_item_tolerance(data, ConfrontationOutput)
    # Les deux éléments sont rejetés et décrits ; l'objet reconstruit (liste vide) reste valide
    # pour le contrat de confrontation (un `none` implicite), sans reclassement.
    assert len(rejected) == 2
    assert [r["literal_received"] for r in rejected] == ["bogus", "bogus"]
    assert isinstance(out, ConfrontationOutput)
    assert out.acts == []
    assert error == ""


# =================================================================================================
# §9.4 — Interne / externe (D23-D24) : 7 tests.
# =================================================================================================
def test_16_grammatical_person_is_not_epistemic_nature() -> None:
    first = "Quel est notre taux d'abandon actuel ?"
    third = "Quel est le taux d'abandon par équipe sur les parcours actuels ?"
    assert classify_fact_source(first) == "internal"
    assert classify_fact_source(third) == "internal"
    assert "metrique_privee_par_unite" in internal_data_markers(third)
    assert "possessif_organisation" in internal_data_markers(first)
    assert classify_fact_source("Existe-t-il une procédure formalisée pour ce cas ?") == "internal"
    assert classify_fact_source("Les clients de l'entreprise utilisent-ils l'option ?") == (
        "internal"
    )


def test_17_public_fact_is_external_when_declared_and_either_by_default() -> None:
    public = "Quelle réglementation impose une formation obligatoire annuelle dans ce secteur ?"
    assert internal_data_markers(public) == []
    assert classify_fact_source(public, declared="external") == "external"
    assert classify_fact_source(public) == "either"  # dans le doute : either, jamais external
    assert classify_fact_source(public, declared="internal") == "internal"


def test_18_mixed_question_is_either_and_the_guard_uses_no_case_words() -> None:
    mixed = "Quel est le prix public de l'offre et notre coût interne de mise en œuvre ?"
    assert classify_fact_source(mixed, declared="external") == "either"
    assert classify_fact_source(mixed) == "either"
    # Garde générique : catégories conceptuelles, aucun mot propre à un cas métier.
    import app.mission_deliberation as md

    sources = "\n".join(
        str(
            getattr(md, name).pattern
            if hasattr(getattr(md, name), "pattern")
            else getattr(md, name)
        )
        for name in ("_OWNED_RECORDS", "_PRIVATE_METRICS", "_ORG_UNITS", "_ORG_POSSESSIVE")
    ).lower()
    for pattern in md._INTERNAL_PATTERNS:
        sources += "\n" + pattern.pattern.lower()
    for word in FORBIDDEN_CASE_WORDS:
        assert word not in sources, word
    assert "personne grammaticale" in CONFRONTATION_SYSTEM
    assert "Dans le doute : either, jamais external" in CONFRONTATION_SYSTEM


def test_19_internal_question_becomes_missing_internal_info_with_a_decision_section(
    client: TestClient, use_llm: Callable[..., Any], research: Callable[[Any], Any]
) -> None:
    provider = research(FakeResearchProvider("found"))
    question = "Quel est le taux de réclamation par agence sur les douze derniers mois ?"
    a = act("P2", "critique", "fact", "le taux réel départage P2", fact_question=question)
    a["fact_source"] = "external"  # déclaration erronée : la garde conservatrice l'emporte
    use_llm(DeliberationLLM(confrontation={"P1": {"acts": [a]}}))
    mission = _post(client)
    item = mission["deliberation"]["research"][0]
    assert item["status"] == "internal_data_required"
    assert item["fact_source"] == "internal"
    assert item["provider"] == "none"
    assert provider.questions == []  # rien n'est envoyé au web
    stop = mission["deliberation"]["stop"]
    assert stop["reason"] == "missing_internal_info"
    assert stop["terminal_failure_reason"] == ""
    assert stop["missing_information"] == [
        {"kind": "internal_data_required", "count": 1, "ids": ["EV-1"]}
    ]
    candidate = _entries(client, mission["id"], "research_candidate")[0]["payload"]
    assert (candidate["declared_source"], candidate["source"]) == ("external", "internal")
    assert "metrique_privee_par_unite" in candidate["internal_markers"]
    requests = mission["report"]["deliberation"]["internal_information_requests"]
    assert len(requests) == 1
    req = requests[0]
    assert req["question"] == question
    assert req["why_it_discriminates"] == "le taux réel départage P2"
    assert req["decision_it_could_change"] == "positions P2"
    assert "probable_owner" in req
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "### Informations internes à obtenir (1)" in md
    assert question in md
    assert "pourquoi elle discrimine : le taux réel départage P2" in md
    assert "décision concernée : positions P2" in md
    assert "Information manquante : internal_data_required (1)" in md
    assert mission["recommendation"]["status"] == "produced"


def test_20_research_selection_is_coverage_based_and_traceable_not_first_come() -> None:
    def q(i: int, author: str, positions: list[str], source: str = "either") -> dict[str, Any]:
        return {
            "question": f"question synthétique {i}",
            "raised_by": author,
            "raised_by_all": [author],
            "positions": positions,
            "source": source,
        }

    candidates = [
        q(1, "P1", ["P2"]),
        q(2, "P1", ["P2"]),
        q(3, "P1", ["P2"]),
        q(4, "P4", ["P5"]),
        q(5, "P6", ["P7", "P8"]),
        q(6, "P1", ["P2"]),
        q(7, "P1", ["P2"]),
        q(8, "P1", ["P2"]),
        q(9, "P1", ["P2"]),
        q(10, "P1", ["P2"]),
    ]
    selected, deferred = select_research_questions(candidates, cap=3)
    assert len(selected) == 3
    assert len(deferred) == 7
    # Pas les trois premières : diversité des auteurs et des positions concernées d'abord.
    assert [s["question"] for s in selected] != [c["question"] for c in candidates[:3]]
    assert {s["raised_by"] for s in selected} == {"P1", "P4", "P6"}
    assert all(d["deferred_reason"].startswith("plafond de recherche (3)") for d in deferred)
    # Les questions internes ne consomment jamais le plafond et sont toutes conservées.
    internal = q(11, "P9", ["P10"], source="internal")
    selected2, deferred2 = select_research_questions([*candidates, internal], cap=3)
    assert internal in selected2
    assert len([s for s in selected2 if s["source"] != "internal"]) == 3
    assert len(deferred2) == 7
    # Plafond nul : tout est écarté (sauf l'interne), rien n'est perdu silencieusement.
    selected0, deferred0 = select_research_questions([*candidates, internal], cap=0)
    assert selected0 == [internal]
    assert len(deferred0) == 10


def test_21_research_cap_is_applied_with_candidate_selected_and_deferred_journals(
    client: TestClient, use_llm: Callable[..., Any], research: Callable[[Any], Any]
) -> None:
    provider = research(FakeResearchProvider("found"))
    questions = [
        f"Quelle norme publique encadre la pratique synthétique N{i} ?" for i in range(1, 6)
    ]
    targets = ["P2", "P3", "P2", "P3", "P2"]
    acts = [
        act(t, "critique", "fact", f"le fait N{i + 1} départage", fact_question=qn)
        for i, (t, qn) in enumerate(zip(targets, questions, strict=True))
    ]
    use_llm(DeliberationLLM(confrontation={"P1": {"acts": acts}}))
    mission = _post(client)
    assert len(provider.questions) == 3  # plafond produit `mission_max_research_tasks`
    assert len(_entries(client, mission["id"], "research_candidate")) == 5
    selected = _entries(client, mission["id"], "research_selected")
    deferred = _entries(client, mission["id"], "research_deferred")
    assert len(selected) == 3
    assert len(deferred) == 2
    assert all(e["payload"]["counts_against_cap"] is True for e in selected)
    assert all(e["payload"]["reason"] for e in deferred)
    assert {e["payload"]["question"] for e in selected} == set(provider.questions)
    assert len(mission["deliberation"]["research"]) == 3
    assert [d["question"] for d in mission["deliberation"]["research_deferred"]] == [
        e["payload"]["question"] for e in deferred
    ]
    assert "research_questions_deferred:2" in mission["deliberation"]["stop"]["warnings"]
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "### Questions factuelles non recherchées (plafond) (2)" in md
    # Aucun appel LLM pour sélectionner : les seuls appels restent ceux du pipeline.
    assert mission["llm_calls_used"] == 1 + 3 + 1 + 3 + 3 + 2 + 1 + 1 + 1 + 1


def test_22_declared_internal_wins_and_internal_plus_external_keeps_both_visible(
    client: TestClient, use_llm: Callable[..., Any], research: Callable[[Any], Any]
) -> None:
    provider = research(FakeResearchProvider("found"))
    public = "Quelle réglementation impose une formation obligatoire annuelle dans ce secteur ?"
    declared_internal = act(
        "P2", "critique", "fact", "seul le demandeur le sait", fact_question=public
    )
    declared_internal["fact_source"] = "internal"
    external = act(
        "P3", "critique", "fact", "la norme publique départage", fact_question=public + " (bis)"
    )
    external["fact_source"] = "external"
    use_llm(DeliberationLLM(confrontation={"P1": {"acts": [declared_internal, external]}}))
    mission = _post(client)
    items = {e["question"]: e for e in mission["deliberation"]["research"]}
    assert items[public]["status"] == "internal_data_required"
    assert items[public]["fact_source"] == "internal"
    assert items[public + " (bis)"]["status"] == "found"
    assert items[public + " (bis)"]["fact_source"] == "external"
    assert provider.questions == [public + " (bis)"]
    stop = mission["deliberation"]["stop"]
    assert stop["reason"] == "missing_internal_info"
    assert [m["kind"] for m in stop["missing_information"]] == ["internal_data_required"]
    synthesis_prompt = next(c for c in _CURRENT["llm"].calls if c["call_type"] == "synthesis")[
        "prompt"
    ]
    assert "Informations INTERNES à demander" in synthesis_prompt


# =================================================================================================
# §9.5 — Compression stratégique (D22) : 5 tests.
# =================================================================================================
def _fam(
    label: str,
    kind: str = "build",
    *,
    ids: list[str],
    objective: str = "",
    target: str = "",
    trigger: str = "",
) -> dict[str, Any]:
    return {
        "label": label,
        "kind": kind,
        "option_ids": ids,
        "group_ids": list(ids),
        "variants": [],
        "internal_disagreements": [],
        "source_kinds": [kind],
        "source": "greffier",
        "objective": objective,
        "target": target,
        "reversibility": "medium",
        "prerequisites": [],
        "trigger": trigger,
        "trade_off": "",
    }


def test_23_families_are_represented_conceptually_and_prompted_that_way() -> None:
    for word in ("objective", "target", "reversibility", "prerequisites", "trigger", "trade_off"):
        assert word in CONSOLIDATION_SYSTEM, word
    assert "ORIENTATION DÉCISIONNELLE" in CONSOLIDATION_SYSTEM
    final, trace = finalize_families(
        [
            _fam(
                "renforcer le dispositif existant",
                ids=["E1-O1"],
                objective="réduire l'écart constaté",
                target="dispositif existant",
                trigger="dès validation",
            )
        ],
        [{"option_id": "E1-O1", "expert_id": "E1", "kind": "build", "dimension": "d"}],
    )
    assert final[0]["objective"] == "réduire l'écart constaté"
    assert final[0]["target"] == "dispositif existant"
    assert final[0]["reversibility"] == "medium"
    assert final[0]["trigger"] == "dès validation"
    assert set(final[0]) >= {"prerequisites", "trade_off", "kind", "variants"}
    assert trace == [{"option_id": "E1-O1", "family_id": "F1", "role": "member"}]


def test_24_paraphrases_merge_on_structured_semantics_material_conditions_stay_apart() -> None:
    notes: list[str] = []
    same = _fam(
        "renforcer l'existant",
        ids=["A"],
        objective="réduire l'écart",
        target="dispositif actuel",
        trigger="immédiat",
    )
    paraphrase = _fam(
        "consolider le dispositif en place",  # libellé sans radical commun
        ids=["B"],
        objective="réduire l'écart",
        target="dispositif actuel",
        trigger="immédiat",
    )
    conditional = _fam(
        "renforcer l'existant",
        ids=["C"],
        objective="réduire l'écart",
        target="dispositif actuel",
        trigger="seulement si la mesure M confirme l'écart",  # condition matérielle
    )
    other_kind = _fam("renforcer l'existant", "wait", ids=["D"])
    merged, fusions = conservative_merge_families(
        [same, paraphrase, conditional, other_kind], notes
    )
    # Paraphrase (même nature + objectif + cible + déclencheur) → une famille, libellé absorbé en
    # variante ; condition matérielle différente → famille distincte ; nature différente → jamais.
    assert fusions == 1
    assert [f["option_ids"] for f in merged] == [["A", "B"], ["C"], ["D"]]
    assert merged[0]["variants"] == [
        {"option_id": "B", "difference": "formulation : consolider le dispositif en place"}
    ]
    assert merged[0]["source"] == "greffier+repli_deterministe"
    assert merged[1]["source"] == "greffier"
    assert notes
    assert "identité stricte" in notes[0]
    # Sans métadonnées structurées, deux libellés proches ne sont PAS rapprochés par radical.
    lexical_a = _fam("externaliser la maintenance", ids=["X"])
    lexical_b = _fam("externaliser la maintenance applicative", ids=["Y"])
    merged2, fusions2 = conservative_merge_families([lexical_a, lexical_b], [])
    assert fusions2 == 0
    assert len(merged2) == 2
    # Libellé normalisé identique et même nature → fusion (accents / casse indifférents).
    merged3, fusions3 = conservative_merge_families(
        [_fam("Réduire le périmètre", ids=["X"]), _fam("reduire le perimetre", ids=["Y"])], []
    )
    assert (fusions3, merged3[0]["option_ids"]) == (1, ["X", "Y"])


def test_25_meta_consolidation_failure_falls_back_conservatively_and_reaches_the_gate(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    state = {"calls": 0}

    def clerk(label: str, prompt: str) -> dict[str, Any]:
        state["calls"] += 1
        if state["calls"] >= 3:  # les deux lots réussissent ; toute méta-passe est inexploitable
            return {"__raw__": '{"families": "pas une liste"}', "__stop__": "end_turn"}
        return competent_clerk(label, prompt)

    framing = framing_with([(f"dimension v1362 {i}", "low", [ANGLE_WORDS[i]]) for i in range(4)])
    llm = use_llm(DeliberationLLM(framing=framing, options=options_for(4, 5), consolidation=clerk))
    mission = _post(client)
    cons = mission["deliberation"]["consolidation"]
    assert cons["groups_after_premerge"] == 20  # > 16 : deux lots + une méta-passe
    assert cons["batches"] == 2
    assert cons["meta_failed"] is True
    assert cons["status"] == "partial"
    assert cons["family_count"] == 20  # aucune famille perdue, aucune fusion hasardeuse
    assert cons["fallback_fusions"] == 0
    assert cons["unconsolidated_option_ids"] == []
    fallback = _entries(client, mission["id"], "meta_fallback")
    assert len(fallback) == 1
    assert fallback[0]["payload"]["fusions"] == 0
    assert fallback[0]["payload"]["families_after"] == 20
    assert "aucun rapprochement lexical" in fallback[0]["payload"]["rule"]
    assert any("repli" in n or "méta-consolidation non exploitable" in n for n in cons["notes"])
    assert [c for c in llm.calls if c["call_type"] == "consolidation"]
    assert mission["recommendation"]["status"] == "produced"
    assert "porte_qualite" in mission["deliberation"]["steps_done"]
    assert "consolidation_partial" in mission["deliberation"]["stop"]["degraded_steps"]


def test_26_comparison_criteria_are_bounded_and_dropped_ones_are_declared(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    def nine_criteria(label: str, prompt: str) -> dict[str, Any]:
        base = default_comparison(prompt)
        extra = [f"critère synthétique {i}" for i in range(6, 10)]
        base["criteria"] = [*base["criteria"], *extra]
        for row in base["rows"]:
            for c in extra:
                row["assessments"][c] = {"value": "appréciation", "basis": "inference"}
        return base

    use_llm(DeliberationLLM(comparison=nine_criteria))
    mission = _post(client)
    comp = mission["deliberation"]["comparison"]
    assert len(comp["criteria"]) == COMPARISON_MAX_CRITERIA == 7
    assert comp["criteria"][:5] == ["résultat attendu", "coût", "délai", "risque", "réversibilité"]
    assert comp["criteria_dropped"] == ["critère synthétique 8", "critère synthétique 9"]
    assert all(set(r["assessments"]) == set(comp["criteria"]) for r in comp["rows"])
    assert comp["status"] == "ok"
    truncated = _entries(client, mission["id"], "criteria_truncated")
    assert len(truncated) == 1
    assert truncated[0]["payload"]["dropped"] == comp["criteria_dropped"]
    gate = mission["recommendation"]["gate"]
    assert any("critères excédentaires écartés" in i for i in gate["issues"])
    # Aucun score numérique dans les appréciations.
    values = [a["value"] for r in comp["rows"] for a in r["assessments"].values()]
    assert not [v for v in values if re.fullmatch(r"\s*\d+([.,]\d+)?\s*(/\s*\d+)?\s*", v)]


def test_27_comparison_contract_never_removes_a_mandatory_criterion() -> None:
    out = ComparisonOutput.model_validate(
        {
            "criteria": [
                "résultat attendu",
                "coût",
                "délai",
                "risque",
                "réversibilité",
                "c6",
                "c7",
                "c8",
                "c6",
            ],
            "rows": [
                {
                    "family_id": "F1",
                    "assessments": {
                        c: {"value": "v", "basis": "inference"} for c in ["coût", "c7", "c8"]
                    },
                }
            ],
        }
    )
    assert out.criteria == [
        "résultat attendu",
        "coût",
        "délai",
        "risque",
        "réversibilité",
        "c6",
        "c7",
    ]
    assert out.criteria_dropped == ["c8"]
    assert set(out.rows[0].assessments) == {"coût", "c7"}
    assert "jamais plus de 7 critères" in CONSOLIDATION_SYSTEM or "jamais plus de 7" in (
        __import__("app.mission_deliberation", fromlist=["COMPARISON_SYSTEM"]).COMPARISON_SYSTEM
    )
    # Contrat de synthèse compressé sans champ retiré : bornes explicites dans la consigne.
    assert (
        "au plus 8 options, 6 preuves, 5 avantages, 5 inconvénients, 6 risques" in SYNTHESIS_SYSTEM
    )
    assert "3 à 5 phrases" in SYNTHESIS_SYSTEM
    for field_name in (
        "problem_understood",
        "objective",
        "constraints",
        "assumptions",
        "options",
        "evidence",
        "advantages",
        "disadvantages",
        "risks",
        "recommendation",
        "confidence",
        "residual_disagreements",
        "change_conditions",
        "next_action",
    ):
        assert field_name in SYNTHESIS_SYSTEM, field_name


# =================================================================================================
# §9.6 — Reporting (§7) : 3 tests.
# =================================================================================================
def test_28_terminal_failure_dominates_missing_information_stays_context(
    client: TestClient, use_llm: Callable[..., Any], research: Callable[[Any], Any]
) -> None:
    research(FakeResearchProvider("found"))
    question = "Quel est le taux de réclamation par agence sur les douze derniers mois ?"
    use_llm(
        DeliberationLLM(
            confrontation={
                "P1": {"acts": [act("P2", "critique", "fact", "départage", fact_question=question)]}
            },
            synthesis=_truncated_then(default_synthesis, n=5),
        )
    )
    mission = _post(client)
    stop = mission["deliberation"]["stop"]
    assert stop["terminal_failure_reason"] == "synthesis_structured_output_failed"
    assert (
        stop["reason"] == "synthesis_structured_output_failed"
    )  # jamais « missing_internal_info »
    assert stop["missing_information"] == [
        {"kind": "internal_data_required", "count": 1, "ids": ["EV-1"]}
    ]
    assert "skipped:porte_qualite" in stop["degraded_steps"]
    assert set(stop) == {
        "reason",
        "terminal_failure_reason",
        "missing_information",
        "degraded_steps",
        "warnings",
        "stop_reason",
        "steps_done",
    }


def test_29_missing_information_without_failure_is_a_context_not_a_terminal_cause(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    public = "Quelle réglementation impose une formation obligatoire annuelle dans ce secteur ?"
    external = act("P2", "critique", "fact", "la norme départage", fact_question=public)
    external["fact_source"] = "external"
    use_llm(DeliberationLLM(confrontation={"P1": {"acts": [external]}}))
    mission = _post(client)  # aucun fournisseur de recherche : externe non résolue
    stop = mission["deliberation"]["stop"]
    assert stop["reason"] == "missing_external_info"
    assert stop["terminal_failure_reason"] == ""
    assert stop["missing_information"] == [
        {"kind": "external_research_unresolved", "count": 1, "ids": ["EV-1"]}
    ]
    assert "research_provider_unavailable" in stop["warnings"]
    assert stop["degraded_steps"] == []
    assert mission["recommendation"]["status"] == "produced"
    assert mission["stop_reason"] == ""


def test_30_revision_without_any_call_is_labelled_evaluated_not_executed(
    client: TestClient, use_llm: Callable[..., Any]
) -> None:
    use_llm(DeliberationLLM())  # aucune objection : rien à réviser
    mission = _post(client)
    d = mission["deliberation"]
    assert "revision_evaluated" in d["steps_done"]
    assert "revision" not in d["steps_done"]
    outcome = d["step_outcomes"]["revision"]
    assert outcome == {
        "evaluated": 3,
        "requested": 0,
        "executed": 0,
        "changed_position": 0,
        "refused_for_budget": 0,
        "label": "revision_evaluated",
    }
    assert not [c for c in _CURRENT["llm"].calls if c["call_type"] == "revision"]
    assert d["stop"]["reason"] == "no_new_information"
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "0 exécutée(s) (appel LLM), 0 changement(s) de position — `revision_evaluated`" in md
    # Témoin : une révision réellement exécutée qui change une position est étiquetée ainsi.
    use_llm(
        DeliberationLLM(
            confrontation={"P1": {"acts": [act("P2", "critique", "solution", "objection")]}},
            revision={
                "P2": {
                    "decision": "nuance",
                    "revised_position": "position deux nuancée",
                    "reason": "l'objection OBJ-1 tient",
                    "triggered_by": ["OBJ-1"],
                }
            },
        )
    )
    changed = _post(client)
    assert changed["deliberation"]["step_outcomes"]["revision"]["label"] == (
        "revision_changed_position"
    )
    assert "revision" in changed["deliberation"]["steps_done"]
    assert changed["deliberation"]["stop"]["reason"] in {"converged", "residual_only"}


# =================================================================================================
# §10 — Cas synthétique de bout en bout (nouveau problème, aucun texte de Mission #10).
# =================================================================================================
E2E_DIMENSIONS = [
    ("dimension v1362 adoption", "high"),
    ("dimension v1362 coût total", "high"),
    ("dimension v1362 réversibilité", "high"),
    ("dimension v1362 conformité", "high"),
    ("dimension v1362 délai", "high"),
]
E2E_PROPOSAL = {
    "label": "acheter une solution externe clé en main",
    "kind": "buy",
    "proposed_by": "demandeur",
}
E2E_INPUT = (
    "Problème synthétique v1362 : une organisation doit choisir comment renouveler un dispositif "
    "interne de formation dont l'usage baisse. Le demandeur propose d'acheter une solution "
    "externe clé en main. Les contraintes : budget annuel plafonné, obligation réglementaire de "
    "formation annuelle, équipes réparties sur plusieurs sites."
)
E2E_EXTERNAL_Q = (
    "Quelle réglementation impose une formation obligatoire annuelle dans ce secteur, et avec "
    "quelle périodicité publiée ?"
)
E2E_INTERNAL_Q = "Quel est le taux d'abandon par équipe sur les parcours actuels ?"


def e2e_framing() -> dict[str, Any]:
    dims = [
        (name, crit, [ANGLE_WORDS[(3 * i + k) % len(ANGLE_WORDS)] for k in range(3)])
        for i, (name, crit) in enumerate(E2E_DIMENSIONS)
    ]
    return framing_with(
        dims,
        problem_understood="renouvellement d'un dispositif interne de formation (cas synthétique)",
        explicit_proposals=[E2E_PROPOSAL],
    )


def e2e_confrontation() -> dict[str, dict[str, Any]]:
    external = act(
        "P2",
        "critique",
        "fact",
        "l'obligation réglementaire contraint P2",
        fact_question=E2E_EXTERNAL_Q,
    )
    external["fact_source"] = "external"
    internal = act(
        "P3",
        "critique",
        "fact",
        "le taux d'abandon réel départage P3",
        fact_question=E2E_INTERNAL_Q,
    )
    internal["fact_source"] = "either"
    return {
        "P1": {"acts": [external, internal, act("P4", "critique", "solution", "objection à P4")]},
        "P5": {"acts": [act("P2", "critique", "value", "arbitrage de valeur avec P2")]},
    }


def semantic_clerk(label: str, prompt: str) -> dict[str, Any]:
    out = competent_clerk(label, prompt)
    for i, fam in enumerate(out["families"]):
        fam.update(
            {
                "objective": f"objectif synthétique {i % 4}",
                "target": f"cible synthétique {i % 3}",
                "reversibility": ["high", "medium", "low"][i % 3],
                "prerequisites": ["prérequis synthétique"],
                "trigger": "",
                "trade_off": "arbitrage synthétique",
            }
        )
    return out


def test_e2e_synthetic_problem_traverses_the_full_pipeline_under_the_structurante_budget(
    client: TestClient,
    use_llm: Callable[..., Any],
    research: Callable[[Any], Any],
    git: Callable[..., GitProbe],
) -> None:
    git(CLEAN_SHA)
    provider = research(FakeResearchProvider("found"))
    framing = e2e_framing()
    assert sum(len(d["suggested_angles"]) for d in framing["dimensions"]) == 15
    llm = use_llm(
        DeliberationLLM(
            framing=framing,
            options=options_for(15, 2),
            relation="identical",  # convergence suspecte des 15 perspectives
            confrontation=e2e_confrontation(),
            revision={
                "P2": {
                    "decision": "nuance",
                    "revised_position": "position deux nuancée : sous réserve de l'obligation",
                    "reason": "la preuve EV-1 établit la périodicité",
                    "triggered_by": ["EV-1"],
                }
            },
            consolidation=semantic_clerk,
        )
    )
    mission = _post(
        client,
        input_text=E2E_INPUT,
        declared_class="structurante",
        expected_freeze=CLEAN_SHA[:7],
    )
    # Budget et identité.
    assert (mission["max_llm_calls"], mission["max_cost_eur"]) == (60, 8.0)
    assert mission["llm_calls_used"] <= 60
    assert mission["cost_eur"] <= 8.0
    assert mission["stop_reason"] == ""
    assert mission["status"] == "candidate"
    assert mission["build_identity"]["git_commit_full"] == CLEAN_SHA
    bounds = mission["composition"]["bounds"]
    assert bounds["plan_feasible"] is True
    assert len(mission["composition"]["experts"]) == 15
    assert mission["composition"]["uncovered_dimensions"] == []
    d = mission["deliberation"]
    for step in (
        "confrontation",
        "steelman",
        "recherche",
        "revision",
        "consolidation",
        "comparaison",
        "synthese",
        "porte_qualite",
    ):
        assert step in d["steps_done"], step
    # Steelman de l'alternative écartée (proposition explicite du demandeur, défendue par aucune
    # position), sous convergence suspecte.
    st = d["steelman"]
    assert st["required"] is True
    assert st["mode"] == "discarded_alternative"
    assert st["alternative"]["label"] == E2E_PROPOSAL["label"]
    assert st["advocate"] != st["critic"]
    assert st["status"] in {"accepted", "accepted_partial"}
    # Recherche : externe recherchée et trouvée, interne jamais envoyée au web.
    items = {e["question"]: e for e in d["research"]}
    assert items[E2E_EXTERNAL_Q]["status"] == "found"
    assert items[E2E_EXTERNAL_Q]["fact_source"] == "external"
    assert items[E2E_INTERNAL_Q]["status"] == "internal_data_required"
    assert items[E2E_INTERNAL_Q]["fact_source"] == "internal"
    assert provider.questions == [E2E_EXTERNAL_Q]
    # Révision : une position change sous preuve, une autre est évaluée sans être forcée.
    revs = {r["label"]: r for r in d["revisions"] if r.get("called")}
    assert revs["P2"]["decision"] == "nuance"
    assert revs["P2"]["triggered_by"] == ["EV-1"]
    assert revs["P4"]["decision"] == "maintain"
    outcome = d["step_outcomes"]["revision"]
    assert outcome["changed_position"] == 1
    assert outcome["executed"] >= 2
    assert outcome["label"] == "revision_changed_position"
    # Familles conceptuelles, comparaison bornée, synthèse et porte.
    families = d["consolidation"]["families"]
    assert len(families) >= 2
    assert all(f["objective"] and f["target"] for f in families)
    assert d["consolidation"]["status"] == "ok"
    comp = d["comparison"]
    assert comp["status"] == "ok"
    assert 5 <= len(comp["criteria"]) <= 7
    assert 1 <= len(comp["retained_family_ids"]) <= 12
    rec = mission["recommendation"]
    assert rec["status"] == "produced"
    assert rec["salvaged"] is False
    assert rec["gate"]["checks"]["steelman_done_if_required"] is True
    assert rec["gate"]["checks"]["synthesis_complete"] is True
    assert "porte_qualite" in d["steps_done"]
    # Raison d'arrêt : l'information interne manquante est un contexte, pas une cause terminale.
    stop = d["stop"]
    assert stop["terminal_failure_reason"] == ""
    assert stop["reason"] == "missing_internal_info"
    assert [m["kind"] for m in stop["missing_information"]] == ["internal_data_required"]
    # Comptage des appels : aucune boucle, aucune relance structurée nécessaire.
    counts: dict[str, int] = {}
    for c in llm.calls:
        counts[c["call_type"]] = counts.get(c["call_type"], 0) + 1
    assert counts["expert_tour0"] == 15
    assert counts["self_qualification"] == 5
    assert counts["confrontation"] == 15
    assert (counts["steelman"], counts["steelman_challenge"]) == (1, 1)
    assert counts["consolidation"] == 3  # 30 groupes : 2 lots + 1 méta
    assert (counts["comparison"], counts["synthesis"], counts["quality_gate"]) == (1, 1, 1)
    assert mission["llm_calls_used"] == len(llm.calls) + 1  # + 1 appel de recherche externe
    assert mission["report"]["budget"]["structured_output_retries"] == 0
    md = client.get(f"/missions/{mission['id']}/report/markdown").json()["markdown"]
    assert "### Informations internes à obtenir (1)" in md
    assert "alternative écartée" in md
    assert f"**Build :** `{CLEAN_SHA[:7]}` CLEAN" in md
