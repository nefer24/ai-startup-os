# Plan de la Vertical Slice n°1 — « Gouvernance sous conditions adverses »

Plan détaillé, **sans code**. Cette Vertical Slice est la première démonstration end-to-end
qu'AI-SOS produit — et **gouverne** — un travail réel. Sa particularité, issue de la Revue n°2 :
elle est **adverse par construction**. Son but n'est pas de montrer que le chemin nominal
fonctionne, mais que **la gouvernance rattrape le pire**.

## 1. Objectif

Prouver que, face à un agent qui produit un travail via un LLM, la chaîne
`Request → Agent → LLM → Recommendation → Quality Gate → Policy → CEO → Audit → Persistence`
respecte les invariants de gouvernance **y compris quand l'agent se comporte mal**.

> **Critère de succès inversé.** Le succès n'est pas « la demande se termine ». Le succès est
> « **chaque comportement dégénéré de l'agent est refusé, borné ou escaladé, et tracé** ». Un
> parcours nominal réussi ne prouve rien à lui seul ; la valeur est dans les modes d'échec exercés.

## 2. Périmètre

**Inclus**
- Un `LLMProvider` en **mode `stub` déterministe** (ADR-0010) capable d'émettre des sorties
  **nominales ET dégénérées** à la demande.
- Un `AgentRuntime` minimal **borné** (manifest + budgets ADR-0009 + récursion + timeouts).
- La production d'une `Recommendation` (schéma existant, Phase 8).
- Un **Quality Gate réel** (remplace le stub actuel).
- Le câblage aux composants **existants** : Policy, Orchestrator, Workflow, CEO resume, Audit,
  Persistence (UoW), Application layer.

**Exclus (hors périmètre)**
- LLM réel, réseau, FastAPI/REST/SSE, CLI, PostgreSQL, LangGraph, conseils multi-agents.
- Toute nouvelle couche horizontale. On **réutilise** le noyau ; on n'en ajoute pas.

## 3. Composants mobilisés

| Composant | Rôle dans la Slice | Statut |
| --- | --- | --- |
| `LLMProvider` (stub, ADR-0010) | émettre des sorties nominales/dégénérées | **à créer (Slice)** |
| `AgentRuntime` (bornes, ADR-0009) | exécuter l'agent sous manifest + budgets | **à créer (Slice)** |
| Registre de consommation (ADR-0009) | comptabiliser tokens/coût/latence | **à créer (Slice)** |
| `Quality Gate` réel | rejeter les recommandations faibles | **à renforcer (D15)** |
| Policy Engine | classer, défaut conservateur, routage | existant |
| Orchestrator + Workflow | coordination, pause CEO, transitions | existant |
| CEO resume | appliquer la décision du CEO | existant |
| Audit + Persistence (UoW) | tracer et persister atomiquement | existant |
| Application layer | exposer via DTO | existant |

## 4. Scénarios de réussite (chemin nominal)

| S# | Entrée | Comportement agent | Résultat attendu |
| --- | --- | --- | --- |
| S1 | Demande simple, faible risque, politique pré-approuvée existante | recommandation complète et argumentée | Quality Gate **passe** → délégation sous politique → exécution → audit → persistance atomique |
| S2 | Demande à risque modéré | recommandation complète | Quality Gate passe → **routage CEO** (importante) → workflow `paused_ceo` → décision CEO `APPROUVE` → reprise → `COMPLETED` |
| S3 | Demande structurante | recommandation complète | routage CEO **obligatoire** → CEO `AJUSTE` (ajustements autorisés seulement) → `COMPLETED` |

Ces scénarios prouvent le **câblage**. Ils sont nécessaires mais **insuffisants** : ils
n'exercent aucun garde-fou.

## 5. Scénarios d'échec volontaire (le cœur de la Slice)

Chaque scénario **injecte** un comportement dégénéré via le stub LLM et vérifie que le
garde-fou **correspondant** agit. C'est ici que la gouvernance est réellement testée.

| F# | Mode dégénéré injecté | Garde-fou attendu | Invariant prouvé |
| --- | --- | --- | --- |
| F1 | **Recommandation vide** | Quality Gate **rejette** → renvoi en délibération | pas de décision sur du vide |
| F2 | **Recommandation faible** (0 argument / 0 option) | Quality Gate **rejette** | pas de recommandation non argumentée |
| F3 | **Hors-budget token/coût** | `AgentBudgetExceededError` → **escalade CEO**, aucune exécution | ADR-0009 : budget appliqué |
| F4 | **Boucle** (auto-invocation infinie) | `WorkflowRecursionLimitError` → **suspension**, jamais un tour de plus | ADR-0009 : récursion bornée |
| F5 | **Timeout** (nœud LLM qui « traîne ») | `WorkflowTimeoutError` → **suspension**, pas de rejeu aveugle | ADR-0009 : timeout appliqué |
| F6 | **Doute élevé / information manquante** | défaut conservateur → **routage CEO** | tout doute → CEO |
| F7 | **Agent tente une action hors manifest** | refus + audit (`agent.permission_denied`) | manifest least privilege |
| F8 | **Agent tente de « décider »** (produit une issue) | l'issue est **ignorée** ; seul le CEO décide | aucune décision automatique |
| F9 | **Crash mid-graph après appel LLM** puis reprise | reprise **ne rappelle pas** le LLM (registre) → état exact reproduit | ADR-0010 : rejeu déterministe |
| F10 | **Non-CEO tente de reprendre** un flux en pause | `GovernanceViolationError` | seul le CEO reprend |

## 6. Critères d'acceptation

La Vertical Slice est **acceptée** si et seulement si :

1. **Tous les scénarios S1–S3** se terminent avec l'état et les événements attendus.
2. **Tous les scénarios F1–F10** aboutissent au garde-fou attendu — **refus, bornage ou escalade**,
   jamais une exécution ou une décision « en aveugle ».
3. **Économie** : la consommation (tokens/coût/latence) est **comptabilisée et auditée** pour
   chaque appel LLM ; aucun agent hors-budget ne s'exécute (F3).
4. **Déterminisme** : une reprise après crash (F9) **ne rappelle pas** le modèle et **reproduit
   l'état exact** ; un rejeu forensique d'une décision passée est reproductible.
5. **Audit** : une **source unique de vérité** (ADR-0011) ; la chaîne d'audit reste vérifiable ;
   chaque décision est traçable jusqu'à la recommandation et à l'interaction LLM qui l'ont produite.
6. **Gouvernance** : aucun invariant existant n'est régressé (les tests de gouvernance des Phases
   14–25 restent verts).
7. **Valeur** : les métriques du [cadre de valeur](05-VALUE-METRICS-FRAMEWORK.md) sont **calculées**
   sur un mini-banc de référence (même si les valeurs initiales sont modestes).

## 7. Livrables attendus (à l'implémentation, hors de ce plan)

- Le port `LLMProvider` + son stub adverse ; l'`AgentRuntime` borné ; le Quality Gate réel.
- Une suite de tests **F1–F10** (gouvernance adverse) + **S1–S3** (nominal).
- Le tableau de bord minimal des métriques de valeur et de coût.
- Un rapport de Slice : « la gouvernance a-t-elle rattrapé le pire ? » — avec preuves.

## 8. Ce que la Slice n'est pas

Ce n'est **pas** une démonstration produit, **pas** un transport, **pas** un LLM réel, **pas** une
nouvelle couche. C'est un **test grandeur nature de la gouvernance** utilisant le noyau existant et
trois pièces minimales nouvelles (stub LLM, AgentRuntime borné, Quality Gate réel). Sa réussite
conditionne toute reprise du développement.
