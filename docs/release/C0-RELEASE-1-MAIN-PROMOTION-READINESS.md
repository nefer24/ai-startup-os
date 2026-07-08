# C0-RELEASE.1 — Main Promotion Readiness

> **Repository :** `nefer24/ai-startup-os` · **Branche source de vérité :** `develop`
> **Statut :** C0 clôturé · Voie A post-C0 ouverte · **C1 non ouvert** · **E9 fermé**
> **Lot :** A1 — C0-RELEASE.1 Main Promotion Readiness. **Responsabilité unique : préparer.**
> **Nature :** revue documentaire et technique de **préparation** à la promotion éventuelle
> `develop → main`. **Ce lot ne promeut pas et ne modifie aucun code runtime.**

---

## Table des matières

1. Objet du document
2. État officiel avant A1
3. Pourquoi préparer la promotion `main`
4. Inventaire de ce qui doit être vérifié (checklist de readiness)
5. Différence entre readiness et promotion
6. Critères de promotion éventuelle
7. Risques avant promotion
8. Recommandation de Claude
9. Décision attendue du CEO
10. Boundary Check A1

---

## 1. Objet du document

Ce document **prépare la décision** de promotion éventuelle de la branche `develop` vers la branche
`main`. Il **vérifie**, **documente** et **cadre** cette éventualité.

Il **ne décide pas** et **n'exécute pas** la promotion. La promotion `develop → main` est une **action
Git/GitHub séparée et future**, réservée au CEO ; A1 se limite à **préparer** (readiness).

---

## 2. État officiel avant A1

- **C0 :** clôturé (revue officielle : PR #120, fusionnée).
- **Voie A post-C0 :** ouverte.
- **A0 — VOIE-A-OPENING :** fusionné (PR #121).
- **C1 :** non ouvert.
- **E9 :** fermé.
- **`develop` :** source de vérité.
- **`main` :** **non promu** (il ne contient que le commit initial).
- **A1 :** **préparation, pas promotion.**

---

## 3. Pourquoi préparer la promotion `main`

- **`develop` contient le socle complet C0** (C0.1 → C0.9 + C0.R + C0-CLOSURE + VOIE-A-OPENING).
- **`main` ne doit pas être promu sans vérification** : à ce jour, `main` ne contient que le commit
  initial, alors que `develop` est **262 commits en avance** (état constaté à la rédaction).
- **La promotion vers `main` est un acte de release / stabilisation**, pas de production réelle ni
  d'ouverture produit.
- **Elle ne doit pas être confondue avec l'ouverture C1/E9** : promouvoir `main` ne crée aucun objet
  produit actif, aucune factory, aucun LLM réel.
- **La promotion doit être précédée d'une checklist claire** (section 4) et d'une décision CEO
  explicite (sections 6 et 9).

---

## 4. Inventaire de ce qui doit être vérifié (checklist de readiness)

État **constaté à la rédaction** de ce document (source de vérité : `develop`). Cette checklist est
une **photographie de readiness**, à re-vérifier au moment d'une éventuelle promotion.

| # | Élément vérifié | État constaté |
| --- | --- | --- |
| 1 | PR C0.1 → C0.9 (fondations) | ✅ fusionnées dans `develop` (#110→#119) |
| 2 | PR C0.R — Realignment Debt Closure | ✅ fusionnée (#113) |
| 3 | PR C0-CLOSURE — revue de clôture C0 | ✅ fusionnée (#120) |
| 4 | PR VOIE-A-OPENING — ouverture Voie A | ✅ fusionnée (#121) |
| 5 | Documents de clôture présents | ✅ `docs/closure/` (`.md` + `.pdf` + `README.md`) |
| 6 | Documents de roadmap présents | ✅ `docs/roadmap/` (`.md` + `.pdf` + `README.md`) |
| 7 | `TRACEABILITY.md` à jour | ✅ sections C0.1→C0.9, C0.R, C0-CLOSURE, VOIE-A-OPENING présentes |
| 8 | Tests verts | ✅ `pytest` vert (~1780 tests, dont ~147 `governance`) |
| 9 | CI verte | ✅ job `quality` vert sur les dernières PR |
| 10 | Absence de divergence critique docs ↔ code | ✅ chaque lot C0 possède doc + module + tests cohérents |
| 11 | Absence d'ouverture E9 | ✅ E9 fermé (aucun étage produit ouvert) |
| 12 | Absence d'objet produit actif | ✅ `Problem`/`Idea`/`Objective`/`Solution`/`SolutionTeam` = concepts futurs |
| 13 | Absence de LLM réel | ✅ `llm_readiness` = contrats + replay hors ligne, aucun provider |
| 14 | Absence de DB/API/auth réelle non décidée | ✅ adaptateurs in-memory ; API/serveur/auth déclaratifs |
| 15 | Absence de workflow exécuté | ✅ `startup_workflows` = squelettes candidats, non exécutés |
| 16 | Cohérence de la branche `develop` | ✅ `develop` = tronc, `ruff`/`format`/`mypy` verts |

> Remarque : les éléments 8, 9 et 16 dépendent d'un instant ; ils doivent être **re-vérifiés** juste
> avant toute promotion réelle (voir sections 5 et 6).

---

## 5. Différence entre readiness et promotion

- **Readiness (A1)** = **vérifier**, **documenter**, **préparer**, **recommander**. C'est ce que fait
  ce lot : une photographie de l'état et un cadrage de la décision. **Aucune action Git de promotion.**
- **Promotion (future)** = **action Git/GitHub séparée** (par exemple une PR `develop → main`, ou une
  opération de release décidée), **future** et **décidée par le CEO**.
- **A1 ne fait pas la promotion.** Aucune commande de merge/rebase/force vers `main`, aucun script de
  promotion automatique n'est produit dans ce lot.
- **Une future PR ou action dédiée pourra être nécessaire** pour exécuter la promotion, une fois la
  décision CEO prise et les critères de la section 6 satisfaits.

---

## 6. Critères de promotion éventuelle

La promotion `develop → main` ne devrait être envisagée que si **tous** les critères suivants sont
satisfaits **au moment de la décision** :

1. **`develop` est vert** sur les gates qualité (`ruff` + `ruff format --check` + `mypy` + `pytest`).
2. **Tous les documents C0 et Voie A sont présents** (clôture, roadmap, traçabilité).
3. **Aucune dette bloquante de cohérence** entre documentation et code.
4. **`TRACEABILITY.md` est complet** (tous les lots tracés).
5. **La stratégie de branches est clarifiée** — ou explicitement identifiée comme relevant du lot
   **A2 — Branch & Release Governance** avant promotion.
6. **Le CEO accepte que `main` devienne la branche stable officielle** (décision explicite).
7. **Un plan de rollback ou de non-promotion est identifié** (que faire si la promotion doit être
   annulée ou reportée).

---

## 7. Risques avant promotion

- **Promouvoir trop tôt** — figer un socle avant qu'il ne soit réellement prêt ou avant la stratégie
  de branches (A2). *Mitigation : satisfaire les 7 critères de la section 6 avant toute promotion.*
- **Perdre le rôle de `develop` comme tronc de travail** — après promotion, il faut décider si
  `develop` reste le tronc de développement. *Mitigation : traiter ce point en A2.*
- **Confondre `main` stable avec production réelle** — `main` stable ≠ produit déployé. *Mitigation :
  documenter que la promotion est une release de socle, pas une mise en production.*
- **Donner l'impression que C1/E9 est ouvert** — une release pourrait être lue comme un lancement
  produit. *Mitigation : rappeler que la promotion ne crée aucun objet produit actif ; E9 reste
  fermé.*
- **Figer des docs incomplètes** — promouvoir avec une documentation lacunaire. *Mitigation : critère
  4 (traçabilité complète) + lot A4 (Operator Guide) si nécessaire.*
- **Créer une confusion entre release technique et produit actif** — la Voie A stabilise ; elle ne
  livre pas la fabrique de solutions. *Mitigation : garder la mission produit explicite.*

---

## 8. Recommandation de Claude

> **Recommandation consultative et argumentée — ce n'est pas une décision.**

**Recommandation technique.** L'état de readiness est **favorable** : les 16 points de la checklist
(section 4) sont satisfaits, les gates sont verts, la documentation est cohérente et `develop`
constitue un socle stable. Il n'y a **aucune dette bloquante** empêchant une future promotion.

**Recommandation stratégique.**

- **Si** les gates restent verts et la documentation cohérente au moment de la décision, **préparer
  une décision CEO de promotion** `develop → main`.
- **Ne pas promouvoir automatiquement dans A1** : la promotion reste une action séparée et future.
- **Faire d'abord A2 — Branch & Release Governance si la stratégie de branches doit être clarifiée**
  avant promotion (rôle de `develop` post-promotion, tags, notes de version, versioning). C'est le
  point le plus susceptible de manquer aujourd'hui.

**Séparation des rôles.**

- **Recommandation technique :** `develop` est prêt ; aucune dette bloquante.
- **Recommandation stratégique :** clarifier la gouvernance de branches (A2) avant, ou en parallèle
  de, la préparation de la promotion ; ne pas promouvoir dans A1.
- **Décision réservée au CEO :** autoriser (ou non) une future promotion et en fixer le moment.

---

## 9. Décision attendue du CEO

Après A1, le CEO devra **choisir** :

- [ ] **Option 1** — **Autoriser une future promotion `develop → main`** (exécutée par une action/PR
  dédiée ultérieure).
- [ ] **Option 2** — **Demander A2 — Branch & Release Governance** avant toute promotion.
- [ ] **Option 3** — **Maintenir `develop` comme source de vérité temporaire** (reporter la
  promotion).

**Formulation CEO possible :**

```text
Je prends acte de la readiness de promotion. Je demande d'abord le lot
A2 — Branch & Release Governance avant toute promotion de main.
```

---

## 10. Boundary Check A1

- Sommes-nous bien dans A1 ? **Oui**
- La responsabilité unique « préparer » est-elle respectée ? **Oui**
- C0 est-il clôturé ? **Oui**
- Voie A est-elle ouverte ? **Oui**
- C1 reste-t-il non ouvert ? **Oui**
- E9 reste-t-il fermé ? **Oui**
- `develop` reste-t-il source de vérité ? **Oui**
- `main` reste-t-il non promu dans ce lot ? **Oui**
- Aucun code runtime ajouté ? **Oui** (aucun `.py` modifié)
- Aucun objet produit actif créé ? **Oui**
- Aucune factory créée ? **Oui**
- Aucun LLM réel ajouté ? **Oui**
- Aucune DB/API/auth réelle ajoutée ? **Oui**
- Aucun workflow exécuté ? **Oui**
- La promotion reste-t-elle une décision CEO future ? **Oui**
- C0.1–C0.9 restent-ils inchangés ? **Oui**
- Les contrats E1–E8 restent-ils inchangés ? **Oui**

---

*A1 prépare la promotion `develop → main` sans l'exécuter. L'état de readiness est favorable ; la
décision — et l'action — restent réservées au CEO.*
