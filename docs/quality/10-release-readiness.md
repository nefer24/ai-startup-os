# Release Readiness

> Critères objectifs de passage en production d'AI-SOS : une barrière vérifiable qui éclaire une **décision du CEO**, jamais une promotion automatique — la CI vérifie, seul le CEO autorise le déploiement.

Ce document définit l'**architecture de validation du passage en production** de la Phase 12, sommet de la pyramide de qualité ([`./01-quality-overview.md`](./01-quality-overview.md)). Il n'écrit **aucun code** et n'introduit **aucun nouveau choix technologique** : il agrège, dans le strict respect de la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md) (décision 016) et des Phases 5–11, les résultats des domaines de qualité 02–09 et les aligne sur les gates par horizon de la roadmap ([`../implementation/10-development-roadmap.md`](../implementation/10-development-roadmap.md), [`../engineering/10-engineering-roadmap.md`](../engineering/10-engineering-roadmap.md)). Invariant directeur : **la CI vérifie, elle ne décide pas** ([`../engineering/06-ci-cd-strategy.md`](../engineering/06-ci-cd-strategy.md)) ; « déployer est une décision » réservée au CEO, jamais un effet de bord d'un automate. Aucun choix technologique nouveau : DT-01 à DT-08 restent des propositions à entériner (futures décisions 017+).

## Objectifs

- **Définir une barrière objective.** Rendre « le système est prêt » une affirmation **prouvée** et non déclarée, en agrégeant des critères vérifiables issus des domaines 02–09.
- **Réserver la décision au CEO.** Le passage en production est un **gate de décision du CEO**, éclairé par des critères vérifiables mais jamais automatique : une CI verte est une condition, pas une permission.
- **Prévenir toute promotion silencieuse.** Aucun automate — CI, token, agent — ne promeut vers `main` ni ne déploie ; la promotion et le déploiement relèvent de la validation explicite du CEO ([`../engineering/06-ci-cd-strategy.md`](../engineering/06-ci-cd-strategy.md)).
- **Consolider gouvernance, audit et sécurité.** Faire converger les preuves des domaines critiques (04, 05, 08, 09) en un verdict unique de go/no-go, où un seul gate rouge suffit à interdire la production.

## Scénarios

La revue de préparation (*readiness review*) s'exécute une fois par candidat de release, sur l'artefact gelé d'une branche `release/*` et en environnement de staging. Le tableau relie chaque scénario au verdict attendu.

| # | Scénario | Attendu observable |
| --- | --- | --- |
| R1 | Revue de préparation agrégeant les résultats des domaines 02–09 | Tableau de bord consolidé : chaque domaine « au vert » ou motif de blocage explicite ; aucun domaine critique non renseigné |
| R2 | Répétition des scénarios de bout en bout ([`../behavior/10-end-to-end-scenarios.md`](../behavior/10-end-to-end-scenarios.md)) en staging | Parcours nominaux et de gouvernance rejoués sur la pile de staging ; aucun chemin vers l'exécution sans validation CEO ou politique référencée |
| R3 | Validation des sauvegardes et de la restauration (DT-05, PITR) | Restauration effective démontrée ; après restauration, `verify_chain` valide de bout en bout ([`./09-audit-validation.md`](./09-audit-validation.md)) |
| R4 | Revue de sécurité (OIDC/JWT, least privilege DT-07, egress) | Refus des accès non autorisés confirmés ; secrets hors dépôt et hors logs ; tokens CI au minimum de privilèges |
| R5 | Vérification du mode dégradé (indisponibilité LLM / store) | Comportement **conservateur** : traitement suspendu et escaladé au CEO ; aucune décision engageante sans preuve d'audit |
| R6 | Calibration des bornes par le CEO ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) | Bornes en configuration versionnée, valeurs par défaut conservatrices, **approuvées par le CEO** avant production |

Extrait illustratif (verdict de readiness, non exécutable) :

```text
go_production = (gouvernance == 100%)
             et (audit_integrite == 100%)
             et (securite == vert) et (resilience == prouvee)
             et (issues_bloquantes == 0)
             et (bornes_approuvees_par_ceo == vrai)
             et (decision_ceo == accordee)   # jamais automatique
```

## Critères de réussite

Definition of Done de release — cases à cocher ; **toutes** requises avant toute production :

- [ ] **Gouvernance à 100 %** : tous les tests de gouvernance passants et bloquants ([`./05-governance-validation.md`](./05-governance-validation.md)).
- [ ] **Couverture au seuil** : globale ≥ 85 %, `core/domain` et `policies` ≥ 95 % ([`../engineering/06-ci-cd-strategy.md`](../engineering/06-ci-cd-strategy.md)).
- [ ] **Intégrité d'audit à 100 %** : chaîne vérifiable, complétude, aucune mutation réussie ([`./09-audit-validation.md`](./09-audit-validation.md)).
- [ ] **Résilience prouvée** : reprise après crash, mode dégradé conservateur, restauration PITR démontrée.
- [ ] **Sécurité validée** : OIDC/JWT, least privilege (DT-07), egress maîtrisé, secrets protégés.
- [ ] **Bornes calibrées et approuvées par le CEO** : en configuration versionnée, modifiables par le CEO seul.
- [ ] **Documentation d'exploitation** : procédures d'incident, restauration, alerte `audit.chain_broken`, mode dégradé.
- [ ] **Mode dégradé vérifié** : indisponibilité LLM/store → suspension et escalade, jamais de progression sans preuve.
- [ ] **Aucune issue bloquante ouverte** et dette connue documentée.
- [ ] **Décision de mise en production accordée par le CEO** (gate final, non délégable).

Chaque critère est **vérifiable**, adossé à un domaine 02–09 ; aucune couverture, aussi élevée soit-elle, ne compense un invariant non prouvé ou un gate critique rouge.

## Métriques

| Métrique | Définition | Sens |
| --- | --- | --- |
| Critères de release satisfaits | Nombre de cases cochées / total de la DoD de release | Progression vers le go/no-go |
| Issues bloquantes ouvertes | Nombre d'anomalies bloquantes non résolues | **Doit être 0** avant production |
| Dette connue documentée | Part de la dette technique identifiée et tracée ([`../implementation/10-development-roadmap.md`](../implementation/10-development-roadmap.md)) | Transparence sur les compromis assumés |
| Scénarios de bout en bout rejoués en staging | Part des scénarios de gouvernance repassés avec succès (R2) | Fidélité de la validation finale |
| Gates critiques au vert | Part des domaines gouvernance / audit / sécurité au vert | Condition de la décision CEO |

## Seuils de validation

> Seuils **canoniques**, cohérents avec l'ensemble des domaines 02–09 et les gates par horizon ([`../implementation/10-development-roadmap.md`](../implementation/10-development-roadmap.md)), à entériner par le CEO comme toute borne.

| Cible | Seuil | Statut |
| --- | --- | --- |
| Gates de gouvernance / audit / sécurité | **Tous au vert** | **Bloquant** |
| Gouvernance | 100 % passants | **Bloquant** |
| Intégrité d'audit | 100 % vérifiable | **Bloquant** |
| Issues bloquantes ouvertes | **0** | **Bloquant** |
| Résilience et mode dégradé | Prouvés (crash, PITR, indisponibilité) | **Bloquant** |
| Bornes calibrées | Approuvées par le CEO | **Bloquant** |
| Décision finale de mise en production | **Réservée au CEO** — aucune promotion automatique | **Bloquant** |

Rappel de gouvernance : franchir tous les gates rend un candidat **promouvable techniquement**, jamais **promu**. Trois barrières demeurent au-dessus de la CI — AI Review Package (décision 012), audit interne (décision 013) et **validation CEO** (règle 5 de la baseline) — et la promotion vers `main` comme le déploiement en production sont des décisions du CEO, jamais l'effet de bord d'un automate.

## Questions ouvertes (CEO)

1. **Critères de gate additionnels** : quels indicateurs mesurables supplémentaires le CEO exige-t-il pour franchir le gate de production, au-delà de la DoD proposée ?
2. **Cadence de release** : à quel rythme les candidats de release sont-ils produits et revus, et qui prépare la revue de préparation (agents consultatifs, sous validation CEO) ?
3. **Environnement de production** : quel choix d'hébergement (cloud / on-premise), OIDC de prod et stockage objet — question ouverte du plan MVP conditionnant l'étape de déploiement ?
4. **Périmètre bloquant au MVP** : quels domaines (06 performance, 07 résilience, 08 sécurité) sont bloquants dès le MVP et lesquels restent indicatifs jusqu'à l'Horizon 2 ([`./01-quality-overview.md`](./01-quality-overview.md)) ?
5. **Gestion de la dette assumée** : quel niveau de dette connue documentée le CEO tolère-t-il à la mise en production, et sous quelles conditions de suivi ?
