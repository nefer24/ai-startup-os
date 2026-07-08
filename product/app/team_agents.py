"""Équipe IA de **composition** — compose une équipe IA spécialisée (Phase 4B).

Phrase fondatrice : « Chaque problème, chaque idée ou chaque objectif mérite une équipe
d'experts. AI-SOS crée cette équipe pour l'analyser, le structurer et le transformer en
solution concrète. »

Cette couche ne fait que **composer** l'équipe candidate ; elle n'exécute jamais son travail.
Quatre rôles, quatre vrais appels LLM (mockés en test) :
  1. Team Designer        — identifie les rôles IA nécessaires ;
  2. Skill Mapper         — compétences, responsabilités, entrées/sorties de chaque rôle ;
  3. Workflow Architect   — ordre de travail, dépendances, validations, livrables ;
  4. Governance Reviewer  — points de validation CEO, limites, risques, garde-fous.

Pas de framework multi-agent : chaque agent est une classe simple qui délègue au
`LLMClient` injecté.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agent_utils import parse_json_fields
from app.llm import LLMClient

TEAM_DESIGNER_ROLE = (
    "Tu es le Team Designer AI-SOS. À partir d'un plan de solution ou d'une amélioration "
    "approuvée, tu identifies les rôles IA nécessaires pour transformer le plan en solution "
    "concrète. Tu proposes un nom d'équipe et une mission claire."
)

SKILL_MAPPER_ROLE = (
    "Tu es le Skill Mapper AI-SOS. Pour chaque rôle proposé, tu définis les compétences, "
    "responsabilités, entrées attendues et sorties attendues."
)

WORKFLOW_ARCHITECT_ROLE = (
    "Tu es le Workflow Architect AI-SOS. Tu définis comment les rôles collaborent : ordre "
    "de travail, dépendances, points de validation et livrables attendus."
)

GOVERNANCE_REVIEWER_ROLE = (
    "Tu es le Governance Reviewer AI-SOS. Tu identifies les points de validation CEO, les "
    "limites, les risques, les actions interdites et les garde-fous. L'équipe ne doit jamais "
    "s'exécuter sans validation CEO explicite."
)


@dataclass(frozen=True)
class TeamInput:
    """Contexte de composition : la source approuvée à équiper."""

    source_type: str
    source_title: str
    source_summary: str


@dataclass(frozen=True)
class TeamDesign:
    """Sortie du Team Designer."""

    team_name: str
    mission: str
    roles: str
    raw: str


@dataclass(frozen=True)
class WorkflowPlan:
    """Sortie du Workflow Architect."""

    workflow: str
    deliverables: str
    raw: str


@dataclass(frozen=True)
class GovernanceReview:
    """Sortie du Governance Reviewer."""

    governance_notes: str
    risks: str
    raw: str


def _format_input(data: TeamInput) -> str:
    """Bloc texte décrivant la source approuvée, réutilisé par tous les prompts."""
    return (
        f"Type de source : {data.source_type}\n"
        f"Titre de la source : {data.source_title}\n"
        f"Résumé de la source :\n{data.source_summary}"
    )


class TeamDesigner:
    """Agent 1 — identifie les rôles IA nécessaires, le nom et la mission de l'équipe."""

    name = "Team Designer"
    role = TEAM_DESIGNER_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: TeamInput) -> TeamDesign:
        """Retourne le nom d'équipe, la mission et les rôles proposés."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            "Réponds STRICTEMENT en JSON, sans texte autour, avec exactement ces clés "
            '(valeurs = chaînes de texte) : {"team_name": "...", "mission": "...", '
            '"roles": "..."}.'
        )
        raw = self._llm.complete(prompt)
        fields = parse_json_fields(raw, ["team_name", "mission", "roles"])
        if fields is None:
            return TeamDesign(team_name="", mission="", roles=raw.strip(), raw=raw)
        return TeamDesign(
            team_name=fields["team_name"],
            mission=fields["mission"],
            roles=fields["roles"],
            raw=raw,
        )


class SkillMapper:
    """Agent 2 — définit compétences, responsabilités, entrées/sorties de chaque rôle."""

    name = "Skill Mapper"
    role = SKILL_MAPPER_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: TeamInput, roles: str) -> str:
        """Retourne les compétences par rôle, en texte clair."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Rôles proposés :\n{roles}\n\n"
            "Pour chaque rôle, précise compétences, responsabilités, entrées et sorties."
        )
        return self._llm.complete(prompt)


class WorkflowArchitect:
    """Agent 3 — définit la collaboration entre rôles et les livrables."""

    name = "Workflow Architect"
    role = WORKFLOW_ARCHITECT_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: TeamInput, roles: str, skills: str) -> WorkflowPlan:
        """Retourne le workflow de collaboration et les livrables."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Rôles :\n{roles}\n\n"
            f"Compétences :\n{skills}\n\n"
            "Réponds STRICTEMENT en JSON, sans texte autour, avec exactement ces clés "
            '(valeurs = chaînes de texte) : {"workflow": "...", "deliverables": "..."}.'
        )
        raw = self._llm.complete(prompt)
        fields = parse_json_fields(raw, ["workflow", "deliverables"])
        if fields is None:
            return WorkflowPlan(workflow=raw.strip(), deliverables="", raw=raw)
        return WorkflowPlan(
            workflow=fields["workflow"], deliverables=fields["deliverables"], raw=raw
        )


class GovernanceReviewer:
    """Agent 4 — points de validation CEO, limites, risques, garde-fous."""

    name = "Governance Reviewer"
    role = GOVERNANCE_REVIEWER_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: TeamInput, workflow: str) -> GovernanceReview:
        """Retourne les notes de gouvernance et les risques."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Workflow proposé :\n{workflow}\n\n"
            "Réponds STRICTEMENT en JSON, sans texte autour, avec exactement ces clés "
            '(valeurs = chaînes de texte) : {"governance_notes": "...", "risks": "..."}.'
        )
        raw = self._llm.complete(prompt)
        fields = parse_json_fields(raw, ["governance_notes", "risks"])
        if fields is None:
            return GovernanceReview(governance_notes=raw.strip(), risks="", raw=raw)
        return GovernanceReview(
            governance_notes=fields["governance_notes"], risks=fields["risks"], raw=raw
        )
