# Registre des risques — AI-SOS (consolidé, v2)

Registre unifié issu des deux revues stratégiques. Échelles : **Probabilité** et **Impact** sur
`Faible / Moyen / Élevé / Critique`. Chaque risque porte une **stratégie de mitigation** et des
**indicateurs de surveillance** mesurables. Le risque est **actif** tant que sa mitigation n'est
pas livrée et vérifiée.

## Carte thermique (impact × probabilité)

| | Proba Faible | Proba Moyenne | Proba Élevée | Proba Critique/Certaine |
| --- | --- | --- | --- | --- |
| **Impact Critique** | | R-ECO (N2) | | R-DET (N1) |
| **Impact Élevé** | | R-MIG (N5), R-SEC (N4) | R-CEO (N3), R-AUD, R-DOC | R-VAL |
| **Impact Moyen** | | R-DIV | R-TEST (N6), R-OVR | |

## Registre détaillé

### R-DET — Contradiction déterminisme ⟂ LLM
- **Probabilité** : Certaine (dès l'arrivée d'un LLM réel) · **Impact** : Critique
- **Description** : le non-déterminisme du LLM casse la promesse « rejouer le cheminement exact »
  et la capacité forensique.
- **Mitigation** : **ADR-0010** (registre record/replay ; rejeu ne rappelle jamais le modèle).
- **Indicateurs** : taux de *cache hit* en rejeu ; reproductibilité bit-à-bit d'un rejeu forensique ;
  nombre de rejeux ayant (à tort) rappelé le modèle (doit rester **0**).

### R-ECO — Emballement économique (coûts, boucles)
- **Probabilité** : Élevée · **Impact** : Critique
- **Description** : agent en boucle ou hors-budget → facture non bornée ; bornes typées mais non
  appliquées (0 `raise`).
- **Mitigation** : **ADR-0009** (budgets 3 niveaux appliqués, récursion, timeouts, ledger).
- **Indicateurs** : coût/demande ; coût/recommandation utile ; nb de récursions stoppées ; nb
  d'appels tronqués par timeout ; dépassements de plafond global.

### R-CEO — Le CEO comme goulot d'étranglement structurel
- **Probabilité** : Élevée (à l'échelle) · **Impact** : Élevé
- **Description** : toute décision structurante/critique + tout doute → CEO unique ; pas de modèle
  de débit décisionnel.
- **Mitigation** : modèle opérationnel HITL (files priorisées, mise en lot, SLA, délégation-sous-
  charge par politiques) — travail M5 ; à instruire (candidat ADR).
- **Indicateurs** : file d'attente de décisions CEO ; délai médian de décision ; taux d'escalade ;
  taux d'escalades *justifiées* (voir cadre de valeur).

### R-AUD — Divergence / double source de vérité d'audit
- **Probabilité** : Élevée (avec adaptateur réel) · **Impact** : Élevé
- **Description** : double écriture (moteur + UoW) → deux preuves potentiellement contradictoires.
- **Mitigation** : **ADR-0011** (source unique de vérité ; moteur en cache).
- **Indicateurs** : écarts détectés entre les deux ledgers (doit être **0** après ADR-0011) ;
  intégrité de la chaîne (`verify_chain`).

### R-DIV — Divergence des états d'exécution
- **Probabilité** : Moyenne · **Impact** : Moyen
- **Description** : `WorkflowState`, `LifecycleState` et représentations de pause peuvent diverger,
  faute d'invariant les liant.
- **Mitigation** : **ADR-0012** (état unifié ou projection explicite).
- **Indicateurs** : incohérences état orchestrateur ↔ état workflow détectées en test ; assertions
  de cohérence ajoutées au CI.

### R-SEC — Sécurité de contenu / injection de prompt
- **Probabilité** : Moyenne · **Impact** : Élevé
- **Description** : le RBAC gouverne l'autorité, pas le contenu ; risque d'injection de prompt et
  d'escalade par l'usage d'outils.
- **Mitigation** : **ADR-0013** (validation de sortie, frontière de confiance de contenu) — M5.
- **Indicateurs** : nb de sorties d'agent rejetées par validation ; tentatives d'usage d'outil hors
  manifest (doivent être bloquées + auditées).

### R-MIG — Évolution/migration de schéma append-only
- **Probabilité** : Moyenne · **Impact** : Élevé
- **Description** : append-only + évolution de schéma = gérer les anciennes versions pour toujours ;
  aucun test de compatibilité.
- **Mitigation** : **ADR-0014** (stratégie de migration + tests de compatibilité).
- **Indicateurs** : versions de schéma vivantes en base ; couverture des tests de compatibilité
  ascendante/descendante.

### R-VAL — Valeur métier non démontrée
- **Probabilité** : Certaine (aujourd'hui) · **Impact** : Élevé
- **Description** : le « cerveau » (agents/LLM) est à 0 % ; la gouvernance n'a jamais été éprouvée
  contre du travail réel.
- **Mitigation** : **Vertical Slice adverse** (M1) + [cadre de valeur](05-VALUE-METRICS-FRAMEWORK.md).
- **Indicateurs** : la gouvernance rattrape-t-elle chaque cas dégénéré ? ; utilité des
  recommandations sur banc gold ; coût par recommandation utile.

### R-TEST — Monoculture de test (fausse confiance)
- **Probabilité** : Élevée · **Impact** : Moyen
- **Description** : 99 % de couverture mais quasi exclusivement unitaire/déterministe/in-memory ;
  0 intégration, 0 propriété, 0 concurrence.
- **Mitigation** : ajouter tests d'intégration (M3), propriétés/fuzzing, concurrence UoW.
- **Indicateurs** : part des tests non-unitaires ; bugs trouvés par fuzzing ; anomalies de
  concurrence détectées.

### R-OVR — Sur-ingénierie / lenteur de mise en valeur
- **Probabilité** : Élevée · **Impact** : Moyen
- **Description** : plomberie spéculative (Event Bus sans abonné, modules vides) ; rituel lourd ;
  auto-audits toujours ~95.
- **Mitigation** : gel horizontal ; retrait des modules morts ; alléger le rituel ; **banc de
  valeur externe** (non auto-noté).
- **Indicateurs** : ratio valeur livrée / effort ; nb de composants sans usage réel ; écart entre
  auto-score et évaluation externe.

### R-DOC — Dérive documentaire
- **Probabilité** : Élevée · **Impact** : Élevé (érosion de la vérité)
- **Description** : docs/code ≈ 3,8:1 décrivant l'inexistant (LangGraph, pgvector, S3, OIDC, SSE).
- **Mitigation** : estampillage `CONSTRUIT/PARTIEL/PLANIFIÉ` ; réconciliation du corpus (M2/M6).
- **Indicateurs** : part des docs estampillés à jour ; nb de promesses documentaires non tenues ;
  liens cassés.

## Priorisation

**Bloc critique à mitiger dans la fenêtre de consolidation / Slice** : R-DET, R-ECO, R-AUD, R-VAL.
**Bloc à planifier** : R-CEO, R-SEC, R-MIG, R-DIV, R-TEST, R-OVR, R-DOC.

Aucun de ces risques n'invalide le noyau construit ; ils conditionnent le passage du **« ça
fonctionne en vase clos »** au **« ça crée de la valeur gouvernée en conditions réelles »**.
