"""Identité du build qui exécute une mission (D20 — v1.3.6.2, intégrité des benchmarks).

Constat (post-mortem Holdout #10) : une mission pouvait être exécutée par un processus dont
personne — ni l'opérateur avant le lancement, ni l'auditeur après coup — ne pouvait établir le
commit, la version du produit, la version du SDK fournisseur ni les réglages structurants. Un
benchmark a été consommé sans exercer le correctif audité.

Invariant : toute mission répond de façon déterministe à « quel code et quelle configuration
m'ont exécutée ? ». L'identité est capturée **au moment de la création de la mission**, persistée
avec elle (immuable), journalisée, exposée par l'API, le rapport, le statut produit et l'interface.

Règles :
* aucun SHA inventé : sans dépôt Git lisible, `git_commit_full = None` et
  `git_identity_status = "unavailable"` ;
* le fingerprint de configuration couvre les paramètres capables de modifier le comportement
  intellectuel ou budgétaire d'une mission (sérialisation canonique + SHA-256), jamais un secret,
  une clé, un jeton ni du contenu utilisateur ;
* mode benchmark strict (`expected_freeze` fourni) : FAIL CLOSED — la mission ne démarre pas si le
  commit diffère, si l'identité Git est indisponible ou si l'arbre de travail est modifié ; aucun
  appel LLM n'est consommé.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import platform
import subprocess
from dataclasses import asdict, dataclass, field
from importlib import metadata
from pathlib import Path
from typing import Any

from app.reasoning_policy import policy_table

PRODUCT_DISTRIBUTION = "aisos-product"
PROVIDER_ADAPTER = "anthropic"
PROVIDER_SDK_DISTRIBUTION = "anthropic"
GIT_STATUS_OK = "ok"
GIT_STATUS_UNAVAILABLE = "unavailable"
BENCHMARK_BUILD_MISMATCH = "benchmark_build_mismatch"
BENCHMARK_BUILD_UNAVAILABLE = "benchmark_build_unavailable"
BENCHMARK_BUILD_DIRTY = "benchmark_build_dirty"
_GIT_TIMEOUT_SECONDS = 5.0

# Paramètres de mission dont dépend le comportement intellectuel ou budgétaire (jamais de secret).
MISSION_CONFIG_FIELDS: tuple[str, ...] = (
    "anthropic_model",
    "mission_ceiling_calls_courante",
    "mission_ceiling_cost_courante",
    "mission_ceiling_calls_importante",
    "mission_ceiling_cost_importante",
    "mission_ceiling_calls_structurante",
    "mission_ceiling_cost_structurante",
    "mission_ceiling_calls_critique",
    "mission_ceiling_cost_critique",
    "mission_max_angles_per_cell",
    "mission_research_provider",
    "mission_max_research_tasks",
    "mission_max_tokens_framing",
    "mission_max_tokens_expert",
    "mission_max_tokens_self_qualification",
    "mission_max_tokens_clerk",
    "mission_max_tokens_confrontation",
    "mission_max_tokens_steelman",
    "mission_max_tokens_recognition",
    "mission_max_tokens_revision",
    "mission_max_tokens_consolidation",
    "mission_max_tokens_comparison",
    "mission_max_tokens_synthesis",
    "mission_max_tokens_gate",
    "mission_max_tokens_research",
    "mission_output_ceiling_self_qualification",
    "mission_output_ceiling_clerk",
    "mission_output_ceiling_consolidation",
    "mission_output_ceiling_comparison",
    "mission_output_ceiling_framing",
    "mission_output_ceiling_expert",
    "mission_output_ceiling_confrontation",
    "mission_output_ceiling_steelman",
    "mission_output_ceiling_revision",
    "mission_output_ceiling_synthesis",
    "mission_max_revision_calls",
    "mission_self_qualification_group_max",
    "mission_reasoning_effort_a",
    "mission_reasoning_effort_b",
    "mission_reasoning_effort_c",
    "mission_reasoning_thinking_c",
    "mission_reasoning_headroom_tokens_a",
    "mission_reasoning_headroom_tokens_synthesis",
    "mission_reasoning_headroom_tokens_b",
    "mission_reasoning_headroom_tokens_c",
    "mission_max_options_per_expert",
    "mission_comparison_max_criteria",
    "mission_provider_max_attempts",
    "mission_provider_max_retries_total",
    "llm_price_input_eur_per_mtok",
    "llm_price_output_eur_per_mtok",
)
# Mots (segments de nom) qui désignent un secret ; « tokens » (budgets de sortie) n'en est pas un.
_FORBIDDEN_WORDS = frozenset({"key", "secret", "token", "password", "credential", "dsn"})
_FORBIDDEN_FRAGMENTS = ("database_url",)


def is_secret_setting(name: str) -> bool:
    """Un réglage dont le nom désigne un secret n'entre jamais dans une empreinte."""
    parts = set(name.lower().split("_"))
    return bool(parts & _FORBIDDEN_WORDS) or any(f in name.lower() for f in _FORBIDDEN_FRAGMENTS)


@dataclass(frozen=True)
class GitProbe:
    """Résultat brut de l'interrogation du dépôt Git (ou son indisponibilité)."""

    commit: str | None
    dirty: bool | None
    branch: str = ""
    status: str = GIT_STATUS_UNAVAILABLE
    detail: str = ""


@dataclass(frozen=True)
class BuildIdentity:
    """Identité auditable d'un build : code, environnement, politique, réglages, horodatage."""

    git_commit_full: str | None
    git_commit_short: str | None
    git_dirty: bool | None
    git_identity_status: str
    git_branch: str
    product_version: str
    python_version: str
    provider_adapter: str
    provider_sdk_version: str
    reasoning_policy_fingerprint: str
    mission_config_fingerprint: str
    created_at: str
    git_detail: str = ""
    mission_config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def compact(self) -> dict[str, Any]:
        """Vue sans le détail des réglages (journal, rapport, statut)."""
        data = self.to_dict()
        data.pop("mission_config", None)
        return data

    @property
    def label(self) -> str:
        """Libellé court pour l'interface : `abc1234 CLEAN|DIRTY|UNAVAILABLE`."""
        if self.git_commit_short is None:
            return "UNAVAILABLE"
        return f"{self.git_commit_short} {'DIRTY' if self.git_dirty else 'CLEAN'}"


def _run_git(args: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=_GIT_TIMEOUT_SECONDS,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout).strip()[:200] or "git error")
    return completed.stdout.strip()


def git_probe(repo_dir: Path | None = None) -> GitProbe:
    """Interroge le dépôt Git qui contient le code exécuté. Jamais d'invention : indisponible =
    `commit None`, `dirty None`, statut `unavailable` avec la raison."""
    cwd = repo_dir or Path(__file__).resolve().parent
    try:
        commit = _run_git(["rev-parse", "HEAD"], cwd)
        porcelain = _run_git(["status", "--porcelain", "--untracked-files=no"], cwd)
        try:
            branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
        except (RuntimeError, OSError, subprocess.SubprocessError):
            branch = ""
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        return GitProbe(None, None, "", GIT_STATUS_UNAVAILABLE, str(exc)[:200])
    if len(commit) < 7:
        return GitProbe(None, None, "", GIT_STATUS_UNAVAILABLE, "commit illisible")
    return GitProbe(commit, bool(porcelain.strip()), branch, GIT_STATUS_OK, "")


def _distribution_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "unknown"


def canonical_json(data: Any) -> str:
    """Sérialisation canonique déterministe (clés triées, séparateurs fixes, ASCII)."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def fingerprint(data: Any) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def mission_config_snapshot(settings: Any) -> dict[str, Any]:
    """Réglages structurants d'une mission (valeurs), sans secret ni contenu utilisateur."""
    snapshot: dict[str, Any] = {}
    for name in MISSION_CONFIG_FIELDS:
        if is_secret_setting(name):
            continue
        if hasattr(settings, name):
            snapshot[name] = getattr(settings, name)
    # Constantes de pipeline qui bornent le comportement (importées localement : pas de cycle).
    from app.mission_budget import CALLS_PER_EXPERT, SYNTHESIS_CORE_CALLS, SYNTHESIS_RECOVERY_CALLS
    from app.mission_consolidation import (
        COMPARISON_MAX_FAMILIES,
        CONSOLIDATION_BATCH_SIZE,
        META_CHUNK_SIZE,
    )
    from app.mission_deliberation import STEELMAN_CLASSES

    snapshot["pipeline"] = {
        "calls_per_expert": CALLS_PER_EXPERT,
        "synthesis_core_calls": SYNTHESIS_CORE_CALLS,
        "synthesis_recovery_calls": SYNTHESIS_RECOVERY_CALLS,
        "comparison_max_families": COMPARISON_MAX_FAMILIES,
        "consolidation_batch_size": CONSOLIDATION_BATCH_SIZE,
        "meta_chunk_size": META_CHUNK_SIZE,
        "steelman_mandatory_classes": sorted(STEELMAN_CLASSES),
    }
    return snapshot


def compute_build_identity(
    settings: Any, *, probe: GitProbe | None = None, now: dt.datetime | None = None
) -> BuildIdentity:
    """Capture l'identité du build courant (à appeler à la création de chaque mission)."""
    g = probe or git_probe()
    config = mission_config_snapshot(settings)
    created = (now or dt.datetime.now(dt.UTC)).isoformat(timespec="seconds")
    return BuildIdentity(
        git_commit_full=g.commit,
        git_commit_short=g.commit[:7] if g.commit else None,
        git_dirty=g.dirty,
        git_identity_status=g.status,
        git_branch=g.branch,
        product_version=_distribution_version(PRODUCT_DISTRIBUTION),
        python_version=platform.python_version(),
        provider_adapter=PROVIDER_ADAPTER,
        provider_sdk_version=_distribution_version(PROVIDER_SDK_DISTRIBUTION),
        reasoning_policy_fingerprint=fingerprint(policy_table(settings)),
        mission_config_fingerprint=fingerprint(config),
        created_at=created,
        git_detail=g.detail,
        mission_config=config,
    )


def _normalize_sha(value: str) -> str:
    return (value or "").strip().lower()


def commits_match(running: str | None, expected: str) -> bool:
    """Un freeze attendu peut être donné en forme courte (≥ 7 caractères) ou complète."""
    exp = _normalize_sha(expected)
    run = _normalize_sha(running or "")
    if not exp or not run or len(exp) < 7:
        return False
    return run.startswith(exp) if len(exp) < len(run) else run == exp


def benchmark_check(identity: BuildIdentity, expected_freeze: str) -> dict[str, Any]:
    """Verdict de pré-vol : MATCH ou raison explicite de refus (fail closed)."""
    expected = _normalize_sha(expected_freeze)
    result: dict[str, Any] = {
        "expected_freeze": expected,
        "running_commit": identity.git_commit_full,
        "running_commit_short": identity.git_commit_short,
        "git_identity_status": identity.git_identity_status,
        "git_dirty": identity.git_dirty,
        "match": False,
        "reason": "",
    }
    if not expected:
        result["match"] = identity.git_identity_status == GIT_STATUS_OK
        result["reason"] = "" if result["match"] else BENCHMARK_BUILD_UNAVAILABLE
        result["verdict"] = "NO_EXPECTED_FREEZE"
        return result
    if identity.git_identity_status != GIT_STATUS_OK or not identity.git_commit_full:
        result["reason"] = BENCHMARK_BUILD_UNAVAILABLE
    elif not commits_match(identity.git_commit_full, expected):
        result["reason"] = BENCHMARK_BUILD_MISMATCH
    elif identity.git_dirty:
        result["reason"] = BENCHMARK_BUILD_DIRTY
    else:
        result["match"] = True
    result["verdict"] = "MATCH" if result["match"] else "MISMATCH"
    return result


class BenchmarkBuildError(Exception):
    """La mission ne peut pas démarrer en mode benchmark : le build n'est pas celui attendu."""

    def __init__(self, reason: str, check: dict[str, Any], identity: BuildIdentity) -> None:
        super().__init__(reason)
        self.reason = reason
        self.check = check
        self.identity = identity


def preflight(settings: Any, expected_freeze: str = "") -> dict[str, Any]:
    """Pré-vol benchmark : ce que l'opérateur doit voir AVANT de lancer un holdout."""
    identity = compute_build_identity(settings)
    check = benchmark_check(identity, expected_freeze)
    ceilings = {
        cls: {
            "max_llm_calls": getattr(settings, f"mission_ceiling_calls_{cls}", None),
            "max_cost_eur": getattr(settings, f"mission_ceiling_cost_{cls}", None),
        }
        for cls in ("courante", "importante", "structurante", "critique")
    }
    return {
        "running_commit": identity.git_commit_full,
        "running_commit_short": identity.git_commit_short,
        "git_branch": identity.git_branch,
        "git_dirty": identity.git_dirty,
        "git_identity_status": identity.git_identity_status,
        "git_detail": identity.git_detail,
        "expected_freeze": check["expected_freeze"],
        "verdict": check["verdict"],
        "reason": check["reason"],
        "provider_adapter": identity.provider_adapter,
        "provider_sdk_version": identity.provider_sdk_version,
        "product_version": identity.product_version,
        "python_version": identity.python_version,
        "reasoning_policy_fingerprint": identity.reasoning_policy_fingerprint,
        "mission_config_fingerprint": identity.mission_config_fingerprint,
        "reasoning_policy": policy_table(settings),
        "class_ceilings": ceilings,
        "benchmark_strict": bool(getattr(settings, "mission_benchmark_strict", False)),
        "build_label": identity.label,
        "checked_at": identity.created_at,
    }


def render_preflight(report: dict[str, Any]) -> str:
    """Rendu texte du pré-vol (commande `python -m app.preflight`)."""
    lines = [
        "AI-SOS — benchmark preflight",
        f"Running commit : {report['running_commit'] or '(indisponible)'}"
        + (f" ({report['git_branch']})" if report.get("git_branch") else ""),
        "Working tree   : "
        + (
            "UNAVAILABLE"
            if report["git_dirty"] is None
            else ("DIRTY" if report["git_dirty"] else "CLEAN")
        ),
        f"Expected freeze: {report['expected_freeze'] or '(aucun)'}",
        f"Verdict        : {report['verdict']}"
        + (f" — {report['reason']}" if report.get("reason") else ""),
        f"Provider       : {report['provider_adapter']} SDK {report['provider_sdk_version']}",
        f"Product        : {report['product_version']} (python {report['python_version']})",
        f"Reasoning policy fingerprint : {report['reasoning_policy_fingerprint']}",
        f"Mission config fingerprint   : {report['mission_config_fingerprint']}",
    ]
    for cls, caps in report["class_ceilings"].items():
        lines.append(
            f"Ceiling {cls:<12}: {caps['max_llm_calls']} appels / {caps['max_cost_eur']} EUR"
        )
    if report.get("git_detail"):
        lines.append(f"Git detail     : {report['git_detail']}")
    return "\n".join(lines)
