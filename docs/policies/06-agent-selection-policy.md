# Agent Selection Policy

> Cette politique décrit comment est composée l'équipe d'Agents spécialisés et de Conseils d'Experts pertinents pour traiter une demande. Pour un Conseil d'Experts ordinaire, la composition est **proposée et assemblée par l'Orchestrateur** au titre du cadrage : c'est un acte de cadrage, non une décision de fond. Le CEO décide de mobiliser au niveau des priorités et de l'enjeu ; il ne sélectionne pas personnellement chaque agent. Seule la composition du **Conseil Stratégique Dynamique** est entérinée par le CEO. La politique fournit des critères observables et des règles conditionnelles pour composer une équipe juste — ni trop, ni trop peu — tout en préservant la neutralité de composition. Le CEO demeure la seule autorité de décision ; les agents sont consultatifs ; l'Orchestrateur assemble les équipes mais ne fixe jamais les priorités.

## Objectif

Déterminer, pour une demande donnée, quels Agents spécialisés et quels Conseils d'Experts doivent être mobilisés, afin que chaque dimension du problème soit couverte par une expertise adéquate, sans surcharge inutile ni angle mort. Pour un Conseil d'Experts ordinaire, cette composition est **assemblée par l'Orchestrateur** dans le cadre du cadrage ; le CEO décide de la mobilisation au niveau des priorités et n'entérine directement que la composition du **Conseil Stratégique Dynamique**.

Cette politique vise à :

- Traduire un problème en un ensemble de spécialités requises, puis en une équipe concrète.
- Garantir une couverture complète des dimensions du problème sans mobiliser d'expertises superflues.
- Préserver la neutralité de composition : la sélection ne doit pas orienter la conclusion à l'avance.
- Respecter le principe de non-débordement : un agent n'agit pas hors de sa spécialité.

L'assemblage produit une composition d'équipe proposée par l'Orchestrateur. La décision de mobiliser cette équipe, au niveau des priorités et de l'enjeu, appartient au CEO, seule autorité ; l'entérinement direct par le CEO d'une composition nominative ne s'impose que pour le Conseil Stratégique Dynamique ([`05-strategic-council-policy.md`](./05-strategic-council-policy.md)).

## Critères

La sélection s'appuie sur des critères observables :

- **Dimensions du problème → spécialités requises.** Décomposer la demande en ses dimensions (produit, technique, sécurité, juridique, financier, etc.) et associer à chacune la ou les spécialités nécessaires.
- **Couverture complète des dimensions.** Chaque dimension identifiée doit être prise en charge par au moins une spécialité. Une dimension sans spécialité assignée est un angle mort observable.
- **Disponibilité et contention.** Vérifier que les agents envisagés sont disponibles et non saturés. Les situations de contention se règlent selon [`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md).
- **Pertinence vs exhaustivité.** Chercher l'équipe minimale suffisante : ni trop d'agents (dilution, coût), ni trop peu (couverture incomplète).
- **Neutralité de composition.** Éviter un panel orienté dont la composition prédétermine la réponse ; la sélection reste indépendante du résultat attendu, conformément au modèle d'intégrité et de menace ([`../behavior/14-integrity-and-threat-model.md`](../behavior/14-integrity-and-threat-model.md)).
- **Quorum d'expertises indispensables.** Certaines décisions exigent un ensemble minimal d'expertises présentes ; en leur absence, la composition est incomplète.

## Règles

1. **Établir la correspondance problème → spécialités → Départements/Conseils.** Partir des dimensions du problème, en déduire les spécialités, puis rattacher celles-ci aux Départements et Conseils compétents ([`../system/04-departments.md`](../system/04-departments.md)).
2. **Composer une équipe minimale suffisante.** Retenir le plus petit ensemble d'agents couvrant toutes les dimensions. Chaque agent ajouté doit répondre à une dimension non encore couverte.
3. **Garantir la neutralité de composition.** La sélection ne doit pas être orientée : on ne choisit pas les agents en fonction de la conclusion souhaitée, mais des dimensions à couvrir. Un panel dont la composition penche vers une réponse est un biais de composition observable à corriger avant délibération, conformément au modèle d'intégrité et de menace ([`../behavior/14-integrity-and-threat-model.md`](../behavior/14-integrity-and-threat-model.md)).
4. **Respecter le non-débordement.** N'assigner à chaque agent que des dimensions relevant de sa spécialité ; ne pas étirer une spécialité pour combler une lacune.
5. **Si une spécialité manque → proposer la création d'un agent.** Lorsqu'aucun agent existant ne couvre une dimension, proposer la création d'une spécialité selon les [`07-agent-creation-rules` de la Phase 3](../behavior/07-agent-creation-rules.md), sans geler la session : le travail se poursuit sur les dimensions couvertes.
6. **Inclure un avocat du diable pour les classes structurante et critique.** Pour toute décision de classe structurante ou critique ([`07-decision-classification-policy.md`](./07-decision-classification-policy.md)), intégrer obligatoirement un rôle contradicteur afin de tester la robustesse de la recommandation et de renforcer la neutralité de composition.
7. **L'Orchestrateur assemble, le CEO décide.** L'Orchestrateur propose et assemble la composition d'un Conseil d'Experts ordinaire et coordonne, mais ne fixe pas les priorités ni ne tranche : le CEO décide de la mobilisation au niveau des priorités. Seule la composition du Conseil Stratégique Dynamique est entérinée directement par le CEO.
8. **Scinder au-delà de la taille de conseil définie.** Lorsqu'un conseil dépasse la taille maximale fixée par [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) (défaut indicatif : 7 membres), former des sous-comités thématiques plutôt que de laisser le conseil grossir.

## Exemples

**Exemple 1 — Problème produit.** Une demande de refonte d'un parcours d'inscription présente des dimensions produit (expérience utilisateur, valeur), technique (faisabilité) et données (mesure d'adoption). Composition minimale suffisante assemblée par l'Orchestrateur : un agent Produit (pilote de la dimension centrale), un agent Ingénierie (faisabilité), un agent Données/Analytics (mesure). Aucune dimension juridique majeure n'étant identifiée, on n'ajoute pas de spécialité juridique. Pour une décision structurante, un avocat du diable challenge la valeur supposée du nouveau parcours.

**Exemple 2 — Problème sécurité.** Une demande d'évaluation d'un incident potentiel présente des dimensions sécurité (analyse de la menace), technique (surface exposée), juridique (obligations de notification) et communication (parties prenantes). Composition : un agent Sécurité (pilote), un agent Ingénierie (surface technique), un agent Juridique (obligations), un agent Communication. Le quorum d'expertises indispensables (sécurité + juridique) doit être présent avant toute recommandation ; à défaut, la composition est déclarée incomplète.

## Cas limites

- **Deux spécialités concurrentes pour un même rôle.** Lorsque deux spécialités revendiquent la même dimension, retenir celle dont le périmètre correspond le mieux à la dimension observée, en respectant le non-débordement. En cas d'ambiguïté persistante, les deux sont incluses avec des périmètres explicitement délimités, et l'arbitrage remonte au CEO.
- **Spécialité indispensable indisponible.** Si une expertise du quorum est saturée ou absente, appliquer la gestion de contention ([`../behavior/12-concurrency-and-contention.md`](../behavior/12-concurrency-and-contention.md)) ou proposer la création d'un agent ([`07-agent-creation-rules`](../behavior/07-agent-creation-rules.md)) sans geler la session. La décision structurante attend que le quorum soit reconstitué.
- **Sur-composition.** Si un conseil dépasse la taille maximale définie ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md), défaut indicatif : 7 membres) et devient trop grand pour délibérer efficacement, le scinder en sous-comités thématiques, chacun couvrant un sous-ensemble cohérent de dimensions, puis consolider leurs conclusions. Cela préserve la pertinence sans sacrifier la couverture.

## Questions ouvertes

- Comment mesurer objectivement la « suffisance » d'une équipe minimale au-delà de la couverture des dimensions ?
- Comment détecter automatiquement un biais de composition avant délibération, au-delà de la règle de neutralité et de l'avocat du diable ?

---

Renvois : [`01-complexity-policy.md`](./01-complexity-policy.md) pour l'évaluation de la complexité en amont ; [`05-strategic-council-policy.md`](./05-strategic-council-policy.md) pour la constitution des conseils stratégiques ; [`07-decision-classification-policy.md`](./07-decision-classification-policy.md) pour les classes de décision ; [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) pour les seuils de taille et de scission ; [`../behavior/14-integrity-and-threat-model.md`](../behavior/14-integrity-and-threat-model.md) pour le modèle d'intégrité et de menace.
