"""Barriere d'activation d'un fournisseur LLM reel (gouvernance CEO-only).

Tracabilite : docs/implementation/08-security-and-permissions.md (actions CEO-only),
docs/adr/ADR-0010-determinisme-interactions-llm.md, docs/components/08-audit-engine.md.

Empeche toute activation d'un fournisseur LLM reel sans autorisation EXPLICITE du CEO. Refus par
defaut ; activation uniquement si l'acteur est le CEO ET la configuration est active/valide.
AUCUNE activation automatique. La garde AUTORISE une configuration — elle ne branche AUCUN
backend, n'effectue AUCUN appel reseau et ne detient AUCUN secret. Le provider reel reste non
cable : une decision d'activation est une preuve gouvernee, pas un branchement runtime.

Sur autorisation, un evenement d'audit CEO-only (`bounds.updated`) est PRODUIT si un moteur
d'audit est fourni (sinon la decision porte l'evenement PROPOSE) — sans jamais consigner de secret.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable

from aisos.audit.interfaces import AuditEngine
from aisos.events import EventEnvelope, EventType
from aisos.infrastructure.llm.config import ProviderName, RealLLMProviderConfig
from aisos.schemas.base import ImmutableModel
from aisos.security.interfaces import Authorizer, Principal


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


class RealLLMActivationRequest(ImmutableModel):
    """Demande d'activation d'un fournisseur LLM reel (soumise a la garde de gouvernance)."""

    principal: Principal
    config: RealLLMProviderConfig
    justification: str = ""


class RealLLMActivationDecision(ImmutableModel):
    """Resultat de la garde : autorisation ou refus. Ne branche jamais de backend.

    `activated_config` n'est renseignee que si `granted` — c'est la configuration AUTORISEE, a
    utiliser par un composant racine sur action explicite du CEO ; rien n'est cable ici.
    """

    granted: bool
    reason: str
    activated_config: RealLLMProviderConfig | None = None
    audit_id: str | None = None
    audit_event_type: str | None = None


class RealLLMActivationGuard:
    """Garde de gouvernance : seul le CEO active un fournisseur LLM reel. Refus par defaut.

    Aucune activation automatique, aucun appel reseau, aucun secret. Sur autorisation, produit un
    evenement d'audit CEO-only si un moteur d'audit est fourni.
    """

    def __init__(
        self,
        authorizer: Authorizer,
        *,
        audit_engine: AuditEngine | None = None,
        clock: Callable[[], dt.datetime] = _utc_now,
    ) -> None:
        self._authz = authorizer
        self._audit = audit_engine
        self._clock = clock

    async def evaluate(self, request: RealLLMActivationRequest) -> RealLLMActivationDecision:
        """Autorise ou refuse une demande d'activation. Refus par defaut ; jamais automatique."""
        # (1) Seul le CEO peut activer un fournisseur reel (invariant de gouvernance).
        if not self._authz.is_ceo(request.principal):
            return RealLLMActivationDecision(
                granted=False,
                reason=(
                    f"refus : principal '{request.principal.role}' n'est pas le CEO "
                    "(activation d'un LLM reel reservee au CEO)"
                ),
            )

        # (2) La configuration doit etre ACTIVE et complete (provider/model/version).
        config = request.config
        if not config.is_active or config.provider == ProviderName.NONE:
            return RealLLMActivationDecision(
                granted=False,
                reason="refus : configuration inactive ou invalide (aucune activation)",
            )

        # (3) Autorisation. Aucune activation automatique n'a eu lieu : c'est une decision CEO.
        # Le provider reste NON cable ; on renvoie la configuration autorisee, sans brancher rien.
        audit_id: str | None = None
        event_type: str | None = None
        if self._audit is not None:
            record = await self._audit.append(self._audit_envelope(request))
            audit_id = record.id
            event_type = str(EventType.BOUNDS_UPDATED)

        return RealLLMActivationDecision(
            granted=True,
            reason="autorise par le CEO (configuration valide) — provider non cable",
            activated_config=config,
            audit_id=audit_id,
            audit_event_type=event_type,
        )

    def _audit_envelope(self, request: RealLLMActivationRequest) -> EventEnvelope:
        """Enveloppe d'audit CEO-only de l'activation. NE consigne AUCUN secret (nom d'env seul)."""
        config = request.config
        return EventEnvelope(
            event_id=f"evt-llm-activation-{config.provider}-{config.model}",
            type=str(EventType.BOUNDS_UPDATED),
            occurred_at=self._clock(),
            actor=f"ceo:{request.principal.subject}",
            payload={
                "action": "real_llm_provider_activation",
                "provider": str(config.provider),
                "model": config.model,
                "model_version": config.model_version,
                "timeout_ms": config.timeout_ms,
                "api_key_env": config.api_key_env,  # NOM de variable, jamais la cle
            },
        )
