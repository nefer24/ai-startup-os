"""Politique minimale de readiness LLM, déterministe (C0.8 — LLM Production Readiness réaligné).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.8),
docs/llm/C0-8-llm-production-readiness.md, docs/implementation/08-security-and-permissions.md.

`LLMReadinessPolicy` **evalue** une seule question : *une demande LLM est-elle autorisee dans le
cadre controle de C0.8 ?* Elle repond `ALLOWED` / `DENIED` — une **autorisation technique de
preparation**, **jamais** une decision metier ni une decision CEO. Elle refuse les modes interdits,
un prompt vide, une notice de securite vide, et tout prompt contenant explicitement un **verbe
d'action interdit** (approve / apply / decide / trigger_e7 / open_e9 / create_solution / create_team
/ mutate / delete / rewrite_audit). Les raisons de refus sont **deterministes**.

Frontieres : la politique **pure et deterministe** (aucun effet de bord) ne repond a **aucune**
question metier, ne devient **jamais** une decision CEO, n'appelle aucun LLM, n'ecrit ni audit ni
memoire, ne declenche aucun E7 et n'ouvre pas E9. Elle n'importe ni `access`, ni `ceo_decision`, ni
`operational_audit`, ni `operational_memory`, ni `evolution`, ni `agents`, ni `orchestrator`, ni
`councils` ; les references restent declaratives. C0.8 ne rouvre aucun contrat E1..E8.
"""

from __future__ import annotations

from enum import StrEnum

from aisos.llm_readiness.contracts import (
    LLMReadinessMode,
    LLMReadinessRequest,
)
from aisos.schemas.base import ImmutableModel

# Modes **surs** de preparation : aucun n'appelle un provider reel. `DISABLED` est refuse (LLM
# eteint).
_ALLOWED_MODES: frozenset[LLMReadinessMode] = frozenset(
    {
        LLMReadinessMode.REPLAY_ONLY,
        LLMReadinessMode.DETERMINISTIC_TEST,
        LLMReadinessMode.PROVIDER_READY_DECLARATIVE,
    }
)

# Verbes d'action **interdits** dans un prompt : le LLM n'agit jamais, il assiste. Ordre
# deterministe.
_FORBIDDEN_PROMPT_TOKENS: tuple[str, ...] = (
    "approve",
    "apply",
    "decide",
    "trigger_e7",
    "open_e9",
    "create_solution",
    "create_team",
    "mutate",
    "delete",
    "rewrite_audit",
)


class LLMReadinessPolicyDecisionStatus(StrEnum):
    """Statut **declaratif** d'une decision de politique de readiness. Jamais une decision metier.

    `ALLOWED` = « preparation LLM techniquement autorisee dans le cadre C0.8 » et **rien d'autre** :
    aucune decision CEO, aucune application, aucun appel reel, aucun declenchement E7, aucune
    ouverture E9. `DENIED` refuse la preparation.
    """

    ALLOWED = "allowed"
    DENIED = "denied"


class LLMReadinessPolicyDecision(ImmutableModel):
    """Decision **technique de preparation** immuable. Jamais une decision metier / CEO.

    Champs : ``request_id`` (non vide), ``mode`` (`LLMReadinessMode` demande), ``status``
    (`ALLOWED` / `DENIED`), ``reasons`` (tuple **deterministe** de motifs ; vide si `ALLOWED` sans
    remarque), ``evaluated_by_policy`` (nom de la politique, non vide). Constat technique : ne cree,
    n'applique, ne mute, ne declenche et n'ouvre rien ; jamais confondue avec une decision CEO.
    """

    request_id: str
    mode: LLMReadinessMode
    status: LLMReadinessPolicyDecisionStatus
    reasons: tuple[str, ...] = ()
    evaluated_by_policy: str


class LLMReadinessPolicy:
    """Politique **deterministe** de readiness LLM. Autorise une preparation, ne decide rien de
    metier.

    `evaluate` inspecte une `LLMReadinessRequest` et retourne une `LLMReadinessPolicyDecision`
    **sans effet de bord**. Elle refuse (`DENIED`) : un mode hors des modes surs (dont `DISABLED`),
    un prompt vide, une notice de securite vide, ou un prompt contenant un verbe d'action interdit.
    Elle autorise (`ALLOWED`) sinon. `ALLOWED` reste une autorisation **technique de preparation** :
    il ne cree aucune decision CEO, n'appelle aucun LLM, n'applique rien, ne declenche aucun E7 et
    n'ouvre pas E9.
    """

    name = "llm-readiness-policy"

    def evaluate(self, request: LLMReadinessRequest) -> LLMReadinessPolicyDecision:
        """Evalue une demande LLM. Constat deterministe, sans effet de bord ni pouvoir metier."""
        reasons = self._reasons_to_deny(request)
        status = (
            LLMReadinessPolicyDecisionStatus.DENIED
            if reasons
            else LLMReadinessPolicyDecisionStatus.ALLOWED
        )
        return LLMReadinessPolicyDecision(
            request_id=request.id,
            mode=request.mode,
            status=status,
            reasons=tuple(reasons),
            evaluated_by_policy=self.name,
        )

    def _reasons_to_deny(self, request: LLMReadinessRequest) -> list[str]:
        """Collecte, dans un ordre **deterministe**, les motifs de refus. Vide => autorise."""
        reasons: list[str] = []
        if request.mode not in _ALLOWED_MODES:
            reasons.append(f"mode non autorise en preparation controlee : {request.mode.value}")
        if not request.prompt.strip():
            reasons.append("prompt vide : une demande d'assistance doit etre explicite")
        if not request.safety_notice.strip():
            reasons.append("safety_notice vide : le cadre de securite doit etre explicite")
        lowered_prompt = request.prompt.lower()
        for token in _FORBIDDEN_PROMPT_TOKENS:
            if token in lowered_prompt:
                reasons.append(f"verbe d'action interdit dans le prompt : {token}")
        return reasons
