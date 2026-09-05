"""Composition d'une équipe OT-V1 (incrément 1) — règles codées, sans appel LLM.

Ordre de construction (Décision 026 §3) :

    dimensions pertinentes → cellules → profondeur nécessaire → contrainte par le budget

et jamais « classe → nombre fixe d'experts ». Le nombre d'experts **émerge** : il dépend du nombre
de dimensions que le cadrage a fait apparaître, de leur criticité présumée, et du budget de la
mission. Les dix angles historiques (`EXPERT_ARCHETYPES`) servent de **catalogue ouvert** : on y
puise des angles, on n'en convoque jamais la totalité par défaut, et un angle proposé par le cadrage
peut s'y ajouter librement. Le mécanisme historique qui stampe dix experts par spécialité
(`build_expert_cells`) n'est **pas** appelé.

Deux bornes existent, toutes deux **économiques et non doctrinales** :
  * `max_angles_per_cell` (défaut 3) — borne EXPÉRIMENTALE et TEMPORAIRE de l'incrément 1, destinée
    à être remplacée par les résultats du protocole de profondeur ; jamais une profondeur normale ;
  * `max_experts` — découle du plafond d'appels de la mission (chaque expert = 2 appels).

Toute décision de composition est journalisée : dimension → angle → justification.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.company_agents import EXPERT_ARCHETYPES
from app.mission_schemas import DimensionOut, FramingOutput

# Ordre par défaut des angles du catalogue quand le cadrage n'en suggère pas assez. Le
# « Synthétiseur / arbitre » est exclu du Tour 0 : c'est un rôle de synthèse, pas une perspective
# d'exploration indépendante.
DEFAULT_ANGLE_ORDER: tuple[str, ...] = (
    "Praticien / implémentation",
    "Expert risques / sécurité",
    "Théoricien / fondamentaux",
    "Expert données / mesure",
    "Red Team / adversaire",
    "Auditeur / conformité",
    "Expert UX / utilisateur",
    "Expert intégration / dépendances",
    "Expert performance / optimisation",
)
CONTRADICTOR_ANGLE = "Red Team / adversaire"
EXCLUDED_FROM_TOUR0 = frozenset({"Synthétiseur / arbitre"})

# Profondeur initiale MODESTE par criticité présumée (avant approfondissement, qui relève des
# incréments suivants). Ce ne sont pas des quotas : elles sont bornées par la classe et le budget.
INITIAL_DEPTH_BY_CRITICALITY = {"low": 1, "medium": 2, "high": 3}

_CATALOGUE: dict[str, dict[str, str]] = {arch["title"]: arch for arch in EXPERT_ARCHETYPES}

# Mots-clés permettant de rattacher un angle libre du cadrage à un angle du catalogue.
_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Théoricien / fondamentaux": ("théor", "fondament", "principe", "concept"),
    "Praticien / implémentation": ("pratic", "terrain", "mise en œuvre", "opération", "faisab"),
    "Auditeur / conformité": ("conform", "audit", "juridi", "réglement", "légal", "fiscal"),
    "Red Team / adversaire": ("adversa", "red team", "contradict", "attaqu", "sceptique"),
    "Expert performance / optimisation": ("performance", "optimis", "efficacité", "coût"),
    "Expert intégration / dépendances": ("intégr", "dépendance", "écosystème", "fournisseur"),
    "Expert risques / sécurité": ("risque", "sécurité", "irréversib", "danger"),
    "Expert UX / utilisateur": ("utilisateur", "usage", "client", "patient", "expérience"),
    "Expert données / mesure": ("donnée", "mesure", "chiffre", "indicateur", "preuve"),
}


@dataclass
class ExpertSpec:
    """Fiche de perspective d'un expert du Tour 0."""

    expert_id: str
    dimension: str
    angle_title: str
    angle_source: str  # "cadrage" | "catalogue" | "contradicteur"
    angle_of_analysis: str
    debate_role: str
    expected_objections: str
    expected_contribution: str
    justification: str
    contradicts_preference: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Représentation sérialisable."""
        return asdict(self)


@dataclass
class CompositionResult:
    """Résultat de la composition : experts, cellules, journal, bornes appliquées."""

    experts: list[ExpertSpec] = field(default_factory=list)
    cells: list[dict[str, Any]] = field(default_factory=list)
    journal: list[dict[str, Any]] = field(default_factory=list)
    uncovered_dimensions: list[str] = field(default_factory=list)
    bounds: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Représentation sérialisable (persistée dans la mission)."""
        return {
            "experts": [e.to_dict() for e in self.experts],
            "cells": self.cells,
            "journal": self.journal,
            "uncovered_dimensions": self.uncovered_dimensions,
            "bounds": self.bounds,
        }


def match_catalogue_angle(free_angle: str) -> str | None:
    """Rattache un angle libre du cadrage à un angle du catalogue (par mots-clés), ou None."""
    text = free_angle.lower()
    for title, keywords in _KEYWORDS.items():
        if title.lower() in text or any(k in text for k in keywords):
            return title
    return None


def _initial_depth(criticality: str, effective_class: str, max_angles_per_cell: int) -> int:
    depth = INITIAL_DEPTH_BY_CRITICALITY.get(criticality, 2)
    if effective_class == "courante":
        # Classe courante : profondeur initiale minimale (une perspective par dimension).
        depth = 1
    return max(1, min(depth, max_angles_per_cell))


def _angles_for_cell(dimension: DimensionOut, depth: int) -> list[tuple[str, str]]:
    """Choisit `depth` angles pour une cellule : d'abord ceux du cadrage, puis le catalogue."""
    chosen: list[tuple[str, str]] = []
    used_titles: set[str] = set()
    for free in dimension.suggested_angles:
        if len(chosen) >= depth:
            break
        title = match_catalogue_angle(free)
        if title is not None and title not in used_titles and title not in EXCLUDED_FROM_TOUR0:
            chosen.append((title, "cadrage"))
            used_titles.add(title)
        elif title is None and free.strip():
            label = free.strip()
            if label not in used_titles:
                chosen.append((label, "cadrage"))
                used_titles.add(label)
    for title in DEFAULT_ANGLE_ORDER:
        if len(chosen) >= depth:
            break
        if title not in used_titles:
            chosen.append((title, "catalogue"))
            used_titles.add(title)
    return chosen[:depth]


def _spec(
    expert_id: str,
    dimension: str,
    title: str,
    source: str,
    justification: str,
    contradicts_preference: bool = False,
) -> ExpertSpec:
    arch = _CATALOGUE.get(title)
    if arch is None:
        # Angle libre proposé par le cadrage : fiche minimale, sans inventer de rôle de débat.
        return ExpertSpec(
            expert_id=expert_id,
            dimension=dimension,
            angle_title=title,
            angle_source=source,
            angle_of_analysis=title,
            debate_role="Apporte la perspective nommée par le cadrage",
            expected_objections="",
            expected_contribution="",
            justification=justification,
            contradicts_preference=contradicts_preference,
        )
    return ExpertSpec(
        expert_id=expert_id,
        dimension=dimension,
        angle_title=title,
        angle_source=source,
        angle_of_analysis=arch["angle_of_analysis"],
        debate_role=arch["debate_role"],
        expected_objections=arch["expected_objections"],
        expected_contribution=arch["expected_contribution"],
        justification=justification,
        contradicts_preference=contradicts_preference,
    )


def compose(
    framing: FramingOutput,
    *,
    effective_class: str,
    ceo_preference: str,
    max_angles_per_cell: int,
    max_experts: int,
) -> CompositionResult:
    """Compose l'équipe du Tour 0 à partir des dimensions émergentes du cadrage."""
    result = CompositionResult(
        bounds={
            "max_angles_per_cell": max_angles_per_cell,
            "max_angles_per_cell_nature": (
                "borne expérimentale temporaire de l'incrément 1, non doctrinale, paramétrable ; "
                "à remplacer par les résultats du protocole de profondeur"
            ),
            "max_experts_by_budget": max_experts,
            "effective_class": effective_class,
        }
    )
    dimensions = list(framing.dimensions)
    if not dimensions:
        dimensions = [
            DimensionOut(
                name="situation d'ensemble",
                why="le cadrage n'a fait émerger aucune dimension distincte",
                presumed_criticality="low",
            )
        ]
        result.journal.append(
            {
                "event": "dimension_par_defaut",
                "detail": "aucune dimension émergente : une cellule unique 'situation d'ensemble'",
            }
        )

    # 1) Profondeur initiale par cellule (modeste), puis angles choisis.
    plan: list[dict[str, Any]] = []
    for dim in dimensions:
        depth = _initial_depth(dim.presumed_criticality, effective_class, max_angles_per_cell)
        plan.append({"dimension": dim, "depth": depth, "angles": _angles_for_cell(dim, depth)})
        result.journal.append(
            {
                "event": "profondeur_initiale",
                "dimension": dim.name,
                "criticality": dim.presumed_criticality,
                "depth": depth,
                "detail": (
                    f"criticité présumée {dim.presumed_criticality} → {depth} angle(s) "
                    f"(classe {effective_class}, borne {max_angles_per_cell})"
                ),
            }
        )

    # 2) Contrainte par le budget : retirer d'abord la profondeur des cellules les moins critiques,
    #    puis, en dernier recours, des dimensions entières (journalisées comme non couvertes).
    order = {"high": 0, "medium": 1, "low": 2}

    def total() -> int:
        return sum(len(p["angles"]) for p in plan)

    while total() > max_experts:
        candidates = [p for p in plan if len(p["angles"]) > 1]
        if candidates:
            victim = sorted(
                candidates,
                key=lambda p: (-order.get(p["dimension"].presumed_criticality, 1), p["depth"]),
            )[0]
            removed = victim["angles"].pop()
            result.journal.append(
                {
                    "event": "reduction_budget",
                    "dimension": victim["dimension"].name,
                    "removed_angle": removed[0],
                    "detail": "plafond d'appels de la mission : profondeur réduite",
                }
            )
            continue
        # Toutes les cellules sont à 1 : retirer la dimension la moins critique.
        victim = sorted(plan, key=lambda p: -order.get(p["dimension"].presumed_criticality, 1))[0]
        plan.remove(victim)
        result.uncovered_dimensions.append(victim["dimension"].name)
        result.journal.append(
            {
                "event": "dimension_non_couverte",
                "dimension": victim["dimension"].name,
                "detail": "plafond d'appels de la mission : dimension non explorée au Tour 0",
            }
        )
        if not plan:
            break

    # 3) T26 — préférence CEO : au moins une perspective susceptible de la contredire, placée sur
    #    la dimension la plus critique, sans opposition artificielle (une seule, pas davantage).
    if ceo_preference.strip() and plan:
        already = any(a[0] == CONTRADICTOR_ANGLE for p in plan for a in p["angles"])
        target = sorted(plan, key=lambda p: order.get(p["dimension"].presumed_criticality, 1))[0]
        if not already:
            if len(target["angles"]) < max_angles_per_cell and total() < max_experts:
                target["angles"].append((CONTRADICTOR_ANGLE, "contradicteur"))
                action = "ajouté"
            else:
                target["angles"][-1] = (CONTRADICTOR_ANGLE, "contradicteur")
                action = "substitué au dernier angle"
            result.journal.append(
                {
                    "event": "perspective_contraire_preference",
                    "dimension": target["dimension"].name,
                    "angle": CONTRADICTOR_ANGLE,
                    "detail": (
                        f"préférence du demandeur déclarée → angle contradicteur {action} sur la "
                        "dimension la plus critique (neutralité de composition)"
                    ),
                }
            )
        else:
            result.journal.append(
                {
                    "event": "perspective_contraire_preference",
                    "detail": (
                        "un angle contradicteur était déjà présent : le mandat de contredire la "
                        "préférence lui est confié, aucun ajout"
                    ),
                }
            )

    # 4) Fiches d'experts et journal dimension → angle → justification.
    counter = 0
    for p in plan:
        dimension: DimensionOut = p["dimension"]
        cell_angles: list[str] = []
        for title, source in p["angles"]:
            counter += 1
            expert_id = f"E{counter}"
            contradicts = bool(ceo_preference.strip()) and title == CONTRADICTOR_ANGLE
            if source == "cadrage":
                why = f"angle appelé par le cadrage pour la dimension « {dimension.name} »"
            elif source == "contradicteur":
                why = "perspective chargée de contredire la préférence déclarée du demandeur"
            else:
                why = (
                    f"angle du catalogue retenu pour couvrir la dimension « {dimension.name} » "
                    f"(criticité présumée {dimension.presumed_criticality})"
                )
            if contradicts and ceo_preference.strip():
                why += f" ; préférence à challenger : {ceo_preference.strip()[:200]}"
            spec = _spec(expert_id, dimension.name, title, source, why, contradicts)
            result.experts.append(spec)
            cell_angles.append(title)
            result.journal.append(
                {
                    "event": "expert",
                    "expert_id": expert_id,
                    "dimension": dimension.name,
                    "angle": title,
                    "source": source,
                    "justification": why,
                }
            )
        result.cells.append(
            {
                "dimension": dimension.name,
                "criticality": dimension.presumed_criticality,
                "angles": cell_angles,
                "depth": len(cell_angles),
            }
        )
    return result
