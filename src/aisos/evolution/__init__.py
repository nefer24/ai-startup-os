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

E7.2 pose la deuxieme brique : **proposer** — formuler une **proposition d'evolution
organisationnelle** (`GovernedEvolutionProposal`, `EvolutionProposalType`,
`EvolutionProposalStatus`) liee a un besoin declare (E7.1), portee par le CEO local, immuable et
sans aucun pouvoir de decision, d'analyse, de plan ni d'application.

E7.3 pose la troisieme brique : **analyser** — representer l'**analyse strategique gouvernee**
(`GovernedEvolutionAnalysis`, `EvolutionAnalysisRecommendation`, `EvolutionAnalysisStatus`) d'une
proposition en cours (E7.2), portee par une autorite consultative (jamais le CEO), immuable et sans
aucun pouvoir de decision, de plan ni d'application ; sa recommandation reste **consultative**.
"""

from __future__ import annotations

from aisos.evolution.analysis import (
    EvolutionAnalysisRecommendation,
    EvolutionAnalysisStatus,
    GovernedEvolutionAnalysis,
)
from aisos.evolution.need import EvolutionNeed, EvolutionNeedKind, EvolutionNeedStatus
from aisos.evolution.proposal import (
    EvolutionProposalStatus,
    EvolutionProposalType,
    GovernedEvolutionProposal,
)

__all__ = [
    "EvolutionAnalysisRecommendation",
    "EvolutionAnalysisStatus",
    "EvolutionNeed",
    "EvolutionNeedKind",
    "EvolutionNeedStatus",
    "EvolutionProposalStatus",
    "EvolutionProposalType",
    "GovernedEvolutionAnalysis",
    "GovernedEvolutionProposal",
]
