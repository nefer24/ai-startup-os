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

E7.7 pose la septieme brique : **tracer** — representer la **tracabilite gouvernee** du cycle
d'evolution et sa memorisation contextuelle (`GovernedEvolutionTrace`, `EvolutionTraceStatus`),
reliant besoin (E7.1), proposition (E7.2), analyse (E7.3), plan (E7.4), decision (E7.5) et
application (E7.6). C'est un **enregistrement de liaison**, immuable : l'audit reste **source de
verite**, la memoire ne fait que **contextualiser** — sans decider, appliquer, muter, reecrire
l'histoire ni remplacer l'audit.

E8.1 ouvre l'evolution continue gouvernee : **lire** — representer une **lecture gouvernee de
plusieurs traces E7 passees** (`GovernedEvolutionHistory`, `EvolutionHistoryStatus`), toutes au
statut TRACED et dans la meme organisation. C'est un **recueil immuable** de traces, dans l'ordre
fourni : sans analyser, regrouper, comparer, identifier de pattern, recommander, decider ni modifier
les traces. *Evolution continue = lecture gouvernee de cycles passes pour preparer de nouveaux
cycles soumis au CEO.*

E8.2 poursuit l'evolution continue gouvernee : **regrouper** — representer un **regroupement
gouverne de cycles** issus d'un historique (`GovernedEvolutionCycleGroup`,
`EvolutionCycleGroupStatus`) sous une **cle descriptive**, a partir d'un historique E8.1 au statut
READ. C'est un **recueil etiquette** immuable de traces (toutes issues de l'historique, TRACED, meme
organisation), conservees telles quelles : sans analyser, comparer, identifier de pattern,
recommander, decider, fusionner ni reordonner.

E8.3 poursuit l'evolution continue gouvernee : **identifier** — representer un **pattern recurrent**
dans un groupe (`GovernedEvolutionPattern`, `EvolutionPatternType`, `EvolutionPatternConfidence`,
`EvolutionPatternStatus`) a partir d'un groupe E8.2 au statut GROUPED. C'est un **constat
descriptif** immuable d'une recurrence (type et confiance descriptifs, traces de soutien du
groupe) : sans recommander, decider, autoriser, creer un besoin/proposition, appliquer ni modifier.
`HIGH` ne vaut jamais "autorise".
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
from aisos.evolution.grouping import (
    EvolutionCycleGroupStatus,
    GovernedEvolutionCycleGroup,
)
from aisos.evolution.history import EvolutionHistoryStatus, GovernedEvolutionHistory
from aisos.evolution.need import EvolutionNeed, EvolutionNeedKind, EvolutionNeedStatus
from aisos.evolution.pattern import (
    EvolutionPatternConfidence,
    EvolutionPatternStatus,
    EvolutionPatternType,
    GovernedEvolutionPattern,
)
from aisos.evolution.plan import EvolutionPlanStatus, GovernedEvolutionPlan
from aisos.evolution.proposal import (
    EvolutionProposalStatus,
    EvolutionProposalType,
    GovernedEvolutionProposal,
)
from aisos.evolution.trace import EvolutionTraceStatus, GovernedEvolutionTrace

__all__ = [
    "EvolutionAnalysisRecommendation",
    "EvolutionAnalysisStatus",
    "EvolutionApplicationStatus",
    "EvolutionCycleGroupStatus",
    "EvolutionDecision",
    "EvolutionDecisionStatus",
    "EvolutionHistoryStatus",
    "EvolutionNeed",
    "EvolutionNeedKind",
    "EvolutionNeedStatus",
    "EvolutionPatternConfidence",
    "EvolutionPatternStatus",
    "EvolutionPatternType",
    "EvolutionPlanStatus",
    "EvolutionProposalStatus",
    "EvolutionProposalType",
    "EvolutionTraceStatus",
    "GovernedEvolutionAnalysis",
    "GovernedEvolutionApplication",
    "GovernedEvolutionCycleGroup",
    "GovernedEvolutionDecision",
    "GovernedEvolutionHistory",
    "GovernedEvolutionPattern",
    "GovernedEvolutionPlan",
    "GovernedEvolutionProposal",
    "GovernedEvolutionTrace",
]
