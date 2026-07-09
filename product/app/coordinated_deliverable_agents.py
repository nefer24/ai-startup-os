"""Coordination d'un **petit ensemble de livrables candidats cohérents** (Phase 10).

Responsabilité : **coordonner** — à partir d'une exploitation **approuvée** (Phase 9), produire
un lot limité (2 à 5) de livrables candidats **liés entre eux**, traçable et validable par le CEO.
Aucune livraison finale, aucun déploiement, aucune modification du repo, aucun multi-LLM.

Processus simple et contrôlé, **cinq vrais appels LLM** (mockés en test) :

  1. Exploitation Context Reader        — lit l'exploitation approuvée, sa provenance ;
  2. Deliverable Set Planner            — plan de coordination (ordre, dépendances, rôles) ;
  3. Coordinated Deliverable Producer   — produit les items candidats du lot (liste structurée) ;
  4. Cross-Deliverable Consistency Reviewer — cohérence globale (contradictions, trous, ordre) ;
  5. Quality & Governance Reviewer      — conformité, garde-fous, points à valider CEO.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.agent_utils import as_text, parse_json, parse_json_fields
from app.llm import LLMClient

EXPLOITATION_CONTEXT_READER_ROLE = (
    "Tu es l'Exploitation Context Reader AI-SOS. Tu lis l'exploitation APPROUVÉE par le CEO, sa "
    "provenance et la référence officielle utilisée, et tu poses le contexte de départ du lot de "
    "livrables. Tu n'inventes rien au-delà de l'exploitation et de sa référence."
)

DELIVERABLE_SET_PLANNER_ROLE = (
    "Tu es le Deliverable Set Planner AI-SOS. À partir de la liste de livrables demandée par le "
    "CEO, tu produis un PLAN DE COORDINATION : ordre logique, dépendances entre livrables et rôle "
    "de chacun. Tu ne remplaces pas le choix du CEO : tu organises seulement ce qui est demandé."
)

COORDINATED_DELIVERABLE_PRODUCER_ROLE = (
    "Tu es le Coordinated Deliverable Producer AI-SOS. À partir du plan de coordination, tu "
    "produis chaque livrable candidat du lot, cohérent avec les autres et limité au périmètre. "
    "Tu ne déploies rien et ne produis pas de gros code applicatif."
)

CROSS_DELIVERABLE_CONSISTENCY_ROLE = (
    "Tu es le Cross-Deliverable Consistency Reviewer AI-SOS. Tu vérifies la cohérence GLOBALE "
    "entre les livrables : contradictions, trous fonctionnels, ordre logique, redondances, "
    "dépendances et alignement avec l'exploitation et la référence."
)

QUALITY_GOVERNANCE_ROLE = (
    "Tu es le Quality & Governance Reviewer AI-SOS. Tu vérifies que la source est une exploitation "
    "approuvée, que les livrables restent candidats, que le lot ne déclenche aucun déploiement ni "
    "livraison externe et ne modifie pas le repo, et tu listes les points à valider par le CEO."
)


@dataclass(frozen=True)
class BatchInput:
    """Contexte de coordination : l'exploitation approuvée et la demande de lot du CEO."""

    exploitation_title: str
    exploitation_output: str
    reference_version_number: int
    objective: str
    requested_deliverables: list[str]
    coordination_instructions: str
    constraints: str
    acceptance_focus: str


@dataclass(frozen=True)
class ItemDraft:
    """Un livrable candidat du lot (sortie du Producer, normalisée)."""

    item_type: str
    title: str
    content: str
    dependencies: str
    consistency_notes: str
    validation_notes: str
    order_index: int


@dataclass(frozen=True)
class BatchPlan:
    """Sortie du Deliverable Set Planner."""

    coordination_plan: str
    provenance_notes: str
    raw: str


@dataclass(frozen=True)
class CoherenceReview:
    """Sortie du Cross-Deliverable Consistency Reviewer."""

    coherence_review: str
    raw: str


@dataclass(frozen=True)
class QualityReview:
    """Sortie du Quality & Governance Reviewer."""

    quality_review: str
    risks: str
    ceo_validation_notes: str
    raw: str = field(default="")


def _format_input(data: BatchInput) -> str:
    """Bloc texte décrivant l'exploitation approuvée et la demande (partagé par les prompts)."""
    requested = ", ".join(data.requested_deliverables)
    return (
        f"Exploitation approuvée : {data.exploitation_title}\n"
        f"Sortie de l'exploitation (candidate output) :\n{data.exploitation_output}\n\n"
        f"Référence officielle sous-jacente : V{data.reference_version_number}\n"
        f"Objectif du lot : {data.objective}\n"
        f"Livrables demandés par le CEO : {requested}\n"
        f"Instructions de coordination : {data.coordination_instructions}\n"
        f"Contraintes : {data.constraints}\n"
        f"Critères d'acceptation à privilégier : {data.acceptance_focus}"
    )


class ExploitationContextReader:
    """Agent 1 — lit l'exploitation approuvée, sa provenance et la référence utilisée."""

    name = "Exploitation Context Reader"
    role = EXPLOITATION_CONTEXT_READER_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: BatchInput) -> str:
        """Retourne le contexte de départ du lot, en texte clair."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            "Pose le contexte de départ : acquis de l'exploitation, périmètre, points d'attention "
            "pour produire un lot cohérent sans sortir du cadre."
        )
        return self._llm.complete(prompt)


class DeliverableSetPlanner:
    """Agent 2 — plan de coordination (ordre, dépendances, rôle de chaque livrable)."""

    name = "Deliverable Set Planner"
    role = DELIVERABLE_SET_PLANNER_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: BatchInput, context: str) -> BatchPlan:
        """Retourne le plan de coordination et les notes de provenance."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Contexte de départ :\n{context}\n\n"
            "Réponds STRICTEMENT en JSON, sans texte autour, avec exactement ces clés "
            '(valeurs = chaînes) : {"coordination_plan": "...", "provenance_notes": "..."}. '
            "`provenance_notes` rappelle que le lot se fonde sur une exploitation approuvée par "
            "le CEO et la référence officielle sous-jacente."
        )
        raw = self._llm.complete(prompt)
        fields = parse_json_fields(raw, ["coordination_plan", "provenance_notes"])
        if fields is None:
            return BatchPlan(coordination_plan=raw.strip(), provenance_notes="", raw=raw)
        return BatchPlan(
            coordination_plan=fields["coordination_plan"],
            provenance_notes=fields["provenance_notes"],
            raw=raw,
        )


class CoordinatedDeliverableProducer:
    """Agent 3 — produit les items candidats du lot (liste structurée et cohérente)."""

    name = "Coordinated Deliverable Producer"
    role = COORDINATED_DELIVERABLE_PRODUCER_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: BatchInput, coordination_plan: str) -> tuple[list[ItemDraft], str]:
        """Retourne la liste des items candidats et la sortie brute de l'agent.

        Chaque `item_type` demandé par le CEO donne un item ; si le LLM renvoie une liste
        exploitable, elle est utilisée, sinon on retombe sur un item par type demandé.
        """
        requested = ", ".join(data.requested_deliverables)
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Plan de coordination :\n{coordination_plan}\n\n"
            f"Produis EXACTEMENT un livrable par type demandé ({requested}). Réponds STRICTEMENT "
            "en JSON, sans texte autour : une LISTE d'objets, chacun avec exactement ces clés "
            '(valeurs = chaînes sauf order_index entier) : {"item_type": "...", "title": "...", '
            '"content": "...", "dependencies": "...", "consistency_notes": "...", '
            '"validation_notes": "...", "order_index": 0}.'
        )
        raw = self._llm.complete(prompt)
        items = self._parse_items(raw, data.requested_deliverables)
        return items, raw

    def _parse_items(self, raw: str, requested: list[str]) -> list[ItemDraft]:
        """Parse la liste d'items JSON ; repli sur un item par type demandé si non exploitable."""
        data = parse_json(raw)
        drafts: list[ItemDraft] = []
        if isinstance(data, list):
            for index, entry in enumerate(data):
                if not isinstance(entry, dict):
                    continue
                drafts.append(
                    ItemDraft(
                        item_type=as_text(entry.get("item_type", "")).strip()
                        or (requested[index] if index < len(requested) else f"item_{index}"),
                        title=as_text(entry.get("title", "")),
                        content=as_text(entry.get("content", "")),
                        dependencies=as_text(entry.get("dependencies", "")),
                        consistency_notes=as_text(entry.get("consistency_notes", "")),
                        validation_notes=as_text(entry.get("validation_notes", "")),
                        order_index=_as_int(entry.get("order_index", index), index),
                    )
                )
        if drafts:
            return drafts
        # Repli : un item par type demandé, contenu = sortie brute (traçabilité).
        return [
            ItemDraft(
                item_type=item_type,
                title=item_type,
                content=raw.strip(),
                dependencies="",
                consistency_notes="",
                validation_notes="",
                order_index=index,
            )
            for index, item_type in enumerate(requested)
        ]


class CrossDeliverableConsistencyReviewer:
    """Agent 4 — cohérence globale entre les livrables du lot."""

    name = "Cross-Deliverable Consistency Reviewer"
    role = CROSS_DELIVERABLE_CONSISTENCY_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: BatchInput, items_summary: str) -> CoherenceReview:
        """Retourne la revue de cohérence inter-livrables, en texte clair."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Livrables produits (résumé) :\n{items_summary}\n\n"
            "Analyse la cohérence globale : contradictions, trous, ordre logique, redondances, "
            "dépendances et alignement avec l'exploitation et la référence."
        )
        return CoherenceReview(coherence_review=self._llm.complete(prompt), raw="")


class QualityGovernanceReviewer:
    """Agent 5 — conformité, garde-fous, points à valider par le CEO."""

    name = "Quality & Governance Reviewer"
    role = QUALITY_GOVERNANCE_ROLE

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def run(self, data: BatchInput, coherence_review: str) -> QualityReview:
        """Retourne la revue qualité, les risques et les notes de validation CEO."""
        prompt = (
            f"{self.role}\n\n"
            f"{_format_input(data)}\n\n"
            f"Revue de cohérence :\n{coherence_review}\n\n"
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


def _as_int(value: object, default: int) -> int:
    """Convertit une valeur en entier, avec repli sur `default`."""
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return default
    return default
