"""Équipe IA spécialisée en **amélioration d'une solution existante** (Phase 3).

Phrase fondatrice : « Lorsqu'une solution existe déjà, AI-SOS l'analyse, identifie ses
faiblesses, propose des améliorations et la fait évoluer afin de la rendre plus performante,
plus différenciante et plus unique. »

Quatre rôles, quatre vrais appels LLM (mockés en test) :
  1. Analyste de solution existante — comprend la solution, ses forces, son contexte ;
  2. Critique / Weakness Reviewer   — identifie faiblesses et angles morts ;
  3. Improvement Architect          — propose des améliorations et une version candidate ;
  4. Differentiation Reviewer       — performance, différenciation, unicité.

Pas de framework multi-agent : chaque agent est une classe simple qui délègue au
`LLMClient` injecté.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agent_utils import parse_json_fields
from app.llm import LLMClient

EXISTING_ANALYST_ROLE = (
    "Tu es l'Analyste de solution existante AI-SOS. Tu comprends la solution existante, "
    "sa proposition de valeur, ses utilisateurs, son fonctionnement, ses forces, son "
    "contexte et ses limites visibles. Tu ne proposes pas encore d'amélioration."
)

WEAKNESS_ROLE = (
    "Tu es le Critique (Weakness Reviewer) AI-SOS. Tu identifies les faiblesses, angles "
    "morts, risques, manque de différenciation, limites UX, limites business, limites "
    "techniques ou produit de la solution existante."
)

IMPROVEMENT_ARCHITECT_ROLE = (
    "Tu es l'Improvement Architect AI-SOS. À partir de l'analyse et des faiblesses, tu "
    "proposes des améliorations concrètes, différenciantes, actionnables et priorisées, "
    "puis une version améliorée candidate de la solution. Elle reste candidate et doit "
    "être validée par le CEO."
)

DIFFERENTIATION_ROLE = (
    "Tu es le Differentiation Reviewer AI-SOS. Tu expliques comment rendre la solution "
    "plus performante, plus différenciante et plus unique, et tu précises les risques, "
    "hypothèses et expertises nécessaires."
)


@dataclass(frozen=True)
class ImprovementInput:
    """Entrée CEO : une solution existante à faire évoluer."""

    title: str
    description: str
    context: str
    improvement_goals: str
    constraints: str
    notes: str


@dataclass(frozen=True)
class ExistingSolutionAnalysis:
    """Sortie de l'Analyste de solution existante."""

    analysis: str
    strengths: str
    raw: str


@dataclass(frozen=True)
class ImprovementProposal:
    """Sortie de l'Improvement Architect."""

    proposed_improvements: str
    improved_solution_candidate: str
    raw: str


@dataclass(frozen=True)
class DifferentiationReview:
    """Sortie du Differentiation Reviewer."""

    differentiation: str
    risks: str
    expertise_needs: str
    raw: str


def _format_input(data: ImprovementInput) -> str:
    """Bloc texte décrivant la solution existante, réutilisé par tous les prompts."""
    return (
        f"Titre : {data.title}\n"
        f"Description : {data.description}\n"
        f"Contexte / marché / utilisateurs : {data.context}\n"
        f"Objectifs d'amélioration : {data.improvement_goals}\n"
        f"Contraintes : {data.constraints}\n"
        f"Notes : {data.notes}"
    )


class ExistingSolutionAnalyst:
    """Agent 1 — comprend la solution existante et ses forces."""

    name = "Analyste de solution existante"
    role = EXISTING_ANALYST_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: ImprovementInput) -> ExistingSolutionAnalysis:
        """Retourne l'analyse de la solution existante et ses forces identifiées."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            "Réponds STRICTEMENT en JSON, sans texte autour, avec exactement ces clés "
            '(valeurs = chaînes de texte) : {"analysis": "...", "strengths": "..."}.'
        )
        raw = self._llm.complete(prompt)
        fields = parse_json_fields(raw, ["analysis", "strengths"])
        if fields is None:
            return ExistingSolutionAnalysis(analysis=raw.strip(), strengths="", raw=raw)
        return ExistingSolutionAnalysis(
            analysis=fields["analysis"], strengths=fields["strengths"], raw=raw
        )


class WeaknessReviewer:
    """Agent 2 — identifie les faiblesses et angles morts."""

    name = "Critique (Weakness Reviewer)"
    role = WEAKNESS_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: ImprovementInput, analysis: str) -> str:
        """Retourne les faiblesses identifiées, en texte clair."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Analyse de la solution existante :\n{analysis}\n\n"
            "Liste les faiblesses, angles morts, risques et limites (UX, business, "
            "technique, différenciation)."
        )
        return self._llm.complete(prompt)


class ImprovementArchitect:
    """Agent 3 — propose des améliorations et une version candidate."""

    name = "Improvement Architect"
    role = IMPROVEMENT_ARCHITECT_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: ImprovementInput, analysis: str, weaknesses: str) -> ImprovementProposal:
        """Retourne les améliorations proposées et la version améliorée candidate."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Analyse :\n{analysis}\n\n"
            f"Faiblesses identifiées :\n{weaknesses}\n\n"
            "Réponds STRICTEMENT en JSON, sans texte autour, avec exactement ces clés "
            '(valeurs = chaînes de texte) : {"proposed_improvements": "...", '
            '"improved_solution_candidate": "..."}.'
        )
        raw = self._llm.complete(prompt)
        fields = parse_json_fields(raw, ["proposed_improvements", "improved_solution_candidate"])
        if fields is None:
            return ImprovementProposal(
                proposed_improvements=raw.strip(), improved_solution_candidate="", raw=raw
            )
        return ImprovementProposal(
            proposed_improvements=fields["proposed_improvements"],
            improved_solution_candidate=fields["improved_solution_candidate"],
            raw=raw,
        )


class DifferentiationReviewer:
    """Agent 4 — performance, différenciation, unicité, risques, expertises."""

    name = "Differentiation Reviewer"
    role = DIFFERENTIATION_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(
        self, data: ImprovementInput, improved_solution_candidate: str
    ) -> DifferentiationReview:
        """Retourne la différenciation, les risques/hypothèses et les expertises nécessaires."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Version améliorée candidate :\n{improved_solution_candidate}\n\n"
            "Réponds STRICTEMENT en JSON, sans texte autour, avec exactement ces clés "
            '(valeurs = chaînes de texte) : {"differentiation": "...", "risks": "...", '
            '"expertise_needs": "..."}.'
        )
        raw = self._llm.complete(prompt)
        fields = parse_json_fields(raw, ["differentiation", "risks", "expertise_needs"])
        if fields is None:
            return DifferentiationReview(
                differentiation=raw.strip(), risks="", expertise_needs="", raw=raw
            )
        return DifferentiationReview(
            differentiation=fields["differentiation"],
            risks=fields["risks"],
            expertise_needs=fields["expertise_needs"],
            raw=raw,
        )
