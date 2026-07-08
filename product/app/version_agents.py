"""Itération **contrôlée** sur un livrable existant (Phase 6).

Responsabilité : **itérer** — à partir d'un livrable existant et d'une demande de révision guidée
du CEO, produire une **nouvelle version candidate**, comparer à la version précédente et rester
traçable et validable. **Aucun déploiement, aucune livraison externe, aucune modification du
repo, aucun écrasement du livrable original** : chaque révision crée une nouvelle version.

Quatre vrais appels LLM (mockés en test) :
  1. Revision Analyst    — comprend le livrable, les instructions, contraintes et focus areas ;
  2. Version Producer    — produit la nouvelle version candidate ;
  3. Version Comparator  — compare version précédente et nouvelle (améliorations, compromis) ;
  4. Quality & Governance Reviewer — périmètre, clarté, risques, points à valider par le CEO.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agent_utils import parse_json_fields
from app.llm import LLMClient

REVISION_ANALYST_ROLE = (
    "Tu es le Revision Analyst AI-SOS. Tu comprends le livrable existant, les instructions de "
    "révision du CEO, les contraintes et les focus areas, puis tu établis un plan de révision "
    "clair et limité (pas de code complet, pas de déploiement)."
)

VERSION_PRODUCER_ROLE = (
    "Tu es le Version Producer AI-SOS. À partir du livrable existant et du plan de révision, tu "
    "produis une NOUVELLE version candidate du livrable, en respectant le périmètre limité et les "
    "contraintes. Tu n'écrases jamais l'original : tu proposes une version distincte."
)

VERSION_COMPARATOR_ROLE = (
    "Tu es le Version Comparator AI-SOS. Tu compares la version précédente et la nouvelle "
    "version : améliorations, compromis, risques et différences notables."
)

VERSION_QUALITY_ROLE = (
    "Tu es le Quality & Governance Reviewer AI-SOS (itération). Tu vérifies que la nouvelle "
    "version reste dans le périmètre, ne déclenche aucune action externe, est claire, validable "
    "et traçable, et tu listes les points que le CEO doit valider."
)


@dataclass(frozen=True)
class VersionInput:
    """Contexte d'itération : le livrable, la version précédente et la demande de révision."""

    deliverable_title: str
    deliverable_type: str
    previous_content: str
    revision_instructions: str
    constraints: str
    focus_areas: str


@dataclass(frozen=True)
class VersionComparison:
    """Sortie du Version Comparator."""

    change_summary: str
    comparison_to_previous: str
    raw: str


@dataclass(frozen=True)
class VersionQualityReview:
    """Sortie du Quality & Governance Reviewer (itération)."""

    quality_review: str
    risks: str
    ceo_validation_notes: str
    raw: str


def _format_input(data: VersionInput) -> str:
    """Bloc texte décrivant le livrable et la demande, réutilisé par tous les prompts."""
    return (
        f"Titre du livrable : {data.deliverable_title}\n"
        f"Type : {data.deliverable_type}\n"
        f"Version précédente (contenu) :\n{data.previous_content}\n\n"
        f"Instructions de révision : {data.revision_instructions}\n"
        f"Contraintes : {data.constraints}\n"
        f"Focus areas : {data.focus_areas}"
    )


class RevisionAnalyst:
    """Agent 1 — comprend le livrable et établit un plan de révision."""

    name = "Revision Analyst"
    role = REVISION_ANALYST_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: VersionInput) -> str:
        """Retourne un plan de révision clair et limité, en texte clair."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            "Établis un plan de révision : quoi changer, quoi garder, dans quel périmètre."
        )
        return self._llm.complete(prompt)


class VersionProducer:
    """Agent 2 — produit la nouvelle version candidate du livrable."""

    name = "Version Producer"
    role = VERSION_PRODUCER_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: VersionInput, revision_plan: str) -> str:
        """Retourne le contenu de la nouvelle version, en texte clair."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Plan de révision :\n{revision_plan}\n\n"
            "Produis la nouvelle version du livrable, limitée au périmètre et aux contraintes."
        )
        return self._llm.complete(prompt)


class VersionComparator:
    """Agent 3 — compare la version précédente et la nouvelle version."""

    name = "Version Comparator"
    role = VERSION_COMPARATOR_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: VersionInput, new_content: str) -> VersionComparison:
        """Retourne le résumé des changements et la comparaison à la version précédente."""
        prompt = (
            f"{self.role}\n\n"
            f"Version précédente :\n{data.previous_content}\n\n"
            f"Nouvelle version :\n{new_content}\n\n"
            "Réponds STRICTEMENT en JSON, sans texte autour, avec exactement ces clés "
            '(valeurs = chaînes) : {"change_summary": "...", "comparison_to_previous": "..."}.'
        )
        raw = self._llm.complete(prompt)
        fields = parse_json_fields(raw, ["change_summary", "comparison_to_previous"])
        if fields is None:
            return VersionComparison(change_summary=raw.strip(), comparison_to_previous="", raw=raw)
        return VersionComparison(
            change_summary=fields["change_summary"],
            comparison_to_previous=fields["comparison_to_previous"],
            raw=raw,
        )


class VersionQualityReviewer:
    """Agent 4 — périmètre, clarté, risques, points à valider par le CEO."""

    name = "Quality & Governance Reviewer (itération)"
    role = VERSION_QUALITY_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: VersionInput, new_content: str) -> VersionQualityReview:
        """Retourne la revue qualité, les risques et les notes de validation CEO."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Nouvelle version :\n{new_content}\n\n"
            "Réponds STRICTEMENT en JSON, sans texte autour, avec exactement ces clés "
            '(valeurs = chaînes) : {"quality_review": "...", "risks": "...", '
            '"ceo_validation_notes": "..."}.'
        )
        raw = self._llm.complete(prompt)
        fields = parse_json_fields(raw, ["quality_review", "risks", "ceo_validation_notes"])
        if fields is None:
            return VersionQualityReview(
                quality_review=raw.strip(), risks="", ceo_validation_notes="", raw=raw
            )
        return VersionQualityReview(
            quality_review=fields["quality_review"],
            risks=fields["risks"],
            ceo_validation_notes=fields["ceo_validation_notes"],
            raw=raw,
        )
