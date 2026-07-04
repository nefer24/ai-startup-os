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

## Décision 016 — Architecture Baseline v1.0

L'architecture d'AI-SOS issue des Phases 1 à 4 est officiellement déclarée **AI-SOS Architecture Baseline v1.0**, documentée dans [`docs/BASELINE-v1.0.md`](./docs/BASELINE-v1.0.md). Cette déclaration s'appuie sur l'Architecture Freeze Review v1 (score 92/100, PR #7) et sur la résolution de son unique incohérence bloquante par l'amendement de l'Article VIII (décision 015, PR #8) : plus aucune incohérence bloquante ne subsiste. La baseline couvre les Phases 1 (Vision & Gouvernance), 2 (Architecture conceptuelle), 3 (Spécification comportementale) et 4 (Politiques de décision), ainsi que les décisions 001 à 016. Règles associées : toute évolution architecturale part de cette baseline ; toute modification importante passe par Pull Request ; toute Pull Request produit un AI Review Package (décision 012) ; toute Pull Request importante passe par un audit interne (décision 013) ; la validation finale du CEO est obligatoire.

## Décision 017 — Discipline de construction séquentielle (Cahier des charges + Debt Ownership)

AI-SOS adopte une **discipline de construction séquentielle** : le projet se bâtit comme un immeuble, étape par étape (E0 → E7), et **il est interdit d'ouvrir un étage tant que le précédent n'est pas terminé ET validé par le CEO**, même si une idée est bonne, alignée avec la vision et techniquement correcte. Le **Cahier des charges de construction** devient la **Constitution de la construction** (la roadmap dit l'ordre ; la Constitution dit pourquoi cet ordre est nécessaire). Toute proposition est évaluée par **cinq garde-fous** : *Vision Alignment · Responsibility Boundary · Construction Sequence · Dependency Justification · Debt Ownership*. Le **Debt Ownership Principle** établit que chaque dette a pour propriétaire une étape précise et ne se traite que lorsque cette étape est ouverte — jamais avant ; une dette d'un étage futur reste dans son étage futur. Toute AI Architecture Review se termine désormais par une section **Construction Discipline Review**. Corollaire de clôture : une étape n'est close que si ses critères de sortie sont validés, ses dettes propres résolues ou explicitement acceptées, et les dettes des étapes futures laissées à leur étage — le perfectionnisme est refusé au profit d'une progression disciplinée.

## Décision 018 — Clôture officielle des Fondations (E0) et ouverture de E1

Après la Revue officielle de clôture des Fondations (verdict 🟡, recommandation d'ouvrir E1) et la revue indépendante d'Orion, le CEO déclare les **Fondations (E0) officiellement clôturées avec réserves**. Preuves à la clôture : **520 tests** (dont **120** de gouvernance), `mypy` strict (96 fichiers), `ruff`/`format`/CI verts, cœur sans framework, ADR-0009/0010/0011 ratifiées et implémentées. Les réserves sont reconnues comme des **dettes planifiées** affectées à leurs étapes (persistance/monde réel ≈ E5 pour l'audit durable, la reprise transactionnelle — dette D7 —, la fusion transport+backend et le chaînage LLM→audit ; E2–E7 pour les modules squelettes) et **ne bloquent pas** l'ouverture de E1. Décisions : (1) E0 est définitivement clôturé ; (2) **E0 est verrouillé** — aucune PR de Fondations, sauf défaut critique ou décision exceptionnelle du CEO ; (3) les dettes reportées restent affectées à leurs étapes et ne doivent pas être anticipées ; (4) **E1 est officiellement ouvert** — à partir de ce jalon, toute proposition appartient à E1. Détail : [`docs/reports/E0-FOUNDATIONS-CLOSURE.md`](./docs/reports/E0-FOUNDATIONS-CLOSURE.md). Interdit immédiat en E1 : « décorer » le cerveau (débats supplémentaires, synthèse enrichie, agents en dur) — la richesse viendra du catalogue en E2.

## Décision 019 — Discipline de développement : huit principes de construction

La discipline de développement (décision 017) est étendue de cinq à **huit principes**, appliqués obligatoirement à toute analyse, recommandation, AI Architecture Review et proposition de PR : (1) **Vision Alignment** ; (2) **Responsibility Boundary** ; (3) **Construction Sequence** ; (4) **Dependency Justification** (justifier chaque dépendance comme une nécessité logique) ; (5) **Debt Ownership** ; (6) **Purpose of the Stage** (expliquer *pourquoi* AI-SOS a besoin de cet étage, pas seulement ce qu'il fait) ; (7) **Contract to Future Stages** (à la clôture, le comportement d'un étage devient une référence stable pour les niveaux supérieurs) ; (8) **New Capabilities Enabled** (nommer ce que la clôture d'un étage rend officiellement possible). Ces huit vérifications guident désormais toutes les futures analyses ; la section **Construction Discipline Review** reste obligatoire en fin de revue.

## Décision 020 — Clôture officielle de E1 (cerveau pur gouverné) et ouverture de E2

Après la Revue officielle de clôture de E1 (verdict ✅) et la revue indépendante d'Orion, le CEO déclare **E1 officiellement clôturé** et **E2 officiellement ouvert**. La revue démontre que les critères de sortie de E1 sont remplis, que les huit principes de construction sont respectés, que le cerveau est une capacité **pure, déterministe, gouvernée, nourrie par contexte et figée**, qu'**aucune capacité de E2 n'a été anticipée** (`src/aisos/agents/` inchangé depuis la PR #62), et que le **contrat laissé à E2 est stable**. Preuves : **520 tests** (dont **120** de gouvernance, **66** du cerveau), `mypy` strict (96 fichiers), `ruff`/`format`/CI verts. Décisions : (1) **E1 est verrouillé** ; (2) le **périmètre du cerveau est gelé comme contrat de référence** — toute évolution future du cerveau devra respecter ce contrat et **ne pourra être réalisée que par une décision explicite du CEO** ; (3) les dettes des étages futurs restent affectées à leurs propriétaires (Debt Ownership) ; (4) **E2 devient l'étape active** — à partir de ce jalon, **toutes les futures PR relèvent de E2** (composition gouvernée : registre de capacités + instanciation déterministe). Détail et contrat de référence : [`docs/reports/E1-BRAIN-CLOSURE.md`](./docs/reports/E1-BRAIN-CLOSURE.md).

## Décision 021 — Clôture officielle de E2 (composition gouvernée) et ouverture de E3

Après la Revue officielle de clôture de E2 (verdict ✅) et la revue indépendante d'Orion, le CEO déclare **E2 officiellement clôturé** et **E3 officiellement ouvert**. La revue démontre que le **contrat de capacité** est une fondation stable, que le **registre** est passif/déterministe/conforme à son rôle, que la **composition gouvernée** est construite et validée, que l'**instanciation auditée sous politique pré-approuvée** est correctement intégrée, que les **huit principes de construction** sont respectés, qu'**aucune responsabilité de E3 n'a été anticipée**, que le **cerveau reste une capacité de référence gelée**, que l'**orchestrateur reste un coordinateur gouverné** et que le **CEO demeure l'unique autorité décisionnelle**. Preuves : **565 tests** (dont **120** de gouvernance et **45** propres à E2 — contrat 11, registre 12, composition 11, instanciation 11), `mypy` strict (100 fichiers), `ruff`/`format`/CI verts, `src/aisos/agents/` inchangé depuis la PR #62. Décisions : (1) **E2 est verrouillé** ; (2) les **contrats de E2 sont gelés comme fondation de référence** — `Capability`/`CapabilityDescriptor` (contrat), `CapabilityRegistry` (registre passif), `compose_organization`/`resolve_capabilities` (composition), `OrganizationInstantiator` (instanciation gouvernée) — toute évolution de ces contrats étant **réservée à une décision explicite du CEO** ; (3) les dettes des étages futurs restent affectées à leurs propriétaires (Debt Ownership) — la *variance* de composition n'est **pas une dette de E2** mais une propriété que **E3 débloquera** ; (4) **E3 devient l'étape active** — à partir de ce jalon, **toutes les futures PR relèvent de E3** (évolution gouvernée des capacités : création/dépréciation sous décision CEO + Conseil Stratégique). La **double frontière** *instancier (délégué, E2.4) / créer (CEO, E3)* est posée et gelée. Détail et contrats de référence : [`docs/reports/E2-COMPOSITION-CLOSURE.md`](./docs/reports/E2-COMPOSITION-CLOSURE.md).

## Décision 022 — Clôture officielle de E3 (évolution gouvernée des capacités) et ouverture de E4

Après la Revue officielle de clôture de E3 (verdict ✅) et la revue indépendante d'Orion, le CEO déclare **E3 officiellement clôturé** et **E4 officiellement ouvert**. La revue démontre que la **création gouvernée** des capacités est construite, auditée et réservée au CEO, que la **dépréciation gouvernée** est non destructive et préserve l'historique, que le **catalogue vivant** est déterministe/traçable/gouverné, que le **Conseil Stratégique** est strictement consultatif (aucune surface d'écriture/gouvernance/décision), que les **huit principes de construction** sont respectés, qu'**aucune responsabilité de E4 n'a été anticipée**, que le **cerveau reste gelé**, que l'**orchestrateur conserve son rôle de gouvernance** et que le **CEO demeure l'unique autorité décisionnelle**. Preuves : **617 tests** (dont **120** de gouvernance et **52** propres à E3 — création 15, dépréciation 14, catalogue 13, Conseil 10), `mypy` strict (104 fichiers), `ruff`/`format`/CI verts, `src/aisos/agents/` inchangé depuis la PR #62, contrats E2 non rouverts. Décisions : (1) **E3 est verrouillé** ; (2) les **contrats de E3 sont gelés comme fondation de référence** — `GovernedCapabilityCreator`/`CapabilityCreation` (création gouvernée), `GovernedCapabilityDeprecator`/`CapabilityDeprecation` (dépréciation gouvernée), `CatalogState`/`GovernedCatalog` (catalogue vivant), `StrategicCouncil`/`CatalogRecommendation` (Conseil consultatif) — toute évolution de ces contrats étant **réservée à une décision explicite du CEO** ; (3) les dettes des étages futurs restent affectées à leurs propriétaires (Debt Ownership) — la **mémoire** de l'évolution n'est **pas une dette de E3** mais le périmètre propre de **E4** ; (4) **E4 devient l'étape active** — à partir de ce jalon, **toutes les futures PR relèvent de E4** (mémoire durable de l'organisation). La **frontière recommandation / décision** (le Conseil recommande, le CEO décide) est construite et gelée. Détail et contrats de référence : [`docs/reports/E3-CAPABILITY-EVOLUTION-CLOSURE.md`](./docs/reports/E3-CAPABILITY-EVOLUTION-CLOSURE.md).
