"""Fabrique d'**entreprises IA spécialisées** — composition (Phase 4B-R).

Réalignement fondateur : AI-SOS n'est pas une plateforme de conseil qui explique comment
faire ; c'est une **fabrique d'entreprises IA spécialisées**. À partir d'un plan ou d'une
amélioration approuvé, AI-SOS **compose une entreprise IA temporaire candidate** organisée pour
produire un livrable concret : départements, spécialités, cellules d'au moins 10 experts par
spécialité, protocole de débat contradictoire, coordination interne et contrat de livraison.

Cette couche **compose seulement** : elle n'exécute jamais la production. L'entreprise reste
candidate jusqu'à validation CEO.

Quatre vrais appels LLM (mockés en test) couvrant les cinq blocs de responsabilité :
  1. AI Company Architect         — nom, mission, objectif, départements ;
  2. Department & Specialty Designer — départements → spécialités de production ;
  3. Debate Protocol Architect    — débat contradictoire, coordination, workflow de production ;
  4. Delivery & Governance Reviewer — livrables concrets, contrat de livraison, validations CEO.

Le **cinquième bloc — Expert Cell Designer** — est réalisé de façon déterministe par AI-SOS
(`build_expert_cells`) : chaque spécialité est développée en une cellule de **10 experts** aux
angles d'analyse et rôles de débat distincts, ce qui **garantit** l'invariant « ≥ 10 experts par
spécialité » quelle que soit la sortie du LLM.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agent_utils import parse_json, parse_json_fields
from app.llm import LLMClient

AI_COMPANY_ARCHITECT_ROLE = (
    "Tu es l'AI Company Architect AI-SOS. À partir d'un plan ou d'une amélioration approuvé, "
    "tu conçois une entreprise IA spécialisée temporaire, organisée pour produire un livrable "
    "concret : tu proposes son nom, sa mission, son objectif et ses départements de production."
)

DEPARTMENT_DESIGNER_ROLE = (
    "Tu es le Department & Specialty Designer AI-SOS. À partir des départements, tu définis les "
    "spécialités de production nécessaires, chacune rattachée à un département."
)

DEBATE_PROTOCOL_ARCHITECT_ROLE = (
    "Tu es le Debate Protocol Architect AI-SOS. Tu définis un protocole de débat contradictoire "
    "(analyse individuelle, propositions, critique croisée, désaccords conservés, arbitrage par "
    "un synthétiseur, synthèse, remontée département, coordination inter-départements, validation "
    "CEO), le modèle de coordination interne et le workflow de production."
)

DELIVERY_GOVERNANCE_ROLE = (
    "Tu es le Delivery & Governance Reviewer AI-SOS. Tu définis les livrables concrets, le contrat "
    "de livraison (ce que l'entreprise IA doit livrer), les points de validation CEO, les notes de "
    "gouvernance et les risques. L'entreprise ne s'exécute jamais sans validation CEO explicite."
)

# Dix archétypes d'experts conçus pour DÉBATTRE (pas pour être d'accord). Chaque spécialité est
# développée en une cellule de 10 experts couvrant ces angles complémentaires et contradictoires.
EXPERT_ARCHETYPES: list[dict[str, str]] = [
    {
        "title": "Théoricien / fondamentaux",
        "angle_of_analysis": "Rigueur des fondamentaux et hypothèses de base",
        "debate_role": "Défend les principes ; conteste les raccourcis",
        "expected_objections": "Hypothèses non fondées, raisonnement fragile",
        "expected_contribution": "Cadre théorique solide",
    },
    {
        "title": "Praticien / implémentation",
        "angle_of_analysis": "Faisabilité concrète et coût de mise en œuvre",
        "debate_role": "Confronte la théorie au terrain",
        "expected_objections": "Trop abstrait, non implémentable en l'état",
        "expected_contribution": "Chemin d'implémentation réaliste",
    },
    {
        "title": "Auditeur / conformité",
        "angle_of_analysis": "Conformité, normes et traçabilité",
        "debate_role": "Vérifie le respect des règles",
        "expected_objections": "Écarts de conformité, angles non tracés",
        "expected_contribution": "Grille de conformité",
    },
    {
        "title": "Red Team / adversaire",
        "angle_of_analysis": "Attaque et scénarios d'échec",
        "debate_role": "Cherche activement à casser la proposition",
        "expected_objections": "Vecteurs d'abus, cas limites ignorés",
        "expected_contribution": "Liste des failles et contre-mesures",
    },
    {
        "title": "Expert performance / optimisation",
        "angle_of_analysis": "Performance, coût et passage à l'échelle",
        "debate_role": "Défend l'efficience contre la sur-ingénierie",
        "expected_objections": "Goulots d'étranglement, coûts cachés",
        "expected_contribution": "Cibles de performance chiffrées",
    },
    {
        "title": "Expert intégration / dépendances",
        "angle_of_analysis": "Intégration, dépendances et interfaces",
        "debate_role": "Met en évidence les couplages risqués",
        "expected_objections": "Dépendances fragiles, verrouillage fournisseur",
        "expected_contribution": "Carte des dépendances et contrats d'interface",
    },
    {
        "title": "Expert risques / sécurité",
        "angle_of_analysis": "Sécurité, confidentialité et risques",
        "debate_role": "Priorise la réduction des risques",
        "expected_objections": "Surface d'attaque, données sensibles exposées",
        "expected_contribution": "Analyse de risques et garde-fous",
    },
    {
        "title": "Expert UX / utilisateur",
        "angle_of_analysis": "Valeur d'usage et expérience utilisateur",
        "debate_role": "Défend l'utilisateur final",
        "expected_objections": "Complexité inutile, valeur d'usage floue",
        "expected_contribution": "Parcours utilisateur et critères d'usage",
    },
    {
        "title": "Expert données / mesure",
        "angle_of_analysis": "Données, métriques et preuve d'impact",
        "debate_role": "Exige des preuves mesurables",
        "expected_objections": "Affirmations non mesurées, biais de données",
        "expected_contribution": "Indicateurs et plan de mesure",
    },
    {
        "title": "Synthétiseur / arbitre",
        "angle_of_analysis": "Vue d'ensemble et arbitrage des désaccords",
        "debate_role": "Arbitre le débat et produit la synthèse de cellule",
        "expected_objections": "Désaccords non résolus, angles manquants",
        "expected_contribution": "Synthèse arbitrée conservant les désaccords utiles",
    },
]

EXPERTS_PER_SPECIALTY = len(EXPERT_ARCHETYPES)


@dataclass(frozen=True)
class CompanyInput:
    """Contexte de composition : la source approuvée à entreprendre."""

    source_type: str
    source_title: str
    source_summary: str


@dataclass(frozen=True)
class CompanyDesign:
    """Sortie de l'AI Company Architect."""

    ai_company_name: str
    company_mission: str
    company_goal: str
    departments: str
    raw: str


@dataclass(frozen=True)
class Specialty:
    """Une spécialité de production rattachée à un département."""

    department: str
    specialty: str


@dataclass(frozen=True)
class DebateDesign:
    """Sortie du Debate Protocol Architect."""

    debate_protocol: str
    coordination_model: str
    production_workflow: str
    raw: str


@dataclass(frozen=True)
class DeliveryDesign:
    """Sortie du Delivery & Governance Reviewer."""

    concrete_deliverables: str
    delivery_contract: str
    ceo_validation_points: str
    governance_notes: str
    risks: str
    raw: str


def _format_input(data: CompanyInput) -> str:
    """Bloc texte décrivant la source approuvée, réutilisé par tous les prompts."""
    return (
        f"Type de source : {data.source_type}\n"
        f"Titre de la source : {data.source_title}\n"
        f"Résumé de la source :\n{data.source_summary}"
    )


class AICompanyArchitect:
    """Agent 1 — conçoit l'entreprise IA : nom, mission, objectif, départements."""

    name = "AI Company Architect"
    role = AI_COMPANY_ARCHITECT_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: CompanyInput) -> CompanyDesign:
        """Retourne le nom, la mission, l'objectif et les départements de l'entreprise IA."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            "Réponds STRICTEMENT en JSON, sans texte autour, avec exactement ces clés "
            '(valeurs = chaînes) : {"ai_company_name": "...", "company_mission": "...", '
            '"company_goal": "...", "departments": "..."}.'
        )
        raw = self._llm.complete(prompt)
        fields = parse_json_fields(
            raw, ["ai_company_name", "company_mission", "company_goal", "departments"]
        )
        if fields is None:
            return CompanyDesign(
                ai_company_name="",
                company_mission="",
                company_goal="",
                departments=raw.strip(),
                raw=raw,
            )
        return CompanyDesign(
            ai_company_name=fields["ai_company_name"],
            company_mission=fields["company_mission"],
            company_goal=fields["company_goal"],
            departments=fields["departments"],
            raw=raw,
        )


class DepartmentSpecialtyDesigner:
    """Agent 2 — définit les spécialités de production, rattachées aux départements."""

    name = "Department & Specialty Designer"
    role = DEPARTMENT_DESIGNER_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: CompanyInput, departments: str) -> list[Specialty]:
        """Retourne la liste des spécialités (au moins une, repli déterministe si besoin)."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Départements proposés :\n{departments}\n\n"
            "Réponds STRICTEMENT en JSON, sans texte autour : "
            '{"specialties": [{"department": "...", "specialty": "..."}, ...]}.'
        )
        raw = self._llm.complete(prompt)
        return _parse_specialties(raw)


def _parse_specialties(raw: str) -> list[Specialty]:
    """Extrait les spécialités du JSON ; repli sur une spécialité générique si nécessaire."""
    data = parse_json(raw)
    items: Any = None
    if isinstance(data, dict):
        items = data.get("specialties")
    elif isinstance(data, list):
        items = data
    specialties: list[Specialty] = []
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                specialty = str(item.get("specialty", "")).strip()
                department = str(item.get("department", "")).strip()
                if specialty:
                    specialties.append(
                        Specialty(department=department or "Général", specialty=specialty)
                    )
    if not specialties:
        specialties.append(Specialty(department="Général", specialty="Production générale"))
    return specialties


def build_expert_cells(specialties: list[Specialty]) -> list[dict[str, Any]]:
    """Développe chaque spécialité en une cellule de 10 experts (invariant garanti).

    Chaque expert porte les 8 champs attendus : name, specialty, expertise_area, skills,
    angle_of_analysis, debate_role, expected_objections, expected_contribution.
    """
    cells: list[dict[str, Any]] = []
    for sp in specialties:
        experts: list[dict[str, str]] = []
        for index, arch in enumerate(EXPERT_ARCHETYPES, start=1):
            experts.append(
                {
                    "name": f"Expert {index} — {arch['title']} ({sp.specialty})",
                    "specialty": sp.specialty,
                    "expertise_area": f"{sp.specialty} — {arch['title']}",
                    "skills": arch["angle_of_analysis"],
                    "angle_of_analysis": arch["angle_of_analysis"],
                    "debate_role": arch["debate_role"],
                    "expected_objections": arch["expected_objections"],
                    "expected_contribution": arch["expected_contribution"],
                }
            )
        cells.append({"department": sp.department, "specialty": sp.specialty, "experts": experts})
    return cells


class DebateProtocolArchitect:
    """Agent 3 — protocole de débat contradictoire, coordination, workflow de production."""

    name = "Debate Protocol Architect"
    role = DEBATE_PROTOCOL_ARCHITECT_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: CompanyInput) -> DebateDesign:
        """Retourne le protocole de débat, le modèle de coordination et le workflow."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            "Réponds STRICTEMENT en JSON, sans texte autour, avec exactement ces clés "
            '(valeurs = chaînes) : {"debate_protocol": "...", "coordination_model": "...", '
            '"production_workflow": "..."}.'
        )
        raw = self._llm.complete(prompt)
        fields = parse_json_fields(
            raw, ["debate_protocol", "coordination_model", "production_workflow"]
        )
        if fields is None:
            return DebateDesign(
                debate_protocol=raw.strip(),
                coordination_model="",
                production_workflow="",
                raw=raw,
            )
        return DebateDesign(
            debate_protocol=fields["debate_protocol"],
            coordination_model=fields["coordination_model"],
            production_workflow=fields["production_workflow"],
            raw=raw,
        )


class DeliveryGovernanceReviewer:
    """Agent 4 — livrables concrets, contrat de livraison, validations CEO, risques."""

    name = "Delivery & Governance Reviewer"
    role = DELIVERY_GOVERNANCE_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: CompanyInput, company_goal: str) -> DeliveryDesign:
        """Retourne les livrables, le contrat de livraison, les validations CEO et les risques."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Objectif de l'entreprise IA :\n{company_goal}\n\n"
            "Réponds STRICTEMENT en JSON, sans texte autour, avec exactement ces clés "
            '(valeurs = chaînes) : {"concrete_deliverables": "...", "delivery_contract": "...", '
            '"ceo_validation_points": "...", "governance_notes": "...", "risks": "..."}.'
        )
        raw = self._llm.complete(prompt)
        fields = parse_json_fields(
            raw,
            [
                "concrete_deliverables",
                "delivery_contract",
                "ceo_validation_points",
                "governance_notes",
                "risks",
            ],
        )
        if fields is None:
            return DeliveryDesign(
                concrete_deliverables=raw.strip(),
                delivery_contract="",
                ceo_validation_points="",
                governance_notes="",
                risks="",
                raw=raw,
            )
        return DeliveryDesign(
            concrete_deliverables=fields["concrete_deliverables"],
            delivery_contract=fields["delivery_contract"],
            ceo_validation_points=fields["ceo_validation_points"],
            governance_notes=fields["governance_notes"],
            risks=fields["risks"],
            raw=raw,
        )
