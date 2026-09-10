"""Orchestration d'une mission OT-V1 (incrément 1).

    Cadrage → Composition → Exploration indépendante (Tour 0) → Cartographie → Rapport de situation

Ce module fait les appels LLM (via le chemin structuré observé), tient le **budget** (plafonds
CEO : appels et euros, estimation avant chaque appel, arrêt propre), tient le **journal**
de la mission (prompts complets du Tour 0 avec empreinte, résultats, arrêts), et persiste les
artefacts. Il ne recommande rien, ne décide rien, n'exécute rien : le rapport reste `candidate`
jusqu'à une action CEO explicite.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import LLMCallLog, Mission, MissionJournalEntry
from app.llm import LLMClient, LLMResponse, LLMUsage
from app.mission_budget import (
    CALLS_PER_EXPERT,
    SYNTHESIS_CORE_CALLS,
    BudgetExceededError,
    BudgetLedger,
    feasible_expert_count,
    mandatory_steelman_calls,
    minimal_deliberation_bound,
    plan_budget,
)
from app.mission_cartography import (
    anonymize_labels,
    build_cartography,
    collect_options,
    relations_table,
    residual_ambiguities,
)
from app.mission_composition import ExpertSpec, compose
from app.mission_consolidation import (
    COMPARISON_MAX_FAMILIES,
    CONSOLIDATION_BATCH_SIZE,
    META_CHUNK_SIZE,
    build_batch_prompt,
    build_compact_comparison_prompt,
    build_meta_prompt,
    coverage_requirements,
    direct_family,
    families_from_batch,
    finalize_families,
    merge_families_from_meta,
    plan_batches,
    plan_consolidation,
    premerge_options,
    select_families_for_attempt,
)
from app.mission_deliberation import (
    COMPARISON_CALL_TYPE,
    COMPARISON_SYSTEM,
    CONFRONTATION_CALL_TYPE,
    CONFRONTATION_SYSTEM,
    CONSOLIDATION_CALL_TYPE,
    CONSOLIDATION_SYSTEM,
    CRITICAL_ANGLE_TITLES,
    GATE_CALL_TYPE,
    GATE_SYSTEM,
    RECOGNITION_CALL_TYPE,
    RECOGNITION_SYSTEM,
    REVISION_CALL_TYPE,
    REVISION_SYSTEM,
    STEELMAN_CALL_TYPE,
    STEELMAN_CLASSES,
    STEELMAN_SYSTEM,
    SYNTHESIS_CALL_TYPE,
    SYNTHESIS_SYSTEM,
    build_confrontation_prompt,
    build_gate_prompt,
    build_map_view,
    build_recognition_prompt,
    build_revision_prompt,
    build_steelman_prompt,
    build_synthesis_prompt,
    epistemic_tag,
    is_premature_convergence,
    material_fact_questions,
    select_contradictor,
    strawman_flags,
)
from app.mission_exploration import (
    CLERK_CALL_TYPE,
    CLERK_SYSTEM,
    EXPERT_CALL_TYPE,
    EXPERT_SYSTEM,
    SELF_QUAL_CALL_TYPE,
    SELF_QUAL_SYSTEM,
    build_clerk_prompt,
    build_expert_prompt,
    build_self_qualification_prompt,
    prompt_fingerprint,
)
from app.mission_framing import (
    FRAMING_CALL_TYPE,
    FRAMING_SYSTEM,
    build_framing_prompt,
    framing_summary_for_experts,
)
from app.mission_report import build_situation_report
from app.mission_research import (
    RESEARCH_CALL_TYPE,
    build_research_provider,
    classify_research_outcome,
)
from app.mission_schemas import (
    ClerkOutput,
    ComparisonOutput,
    ConfrontationOutput,
    ConsolidationOutput,
    ExpertOutput,
    FramingOutput,
    GateOutput,
    RecognitionOutput,
    RecommendationOutput,
    RevisionOutput,
    SelfQualificationOutput,
    SteelmanOutput,
)
from app.observability import observed
from app.output_budget import (
    RULES as OUTPUT_BUDGET_RULES,
)
from app.output_budget import (
    OutputBudget,
    fixed_output_budget,
    output_budget,
    plan_truncation_retry,
)
from app.provider_errors import (
    COST_KNOWN,
    COST_KNOWN_ZERO,
    COST_UNCERTAIN,
    LOCAL_ERROR,
    PERMANENT_PROVIDER_ERROR,
    TRANSIENT_PROVIDER_ERROR,
    ProviderErrorInfo,
    classify_provider_error,
    retry_delay_seconds,
)
from app.schemas import MissionCreateRequest
from app.structured_output import (
    MAX_STRUCTURED_RETRIES_PER_CALL,
    STRUCTURED_OUTPUT_RECOVERY_EXHAUSTED,
    STRUCTURED_OUTPUT_RETRY_REFUSED_BUDGET,
    analyze_structured_output,
    build_correction_block,
)

# Attente entre deux tentatives fournisseur : remplaçable en test (aucun vrai sommeil).
provider_sleep: Callable[[float], None] = time.sleep


class MissionCallFailedError(Exception):
    """Un appel logique a échoué définitivement (relances épuisées ou erreur non relançable)."""

    def __init__(self, failure: dict[str, Any]) -> None:
        super().__init__(failure.get("reason", "call_failed"))
        self.failure = failure


PHASE = "otv1_inc1"
PROVISIONAL_CLASS = "importante_provisoire"
CLASS_RANK = {
    "courante": 0,
    "importante": 1,
    PROVISIONAL_CLASS: 1,
    "structurante": 2,
    "critique": 3,
}
# Escalade par défaut d'un rang quand le cadrage signale un risque sans proposer de classe.
NEXT_CLASS = {
    "courante": "importante",
    "importante": "structurante",
    PROVISIONAL_CLASS: "structurante",
    "structurante": "critique",
    "critique": "critique",
}
CEO_ACTIONS = {
    "approve": "approved",
    "request_revision": "revision_requested",
    "reject": "rejected",
}


class MissionNotFoundError(Exception):
    """Mission introuvable."""


class InvalidMissionStatusError(Exception):
    """Action CEO impossible dans le statut courant."""


@dataclass
class _Run:
    """État de travail d'une mission en cours d'exécution (non persisté tel quel)."""

    mission: Mission
    ledger: BudgetLedger
    seq: int = 0
    framing: FramingOutput | None = None
    framing_error: str = ""
    composition: dict[str, Any] = field(default_factory=dict)
    experts: list[ExpertSpec] = field(default_factory=list)
    expert_results: list[dict[str, Any]] = field(default_factory=list)
    self_qual: dict[str, SelfQualificationOutput | None] = field(default_factory=dict)
    clerk: ClerkOutput | None = None
    stop_reason: str = ""
    budget_source: str = "class_ceiling"
    cartography: dict[str, Any] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)
    confrontations: dict[str, ConfrontationOutput | None] = field(default_factory=dict)
    objections: list[dict[str, Any]] = field(default_factory=list)
    steelman: dict[str, Any] = field(default_factory=dict)
    research: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    revisions: list[dict[str, Any]] = field(default_factory=list)
    current_positions: dict[str, str] = field(default_factory=dict)
    consolidation: dict[str, Any] = field(default_factory=dict)
    comparison: dict[str, Any] = field(default_factory=dict)
    recommendation: dict[str, Any] = field(default_factory=dict)
    gate: dict[str, Any] = field(default_factory=dict)
    steps_done: list[str] = field(default_factory=list)
    steps_skipped: list[dict[str, str]] = field(default_factory=list)
    budget_request: dict[str, Any] = field(default_factory=dict)
    # Cœur de synthèse effectif : consolidation (lots planifiés) + comparaison + synthèse + porte.
    core_calls: int = SYNTHESIS_CORE_CALLS
    # Pire cas borné du cœur : nominal + relances autorisées (une par lot, une pour la
    # comparaison). Les étapes optionnelles ne sont financées qu'au-delà de ce pire cas.
    core_worst_calls: int = SYNTHESIS_CORE_CALLS + 1
    core_plan: dict[str, int] = field(default_factory=dict)
    # B10 — comptabilité des tentatives fournisseur, distincte des appels logiques du registre :
    # `llm_calls_used` compte les appels logiques réussis ; les tentatives physiques, relances et
    # échecs sont comptés ici et journalisés par tentative.
    logical_calls: int = 0
    provider_attempts: int = 0
    provider_retries: int = 0
    provider_failures: int = 0
    # B13 — couche de sortie structurée (après réponse fournisseur) : réponses invalides,
    # récupérations locales appliquées, relances correctives LLM (chacune est un appel logique
    # réel, visible dans `llm_calls_used`), épuisements.
    structured_output_failures: int = 0
    structured_output_recoveries: int = 0
    structured_output_retries: int = 0
    structured_output_exhausted: int = 0
    # B14-prime (O3) — réserve du cycle minimal de délibération, calculée dès la clôture du Tour 0
    # (confrontations + cœur réel + steelman obligatoire de la classe) et opposable aux dépenses
    # pré-délibération restantes (auto-qualification, greffier, relances correctives).
    deliberation_reserve: int | None = None
    deliberation_plan: dict[str, Any] = field(default_factory=dict)
    failure: dict[str, Any] = field(default_factory=dict)


def _journal(
    session: Session, run: _Run, step: str, entry_type: str, actor: str, payload: dict[str, Any]
) -> None:
    run.seq += 1
    session.add(
        MissionJournalEntry(
            mission_id=run.mission.id,
            seq=run.seq,
            step=step,
            entry_type=entry_type,
            actor=actor,
            payload_json=json.dumps(payload, ensure_ascii=False, default=str),
        )
    )
    session.commit()


def _sync_budget(session: Session, run: _Run) -> None:
    m = run.mission
    m.llm_calls_used = run.ledger.calls_used
    m.input_tokens = run.ledger.input_tokens
    m.output_tokens = run.ledger.output_tokens
    m.cost_eur = run.ledger.cost_eur
    session.commit()


def _call(
    session: Session,
    run: _Run,
    llm: LLMClient,
    settings: Settings,
    *,
    step: str,
    actor: str,
    system: str,
    prompt: str,
    call_type: str,
    max_tokens: int,
    planned_extra: dict[str, Any] | None = None,
) -> LLMResponse | None:
    """Appel structuré sous budget : estimation, refus/arrêt, appel, enregistrement, journal.

    Retourne None si le budget interdit l'appel (la mission s'arrête proprement : `stop_reason`).
    `planned_extra` : métadonnées ajoutées à `call_planned` (budget de sortie dérivé, B14-prime).
    """
    try:
        estimate = run.ledger.check_before_call(
            system=system, prompt=prompt, max_tokens=max_tokens, call_type=call_type
        )
    except BudgetExceededError as exc:
        run.stop_reason = exc.reason
        _journal(
            session,
            run,
            step,
            "budget_stop",
            "facilitateur",
            {"reason": exc.reason, **exc.detail, "budget": run.ledger.snapshot()},
        )
        return None
    _journal(
        session,
        run,
        step,
        "call_planned",
        actor,
        {
            "call_type": call_type,
            "max_tokens": max_tokens,
            "estimated_cost_eur_upper_bound": estimate,
            "prompt_sha256": prompt_fingerprint(system, prompt),
            "prompt_text": prompt,
            "system_text": system,
            **(planned_extra or {}),
        },
    )
    client = observed(
        llm,
        session,
        PHASE,
        actor,
        call_type,
        settings.anthropic_model,
        mission_id=run.mission.id,
        price_in_per_mtok=settings.llm_price_input_eur_per_mtok,
        price_out_per_mtok=settings.llm_price_output_eur_per_mtok,
    )
    response, attempt = _call_with_retries(
        session,
        run,
        settings,
        client=client,
        step=step,
        actor=actor,
        system=system,
        prompt=prompt,
        call_type=call_type,
        max_tokens=max_tokens,
        estimated_cost_eur=estimate,
    )
    cost = run.ledger.record(response.usage)
    _sync_budget(session, run)
    _journal(
        session,
        run,
        step,
        "call_done",
        actor,
        {
            "call_type": call_type,
            "logical_call_id": f"LC-{run.logical_calls}",
            "attempt_number": attempt,
            "recovered_after_retries": attempt - 1,
            "provider": "anthropic",
            "model": settings.anthropic_model,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "max_tokens": max_tokens,
            "stop_reason": response.stop_reason,
            "truncated": response.truncated,
            "raw_length_chars": len(response.text),
            **_content_block_view(response),
            "cost_eur": cost,
            "budget": run.ledger.snapshot(),
        },
    )
    return response


def _call_with_retries(
    session: Session,
    run: _Run,
    settings: Settings,
    *,
    client: Any,
    step: str,
    actor: str,
    system: str,
    prompt: str,
    call_type: str,
    max_tokens: int,
    estimated_cost_eur: float,
) -> tuple[LLMResponse, int]:
    """Tentatives physiques bornées d'UN appel logique déjà admis par le budget (B10, B12).

    Une erreur classée transitoire est relancée avec attente exponentielle bornée (ou `Retry-After`
    plafonné), au plus `mission_provider_max_attempts` tentatives par appel logique et
    `mission_provider_max_retries_total` relances par mission ; une erreur permanente, locale ou
    inconnue n'est jamais relancée. Chaque tentative est journalisée (`call_attempt_failed`) et
    tracée dans `llm_call_logs` par le client observé. Les tentatives échouées ne consomment aucun
    appel logique : les réserves en appels des étapes obligatoires (B8) restent intactes.

    Coût des tentatives échouées (B12) : un rejet explicite avant traitement (`known_zero`) ne
    coûte rien ; un échec ambigu (`uncertain` : délai, coupure, 500/502/504, inconnu) ajoute la
    borne pré-appel `estimated_cost_eur` à l'exposition potentielle du registre ; un usage réel
    exposé par l'exception (`known`) est compté en coût connu. Une relance n'est admise que si
    connu + incertain + `estimated_cost_eur` ≤ `max_cost_eur` (sinon
    `retry_refused_uncertain_cost_budget`, fail-closed). L'exposition reste ensuite déduite du
    plafond pour tous les appels suivants, obligatoires compris. Côté mission, un seul résultat
    logique est enregistré, quel que soit le nombre de tentatives.
    """
    run.logical_calls += 1
    logical_call_id = f"LC-{run.logical_calls}"
    max_attempts = max(1, settings.mission_provider_max_attempts)
    attempt = 0
    while True:
        attempt += 1
        run.provider_attempts += 1
        try:
            response: LLMResponse = client.complete_structured(
                system=system, prompt=prompt, call_type=call_type, max_tokens=max_tokens
            )
            return response, attempt
        except Exception as exc:
            info = classify_provider_error(exc)
            run.provider_failures += 1
            attempt_cost = _account_failed_attempt(
                run,
                info,
                estimated_cost_eur=estimated_cost_eur,
                call_type=call_type,
                logical_call_id=logical_call_id,
                attempt=attempt,
            )
            _sync_budget(session, run)
            total_cap_reached = run.provider_retries >= settings.mission_provider_max_retries_total
            cost_allows = run.ledger.retry_allowed_by_cost(estimated_cost_eur)
            otherwise_allowed = info.retryable and attempt < max_attempts and not total_cap_reached
            can_retry = otherwise_allowed and cost_allows
            if can_retry:
                refusal_reason = ""
            elif not info.retryable:
                refusal_reason = "not_retryable"
            elif attempt >= max_attempts:
                refusal_reason = "max_attempts_reached"
            elif total_cap_reached:
                refusal_reason = "total_retry_cap_reached"
            else:
                refusal_reason = "retry_refused_uncertain_cost_budget"
            cost_view = {
                **attempt_cost,
                "known_cost_eur": run.ledger.known_cost_eur,
                "uncertain_cost_upper_bound_eur": round(
                    run.ledger.uncertain_cost_upper_bound_eur, 6
                ),
                "potential_total_cost_upper_bound_eur": (
                    run.ledger.potential_total_cost_upper_bound_eur
                ),
                "estimated_retry_cost_eur": estimated_cost_eur,
                "max_cost_eur": run.ledger.max_cost_eur,
                "retry_allowed_by_cost": cost_allows,
                "retry_refusal_reason": refusal_reason,
            }
            delay = (
                retry_delay_seconds(
                    attempt,
                    info,
                    base=settings.mission_provider_backoff_base_seconds,
                    cap=settings.mission_provider_backoff_cap_seconds,
                    retry_after_cap=settings.mission_provider_retry_after_cap_seconds,
                )
                if can_retry
                else None
            )
            _journal(
                session,
                run,
                step,
                "call_attempt_failed",
                actor,
                {
                    "logical_call_id": logical_call_id,
                    "call_type": call_type,
                    "provider": "anthropic",
                    "model": settings.anthropic_model,
                    "attempt_number": attempt,
                    "max_attempts": max_attempts,
                    "status": "error",
                    **info.to_dict(),
                    "will_retry": can_retry,
                    "retry_delay_seconds": delay,
                    "retries_total_used": run.provider_retries,
                    "retries_total_max": settings.mission_provider_max_retries_total,
                    **cost_view,
                    "budget": run.ledger.snapshot(),
                },
            )
            if can_retry and delay is not None:
                run.provider_retries += 1
                provider_sleep(delay)
                continue
            if refusal_reason == "retry_refused_uncertain_cost_budget":
                reason = refusal_reason
            elif info.category == TRANSIENT_PROVIDER_ERROR:
                reason = "transient_retries_exhausted"
            elif info.category == PERMANENT_PROVIDER_ERROR:
                reason = "permanent_provider_error"
            elif info.category == LOCAL_ERROR:
                reason = "local_error"
            else:
                reason = "unknown_error"
            failure = {
                "reason": reason,
                "step": step,
                "actor": actor,
                "call_type": call_type,
                "logical_call_id": logical_call_id,
                "provider": "anthropic",
                "model": settings.anthropic_model,
                "attempts": attempt,
                "max_attempts": max_attempts,
                "retries_total_used": run.provider_retries,
                "retries_total_max": settings.mission_provider_max_retries_total,
                "total_retry_cap_reached": total_cap_reached and info.retryable,
                **info.to_dict(),
                **cost_view,
            }
            raise MissionCallFailedError(failure) from exc


def _account_failed_attempt(
    run: _Run,
    info: ProviderErrorInfo,
    *,
    estimated_cost_eur: float,
    call_type: str,
    logical_call_id: str,
    attempt: int,
) -> dict[str, Any]:
    """Comptabilité financière d'une tentative échouée selon sa sémantique de coût (B12)."""
    if info.cost_semantics == COST_KNOWN and info.usage_input_tokens is not None:
        usage = LLMUsage(
            input_tokens=int(info.usage_input_tokens),
            output_tokens=int(info.usage_output_tokens or 0),
        )
        return {
            "cost_semantics": COST_KNOWN,
            "attempt_known_cost_eur": run.ledger.record_failed_attempt_usage(usage),
            "attempt_uncertain_upper_bound_eur": 0.0,
        }
    if info.cost_semantics == COST_UNCERTAIN:
        exposure = run.ledger.record_uncertain_attempt(
            estimated_cost_eur,
            call_type=call_type,
            logical_call_id=logical_call_id,
            attempt=attempt,
        )
        return {
            "cost_semantics": COST_UNCERTAIN,
            "attempt_known_cost_eur": 0.0,
            "attempt_uncertain_upper_bound_eur": exposure["upper_bound_eur"],
            "exposure_id": exposure["id"],
        }
    return {
        "cost_semantics": COST_KNOWN_ZERO,
        "attempt_known_cost_eur": 0.0,
        "attempt_uncertain_upper_bound_eur": 0.0,
    }


def _content_block_view(response: LLMResponse) -> dict[str, Any]:
    """Métadonnées des blocs de sortie (B14-prime — D) : types, comptes, texte retenu, ratio.

    Aucun contenu de bloc non textuel n'est journalisé. Le ratio tokens de sortie / caractères de
    texte est une mesure brute, sans interprétation sémantique.
    """
    blocks = response.content_blocks
    text_chars = len(response.text)
    out = response.usage.output_tokens
    if blocks is None:
        text_blocks: int | None = None
        non_text: int | None = None
    else:
        text_blocks = blocks.get("text", 0)
        non_text = sum(v for k, v in blocks.items() if k != "text")
    return {
        "content_blocks": blocks if blocks is not None else "unknown",
        "content_blocks_total": None if blocks is None else sum(blocks.values()),
        "text_blocks": text_blocks,
        "non_text_blocks": non_text,
        "text_chars": text_chars,
        "output_tokens_per_text_char": (
            round(out / text_chars, 3) if text_chars else ("n/a" if out == 0 else "no_text")
        ),
    }


# --- B13 — appel structuré : analyse, récupération locale, relance corrective bornée ------------
# Réserve d'appels exigée avant une relance corrective, par étape (B8, B14-prime) : après la
# clôture du
# Tour 0, la réserve du cycle minimal de délibération (confrontations + cœur réel + steelman
# obligatoire) est opposable ; avant, les étapes préalables exigent que le pire cas du cœur reste
# finançable ; le cadrage n'exige rien (sans cadrage, rien n'existe) ; la synthèse réserve la
# porte ; la porte ne réserve rien. La consolidation et la comparaison possèdent déjà une relance
# bornée propre (lot scindé, compaction) : la relance B13 y est désactivée (récupération locale
# seulement) pour ne pas dépasser le pire cas réservé.
_STRUCTURED_RETRY_DISABLED_STEPS = frozenset({"consolidation", "comparaison"})
_PRE_DELIBERATION_STEPS = frozenset({"tour0", "auto_qualification", "greffier"})
RETRY_REFUSED_DELIBERATION_RESERVE = "structured_output_retry_refused_deliberation_reserve"


def _structured_retry_reserve(run: _Run, step: str) -> tuple[int, str]:
    """(réserve exigée, nom de la réserve) pour une relance corrective à cette étape."""
    if step == "cadrage":
        return 0, "none"
    if step == "synthese":
        return 1, "quality_gate"
    if step == "porte_qualite":
        return 0, "none"
    if step in _PRE_DELIBERATION_STEPS and run.deliberation_reserve is not None:
        return run.deliberation_reserve, "deliberation_reserve"
    return run.core_worst_calls, "core_worst_case"


def _output_budget_for(settings: Settings, call_type: str, n_items: int | None) -> OutputBudget:
    """Limite de sortie d'un appel : formule proportionnée (O1) ou limite fixe de l'étape."""
    floor = int(getattr(settings, f"mission_max_tokens_{_SETTING_SUFFIX[call_type]}"))
    if n_items is None or call_type not in OUTPUT_BUDGET_RULES:
        return fixed_output_budget(call_type, floor)
    ceiling = int(getattr(settings, f"mission_output_ceiling_{_SETTING_SUFFIX[call_type]}"))
    return output_budget(call_type, n_items, floor=floor, ceiling=ceiling)


_SETTING_SUFFIX = {
    "framing": "framing",
    "expert_tour0": "expert",
    "self_qualification": "self_qualification",
    "clerk": "clerk",
    "confrontation": "confrontation",
    "steelman": "steelman",
    "steelman_recognition": "recognition",
    "revision": "revision",
    "consolidation": "consolidation",
    "comparison": "comparison",
    "synthesis": "synthesis",
    "quality_gate": "gate",
}


def _call_structured[T: BaseModel](
    session: Session,
    run: _Run,
    llm: LLMClient,
    settings: Settings,
    *,
    step: str,
    actor: str,
    system: str,
    prompt: str,
    call_type: str,
    model: type[T],
    n_items: int | None = None,
) -> tuple[LLMResponse | None, T | None, str]:
    """Appel LLM dont la réponse doit satisfaire un contrat de sortie (B13, B14-prime).

    Retourne (dernière réponse, sortie validée ou None, erreur classée). Chemin : limite de sortie
    proportionnée à la tâche (O1, `n_items`) ou fixe → appel sous budget (B10 / B12 à l'intérieur)
    → analyse (`analyze_structured_output` : récupération locale déterministe de l'enveloppe,
    parsing, validation stricte) → si invalide et finançable, **une** relance corrective ciblée sur
    le contrat (nouvel appel logique, même schéma) → si toujours invalide,
    `structured_output_recovery_exhausted`.

    Relance après troncature (F) : jamais à l'identique ; seulement avec une limite
    déterministement suffisante (extrapolation sur les éléments complets observés, ou plafond de
    l'étape), sinon `structured_output_retry_refused_output_budget`. Une relance qui entamerait la
    réserve du cycle minimal de délibération (O3) est refusée :
    `structured_output_retry_refused_deliberation_reserve`. Une relance non finançable (appels,
    coût connu + exposition incertaine) est refusée : `structured_output_retry_refused_budget`.
    Une étape logique n'accepte jamais plus d'un résultat ; toutes les tentatives sont
    journalisées.
    """
    budget = _output_budget_for(settings, call_type, n_items)
    max_tokens = budget.granted
    response = _call(
        session,
        run,
        llm,
        settings,
        step=step,
        actor=actor,
        system=system,
        prompt=prompt,
        call_type=call_type,
        max_tokens=max_tokens,
        planned_extra={
            "output_budget": budget.to_dict(),
            "number_of_required_items": budget.n_items,
            "deliberation_reserve": run.deliberation_reserve,
        },
    )
    if response is None:
        return None, None, ""
    outcome = analyze_structured_output(response, model)
    logical_call_id = f"LC-{run.logical_calls}"
    if outcome.recovery.applied:
        run.structured_output_recoveries += 1
        _journal(
            session,
            run,
            step,
            "structured_output_recovered",
            actor,
            {
                "logical_call_id": logical_call_id,
                "call_type": call_type,
                "valid_after_recovery": outcome.valid,
                **outcome.to_journal(),
            },
        )
    if outcome.valid:
        return response, outcome.output, ""
    run.structured_output_failures += 1
    error = f"{outcome.category}: {outcome.error}"
    # Relance après troncature (F) : limite déterministement suffisante ou refus ; sinon (syntaxe,
    # schéma, réponse vide à raison d'arrêt normale) : relance corrective à la même limite.
    retry_max_tokens = max_tokens
    truncation_plan = None
    if outcome.truncated:
        truncation_plan = plan_truncation_retry(
            budget, output_tokens=response.usage.output_tokens, raw_text=response.text
        )
        retry_max_tokens = truncation_plan.max_tokens
    retry_prompt = (
        prompt
        + "\n\n"
        + build_correction_block(
            model, outcome, max_tokens=max_tokens, output_tokens=response.usage.output_tokens
        )
    )
    estimate = run.ledger.estimate_call_cost_eur(system, retry_prompt, retry_max_tokens)
    reserve, reserve_name = _structured_retry_reserve(run, step)
    refusal = ""
    if step in _STRUCTURED_RETRY_DISABLED_STEPS:
        refusal = "step_has_own_bounded_retry"
    elif run.stop_reason:
        refusal = f"mission_stopping:{run.stop_reason}"
    elif truncation_plan is not None and not truncation_plan.allowed:
        refusal = truncation_plan.reason
    elif run.ledger.remaining_calls - 1 < reserve:
        refusal = (
            RETRY_REFUSED_DELIBERATION_RESERVE
            if reserve_name == "deliberation_reserve"
            else STRUCTURED_OUTPUT_RETRY_REFUSED_BUDGET
        )
    elif not run.ledger.retry_allowed_by_cost(estimate):
        refusal = STRUCTURED_OUTPUT_RETRY_REFUSED_BUDGET
    will_retry = refusal == ""
    _journal(
        session,
        run,
        step,
        "structured_output_invalid",
        actor,
        {
            "logical_call_id": logical_call_id,
            "call_type": call_type,
            "provider": "anthropic",
            "model": settings.anthropic_model,
            "structured_attempt": 1,
            "max_structured_retries": MAX_STRUCTURED_RETRIES_PER_CALL,
            **outcome.to_journal(),
            "output_tokens": response.usage.output_tokens,
            "max_tokens": max_tokens,
            "output_budget": budget.to_dict(),
            "stop_reason": response.stop_reason,
            **_content_block_view(response),
            "truncation_retry_plan": (
                truncation_plan.to_dict() if truncation_plan is not None else None
            ),
            "retry_requested": True,
            "will_retry": will_retry,
            "retry_allowed": will_retry,
            "retry_max_tokens": retry_max_tokens if will_retry else None,
            "retry_refusal_reason": refusal,
            "estimated_retry_cost_eur": estimate,
            "remaining_calls": run.ledger.remaining_calls,
            "reserved_calls_for_step": reserve,
            "reserve_kind": reserve_name,
            "deliberation_reserve_before": run.deliberation_reserve,
            "deliberation_reserve_after": run.deliberation_reserve,
            "known_cost_eur": run.ledger.known_cost_eur,
            "uncertain_cost_upper_bound_eur": round(run.ledger.uncertain_cost_upper_bound_eur, 6),
            "potential_total_cost_upper_bound_eur": (
                run.ledger.potential_total_cost_upper_bound_eur
            ),
            "max_cost_eur": run.ledger.max_cost_eur,
            "budget": run.ledger.snapshot(),
        },
    )
    if not will_retry:
        if refusal in (
            STRUCTURED_OUTPUT_RETRY_REFUSED_BUDGET,
            RETRY_REFUSED_DELIBERATION_RESERVE,
            "structured_output_retry_refused_output_budget",
        ):
            prefix = refusal
        else:
            prefix = "structured_output_not_retried"
        return response, None, f"{prefix}: {error}"
    run.structured_output_retries += 1
    _journal(
        session,
        run,
        step,
        "structured_output_retry_planned",
        actor,
        {
            "original_logical_call_id": logical_call_id,
            "structured_retry_number": run.structured_output_retries,
            "category": outcome.category,
            "estimated_cost_eur": estimate,
            "max_tokens": retry_max_tokens,
            "max_tokens_initial": max_tokens,
        },
    )
    retry_response = _call(
        session,
        run,
        llm,
        settings,
        step=step,
        actor=actor,
        system=system,
        prompt=retry_prompt,
        call_type=call_type,
        max_tokens=retry_max_tokens,
        planned_extra={
            "output_budget": budget.to_dict(),
            "number_of_required_items": budget.n_items,
            "structured_retry_of": logical_call_id,
            "max_tokens_initial": max_tokens,
            "deliberation_reserve": run.deliberation_reserve,
        },
    )
    if retry_response is None:
        # Refus du registre au moment de l'appel : même sémantique fail-closed.
        return response, None, f"{STRUCTURED_OUTPUT_RETRY_REFUSED_BUDGET}: {error}"
    retry_outcome = analyze_structured_output(retry_response, model)
    retry_logical_call_id = f"LC-{run.logical_calls}"
    if retry_outcome.recovery.applied:
        run.structured_output_recoveries += 1
    if not retry_outcome.valid:
        run.structured_output_failures += 1
        run.structured_output_exhausted += 1
    _journal(
        session,
        run,
        step,
        "structured_output_retry_result",
        actor,
        {
            "original_logical_call_id": logical_call_id,
            "logical_call_id": retry_logical_call_id,
            "call_type": call_type,
            "structured_attempt": 2,
            "valid": retry_outcome.valid,
            "final": ("accepted" if retry_outcome.valid else STRUCTURED_OUTPUT_RECOVERY_EXHAUSTED),
            **retry_outcome.to_journal(),
            "output_tokens": retry_response.usage.output_tokens,
            "max_tokens": retry_max_tokens,
            "stop_reason": retry_response.stop_reason,
            **_content_block_view(retry_response),
            "budget": run.ledger.snapshot(),
        },
    )
    if retry_outcome.valid:
        return retry_response, retry_outcome.output, ""
    return (
        retry_response,
        None,
        f"{STRUCTURED_OUTPUT_RECOVERY_EXHAUSTED}: {retry_outcome.category}: {retry_outcome.error}",
    )


def _structured_failure(
    run: _Run,
    settings: Settings,
    *,
    step: str,
    actor: str,
    call_type: str,
    error: str,
) -> dict[str, Any]:
    """Échec structuré terminal d'une étape sans laquelle la mission ne peut exister (cadrage)."""
    refusal_prefixes = (
        STRUCTURED_OUTPUT_RETRY_REFUSED_BUDGET,
        RETRY_REFUSED_DELIBERATION_RESERVE,
        "structured_output_retry_refused_output_budget",
    )
    refused_as = next((r for r in refusal_prefixes if error.startswith(r)), "")
    refused = bool(refused_as)
    reason = refused_as or STRUCTURED_OUTPUT_RECOVERY_EXHAUSTED
    # `error` = "<raison>: <catégorie>: <détail>" ; la catégorie est le second segment.
    parts = error.split(": ", 2)
    category = parts[1] if len(parts) >= 2 else ""
    detail = parts[2] if len(parts) == 3 else error
    return {
        "reason": reason,
        "kind": "structured_output",
        "step": step,
        "actor": actor,
        "call_type": call_type,
        "logical_call_id": f"LC-{run.logical_calls}",
        "provider": "anthropic",
        "model": settings.anthropic_model,
        "attempts": 1 if refused else 1 + MAX_STRUCTURED_RETRIES_PER_CALL,
        "max_attempts": 1 + MAX_STRUCTURED_RETRIES_PER_CALL,
        "category": category,
        "error_category": category,
        "retryable": False,
        "message": detail[:300],
        "structured_output_retries": run.structured_output_retries,
    }


def _escalate_class(session: Session, run: _Run) -> dict[str, Any]:
    """Applique ou consigne l'escalade de classe suggérée par le cadrage."""
    m = run.mission
    info: dict[str, Any] = {
        "declared": m.declared_class,
        "effective": m.effective_class,
        "provisional": m.class_is_provisional,
        "escalation": "",
    }
    if run.framing is None:
        return info
    suggested: str = run.framing.suggested_class
    signals = list(run.framing.escalation_signals)
    if not suggested and not signals:
        return info
    current_rank = CLASS_RANK.get(m.effective_class, 1)
    default_used = False
    if signals and not suggested:
        # Contrat d'escalade : des signaux substantiels sans classe suggérée exploitable ne
        # peuvent pas laisser la classe inchangée « faute d'un champ facultatif ». Escalade d'un
        # rang par défaut (appliquée si la classe est provisoire, soumise au CEO sinon).
        suggested = NEXT_CLASS.get(m.effective_class, "structurante")
        default_used = True
    suffix = (
        " (escalade par défaut d'un rang : signaux substantiels sans classe suggérée exploitable)"
        if default_used
        else ""
    )
    suggested_rank = CLASS_RANK.get(suggested, -1)
    if suggested_rank > current_rank:
        if m.class_is_provisional:
            m.effective_class = suggested
            session.commit()
            info["effective"] = suggested
            info["escalation"] = (
                f"classe provisoire escaladée à « {suggested} » par le cadrage{suffix}"
            )
        else:
            info["escalation"] = (
                f"le cadrage recommande « {suggested} »{suffix} ; la classe déclarée par le CEO "
                f"(« {m.declared_class} ») est conservée — escalade soumise au CEO"
            )
    elif signals:
        info["escalation"] = (
            "signaux d'escalade consignés ; la classe en vigueur est déjà au moins égale à la "
            "classe suggérée"
        )
    info["suggested_class_missing"] = run.framing.suggested_class_missing
    _journal(
        session,
        run,
        "cadrage",
        "class_escalation",
        "facilitateur",
        {
            **info,
            "signals": signals,
            "suggested_class": run.framing.suggested_class,
            "applied_suggestion": suggested,
            "default_escalation_used": default_used,
        },
    )
    return info


def run_mission(
    session: Session, llm: LLMClient, request: MissionCreateRequest, settings: Settings
) -> Mission:
    """Crée et exécute une mission de cadrage sous budget ; retourne la mission `candidate`."""
    declared = request.declared_class or ""
    mission = Mission(
        input_type=request.input_type,
        input_text=request.input_text,
        context_text=request.context_text,
        ceo_preference=request.ceo_preference,
        declared_class=declared,
        effective_class=declared or PROVISIONAL_CLASS,
        class_is_provisional=not declared,
        status="running",
    )
    planned_calls, planned_cost, budget_source = plan_budget(
        effective_class=mission.effective_class,
        settings=settings,
        override_calls=request.max_llm_calls,
        override_cost=request.max_cost_eur,
    )
    mission.max_llm_calls = planned_calls
    mission.max_cost_eur = planned_cost
    session.add(mission)
    session.commit()
    session.refresh(mission)
    run = _Run(
        mission=mission,
        ledger=BudgetLedger(
            max_calls=mission.max_llm_calls,
            max_cost_eur=mission.max_cost_eur,
            price_in_per_mtok=settings.llm_price_input_eur_per_mtok,
            price_out_per_mtok=settings.llm_price_output_eur_per_mtok,
        ),
        budget_source=budget_source,
    )
    _journal(
        session,
        run,
        "mission",
        "created",
        "ceo",
        {
            "input_type": mission.input_type,
            "effective_class": mission.effective_class,
            "class_is_provisional": mission.class_is_provisional,
            "budget_source": budget_source,
            "budget": run.ledger.snapshot(),
        },
    )
    class_info: dict[str, Any] = {
        "declared": mission.declared_class,
        "effective": mission.effective_class,
        "provisional": mission.class_is_provisional,
        "escalation": "",
    }
    try:
        try:
            _run_pipeline(session, run, llm, settings, class_info)
        except MissionCallFailedError as exc:
            # B10 — échec définitif d'un appel fournisseur : état terminal explicite, données
            # déjà produites conservées, rapport diagnostic partiel, aucune recommandation.
            _fail_mission(session, run, exc.failure)
    except Exception as exc:
        mission.status = "failed"
        mission.stop_reason = f"{type(exc).__name__}: {str(exc)[:200]}"
        run.failure = run.failure or {
            "reason": "local_error",
            "step": "mission",
            "error_category": LOCAL_ERROR,
            "exception_type": type(exc).__name__,
            "message": str(exc)[:300],
        }
        mission.failure_json = json.dumps(run.failure, ensure_ascii=False, default=str)
        session.commit()
        _journal(session, run, "mission", "failed", "facilitateur", {"error": mission.stop_reason})
        raise
    return mission


def _run_pipeline(
    session: Session, run: _Run, llm: LLMClient, settings: Settings, class_info: dict[str, Any]
) -> None:
    """Enchaînement complet d'une mission (cadrage → … → porte), puis finalisation."""
    _step_framing(session, run, llm, settings)
    class_info.update(_escalate_class(session, run))
    _apply_budget_plan_after_escalation(session, run, settings)
    if run.framing is None:
        # Arrêt réel : sans cadrage valide (panne de parsing ou appel refusé par le budget),
        # aucune composition fictive, aucun Tour 0, aucune auto-qualification, aucun greffier,
        # aucun autre appel LLM. Le rapport diagnostic partiel est produit tel quel.
        _journal(
            session,
            run,
            "mission",
            "stopped_after_framing_failure",
            "facilitateur",
            {
                "stop_reason": run.stop_reason,
                "framing_error": run.framing_error,
                "skipped_steps": ["composition", "tour0", "auto_qualification", "greffier"],
                "llm_calls_used": run.ledger.calls_used,
                "budget": run.ledger.snapshot(),
            },
        )
    else:
        _step_composition(session, run, settings)
        _check_uncovered_critical_dimension(session, run)
        _step_tour0(session, run, llm, settings)
        _step_self_qualification(session, run, llm, settings)
        _step_clerk(session, run, llm, settings)
        _build_interim_cartography(run)
        # Incrément 2 — délibération probante (chaque étape se saute proprement sous budget).
        _check_deliberation_affordable(session, run)
        _step_confrontation(session, run, llm, settings)
        _step_steelman(session, run, llm, settings)
        _step_research(session, run, llm, settings)
        _step_revision(session, run, llm, settings)
        _step_consolidation(session, run, llm, settings)
        _step_comparison(session, run, llm, settings)
        _step_synthesis(session, run, llm, settings)
        _step_gate(session, run, llm, settings)
    _finalize(session, run, class_info)


def _fail_mission(session: Session, run: _Run, failure: dict[str, Any]) -> None:
    """État terminal `failed` après échec définitif d'un appel fournisseur (B10).

    Ce qui a été produit (cadrage, composition, exposés réussis) est conservé ; un rapport
    diagnostic partiel est écrit ; aucune recommandation, aucun `decision_ready`.
    """
    m = run.mission
    run.failure = failure
    run.stop_reason = str(failure.get("reason", "provider_error"))
    m.failure_json = json.dumps(failure, ensure_ascii=False, default=str)
    session.commit()
    entry_type = (
        "failed_structured_output"
        if failure.get("kind") == "structured_output"
        else "failed_provider_call"
    )
    _journal(
        session,
        run,
        "mission",
        entry_type,
        "facilitateur",
        {
            **{k: v for k, v in failure.items() if k != "message"},
            "message": str(failure.get("message", ""))[:300],
            "provider_attempts": run.provider_attempts,
            "provider_retries": run.provider_retries,
            "provider_failures": run.provider_failures,
            "structured_output_retries": run.structured_output_retries,
            "budget": run.ledger.snapshot(),
        },
    )
    class_info = {
        "declared": m.declared_class,
        "effective": m.effective_class,
        "provisional": m.class_is_provisional,
        "escalation": "",
    }
    _finalize(session, run, class_info, failed=True)


def _step_framing(session: Session, run: _Run, llm: LLMClient, settings: Settings) -> None:
    m = run.mission
    prompt = build_framing_prompt(
        input_type=m.input_type,
        input_text=m.input_text,
        context_text=m.context_text,
        ceo_preference=m.ceo_preference,
        effective_class=m.effective_class,
    )
    response, framing, error = _call_structured(
        session,
        run,
        llm,
        settings,
        step="cadrage",
        actor="Cadrage",
        system=FRAMING_SYSTEM,
        prompt=prompt,
        call_type=FRAMING_CALL_TYPE,
        model=FramingOutput,
    )
    if response is None:
        run.framing_error = f"cadrage non exécuté ({run.stop_reason})"
        return
    run.framing = framing
    run.framing_error = error
    m.framing_json = json.dumps(
        {
            "parsed": framing.model_dump() if framing else None,
            "error": error,
            "stop_reason": response.stop_reason,
            "output_tokens": response.usage.output_tokens,
            "max_tokens": settings.mission_max_tokens_framing,
            "raw": response.text,
        },
        ensure_ascii=False,
    )
    session.commit()
    if framing is None:
        # Panne de cadrage après récupération bornée (B13) : la mission ne continue pas sur un
        # cadrage fictif. État terminal `failed` explicite (raison, catégorie, tentatives), réponse
        # brute de la dernière tentative conservée pour diagnostic, rapport partiel — jamais un
        # rapport `candidate` presque vide, aucune composition, aucune recommandation.
        failure = _structured_failure(
            run,
            settings,
            step="cadrage",
            actor="Cadrage",
            call_type=FRAMING_CALL_TYPE,
            error=error,
        )
        _journal(
            session,
            run,
            "cadrage",
            "framing_failed",
            "facilitateur",
            {
                "kind": failure["category"],
                "reason": failure["reason"],
                "error": error,
                "stop_reason": response.stop_reason,
                "output_tokens": response.usage.output_tokens,
                "max_tokens": settings.mission_max_tokens_framing,
                "raw_length_chars": len(response.text),
            },
        )
        raise MissionCallFailedError(failure)
    _journal(
        session,
        run,
        "cadrage",
        "framing_result",
        "Cadrage",
        {
            "parse_error": error,
            "dimensions": [d.name for d in framing.dimensions] if framing else [],
            "contestation": framing.contestation.status if framing else "",
            "global_unknowns": len(framing.global_unknowns) if framing else 0,
        },
    )


def _step_composition(session: Session, run: _Run, settings: Settings) -> None:
    m = run.mission
    framing = run.framing or FramingOutput(problem_understood=m.input_text[:500])
    # B14-prime (O2) — invariant de composition : la largeur du Tour 0 est bornée par le plus grand
    # nombre d'experts dont le noyau obligatoire (exposé + auto-qualification par expert, une
    # confrontation par position, cœur de synthèse borné par la cardinalité maximale des options,
    # steelman si la classe l'impose) tient dans le budget restant. La borne est dérivée de
    # contrats contrôlés (options par expert ≤ `mission_max_options_per_expert`), jamais d'une
    # moyenne empirique. Une largeur non délibérable n'est jamais engagée : si moins de deux
    # positions sont délibérables, arrêt explicite après le cadrage avec demande de budget.
    remaining = run.ledger.remaining_calls
    options_cap = settings.mission_max_options_per_expert

    def bound_for(n: int) -> dict[str, int]:
        return minimal_deliberation_bound(
            n,
            effective_class=m.effective_class,
            options_per_expert=options_cap,
            batch_size=CONSOLIDATION_BATCH_SIZE,
            meta_chunk_size=META_CHUNK_SIZE,
        )

    n_feasible = feasible_expert_count(
        remaining,
        effective_class=m.effective_class,
        options_per_expert=options_cap,
        batch_size=CONSOLIDATION_BATCH_SIZE,
        meta_chunk_size=META_CHUNK_SIZE,
    )
    needed = max(2, len(framing.dimensions))
    # Une seule dimension émergente : une seule position est légitime (aucune confrontation
    # possible, porte fail-closed B4) ; à partir de deux dimensions, au moins deux positions.
    min_positions = 1 if len(framing.dimensions) <= 1 else 2
    budget_plan = "full_deliberation" if n_feasible >= needed else "coverage_first"
    result = compose(
        framing,
        effective_class=m.effective_class,
        ceo_preference=m.ceo_preference,
        max_angles_per_cell=settings.mission_max_angles_per_cell,
        max_experts=n_feasible,
    )
    retained = len(result.experts)
    bound = bound_for(retained)
    critical = {d.name for d in framing.dimensions if d.presumed_criticality == "high"}
    critical_dropped = any(d in critical for d in result.uncovered_dimensions)
    result.bounds.update(
        {
            "budget_plan": budget_plan,
            "calls_per_expert_full_deliberation": CALLS_PER_EXPERT,
            "max_experts_by_budget": n_feasible,
            "max_experts_feasible_deliberation": n_feasible,
            "needed_experts_for_dimensions": needed,
            "min_positions": min_positions,
            "options_per_expert_bound": options_cap,
            "remaining_calls_at_composition": remaining,
            **bound,
            "plan_feasible": bound["total_required_calls"] <= remaining
            and retained >= min_positions,
        }
    )
    run.experts = result.experts
    run.composition = result.to_dict()
    if budget_plan == "coverage_first" and result.experts:
        _journal(
            session,
            run,
            "composition",
            "budget_plan_coverage_first",
            "facilitateur",
            {
                "detail": (
                    "le plafond ne finance pas une position délibérable par dimension émergente : "
                    "la largeur est réduite à ce qui reste délibérable jusqu'à la porte "
                    "(profondeur puis dimensions les moins critiques, journalisées) ; une "
                    "dimension critique ne disparaît jamais silencieusement"
                ),
                "max_experts_feasible_deliberation": n_feasible,
                "needed_experts_for_dimensions": needed,
                "budget": run.ledger.snapshot(),
            },
        )
    if run.stop_reason:
        pass
    elif remaining <= 1:
        # Pas même un exposé finançable : rien n'est explorable.
        run.stop_reason = "budget_insufficient_for_exploration"
        _journal(
            session,
            run,
            "composition",
            "budget_stop",
            "facilitateur",
            {"reason": run.stop_reason, "budget": run.ledger.snapshot()},
        )
    elif critical_dropped:
        # Une dimension critique retirée par le budget est traitée par le contrôle dédié
        # (`critical_dimension_uncovered`) : jamais masquée par un autre arrêt.
        pass
    elif not result.experts:
        run.stop_reason = "budget_insufficient_for_exploration"
        _journal(
            session,
            run,
            "composition",
            "budget_stop",
            "facilitateur",
            {"reason": run.stop_reason, "budget": run.ledger.snapshot()},
        )
    elif retained < min_positions:
        # Moins de positions délibérables que le cadrage n'en exige : engager le Tour 0 « pour
        # voir » consommerait le budget sans aucune recommandation possible. Arrêt fail-closed
        # après un seul appel, avec demande de budget chiffrée (B14-prime).
        need_bound = bound_for(needed)
        run.stop_reason = "deliberation_budget_insufficient"
        run.budget_request = {
            "detected_at_step": "composition",
            "minimal_deliberation_calls": need_bound["total_required_calls"],
            "remaining_calls": remaining,
            "additional_calls_estimate": need_bound["total_required_calls"] - remaining,
            "feasible_experts": n_feasible,
            "needed_experts": needed,
            "current_max_calls": run.ledger.max_calls,
            "current_max_cost_eur": run.ledger.max_cost_eur,
            "advice": (
                "relever le plafond d'appels de la mission : le budget restant ne finance pas "
                "un cycle minimal de délibération pour les positions qu'appelle le cadrage ; "
                "aucun appel n'a été dépensé au-delà du cadrage"
            ),
        }
        run.experts = []
        result.experts = []
        run.composition = result.to_dict()
        _journal(
            session,
            run,
            "composition",
            "budget_insufficient",
            "facilitateur",
            {**run.budget_request, "budget": run.ledger.snapshot()},
        )
    m.composition_json = json.dumps(run.composition, ensure_ascii=False)
    session.commit()
    _journal(
        session,
        run,
        "composition",
        "composition_result",
        "facilitateur",
        {
            "experts": [
                {"expert_id": e.expert_id, "dimension": e.dimension, "angle": e.angle_title}
                for e in result.experts
            ],
            "cells": result.cells,
            "uncovered_dimensions": result.uncovered_dimensions,
            "bounds": result.bounds,
            "journal": result.journal,
        },
    )


def _step_tour0(session: Session, run: _Run, llm: LLMClient, settings: Settings) -> None:
    m = run.mission
    dossier = framing_summary_for_experts(
        run.framing or FramingOutput(problem_understood=m.input_text[:500])
    )
    for spec in run.experts:
        if run.stop_reason:
            _journal(
                session,
                run,
                "tour0",
                "expert_skipped",
                spec.expert_id,
                {"reason": run.stop_reason},
            )
            continue
        prompt = build_expert_prompt(
            spec=spec,
            framing_dossier=dossier,
            input_type=m.input_type,
            input_text=m.input_text,
            context_text=m.context_text,
            ceo_preference=m.ceo_preference,
        )
        response, output, error = _call_structured(
            session,
            run,
            llm,
            settings,
            step="tour0",
            actor=spec.expert_id,
            system=EXPERT_SYSTEM,
            prompt=prompt,
            call_type=EXPERT_CALL_TYPE,
            model=ExpertOutput,
        )
        if response is None:
            continue
        cap = settings.mission_max_options_per_expert
        if output is not None and len(output.options) > cap:
            # Contrat de cardinalité (B14-prime — O2) : au plus `cap` options par expert, annoncé
            # dans la
            # consigne ; l'excédent est écarté de façon déterministe et journalisée (jamais
            # silencieusement), afin que la borne du plan de consolidation reste vraie.
            _journal(
                session,
                run,
                "tour0",
                "options_capped",
                spec.expert_id,
                {
                    "proposed": len(output.options),
                    "kept": cap,
                    "dropped_labels": [o.label for o in output.options[cap:]],
                },
            )
            output = output.model_copy(update={"options": list(output.options[:cap])})
        run.expert_results.append(
            {
                "expert_id": spec.expert_id,
                "dimension": spec.dimension,
                "angle": spec.angle_title,
                "output": output,
                "parse_error": error,
                "raw": response.text,
            }
        )
        _journal(
            session,
            run,
            "tour0",
            "expert_result",
            spec.expert_id,
            {
                "parse_error": error,
                "position": output.position if output else "",
                "options": [o.label for o in output.options] if output else [],
                "raw": response.text,
            },
        )
    _journal(
        session,
        run,
        "tour0",
        "tour0_closed",
        "facilitateur",
        {
            "positions": [
                {
                    "expert_id": r["expert_id"],
                    "position": r["output"].position if r["output"] else "",
                }
                for r in run.expert_results
            ],
            "answered": len([r for r in run.expert_results if r["output"] is not None]),
            "planned": len(run.experts),
        },
    )
    _plan_deliberation_core(session, run)


def _plan_deliberation_core(session: Session, run: _Run) -> None:
    """B14-prime (O3) — dès la clôture du Tour 0, le cœur réel et la réserve du cycle minimal.

    Les options réelles sont connues : prétraitement déterministe, plan de consolidation réel
    (lots, méta-passes), cœur nominal et pire cas (B8), cycle minimal (une confrontation par
    position + cœur) et steelman obligatoire de la classe. Cette réserve est opposable aux
    dépenses pré-délibération restantes : auto-qualification nominale, greffier, relances B13.
    """
    answered = _answered(run)
    if len(answered) < 2:
        return
    options = collect_options(run.expert_results)
    plan = plan_consolidation(options, CONSOLIDATION_BATCH_SIZE)
    run.core_plan = plan
    run.core_calls = (SYNTHESIS_CORE_CALLS - 1) + plan["nominal"]
    run.core_worst_calls = run.core_calls + 2 * plan["batches"] + 1
    steelman = mandatory_steelman_calls(run.mission.effective_class)
    minimal = len(answered) + run.core_calls
    run.deliberation_reserve = minimal + steelman
    run.deliberation_plan = {
        "answered_positions": len(answered),
        "options": len(options),
        "groups": plan["groups"],
        "batches": plan["batches"],
        "meta_passes": plan["meta"],
        "core_nominal_calls": run.core_calls,
        "core_worst_calls": run.core_worst_calls,
        "minimal_cycle_calls": minimal,
        "mandatory_steelman_calls": steelman,
        "reserved_deliberation_calls": run.deliberation_reserve,
        "remaining_calls": run.ledger.remaining_calls,
        "pre_deliberation_margin": run.ledger.remaining_calls - run.deliberation_reserve,
    }
    _journal(
        session,
        run,
        "tour0",
        "deliberation_core_planned",
        "facilitateur",
        {**run.deliberation_plan, "consolidation_plan": plan, "budget": run.ledger.snapshot()},
    )


def _reserve_allows(session: Session, run: _Run, step: str, what: str) -> bool:
    """Une dépense pré-délibération (un appel) n'est admise que si la réserve du cycle minimal
    reste intacte après elle ; sinon elle est sautée et journalisée (jamais inventée)."""
    if run.deliberation_reserve is None:
        return True
    if run.ledger.remaining_calls - 1 >= run.deliberation_reserve:
        return True
    _journal(
        session,
        run,
        step,
        "skipped_for_deliberation_reserve",
        "facilitateur",
        {
            "skipped": what,
            "remaining_calls": run.ledger.remaining_calls,
            "reserved_deliberation_calls": run.deliberation_reserve,
        },
    )
    return False


def _step_self_qualification(
    session: Session, run: _Run, llm: LLMClient, settings: Settings
) -> None:
    answered = [r for r in run.expert_results if r["output"] is not None]
    if len(answered) < 2 or run.stop_reason:
        _journal(
            session,
            run,
            "auto_qualification",
            "skipped",
            "facilitateur",
            {"reason": run.stop_reason or "moins de deux positions : rien à qualifier"},
        )
        return
    labels = anonymize_labels([r["expert_id"] for r in answered])
    for r in answered:
        if run.stop_reason:
            break
        if not _reserve_allows(
            session, run, "auto_qualification", f"auto-qualification de {r['expert_id']}"
        ):
            # Information de second ordre : la position du Tour 0 est conservée, ses relations
            # restent absentes (cartographie partielle), la confrontation reste finançable.
            run.self_qual[r["expert_id"]] = None
            continue
        others = [
            (labels[o["expert_id"]], o["output"].position)
            for o in answered
            if o["expert_id"] != r["expert_id"]
        ]
        prompt = build_self_qualification_prompt(
            own_label=labels[r["expert_id"]], own_position=r["output"].position, others=others
        )
        response, output, error = _call_structured(
            session,
            run,
            llm,
            settings,
            step="auto_qualification",
            actor=r["expert_id"],
            system=SELF_QUAL_SYSTEM,
            prompt=prompt,
            call_type=SELF_QUAL_CALL_TYPE,
            model=SelfQualificationOutput,
            n_items=len(others),
        )
        if response is None:
            break
        run.self_qual[r["expert_id"]] = output
        _journal(
            session,
            run,
            "auto_qualification",
            "result",
            r["expert_id"],
            {
                "parse_error": error,
                "relations": [rel.model_dump() for rel in output.relations] if output else [],
            },
        )


def _step_clerk(session: Session, run: _Run, llm: LLMClient, settings: Settings) -> None:
    answered = [r for r in run.expert_results if r["output"] is not None]
    if run.stop_reason or len(answered) < 2:
        return
    labels = anonymize_labels([r["expert_id"] for r in answered])
    relations = relations_table(run.self_qual, labels)
    ambiguities = residual_ambiguities(relations)
    if not ambiguities:
        _journal(
            session,
            run,
            "greffier",
            "skipped",
            "facilitateur",
            {"reason": "aucune ambiguïté résiduelle après auto-qualification"},
        )
        return
    if not _reserve_allows(session, run, "greffier", "greffier (facultatif)"):
        # Le greffier est facultatif : la cartographie déterministe continue sans lui, et son
        # absence est signalée (`clerk_used = false`), jamais compensée par une sortie inventée.
        return
    options = collect_options(run.expert_results)
    prompt = build_clerk_prompt(
        options=options,
        positions=[(labels[r["expert_id"]], r["output"].position) for r in answered],
        ambiguities=ambiguities,
    )
    response, output, error = _call_structured(
        session,
        run,
        llm,
        settings,
        step="greffier",
        actor="Greffier",
        system=CLERK_SYSTEM,
        prompt=prompt,
        call_type=CLERK_CALL_TYPE,
        model=ClerkOutput,
        n_items=len(options) + len(ambiguities),
    )
    if response is None:
        return
    run.clerk = output
    _journal(
        session,
        run,
        "greffier",
        "result",
        "Greffier",
        {
            "parse_error": error,
            "groups": [g.model_dump() for g in output.groups] if output else [],
            "disagreements": [d.model_dump() for d in output.disagreements] if output else [],
        },
    )


def _budget_snapshot(run: _Run) -> dict[str, Any]:
    """Registre budgétaire + comptabilité des tentatives fournisseur (B10)."""
    return {
        **run.ledger.snapshot(),
        "logical_calls": run.logical_calls,
        "provider_attempts": run.provider_attempts,
        "provider_retries": run.provider_retries,
        "provider_failures": run.provider_failures,
        "structured_output_failures": run.structured_output_failures,
        "structured_output_recoveries": run.structured_output_recoveries,
        "structured_output_retries": run.structured_output_retries,
        "structured_output_exhausted": run.structured_output_exhausted,
        "reserved_deliberation_calls": run.deliberation_reserve,
        "deliberation_plan": dict(run.deliberation_plan),
    }


def _finalize(
    session: Session, run: _Run, class_info: dict[str, Any], *, failed: bool = False
) -> None:
    m = run.mission
    if not run.cartography:
        _build_interim_cartography(run)
    cartography = run.cartography
    deliberation = _deliberation_payload(run)
    m.deliberation_json = json.dumps(deliberation, ensure_ascii=False, default=str)
    m.recommendation_json = (
        json.dumps(run.recommendation, ensure_ascii=False, default=str)
        if run.recommendation
        else ""
    )
    report = build_situation_report(
        mission_id=m.id,
        input_type=m.input_type,
        input_text=m.input_text,
        class_info=class_info,
        framing=run.framing,
        framing_error=run.framing_error,
        composition=run.composition,
        cartography=cartography,
        budget=_budget_snapshot(run),
        stop_reason=run.stop_reason,
        deliberation=deliberation,
        recommendation=run.recommendation or None,
    )
    # Une panne de cadrage ou un échec définitif d'appel fournisseur n'est pas un rapport
    # candidat : la mission est `failed`, le rapport partiel reste disponible pour le diagnostic.
    m.status = "failed" if (failed or run.stop_reason.startswith("framing_failed")) else "candidate"
    report["status"] = m.status
    report["failure"] = run.failure or None
    m.cartography_json = json.dumps(cartography, ensure_ascii=False, default=str)
    m.report_json = json.dumps(report, ensure_ascii=False, default=str)
    m.stop_reason = run.stop_reason
    session.commit()
    _journal(
        session,
        run,
        "rapport",
        "report_ready",
        "facilitateur",
        {
            "partial": bool(run.stop_reason),
            "stop_reason": run.stop_reason,
            "distinct_option_groups": cartography["distinct_option_groups"],
            "divergence_index": cartography["divergence_index"],
            "budget": _budget_snapshot(run),
            "status": m.status,
        },
    )


# =====================================================================================
# Incrément 2 — délibération probante → recommandation décisionnelle
# =====================================================================================
BUDGET_STOP_REASONS = frozenset(
    {
        "max_calls_reached",
        "cost_cap_would_be_exceeded",
        "budget_insufficient_for_exploration",
        "deliberation_budget_insufficient",
        # B12 — relance fournisseur refusée : l'exposition financière potentielle atteindrait le
        # plafond CEO (arrêt budgétaire, pas une panne).
        "retry_refused_uncertain_cost_budget",
    }
)
OBJECTION_ACTS = frozenset({"critique", "refute", "third_way", "steelman_critique"})


def _apply_budget_plan_after_escalation(session: Session, run: _Run, settings: Settings) -> None:
    """Après escalade de classe, relever les plafonds jusqu'au couloir de la nouvelle classe.

    Jamais à la baisse ; jamais au-delà d'une surcharge CEO (absolue).
    """
    m = run.mission
    if run.budget_source == "ceo_override":
        return
    calls, cost, _ = plan_budget(
        effective_class=m.effective_class,
        settings=settings,
        override_calls=None,
        override_cost=None,
    )
    if calls > run.ledger.max_calls or cost > run.ledger.max_cost_eur:
        change = run.ledger.raise_caps(calls, cost)
        m.max_llm_calls = run.ledger.max_calls
        m.max_cost_eur = run.ledger.max_cost_eur
        session.commit()
        _journal(
            session,
            run,
            "budget",
            "caps_raised_after_escalation",
            "facilitateur",
            {"effective_class": m.effective_class, **change},
        )


def _skip(session: Session, run: _Run, step: str, reason: str) -> None:
    run.steps_skipped.append({"step": step, "reason": reason})
    _journal(session, run, step, "skipped", "facilitateur", {"reason": reason})


def _answered(run: _Run) -> list[dict[str, Any]]:
    return [r for r in run.expert_results if r["output"] is not None]


def _check_uncovered_critical_dimension(session: Session, run: _Run) -> None:
    """Une dimension critique non couverte faute de budget n'est jamais une fausse couverture."""
    if run.stop_reason or run.framing is None:
        return
    critical = {d.name for d in run.framing.dimensions if d.presumed_criticality == "high"}
    uncovered = [d for d in run.composition.get("uncovered_dimensions", []) if d in critical]
    if not uncovered:
        return
    run.stop_reason = "critical_dimension_uncovered"
    run.budget_request = {
        "uncovered_critical_dimensions": uncovered,
        "additional_calls_estimate": len(uncovered) * CALLS_PER_EXPERT,
        "current_max_calls": run.ledger.max_calls,
        "current_max_cost_eur": run.ledger.max_cost_eur,
        "advice": (
            "relever le plafond de la mission ou réduire son périmètre ; la mission s'arrête "
            "plutôt que d'ignorer silencieusement une dimension critique"
        ),
    }
    _journal(
        session,
        run,
        "composition",
        "critical_dimension_uncovered",
        "facilitateur",
        {**run.budget_request, "budget": run.ledger.snapshot()},
    )


def _build_interim_cartography(run: _Run) -> None:
    answered = _answered(run)
    run.labels = anonymize_labels([r["expert_id"] for r in answered])
    run.cartography = build_cartography(
        expert_results=run.expert_results,
        self_qual=run.self_qual,
        clerk=run.clerk,
        labels=run.labels,
    )
    run.current_positions = {r["expert_id"]: r["output"].position for r in answered}


def _needs_two_positions(session: Session, run: _Run, step: str) -> bool:
    if run.stop_reason:
        _skip(session, run, step, f"arrêt en cours : {run.stop_reason}")
        return False
    if len(_answered(run)) < 2:
        _skip(session, run, step, "moins de deux positions : rien à confronter")
        return False
    return True


def _check_deliberation_affordable(session: Session, run: _Run) -> None:
    """Avant d'entamer la délibération : le budget restant finance-t-il un cycle minimal ?

    Cycle minimal = une confrontation par position exprimée + consolidation, comparaison,
    synthèse et porte qualité. Sinon la délibération n'est pas entamée « pour voir » : arrêt
    partiel explicite (`deliberation_budget_insufficient`), rapport de situation conservé, et
    la demande de budget chiffrée est journalisée. Aucune relance illimitée.
    """
    if run.stop_reason:
        return
    answered = len(_answered(run))
    if answered < 2:
        return
    # Le cœur de synthèse dépend de la matière : la consolidation est planifiée en lots bornés
    # (jamais un appel monolithique), donc son nombre d'appels est estimé ici, avant de délibérer.
    options = run.cartography.get("options", [])
    plan = plan_consolidation(options, CONSOLIDATION_BATCH_SIZE)
    run.core_plan = plan
    run.core_calls = (SYNTHESIS_CORE_CALLS - 1) + plan["nominal"]
    # Pire cas borné (B8) : + une relance scindée par lot de consolidation, + une relance de
    # comparaison. Les relances ne sont dépensées que si les étapes plus prioritaires restent
    # finançables (porte > synthèse > comparaison valide > consolidation valide > relances).
    run.core_worst_calls = run.core_calls + 2 * plan["batches"] + 1
    minimal = answered + run.core_calls
    _journal(
        session,
        run,
        "deliberation",
        "budget_plan",
        "facilitateur",
        {
            "answered_positions": answered,
            "core_nominal_calls": run.core_calls,
            "core_worst_case_calls": run.core_worst_calls,
            "consolidation_plan": plan,
            "remaining_calls": run.ledger.remaining_calls,
            "minimal_cycle_calls": minimal,
            "retries_guaranteed": run.ledger.remaining_calls >= answered + run.core_worst_calls,
        },
    )
    if run.ledger.remaining_calls >= minimal:
        return
    run.stop_reason = "deliberation_budget_insufficient"
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
        run.steps_skipped.append({"step": step, "reason": "budget insuffisant pour délibérer"})
    run.budget_request = {
        "detected_at_step": "deliberation",
        "minimal_deliberation_calls": minimal,
        "remaining_calls": run.ledger.remaining_calls,
        "additional_calls_estimate": minimal - run.ledger.remaining_calls,
        "current_max_calls": run.ledger.max_calls,
        "current_max_cost_eur": run.ledger.max_cost_eur,
        "advice": (
            "relever le plafond d'appels de la mission pour délibérer sur les positions "
            "rassemblées ; le rapport de situation (Tour 0) reste exploitable tel quel"
        ),
    }
    _journal(
        session,
        run,
        "deliberation",
        "budget_insufficient",
        "facilitateur",
        {**run.budget_request, "budget": run.ledger.snapshot()},
    )


def _can_spend(session: Session, run: _Run, step: str, calls_needed: int, what: str) -> bool:
    """Une étape optionnelle n'est financée que si le cœur de synthèse reste finançable après.

    Priorité explicite : largeur du Tour 0 → confrontation → (steelman, recherche, révision si
    le budget le permet) → consolidation, comparaison, synthèse, porte qualité. Un refus est
    journalisé ; il n'y a ni relance ni file d'attente.
    """
    if run.ledger.remaining_calls - calls_needed >= run.core_worst_calls:
        return True
    _journal(
        session,
        run,
        step,
        "budget_reserved_for_synthesis",
        "facilitateur",
        {
            "skipped": what,
            "calls_needed": calls_needed,
            "remaining_calls": run.ledger.remaining_calls,
            "synthesis_core_calls": run.core_calls,
            "synthesis_core_worst_case_calls": run.core_worst_calls,
        },
    )
    return False


# --- C. Confrontation -----------------------------------------------------------------------
def _step_confrontation(session: Session, run: _Run, llm: LLMClient, settings: Settings) -> None:
    step = "confrontation"
    if not _needs_two_positions(session, run, step):
        return
    label_to_expert = {v: k for k, v in run.labels.items()}
    for r in _answered(run):
        if run.stop_reason:
            break
        own_label = run.labels[r["expert_id"]]
        prompt = build_confrontation_prompt(
            own_label=own_label,
            own_position=r["output"].position,
            map_view=build_map_view(run.cartography, exclude_label=own_label),
        )
        response, output, error = _call_structured(
            session,
            run,
            llm,
            settings,
            step=step,
            actor=r["expert_id"],
            system=CONFRONTATION_SYSTEM,
            prompt=prompt,
            call_type=CONFRONTATION_CALL_TYPE,
            model=ConfrontationOutput,
        )
        if response is None:
            break
        registered: list[str] = []
        rejected: list[dict[str, Any]] = []
        valid_acts = []
        if output is not None:
            for act in output.acts:
                if act.act == "none" or not act.text.strip():
                    continue
                # Intégrité des cibles (déterministe) : un acte adressé doit viser une position
                # existante et distincte de la sienne ; sinon il est rejeté et journalisé, sans
                # créer d'objection, sans atteindre la recherche, la révision ni la synthèse.
                # `third_way` peut rester sans cible (une cible invalide y est simplement effacée).
                target_ok = act.target in label_to_expert and act.target != own_label
                if act.act == "third_way":
                    if act.target and not target_ok:
                        act = act.model_copy(update={"target": ""})
                elif not target_ok:
                    rejected.append(
                        {
                            "act": act.act,
                            "target": act.target,
                            "nature": act.nature,
                            "text": act.text[:300],
                            "reason": (
                                "cible inexistante ou égale à sa propre position "
                                f"(labels valides : {sorted(label_to_expert)})"
                            ),
                        }
                    )
                    continue
                valid_acts.append(act)
                obj_id = f"OBJ-{len(run.objections) + 1}"
                run.objections.append(
                    {
                        "id": obj_id,
                        "from": own_label,
                        "from_expert": r["expert_id"],
                        "target": act.target,
                        "target_expert": label_to_expert.get(act.target, ""),
                        "act": act.act,
                        "nature": act.nature,
                        "text": act.text,
                        "depends_on_fact": act.depends_on_fact,
                        "fact_question": act.fact_question,
                        "status": "open" if act.act in OBJECTION_ACTS else "n/a",
                    }
                )
                registered.append(obj_id)
        # Seuls les actes valides sont conservés en aval (recherche, charge utile de délibération).
        run.confrontations[r["expert_id"]] = (
            output.model_copy(update={"acts": valid_acts}) if output is not None else None
        )
        for bad in rejected:
            _journal(session, run, step, "act_rejected", r["expert_id"], bad)
        _journal(
            session,
            run,
            step,
            "result",
            r["expert_id"],
            {
                "parse_error": error,
                "acts_registered": registered,
                "acts_rejected": len(rejected),
                "act_count": len(output.acts) if output else 0,
                "convergence_note": output.convergence_note if output else "",
            },
        )
    run.steps_done.append(step)


# --- D. Steelman ------------------------------------------------------------------------------
def _step_steelman(session: Session, run: _Run, llm: LLMClient, settings: Settings) -> None:
    step = "steelman"
    m = run.mission
    if run.stop_reason:
        _skip(session, run, step, f"arrêt en cours : {run.stop_reason}")
        return
    answered = _answered(run)
    open_objections = [o for o in run.objections if o["status"] == "open"]
    required_by_class = m.effective_class in STEELMAN_CLASSES
    premature = is_premature_convergence(
        effective_class=m.effective_class,
        divergence_index=float(run.cartography.get("divergence_index", 0.0)),
        objection_count=len(open_objections),
    )
    run.steelman = {
        "required": required_by_class or premature,
        "reason": (
            "classe structurante/critique"
            if required_by_class
            else ("convergence prématurée" if premature else "")
        ),
        "status": "not_required",
    }
    if not run.steelman["required"]:
        _journal(session, run, step, "not_required", "facilitateur", dict(run.steelman))
        return
    if len(answered) < 2:
        run.steelman["status"] = "impossible_single_position"
        _skip(session, run, step, "une seule position : aucun contradicteur possible")
        return
    if not _can_spend(session, run, step, 2, "steelman + reconnaissance"):
        run.steelman["status"] = "budget_reserved_for_synthesis"
        _skip(session, run, step, "budget réservé au cœur de synthèse : steelman non financé")
        return
    clusters = run.cartography.get("position_clusters") or [[r["expert_id"] for r in answered]]
    dominant = list(clusters[0])
    target_expert = dominant[0]
    experts_view = [{"expert_id": r["expert_id"], "angle": r["angle"]} for r in answered]
    contradictor = select_contradictor(experts_view, dominant, run.labels)
    if contradictor is None:
        # Unanimité : le contradicteur est désigné hors du tenant, angle critique de préférence.
        others = [e for e in experts_view if e["expert_id"] != target_expert]
        critical = [e for e in others if e["angle"] in CRITICAL_ANGLE_TITLES]
        contradictor = str((critical or others)[0]["expert_id"])
    target = next(r for r in answered if r["expert_id"] == target_expert)
    target_args = " ; ".join(
        [target["output"].reasoning, *list(target["output"].assumptions)]
    ).strip(" ;")
    run.steelman.update(
        {
            "target_expert": target_expert,
            "target": run.labels[target_expert],
            "contradictor_expert": contradictor,
            "contradictor": run.labels[contradictor],
            "dominant_cluster": [run.labels[e] for e in dominant],
        }
    )
    response, output, error = _call_structured(
        session,
        run,
        llm,
        settings,
        step=step,
        actor=contradictor,
        system=STEELMAN_SYSTEM,
        prompt=build_steelman_prompt(
            contradictor_label=run.labels[contradictor],
            target_label=run.labels[target_expert],
            target_position=target["output"].position,
            target_arguments=target_args,
        ),
        call_type=STEELMAN_CALL_TYPE,
        model=SteelmanOutput,
    )
    if response is None:
        run.steelman["status"] = "budget_stop"
        return
    if output is None:
        run.steelman.update({"status": "failed", "parse_error": error})
        _journal(session, run, step, "failed", contradictor, {"parse_error": error})
        return
    flags = strawman_flags(output)
    run.steelman.update(
        {
            "steelman": output.steelman,
            "strengths": output.strengths,
            "failure_scenarios": output.failure_scenarios,
            "critique": output.critique,
            "strawman_flags": flags,
        }
    )
    _journal(
        session,
        run,
        step,
        "steelman_result",
        contradictor,
        {
            "target": run.labels[target_expert],
            "strawman_flags": flags,
            "critique_present": bool(output.critique),
        },
    )
    # Reconnaissance par le tenant de la position : la reformulation le représente-t-elle ?
    rec_response, rec_out, rec_err = _call_structured(
        session,
        run,
        llm,
        settings,
        step=step,
        actor=target_expert,
        system=RECOGNITION_SYSTEM,
        prompt=build_recognition_prompt(
            own_label=run.labels[target_expert],
            own_position=target["output"].position,
            steelman=output.steelman,
            strengths=output.strengths,
        ),
        call_type=RECOGNITION_CALL_TYPE,
        model=RecognitionOutput,
    )
    recognition = "no"
    missing: list[str] = []
    if rec_response is not None:
        if rec_out is not None:
            recognition = rec_out.recognized
            missing = rec_out.missing_points
        run.steelman["recognition_parse_error"] = rec_err
    else:
        run.steelman["recognition_parse_error"] = "reconnaissance non exécutée (budget)"
    if flags or recognition == "no":
        status = "rejected_strawman"
    elif recognition == "partial":
        status = "accepted_partial"
    else:
        status = "accepted"
    run.steelman.update({"recognition": recognition, "missing_points": missing, "status": status})
    if output.critique.strip():
        run.objections.append(
            {
                "id": f"OBJ-{len(run.objections) + 1}",
                "from": run.labels[contradictor],
                "from_expert": contradictor,
                "target": run.labels[target_expert],
                "target_expert": target_expert,
                "act": "steelman_critique",
                "nature": "solution",
                "text": output.critique,
                "depends_on_fact": False,
                "fact_question": "",
                "status": "open" if status != "rejected_strawman" else "inadmissible_strawman",
                "failure_scenarios": output.failure_scenarios,
            }
        )
    _journal(
        session,
        run,
        step,
        "recognition_result",
        target_expert,
        {"recognized": recognition, "missing_points": missing, "steelman_status": status},
    )
    run.steps_done.append(step)


# --- E. Recherche ciblée -------------------------------------------------------------------------
def _step_research(session: Session, run: _Run, llm: LLMClient, settings: Settings) -> None:
    step = "recherche"
    if run.stop_reason:
        _skip(session, run, step, f"arrêt en cours : {run.stop_reason}")
        return
    questions = material_fact_questions(
        run.confrontations, run.cartography, run.labels, cap=settings.mission_max_research_tasks
    )
    if not questions:
        _skip(session, run, step, "aucun désaccord pertinent ne dépend d'un fait vérifiable")
        return
    provider = build_research_provider(settings)
    for q in questions:
        if run.stop_reason:
            break
        if provider.name == "none":
            result = provider.search(q["question"], max_tokens=0)  # aucun appel, aucun coût
        else:
            if not _can_spend(session, run, step, 1, f"recherche « {q['question'][:80]} »"):
                break
            result = _research_call(session, run, settings, provider, q["question"])
            if result is None:
                break
        # Intégrité sémantique (B1) : le statut est reclassé déterministement — `found` exige des
        # sources ET une réponse matérielle déclarée ; des documents génériques restent tracés
        # comme résultats de recherche, jamais comme preuve.
        status, reason = classify_research_outcome(result)
        first = result.findings[0] if (result.findings and status == "found") else None
        # Provenance de débat : objections dont cette question est issue (pour la trace et pour
        # cibler la révision), positions concernées (jamais « tout le monde »).
        q_key = " ".join(q["question"].lower().split())
        objection_ids = [
            o["id"]
            for o in run.objections
            if o.get("depends_on_fact")
            and " ".join(str(o.get("fact_question", "")).lower().split()) == q_key
        ]
        item = {
            "id": f"EV-{len(run.evidence) + 1}",
            "question": q["question"],
            "claim": q["claim"],
            "raised_by": q["raised_by"],
            "raised_by_all": q.get("raised_by_all", [q["raised_by"]]),
            "target": q["target"],
            "positions": list(q.get("positions", [])),
            "objection_ids": objection_ids,
            "status": status,
            "reason": reason,
            "documents_returned": len(result.findings),
            "answer_found": result.answer_found,
            "requires_internal_data": result.requires_internal_data,
            "provider": result.provider,
            "findings": [f.to_dict() for f in result.findings],
            "source": first.source if first else "",
            "date": first.date if first else "",
            "excerpt": first.excerpt if first else "",
            "reliability": first.reliability if first else "unknown",
            "provenance": (
                "external"
                if status == "found"
                else ("non_material" if result.findings else "unavailable")
            ),
            "note": result.note,
            "answer_summary": result.answer_summary if status == "found" else "",
        }
        run.evidence.append(item)
        run.research.append(item)
        _journal(
            session,
            run,
            step,
            "result",
            "Recherche",
            {k: v for k, v in item.items() if k != "answer_summary"},
        )
    run.steps_done.append(step)


RESEARCH_SYSTEM_LABEL = "recherche ciblée"


def _research_call(
    session: Session, run: _Run, settings: Settings, provider: Any, question: str
) -> Any:
    """Appel réseau de recherche sous la même chaîne d'audit qu'un appel LLM ordinaire.

    Avant : estimation budgétaire (refus = arrêt), `call_planned` (question complète, SHA-256,
    fournisseur, `max_tokens`, majorant). Après : enregistrement au registre, ligne
    `llm_call_logs`, `call_done` (usage, coût, statut, fournisseur, nombre de résultats).
    Retourne None si le budget interdit l'appel.
    """
    step = "recherche"
    max_tokens = settings.mission_max_tokens_research
    try:
        estimate = run.ledger.check_before_call(
            system=RESEARCH_SYSTEM_LABEL,
            prompt=question,
            max_tokens=max_tokens,
            call_type=RESEARCH_CALL_TYPE,
        )
    except BudgetExceededError as exc:
        run.stop_reason = exc.reason
        _journal(
            session,
            run,
            step,
            "budget_stop",
            "facilitateur",
            {"reason": exc.reason, **exc.detail, "budget": run.ledger.snapshot()},
        )
        return None
    _journal(
        session,
        run,
        step,
        "call_planned",
        "Recherche",
        {
            "call_type": RESEARCH_CALL_TYPE,
            "provider": provider.name,
            "max_tokens": max_tokens,
            "estimated_cost_eur_upper_bound": estimate,
            "prompt_sha256": prompt_fingerprint(RESEARCH_SYSTEM_LABEL, question),
            "prompt_text": question,
            "system_text": RESEARCH_SYSTEM_LABEL,
        },
    )
    start = time.perf_counter()
    result = provider.search(question, max_tokens=max_tokens)
    duration_ms = int((time.perf_counter() - start) * 1000)
    # Un appel réseau tenté est compté et facturé sur l'usage rapporté (0 si le fournisseur n'en
    # rapporte pas, par exemple sur exception) : aucun appel externe n'échappe au registre.
    usage = result.usage or LLMUsage(input_tokens=0, output_tokens=0)
    cost = run.ledger.record(usage)
    _sync_budget(session, run)
    session.add(
        LLMCallLog(
            phase=PHASE,
            agent_name="Recherche",
            operation_type=RESEARCH_CALL_TYPE,
            provider=provider.name,
            model=settings.anthropic_model,
            prompt_preview=question[:500],
            response_preview=result.answer_summary[:500],
            status="success" if result.status != "error" else "error",
            error=result.note[:500] if result.status == "error" else "",
            duration_ms=duration_ms,
            call_type=RESEARCH_CALL_TYPE,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cost_eur=cost,
            mission_id=run.mission.id,
        )
    )
    session.commit()
    _journal(
        session,
        run,
        step,
        "call_done",
        "Recherche",
        {
            "call_type": RESEARCH_CALL_TYPE,
            "provider": provider.name,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "max_tokens": max_tokens,
            "stop_reason": result.status,
            "truncated": False,
            "findings_count": len(result.findings),
            "duration_ms": duration_ms,
            "cost_eur": cost,
            "budget": run.ledger.snapshot(),
        },
    )
    return result


# --- F. Révision -------------------------------------------------------------------------------
def _step_revision(session: Session, run: _Run, llm: LLMClient, settings: Settings) -> None:
    step = "revision"
    if run.stop_reason:
        _skip(session, run, step, f"arrêt en cours : {run.stop_reason}")
        return
    answered = _answered(run)
    if not answered:
        _skip(session, run, step, "aucune position à réviser")
        return
    for r in answered:
        if run.stop_reason:
            break
        eid = r["expert_id"]
        label = run.labels[eid]
        previous = run.current_positions.get(eid, r["output"].position)
        my_objections = [
            o for o in run.objections if o["target_expert"] == eid and o["status"] == "open"
        ]
        # Preuve ciblée uniquement : une preuve n'atteint que les positions qu'elle concerne
        # (provenance de débat : cible de l'objection factuelle, ou auteur d'une objection
        # factuelle du Tour 0). Jamais de diffusion globale.
        found_evidence = [
            e for e in run.evidence if e["status"] == "found" and label in e.get("positions", [])
        ]
        steelman_critique = ""
        if run.steelman.get("target_expert") == eid and run.steelman.get("status") in {
            "accepted",
            "accepted_partial",
        }:
            steelman_critique = str(run.steelman.get("critique", ""))
        new_ids = [o["id"] for o in my_objections] + [e["id"] for e in found_evidence]
        if steelman_critique:
            new_ids.append("STEELMAN")
        if not new_ids:
            run.revisions.append(
                {
                    "expert_id": eid,
                    "label": label,
                    "previous_position": previous,
                    "decision": "maintain",
                    "revised_position": previous,
                    "reason": "aucune information nouvelle : pas de révision demandée",
                    "triggered_by": [],
                    "new_information_ids": [],
                    "called": False,
                }
            )
            _journal(session, run, step, "no_new_information", eid, {"label": label})
            continue
        if not _can_spend(session, run, step, 1, f"révision de {label}"):
            run.revisions.append(
                {
                    "expert_id": eid,
                    "label": label,
                    "previous_position": previous,
                    "decision": "maintain",
                    "revised_position": previous,
                    "reason": "budget réservé au cœur de synthèse : révision non financée",
                    "triggered_by": [],
                    "new_information_ids": new_ids,
                    "called": False,
                    "budget_reserved": True,
                }
            )
            continue
        prompt = build_revision_prompt(
            own_label=label,
            own_position=previous,
            objections=[
                {"id": o["id"], "nature": o["nature"], "from": o["from"], "text": o["text"]}
                for o in my_objections
                if o["act"] != "steelman_critique"
            ],
            steelman_critique=steelman_critique,
            new_evidence=[
                {
                    "id": e["id"],
                    "claim": e.get("answer_summary") or e["question"],
                    "source": e["source"],
                    "reliability": e["reliability"],
                    "status": e["status"],
                }
                for e in found_evidence
            ],
        )
        response, output, error = _call_structured(
            session,
            run,
            llm,
            settings,
            step=step,
            actor=eid,
            system=REVISION_SYSTEM,
            prompt=prompt,
            call_type=REVISION_CALL_TYPE,
            model=RevisionOutput,
        )
        if response is None:
            break
        decision = output.decision if output else "maintain"
        revised = previous
        if output and decision != "maintain" and output.revised_position.strip():
            revised = output.revised_position.strip()
        triggered = list(output.triggered_by) if output else []
        entry = {
            "expert_id": eid,
            "label": label,
            "previous_position": previous,
            "decision": decision,
            "revised_position": revised,
            "reason": output.reason if output else "",
            "triggered_by": triggered,
            "new_information_ids": new_ids,
            "called": True,
            "parse_error": error,
            "unexplained_change": decision != "maintain" and not triggered,
        }
        run.revisions.append(entry)
        run.current_positions[eid] = revised
        if decision != "maintain":
            for o in my_objections:
                by_steelman = "STEELMAN" in triggered and o["act"] == "steelman_critique"
                if o["id"] in triggered or by_steelman:
                    o["status"] = "addressed"
        _journal(session, run, step, "result", eid, entry)
    run.steps_done.append(step)


def _residual_disagreements(run: _Run) -> list[dict[str, Any]]:
    """Objections restées ouvertes après révision : conservées, jamais lissées."""
    residual: list[dict[str, Any]] = []
    for o in run.objections:
        if o["status"] != "open" or o["act"] not in OBJECTION_ACTS:
            continue
        residual.append(
            {
                "id": o["id"],
                "between": [o["from"], o["target"]] if o["target"] else [o["from"]],
                "nature": o["nature"],
                "description": o["text"],
                "depends_on_fact": o.get("depends_on_fact", False),
            }
        )
    return residual


# --- G. Consolidation ----------------------------------------------------------------------------
def _consolidation_output(
    session: Session,
    run: _Run,
    llm: LLMClient,
    settings: Settings,
    *,
    prompt: str,
    what: str,
    n_items: int,
) -> tuple[ConsolidationOutput | None, str, bool]:
    """Un appel de consolidation sous budget : (sortie, erreur classée, budget_stop)."""
    response, output, error = _call_structured(
        session,
        run,
        llm,
        settings,
        step="consolidation",
        actor="Greffier",
        system=CONSOLIDATION_SYSTEM,
        prompt=prompt,
        call_type=CONSOLIDATION_CALL_TYPE,
        model=ConsolidationOutput,
        n_items=n_items,
    )
    if response is None:
        return None, "budget", True
    if output is None:
        _journal(
            session,
            run,
            "consolidation",
            "parse_failed",
            "Greffier",
            {"what": what, "parse_error": error},
        )
    return output, error, False


def _retry_allowed(
    session: Session, run: _Run, step: str, *, extra_calls: int, higher_priority_calls: int
) -> bool:
    """Une relance n'est financée que si les étapes plus prioritaires restent finançables.

    Hiérarchie (B8) : porte qualité > synthèse > comparaison valide > consolidation valide >
    relance de comparaison > relance de consolidation > révisions > recherche > profondeur.
    """
    if run.ledger.remaining_calls - extra_calls >= higher_priority_calls:
        return True
    _journal(
        session,
        run,
        step,
        "retry_refused_budget",
        "facilitateur",
        {
            "extra_calls": extra_calls,
            "remaining_calls": run.ledger.remaining_calls,
            "reserved_for_higher_priority": higher_priority_calls,
        },
    )
    return False


def _step_consolidation(session: Session, run: _Run, llm: LLMClient, settings: Settings) -> None:
    """Familles stratégiques : précompression → lots bornés inter-natures → méta-passe.

    La nature est un signal, pas une frontière (B6) : le greffier peut réunir des formulations
    équivalentes de natures compatibles ; « agir » et « ne rien faire / différer » restent
    distincts (garde déterministe). Aucun appel monolithique ; une relance au plus par lot (lot
    scindé), financée seulement si comparaison, synthèse et porte restent finançables (B8) ;
    jamais de repli « chaque option devient une famille » après erreur.
    """
    step = "consolidation"
    if run.stop_reason:
        _skip(session, run, step, f"arrêt en cours : {run.stop_reason}")
        return
    options = run.cartography.get("options", [])
    if not options:
        _skip(session, run, step, "aucune option proposée")
        return
    groups = premerge_options(options)
    batches = plan_batches(groups, CONSOLIDATION_BATCH_SIZE)
    not_merged: list[dict[str, Any]] = []
    notes: list[str] = []
    unconsolidated: list[str] = []
    calls = 0
    retries = 0
    last_error = ""
    status = "ok"
    premerged = sum(1 for g in groups if len(g["member_ids"]) > 1)
    cross_kind = sum(1 for g in groups if len(g["source_kinds"]) > 1)
    if premerged:
        notes.append(
            f"{premerged} groupe(s) de formulations identiques fusionnés avant appel"
            + (f", dont {cross_kind} entre natures compatibles" if cross_kind else "")
        )
    meta_passes = max(1, -(-len(groups) // META_CHUNK_SIZE)) if len(batches) > 1 else 0
    _journal(
        session,
        run,
        step,
        "plan",
        "facilitateur",
        {
            "atomic_count": len(options),
            "groups_after_premerge": len(groups),
            "batches": [len(items) for items in batches],
            "meta_passes": meta_passes,
            "batch_size": CONSOLIDATION_BATCH_SIZE,
        },
    )
    families_raw: list[dict[str, Any]] = []
    if not batches:
        families_raw = [direct_family(g) for g in groups]
    budget_stop = False
    remaining_batches = len(batches)
    for items in batches:
        remaining_batches -= 1
        if budget_stop or run.stop_reason:
            unconsolidated += [m for g in items for m in g["member_ids"]]
            continue
        pending: list[list[dict[str, Any]]] = [items]
        attempt = 0
        while pending:
            chunk = pending.pop(0)
            calls += 1
            output, error, budget_stop = _consolidation_output(
                session,
                run,
                llm,
                settings,
                prompt=build_batch_prompt(chunk),
                what=f"lot de {len(chunk)} groupe(s)",
                n_items=len(chunk),
            )
            if budget_stop:
                unconsolidated += [m for g in chunk for m in g["member_ids"]]
                unconsolidated += [m for c in pending for g in c for m in g["member_ids"]]
                break
            if output is None:
                last_error = error
                # Relance compacte bornée : le lot est scindé en deux, une seule fois, et
                # seulement si les étapes plus prioritaires restent finançables.
                higher = remaining_batches + meta_passes + 3  # lots restants, méta, comp/syn/porte
                if (
                    attempt == 0
                    and len(chunk) >= 2
                    and _retry_allowed(
                        session, run, step, extra_calls=2, higher_priority_calls=higher
                    )
                ):
                    attempt = 1
                    retries += 1
                    half = len(chunk) // 2
                    pending = [chunk[:half], chunk[half:], *pending]
                    _journal(
                        session,
                        run,
                        step,
                        "retry",
                        "facilitateur",
                        {
                            "attempt": attempt,
                            "split_into": [half, len(chunk) - half],
                            "reason": error,
                        },
                    )
                    continue
                status = "failed"
                unconsolidated += [m for g in chunk for m in g["member_ids"]]
                continue
            fams, nm = families_from_batch(output, chunk, notes)
            families_raw.extend(fams)
            not_merged += nm
    # Méta-consolidation (bornée) : familles issues de lots différents, natures compatibles.
    if meta_passes and families_raw and not budget_stop and not run.stop_reason:
        ordered = sorted(families_raw, key=lambda f: f["label"].lower())
        merged_all: list[dict[str, Any]] = []
        for start in range(0, len(ordered), META_CHUNK_SIZE):
            chunk_f = ordered[start : start + META_CHUNK_SIZE]
            if len(chunk_f) < 2:
                merged_all += chunk_f
                continue
            for i, f in enumerate(chunk_f, start=1):
                f["temp_id"] = f"T{start + i}"
            calls += 1
            output, error, budget_stop = _consolidation_output(
                session,
                run,
                llm,
                settings,
                prompt=build_meta_prompt(chunk_f),
                what=f"méta-consolidation ({len(chunk_f)} famille(s))",
                n_items=len(chunk_f),
            )
            if output is not None:
                merged = merge_families_from_meta(output, chunk_f, notes)
                notes.append(f"méta-consolidation : {len(chunk_f)} → {len(merged)} famille(s)")
                merged_all += merged
            else:
                last_error = error or last_error
                if not budget_stop and status == "ok":
                    status = "partial"
                notes.append("méta-consolidation non exploitable : familles des lots conservées")
                for f in chunk_f:
                    f.pop("temp_id", None)
                merged_all += chunk_f
            if budget_stop:
                break
        families_raw = merged_all
    if budget_stop:
        status = "failed"
    families, trace = finalize_families(families_raw, options)
    run.consolidation = {
        "status": status,
        "families": families,
        "not_merged_because": not_merged,
        "trace": trace,
        "atomic_count": len(options),
        "groups_after_premerge": len(groups),
        "cross_kind_groups": cross_kind,
        "family_count": len(families),
        "unconsolidated_option_ids": unconsolidated,
        "batches": len(batches),
        "calls": calls,
        "retries": retries,
        "notes": notes,
        "parse_error": last_error,
    }
    _journal(
        session,
        run,
        step,
        "result",
        "Greffier",
        {k: v for k, v in run.consolidation.items() if k not in {"families", "trace"}},
    )
    if not budget_stop:
        run.steps_done.append(step)


def _evidence_for_synthesis(run: _Run) -> list[dict[str, Any]]:
    """Toutes les preuves, étiquetées par provenance : entrée CEO, externe, modèle, hypothèse."""
    items: list[dict[str, Any]] = []
    provenance_by_status = {
        "verified": "ceo_input",
        "model_knowledge": "model_knowledge",
        "unverified": "hypothesis",
    }
    for i, e in enumerate(run.cartography.get("evidence", []), start=1):
        items.append(
            {
                "id": f"T0-EV-{i}",
                "claim": e["claim"],
                "source": e["source"],
                "reliability": "n/a",
                "provenance": provenance_by_status.get(e["status"], "hypothesis"),
                "expert_id": e["expert_id"],
            }
        )
    for e in run.evidence:
        items.append(
            {
                "id": e["id"],
                "claim": e.get("answer_summary") or e["question"],
                "source": e["source"],
                "reliability": e["reliability"],
                "provenance": e["provenance"],
                "status": e["status"],
            }
        )
    return items


# --- Comparaison ---------------------------------------------------------------------------------
def _comparison_rows(
    output: ComparisonOutput | None, retained: list[dict[str, Any]]
) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    """Lignes validées : familles retenues seulement ; renvoie (critères, lignes, manquantes)."""
    criteria = list(output.criteria) if output else []
    rows: list[dict[str, Any]] = []
    known = {f["family_id"] for f in retained}
    seen: set[str] = set()
    if output is not None:
        for row in output.rows:
            if row.family_id not in known or row.family_id in seen:
                continue
            seen.add(row.family_id)
            rows.append(
                {
                    "family_id": row.family_id,
                    "assessments": {k: v.model_dump() for k, v in row.assessments.items()},
                }
            )
    missing = sorted(known - seen)
    if criteria:
        for built in rows:
            if any(c not in built["assessments"] for c in criteria):
                missing.append(built["family_id"])
    return criteria, rows, sorted(set(missing))


def _request_texts(run: _Run) -> list[str]:
    m = run.mission
    f = run.framing
    return [
        m.input_text,
        m.context_text,
        m.ceo_preference,
        f.problem_understood if f else "",
        f.assumed_objective if f else "",
        *(f.constraints if f else []),
    ]


def _step_comparison(session: Session, run: _Run, llm: LLMClient, settings: Settings) -> None:
    """Comparaison des familles avec couverture stratégique protégée à chaque tentative (B7/B9).

    Sélection stratifiée sous plafond dur (`COMPARISON_MAX_FAMILIES`) : familles individuellement
    indispensables (hard : citées dans la demande, désaccord unique), puis UNE famille par exigence
    de représentation (nature, dimension critique, non-action, minorité matérielle, désaccord,
    multi-dimensions), puis facultatives. Si les hard dépassent le plafond : conflit déclaré,
    aucune tentative, `failed`, porte bloquée. Une relance compacte au plus, qui n'écarte que des
    facultatives et n'est financée que si synthèse et porte restent finançables (B8). `status = ok`
    seulement si hard et couverture sont préservées et chaque famille retenue évaluée.
    """
    step = "comparaison"
    if run.stop_reason:
        _skip(session, run, step, f"arrêt en cours : {run.stop_reason}")
        return
    families = run.consolidation.get("families", [])
    if not families or run.framing is None:
        _skip(session, run, step, "aucune famille stratégique à comparer")
        return
    option_labels = {o["option_id"]: o["label"] for o in run.cartography.get("options", [])}
    for f in families:
        f["option_labels"] = [option_labels[o] for o in f["option_ids"] if o in option_labels]
    critical = {d.name for d in run.framing.dimensions if d.presumed_criticality == "high"}
    coverage = coverage_requirements(
        families, request_texts=_request_texts(run), critical_dimensions=critical
    )
    picked = select_families_for_attempt(families, coverage, cap=COMPARISON_MAX_FAMILIES)
    for f in families:
        f.pop("option_labels", None)
    hard_ids = sorted(coverage["hard"], key=lambda x: int(x[1:]))
    selection = picked["selection"]
    _journal(
        session,
        run,
        step,
        "selection",
        "facilitateur",
        {
            "families_total": len(families),
            "cap": COMPARISON_MAX_FAMILIES,
            "hard_mandatory": hard_ids,
            "hard_conflict": picked["hard_conflict"],
            "coverage_requirements": [
                {
                    "id": r["id"],
                    "satisfied_by": r.get("satisfied_by"),
                    "candidates": r["candidates"],
                }
                for r in picked["requirements"]
            ],
            "unsatisfied_requirements": picked["unsatisfied"],
            "retained": [f["family_id"] for f in picked["retained"]],
            "deferred": [d["family_id"] for d in picked["deferred"]],
            "selection": selection,
        },
    )
    base_payload: dict[str, Any] = {
        "cap": COMPARISON_MAX_FAMILIES,
        "hard_mandatory_family_ids": hard_ids,
        "hard_mandatory_conflict": picked["hard_conflict"],
        "coverage_requirements": [
            {"id": r["id"], "label": r["label"], "satisfied_by": r.get("satisfied_by")}
            for r in picked["requirements"]
        ],
        "unsatisfied_requirements": picked["unsatisfied"],
        "selection": selection,
    }
    if picked["hard_conflict"]:
        # Fail-closed : plus de familles individuellement indispensables que le plafond. Aucune
        # tentative n'envoie plus de `cap` familles ; aucune n'est écartée en silence.
        run.comparison = {
            **base_payload,
            "status": "failed",
            "criteria": [],
            "rows": [],
            "retained_family_ids": [],
            "mandatory_family_ids": hard_ids,
            "coverage": {fid: selection[fid]["reasons"] for fid in hard_ids},
            "coverage_preserved": False,
            "not_compared": [],
            "missing_family_ids": [],
            "attempts": [],
            "notes": "",
            "coverage_note": (
                f"hard_mandatory_exceeds_cap : {len(hard_ids)} familles individuellement "
                f"indispensables pour {COMPARISON_MAX_FAMILIES} places — comparaison non "
                "réalisable sous le plafond sans perdre une alternative demandée"
            ),
            "parse_error": "",
        }
        _journal(
            session,
            run,
            step,
            "hard_mandatory_exceeds_cap",
            "facilitateur",
            {"hard_mandatory": hard_ids, "cap": COMPARISON_MAX_FAMILIES},
        )
        run.steps_done.append(step)
        return
    retained, deferred = picked["retained"], picked["deferred"]
    mandatory: dict[str, list[str]] = {
        fid: s["reasons"] for fid, s in selection.items() if s["role"] in {"hard", "coverage"}
    }
    unknowns = list(run.framing.global_unknowns) + [
        u["text"] for u in run.cartography.get("unknowns", [])
    ]
    evidence = _evidence_for_synthesis(run)
    attempts: list[dict[str, Any]] = []
    output: ComparisonOutput | None = None
    error = ""
    compared = retained
    coverage_note = ""
    for attempt in (1, 2):
        response, output, error = _call_structured(
            session,
            run,
            llm,
            settings,
            step=step,
            actor="Synthétiseur",
            system=COMPARISON_SYSTEM,
            prompt=build_compact_comparison_prompt(
                problem=run.framing.problem_understood,
                constraints=list(run.framing.constraints),
                families=compared,
                evidence=evidence,
                unknowns=unknowns,
            ),
            call_type=COMPARISON_CALL_TYPE,
            model=ComparisonOutput,
            n_items=len(compared),
        )
        if response is None:
            run.comparison = {
                **base_payload,
                "status": "failed",
                "criteria": [],
                "rows": [],
                "retained_family_ids": [f["family_id"] for f in retained],
                "mandatory_family_ids": sorted(mandatory, key=lambda x: int(x[1:])),
                "coverage": mandatory,
                "coverage_preserved": False,
                "not_compared": deferred,
                "attempts": attempts,
                "parse_error": "budget",
            }
            return
        attempts.append({"attempt": attempt, "families": len(compared), "parse_error": error})
        if output is not None or attempt == 2:
            break
        # Relance compacte bornée et STRATIFIÉE : hard et couverture sont tous conservés ; seules
        # les facultatives les moins soutenues sont écartées. Sans marge, pas de relance.
        must = [f for f in compared if f["family_id"] in mandatory]
        optional = sorted(
            [f for f in compared if f["family_id"] not in mandatory],
            key=lambda f: (-len(f.get("supporting_experts", [])), int(f["family_id"][1:])),
        )
        target_size = max(len(must), len(compared) // 2)
        keep_optional = optional[: max(0, target_size - len(must))]
        if len(must) + len(keep_optional) >= len(compared):
            coverage_note = (
                "relance impossible sans sacrifier une famille indispensable ou nécessaire à la "
                "couverture stratégique"
            )
            _journal(
                session,
                run,
                step,
                "retry_refused_coverage",
                "facilitateur",
                {"mandatory": len(must), "compared": len(compared)},
            )
            break
        if not _retry_allowed(session, run, step, extra_calls=1, higher_priority_calls=2):
            coverage_note = "relance non financée : synthèse et porte qualité prioritaires"
            break
        kept_ids = {f["family_id"] for f in must + keep_optional}
        for f in compared:
            if f["family_id"] not in kept_ids:
                selection[f["family_id"]] = {
                    "role": "dropped_on_retry",
                    "reasons": [
                        "facultative pour la couverture ; écartée de la relance compacte après "
                        "sortie non exploitable"
                    ],
                }
                deferred.append(
                    {
                        "family_id": f["family_id"],
                        "label": f["label"],
                        "kind": f["kind"],
                        "reason": selection[f["family_id"]]["reasons"][0],
                    }
                )
        compared = sorted(must + keep_optional, key=lambda f: int(f["family_id"][1:]))
        _journal(
            session,
            run,
            step,
            "retry",
            "facilitateur",
            {
                "attempt": 2,
                "families": len(compared),
                "mandatory_kept": len(must),
                "reason": error,
            },
        )
    criteria, rows, missing = _comparison_rows(output, compared)
    compared_ids = {f["family_id"] for f in compared}
    coverage_preserved = all(fid in compared_ids for fid in mandatory) and not picked["unsatisfied"]
    if output is None:
        status = "failed"
    elif missing or not criteria or not rows or not coverage_preserved:
        status = "partial"
    else:
        status = "ok"
    if output is not None:
        for fid in missing:
            rows.append(
                {"family_id": fid, "assessments": {}, "note": "non évaluée par la comparaison"}
            )
    if picked["unsatisfied"] and not coverage_note:
        coverage_note = "exigences de couverture non satisfaisables sous le plafond : " + ", ".join(
            picked["unsatisfied"]
        )
    run.comparison = {
        **base_payload,
        "status": status,
        "criteria": criteria,
        "rows": rows,
        "retained_family_ids": [f["family_id"] for f in compared],
        "mandatory_family_ids": sorted(mandatory, key=lambda x: int(x[1:])),
        "coverage": mandatory,
        "coverage_preserved": coverage_preserved,
        "not_compared": deferred,
        "missing_family_ids": missing,
        "attempts": attempts,
        "notes": output.notes if output else coverage_note,
        "coverage_note": coverage_note,
        "parse_error": error,
    }
    _journal(
        session,
        run,
        step,
        "result",
        "Synthétiseur",
        {
            "status": status,
            "criteria": criteria,
            "rows": len(rows),
            "retained": len(compared),
            "hard_mandatory": len(hard_ids),
            "mandatory": len(mandatory),
            "coverage_preserved": coverage_preserved,
            "not_compared": len(deferred),
            "missing": missing,
            "attempts": attempts,
            "coverage_note": coverage_note,
            "parse_error": error,
        },
    )
    run.steps_done.append(step)


# --- Synthèse et porte qualité -------------------------------------------------------------------
def _synthesis_matter(run: _Run, residual: list[dict[str, Any]]) -> str:
    f = run.framing
    m = run.mission
    parts: list[str] = [
        f"Classe de décision : {m.effective_class}",
        f"Problème compris : {f.problem_understood if f else ''}",
        f"Objectif supposé : {f.assumed_objective if f else ''}",
    ]
    if f and f.constraints:
        parts.append("Contraintes : " + " ; ".join(f.constraints))
    if f and f.assumptions:
        parts.append(
            "Hypothèses de la demande (non vérifiées) : "
            + " ; ".join(f"{a} [{epistemic_tag(a)}]" for a in f.assumptions)
        )
    if f and f.contestation.status == "raised":
        parts.append(
            f"Contestation soulevée au cadrage : {f.contestation.target} — "
            f"{f.contestation.argument}"
        )
    parts.append("Positions (initiale → après révision) :")
    for rev in run.revisions:
        parts.append(
            f"- {rev['label']} : « {rev['previous_position']} » → {rev['decision']} → "
            f"« {rev['revised_position']} » ({rev['reason']})"
        )
    if not run.revisions:
        for eid, pos in run.current_positions.items():
            parts.append(f"- {run.labels.get(eid, eid)} : {pos}")
    parts.append("Familles stratégiques :")
    for fam in run.consolidation.get("families", []):
        parts.append(
            f"- {fam['family_id']} {fam['label']} [{fam['kind']}] — options "
            + ", ".join(fam["option_ids"])
            + (
                f" — désaccords internes : {' ; '.join(fam['internal_disagreements'])}"
                if fam.get("internal_disagreements")
                else ""
            )
        )
    if run.consolidation.get("unconsolidated_option_ids"):
        parts.append(
            "Options NON consolidées (échec technique de consolidation, à ne pas présenter comme "
            "familles) : " + ", ".join(run.consolidation["unconsolidated_option_ids"])
        )
    if run.comparison.get("status") and run.comparison["status"] != "ok":
        parts.append(
            f"Comparaison INVALIDE ou incomplète (statut {run.comparison['status']}) : aucune "
            "prétention à une comparaison valide."
        )
    if run.comparison.get("not_compared"):
        parts.append(
            "Familles non comparées (plafond de comparaison) : "
            + ", ".join(f["family_id"] for f in run.comparison["not_compared"])
        )
    if run.comparison.get("rows"):
        parts.append("Comparaison (" + ", ".join(run.comparison.get("criteria", [])) + ") :")
        for row in run.comparison["rows"]:
            cells = " ; ".join(
                f"{k}: {v['value']} [{v['basis']}]" for k, v in row["assessments"].items()
            )
            parts.append(f"- {row['family_id']} : {cells or row.get('note', '')}")
    parts.append("Preuves (provenance) :")
    for e in _evidence_for_synthesis(run):
        parts.append(
            f"- {e['id']} [{e['provenance']}] {e['claim']} — source : "
            f"{e.get('source') or 'aucune'} — fiabilité {e.get('reliability', 'unknown')}"
        )
    unavailable = [e for e in run.research if e["status"] in {"unavailable", "not_found", "error"}]
    if unavailable:
        parts.append(
            "Questions factuelles NON résolues (recherche indisponible ou sans résultat) : "
            + " ; ".join(e["question"] for e in unavailable)
        )
    st = run.steelman
    if st.get("required"):
        parts.append(
            f"Steelman : requis ({st.get('reason')}) — statut {st.get('status')} ; cible "
            f"{st.get('target', '')} ; critique : {st.get('critique', '') or '(aucune)'}"
        )
    parts.append("Désaccords résiduels (à conserver) :")
    if residual:
        for d in residual:
            parts.append(
                f"- {d['id']} [{d['nature']}] {' / '.join(d['between'])} : {d['description']}"
            )
    else:
        parts.append("- aucun")
    parts.append(
        "Rappels : la preuve prime sur la majorité ; aucune obligation de recommander de "
        "construire ; si l'information manque, information_insufficient = true."
    )
    return "\n".join(parts)


def _step_synthesis(session: Session, run: _Run, llm: LLMClient, settings: Settings) -> None:
    step = "synthese"
    m = run.mission
    if run.stop_reason:
        _skip(session, run, step, f"arrêt en cours : {run.stop_reason}")
        return
    if not run.consolidation.get("families"):
        _skip(session, run, step, "aucune matière consolidée")
        return
    residual = _residual_disagreements(run)
    response, output, error = _call_structured(
        session,
        run,
        llm,
        settings,
        step=step,
        actor="Synthétiseur",
        system=SYNTHESIS_SYSTEM,
        prompt=build_synthesis_prompt(matter=_synthesis_matter(run, residual)),
        call_type=SYNTHESIS_CALL_TYPE,
        model=RecommendationOutput,
    )
    if response is None:
        return
    if output is None:
        run.recommendation = {"status": "failed", "error": error}
        _journal(session, run, step, "failed", "Synthétiseur", {"parse_error": error})
        return
    rec: dict[str, Any] = output.model_dump()
    # Déterministe : les désaccords résiduels du facilitateur ne peuvent pas disparaître.
    known_desc = {d["description"] for d in rec["residual_disagreements"]}
    for d in residual:
        if d["description"] not in known_desc:
            rec["residual_disagreements"].append(
                {"between": d["between"], "nature": d["nature"], "description": d["description"]}
            )
    rec["status"] = "produced"
    rec["class"] = m.effective_class
    rec["requires_ceo_decision"] = True  # les agents recommandent ; ils ne décident jamais
    rec["ceo_decision_mandatory_by_class"] = m.effective_class in STEELMAN_CLASSES
    rec["ceo_arbitration_required"] = any(
        d["nature"] == "value" for d in rec["residual_disagreements"]
    )
    # `decision_ready` n'est jamais vrai avant la porte qualité : information suffisante ET porte
    # passée. Une porte non exécutée (budget) laisse la recommandation « bloquée qualité ».
    rec["decision_ready"] = False
    rec["quality_blocked"] = True
    rec["quality_gate_status"] = "pending"
    rec["families_count"] = len(run.consolidation.get("families", []))
    run.recommendation = rec
    _journal(
        session,
        run,
        step,
        "result",
        "Synthétiseur",
        {
            "kind": rec["recommendation"]["kind"],
            "family_id": rec["recommendation"]["family_id"],
            "confidence": rec["confidence"]["level"],
            "information_insufficient": rec["information_insufficient"],
            "residual_disagreements": len(rec["residual_disagreements"]),
            "ceo_arbitration_required": rec["ceo_arbitration_required"],
            "parse_error": error,
        },
    )
    run.steps_done.append(step)


def _pipeline_integrity_failures(run: _Run) -> list[tuple[str, str]]:
    """Étapes obligatoires invalides : (étape, cause). Vide = intégrité du pipeline établie.

    required_pipeline_integrity = confrontation valide ∧ steelman valide si requis ∧
    consolidation valide ∧ comparaison valide ∧ synthèse valide.
    """
    failures: list[tuple[str, str]] = []
    if "confrontation" not in run.steps_done:
        failures.append(("confrontation", "étape non réalisée"))
    else:
        broken = [
            run.labels.get(eid, eid) for eid, out in run.confrontations.items() if out is None
        ]
        if broken:
            failures.append(("confrontation", f"sortie non exploitable pour {', '.join(broken)}"))
    st = run.steelman
    if st.get("required") and st.get("status") not in {"accepted", "accepted_partial"}:
        failures.append(("steelman", f"requis ({st.get('reason')}) : {st.get('status')}"))
    cons = run.consolidation
    if cons.get("status") != "ok":
        failures.append(
            (
                "consolidation",
                f"statut {cons.get('status', 'absente')}"
                + (
                    f" ; {len(cons.get('unconsolidated_option_ids', []))} option(s) non "
                    f"consolidée(s)"
                    if cons.get("unconsolidated_option_ids")
                    else ""
                ),
            )
        )
    comp = run.comparison
    if comp.get("status") != "ok":
        failures.append(
            (
                "comparaison",
                f"statut {comp.get('status', 'absente')}"
                + (
                    f" ; familles sans évaluation : {', '.join(comp.get('missing_family_ids', []))}"
                    if comp.get("missing_family_ids")
                    else ""
                ),
            )
        )
    if run.recommendation.get("status") != "produced":
        failures.append(("synthese", f"statut {run.recommendation.get('status', 'absente')}"))
    return failures


def _step_gate(session: Session, run: _Run, llm: LLMClient, settings: Settings) -> None:
    step = "porte_qualite"
    if run.stop_reason:
        _skip(session, run, step, f"arrêt en cours : {run.stop_reason}")
        return
    if run.recommendation.get("status") != "produced":
        _skip(session, run, step, "aucune recommandation à contrôler")
        return
    residual = _residual_disagreements(run)
    st = run.steelman
    steelman_required = bool(st.get("required"))
    steelman_done = st.get("status") in {"accepted", "accepted_partial"}
    unknowns = list(run.framing.global_unknowns) if run.framing else []
    response, output, error = _call_structured(
        session,
        run,
        llm,
        settings,
        step=step,
        actor="Porte qualité",
        system=GATE_SYSTEM,
        prompt=build_gate_prompt(
            recommendation_json=json.dumps(run.recommendation, ensure_ascii=False),
            families=run.consolidation.get("families", []),
            residual=residual,
            steelman_required=steelman_required,
            steelman_done=steelman_done,
            unknowns=unknowns,
        ),
        call_type=GATE_CALL_TYPE,
        model=GateOutput,
    )
    if response is None:
        return
    checks: dict[str, bool] = dict(output.checks) if output else {}
    issues: list[str] = (
        list(output.issues) if output else [f"porte qualité non exploitable : {error}"]
    )
    # Contrôles déterministes : ils priment sur l'avis de l'instance.
    checks["steelman_done_if_required"] = (not steelman_required) or steelman_done
    if steelman_required and not steelman_done:
        issues.append(
            f"steelman requis ({st.get('reason')}) mais non réalisé/reconnu : {st.get('status')}"
        )
    rec_residual = run.recommendation.get("residual_disagreements", [])
    checks["minorities_preserved"] = len(rec_residual) >= len(residual)
    checks["no_forced_consensus"] = checks.get("no_forced_consensus", True) and len(
        rec_residual
    ) >= len(residual)
    # Veto déterministe d'intégrité du pipeline (fail-closed) : les étapes obligatoires doivent
    # être valides ; l'instance LLM de porte ne peut jamais écraser ce veto.
    integrity_failures = _pipeline_integrity_failures(run)
    checks["pipeline_integrity"] = not integrity_failures
    issues += [f"upstream_stage_failed:{stage} — {why}" for stage, why in integrity_failures]
    passed = bool(output.passed) if output else False
    passed = passed and all(checks.values())
    run.gate = {
        "passed": passed,
        "checks": checks,
        "issues": issues,
        "integrity_failures": [f"upstream_stage_failed:{s}" for s, _ in integrity_failures],
        "llm_verdict": bool(output.passed) if output else None,
        "parse_error": error,
    }
    rec = run.recommendation
    rec["gate"] = run.gate
    # La porte conditionne réellement `decision_ready` : la proposition est conservée pour audit
    # même si la porte échoue, mais elle ne peut pas être présentée comme prête à décider.
    rec["quality_gate_status"] = "passed" if passed else "failed"
    rec["quality_blocked"] = not passed
    rec["decision_ready"] = bool(passed) and not bool(rec.get("information_insufficient"))
    _journal(
        session,
        run,
        step,
        "result",
        "Porte qualité",
        {
            **run.gate,
            "decision_ready": rec["decision_ready"],
            "quality_blocked": rec["quality_blocked"],
        },
    )
    run.steps_done.append(step)


def _deliberation_stop(run: _Run, residual: list[dict[str, Any]]) -> dict[str, Any]:
    reason: str
    framing_output_failed = (
        run.failure.get("kind") == "structured_output" and run.failure.get("step") == "cadrage"
    )
    if run.stop_reason.startswith("framing_failed") or framing_output_failed:
        reason = "framing_failed"
    elif (
        run.stop_reason in BUDGET_STOP_REASONS or run.stop_reason == "critical_dimension_uncovered"
    ):
        reason = "budget"
    elif any(e["status"] in {"unavailable", "not_found", "error"} for e in run.research):
        reason = "missing_external_info"
    elif any(d["nature"] == "value" for d in residual):
        reason = "ceo_decision_needed"
    elif residual:
        reason = "residual_only"
    elif "revision" in run.steps_done:
        called = any(r.get("called") for r in run.revisions)
        reason = "converged" if called else "no_new_information"
    else:
        reason = "not_deliberated"
    return {"reason": reason, "stop_reason": run.stop_reason, "steps_done": list(run.steps_done)}


def _deliberation_payload(run: _Run) -> dict[str, Any]:
    residual = _residual_disagreements(run)
    return {
        "steps_done": list(run.steps_done),
        "steps_skipped": list(run.steps_skipped),
        "confrontation": {
            "objections": run.objections,
            "outputs": {
                eid: (out.model_dump() if out else None) for eid, out in run.confrontations.items()
            },
        },
        "steelman": run.steelman,
        "research": run.research,
        "evidence": _evidence_for_synthesis(run),
        "revisions": run.revisions,
        "positions_after": {run.labels.get(k, k): v for k, v in run.current_positions.items()},
        "consolidation": run.consolidation,
        "comparison": run.comparison,
        "gate": run.gate,
        "residual_disagreements": residual,
        "stop": _deliberation_stop(run, residual),
        "budget_request": run.budget_request,
    }


# --- Lectures et actions CEO --------------------------------------------------------------
def get_mission(session: Session, mission_id: int) -> Mission:
    """Retourne une mission ou lève `MissionNotFoundError`."""
    mission = session.get(Mission, mission_id)
    if mission is None:
        raise MissionNotFoundError(mission_id)
    return mission


def list_missions(session: Session, limit: int = 100) -> list[Mission]:
    """Liste les missions, de la plus récente à la plus ancienne."""
    return list(
        session.execute(select(Mission).order_by(Mission.id.desc()).limit(limit)).scalars().all()
    )


def list_journal(session: Session, mission_id: int) -> list[MissionJournalEntry]:
    """Journal complet d'une mission, dans l'ordre."""
    return list(
        session.execute(
            select(MissionJournalEntry)
            .where(MissionJournalEntry.mission_id == mission_id)
            .order_by(MissionJournalEntry.seq.asc())
        )
        .scalars()
        .all()
    )


def apply_ceo_action(session: Session, mission: Mission, action: str, notes: str) -> Mission:
    """Action CEO explicite sur un rapport `candidate`. Ne déclenche aucune exécution."""
    if action not in CEO_ACTIONS:
        raise ValueError(f"action inconnue : {action}")
    if mission.status != "candidate":
        raise InvalidMissionStatusError(
            f"la mission est en statut « {mission.status} » : action CEO impossible"
        )
    mission.status = CEO_ACTIONS[action]
    if notes.strip():
        mission.ceo_notes = (mission.ceo_notes + "\n" if mission.ceo_notes else "") + notes.strip()
    session.commit()
    session.refresh(mission)
    return mission


def mission_payload(mission: Mission) -> dict[str, Any]:
    """Vue complète d'une mission (champs JSON décodés) pour l'API."""

    def _load(raw: str) -> Any:
        return json.loads(raw) if raw else None

    return {
        "id": mission.id,
        "input_type": mission.input_type,
        "input_text": mission.input_text,
        "context_text": mission.context_text,
        "ceo_preference": mission.ceo_preference,
        "declared_class": mission.declared_class,
        "effective_class": mission.effective_class,
        "class_is_provisional": mission.class_is_provisional,
        "status": mission.status,
        "stop_reason": mission.stop_reason,
        "max_llm_calls": mission.max_llm_calls,
        "max_cost_eur": mission.max_cost_eur,
        "llm_calls_used": mission.llm_calls_used,
        "input_tokens": mission.input_tokens,
        "output_tokens": mission.output_tokens,
        "cost_eur": mission.cost_eur,
        "ceo_notes": mission.ceo_notes,
        "created_at": mission.created_at,
        "updated_at": mission.updated_at,
        "framing": _load(mission.framing_json),
        "composition": _load(mission.composition_json),
        "cartography": _load(mission.cartography_json),
        "report": _load(mission.report_json),
        "deliberation": _load(mission.deliberation_json),
        "recommendation": _load(mission.recommendation_json),
        "failure": _load(mission.failure_json),
    }
