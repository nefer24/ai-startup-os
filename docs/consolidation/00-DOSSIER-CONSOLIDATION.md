# Dossier de consolidation architecturale — AI-SOS

- **Destinataire** : CEO · **Auteur** : Chief Software Architect · **Date** : 2026-07-02
- **Statut** : Dossier de décision — **aucune décision n'est prise ici**, aucune n'est engagée sans
  ratification explicite du CEO.
- **Nature** : consolidation architecturale exclusive. Aucun code, aucune fonctionnalité, aucun
  composant modifié, aucune Pull Request. Uniquement des **décisions et des plans**.

## Pourquoi ce dossier

Après 30 Pull Requests et deux revues stratégiques, la décision a été prise de **stabiliser la
vision avant de reprendre le développement**. Ce dossier transforme les conclusions des deux revues
en **artefacts officiels et durables**, versionnés dans le dépôt. Il est la référence de travail de
la phase de consolidation.

## Contenu du dossier

| # | Document | Objet |
| --- | --- | --- |
| — | [ADR — index & convention](../adr/README.md) | Cadre des décisions d'architecture |
| — | [ADR-0009 — Gouvernance économique](../adr/ADR-0009-gouvernance-economique.md) | DT-09 : budgets, coûts, récursion, timeouts, quotas |
| — | [ADR-0010 — Déterminisme LLM](../adr/ADR-0010-determinisme-interactions-llm.md) | DT-10 : hash, versionnement, replay, cache, reproductibilité |
| — | [ADR — Backlog](../adr/ADR-BACKLOG.md) | Ratification DT-01→08 + 5 décisions à instruire |
| 01 | [Dette technique](01-TECHNICAL-DEBT.md) | 15 items priorisés (redondances, simplifications, refactorings, à surveiller) |
| 02 | [Registre des risques](02-RISK-REGISTER.md) | 11 risques : proba, impact, mitigation, indicateurs |
| 03 | [Roadmap orientée validation](03-ROADMAP.md) | M0→M6, chaque étape à critère de succès mesurable |
| 04 | [Plan Vertical Slice n°1](04-VERTICAL-SLICE-01-PLAN.md) | Objectif, périmètre, scénarios de réussite & d'échec volontaire, acceptation |
| 05 | [Cadre de mesure de la valeur](05-VALUE-METRICS-FRAMEWORK.md) | Qualité, utilité, acceptation, impact — mesurés de l'extérieur |

## Executive Summary

**Constat partagé (Revues n°1 & n°2).** Le noyau de gouvernance d'AI-SOS est excellent
(déterminisme, frontières appliquées, invariants prouvés, couverture 99 %) mais le « cerveau » —
des agents produisant une recommandation réelle via un LLM — est à **0 %**. La gouvernance n'a
jamais été éprouvée contre du travail réel.

**Trois décisions structurantes formalisées ici.**
1. **ADR-0009 (Gouvernance économique)** — le risque n°1 opérationnel d'un système agentique
   (emballement des coûts et des boucles) doit être **borné et appliqué**, pas seulement typé.
   Fait mesuré : les bornes existent en type mais sont appliquées **0 fois**.
2. **ADR-0010 (Déterminisme LLM)** — la promesse documentée « rejouer le cheminement exact » est
   **incompatible** avec un LLM réel non déterministe, sauf mécanisme d'**enregistrement/rejeu**.
   Sans lui, la capacité forensique s'effondre le jour de l'intégration LLM.
3. **ADR-0011 (Audit source unique de vérité)** — le double-write d'audit actuel (moteur + UoW)
   crée deux preuves potentiellement contradictoires ; à réduire à un ledger unique.

**Priorité absolue.** Ne plus empiler de couches. **Ratifier** (M0), puis **prouver** via une
**Vertical Slice adverse** (M1) dont le succès n'est pas « le chemin nominal fonctionne » mais
« **la gouvernance rattrape le pire** » — recommandation vide, faible, hors-budget, en boucle,
en timeout, agent qui tente de décider ou d'agir hors manifest.

**Cinquième dimension d'évaluation.** À la robustesse technique s'ajoute désormais la **valeur
métier produite**, mesurée **de l'extérieur** (banc gold), avec pour indicateur nord le **coût par
recommandation utile** — la seule métrique qui relie valeur et gouvernance économique.

## Décisions demandées au CEO (porte M0)

1. **Ratifier** ADR-0009 et ADR-0010 (P1).
2. **Ouvrir et arbitrer** ADR-0011 (audit source unique) — P1.
3. **Ratifier ou réviser** DT-02 (LangGraph), DT-03 (LLMProvider), DT-08 (interrupt CEO) — P1 —
   en tenant compte des tensions déterminisme (ADR-0010) et framework-agnostique.
4. **Ratifier « en principe »** DT-01/04/05/06/07 ; ouvrir ADR-0012→0015 comme travaux à instruire.
5. **Valider** la roadmap orientée validation et le plan de Vertical Slice adverse.
6. **Adopter** le cadre de mesure de la valeur comme cinquième dimension d'évaluation.

## Ce que ce dossier ne fait pas

Il ne code rien, ne crée aucun composant, ne démarre aucune Vertical Slice, n'ouvre aucune Pull
Request et ne modifie aucun composant existant. Il **stabilise la vision**. La première Vertical
Slice à implémenter sera décidée **ensemble**, après ratification.
