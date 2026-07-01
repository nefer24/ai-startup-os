# System Architecture

> The conceptual architecture of AI-SOS (Phase 2).

Ce dossier contient l'**architecture conceptuelle complète** d'AI-SOS, produite lors de la **Phase 2** du projet. Il décrit *comment* le système est organisé et *comment* il fonctionne — au niveau des concepts, des rôles, des flux et des règles — afin qu'un développeur ou un agent IA puisse ensuite commencer le développement sans avoir à prendre de décision architecturale majeure.

Cette phase est **exclusivement conceptuelle** : elle ne contient aucun code et ne choisit aucune technologie. Les choix technologiques seront effectués lors de la **Phase 3**, dans le respect du principe de neutralité technologique de la Constitution.

L'ensemble de ces documents est cohérent avec, et subordonné à, la Constitution ([`../00-vision.md`](../00-vision.md)) et les Principes fondamentaux ([`../01-principles.md`](../01-principles.md)).

## Documents

| Document | Objet |
| --- | --- |
| [`00-glossary.md`](./00-glossary.md) | Vocabulaire de référence du dossier |
| [`01-system-overview.md`](./01-system-overview.md) | Vue générale et architecture d'ensemble |
| [`02-orchestrator.md`](./02-orchestrator.md) | L'Orchestrateur : mission, cycle de vie, décisions, fédération |
| [`03-expert-councils.md`](./03-expert-councils.md) | Les Conseils d'Experts : délibération et recommandation |
| [`04-departments.md`](./04-departments.md) | Les Départements et leurs agents |
| [`05-specialized-agents.md`](./05-specialized-agents.md) | Les Agents spécialisés : mission, limites, cycle de vie |
| [`06-memory.md`](./06-memory.md) | L'architecture de la mémoire du système |
| [`07-communication.md`](./07-communication.md) | La communication et la collaboration entre agents |
| [`08-decision-flow.md`](./08-decision-flow.md) | Le cycle de vie complet d'une demande utilisateur |
| [`09-agent-creation.md`](./09-agent-creation.md) | Les règles de création, d'évolution et de retrait d'un agent |
| [`10-system-principles.md`](./10-system-principles.md) | Les propriétés systémiques (robustesse, sécurité, scalabilité…) |
| [`11-executive-board.md`](./11-executive-board.md) | L'Executive Board : rôle, responsabilités, frontières |

## Parcours de lecture recommandé

Pour une première découverte (≈ 60–75 min de lecture attentive) :

1. [`00-glossary.md`](./00-glossary.md) — le vocabulaire (5 min).
2. [`01-system-overview.md`](./01-system-overview.md) — la vue d'ensemble (10 min).
3. [`08-decision-flow.md`](./08-decision-flow.md) — le parcours d'une demande de bout en bout (10 min).
4. [`02-orchestrator.md`](./02-orchestrator.md), [`11-executive-board.md`](./11-executive-board.md), [`03-expert-councils.md`](./03-expert-councils.md) — les instances de coordination et de décision.
5. [`04-departments.md`](./04-departments.md), [`05-specialized-agents.md`](./05-specialized-agents.md) — les acteurs qui produisent le travail.
6. [`06-memory.md`](./06-memory.md), [`07-communication.md`](./07-communication.md), [`09-agent-creation.md`](./09-agent-creation.md) — les mécanismes transverses.
7. [`10-system-principles.md`](./10-system-principles.md) — les propriétés systémiques.

## Conventions

- **Langue :** titre de niveau 1 en anglais, corps du document en français.
- **Terminologie :** les termes canoniques (Orchestrateur, Conseils d'Experts, Départements, Agents spécialisés, Executive Board, spécialité…) sont définis dans le [`00-glossary.md`](./00-glossary.md) et employés de façon uniforme.

## Portée

- **Ce que couvre cette phase :** l'organisation, les rôles, les responsabilités, les flux de décision, la mémoire, la communication et les principes techniques conceptuels.
- **Ce que cette phase ne couvre pas :** le code, les langages, les cadres, les bases de données, l'infrastructure et tout autre choix technologique — réservés à la Phase 3.
