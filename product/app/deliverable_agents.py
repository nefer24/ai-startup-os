"""Production **encadrée** d'un livrable par une entreprise IA approuvée (Phase 5).

Responsabilité : **produire** un premier livrable concret, limité, traçable et validable par
le CEO — sans autonomie complète, sans exécuter tout le contrat de livraison, sans déploiement.

Processus simple et contrôlé, **quatre vrais appels LLM** (mockés en test) — surtout PAS un appel
par expert : la structure des cellules déjà composée est utilisée telle quelle, en synthèse.

  1. Deliverable Planner        — comprend la demande, choisit la structure du livrable ;
  2. Expert Cell Synthesizer    — synthèse encadrée des départements/spécialités/cellules ;
  3. Deliverable Producer       — produit le contenu concret du livrable ;
  4. Quality & Governance Reviewer — clarté, limites, risques, conformité, points à valider CEO.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agent_utils import parse_json_fields
from app.llm import LLMClient

DELIVERABLE_PLANNER_ROLE = (
    "Tu es le Deliverable Planner AI-SOS. Tu comprends la demande de livrable du CEO, le contrat "
    "de livraison de l'entreprise IA et les contraintes, puis tu choisis une structure claire et "
    "limitée pour le livrable (pas de production complète, pas de déploiement)."
)

EXPERT_CELL_SYNTHESIZER_ROLE = (
    "Tu es l'Expert Cell Synthesizer AI-SOS. À partir de la structure déjà composée de "
    "l'entreprise IA (départements, spécialités, cellules d'experts), tu produis une SYNTHÈSE "
    "encadrée des apports pertinents. Tu ne simules pas chaque expert individuellement : tu "
    "synthétises les angles et objections utiles au livrable demandé."
)

DELIVERABLE_PRODUCER_ROLE = (
    "Tu es le Deliverable Producer AI-SOS. À partir de la structure et de la synthèse, tu produis "
    "le contenu concret du livrable demandé, en respectant strictement le périmètre limité et les "
    "contraintes. Tu ne déploies rien et ne produis pas de gros code applicatif."
)

QUALITY_GOVERNANCE_ROLE = (
    "Tu es le Quality & Governance Reviewer AI-SOS. Tu vérifies la clarté, les limites, les "
    "risques, la conformité au périmètre et l'absence d'exécution non autorisée, et tu listes "
    "les points que le CEO doit valider. Le livrable reste candidat jusqu'à validation CEO."
)


@dataclass(frozen=True)
class DeliverableInput:
    """Contexte de production : l'entreprise IA approuvée et la demande de livrable."""

    company_name: str
    company_summary: str
    deliverable_type: str
    title: str
    instructions: str
    constraints: str


@dataclass(frozen=True)
class DeliverablePlan:
    """Sortie du Deliverable Planner."""

    structure: str
    production_notes: str
    raw: str


@dataclass(frozen=True)
class QualityReview:
    """Sortie du Quality & Governance Reviewer."""

    quality_review: str
    risks: str
    ceo_validation_notes: str
    raw: str


def _format_input(data: DeliverableInput) -> str:
    """Bloc texte décrivant l'entreprise IA et la demande, réutilisé par tous les prompts."""
    return (
        f"{data.company_summary}\n\n"
        f"Type de livrable demandé : {data.deliverable_type}\n"
        f"Titre : {data.title}\n"
        f"Instructions : {data.instructions}\n"
        f"Contraintes : {data.constraints}"
    )


class DeliverablePlanner:
    """Agent 1 — comprend la demande et choisit la structure du livrable."""

    name = "Deliverable Planner"
    role = DELIVERABLE_PLANNER_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: DeliverableInput) -> DeliverablePlan:
        """Retourne la structure du livrable et les notes de production."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            "Réponds STRICTEMENT en JSON, sans texte autour, avec exactement ces clés "
            '(valeurs = chaînes) : {"structure": "...", "production_notes": "..."}.'
        )
        raw = self._llm.complete(prompt)
        fields = parse_json_fields(raw, ["structure", "production_notes"])
        if fields is None:
            return DeliverablePlan(structure=raw.strip(), production_notes="", raw=raw)
        return DeliverablePlan(
            structure=fields["structure"],
            production_notes=fields["production_notes"],
            raw=raw,
        )


class ExpertCellSynthesizer:
    """Agent 2 — synthèse encadrée des cellules d'experts (pas un appel par expert)."""

    name = "Expert Cell Synthesizer"
    role = EXPERT_CELL_SYNTHESIZER_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: DeliverableInput, structure: str) -> str:
        """Retourne une synthèse encadrée des apports des cellules, en texte clair."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Structure retenue :\n{structure}\n\n"
            "Produis une synthèse des angles, contributions et objections utiles au livrable."
        )
        return self._llm.complete(prompt)


class DeliverableProducer:
    """Agent 3 — produit le contenu concret du livrable."""

    name = "Deliverable Producer"
    role = DELIVERABLE_PRODUCER_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: DeliverableInput, structure: str, synthesis: str) -> str:
        """Retourne le contenu concret du livrable, en texte clair."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Structure :\n{structure}\n\n"
            f"Synthèse des cellules :\n{synthesis}\n\n"
            "Produis le contenu concret du livrable, limité au périmètre et aux contraintes."
        )
        return self._llm.complete(prompt)


class QualityGovernanceReviewer:
    """Agent 4 — clarté, limites, risques, conformité, points à valider par le CEO."""

    name = "Quality & Governance Reviewer"
    role = QUALITY_GOVERNANCE_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: DeliverableInput, content: str) -> QualityReview:
        """Retourne la revue qualité, les risques et les notes de validation CEO."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Contenu produit :\n{content}\n\n"
            "Réponds STRICTEMENT en JSON, sans texte autour, avec exactement ces clés "
            '(valeurs = chaînes) : {"quality_review": "...", "risks": "...", '
            '"ceo_validation_notes": "..."}.'
        )
        raw = self._llm.complete(prompt)
        fields = parse_json_fields(raw, ["quality_review", "risks", "ceo_validation_notes"])
        if fields is None:
            return QualityReview(
                quality_review=raw.strip(), risks="", ceo_validation_notes="", raw=raw
            )
        return QualityReview(
            quality_review=fields["quality_review"],
            risks=fields["risks"],
            ceo_validation_notes=fields["ceo_validation_notes"],
            raw=raw,
        )
