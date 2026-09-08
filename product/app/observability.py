"""Observabilité du runtime produit (Phase 8) — **lecture seule**, sans changer le métier.

Deux mécanismes :
  * `ObservedLLMClient` — un **wrapper** autour d'un `LLMClient` qui mesure la durée, journalise
    chaque appel (succès ou erreur) dans `llm_call_logs`, puis **relance** l'erreur pour ne pas
    changer le comportement existant. Les agents ne connaissent pas la base : l'instrumentation
    est branchée au niveau **service** (`observed(...)`).
  * `log_product_event` — un helper simple pour tracer les événements produit importants dans
    `product_event_logs`.

On ne stocke **jamais** le prompt complet : seulement un **preview tronqué**. Aucun secret n'y
figure (la clé API n'est pas dans le prompt). Les fonctions de lecture n'écrivent rien.
"""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select

from app.db import LLMCallLog, ProductEventLog
from app.llm import LLMResponse, StructuredCompletionUnsupportedError, estimate_cost_eur

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.llm import LLMClient

PREVIEW_LIMIT = 500


def _truncate(text: str, limit: int = PREVIEW_LIMIT) -> str:
    """Tronque proprement un texte pour le preview (ajoute une ellipse si coupé)."""
    if len(text) <= limit:
        return text
    return text[:limit] + "…"


class ObservedLLMClient:
    """Wrapper d'un `LLMClient` qui journalise chaque appel `complete` (sans changer le retour)."""

    def __init__(
        self,
        inner: LLMClient,
        session: Session,
        phase: str,
        agent_name: str,
        operation_type: str,
        model: str = "unknown",
        provider: str = "anthropic",
        mission_id: int | None = None,
        price_in_per_mtok: float = 0.0,
        price_out_per_mtok: float = 0.0,
    ) -> None:
        self._inner = inner
        self._session = session
        self._phase = phase
        self._agent_name = agent_name
        self._operation_type = operation_type
        self._model = model or "unknown"
        self._provider = provider or "anthropic"
        self._mission_id = mission_id
        self._price_in = price_in_per_mtok
        self._price_out = price_out_per_mtok

    def complete(self, prompt: str) -> str:
        """Appelle le vrai client, journalise (succès/erreur + durée), puis relance si erreur."""
        start = time.perf_counter()
        try:
            response = self._inner.complete(prompt)
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start) * 1000)
            self._log(
                prompt=prompt,
                response="",
                status="error",
                error=f"{type(exc).__name__}: {exc}",
                duration_ms=duration_ms,
            )
            raise
        duration_ms = int((time.perf_counter() - start) * 1000)
        self._log(
            prompt=prompt,
            response=response,
            status="success",
            error="",
            duration_ms=duration_ms,
        )
        return response

    def complete_structured(
        self, *, system: str, prompt: str, call_type: str, max_tokens: int
    ) -> LLMResponse:
        """Chemin structuré (OT-V1) : journalise tokens, coût estimé et type d'appel.

        Le client interne doit implémenter `complete_structured` ; sinon une erreur explicite est
        levée (aucun repli silencieux sur `complete`, qui perdrait l'usage et le system prompt).
        """
        inner_structured = getattr(self._inner, "complete_structured", None)
        if inner_structured is None:
            raise StructuredCompletionUnsupportedError(
                f"{type(self._inner).__name__} n'implémente pas complete_structured"
            )
        start = time.perf_counter()
        preview_prompt = f"[system] {system}\n[user] {prompt}"
        try:
            response: LLMResponse = inner_structured(
                system=system, prompt=prompt, call_type=call_type, max_tokens=max_tokens
            )
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start) * 1000)
            self._log(
                prompt=preview_prompt,
                response="",
                status="error",
                error=f"{type(exc).__name__}: {exc}",
                duration_ms=duration_ms,
                call_type=call_type,
            )
            raise
        duration_ms = int((time.perf_counter() - start) * 1000)
        cost = estimate_cost_eur(
            response.usage.input_tokens,
            response.usage.output_tokens,
            self._price_in,
            self._price_out,
        )
        self._log(
            prompt=preview_prompt,
            response=response.text,
            status="success",
            error="",
            duration_ms=duration_ms,
            call_type=call_type,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cost_eur=cost,
        )
        return response

    def _log(
        self,
        prompt: str,
        response: str,
        status: str,
        error: str,
        duration_ms: int,
        call_type: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        cost_eur: float | None = None,
    ) -> None:
        """Ajoute une ligne `llm_call_logs` à la session (persistée au commit du service)."""
        self._session.add(
            LLMCallLog(
                phase=self._phase,
                agent_name=self._agent_name,
                operation_type=self._operation_type,
                provider=self._provider,
                model=self._model,
                prompt_preview=_truncate(prompt),
                response_preview=_truncate(response),
                status=status,
                error=_truncate(error),
                duration_ms=duration_ms,
                call_type=call_type,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_eur=cost_eur,
                mission_id=self._mission_id,
            )
        )


def observed(
    inner: LLMClient,
    session: Session,
    phase: str,
    agent_name: str,
    operation_type: str,
    model: str = "unknown",
    mission_id: int | None = None,
    price_in_per_mtok: float = 0.0,
    price_out_per_mtok: float = 0.0,
) -> ObservedLLMClient:
    """Fabrique un `ObservedLLMClient` : instrumentation à brancher au niveau service."""
    return ObservedLLMClient(
        inner=inner,
        session=session,
        phase=phase,
        agent_name=agent_name,
        operation_type=operation_type,
        model=model,
        mission_id=mission_id,
        price_in_per_mtok=price_in_per_mtok,
        price_out_per_mtok=price_out_per_mtok,
    )


def log_product_event(
    session: Session,
    event_type: str,
    phase: str,
    entity_type: str,
    entity_id: int,
    status: str = "",
    message: str = "",
    metadata: dict[str, Any] | None = None,
) -> ProductEventLog:
    """Journalise un événement produit important et le persiste (commit immédiat)."""
    event = ProductEventLog(
        event_type=event_type,
        phase=phase,
        entity_type=entity_type,
        entity_id=entity_id,
        status=status,
        message=message,
        metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


# --- Lectures (aucune écriture) --------------------------------------------
def list_llm_calls(
    session: Session,
    limit: int = 50,
    status: str | None = None,
    phase: str | None = None,
    agent_name: str | None = None,
    operation_type: str | None = None,
) -> list[LLMCallLog]:
    """Liste les derniers appels LLM, filtres optionnels, du plus récent au plus ancien."""
    stmt = select(LLMCallLog).order_by(LLMCallLog.id.desc())
    if status is not None:
        stmt = stmt.where(LLMCallLog.status == status)
    if phase is not None:
        stmt = stmt.where(LLMCallLog.phase == phase)
    if agent_name is not None:
        stmt = stmt.where(LLMCallLog.agent_name == agent_name)
    if operation_type is not None:
        stmt = stmt.where(LLMCallLog.operation_type == operation_type)
    return list(session.execute(stmt.limit(limit)).scalars().all())


def list_events(
    session: Session,
    limit: int = 50,
    phase: str | None = None,
    entity_type: str | None = None,
    event_type: str | None = None,
) -> list[ProductEventLog]:
    """Liste les derniers événements produit, filtres optionnels, du plus récent au plus ancien."""
    stmt = select(ProductEventLog).order_by(ProductEventLog.id.desc())
    if phase is not None:
        stmt = stmt.where(ProductEventLog.phase == phase)
    if entity_type is not None:
        stmt = stmt.where(ProductEventLog.entity_type == entity_type)
    if event_type is not None:
        stmt = stmt.where(ProductEventLog.event_type == event_type)
    return list(session.execute(stmt.limit(limit)).scalars().all())


def observability_summary(session: Session) -> dict[str, Any]:
    """Retourne un résumé simple (compteurs, durée moyenne, répartitions, dernière erreur)."""
    total = session.execute(select(func.count()).select_from(LLMCallLog)).scalar_one()
    ok = session.execute(
        select(func.count()).select_from(LLMCallLog).where(LLMCallLog.status == "success")
    ).scalar_one()
    failed = session.execute(
        select(func.count()).select_from(LLMCallLog).where(LLMCallLog.status == "error")
    ).scalar_one()
    avg_duration = session.execute(select(func.avg(LLMCallLog.duration_ms))).scalar_one()
    total_events = session.execute(select(func.count()).select_from(ProductEventLog)).scalar_one()

    events_by_phase = {
        str(phase): int(count)
        for phase, count in session.execute(
            select(ProductEventLog.phase, func.count()).group_by(ProductEventLog.phase)
        ).all()
    }
    llm_calls_by_phase = {
        str(phase): int(count)
        for phase, count in session.execute(
            select(LLMCallLog.phase, func.count()).group_by(LLMCallLog.phase)
        ).all()
    }
    latest_error = session.execute(
        select(LLMCallLog.error)
        .where(LLMCallLog.status == "error")
        .order_by(LLMCallLog.id.desc())
        .limit(1)
    ).scalar_one_or_none()

    return {
        "total_llm_calls": int(total),
        "successful_llm_calls": int(ok),
        "failed_llm_calls": int(failed),
        "average_duration_ms": round(float(avg_duration), 2) if avg_duration is not None else 0.0,
        "total_events": int(total_events),
        "events_by_phase": events_by_phase,
        "llm_calls_by_phase": llm_calls_by_phase,
        "latest_error": latest_error,
    }
