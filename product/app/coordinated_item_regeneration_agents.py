"""Régénération **guidée** d'un item coordonné marqué `revision_requested` (Phase 12).

Responsabilité : **régénérer** — produire une nouvelle version candidate d'UN item en révision, à
partir de son contenu original et des instructions/décisions CEO, sans toucher au lot ni aux autres
items. AI-SOS **ne remplace pas** l'item original ; la régénération est un candidat séparé.

Processus simple et contrôlé, **quatre vrais appels LLM** (mockés en test) :

  1. Item Revision Context Analyst  — lit l'item, son statut, ses décisions, la provenance ;
  2. Item Regeneration Planner      — plan de régénération limité à cet item ;
  3. Item Regeneration Producer     — produit le nouveau contenu candidat de l'item ;
  4. Item Regeneration Quality Reviewer — cohérence, prise en compte CEO, garde-fous.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agent_utils import parse_json_fields
from app.llm import LLMClient

ITEM_REVISION_CONTEXT_ANALYST_ROLE = (
    "Tu es l'Item Revision Context Analyst AI-SOS. Tu lis un livrable (item) d'un lot coordonné "
    "marqué `revision_requested`, son contenu original, ses décisions CEO précédentes et la "
    "provenance du lot. Tu identifies précisément ce qui doit être corrigé, sans élargir le "
    "périmètre ni toucher aux autres items."
)

ITEM_REGENERATION_PLANNER_ROLE = (
    "Tu es l'Item Regeneration Planner AI-SOS. À partir du contexte de révision et des consignes "
    "CEO, tu prépares un plan de régénération LIMITÉ à cet item : ce qui change, ce qui reste, et "
    "comment rester cohérent avec le lot sans modifier les autres items."
)

ITEM_REGENERATION_PRODUCER_ROLE = (
    "Tu es l'Item Regeneration Producer AI-SOS. À partir du plan, tu produis le NOUVEAU contenu "
    "candidat de l'item, cohérent avec le lot, les contraintes et les instructions CEO. Tu ne "
    "déploies rien et ne produis pas de gros code applicatif."
)

ITEM_REGENERATION_QUALITY_ROLE = (
    "Tu es l'Item Regeneration Quality Reviewer AI-SOS. Tu vérifies la cohérence avec le contenu "
    "original, la prise en compte des demandes CEO, le respect des contraintes, l'absence de "
    "déploiement et de modification du repo, et le caractère candidat. Tu listes les points à "
    "valider par le CEO."
)


@dataclass(frozen=True)
class RegenerationInput:
    """Contexte de régénération : l'item source en révision et la demande CEO."""

    item_type: str
    item_title: str
    original_content: str
    dependencies: str
    consistency_notes: str
    validation_notes: str
    prior_decisions_summary: str
    revision_instructions: str
    constraints: str
    acceptance_focus: str


@dataclass(frozen=True)
class RegenerationPlan:
    """Sortie de l'Item Regeneration Planner."""

    regeneration_plan: str
    provenance_notes: str
    raw: str


@dataclass(frozen=True)
class QualityReview:
    """Sortie de l'Item Regeneration Quality Reviewer."""

    quality_review: str
    risks: str
    ceo_validation_notes: str
    raw: str


def _format_input(data: RegenerationInput) -> str:
    """Bloc texte décrivant l'item en révision et la demande (partagé par les prompts)."""
    return (
        f"Item : {data.item_type} — {data.item_title}\n"
        f"Contenu original (à réviser) :\n{data.original_content}\n\n"
        f"Dépendances : {data.dependencies}\n"
        f"Notes de cohérence : {data.consistency_notes}\n"
        f"Notes de validation : {data.validation_notes}\n"
        f"Décisions CEO précédentes :\n{data.prior_decisions_summary}\n\n"
        f"Instructions de révision (CEO) : {data.revision_instructions}\n"
        f"Contraintes : {data.constraints}\n"
        f"Critères d'acceptation à privilégier : {data.acceptance_focus}"
    )


class ItemRevisionContextAnalyst:
    """Agent 1 — lit l'item en révision, ses décisions et la provenance."""

    name = "Item Revision Context Analyst"
    role = ITEM_REVISION_CONTEXT_ANALYST_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: RegenerationInput) -> str:
        """Retourne l'analyse de ce qui doit être corrigé, en texte clair."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            "Identifie ce qui doit être corrigé dans cet item, en tenant compte des décisions CEO "
            "précédentes, sans élargir le périmètre ni toucher aux autres items."
        )
        return self._llm.complete(prompt)


class ItemRegenerationPlanner:
    """Agent 2 — plan de régénération limité à cet item."""

    name = "Item Regeneration Planner"
    role = ITEM_REGENERATION_PLANNER_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: RegenerationInput, analysis: str) -> RegenerationPlan:
        """Retourne le plan de régénération et les notes de provenance."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Analyse de révision :\n{analysis}\n\n"
            "Réponds STRICTEMENT en JSON, sans texte autour, avec exactement ces clés "
            '(valeurs = chaînes) : {"regeneration_plan": "...", "provenance_notes": "..."}. '
            "`provenance_notes` rappelle que la régénération porte sur un item en révision et ne "
            "remplace pas l'item original ni ne modifie le lot."
        )
        raw = self._llm.complete(prompt)
        fields = parse_json_fields(raw, ["regeneration_plan", "provenance_notes"])
        if fields is None:
            return RegenerationPlan(regeneration_plan=raw.strip(), provenance_notes="", raw=raw)
        return RegenerationPlan(
            regeneration_plan=fields["regeneration_plan"],
            provenance_notes=fields["provenance_notes"],
            raw=raw,
        )


class ItemRegenerationProducer:
    """Agent 3 — produit le nouveau contenu candidat de l'item."""

    name = "Item Regeneration Producer"
    role = ITEM_REGENERATION_PRODUCER_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: RegenerationInput, regeneration_plan: str) -> str:
        """Retourne le nouveau contenu candidat de l'item, en texte clair."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Plan de régénération :\n{regeneration_plan}\n\n"
            "Produis le nouveau contenu candidat de l'item, limité au périmètre et contraintes, "
            "en tenant compte des instructions CEO."
        )
        return self._llm.complete(prompt)


class ItemRegenerationQualityReviewer:
    """Agent 4 — cohérence, prise en compte CEO, garde-fous, points à valider."""

    name = "Item Regeneration Quality Reviewer"
    role = ITEM_REGENERATION_QUALITY_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: RegenerationInput, regenerated_content: str) -> QualityReview:
        """Retourne la revue qualité, les risques et les notes de validation CEO."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Contenu régénéré :\n{regenerated_content}\n\n"
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
