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
| [`11-decision-classification-and-policies.md`](./11-decision-classification-and-policies.md) | Classification des décisions et politiques pré-approuvées du CEO |
| [`12-concurrency-and-contention.md`](./12-concurrency-and-contention.md) | Traitement de plusieurs demandes simultanées et contention |
| [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md) | Bornes et seuils comportementaux (qui les fixe, valeurs par défaut) |
| [`14-integrity-and-threat-model.md`](./14-integrity-and-threat-model.md) | Intégrité, modèle de menace comportementale et contre-pouvoirs |

## Acteurs (vocabulaire de référence)

- **Utilisateur** : porteur d'un besoin à l'origine d'une demande ; il n'est pas le décideur.
- **CEO** : seule autorité humaine, seul décideur ; prend en charge la demande sous son autorité.
- **Conseil Stratégique Dynamique** : instance IA consultative, activée par le CEO au besoin, composée dynamiquement, dissoute après remise de sa recommandation stratégique (décision 014).
- **Orchestrateur** : coordonne le travail et consolide la recommandation finale opérationnelle ; ne décide pas.
- **Conseils d'Experts** : délibèrent et produisent des recommandations opérationnelles.
- **Départements** / **Agents spécialisés** : produisent le travail dans leur spécialité.

## Référentiel des étapes

Toutes les numérotations d'étapes de ce dossier s'indexent sur les **sept étapes constitutionnelles** (Article XI, voir [`../system/08-decision-flow.md`](../system/08-decision-flow.md), Vue 2) : Analyse → Débat → Documentation → Recommandation → Validation humaine → Exécution → Amélioration.

## Invariants comportementaux

Quel que soit le comportement décrit, les invariants suivants s'appliquent toujours :

- **Une seule autorité humaine** : le CEO. Il est le seul décideur.
- **Les agents recommandent, ils ne décident jamais** : toutes les autres instances sont exclusivement des agents IA, consultatifs.
- **Validation humaine** : aucune décision importante n'est exécutée sans validation du CEO ; la délégation ne va que vers des politiques pré-approuvées par le CEO, jamais vers un autre humain ni vers un agent.
- **Bornes et terminaison** : aucun débat, aucune boucle, aucune attente n'est infini ; toute borne a un responsable et une valeur par défaut ([`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md)).
- **Traçabilité et versioning** : chaque comportement significatif laisse une trace exploitable ; les protocoles comportementaux eux-mêmes sont versionnés, afin qu'une décision passée reste rattachable à la version de protocole sous laquelle elle a été prise.

## Points à arbitrer par le CEO

Certaines questions de long terme dépassent la présente phase et touchent la vision « une seule autorité humaine » : elles sont documentées comme ouvertes (voir [`14-integrity-and-threat-model.md`](./14-integrity-and-threat-model.md)) — notamment l'audit/la calibration des décisions du CEO lui-même, et l'ouverture à des organisations multi-humaines ou inter-organisations. Elles relèvent d'une décision distincte du CEO.

## Portée

- **Ce que couvre cette phase :** le comportement observable du système — séquences, protocoles, règles, conditions, exemples et cas limites.
- **Ce que cette phase ne couvre pas :** le code, les langages, les cadres et toute technologie d'implémentation.
