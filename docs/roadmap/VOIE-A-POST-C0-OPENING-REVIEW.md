# VOIE A POST-C0 — Revue officielle d'ouverture

> **Repository :** `nefer24/ai-startup-os` · **Branche source de vérité :** `develop`
> **Statut :** C0 clôturé · **Voie A post-C0 ouverte** · **C1 non ouvert** · **E9 fermé**
> **Lot :** VOIE-A-OPENING — Revue d'ouverture officielle de la Voie A post-C0. **Responsabilité unique : cadrer.**
> **Nature :** document d'ouverture officielle, cahier des charges et roadmap. **Aucune implémentation runtime.**

---

## Table des matières

1. Décision CEO d'ouverture
2. Statut officiel après C0
3. Raison d'être de la Voie A post-C0
4. Ce que la Voie A autorise
5. Ce que la Voie A interdit
6. Roadmap proposée de la Voie A post-C0
7. Cahier des charges de la Voie A
8. Boundary Check global de la Voie A
9. Risques
10. Recommandation de Claude
11. Décision attendue du CEO
12. Conclusion

---

## 1. Décision CEO d'ouverture

Le CEO a acté officiellement :

> « En tant que CEO, je déclare officiellement la clôture de C0 et l'ouverture officielle de la
> Voie A post-C0. »

**Portée exacte de cette phrase :**

- Elle **clôt officiellement C0** (la phase de consolidation du socle E1–E8, dont la revue de clôture
  officielle est la PR #120, fusionnée dans `develop`).
- Elle **ouvre officiellement la Voie A post-C0** (phase de **stabilisation / release readiness** du
  socle consolidé).
- Elle **n'ouvre pas C1** (la phase produit).
- Elle **n'ouvre pas E9** (la fabrique gouvernée d'équipes IA / objets produit actifs).

Autrement dit, cette décision **change de phase** (de « consolidation » vers « stabilisation ») **sans
franchir la frontière produit**. La Voie A prépare, durcit et documente ; elle ne construit aucune
capacité métier nouvelle.

---

## 2. Statut officiel après C0

- **C0 :** clôturé.
- **Voie A post-C0 :** ouverte.
- **C1 :** non ouvert.
- **E9 :** fermé.
- **Source de vérité :** la branche `develop`.
- **`main` :** **non promu** (la promotion `develop → main` relève d'une décision future, préparée mais
  non exécutée dans ce lot).
- **Prochaine phase de travail :** **stabilisation / release readiness** (durcir, documenter, préparer
  la promotion et l'infrastructure non-métier), lot par lot, chacun sous validation CEO.

---

## 3. Raison d'être de la Voie A post-C0

C0 a produit un **socle complet mais encore déclaratif** : visible, exposable, persistant, réaligné,
sécurisé, décidable, traçable, mémorisable, prêt pour une assistance LLM contrôlée, et capable de
représenter des workflows minimaux — le tout en modèles immuables, déterministes, avec adaptateurs
**in-memory**.

La **Voie A** sert à transformer ce socle « prouvé mais déclaratif » en un socle **stable, publiable et
techniquement prêt**, sans franchir la frontière produit. Concrètement, elle vise à :

- **stabiliser** le socle (cohérence globale, absence de dette bloquante) ;
- **vérifier la cohérence globale** (traçabilité, invariants, documentation) ;
- **préparer une release propre** (versioning, notes de version, stratégie de branches) ;
- **préparer éventuellement la promotion `develop → main`** (readiness, pas exécution) ;
- **durcir l'infrastructure non-métier** si le CEO le décide (DB/API lecture/auth **en préparation**,
  puis en lots dédiés) ;
- **préparer la future ouverture C1/E9 sans l'ouvrir maintenant** (garder la porte fermée, mais le
  socle prêt).

**Mission product alignment :** un socle stable, publiable, auditable et techniquement prêt **protège
la future fabrique de solutions et d'équipes IA spécialisées** — on consolide le cadre avant d'ouvrir
la production, pour ne pas fragiliser la mission.

---

## 4. Ce que la Voie A autorise

La Voie A peut autoriser, **lot par lot**, **après PROMPT OFFICIEL et validation CEO** :

- une **revue de release readiness** ;
- un **audit documentaire de cohérence** ;
- la **préparation de la promotion `develop → main`** (readiness et plan, pas exécution automatique) ;
- la **clarification de la stratégie de branches** (`develop`, `main`, tags) ;
- le **packaging** ;
- le **versioning** ;
- le **durcissement CI / qualité** (quality gate hardening) ;
- la **documentation utilisateur / technique** ;
- le **choix d'adaptateurs d'infrastructure non-métier** ;
- une **vraie DB uniquement comme adaptateur d'un contrat existant** (C0.3), **si lot dédié** ;
- un **serveur API réel en lecture uniquement** (basé sur C0.2), **si lot dédié** ;
- une **auth réelle uniquement comme adaptateur de C0.4**, **si lot dédié** ;
- une **observabilité technique non-métier**, **si lot dédié**.

> Principe : tout ce qui est « réel » (DB, API, auth, observabilité) reste un **adaptateur d'un contrat
> C0 déjà existant**, jamais une capacité métier nouvelle, et jamais dans le lot d'ouverture actuel.

---

## 5. Ce que la Voie A interdit

La Voie A **interdit explicitement** :

- l'**ouverture de C1** ;
- l'**ouverture de E9** ;
- les **objets produit actifs** : `Problem`, `Idea`, `Objective`, `Solution`, `SolutionVersion`,
  `SolutionTeam`, `ImprovementOpportunity` ;
- les **factories** : `SolutionTeamFactory`, `ProjectTeamFactory`, `AIOrganizationFactory` ;
- tout **workflow exécuté** ;
- tout **agent actif** ;
- tout **orchestrateur actif** ;
- tout **LLM réel de production** ;
- tout **RAG, embeddings, vector store** ;
- toute **création ou amélioration réelle de solution** ;
- toute **décision automatique** ;
- toute **application automatique** ;
- toute **mutation métier** ;
- tout **déploiement produit** ;
- tout **franchissement produit sans décision CEO séparée**.

---

## 6. Roadmap proposée de la Voie A post-C0

Roadmap **ordonnée**, chaque lot ayant **une responsabilité unique**. Elle est **consultative** : le
CEO valide chaque lot par un PROMPT OFFICIEL dédié avant implémentation.

| Lot | Titre | Responsabilité unique | Nature | But |
| --- | --- | --- | --- | --- |
| **A0** | VOIE-A-OPENING | **cadrer** | Revue d'ouverture + cahier des charges + roadmap | Ouvrir officiellement la Voie A sans implémentation runtime (**ce document**). |
| **A1** | C0-RELEASE.1 Main Promotion Readiness | **préparer** | Documentaire + checks + plan de promotion | Vérifier si `develop` peut devenir la base officielle à promouvoir vers `main`. |
| **A2** | C0-RELEASE.2 Branch & Release Governance | **organiser** | Docs + config minimale si nécessaire | Définir stratégie `develop`/`main`, tags, notes de version, versioning. |
| **A3** | C0-RELEASE.3 Quality Gate Hardening | **durcir** | CI, checks, scripts qualité | Renforcer CI/qualité sans modifier le runtime métier. |
| **A4** | C0-RELEASE.4 Documentation & Operator Guide | **documenter** | Docs | Rendre le socle compréhensible/exploitable par un développeur/opérateur. |
| **A5** | C0-INFRA.1 Persistence Adapter Readiness | **préparer** | Design doc / contrats / choix technique | Préparer l'arrivée éventuelle d'une vraie DB comme adaptateur de C0.3. |
| **A6** | C0-INFRA.2 Read API Server Readiness | **préparer** | Design doc / choix framework / contraintes | Préparer un serveur API réel **en lecture** basé sur C0.2. |
| **A7** | C0-INFRA.3 Auth Adapter Readiness | **préparer** | Design doc / choix JWT/OAuth/… | Préparer l'auth réelle comme adaptateur de C0.4. |
| **A8** | VOIE-A-CLOSURE | **clôturer** | Revue de clôture | Clôturer la Voie A et préparer une décision CEO : rester en infra, promouvoir `main`, ou ouvrir C1/E9. |

**Interdictions spécifiques par lot :**

- **A1** — ne pas promouvoir réellement si la promotion demande une PR/décision séparée.
- **A2** — pas de comportement métier.
- **A3** — pas de nouvelle capacité produit.
- **A4** — pas de runtime.
- **A5/A6/A7** — pas de DB / serveur / auth **réels** dans ces lots ; uniquement **readiness** (design,
  contrats, choix). Le réel viendra, le cas échéant, dans un lot futur explicitement décidé.
- **A8** — ne pas ouvrir C1 automatiquement.

**Justification de l'ordre (inchangé par rapport à la proposition).** La séquence part de la
**release readiness** (A1→A4 : promotion, gouvernance de branches, qualité, documentation) parce
qu'elle sécurise et rend publiable **ce qui existe déjà**, sans coût d'infrastructure. Elle poursuit
par la **readiness d'infrastructure** (A5→A7 : DB, API lecture, auth **en préparation seulement**),
qui prépare le « réel » sans le construire. Elle se termine par une **clôture** (A8) qui remet au CEO
la décision de direction suivante. L'inspection du dépôt ne révèle aucune raison de réordonner : la
release readiness ne dépend d'aucune infrastructure réelle, et la readiness d'infrastructure gagne à
s'appuyer sur une stratégie de branches/versioning déjà clarifiée (A2). **L'ordre proposé est donc
conservé.**

---

## 7. Cahier des charges de la Voie A

### Objectifs

- Stabiliser et rendre **publiable** le socle C0 (sans capacité métier nouvelle).
- Clarifier la **stratégie de branches / release / versioning**.
- Préparer (readiness) la **promotion `develop → main`** et l'**infrastructure non-métier**.
- Préserver **tous les garde-fous** C0 et garder **E9 fermé**.
- Préparer une **décision CEO** claire pour la suite (rester en infra, promouvoir, ou ouvrir C1/E9).

### Livrables (par lot, sous validation CEO)

- Revues et plans documentaires (A1, A2, A4, A8).
- Durcissement CI/qualité (A3).
- Design docs / contrats / choix techniques d'infrastructure (A5, A6, A7).

### Critères de réussite

- **C0 documenté et stabilisé.**
- **Branch strategy clarifiée.**
- **Release readiness documentée.**
- **Qualité CI stable.**
- **Documentation suffisante** pour reprise par un développeur.
- **Aucune ouverture E9.**
- **Aucune création d'objet produit actif.**
- **Aucun comportement métier introduit.**
- **Décision CEO préparée** pour la suite.

### Limites et non-objectifs

- **Non-objectif :** créer une capacité produit, un objet produit actif, une factory, un LLM réel, une
  exécution de workflow.
- **Non-objectif :** promouvoir `main` automatiquement.
- **Non-objectif :** construire une DB / API / auth **réelles** dans les lots de *readiness* (A5–A7).
- **Limite :** chaque lot reste **additif, isolé, à responsabilité unique**, et **ne modifie pas** le
  comportement runtime existant.

---

## 8. Boundary Check global de la Voie A

- Voie A ouverte ? **Oui**
- C0 clôturé ? **Oui**
- C1 non ouvert ? **Oui**
- E9 fermé ? **Oui**
- Aucun objet produit actif ? **Oui**
- Aucune factory ? **Oui**
- Aucun LLM réel ? **Oui**
- Aucun workflow exécuté ? **Oui**
- Aucune décision automatique ? **Oui**
- Aucune application automatique ? **Oui**
- `develop` reste source de vérité ? **Oui**
- Promotion `main` non automatique ? **Oui**
- Chaque futur lot aura-t-il une responsabilité unique ? **Oui**
- Chaque futur lot demandera-t-il une validation CEO ? **Oui**

---

## 9. Risques

- **Glisser vers C1 sans décision** — une readiness d'infrastructure (A5–A7) pourrait être interprétée
  comme une autorisation d'ouvrir le produit. *Mitigation : chaque lot est readiness-only, C1/E9 exige
  une décision CEO séparée.*
- **Faire de l'infrastructure une nouvelle finalité** — investir dans DB/API/auth au point d'oublier
  que ce ne sont que des adaptateurs au service de la mission. *Mitigation : rappeler que la
  gouvernance et l'infra sont des cadres, pas la finalité.*
- **Confondre release readiness et produit actif** — croire qu'une release C0 « livre le produit ».
  *Mitigation : la release publie un socle, pas une solution.*
- **Promouvoir `main` trop tôt** — figer un socle avant qu'il ne soit réellement prêt. *Mitigation :
  A1 est une readiness ; la promotion réelle est une décision/PR séparée.*
- **Créer un serveur / DB / auth réels avant cadrage** — court-circuiter A5–A7 (design) en sautant au
  réel. *Mitigation : le réel n'arrive qu'après un lot dédié explicitement décidé.*
- **Perdre la mission produit sous la documentation** — sur-documenter au détriment de la trajectoire
  vers la fabrique de solutions. *Mitigation : garder la Voie A courte et orientée readiness, puis
  rendre la main au CEO (A8).*

---

## 10. Recommandation de Claude

> **Recommandation consultative et argumentée — ce n'est pas une décision.**

**Recommandation technique.** Le socle C0 est stable, sans dette bloquante. La priorité la plus utile
et la moins risquée est de **sécuriser et rendre publiable ce qui existe déjà** avant d'investir dans
de l'infrastructure réelle.

**Recommandation stratégique.** Je recommande de **commencer par A1 — C0-RELEASE.1 Main Promotion
Readiness**. Vérifier objectivement si `develop` peut devenir la base à promouvoir vers `main`
constitue le socle de tous les lots suivants (gouvernance de branches, versioning, documentation), et
n'engage aucun coût d'infrastructure. Les lots d'infrastructure (A5–A7) ne devraient être abordés
qu'après la release readiness, et rester en **design/readiness** jusqu'à décision CEO.

**Séparation des rôles.**

- **Recommandation technique :** stabiliser/publier l'existant avant l'infra réelle.
- **Recommandation stratégique :** démarrer par **A1**, garder A5–A7 en readiness, clôturer par A8.
- **Décision réservée au CEO :** le choix du prochain lot, et — à terme — l'ouverture éventuelle de
  C1/E9.

---

## 11. Décision attendue du CEO

Pour poursuivre, le CEO devra **valider le premier lot de la roadmap** :

> **A1 — C0-RELEASE.1 Main Promotion Readiness** (responsabilité unique : *préparer*).

Ce lot sera cadré par un **PROMPT OFFICIEL** dédié (rédigé avec Orion), implémenté par Claude sur une
branche, ouvert en PR vers `develop`, **sans fusion** avant la validation explicite du CEO.

**Formulation CEO possible :**

```text
Je valide l'ouverture de la Voie A post-C0. Je demande le démarrage du lot
A1 — C0-RELEASE.1 Main Promotion Readiness.
```

---

## 12. Conclusion

- **C0 est clôturé.**
- **La Voie A post-C0 est ouverte.**
- **C1 n'est pas ouvert.**
- **E9 reste fermé.**
- **Prochaine étape recommandée : A1 — C0-RELEASE.1 Main Promotion Readiness.**

La Voie A est une phase de **stabilisation / release readiness** au service de la mission : elle rend
le socle stable, publiable et prêt, **sans franchir la frontière produit**, et remet au CEO — à sa
clôture — la décision de direction suivante.
