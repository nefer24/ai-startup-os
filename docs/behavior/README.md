# Behavioral Specification

> The behavioral specification of AI-SOS (Phase 3).

Ce dossier contient la **spécification comportementale** d'AI-SOS, produite lors de la **Phase 3**. Là où la Phase 2 ([`../system/`](../system/)) décrit *comment le système est organisé* (rôles, instances, flux conceptuels), la Phase 3 décrit *comment le système se comporte réellement* lorsqu'il reçoit une demande : séquences, protocoles, règles, conditions, exemples et cas limites.

L'objectif est qu'à la fin de cette phase, un développeur ou un agent IA puisse **implémenter AI-SOS sans avoir à inventer son fonctionnement**. Cette phase reste **exclusivement comportementale** : elle ne contient aucun code et ne choisit aucune technologie (réservés à une phase ultérieure).

Ces documents sont cohérents avec, et subordonnés à, la Constitution ([`../00-vision.md`](../00-vision.md)), les Principes fondamentaux ([`../01-principles.md`](../01-principles.md)), les décisions d'architecture ([`../../DECISIONS.md`](../../DECISIONS.md)) et l'architecture conceptuelle de la Phase 2 ([`../system/`](../system/)).

## Documents

| Document | Objet |
| --- | --- |
| [`01-request-lifecycle.md`](./01-request-lifecycle.md) | Cycle de vie complet d'une demande utilisateur |
| [`02-strategic-council-activation.md`](./02-strategic-council-activation.md) | Activation, composition et dissolution du Conseil Stratégique Dynamique |
| [`03-orchestrator-workflow.md`](./03-orchestrator-workflow.md) | Workflow complet de l'Orchestrateur |
| [`04-debate-protocol.md`](./04-debate-protocol.md) | Protocole de débat des Conseils d'Experts |
| [`05-decision-protocol.md`](./05-decision-protocol.md) | Présentation des recommandations et validation par le CEO |
| [`06-memory-update-rules.md`](./06-memory-update-rules.md) | Règles de mise à jour de la mémoire |
| [`07-agent-creation-rules.md`](./07-agent-creation-rules.md) | Règles de création, d'intégration et de retrait d'un agent |
| [`08-learning-rules.md`](./08-learning-rules.md) | Règles d'apprentissage et prévention de la dérive |
| [`09-error-handling.md`](./09-error-handling.md) | Gestion des erreurs, conflits, blocages et ambiguïtés |
| [`10-end-to-end-scenarios.md`](./10-end-to-end-scenarios.md) | Scénarios complets de bout en bout |

## Invariants comportementaux

Quel que soit le comportement décrit, les invariants suivants s'appliquent toujours :

- **Une seule autorité humaine** : le CEO. Il est le seul décideur.
- **Les agents recommandent, ils ne décident jamais** : toutes les autres instances sont exclusivement des agents IA, consultatifs.
- **Validation humaine** : aucune décision importante n'est exécutée sans validation du CEO ; la délégation ne va que vers des politiques pré-approuvées par le CEO, jamais vers un autre humain ni vers un agent.
- **Traçabilité** : chaque comportement significatif laisse une trace exploitable.

## Portée

- **Ce que couvre cette phase :** le comportement observable du système — séquences, protocoles, règles, conditions, exemples et cas limites.
- **Ce que cette phase ne couvre pas :** le code, les langages, les cadres et toute technologie d'implémentation.
