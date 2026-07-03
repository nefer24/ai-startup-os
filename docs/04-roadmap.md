# Roadmap

> What we are building and when.

This document outlines the planned evolution of AI-SOS across upcoming milestones.

## Completed Milestones

### M0 — Préparation d'un fournisseur LLM réel sécurisé ✅ (2026-07-03)

Fondation sûre, déterministe et gouvernée, prête à recevoir un fournisseur LLM réel **sans en
avoir branché un**. Livrables : port `LLMProvider`, record/replay déterministe,
`LLMInteractionStore`, persistance mémoire des interactions, Vertical Slice adverse F1–F10,
audit source unique, cadre de valeur, squelette d'adaptateur réel (désactivé par défaut),
barrière d'activation CEO-only. ADR ratifiées : **ADR-0009** (M0-001), **ADR-0010** (M0-002),
**ADR-0011** (M0-003). Rapport de clôture :
[`docs/reports/M0_LLM_READINESS_REPORT.md`](reports/M0_LLM_READINESS_REPORT.md).

## Current Focus

Clôture officielle de M0 (rapport de readiness). Aucun provider réel branché.

## Upcoming Milestones

### M1 — Premier branchement réel gouverné (proposé, non ratifié)

Implémentation d'un backend derrière le port `LLMProvider`, chargement sécurisé du secret depuis
la variable d'environnement référencée, consommation de `activated_config` par un composant
racine **passant par la barrière d'activation CEO-only**, première campagne record/replay contre
un modèle réel — le tout sous décision CEO explicite. Voir les risques restants RR1–RR7 du
rapport M0.

## Future Exploration

Persistance durable (base réelle derrière les ports existants), surface d'exposition (API),
stratégie de rétention/archivage de l'audit.
