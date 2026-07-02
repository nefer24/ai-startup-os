# ADR-0009 — Gouvernance économique (DT-09)

- **Statut** : Proposé (en attente de ratification CEO — porte M0)
- **Date** : 2026-07-02
- **Origine** : Revue stratégique n°2, risque N2 (« Absence de gouvernance économique »)
- **Décideur** : CEO (ratification requise) · **Instructeur** : Chief Software Architect
- **Portée** : `AgentRuntime`, `Orchestrator`, `Policy`, `Workflow`, futur `LLMProvider`

## Contexte

La gouvernance actuelle d'AI-SOS gouverne **l'autorité** (qui décide, qui recommande, qui exécute)
mais **pas l'économie** (combien coûte une exécution, combien de fois un agent peut boucler,
combien de temps il peut tourner). Trois faits mesurés le confirment :

1. Les types d'erreurs `AgentBudgetExceededError`, `WorkflowRecursionLimitError`,
   `WorkflowTimeoutError` **existent** dans `domain/errors.py` mais sont **appliqués 0 fois**
   (aucun `raise` dans le code métier).
2. Le manifest d'agent (Phase 17) borne les **outils, portées et egress**, mais son champ
   `token_budget` n'est **jamais vérifié** dans un chemin d'exécution (aucun `AgentRuntime`
   n'existe encore).
3. Aucun concept de **coût monétaire** (prix par token, plafond par demande, plafond global)
   n'est modélisé.

Le risque n°1 opérationnel d'un système agentique n'est pas l'autorité mais **l'emballement des
coûts et des boucles** : un agent qui s'auto-invoque sur une entrée ambiguë peut générer une
facture à quatre chiffres en une nuit, sans qu'aucun humain ne le voie. Une constitution de
l'autorité sans **constitution économique** est incomplète.

## Décision

AI-SOS se dote d'une **gouvernance économique** de premier ordre, **appliquée** (les bornes
lèvent une erreur et interrompent proprement), et non seulement déclarée. Elle repose sur cinq
mécanismes.

### 1. Budgets à trois niveaux

| Niveau | Borne | Défaut conservateur | Dépassement |
| --- | --- | --- | --- |
| **Par appel LLM** | `max_tokens`, `max_latency_ms` | fournis par le manifest | tronque / annule l'appel, audité |
| **Par agent / par demande** | `token_budget`, `cost_budget_eur`, `max_steps` | manifest + politique | `AgentBudgetExceededError` → escalade CEO |
| **Global (plateforme)** | plafond de coût horaire/journalier, taux d'appels | configuration CEO-only | dégradation contrôlée + alerte |

Règle : **un budget non déclaré vaut refus** (cohérent avec le least privilege de la Phase 17).
Un agent sans `token_budget` ne s'exécute pas.

### 2. Limite de récursion et de profondeur

Tout enchaînement d'auto-invocations ou de délégations est borné par `max_recursion_depth`.
Le dépassement lève `WorkflowRecursionLimitError`, **suspend** le workflow (état `paused_ceo` ou
`escalation.raised`) et **n'exécute jamais** un tour supplémentaire « en aveugle ».

### 3. Timeouts

Tout nœud à effet externe (appel LLM, appel d'outil) porte un `timeout`. Le dépassement lève
`WorkflowTimeoutError` ; le workflow est **suspendu**, jamais ré-exécuté silencieusement (cohérent
avec la stratégie de checkpointing : « pas d'effet non idempotent rejoué en aveugle »).

### 4. Comptabilité des ressources (ledger économique)

Chaque appel LLM produit une **entrée de consommation** (tokens in/out, coût estimé, latence,
modèle) rattachée à la demande et **auditée**. Le coût réel d'une décision devient une donnée de
première classe, base de la métrique « coût par recommandation utile »
(voir [cadre de valeur](../consolidation/05-VALUE-METRICS-FRAMEWORK.md)).

### 5. Point d'application

Les bornes sont **câblées dans l'`AgentRuntime` dès sa première ligne** (Vertical Slice n°1),
et vérifiées par le Policy Engine au routage. Aucune borne ne peut être contournée par un chemin
alternatif : c'est un **invariant de gouvernance**, prouvé par test (le stub LLM « hors-budget »
doit être arrêté et escaladé).

## Conséquences

**Positives**
- Le risque financier n°1 est **borné et observable**.
- Le coût devient mesurable → la valeur métier peut être rapportée au coût (utilité/€).
- Les erreurs déjà typées sont enfin **appliquées** : cohérence code ↔ intention.

**Négatives / coûts**
- L'`AgentRuntime` doit intégrer la comptabilité dès le départ (léger surcoût de conception).
- Les bornes par défaut trop serrées peuvent sur-escalader ; à calibrer (seuils = CEO-only).

**Invariants ajoutés**
- *Aucune exécution sans budget déclaré.*
- *Aucun tour supplémentaire au-delà d'une borne — suspension et escalade, jamais rejeu aveugle.*
- *Toute consommation LLM est auditée.*

## Alternatives écartées

- **Bornes advisory (log seulement).** Rejeté : ne stoppe pas l'emballement ; le risque demeure.
- **Budget global uniquement.** Rejeté : un seul agent fautif peut épuiser le plafond commun ;
  il faut des bornes par agent/demande.
- **Reporter à la mise en production.** Rejeté : le coût de câbler ces bornes est faible tant
  qu'aucun LLM réel n'est branché, et élevé une fois qu'il l'est (voir registre des risques, N2).

## Suivi

- **Indicateurs** : coût par demande, coût par recommandation utile, taux d'escalade pour
  dépassement de budget, nombre de récursions stoppées, part des appels tronqués par timeout.
- **Test d'acceptation** (Vertical Slice) : un agent en boucle et un agent hors-budget sont
  **arrêtés et escaladés** ; l'audit consigne la consommation.
- **Dépendance** : DT-03 (LLMProvider) et ADR-0010 (déterminisme LLM) pour la comptabilité réelle.
