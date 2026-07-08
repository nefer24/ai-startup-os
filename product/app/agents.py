"""Équipe IA minimale du produit — de vrais appels LLM avec des prompts de rôle.

Pas de framework multi-agent (ni LangGraph, ni CrewAI, ni orchestrateur complexe) :
chaque agent est une classe simple qui compose un prompt de rôle et délègue l'appel
réel au `LLMClient` injecté (mocké en test — aucune vraie clé API requise).

Trois rôles :
  * Analyste            — clarifie et structure l'entrée CEO ;
  * Architecte          — propose un plan de solution candidat ;
  * Relecteur risques   — hypothèses, risques, limites, expertises nécessaires.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from app.llm import LLMClient

ANALYST_ROLE = (
    "Tu es l'Analyste AI-SOS. Tu clarifies le problème, l'idée ou l'objectif du CEO. "
    "Tu identifies le contexte, le besoin réel, les contraintes, les bénéficiaires, "
    "les résultats attendus et les zones d'incertitude. "
    "Tu ne proposes pas encore de solution finale."
)

ARCHITECT_ROLE = (
    "Tu es l'Architecte de solution AI-SOS. À partir de l'analyse, tu proposes un plan "
    "de solution candidat clair, structuré et actionnable. Tu privilégies une solution "
    "concrète, différenciante et utile. Le plan reste candidat et doit être validé par le CEO."
)

RISK_ROLE = (
    "Tu es le Relecteur risques AI-SOS. Tu identifies les hypothèses, risques, limites, "
    "dépendances, coûts possibles et points faibles du plan candidat. Tu proposes aussi "
    "les expertises nécessaires pour améliorer le plan."
)


@dataclass(frozen=True)
class AgentInput:
    """Entrée CEO transmise à l'équipe IA."""

    input_type: str
    title: str
    description: str


@dataclass(frozen=True)
class RiskReview:
    """Sortie structurée du Relecteur risques."""

    assumptions: str
    risks: str
    expertise_needs: str
    raw: str


def _format_input(data: AgentInput) -> str:
    """Bloc texte décrivant l'entrée CEO, réutilisé par tous les prompts de rôle."""
    return (
        f"Type d'entrée : {data.input_type}\nTitre : {data.title}\nDescription : {data.description}"
    )


class Analyst:
    """Agent 1 — clarifie et structure l'entrée CEO."""

    name = "Analyste"
    role = ANALYST_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: AgentInput) -> str:
        """Retourne une analyse structurée en texte clair."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            "Rends une analyse structurée : contexte, besoin réel, contraintes, "
            "bénéficiaires, résultats attendus, zones d'incertitude."
        )
        return self._llm.complete(prompt)


class SolutionArchitect:
    """Agent 2 — propose un plan de solution candidat à partir de l'analyse."""

    name = "Architecte de solution"
    role = ARCHITECT_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: AgentInput, analysis: str) -> str:
        """Retourne un plan de solution candidat structuré, en texte clair."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Analyse de l'Analyste :\n{analysis}\n\n"
            "Propose un plan de solution candidat : objectif, étapes concrètes, "
            "éléments différenciants, livrables attendus. Le plan reste candidat."
        )
        return self._llm.complete(prompt)


class RiskReviewer:
    """Agent 3 — identifie hypothèses, risques et expertises nécessaires."""

    name = "Relecteur risques"
    role = RISK_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: AgentInput, analysis: str, candidate_plan: str) -> RiskReview:
        """Retourne une relecture structurée (hypothèses, risques, expertises)."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Analyse :\n{analysis}\n\n"
            f"Plan candidat :\n{candidate_plan}\n\n"
            "Réponds STRICTEMENT en JSON, sans texte autour, avec exactement ces clés "
            '(chaque valeur est une chaîne de texte) : {"assumptions": "...", '
            '"risks": "...", "expertise_needs": "..."}.'
        )
        raw = self._llm.complete(prompt)
        return _parse_risk_review(raw)


def _as_text(value: object) -> str:
    """Normalise une valeur JSON (chaîne, liste, objet) en texte lisible."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(f"- {_as_text(item)}" for item in value)
    if isinstance(value, dict):
        return "\n".join(f"{key}: {_as_text(val)}" for key, val in value.items())
    return str(value)


def _strip_code_fences(text: str) -> str:
    """Retire d'éventuelles balises de bloc de code ```json ... ``` autour du JSON."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    stripped = stripped.strip("`").strip()
    if stripped[:4].lower() == "json":
        stripped = stripped[4:].strip()
    return stripped


def _parse_risk_review(raw: str) -> RiskReview:
    """Parse la sortie JSON du Relecteur ; retombe proprement sur du texte si le JSON échoue."""
    try:
        data = json.loads(_strip_code_fences(raw))
    except (json.JSONDecodeError, ValueError):
        return RiskReview(assumptions="", risks=raw.strip(), expertise_needs="", raw=raw)
    if not isinstance(data, dict):
        return RiskReview(assumptions="", risks=raw.strip(), expertise_needs="", raw=raw)
    return RiskReview(
        assumptions=_as_text(data.get("assumptions", "")),
        risks=_as_text(data.get("risks", "")),
        expertise_needs=_as_text(data.get("expertise_needs", "")),
        raw=raw,
    )
