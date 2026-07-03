# Backlog ADR — décisions à instruire et ratifier

Ce document liste les ADR **à produire ou à ratifier**, avec leur justification et leur priorité.
Il sert d'ordre du jour à la **porte de ratification M0** de la roadmap de consolidation. Rien ici
n'est décidé : ce sont des propositions du comité d'architecture soumises au CEO.

## A. Ratification des décisions techniques fondatrices (DT-01 à DT-08)

Ces huit décisions structurent tout le noyau existant mais n'ont **jamais été ratifiées**. C'est
la dette de gouvernance la plus ancienne (Revue n°1, risque R2 ; Revue n°2, priorité M0). Chacune
doit devenir un ADR `Accepté` (ou être révisée) avant toute mise en production.

| ADR proposé | Décision technique | Enjeu de ratification | Priorité |
| --- | --- | --- | --- |
| ADR-0001 | **DT-01** Python 3.12 | Faible risque ; formaliser pour clore. | P3 |
| ADR-0002 | **DT-02** Workflow via LangGraph (checkpointer) | **Rouvrir** : tension avec le déterminisme (ADR-0010) et le cœur framework-agnostique. Décider si LangGraph reste ou si le `WorkflowEngine` maison suffit. | **P1** |
| ADR-0003 | **DT-03** Abstraction `LLMProvider` (défaut Claude) | **Rouvrir** avec la contrainte de rejeu (ADR-0010) et d'économie (ADR-0009). Prérequis absolu de la Vertical Slice. | **P1** |
| ADR-0004 | **DT-04** API FastAPI + SSE | Transport ; à confirmer, non urgent (aucun transport avant la Slice). | P2 |
| ADR-0005 | **DT-05** PostgreSQL 16 + pgvector + S3 | Persistance réelle ; confirmer la cible avant le premier adaptateur réel (M3). | P2 |
| ADR-0006 | **DT-06** Logs JSON + OpenTelemetry + audit append-only | Observabilité ; confirmer, aligner avec ADR-0009 (comptabilité coûts). | P2 |
| ADR-0007 | **DT-07** OIDC/JWT + RBAC + manifest | Authentification réelle ; confirmer, aligner avec ADR-0013 (sécurité de contenu). | P2 |
| ADR-0008 | **DT-08** Interrupt / resume CEO durable | Cœur de gouvernance déjà implémenté ; formaliser. | P1 |

> **Recommandation d'instruction.** Traiter en priorité **DT-02, DT-03, DT-08** (P1) : ce sont
> celles dont dépend la Vertical Slice et celles porteuses des tensions identifiées. Les autres (P2)
> peuvent être ratifiées « en principe » à M0 et confirmées à l'approche de leur mise en œuvre.

## B. Décisions nouvelles issues des revues stratégiques

| ADR proposé | Titre | Justification | Priorité |
| --- | --- | --- | --- |
| **ADR-0009** | Gouvernance économique | *Rédigé.* Risque N2. Prérequis de la Slice. | **P1** |
| **ADR-0010** | Déterminisme des interactions LLM | *Rédigé.* Risque N1. Prérequis de la Slice. | **P1** |
| ADR-0011 | **Audit : source unique de vérité** | Résout le double-write d'audit (§8.2 Revue n°2, risque de divergence). Faire de l'`AuditStore` persistant le ledger unique ; le moteur en mémoire devient un cache derrière le port. | **P1** |
| ADR-0012 | **Modèle d'état d'exécution unifié** | Clarifie la relation `WorkflowState` ⟂ `LifecycleState` (redondance identifiée). Décider d'une source de vérité unique de l'état, ou d'une projection explicite de l'un vers l'autre. | P2 |
| ADR-0013 | **Sécurité de contenu / frontière agent** | Traite l'injection de prompt et la validation de sortie (risque N4), au-delà du RBAC. À aligner avec DT-07. | P2 |
| ADR-0014 | **Évolution et migration de schéma append-only** | Stratégie de compatibilité ascendante/descendante des données immuables (audit, mémoire) — risque N5. | P2 |
| ADR-0015 | **Cadre de mesure de la valeur métier** | Formalise le [cadre de valeur](../consolidation/05-VALUE-METRICS-FRAMEWORK.md) en décision : quelles métriques, quel banc de référence, quelle gouvernance. | P2 |

## Ordre de traitement recommandé (porte M0)

1. **Bloc P1 d'abord** — ADR-0009, ADR-0010, ADR-0011, puis ratification DT-02/DT-03/DT-08.
   Sans ce bloc, la Vertical Slice ne peut pas démarrer proprement.
2. **Bloc P2 ensuite** — ratifier « en principe » DT-04/05/06/07 ; ouvrir ADR-0012→0015 comme
   travaux à instruire au fil de la roadmap, pas comme bloqueurs.
3. **Bloc P3** — ADR-0001 (Python) : formalité de clôture.

Aucun ADR de ce backlog ne passe `Accepté` sans **ratification explicite du CEO**.
