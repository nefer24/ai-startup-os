# Roadmap révisée — orientée validation

Cette roadmap remplace toute logique d'empilement horizontal. Son unique objectif :
**convertir la valeur potentielle de la fondation en valeur prouvée**, en dé-risquant les
hypothèses dans l'ordre de leur danger. Chaque étape a un **critère de succès mesurable** ; on ne
passe pas à la suivante sans lui.

## Principe directeur

> On n'ajoute plus de couche. On **prouve** que le moteur fonctionne — d'abord en conditions
> adverses, puis avec des adaptateurs réels, puis sous charge. La valeur métier devient une
> dimension de mesure au même titre que la robustesse technique.

## Phases

### M0 — Porte de ratification *(≈ 2 semaines) · BLOQUANT*
- Ratifier ADR-0009, ADR-0010, ADR-0011 (bloc P1) et les DT-02/DT-03/DT-08.
- Ratifier « en principe » DT-01/04/05/06/07 ; ouvrir ADR-0012→0015.
- Estampiller la documentation `CONSTRUIT / PARTIEL / PLANIFIÉ`.
- Formaliser le gel de l'expansion horizontale.
- **Succès** : ADR P1 `Accepté` ; périmètre technique figé ; aucun code de Slice avant cette porte.

### M1 — Vertical Slice adverse v1 *(le cœur de la validation)*
- Port `LLMProvider` + **stub déterministe à modes dégénérés** (mode `stub` d'ADR-0010).
- `AgentRuntime` **borné** (manifest + budgets ADR-0009 + récursion + timeouts), appliqués.
- Production d'une `Recommendation` (jamais une décision).
- **Quality Gate réel** (remplace le stub).
- Câblage complet : Orchestrateur → Policy → CEO → Audit → Persistence.
- **Succès** : la gouvernance **refuse ou escalade** chaque cas dégénéré (vide, faible, hors-budget,
  boucle, timeout). Voir [plan détaillé](04-VERTICAL-SLICE-01-PLAN.md).

### M2 — Consolidation ciblée
- **Audit source unique de vérité** (ADR-0011).
- **Registre de rejeu LLM** opérationnel (ADR-0010, modes record/replay).
- Retrait/conversion des modules morts (D9) ; décision Event Bus (D8).
- **Succès** : une seule preuve d'audit ; rejeu déterministe démontré malgré un LLM.

### M3 — Premier adaptateur réel + diversification des tests
- Choisir l'adaptateur le plus dé-risquant : **LLMProvider réel** (derrière le registre de rejeu)
  **ou** **persistance PostgreSQL**.
- Ajouter tests **d'intégration**, **de propriétés/fuzzing**, **de concurrence** (UoW) — traite D13.
- **Succès** : un adaptateur réel **passe la Slice adverse** ; les nouveaux types de tests tournent.

### M4 — Transport minimal + observabilité + coûts
- Un point d'entrée réel **mince** (CLI ou adaptateur HTTP) au-dessus de la couche Application.
- Application effective de la comptabilité économique (ADR-0009) + observabilité (DT-06).
- **Succès** : démo end-to-end reproductible qu'un humain peut lancer ; coûts bornés et observables.

### M5 — Durcissement
- Sécurité adverse : frontière d'injection de prompt + validation de sortie (ADR-0013, R-SEC).
- Migration/évolution de schéma + tests de compatibilité (ADR-0014, R-MIG).
- Modèle opérationnel de débit décisionnel CEO / HITL (R-CEO).
- Test de charge/soak de la boucle agentique.
- **Succès** : le système résiste à l'adversaire et à la charge.

### M6 — Consolider & décider
- Go/No-Go trajectoire production ; réconciliation documentaire finale.
- Décision **éclairée** sur les conseils / multi-agents (l'ambition différée), à la lumière de ce
  que la Slice a enseigné.
- **Re-scoring** du projet (les trois lentilles : fondation / produit / position stratégique).
- **Succès** : décision d'expansion fondée sur des preuves, pas des espoirs.

## Vue calendaire

| Chantier | M0 | M1 | M2 | M3 | M4 | M5 | M6 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ratification ADR / DT | ██ | | | | | | |
| Vertical Slice adverse | | ████ | ██ | | | | |
| Consolidation (audit, rejeu) | | | ████ | ██ | | | |
| Adaptateur réel + tests | | | | ████ | ██ | | |
| Transport + coûts + observabilité | | | | | ████ | ██ | |
| Durcissement (sécurité, migration, HITL) | | | | | | ████ | ██ |
| Go/No-Go + re-scoring | | | | | | | ██ |

## Ce qui reste explicitement HORS roadmap immédiate

- Nouvelles couches horizontales (composition root exclue jusqu'à M4, conseils multi-agents jusqu'à
  M6, transports complets jusqu'à M4).
- Grand refactor : les redondances P2 sont **planifiées**, pas traitées en urgence.
- Toute fonctionnalité qui n'aide pas à **prouver la valeur gouvernée**.
