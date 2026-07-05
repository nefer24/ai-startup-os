"""evolution — Auto-evolution gouvernee (E7) : proposer son evolution, jamais s'auto-decider.

Une organisation AI-SOS peut **proposer, analyser et preparer** l'evolution de sa propre structure
organisationnelle, **en fonction du probleme a resoudre** — mais **sans jamais s'auto-decider, sans
auto-gouvernance et sans mutation libre**. Le CEO reste l'unique autorite de decision ;
l'orchestrateur gouverne le processus ; le Conseil recommande ; le raisonnement informe ; la memoire
contextualise ; l'audit fait foi ; la federation peut informer, mais ne gouverne jamais l'evolution
locale. **Auto-evolution = proposition gouvernee d'evolution organisationnelle, soumise a decision
CEO.**

E7.1 pose la premiere brique : **representer** un **besoin d'evolution** (`EvolutionNeed`,
`EvolutionNeedKind`, `EvolutionNeedStatus`) — une declaration gouvernee, immuable, portee par le CEO
local, sans pouvoir, sans auto-detection, sans rien declencher.
"""

from __future__ import annotations

from aisos.evolution.need import EvolutionNeed, EvolutionNeedKind, EvolutionNeedStatus

__all__ = [
    "EvolutionNeed",
    "EvolutionNeedKind",
    "EvolutionNeedStatus",
]
