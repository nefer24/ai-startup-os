"""Liquidation des dettes de réalignement (C0.R — Realignment Debt Closure).

Tracabilite : docs/strategy/AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md,
TRACEABILITY.md (C0.R), AI-SOS_Vision_Fondatrice_Mission_Produit_Realignement_C0.pdf.

C0.R est un **réalignement documentaire et stratégique** : responsabilité unique **réaligner**. Ces
tests sont des **gardes de documentation** — ils ne testent aucun comportement runtime (C0.R n'en
change aucun). Ils prouvent que : la vision fondatrice est integree dans le repo (document
strategique versionne + les deux phrases fondatrices + Vision Product Compass + dettes + E9 ferme),
que `TRACEABILITY.md` mentionne C0.R et les deux phrases fondatrices, qu'**aucun objet produit
metier actif** (Problem / Idea / Objective / Solution / SolutionTeam...) n'est defini dans
`src/aisos`, et
que les surfaces publiques de C0.1 (`ceo_console`), C0.2 (`api.read`) et C0.3 (`persistence`)
**restent intactes**. E9 reste ferme.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STRATEGY_DOC = (
    _REPO_ROOT / "docs" / "strategy" / "AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md"
)
_TRACEABILITY = _REPO_ROOT / "TRACEABILITY.md"
_SRC = _REPO_ROOT / "src" / "aisos"

_PHRASE_1 = (
    "Chaque problème, chaque idée ou chaque objectif mérite une équipe d'experts. AI-SOS crée "
    "cette équipe pour l'analyser, le structurer et le transformer en solution concrète."
)
_PHRASE_2 = (
    "Lorsqu'une solution existe déjà, AI-SOS l'analyse, identifie ses faiblesses, propose des "
    "améliorations et la fait évoluer afin de la rendre plus performante, plus différenciante et "
    "plus unique."
)


def _normalize(text: str) -> str:
    # Aplati les retours a la ligne et les marqueurs de citation markdown pour comparer le contenu
    # independamment du reformatage (une phrase peut etre repartie sur plusieurs lignes).
    without_quotes = text.replace("\n>", "\n")
    return re.sub(r"\s+", " ", without_quotes)


def _strategy_text() -> str:
    return _normalize(_STRATEGY_DOC.read_text(encoding="utf-8"))


def _traceability_text() -> str:
    return _normalize(_TRACEABILITY.read_text(encoding="utf-8"))


# --- Le document strategique est integre et complet --------------------------------------------


def test_strategy_document_exists() -> None:
    assert _STRATEGY_DOC.is_file()


def test_strategy_document_contains_both_founding_phrases() -> None:
    text = _strategy_text()
    assert _PHRASE_1 in text
    assert _PHRASE_2 in text


@pytest.mark.parametrize(
    "section",
    [
        "Mission principale",
        "Vision Product Compass",
        "Realignment Debts",
        "Debts Closed by C0.R",
        "Debts Still Open",
        "No Code Behavior Change",
        "Roadmap Consequence",
    ],
)
def test_strategy_document_covers_required_sections(section: str) -> None:
    assert section in _strategy_text()


def test_strategy_document_keeps_e9_closed() -> None:
    assert "E9 reste fermé" in _strategy_text()


def test_strategy_document_states_mission_over_governance() -> None:
    text = _strategy_text()
    assert "La gouvernance sert la mission" in text
    assert "ne remplace pas la mission" in text


# --- TRACEABILITY.md mentionne le realignement -------------------------------------------------


def test_traceability_contains_c0r_section() -> None:
    assert "C0.R — Realignment Debt Closure" in _traceability_text()


def test_traceability_contains_both_founding_phrases() -> None:
    text = _traceability_text()
    assert _PHRASE_1 in text
    assert _PHRASE_2 in text


def test_traceability_mentions_e9_closed_in_c0r() -> None:
    text = _traceability_text()
    c0r = text[text.index("C0.R — Realignment Debt Closure") :]
    assert "E9 reste fermé" in c0r


# --- Aucun objet produit metier actif dans le code ---------------------------------------------

_PRODUCT_OBJECT_NAMES = (
    "Problem",
    "Idea",
    "Objective",
    "Solution",
    "SolutionVersion",
    "SolutionTeam",
    "ImprovementOpportunity",
    "SolutionTeamFactory",
    "ProjectTeamFactory",
    "AIOrganizationFactory",
)


@pytest.mark.parametrize("name", _PRODUCT_OBJECT_NAMES)
def test_no_active_product_object_class_defined(name: str) -> None:
    # C0.R ne doit pas implementer les objets produit comme classes actives dans src/aisos.
    pattern = re.compile(rf"^\s*class\s+{re.escape(name)}\b", re.MULTILINE)
    for path in _SRC.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert not pattern.search(source), f"objet produit interdit defini dans {path}: {name}"


# --- Surfaces publiques C0.1 / C0.2 / C0.3 intactes --------------------------------------------


def test_c0_1_public_surface_intact() -> None:
    from aisos.ceo_console import (  # noqa: F401
        CEOReadConsoleView,
        CEORecommendationSummary,
        CEOVisibleGovernanceNature,
    )


def test_c0_2_public_surface_intact() -> None:
    from aisos.api.read import (  # noqa: F401
        APIReadOnlyMethod,
        CEOConsoleReadService,
        build_ceo_console_read_routes,
    )


def test_c0_3_public_surface_intact() -> None:
    from aisos.persistence import (  # noqa: F401
        InMemoryAppendOnlyPersistenceRepository,
        PersistenceRecord,
        PersistenceRecordType,
    )
