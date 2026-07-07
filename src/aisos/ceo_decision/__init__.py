"""Workflow déclaratif de décision CEO (C0.5 — CEO Decision Workflow réaligné).

Phase C0 — Consolidation du socle E1..E8 (E9 reste ferme). C0.5 se limite a la responsabilite :
**decider**. Ce paquet **framework-agnostique** definit une fondation **declarative** de decision
CEO sur des orientations critiques liees aux projets, solutions, equipes IA futures et
recommandations : demande (`CEODecisionRequest`), enregistrement de decision (`CEODecisionRecord`),
statuts (`CEODecisionRequestStatus`), resultats (`CEODecisionOutcome`), perimetres
(`CEODecisionScope`) et references declaratives (`CEODecisionReference` /
`CEODecisionReferenceKind`).

La decision CEO est un **acte humain explicite, tracable et non automatique** : seul un `HumanUser`
de role `CEO` (C0.4) peut decider ; `APPROVED` n'applique rien, `REJECTED` ne supprime rien,
`NEEDS_REVISION` ne modifie rien. C0.5 **n'applique rien**, ne mute rien, ne cree/n'ameliore aucune
solution, ne cree aucune equipe IA, n'ecrit ni audit ni memoire, ne declenche aucun E7 et n'ouvre
pas E9 ; une `AccessDecision.ALLOWED` (C0.4) ne devient **jamais** une decision CEO. C0.5 ne modifie
ni ne remplace **E7.5**, ne rouvre aucun contrat E1..E8, ne modifie ni C0.1/C0.2/C0.3/C0.R/C0.4, ne
cree aucun objet produit actif et n'anticipe pas C0.6/C0.7/C0.8/C0.9. Voir la docstring du module
`workflow`.
"""

from aisos.ceo_decision.workflow import (
    CEODecisionOutcome,
    CEODecisionRecord,
    CEODecisionReference,
    CEODecisionReferenceKind,
    CEODecisionRequest,
    CEODecisionRequestStatus,
    CEODecisionScope,
)

__all__ = [
    "CEODecisionOutcome",
    "CEODecisionRecord",
    "CEODecisionReference",
    "CEODecisionReferenceKind",
    "CEODecisionRequest",
    "CEODecisionRequestStatus",
    "CEODecisionScope",
]
