# `aisos.reasoning` — Le raisonnement gouverné (E5)

Le LLM **raisonne** ; il ne devient jamais le cerveau de l'entreprise. Il vit derrière le contrat de
délibération existant (`DeliberationPort`, E1), alimenté par le port `LLMProvider` du cœur
(`aisos.llm`, ADR-0010). **Le CEO décide, l'orchestrateur gouverne, le Conseil recommande, la mémoire
informe ; le LLM raisonne.** Aucune décision, aucune écriture, aucune gouvernance ne lui appartient.

## Périmètre gelé — contrats de référence (E5 clôturé)

L'étape **E5 (le raisonnement gouverné)** est officiellement close. Les contrats produits par E5 sont
**gelés** et constituent la **fondation de raisonnement** d'AI-SOS — des références stables sur
lesquelles E6 (la fédération) s'appuiera sans les rouvrir :

- **Moteur de raisonnement** (`engine.py`) : `GovernedReasoningEngine` **branche** un vrai LLM
  derrière le `DeliberationPort` existant (implémenté **sans modifier son contrat**), alimenté par le
  port `LLMProvider` ; le LLM raisonne, il **ne décide jamais** (une décision tentée est **consignée
  puis ignorée**) ; indisponibilité ⇒ **escalade** conservatrice
  (`tests/unit/test_governed_reasoning_engine.py`).
- **Ancrage mémoire** (`grounding.py`) : `MemoryGroundedReasoningEngine` **ancre** le raisonnement
  dans un `MemoryContext` (E4) fourni **à la construction**, en **lecture seule** stricte ;
  `render_memory_context` en produit un rendu déterministe ; le contexte immuable n'est **jamais
  muté** et le `DeliberationPort` reste inchangé
  (`tests/unit/test_memory_grounded_reasoning.py`).
- **Bornage économique** (`budget.py`) : `BudgetBoundedReasoningEngine` **borne** tout
  `DeliberationPort` par un `ReasoningBudget` (jetons / coût / latence) ; **tout dépassement ⇒
  `ESCALATE` audité** (ADR-0009 A3), jamais une action ni une décision automatique — l'audit et la
  suspension restent la propriété de l'orchestrateur (`tests/unit/test_reasoning_budget.py`).
- **Traçabilité** (`trace.py`) : `ReasoningTracer` **produit** un `ReasoningTrace` immuable et
  déterministe **à partir du résultat** d'un raisonnement ; le **LLM n'écrit jamais** la trace ; le
  tracer observe sans ré-exécuter et n'implémente pas le `DeliberationPort`
  (`tests/unit/test_reasoning_trace.py`).

**Frontière raisonner / décider figée** : le **LLM raisonne** ; le **CEO décide**. L'orchestrateur
gouverne, le Conseil recommande, la mémoire informe. Le déterminisme d'audit (**record/replay**,
ADR-0010) garantit que tout raisonnement est reproductible **sans rappeler le modèle**. Le LLM
demeure **sans pouvoir** : aucune surface de décision, de gouvernance ni d'écriture.

**Toute évolution future de ces contrats doit respecter cette fondation de référence et ne peut être
réalisée que par une décision explicite du CEO.** Voir
[`../../../docs/reports/E5-REASONING-CLOSURE.md`](../../../docs/reports/E5-REASONING-CLOSURE.md).
