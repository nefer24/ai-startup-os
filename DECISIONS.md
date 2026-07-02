# AI-SOS Architecture Decisions Register

> The official register of AI-SOS architecture decisions.

Ce document est le registre officiel des décisions d'architecture d'AI-SOS. Chaque décision importante y est consignée afin d'assurer la traçabilité exigée par la Constitution. Seule la structure est préparée ici ; le contenu détaillé de chaque décision sera renseigné ultérieurement. D'autres décisions seront ajoutées au registre au fil de leur adoption.

## Décision 001 — Nouvelle stratégie Git officielle AI-SOS

## Décision 002 — Nouvelle gouvernance des Pull Requests

## Décision 003 — Rôles officiels

## Décision 004 — Principe de délégation contrôlée

## Décision 005 — Création du Engineering Handbook

## Décision 006 — Registre officiel des décisions

## Décision 007 — Guide des contributions

## Décision 008 — Code de conduite

## Décision 009 — Templates GitHub

## Décision 010 — Standards AI-SOS

## Décision 011 — Reviews

## Décision 012 — AI Review Package (ARP)

## Décision 013 — Audit d'architecture interne obligatoire

L'audit interne mené par un Conseil de Revue (plusieurs experts indépendants) devient une étape officielle du workflow AI-SOS, préalable à toute revue par le Chief AI Architect. Son rapport est archivé dans `reviews/packages/`.

## Décision 014 — Conseil Stratégique Dynamique (remplacement de l'Executive Board)

Le concept d'Executive Board est abandonné. AI-SOS adopte le **Conseil Stratégique Dynamique** : une instance exclusivement composée d'agents IA, consultative, rattachée directement au CEO, indépendante de l'Orchestrateur, activable au besoin et recomposée dynamiquement selon le problème, l'objectif ou le projet. Il analyse, débat, critique, priorise et recommande ; il ne décide jamais. Le CEO demeure la seule autorité humaine et le seul décideur. Corollaire : aucune autre autorité humaine que le CEO n'existe dans AI-SOS, et la « validation humaine graduée » ne peut déléguer la validation que vers des politiques pré-approuvées par le CEO, jamais vers un autre humain. Point à arbitrer séparément : l'Article VIII de la Constitution mentionne encore « Executive Board ». *(Point résolu par la décision 015.)*

## Décision 015 — Amendement de l'Article VIII : Conseil Stratégique Dynamique

L'Article VIII de la Constitution ([`docs/00-vision.md`](./docs/00-vision.md)) est amendé pour résoudre l'unique incohérence bloquante identifiée par l'Architecture Freeze Review v1 ([`reviews/packages/ARCHITECTURE-FREEZE-REVIEW-v1.md`](./reviews/packages/ARCHITECTURE-FREEZE-REVIEW-v1.md), INC-1).

**Pourquoi l'Executive Board est abandonné.** L'Executive Board décrivait une « instance de direction » qui traduit l'intention en orientations — un organe permanent évoquant une direction humaine intermédiaire. Ce concept contredisait la vision officielle d'AI-SOS : il n'existe **qu'une seule autorité humaine, le CEO**, et aucune instance intermédiaire ne « dirige » ni n'« arbitre » à sa place. La décision 014 avait acté cet abandon dans l'architecture ; le texte fondateur restait le seul document non aligné.

**Pourquoi le Conseil Stratégique Dynamique devient le concept officiel.** Il correspond à ce qu'AI-SOS est réellement : une instance **exclusivement composée d'agents IA**, **consultative**, **rattachée directement au CEO**, **indépendante de l'Orchestrateur**, **activée uniquement lorsqu'une réflexion stratégique est nécessaire**, **composée dynamiquement selon la nature du problème**, **dissoute après la remise de ses recommandations** et **dépourvue de tout pouvoir décisionnel**. Les agents IA analysent, débattent, critiquent, proposent et recommandent ; seul le CEO prend les décisions finales.

**Impacts sur l'architecture.** Aucun changement conceptuel : les Phases 2, 3 et 4 appliquaient déjà la décision 014. L'amendement aligne le texte fondateur sur l'aval (Article VIII : remplacement du niveau « Executive Board », réaffirmation de l'autorité unique du CEO, mise en cohérence du « mouvement type », correction « Orchestrator » → « Orchestrateur »), et les notes « à arbitrer » devenues sans objet sont retirées de `docs/system/01`, `docs/system/08`, `docs/policies/10` et `docs/policies/README`. Cet amendement lève la dernière réserve avant la déclaration de l'**Architecture Baseline v1.0**.
