# Rapport de validation — Vertical Slice adverse n°1

- **Objet** : premier rapport de validation de la Vertical Slice adverse d'AI-SOS.
- **Destinataire** : CEO · **Auteur** : Chief Software Architect · **Date** : 2026-07-03.
- **Portée** : constat **factuel** de ce qui est construit et prouvé par test. Ce rapport ne
  déclare **pas** le système prêt pour la production (voir §8 Limites et §9 Risques).
- **Sources** : PR #32 (Slice F1–F6), PR #33 (Slice F7–F10), PR #34 (cadre de valeur), toutes
  fusionnées dans `develop`. Code : `src/aisos/slice/`, `src/aisos/value/`, intégration
  `src/aisos/orchestrator/`.

## Avertissement de périmètre (à lire en premier)

Cette Slice est un **test grandeur nature de la gouvernance** sur le noyau existant, avec trois
pièces minimales nouvelles. Elle n'est **pas** un produit. En particulier, **à ce jour** :

- le **LLM est un stub déterministe** (`StubLLMProvider`) — aucun modèle réel, aucun appel réseau ;
- la **persistance est en mémoire** (`InMemoryUnitOfWork`, `InMemoryDatabase`,
  `InMemoryCheckpointStore`) — aucune base réelle (pas de PostgreSQL) ;
- il n'y a **aucune API** (pas de FastAPI, REST, GraphQL, WebSocket, CLI) ;
- il n'y a **aucun adaptateur réel** (ni LLM, ni base, ni broker, ni transport) ;
- il n'y a **aucun framework d'orchestration** réel (pas de LangGraph).

Ces points ne sont pas des défauts de la Slice : ils sont **hors de son périmètre**, volontairement.

## 1. Objectif de la Vertical Slice

Démontrer, de bout en bout, que le noyau construit pendant les 30 premières PR **gouverne un
travail réel** produit par un agent — **y compris quand l'agent se comporte mal**. Le critère de
succès est **inversé** : le succès n'est pas « le chemin nominal se termine », mais « **chaque
comportement dégénéré de l'agent est refusé, borné ou escaladé, et tracé** », sans jamais produire
de décision automatique ni d'état incohérent (réf. `docs/consolidation/04-VERTICAL-SLICE-01-PLAN.md`).

## 2. Pipeline complet testé

La chaîne exercée, câblée aux composants **existants** (aucune couche horizontale nouvelle) :

```
Request Application Service
  → Orchestrateur (ComponentCoordinator)
    → Workflow (InMemoryWorkflowEngine)
      → Agent Runtime (borné, stub)        ┐ pièces
        → LLM Provider (stub déterministe)  │ nouvelles
          → Recommendation                  │ de la
            → Quality Gate (réel)           ┘ Slice
              → Policy Engine
                → pause CEO si nécessaire
                  → Audit (chaîné, append-only)
                    → Persistence (Unit of Work mémoire + checkpoint)
                      → Response (DTO)
```

Trois pièces neuves seulement : `StubLLMProvider`, `AgentRuntime` borné, `DeterministicQualityGate`.
Tout le reste est le noyau des Phases 13–25. L'intégration est **opt-in** : sans étage de
délibération injecté, le comportement des Phases 19–25 est inchangé.

## 3. Scénarios adverses F1 à F10

Chaque scénario **injecte** un comportement dégénéré via le stub et vérifie que le **garde-fou
correspondant** agit, puis que l'issue est auditée et l'état cohérent.

| # | Comportement injecté | Garde-fou observé | Test (governance) |
| --- | --- | --- | --- |
| F1 | timeout LLM | suspension + `escalation.raised` audité | `test_f1_llm_timeout_is_escalated_and_audited` |
| F2 | réponse LLM vide | Quality Gate **rejette** (renvoi), aucune décision | `test_f2_empty_response_is_rejected_by_quality_gate` |
| F3 | budget dépassé | escalade ; **aucune** exécution ni écriture mémoire | `test_f3_budget_exceeded_is_escalated_no_execution` |
| F4 | boucle (auto-invocation) | récursion **bornée** + escalade | `test_f4_loop_is_bounded_and_escalated` |
| F5 | recommandation faible | Quality Gate **rejette** | `test_f5_weak_recommendation_is_rejected` |
| F6 | demande à risque élevé | reco valide ⇒ **routage CEO** (`paused_ceo`) | `test_f6_high_risk_routes_to_ceo_after_valid_recommendation` |
| F7 | outil hors manifest | refus + `agent.permission_denied` audité ; aucune exécution dangereuse | `test_f7_tool_outside_manifest_is_denied_and_audited` |
| F8 | agent tente de décider | issue **ignorée** (aucun champ de décision dans la reco) ; seul le CEO décide | `test_f8_agent_decision_is_ignored_only_ceo_decides` |
| F9 | crash après appel LLM + reprise | appel LLM enregistré ; reprise **ne rappelle pas** le modèle ; rejeu **exact** ; audit cohérent | `test_f9_crash_after_llm_then_replay_without_recall` |
| F10 | non-CEO tente de reprendre | `GovernanceViolationError` ; workflow reste suspendu | `test_f10_non_ceo_cannot_resume_suspended_flow` |

Un test méta (`test_all_ten_adverse_scenarios_are_covered`) vérifie que les dix scénarios disposent
chacun d'au moins un test. Deux compléments confirment la précision des garde-fous : F7 avec l'outil
**déclaré** au manifest ne déclenche pas de refus (`test_f7_declared_tool_would_pass`) ; la reprise
n'a lieu que sur décision valide du CEO (`test_escalated_flow_resumes_only_on_ceo_decision`).

## 4. Scénario nominal S1

Le chemin nominal est nécessaire mais **insuffisant** à lui seul (il n'exerce aucun garde-fou) :

- `test_s1_nominal_without_policy_routes_to_ceo` : sans politique pré-approuvée, même une demande
  courante remonte au CEO (aucune validation implicite).
- `test_s1_with_policy_completes_under_delegation` : avec une politique pré-approuvée éligible, la
  demande est **exécutée sous délégation** jusqu'à `completed`, et le pipeline complet
  (`request.received → agent.invoked → quality_gate.passed → policy.evaluated → policy.applied →
  memory.updated`) est audité, chaîne d'audit valide.

## 5. Métriques de valeur disponibles

Un cadre de mesure **externe** (`src/aisos/value/`) lit les résultats de la Slice et calcule sept
métriques **déterministes**, contre un **banc gold en mémoire** dont les attentes sont connues et
indépendantes du système. **Le système ne se note jamais lui-même ; aucun LLM n'est utilisé pour
évaluer** (le module `value` n'importe ni LLM ni la Slice — prouvé par test).

| Métrique | Définition |
| --- | --- |
| Qualité | qualité moyenne des recommandations (grille externe, cas non adverses) |
| Utilité métier | part des recommandations jugées utiles (banc gold) |
| Taux d'acceptation | part d'`approuve` sans ajustement (ni 0 % ni 100 % attendus) |
| Ampleur des ajustements CEO | nombre moyen d'ajustements sur les issues `ajuste` |
| Coût par recommandation utile | coût LLM total ÷ nombre de recommandations utiles (**indicateur nord**) |
| Taux de rattrapage adverse | part des cas adverses rattrapés (cible : 100 %) |
| Taux d'escalade justifiée | part des escalades qui étaient justifiées |

**Réserve importante** : ces métriques sont calculées sur un **mini-banc en mémoire** et avec un
LLM **stub**. Les valeurs de qualité/utilité reflètent donc la structure des sorties **simulées**,
pas la performance d'un modèle réel. Le cadre est **prêt à mesurer** ; il n'a pas encore mesuré un
travail réel.

## 6. Résultats des tests

Vérification exécutée sur `develop` (Python 3.12, environnement `.venv-verify`) :

| Contrôle | Résultat |
| --- | --- |
| `ruff check .` + `ruff format --check .` | ✅ All checks passed |
| `mypy` (strict, plugin pydantic) | ✅ no issues found in 83 source files |
| `pytest` (total) | ✅ **320 passed** |
| dont marqueur `governance` | ✅ **112 passed** |
| dont marqueur `unit` | ✅ **207 passed** |
| Couverture `src/aisos/slice/`, `src/aisos/value/`, `orchestrator/deliberation.py` | ✅ **100 %** |
| GitHub Actions (job `quality`) sur PR #32, #33, #34 | ✅ vert |

Aucune régression : les tests des Phases 13–25 restent verts (la Slice est opt-in).

## 7. Invariants de gouvernance prouvés

Prouvés par test **sous conditions adverses** (au-delà de la simple présence de code) :

- **L'Orchestrateur ne décide jamais** : sur chaque cas suspendu, `ceo_outcome` reste `None` hors
  reprise CEO ; le workflow s'arrête proprement en `paused_ceo`.
- **Un agent ne décide jamais** : le schéma `Recommendation` ne porte aucun champ de décision ;
  une « décision » tentée par l'agent (F8) est auditée comme **ignorée**.
- **Seul le CEO reprend** : une tentative non-CEO (F10) lève `GovernanceViolationError` ; le flux
  reste suspendu.
- **Bornes économiques appliquées** (ADR-0009) : budget (F3), récursion (F4), timeout (F1) sont
  **appliqués** — des erreurs jusqu'ici jamais levées (DT-09) le sont désormais.
- **Least privilege** (F7) : un outil hors manifest est refusé et audité (`agent.permission_denied`).
- **Défaut conservateur** : le doute/risque route vers le CEO (F6).
- **Audit append-only et chaîné** : la chaîne reste vérifiable sur tous les scénarios ; chaque
  événement publié est aussi audité.
- **Atomicité** : une panne en cours d'orchestration provoque un rollback total (aucune écriture
  partielle) ; la reprise depuis checkpoint reconstitue l'état exact.
- **Déterminisme du rejeu** (ADR-0010) : après crash, la reprise **ne rappelle pas** le modèle et
  reproduit exactement la sortie enregistrée (F9).

## 8. Limites actuelles

- **LLM simulé** : `StubLLMProvider` déterministe ; aucun modèle réel, aucun coût réel, aucune
  variabilité de modèle. Les métriques de qualité/utilité ne portent donc pas encore de signal
  produit réel.
- **Persistance en mémoire** : `InMemoryDatabase` / `InMemoryUnitOfWork` / `InMemoryCheckpointStore` ;
  rien n'est durable après l'arrêt du processus ; aucune contrainte SQL, aucune concurrence réelle.
- **Aucune API / aucun transport** : le point d'entrée est la couche Application (appels
  in-process) ; pas de FastAPI, REST, SSE, CLI.
- **Aucun adaptateur réel** : ni LLM, ni base, ni broker, ni OIDC réel.
- **Registre de rejeu local à la Slice** : le mécanisme record/replay (F9) est en mémoire et propre
  à la Slice ; il n'est pas encore un service de rejeu généralisé (prévu M2).
- **Double écriture d'audit non encore résolue** : l'audit est écrit par le moteur ET l'unité de
  travail (dette D1 / ADR-0011 à instruire) — non traité par cette Slice.
- **Banc gold minimal** : le banc de valeur est un échantillon en mémoire, pas un banc représentatif.

## 9. Risques restants

- **R-DET (déterminisme ⟂ LLM réel)** : le rejeu déterministe est prouvé **contre un stub**. Sa
  tenue face à un LLM réel (non déterministe) reste à démontrer à l'intégration (M2/M3).
- **R-AUD (intégrité d'audit)** : tant que le double-write (D1) n'est pas réduit à une source unique
  (ADR-0011), deux preuves potentiellement divergentes coexistent.
- **R-ECO (coût réel)** : la comptabilité économique est appliquée sur des coûts **simulés** ; le
  coût par recommandation utile n'a de sens qu'avec un LLM réel et un barème de prix.
- **R-VAL (signal de valeur)** : les métriques ne mesurent pas encore un travail réel ; le risque
  d'auto-complaisance est écarté par construction (mesure externe), mais le signal reste à établir
  sur un banc représentatif.
- **R-MIG / R-SEC / R-CEO** : migration de schéma, sécurité de contenu (injection de prompt) et
  débit décisionnel du CEO ne sont pas abordés par cette Slice (planifiés M4–M5).

## 10. Recommandations pour la prochaine étape

Par ordre de dé-risquage (aligné sur `docs/consolidation/03-ROADMAP.md`) :

1. **M2 — Consolidation ciblée** : réduire l'audit à une **source unique** (ADR-0011, dette D1) et
   généraliser le **registre de rejeu LLM** (modes record/replay) au-delà de la Slice.
2. **Porte M0 (suite)** : instruire/ratifier **ADR-0010** (déterminisme), **ADR-0011** (audit
   source unique), puis **DT-02/DT-03/DT-08**.
3. **M3 — Premier adaptateur réel** : choisir l'axe le plus dé-risquant — **LLMProvider réel**
   (derrière le registre de rejeu) **ou** **persistance PostgreSQL** — et exiger qu'il **passe la
   Slice adverse** (F1–F10) sans régression. Ajouter des tests d'intégration, de propriétés/fuzzing
   et de concurrence.
4. **Instrumenter la valeur sur données réelles** : constituer un banc gold représentatif et
   calculer qualité/utilité/coût par recommandation utile contre un modèle réel.

Aucune de ces étapes ne doit précéder une décision explicite du CEO. **Ce rapport n'engage aucune
action** ; il établit un constat.

---

*Ce rapport est strictement documentaire. Aucun code source n'a été modifié, aucun composant créé.
Il reflète l'état de `develop` au 2026-07-03 (PR #32, #33, #34 fusionnées).*
