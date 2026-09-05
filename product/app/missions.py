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
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import Mission, MissionJournalEntry
from app.llm import LLMClient, LLMResponse
from app.mission_budget import BudgetExceededError, BudgetLedger
from app.mission_cartography import (
    anonymize_labels,
    build_cartography,
    collect_options,
    relations_table,
    residual_ambiguities,
)
from app.mission_composition import ExpertSpec, compose
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
from app.mission_schemas import (
    ClerkOutput,
    ExpertOutput,
    FramingOutput,
    SelfQualificationOutput,
    parse_structured,
)
from app.observability import observed
from app.schemas import MissionCreateRequest

PHASE = "otv1_inc1"
PROVISIONAL_CLASS = "importante_provisoire"
CLASS_RANK = {
    "courante": 0,
    "importante": 1,
    PROVISIONAL_CLASS: 1,
    "structurante": 2,
    "critique": 3,
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
) -> LLMResponse | None:
    """Appel structuré sous budget : estimation, refus/arrêt, appel, enregistrement, journal.

    Retourne None si le budget interdit l'appel (la mission s'arrête proprement : `stop_reason`).
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
    response = client.complete_structured(
        system=system, prompt=prompt, call_type=call_type, max_tokens=max_tokens
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
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "cost_eur": cost,
            "budget": run.ledger.snapshot(),
        },
    )
    return response


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
    suggested = run.framing.suggested_class
    signals = list(run.framing.escalation_signals)
    if not suggested and not signals:
        return info
    current_rank = CLASS_RANK.get(m.effective_class, 1)
    suggested_rank = CLASS_RANK.get(suggested, -1) if suggested else -1
    if suggested_rank > current_rank:
        if m.class_is_provisional:
            m.effective_class = suggested
            session.commit()
            info["effective"] = suggested
            info["escalation"] = f"classe provisoire escaladée à « {suggested} » par le cadrage"
        else:
            info["escalation"] = (
                f"le cadrage recommande « {suggested} » ; la classe déclarée par le CEO "
                f"(« {m.declared_class} ») est conservée — escalade soumise au CEO"
            )
    elif signals:
        info["escalation"] = "signaux d'escalade consignés sans changement de classe"
    _journal(
        session,
        run,
        "cadrage",
        "class_escalation",
        "facilitateur",
        {**info, "signals": signals, "suggested_class": suggested},
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
        max_llm_calls=request.max_llm_calls or settings.mission_max_llm_calls,
        max_cost_eur=request.max_cost_eur or settings.mission_max_cost_eur,
    )
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
            "budget": run.ledger.snapshot(),
        },
    )
    try:
        _step_framing(session, run, llm, settings)
        class_info = _escalate_class(session, run)
        _step_composition(session, run, settings)
        _step_tour0(session, run, llm, settings)
        _step_self_qualification(session, run, llm, settings)
        _step_clerk(session, run, llm, settings)
        _finalize(session, run, class_info)
    except Exception as exc:
        mission.status = "failed"
        mission.stop_reason = f"{type(exc).__name__}: {str(exc)[:200]}"
        session.commit()
        _journal(session, run, "mission", "failed", "facilitateur", {"error": mission.stop_reason})
        raise
    return mission


def _step_framing(session: Session, run: _Run, llm: LLMClient, settings: Settings) -> None:
    m = run.mission
    prompt = build_framing_prompt(
        input_type=m.input_type,
        input_text=m.input_text,
        context_text=m.context_text,
        ceo_preference=m.ceo_preference,
        effective_class=m.effective_class,
    )
    response = _call(
        session,
        run,
        llm,
        settings,
        step="cadrage",
        actor="Cadrage",
        system=FRAMING_SYSTEM,
        prompt=prompt,
        call_type=FRAMING_CALL_TYPE,
        max_tokens=settings.mission_max_tokens_framing,
    )
    if response is None:
        run.framing_error = f"cadrage non exécuté ({run.stop_reason})"
        return
    framing, error = parse_structured(response.text, FramingOutput)
    run.framing = framing
    run.framing_error = error
    m.framing_json = json.dumps(
        {"parsed": framing.model_dump() if framing else None, "error": error, "raw": response.text},
        ensure_ascii=False,
    )
    session.commit()
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
    max_experts = run.ledger.max_affordable_experts(reserved_calls=1)
    result = compose(
        framing,
        effective_class=m.effective_class,
        ceo_preference=m.ceo_preference,
        max_angles_per_cell=settings.mission_max_angles_per_cell,
        max_experts=max_experts,
    )
    run.experts = result.experts
    run.composition = result.to_dict()
    if not result.experts and not run.stop_reason:
        run.stop_reason = "budget_insufficient_for_exploration"
        _journal(
            session,
            run,
            "composition",
            "budget_stop",
            "facilitateur",
            {"reason": run.stop_reason, "budget": run.ledger.snapshot()},
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
        response = _call(
            session,
            run,
            llm,
            settings,
            step="tour0",
            actor=spec.expert_id,
            system=EXPERT_SYSTEM,
            prompt=prompt,
            call_type=EXPERT_CALL_TYPE,
            max_tokens=settings.mission_max_tokens_expert,
        )
        if response is None:
            continue
        output, error = parse_structured(response.text, ExpertOutput)
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
        others = [
            (labels[o["expert_id"]], o["output"].position)
            for o in answered
            if o["expert_id"] != r["expert_id"]
        ]
        prompt = build_self_qualification_prompt(
            own_label=labels[r["expert_id"]], own_position=r["output"].position, others=others
        )
        response = _call(
            session,
            run,
            llm,
            settings,
            step="auto_qualification",
            actor=r["expert_id"],
            system=SELF_QUAL_SYSTEM,
            prompt=prompt,
            call_type=SELF_QUAL_CALL_TYPE,
            max_tokens=settings.mission_max_tokens_self_qualification,
        )
        if response is None:
            break
        output, error = parse_structured(response.text, SelfQualificationOutput)
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
    prompt = build_clerk_prompt(
        options=collect_options(run.expert_results),
        positions=[(labels[r["expert_id"]], r["output"].position) for r in answered],
        ambiguities=ambiguities,
    )
    response = _call(
        session,
        run,
        llm,
        settings,
        step="greffier",
        actor="Greffier",
        system=CLERK_SYSTEM,
        prompt=prompt,
        call_type=CLERK_CALL_TYPE,
        max_tokens=settings.mission_max_tokens_clerk,
    )
    if response is None:
        return
    output, error = parse_structured(response.text, ClerkOutput)
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


def _finalize(session: Session, run: _Run, class_info: dict[str, Any]) -> None:
    m = run.mission
    answered = [r for r in run.expert_results if r["output"] is not None]
    labels = anonymize_labels([r["expert_id"] for r in answered])
    cartography = build_cartography(
        expert_results=run.expert_results, self_qual=run.self_qual, clerk=run.clerk, labels=labels
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
        budget=run.ledger.snapshot(),
        stop_reason=run.stop_reason,
    )
    m.cartography_json = json.dumps(cartography, ensure_ascii=False, default=str)
    m.report_json = json.dumps(report, ensure_ascii=False, default=str)
    m.stop_reason = run.stop_reason
    m.status = "candidate"
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
            "budget": run.ledger.snapshot(),
        },
    )


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
    }
