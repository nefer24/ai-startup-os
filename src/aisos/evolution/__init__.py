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

E7.4 pose la quatrieme brique : **planifier** — representer un **plan d'evolution gouverne**
(`GovernedEvolutionPlan`, `EvolutionPlanStatus`) a partir d'une analyse produite (E7.3) : la
description gouvernee des etapes qu'il faudrait suivre SI le CEO approuve — une preparation
immuable, sans aucun pouvoir de decision, d'approbation, d'application ni d'execution.

E7.5 pose la cinquieme brique : **decider** — representer l'**acte decisionnel reserve au CEO**
(`GovernedEvolutionDecision`, `EvolutionDecision`, `EvolutionDecisionStatus`) sur un plan prepare
(E7.4). C'est le seul endroit ou une decision CEO apparait ; elle reste un **verdict** (approuve /
refuse / reporte / demande une revision) **sans effet operationnel** : meme APPROVE n'applique
rien.

E7.6 pose la sixieme brique : **appliquer** — representer l'**application gouvernee** d'une
evolution **approuvee** (`GovernedEvolutionApplication`, `EvolutionApplicationStatus`) selon le plan
valide (E7.4), sur decision APPROVE au statut DECIDED (E7.5). C'est la premiere etape ou l'on parle
d'application, mais elle reste **declarative et bornee** : elle **constate** la conformite au plan —
sans decision nouvelle, sans execution runtime, sans mutation libre ni reouverture des contrats
figes.
"""

from __future__ import annotations

from aisos.evolution.analysis import (
    EvolutionAnalysisRecommendation,
    EvolutionAnalysisStatus,
    GovernedEvolutionAnalysis,
)
from aisos.evolution.application import (
    EvolutionApplicationStatus,
    GovernedEvolutionApplication,
)
from aisos.evolution.decision import (
    EvolutionDecision,
    EvolutionDecisionStatus,
    GovernedEvolutionDecision,
)
from aisos.evolution.need import EvolutionNeed, EvolutionNeedKind, EvolutionNeedStatus
from aisos.evolution.plan import EvolutionPlanStatus, GovernedEvolutionPlan
from aisos.evolution.proposal import (
    EvolutionProposalStatus,
    EvolutionProposalType,
    GovernedEvolutionProposal,
)

__all__ = [
    "EvolutionAnalysisRecommendation",
    "EvolutionAnalysisStatus",
    "EvolutionApplicationStatus",
    "EvolutionDecision",
    "EvolutionDecisionStatus",
    "EvolutionNeed",
    "EvolutionNeedKind",
    "EvolutionNeedStatus",
    "EvolutionPlanStatus",
    "EvolutionProposalStatus",
    "EvolutionProposalType",
    "GovernedEvolutionAnalysis",
    "GovernedEvolutionApplication",
    "GovernedEvolutionDecision",
    "GovernedEvolutionPlan",
    "GovernedEvolutionProposal",
]
