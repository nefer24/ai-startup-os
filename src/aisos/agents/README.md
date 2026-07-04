# agents

Interfaces d'exécution d'agent : manifest de capacités et exécution sous moindre
privilège. Un agent produit des recommandations ; il ne décide jamais. Aucune
logique métier n'est implémentée ici.

## Contenu

Squelette uniquement :

- Contrat de manifest d'agent (capacités, permissions déclarées).
- Interfaces d'exécution d'agent respectant le principe de moindre privilège.
- Pur service de délibération : reçoit tâche + contexte, produit une
  recommandation. La gouvernance (audit, pause CEO, décisions) et la mémoire
  appartiennent à l'orchestrateur, qui appelle le cerveau via le port de
  délibération et lui injecte le contexte nécessaire.

## Périmètre gelé — contrat de référence (E1 clôturé)

L'étape **E1 (clôture du rez-de-chaussée : cerveau pur gouverné)** est officiellement close.
Le périmètre du cerveau est **gelé** et constitue désormais un **contrat de référence stable** :

- **Pur** : aucun import audit/événements/mémoire dans `agents/*.py` ; aucun symbole de gouvernance
  dans le code (prouvé par `tests/unit/test_brain_purity.py`).
- **Déterministe** et compatible **record/replay** (le rejeu ne rappelle jamais le fournisseur).
- **Gouverné de l'extérieur** : invoqué via `DeliberationPort` ; ne crée aucune pause CEO, n'écrit
  aucun audit, n'émet aucun événement, ne reprend aucune décision.
- **Nourri par contexte** : reçoit `AgentTask.context` préparé par l'orchestration ; ne lit aucune
  mémoire.
- **Ne produit qu'une** `Recommendation` / `CouncilSynthesis` (jamais une décision).
- **Périmètre figé** : deux agents, débat à deux tours — pas de 3ᵉ tour, pas de 3ᵉ agent, pas de
  synthèse enrichie.

**Toute évolution future du cerveau doit respecter ce contrat de référence et ne peut être réalisée
que par une décision explicite du CEO.** Voir [`../../../docs/reports/E1-BRAIN-CLOSURE.md`](../../../docs/reports/E1-BRAIN-CLOSURE.md).

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/components/02-agent-runtime.md`](../../../docs/components/02-agent-runtime.md)

## Invariant de gouvernance

Un agent recommande, il ne décide jamais. Il opère sous moindre privilège, dans
les limites de son manifest et des politiques pré-approuvées ; la CEO demeure
seule autorité humaine et seule décideuse. Toute action est auditée de façon
immuable.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
