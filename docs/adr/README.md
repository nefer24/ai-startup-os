# Architecture Decision Records (ADR) — AI-SOS

Ce répertoire consigne les **décisions d'architecture officielles** d'AI-SOS. Un ADR fige une
décision structurante, son contexte, ses alternatives et ses conséquences. Une fois **acceptée**,
une décision fait autorité ; elle ne peut être révisée que par un nouvel ADR qui la **remplace**.

> **Autorité.** Conformément à la Constitution AI-SOS, le CEO est le seul décideur. Un ADR au
> statut `Proposé` est une **recommandation du comité d'architecture** ; il ne devient `Accepté`
> qu'après **ratification explicite du CEO**. Cette ratification est l'objet de la porte M0 de la
> roadmap de consolidation.

## Convention

- Fichier : `ADR-NNNN-titre-court.md` (numérotation continue, jamais réutilisée).
- Statut : `Proposé` · `Accepté` · `Remplacé par ADR-XXXX` · `Rejeté` · `Déprécié`.
- Format : Contexte → Décision → Conséquences → Alternatives écartées → Suivi.

## Origine des décisions techniques (DT)

Les propositions techniques historiques (« DT-01 à DT-08 ») ont été formulées dans le corpus
documentaire (Phases 5–12) mais **jamais ratifiées formellement**. La mission de consolidation
les transforme en ADR pour lever cette dette de gouvernance. Les deux revues stratégiques ont en
outre fait émerger deux décisions nouvelles, **DT-09** et **DT-10**, rédigées ici en priorité.

## Index

| ADR | Titre | Origine | Statut |
| --- | --- | --- | --- |
| [ADR-0009](ADR-0009-gouvernance-economique.md) | Gouvernance économique (budgets, coûts, récursion, timeouts, quotas) | DT-09 (Revue n°2) | **Accepted** (ratifié M0-001, 2026-07-02) |
| [ADR-0010](ADR-0010-determinisme-interactions-llm.md) | Déterminisme des interactions avec les LLM (hash, versionnement, replay, cache) | DT-10 (Revue n°2) | **Accepted** (ratifié M0-002, 2026-07-03) |
| [ADR-0011](ADR-0011-audit-source-unique.md) | Audit : source unique de vérité (fin du double-write, dette D1) | Revue n°2 (D1) | **Proposé** (implémenté ; M0-003 recommandée) |
| [ADR-BACKLOG](ADR-BACKLOG.md) | ADR proposés à instruire (ratification DT-01→08 + 5 décisions issues des revues) | Revues n°1 & n°2 | Backlog priorisé |

## Lien avec le dossier de consolidation

Les ADR sont les **décisions** ; le [dossier de consolidation](../consolidation/00-DOSSIER-CONSOLIDATION.md)
en est le **contexte** (dette technique, registre des risques, roadmap, plan de Vertical Slice,
cadre de mesure de la valeur). Les deux se lisent ensemble.
