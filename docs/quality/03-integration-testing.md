# Integration Testing

> Tests d'intégration entre composants d'AI-SOS : vérifier que l'API, la persistence, l'audit, le moteur de politiques et l'orchestration collaborent réellement, sur base Postgres jetable et LLM bouchonné, sans jamais rompre un invariant de gouvernance.

Ce document définit l'**architecture de validation par intégration** de la Phase 12. Il ne produit aucun code et n'introduit aucun choix technologique : il opérationnalise la couche intermédiaire de la [`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md) dans le strict respect de la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) (décision 016) et des Phases 5–11. Les décisions techniques mobilisées — DT-02 (LangGraph : `StateGraph`, interrupts, checkpointer), DT-04 (FastAPI), DT-05 (Postgres jetable pour les tests), DT-06 (audit append-only à chaînage de hachés) et le faux `LLMProvider` déterministe (Phase 6) — restent des **propositions à entériner par le CEO** (futures décisions 017+). Invariant permanent : le **CEO est le seul décideur** ; ces tests ne font que **prouver** la conformité, ils ne l'établissent pas.

Là où [`./02-unit-testing.md`](./02-unit-testing.md) isole chaque composant, l'intégration valide leurs **coutures** ; là où [`./04-runtime-validation.md`](./04-runtime-validation.md) prouve les propriétés du graphe et [`./05-governance-validation.md`](./05-governance-validation.md) consolide les preuves d'invariants, le présent document garantit que les collaborations réelles ([`../components/10-component-interactions.md`](../components/10-component-interactions.md)) tiennent de bout en bout.

Le principe directeur reste celui de la stratégie de tests : **la conformité se démontre, elle ne se déclare pas**. Un invariant de gouvernance qui ne serait pas prouvé par au moins un test d'intégration est traité comme un **défaut**, non comme une simple lacune de couverture. L'intégration est la couche où l'on cesse de faire confiance aux contrats isolés pour vérifier que le système, assemblé, refuse réellement les chemins interdits.

### Pile de test et hermétisme

Toute suite d'intégration s'exécute sur une pile jetable et reproductible, sans dépendance à un service tiers réel :

| Élément | Choix | Rôle |
| --- | --- | --- |
| Base de données | PostgreSQL 16 jetable (DT-05), montée à neuf par Alembic | Persistence + checkpointer + event store réels |
| LLM | Faux `LLMProvider` déterministe (Phase 6) | Réponses scénarisées, **aucun** appel réseau |
| Horloge | Horloge injectable | Échéances (report, relance) testées sans attendre le temps réel |
| Données | Seeds fixes + factories déterministes | Échecs reproductibles, isolation entre tests |
| API | FastAPI (DT-04) montée en test | Endpoints authentifiés, RBAC minimal (DT-07) exercés |

Règle d'or : un test qui atteindrait le réseau réel est un **défaut de conception du test**, pas une fatalité. Chaque test part d'une base migrée à neuf ou d'une transaction annulée en fin de test ; aucun état ne fuit d'un test à l'autre.

## Objectifs

- **Valider les interactions réelles** entre API (DT-04), persistence et checkpointer (DT-05), audit immuable (DT-06), moteur de politiques et orchestration ([`../components/10-component-interactions.md`](../components/10-component-interactions.md)), sur une base **Postgres jetable** avec migrations Alembic appliquées à neuf et faux `LLMProvider` déterministe (aucun appel réseau).
- **Prouver qu'aucune écriture ne contourne l'event store** : toute mutation de gouvernance passe par un événement append-only persisté à l'audit dans la même transaction que l'écriture métier ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)).
- **Vérifier la séquence des événements** attendue par le catalogue ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)) sur des parcours complets, y compris l'ordre et le chaînage de hachés.
- **Valider l'isolation des cheminements** sous concurrence : deux demandes en parallèle progressent sans état partagé et sans interférence de checkpoints ([`../components/07-workflow-engine.md`](../components/07-workflow-engine.md)).
- **Prouver les invariants de gouvernance au niveau intégration** : aucun chemin vers l'exécution sans validation CEO ou politique référencée ; quality gate avant présentation ; refus des identités non-CEO sur les endpoints de validation.
- **Rester hermétique et déterministe** : base jetable, horloge injectable, seeds fixes ; aucun test ne dépend d'un service tiers réel ([`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md)).
- **Exercer les modes dégradés** documentés ([`../components/10-component-interactions.md`](../components/10-component-interactions.md)) : audit indisponible (aucune exécution non auditée), LLM indisponible (attente bornée puis escalade), CEO indisponible (seules les politiques actives avancent) — sans jamais ouvrir de chemin d'exécution de substitution.

## Scénarios

Chaque scénario s'exécute de bout en bout sur la pile réelle jetable. Le tableau relie le scénario aux composants impliqués et au résultat attendu observable (événements + état persisté). Les scénarios S1 à S7 sont des **scénarios de gouvernance** : leur passage à 100 % est bloquant. S8 et S9 valident la robustesse d'exécution (concurrence, reprise).

| # | Scénario | Composants impliqués | Attendu observable |
| --- | --- | --- | --- |
| S1 | Parcours nominal : intake → évaluation → classification → interrupt CEO → resolve (les 4 issues) → exécution → audit | API (09) · Policy Engine (04) · Workflow Engine (07) · Human Interaction (09) · Audit (08) | Pour **Approuve/Ajuste** : `execution.started` seulement après `decision.resolved` (`validated_by = ceo`). **Reporte** : `decision.pending` + `deadline`, aucune exécution. **Rejette** : `request.rejected`, aucune exécution. |
| S2 | Délégation par politique pré-approuvée (classe courante éligible) | Policy Engine (04) · Workflow Engine (07) · Audit (08) | `policy.evaluated` (`eligible = true`) → `policy.applied` (`policy_id` + `policy_version` + `caps_consumed`) → exécution, **sans** `interrupt()`. Contournement journalisé, décision re-classifiable. |
| S3 | Refus de délégation : classe structurante/critique | Policy Engine (04) · Human Interaction (09) | `policy.evaluated` (`eligible = false`) → `interrupt()` CEO **obligatoire** ; aucune arête de politique empruntée. |
| S4 | Escalade : borne atteinte / non-convergence | Agent Runtime (02) · Orchestrator (01) · Human Interaction (09) | `escalation.raised` (options à parité) → `interrupt()` CEO ; jamais de décision d'agent ni de vote couperet. |
| S5 | Refus d'identité non-CEO sur `resolve` | API (DT-08) · Audit (08) | `403` + tentative journalisée comme anomalie ; interrupt maintenu ; état inchangé. |
| S6 | Audit append-only et chaînage vérifiés de bout en bout | Persistence (DT-05) · Audit (08) | Toute tentative d'`UPDATE`/`DELETE` sur l'event store refusée ; job de vérification confirme `hash = H(prev_hash ‖ payload)` sur toute la chaîne ; rupture détectée. |
| S7 | Quality gate bloquant avant présentation | Policy Engine (04) · Human Interaction (09) | Recommandation sous le seuil → `quality_gate.failed` → renvoi en délibération ; **aucune** entrée dans l'inbox CEO. |
| S8 | Contention / concurrence : deux demandes en parallèle | Workflow Engine (07) · persistence (DT-05) | Deux threads isolés, aucun état partagé ; chaînage d'audit cohérent par `thread_id` ; aucune interférence de checkpoints ([`../components/07-workflow-engine.md`](../components/07-workflow-engine.md)). |
| S9 | Reprise après crash mid-graph | Workflow Engine (07) · checkpointer (DT-05) | Thread orphelin repris au dernier checkpoint ; aucune étape engageante rejouée en aveugle ; audit sans trou. |
| S10 | Mode dégradé : audit indisponible | Audit (08) · Workflow Engine (07) | Event store non scellable → le flux se bloque de façon conservatrice et remonte au CEO ; **aucune exécution non auditée** ([`../components/10-component-interactions.md`](../components/10-component-interactions.md)). |
| S11 | Mode dégradé : CEO indisponible | Human Interaction (09) · Policy Engine (04) | File priorisée ; seules les décisions courantes couvertes par une politique active avancent ; structurantes/critiques attendent le CEO, bornées et notifiées. |

Extrait illustratif (assertion d'ordre d'événements, non exécutable) :

```text
assert ordre(request.received, evaluation.done, quality_gate.passed,
             decision.pending, decision.resolved, execution.started)
assert absent(execution.started) tant que decision.resolved absent
```

Le point vérifié n'est pas seulement que les bons événements existent, mais qu'ils apparaissent **dans le bon ordre** et **avec la bonne corrélation** : `execution.started` ne peut jamais précéder un `decision.resolved` correspondant (S1), et un `policy.applied` porte toujours `policy_id` + `policy_version` (S2). L'ordre est une propriété de gouvernance, pas un détail de journalisation.

Correspondance indicative entre scénario et événements clés attendus (référence : [`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)) :

| Scénario | Événements clés attendus (dans l'ordre) |
| --- | --- |
| S1 (Approuve) | `request.received` → `evaluation.done` → `quality_gate.passed` → `decision.pending` → `decision.resolved` (`ceo`) → `execution.started` |
| S2 (délégation) | `evaluation.done` → `policy.evaluated` (`eligible`) → `policy.applied` → `execution.started` (sans `decision.pending`) |
| S3 (refus délégation) | `policy.evaluated` (`eligible = false`) → `decision.pending` → `decision.resolved` (`ceo`) |
| S4 (escalade) | `escalation.raised` → `decision.pending` → `decision.resolved` (`ceo`) |
| S7 (gate) | `quality_gate.failed` → retour délibération ; **aucun** `decision.pending` |
| S6 (audit) | chaque événement suivi de son `audit.recorded` chaîné |

### Frontière avec les autres couches

Les scénarios ci-dessus se limitent aux **collaborations réelles** entre composants. La preuve exhaustive des chemins du graphe relève de [`./04-runtime-validation.md`](./04-runtime-validation.md) ; la classification et le quality gate en isolation relèvent des tests unitaires ([`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md)). L'intégration confirme que ces briques, une fois câblées, produisent le comportement attendu de bout en bout.

En résumé, la valeur propre de cette couche est de faire échouer les défauts qui n'apparaissent **qu'à l'assemblage** : un événement omis dans une transaction, une transaction d'audit non atomique avec l'écriture métier, une arête de politique empruntée à tort, un checkpoint mal corrélé sous concurrence. Aucun test unitaire ne les voit ; l'intégration les rend visibles et opposables.

## Critères de réussite

- **Chaque scénario de bout en bout passe** sur la pile jetable, migrations appliquées, LLM bouchonné.
- **Aucune écriture ne contourne l'event store** : toute mutation de gouvernance est adossée à un événement persisté à l'audit dans la même transaction ; un scénario qui muterait sans trace est un échec.
- **Les événements sont émis dans l'ordre attendu** ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)) : séquence, corrélation (`request_id`/`thread_id`) et chaînage de hachés vérifiés.
- **Les invariants de gouvernance testables en intégration sont prouvés** : pas d'exécution sans validation CEO ou politique référencée (S1–S3), quality gate bloquant (S7), refus non-CEO (S5), audit immuable (S6).
- **Les modes dégradés restent conservateurs** : audit indisponible bloque toute exécution (S10), CEO indisponible ne laisse avancer que les politiques actives (S11) ; aucun chemin de substitution n'est ouvert.
- **Hermétisme confirmé** : aucun accès réseau réel ; un test qui atteindrait un service tiers est un défaut de conception du test.
- **Isolation vérifiée** : sous concurrence (S8), aucun thread n'observe l'état d'un autre ; le chaînage d'audit reste cohérent par `thread_id`.
- **Comportement conservateur sous panne** : dans tout mode dégradé (S10, S11), le système bloque ou met en file, il n'ouvre jamais un chemin d'exécution de substitution ni ne substitue une autorité au CEO.

Un scénario est considéré **réussi** uniquement si l'état final persisté **et** la séquence d'événements correspondent à l'attendu : une exécution qui produirait le bon état par un chemin d'événements incorrect (par exemple sans `quality_gate.passed`) est un échec, même si l'état terminal paraît conforme.

### Invariants prouvés au niveau intégration

| Invariant | Scénario qui le prouve | Preuve observable |
| --- | --- | --- |
| Aucun chemin vers l'exécution sans validation CEO ou politique référencée | S1, S2, S3 | `execution.started` toujours précédé de `decision.resolved` (ceo) ou `policy.applied` |
| Structurante/critique jamais déléguée | S3 | `policy.evaluated` (`eligible = false`) → interrupt CEO forcé |
| Quality gate avant présentation | S7 | `quality_gate.failed` → renvoi ; aucune entrée inbox |
| CEO seul décideur (identité) | S5 | `403` + anomalie journalisée sur `resolve` non-CEO |
| Audit immuable et chaîné | S6 | `UPDATE`/`DELETE` refusés ; `hash = H(prev_hash ‖ payload)` vérifié |
| Reprise fidèle | S9 | reprise au dernier checkpoint sans rejeu engageant |
| Aucune exécution non auditée | S10 | flux bloqué et remonté au CEO si audit indisponible |

Cette table est le point de raccordement vers [`./05-governance-validation.md`](./05-governance-validation.md), qui consolide l'ensemble des preuves d'invariants toutes couches confondues.

## Métriques

Les métriques ci-dessous sont collectées à chaque exécution de la suite `integration` en CI. Elles servent l'observabilité de la qualité, pas la décision de fusion — celle-ci reste au CEO. Le **taux de flakiness** fait l'objet d'une attention particulière : sur une suite d'intégration à base réelle, la non-détermination provient presque toujours d'un défaut de conception (ordonnancement non maîtrisé, temps réel utilisé au lieu de l'horloge injectable, seed non fixé). Un scénario de gouvernance instable n'est jamais accepté tel quel : il est corrigé ou, sous décision explicite du CEO, mis en quarantaine tracée.

| Métrique | Définition | Sens |
| --- | --- | --- |
| Nombre de scénarios | Total de scénarios d'intégration exécutés (dont scénarios de gouvernance) | Étendue de la couverture des coutures |
| Couverture d'intégration | Part des chemins inter-composants ([`../components/10-component-interactions.md`](../components/10-component-interactions.md)) exercés par au moins un scénario | Complétude des collaborations validées |
| Temps de suite | Durée d'exécution de la suite `integration` en CI | Coût et tenue du budget de feedback |
| Taux de flakiness | Part d'exécutions non déterministes (échec/succès sans changement de code) | Fiabilité ; un test de gouvernance instable est traité conservativement |
| Couverture d'événements | Part des types du catalogue ([`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md)) émis et vérifiés | Fidélité de la trace de bout en bout |
| Couverture des modes dégradés | Part des modes dégradés ([`../components/10-component-interactions.md`](../components/10-component-interactions.md)) exercés par un scénario | Robustesse conservatrice sous panne |
| Isolation sous concurrence | Nombre de threads parallèles vérifiés sans interférence | Fidélité de l'isolation des cheminements |

## Seuils de validation

> Seuils **indicatifs**, cohérents avec la [`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md), à entériner par le CEO comme toute borne ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).

| Cible | Seuil | Statut |
| --- | --- | --- |
| Scénarios de gouvernance de bout en bout passants (S1–S7) | **100 %** | Bloquant |
| Taux de flakiness | **≈ 0** ; tout test de gouvernance instable bloque par défaut (position conservatrice) | Bloquant |
| CI | Suite `integration` exécutée à chaque PR vers `develop` | **Bloquante** ([`../engineering/06-ci-cd-strategy.md`](../engineering/06-ci-cd-strategy.md)) |
| Couverture d'intégration | Cible indicative, cohérente avec le ≥ 85 % global | Indicatif |
| Audit append-only + chaînage | Vérifiés sur 100 % des scénarios écrivant à l'audit | Bloquant |
| Modes dégradés conservateurs (S10, S11) | Comportement conservateur vérifié ; aucune exécution de substitution | Bloquant |
| Couverture d'événements du catalogue | Cible indicative ; tout événement de gouvernance émis dans un scénario est vérifié | Indicatif |

La CI **vérifie** ; seul le CEO **autorise** la fusion. Un test de gouvernance rouge bloque au même titre qu'un test fonctionnel rouge ([`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md)).

Distinction importante entre seuils **bloquants** et **indicatifs** : les seuils bloquants (scénarios de gouvernance, flakiness, audit immuable) sont des conditions de non-régression que la CI applique sans appréciation ; les seuils indicatifs (couverture d'intégration) éclairent la revue mais restent à calibrer par le CEO, comme toute borne ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)). Aucun seuil ne se substitue à la preuve : un périmètre couvert à 100 % dont aucun scénario ne prouve un invariant reste défaillant.

Les scénarios de non-régression des invariants (S1–S7, S10–S11) sont ré-exécutés à chaque PR : un invariant qui cesse d'être prouvé par l'intégration fait **échouer la CI**, indépendamment de la couverture atteinte. C'est la traduction en tests d'intégration du principe « chaque invariant est adossé à au moins un test qui le prouve » ([`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md)).

## Questions ouvertes (CEO)

1. **pgvector dans la base d'intégration** : la base jetable monte-t-elle pgvector dès le MVP, ou une base relationnelle stricte suffit-elle pour la suite d'intégration (question ouverte du plan MVP) ?
2. **Périmètre des scénarios figés** : lesquels des scénarios S1–S9 deviennent des références opposables au MVP, et lesquels attendent l'Horizon 2 ([`../behavior/10-end-to-end-scenarios.md`](../behavior/10-end-to-end-scenarios.md)) ?
3. **Politique de flakiness** : un scénario de gouvernance instable doit-il bloquer la CI par défaut (position retenue) ou être mis en quarantaine sous décision explicite ?
4. **Base jetable en CI** : Testcontainers ou service Postgres géré par la CI — quel mode le CEO privilégie-t-il pour l'hermétisme et le coût ([`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md)) ?
5. **Granularité de vérification d'audit** : la chaîne de hachés est-elle vérifiée intégralement à chaque scénario, ou par échantillonnage borné en dehors des scénarios S6 dédiés ?
6. **Budget de temps de suite** : quelle durée maximale d'exécution le CEO fixe-t-il pour la suite `integration` en CI, au-delà de laquelle une optimisation ou un découpage devient obligatoire ?
7. **Modes dégradés au MVP** : lesquels des modes dégradés (S10 audit, S11 CEO, indisponibilité LLM) sont exigés dès le MVP, et lesquels relèvent d'un jalon ultérieur ([`../components/10-component-interactions.md`](../components/10-component-interactions.md)) ?
8. **Entérinement des DT** : ces tests supposent DT-02/DT-04/DT-05/DT-06 et le faux `LLMProvider` ; ils ne deviennent normatifs qu'après décision du CEO (futures décisions 017+).
