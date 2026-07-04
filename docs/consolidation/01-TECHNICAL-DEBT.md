# Registre de dette technique — AI-SOS

Vision unique de la dette technique avant reprise du développement. Chaque item porte une
**priorité** (P1 = à traiter dans la fenêtre de consolidation / Vertical Slice ; P2 = à planifier ;
P3 = à surveiller), un **type**, un **coût si reporté** et une **action recommandée**.

> Principe directeur (Revue n°2) : **chaque item est bon marché tant qu'aucun LLM ni client réel
> n'est branché, et coûteux dès qu'ils le sont.** La fenêtre de traitement optimale est
> maintenant.

## Synthèse

| # | Item | Type | Priorité | ADR lié |
| --- | --- | --- | --- | --- |
| D1 | Double écriture d'audit (moteur + UoW) | Intégrité | **P1** | ADR-0011 |
| D2 | Bornes économiques déclarées mais non appliquées | Gouvernance | **P1** | ADR-0009 |
| D3 | Absence de rejeu déterministe des LLM | Architecture | **P1** | ADR-0010 |
| D4 | `WorkflowState` vs `LifecycleState` (double suivi d'état) | Redondance | P2 | ADR-0012 |
| D5 | Représentations multiples de la « pause » (registry + checkpoint + snapshot) | Redondance | P2 | ADR-0012 |
| D6 | Duplication `coordinator._emit` / `resume._emit` | Redondance | P2 | — |
| D7 | Reprise (resume) non transactionnelle (asymétrie avec dispatch) | Cohérence | P2 | — |
| D8 | Event Bus construit mais sans abonné en production | Sur-ingénierie | P2 | — |
| D9 | Modules squelettes vides (`agents`,`api`,`councils`,`runtime`,`services`) | Bruit / sur-ingénierie | P2 | — |
| D10 | Couche Application façonnée avant tout client réel | Churn potentiel | P3 | — |
| D11 | `verify_chain` d'audit en O(n) global (non fenêtré) | Passage à l'échelle | P2 | ADR-0011 |
| D12 | Dette catalogue d'événements (`request.cancelled` non réconcilié) | Cohérence | P3 | — |
| D13 | Monoculture de test (unitaire + déterministe + in-memory) | Qualité / confiance | P2 | — |
| D14 | Dérive documentaire (docs décrivant l'inexistant) | Documentaire | P2 | — |
| D15 | Quality Gate en stub (vérification minimale) | Fonctionnel | **P1** (Slice) | — |

## Détail des items P1

### D1 — Double écriture d'audit *(intégrité)*
`coordinator.py` écrit chaque événement **deux fois** : `audit_engine.append(envelope)` (chaîne de
hachés, « preuve ») puis `uow.audit.append(record)` (persistance transactionnelle). Deux ledgers,
deux sources de vérité. Pour un registre faisant **foi légale** (décision 013), deux exemplaires
non réconciliés = **bug d'intégrité latent** (divergence possible en cas d'échec partiel avec un
adaptateur réel). **Action** : ADR-0011 — l'`AuditStore` persistant devient le ledger unique ; le
moteur en mémoire passe en cache derrière le port. *Effort : faible. Valeur : élevée.*

### D2 — Bornes économiques non appliquées *(gouvernance)*
`AgentBudgetExceededError`, `WorkflowRecursionLimitError`, `WorkflowTimeoutError` : **0 `raise`**.
**Action** : ADR-0009 — câbler les bornes dans l'`AgentRuntime` de la Vertical Slice dès la
première ligne. *Effort : moyen. Valeur : critique.*

### D3 — Rejeu déterministe des LLM absent *(architecture)*
Aucun mécanisme d'enregistrement/rejeu ; contradiction directe avec la promesse « rejouer le
cheminement exact ». **Action** : ADR-0010 — port de registre LLM (record/replay/stub).
*Effort : moyen. Valeur : critique (forensique/conformité).*

### D15 — Quality Gate en stub *(fonctionnel)*
Le `quality_gate` actuel ne vérifie que la présence d'options et d'arguments. C'est le garde-fou
central contre les recommandations faibles. **Action** : le rendre **réel** dans la Vertical Slice
(critères de complétude, argumentation, avocat du diable) — c'est précisément ce que la Slice
adverse doit exercer. *Effort : moyen. Valeur : élevée.*

## Détail des items P2 (à planifier, non bloquants)

- **D4 / D5 — Redondance d'état et de pause.** Décider (ADR-0012) d'une **source de vérité unique**
  de l'état d'exécution, ou d'une projection explicite. Aujourd'hui trois représentations coexistent
  sans invariant les liant. *Risque : divergence silencieuse. Effort : moyen.*
- **D6 — Duplication d'émission.** Factoriser un émetteur d'événements commun coordinateur/resumer.
  *Effort : faible.*
- **D7 — Resume non transactionnel.** Uniformiser : la reprise doit s'exécuter dans une UoW comme
  le dispatch. *Effort : faible-moyen.*
- **D8 — Event Bus sans abonné.** Décider : câbler un abonné réel (projection d'audit / observabilité)
  **ou** retirer le composant jusqu'au besoin réel. *Généralité spéculative à trancher.*
- **D9 — Modules squelettes.** Retirer ou convertir en stubs actifs. *Bruit qui suggère une
  couverture fonctionnelle inexistante.*
- **D11 — `verify_chain` global.** Introduire une vérification **fenêtrée / incrémentale** ; à faire
  avec l'adaptateur d'audit réel (ADR-0011). *Passage à l'échelle.*
- **D13 — Monoculture de test.** Ajouter des tests **d'intégration** (adaptateurs réels), **de
  propriétés / fuzzing** et **de concurrence** (UoW). Le 99 % actuel prouve la cohérence interne,
  pas la correction externe. *À démarrer avec le premier adaptateur réel (M3).*
- **D14 — Dérive documentaire.** Estampiller chaque doc `CONSTRUIT / PARTIEL / PLANIFIÉ` ;
  réconcilier le corpus (18k lignes) avec la surface réelle. *Vérité et maintenance.*

## Items P3 (surveiller)

- **D10 — Couche Application prématurée.** Légitime mais façonnée avant un vrai client → sa forme
  (DTO) churnera un peu. Coût de refonte faible (couche mince, 100 % couverte). Surveiller.
- **D12 — Dette catalogue.** `request.cancelled` à réconcilier lors d'un futur travail sur le
  catalogue d'événements.

## Ce que la dette technique n'est PAS ici

La qualité intrinsèque du construit reste élevée (couverture 99 %, mypy strict, frontières
appliquées). La dette listée est **de conception et de cohérence**, pas de correction : aucun item
ne remet en cause le fonctionnement des invariants déjà prouvés. La priorité P1 tient à un seul
principe : **traiter maintenant ce qui deviendra cher à l'arrivée du LLM et des clients réels.**

---

## Affectation des dettes aux étapes de construction (Debt Ownership)

> Ajout à la clôture des Fondations (E0), 2026-07-04. Application du **Debt Ownership Principle** :
> chaque dette a pour propriétaire une étape précise du Cahier des charges de construction et ne
> se traite que lorsque **cette** étape est ouverte — jamais avant. Une dette d'un étage futur
> reste dans son étage futur. Voir [`docs/reports/E0-FOUNDATIONS-CLOSURE.md`](../reports/E0-FOUNDATIONS-CLOSURE.md).

**Dettes résolues pendant les Fondations (E0)** — closes, conservées pour mémoire :

| Dette | Résolution |
| --- | --- |
| D1 — Double écriture d'audit | ✅ ADR-0011 / PR #38 — source unique, WORM, chaîne vérifiable |
| D2 — Bornes économiques non appliquées | ✅ ADR-0009 — bornes appliquées + escalade auditée (Slice adverse) |
| D3 — Rejeu déterministe LLM absent | ✅ ADR-0010 / PR #36 — port `LLMProvider` + record/replay |
| D15 — Quality Gate en stub | ✅ rendu réel dans la Vertical Slice adverse |

**Dettes ouvertes, affectées à leur étage propriétaire** — à ne pas anticiper :

| Dette | Étage propriétaire | Justification de l'affectation |
| --- | --- | --- |
| D7 — Reprise (resume) non transactionnelle | **E5** (persistance / monde réel) | Auditée et chaînée aujourd'hui ; à sceller avant l'exploitation durable, sans effet sur E1–E4 (déterministes en mémoire). |
| Adaptateur d'audit durable (PostgreSQL) | **E5** | Invariant d'audit prouvé en mémoire ; durabilité = propriété d'exploitation. |
| Fusion transport + backend LLM | **E5** | Abstraction gelée (revue #53) ; résolue au branchement d'un vrai LLM. |
| Chaînage enregistrement LLM → audit | **E5** | Pertinent quand la consommation LLM réelle entre dans le système. |
| D11 — `verify_chain` en O(n) global | **E5 / E6** | Optimisation liée à l'audit durable et au passage à l'échelle. |
| D13 — Monoculture de test | **E5** | Tests d'intégration/propriétés/concurrence à démarrer avec le premier adaptateur/LLM réel. |
| D4 / D5 — Redondance d'état et de pause (ADR-0012) | **E2** (à confirmer par ADR-0012) | À trancher quand la composition sollicitera l'orchestrateur ; non bloquant pour E1. |
| D8 — Event Bus sans abonné | **E2+** | Abonnés réels apparaîtront avec la composition / les consommateurs de production. |
| D9 — Modules squelettes (`agents`, `councils`, `runtime`, `services`, `api`) | **E2 – E7** | Activés à leur étage, jamais avant (composition, capacités, échelle). |
| D6 — Duplication `coordinator._emit` / `resume._emit` | **Opportuniste** | Nettoyage mineur, à faire seulement si un étage touche ce code ; non affecté à un étage propre. |
| D12 — Dette catalogue d'événements | **Opportuniste** | À réconcilier lors d'un futur travail sur le catalogue. |
| D10 — Couche Application prématurée | **Surveillance** | Churn possible ; refonte faible ; surveiller sans agir. |
| D14 — Dérive documentaire | **Transverse (chaque étage)** | Estampiller CONSTRUIT/PARTIEL/PLANIFIÉ au fil de chaque étage. |

**Règle** : aucune de ces dettes ouvertes ne doit être traitée pendant E1. Toute proposition les
concernant sera signalée comme appartenant à son étage propriétaire et **reportée**.
