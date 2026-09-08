# AI Review Package

**Pull Request :** #144 — *OT-V1 — Incrément 2 : délibération probante → recommandation décisionnelle*
**Branche :** `product/increment-2` (créée depuis `product/mvp` au freeze v3.1 `d2931a7`) → `develop`
**Auteur :** Claude Code (Chief System Architect)
**Date :** 2026-09-08 (ARP v1)
**Commits :** départ `d2931a7` (PR #143, freeze v3.1 + ARP) → **INCREMENT 2 CODE FREEZE v1** (commit identifié dans le message de commit)

> **Note de périmètre.** La PR #143 (incrément 1) n'est pas encore fusionnée dans `develop`. Pour ne pas altérer son diff audité, l'incrément 2 est porté par une branche distincte. Tant que #143 n'est pas fusionnée, le diff GitHub de cette PR vers `develop` inclut les commits de l'incrément 1 ; le diff **propre à l'incrément 2** est `product/mvp...product/increment-2`. Ordre de fusion attendu : #143 puis #144 (la PR se réduit alors automatiquement à l'incrément 2). Aucune fusion sans ordre explicite du CEO.

## 1. Executive Summary

L'incrément 1 rassemblait la matière (cadrage, composition émergente, Tour 0 isolé, cartographie) et s'interdisait toute recommandation. L'incrément 2 ajoute la **délibération probante** et la **recommandation décisionnelle** : confrontation adressée → steelman reconnu (ou strawman refusé) → recherche ciblée quand un fait vérifiable est en jeu → révision sous preuve → familles stratégiques → comparaison sur critères communs → synthèse en 14 champs → porte qualité indépendante. Les agents **recommandent**, le CEO **décide** (Décision 026) : le rapport reste `candidate`, `structurante` / `critique` reviennent obligatoirement au CEO, un désaccord de valeurs lève un arbitrage CEO, aucune exécution n'existe. Le budget devient **adaptatif** avec des **plafonds durs par classe**, un plan de composition à deux niveaux, un cycle minimal vérifié avant de délibérer et une priorité explicite (largeur du Tour 0 → confrontation → étapes optionnelles → cœur de synthèse) ; toute impossibilité produit un **arrêt partiel explicite avec demande de budget chiffrée**, jamais une relance ni une fausse couverture. **401 tests verts** (377 historiques + 24 scénarios synthétiques), lint / format / typage verts (produit et racine). Aucun problème scellé n'a été demandé, consulté ni reconstruit. **V1 n'est pas terminé** : T16 (classification), protocole de profondeur, mémoire inter-missions et exécution restent hors périmètre.

**Un écart doctrinal est déclaré et soumis au CEO** (§7, §13) : les plafonds par défaut de `courante` (16 appels / 1,50 €) et `importante` (30 / 3 €) sont **supérieurs** aux a priori du document canonique §6.1 (≤ 4 / < 0,10 € ; ≤ 15 / 0,3 à 1 €). Cause : le cycle minimal de cet incrément (cadrage à 8 000 tokens de sortie depuis la correction de troncature, exposés, confrontation, consolidation, comparaison, synthèse, porte) ne tient pas dans ces a priori ; le majorant pré-appel refuserait même le cadrage sous 0,10 €. Les valeurs sont configurables ; seul le CEO assouplit ou ramène.

## 2. Objectifs

Améliorer de façon mesurable **T06, T07, T08, T09, T10, T11** (mandat) en préservant **T02, T04, T05, T12, T13, T14, T15, T23, T25, T26**. Aucune réarchitecture : extension additive du pipeline de l'incrément 1.

## 3. Fichiers modifiés

Ajoutés : `product/app/mission_deliberation.py` (prompts + règles déterministes : carte, contradicteur, convergence prématurée, strawman, questions factuelles matérielles), `product/app/mission_research.py` (`ResearchProvider`, `UnavailableResearchProvider`, `AnthropicWebSearchProvider`, `build_research_provider`), `product/tests/test_missions_deliberation.py` (24 scénarios), `reviews/packages/PR-144-otv1-increment-2.md`.
Modifiés : `product/app/missions.py` (huit étapes de délibération, plan budgétaire, cycle minimal, réserve de synthèse, arrêt et charge utile de délibération), `mission_budget.py` (`CALLS_PER_EXPERT = 3`, `SYNTHESIS_CORE_CALLS`, `class_ceilings`, `plan_budget`, `reserved_downstream_calls`, `raise_caps`), `mission_schemas.py` (schémas de confrontation, steelman, reconnaissance, révision, consolidation, comparaison, recommandation 14 champs, porte ; `FORBIDDEN_COMPARISON_FIELDS`), `mission_report.py` (14 champs remplis depuis la recommandation, sections 15–16, rendu), `config.py` (plafonds par classe, fournisseur de recherche, `max_tokens` des nouveaux appels ; retrait de `mission_max_llm_calls` / `mission_max_cost_eur`), `db.py` (`deliberation_json`, `recommendation_json`, ajout idempotent), `schemas.py` (`MissionOut.deliberation` / `.recommendation`), `product_status.py` (1 capacité), `ui/streamlit_app.py` (plafonds de classe par défaut, surcharge optionnelle, encart de recommandation), `product/README.md`, `TRACEABILITY.md`, `tests/test_missions_otv1.py` et `tests/test_missions_truncation.py` (faux clients étendus aux nouveaux types d'appel ; assertions de budget adaptées aux plafonds par classe).
**Aucun fichier de `src/`, des `docs/` gelés, ni des 32 agents historiques modifié.**

## 4. Changements importants

- **Confrontation (C)** : chaque expert reçoit la carte sans sa propre position ; actes `critique` / `defend` / `complement` / `refute` / `third_way` / `none`, typés `solution` / `hypothesis` / `fact` / `value` / `other`, adressés à un label P-n résolu en expert ; registre d'objections `OBJ-n` (`open` / `addressed` / `inadmissible_strawman`). `none` + `convergence_note` est un résultat légitime ; aucune opposition n'est fabriquée ; un appel = une perspective (jamais une instance multi-persona).
- **Steelman (D)** : requis par classe (`structurante` / `critique`) ou par **convergence prématurée** (aucune objection, divergence 0, classe ≥ importante). Contradicteur hors de la position dominante (angle critique de préférence, repli journalisé si unanimité). Trois objets séparés : steelman, forces + scénarios d'échec, critique. Reconnaissance par le tenant (`yes` / `partial` / `no`). `strawman_flags` déterministes (texte < 80 caractères, aucune force, identique à la critique, vocabulaire dépréciatif). Refus ⇒ `rejected_strawman`, critique `inadmissible_strawman` (ni résiduelle ni cause de révision), porte `steelman_done_if_required = false`.
- **Recherche ciblée (E)** : déclenchée uniquement par un acte `depends_on_fact` avec `fact_question`, ou une objection typée « fait » du Tour 0 ; dédoublonnage, plafond `MISSION_MAX_RESEARCH_TASKS` (3). Fournisseur remplaçable : `none` (défaut) ⇒ `unavailable`, **aucun appel, aucun coût**, inconnue déclarée ; `anthropic_web_search` ⇒ seules les citations réelles sont conservées (`not_found` sinon ; `error` en cas de panne), usage compté au registre et journalisé (`llm_call_logs`, `call_type = research`). Champs : question, source, date, extrait, fiabilité (`unknown` par défaut, jamais inventée), claim, positions. Provenance des preuves : `ceo_input` / `external` / `model_knowledge` / `inference` / `hypothesis` (les preuves du Tour 0 sont mappées : `verified` → `ceo_input`, `model_knowledge`, sinon `hypothesis`).
- **Révision (F)** : appel seulement en présence d'information nouvelle (objection adressée, critique de steelman reconnue, preuve `found`) ; sinon entrée `called = false`, journal `no_new_information`. `maintain` / `modify` / `nuance` / `abandon`, `triggered_by` obligatoire pour changer ; `unexplained_change` sinon. Tour 0 immuable ; `positions_after` séparées. Le prompt interdit le changement sous insistance et le changement « pour faire plaisir ».
- **Consolidation (G)** : greffier au schéma fermé + normalisation déterministe : identifiants inconnus ignorés, **scission des familles mêlant des natures différentes** (`greffier+scission`, note journalisée), singletons conservés, variantes et désaccords intra-famille visibles, `not_merged_because` transmis, trace atomique → famille → variante.
- **Comparaison** : critères communs (noyau + spécifiques), appréciation qualitative + base ; schéma sans `score` / `rank` / `winner` / `best` (attesté par test) ; familles non évaluées marquées ; le nombre de soutiens n'est pas un critère.
- **Synthèse (14 champs)** : synthétiseur distinct ; kinds `build` / `buy` / `integrate` / `simplify` / `test` / `wait` / `do_nothing` / `abandon` / `other` ; `information_insufficient` ⇒ `decision_ready = false` ; **réinjection déterministe** des désaccords résiduels du facilitateur ; drapeaux `requires_ceo_decision` (toujours vrai), `ceo_decision_mandatory_by_class`, `ceo_arbitration_required` (désaccord `value`).
- **Porte qualité** : instance distincte ; six contrôles ; les contrôles déterministes (`steelman_done_if_required`, `minorities_preserved`, `no_forced_consensus`) priment ; `passed` = avis ∧ tous les contrôles.
- **Budget adaptatif** : `plan_budget` (surcharge CEO absolue, sinon plafond de la classe effective ; relèvement à l'escalade au cadrage sauf surcharge) ; composition à deux niveaux (`full_deliberation` si 3 appels/expert + réservation aval financent ≥ max(2, nb dimensions) experts, sinon `coverage_first`) ; `_check_deliberation_affordable` (cycle minimal = une confrontation par position + 4) ⇒ `deliberation_budget_insufficient` + `budget_request` ; `_can_spend` réserve le cœur de synthèse devant steelman / recherche / révision (`budget_reserved_for_synthesis`) ; `critical_dimension_uncovered` + `budget_request` avant tout Tour 0 quand une dimension `high` n'est pas couverte. Aucune relance : un refus du registre = un arrêt (`max_calls_reached` / `cost_cap_would_be_exceeded`), rapport partiel.
- **Arrêt de délibération** (`deliberation.stop.reason`) : `framing_failed`, `budget`, `missing_external_info`, `ceo_decision_needed`, `residual_only`, `converged`, `no_new_information`, `not_deliberated`.
- **Rapport** : 14 champs remplis depuis la recommandation (options = familles, preuves étiquetées, confiance justifiée, désaccords résiduels, conditions, prochaine action + arbitrage CEO) ou marqueurs explicites (« délibération interrompue après … (arrêt : …) », demande de budget) ; sections « 15. Délibération (trace) » et « 16. Familles stratégiques et comparaison » ; bannière « les agents recommandent, ils ne décident pas ».

## 5. Raisons des choix

- **Registre d'objections adressées** plutôt que « tour de débat » libre : T06 exige des actes adressés à des positions identifiables ; le registre rend la minorité et le résiduel calculables sans jugement du facilitateur.
- **Reconnaissance par le tenant + contrôles déterministes** : le steelman n'est validé ni par son auteur ni par le facilitateur ; T07 se prouve par le tenant, les règles déterministes attrapent les cas grossiers avant même la reconnaissance.
- **Recherche déclenchée par un fait déclaré** (`depends_on_fact`) plutôt que par heuristique textuelle : « un fait recherchable doit battre un tour de débat », mais jamais une recherche « pour remplir ».
- **Révision conditionnelle** : ne pas appeler un expert sans information nouvelle est à la fois T09 (l'insistance ne change rien) et une économie.
- **Réinjection déterministe des résiduels et scission par nature** : deux endroits où une instance LLM pourrait lisser ; on ne lui laisse pas le pouvoir.
- **Plafonds par classe + priorité explicite** plutôt qu'un plafond unique : le budget doit suivre la classe (mandat) ; la priorité largeur → confrontation → synthèse évite la « délibération d'une seule perspective » et le gaspillage d'un cycle inachevé.

## 6. Alternatives étudiées

- *Un seul appel « débat » multi-persona* — rejeté : interdit (un expert ≠ un appel n'est pas une licence pour une instance qui joue tous les rôles).
- *Conserver le plafond unique 12 / 2 €* — rejeté : la délibération minimale sur trois dimensions demande 14 appels ; le mandat exige un budget par classe.
- *Plafonds strictement égaux aux a priori du §6.1* — rejeté pour cet incrément : `courante` < 0,10 € refuserait le cadrage lui-même sous le majorant pré-appel ; déclaré comme écart à arbitrer (§13).
- *Recherche via un moteur tiers ou du scraping* — rejeté : nouvelle dépendance et surface d'erreur ; l'outil web du fournisseur est derrière une interface remplaçable.
- *Laisser la synthèse produire les familles* — rejeté : la consolidation appartient au greffier au schéma fermé, avec règles déterministes.
- *Scores numériques dans la comparaison* — rejeté : interdits (fabrication de précision).

## 7. Risques

- **Écart de plafonds** (`courante`, `importante`) par rapport au §6.1 : déclaré, configurable, à ratifier ou ramener par le CEO ; `critique` est en dessous (90 / 15 € vs ≤ 120 / 5–20 €).
- Le fournisseur `anthropic_web_search` n'est **pas exercé** en CI (aucun réseau) ; le contrat est défensif (tout écart ⇒ `not_found` / `error`), mais son comportement réel sera vu au premier benchmark avec `MISSION_RESEARCH_PROVIDER=anthropic_web_search`.
- Les tests prouvent le **mécanisme** (faux client scripté) ; la qualité réelle des actes, steelmans et synthèses sera jugée sur le jeu de problèmes scellés créé indépendamment.
- La fiabilité des sources reste `unknown` faute de règle explicite : c'est voulu (rien d'inventé), mais la comparaison reçoit donc des preuves « externes, fiabilité inconnue ».
- Une mission à une seule perspective (cas simple) produit une recommandation sans confrontation possible ; la porte et le rapport le disent (`impossible_single_position` pour le steelman, `not_deliberated` / `no_new_information`).

## 8. Impact sur la Constitution

Conforme à l'article X : recommandation ≠ décision (`requires_ceo_decision`), `structurante` / `critique` reviennent au CEO, arbitrage de valeurs escaladé, rapport `candidate`, aucune exécution, aucune chaîne Capability → Tool → Execution. Conforme aux politiques 03 (preuves étiquetées, sources jamais inventées), 04 (confrontation adressée, steelman, révision sous preuve), 06 (largeur préservée par `coverage_first`), 07 (budget par classe, escalade), 13 (arrêt explicite, demande de budget).

## 9. Impact sur l'architecture

Extension additive : 2 modules, 2 colonnes nullable, aucun endpoint nouveau (les artefacts s'ajoutent à `GET /missions/{id}`), aucune infrastructure de workflow, aucun exécuteur, aucun accès externe par défaut (`none`).

## 10. Compatibilité

377 tests historiques verts ; `complete(prompt)` inchangé ; bases existantes migrées par ajout de colonnes nullable ; les deux faux clients de l'incrément 1 répondent aux nouveaux types d'appel par des réponses neutres. **Changement de contrat** : `mission_max_llm_calls` / `mission_max_cost_eur` retirés au profit de `MISSION_CEILING_CALLS_*` / `MISSION_CEILING_COST_*` ; `max_llm_calls` / `max_cost_eur` par mission restent des surcharges absolues.

## 11. Tests effectués

**24 scénarios ajoutés** (`test_missions_deliberation.py`), fixtures purement synthétiques (dimensions alpha / beta / gamma, positions « synthétique un / deux / trois », options A / B / C, question « Q1 synthétique »), sans clé ni réseau. Rapport **appels / coût par scénario** (faux client : 1 000 tokens entrée + 500 sortie par appel ; barème 3 / 15 €/M ; recherche factice 300 + 200) :

| Scénario | Classe | Appels utilisés / plafond | Coût réel / plafond (€) | Arrêt mission | Arrêt délibération | Recommandation |
| --- | --- | --- | --- | --- | --- | --- |
| trois alternatives réelles | importante_provisoire | 14/30 | 0,1470 / 3,0 | — | no_new_information | produite |
| désaccord motivé adressé | importante_provisoire | 16/30 | 0,1680 / 3,0 | — | residual_only | produite |
| steelman reconnu (structurante) | structurante | 17/60 | 0,1785 / 8,0 | — | residual_only | produite |
| strawman refusé (règles) | structurante | 16/60 | 0,1680 / 8,0 | — | no_new_information | produite (porte : échec) |
| strawman refusé (tenant) | structurante | 16/60 | 0,1680 / 8,0 | — | no_new_information | produite (porte : échec) |
| fait contesté, recherche indisponible | importante_provisoire | 15/30 | 0,1575 / 3,0 | — | missing_external_info | produite |
| recherche not_found | importante_provisoire | 16/30 | 0,1592 / 3,0 | — | missing_external_info | produite |
| recherche error | importante_provisoire | 16/30 | 0,1592 / 3,0 | — | missing_external_info | produite |
| preuve externe change une position | importante_provisoire | 18/30 | 0,1824 / 3,0 | — | residual_only | produite |
| insistance sans preuve | importante_provisoire | 15/30 | 0,1575 / 3,0 | — | residual_only | produite |
| synonymes consolidés | importante_provisoire | 14/30 | 0,1470 / 3,0 | — | no_new_information | produite |
| proches mais différentes non fusionnées | importante_provisoire | 14/30 | 0,1470 / 3,0 | — | no_new_information | produite |
| minorité conservée | importante_provisoire | 15/30 | 0,1575 / 3,0 | — | residual_only | produite |
| convergence courante | courante | 14/16 | 0,1470 / 1,5 | — | no_new_information | produite |
| convergence prématurée (importante) | importante_provisoire | 17/30 | 0,1785 / 3,0 | — | residual_only | produite |
| recommandation attendre | importante_provisoire | 14/30 | 0,1470 / 3,0 | — | no_new_information | produite (`wait`) |
| critique : retour CEO + valeurs | critique | 17/90 | 0,1785 / 15,0 | — | ceo_decision_needed | produite |
| arrêt coût en délibération | importante_provisoire | 12/30 | 0,1260 / 0,25 | cost_cap_would_be_exceeded | budget | aucune |
| cycle minimal sous 14 appels | importante_provisoire | 14/14 | 0,1470 / 3,0 | — | residual_only | produite |
| délibération non entamée (9 appels) | importante_provisoire | 7/9 | 0,0735 / 3,0 | deliberation_budget_insufficient | budget | aucune |
| dimension critique non couverte | importante_provisoire | 1/5 | 0,0105 / 3,0 | critical_dimension_uncovered | budget | aucune |
| comparaison et provenance | importante_provisoire | 14/30 | 0,1470 / 3,0 | — | no_new_information | produite |
| journal complet | importante_provisoire | 15/30 | 0,1575 / 3,0 | — | residual_only | produite |

Profil d'appels d'un scénario complet à trois positions : `framing` 1, `expert_tour0` 3, `self_qualification` 3, `confrontation` 3, `revision` 0–3 (conditionnelle), `steelman` + `steelman_recognition` 0–2, `research` 0–1 (fournisseur factice), `consolidation` 1, `comparison` 1, `synthesis` 1, `quality_gate` 1. Ordre de grandeur réel attendu au benchmark (tokens réels, barème réel) : à mesurer ; les plafonds sont des plafonds, pas des cibles.

Ce que prouvent les scénarios : actes adressés à des labels résolus et carte sans sa propre position ; `none` n'enregistre rien ; seuls les destinataires d'une information nouvelle sont révisés ; steelman requis pour `structurante` avec contradicteur `P3` (angle critique) hors du tenant `P1`, reconnaissance appelée après le steelman, trois objets séparés, critique adressée au tenant ; strawman rejeté par les règles ou par le tenant ⇒ critique inadmissible, aucune révision, porte en échec ; question factuelle dédoublonnée, `unavailable` sans appel ni coût, inconnue transmise à la synthèse ; `not_found` / `error` ⇒ aucune source, `provenance = unavailable`, appel compté ; preuve `found` ⇒ révision `modify` déclenchée par `OBJ-1` + `EV-1`, Tour 0 immuable, objection `addressed`, ligne `research` facturée ; insistance ⇒ `maintain`, résiduel conservé jusqu'à la recommandation ; famille A / A bis fusionnée avec variante et désaccord interne, trace ; `build` + `buy` scindées, non-fusion motivée rendue ; minorité réinjectée malgré une synthèse qui l'omet ; `courante` sans objection ⇒ aucun steelman ni révision, `no_new_information` ; divergence 0 sur `importante` ⇒ steelman « convergence prématurée » ; `wait` + `information_insufficient` ⇒ `decision_ready = false` ; `critique` ⇒ décision CEO obligatoire, désaccord de valeurs ⇒ arbitrage, approuver n'appelle rien, seuls des événements de rapport ; plafond de coût 0,25 € ⇒ un seul refus (`synthesis`), aucune recommandation, statut explicite ; 14 appels ⇒ cycle minimal complet, révision cédée à la synthèse et journalisée ; 9 appels ⇒ 7 appels consommés, huit étapes sautées, demande de 5 appels ; quatre dimensions critiques sous 5 appels ⇒ 1 appel, trois non couvertes, demande de 9 appels ; schéma de comparaison sans champ interdit, bases valides, aucune valeur numérique ; journal : un `call_planned` avec empreinte par appel, ordre des étapes, `call_done` avec coût.

Tests de l'incrément 1 adaptés (comportement, pas doctrine) : plafonds par classe (`class_ceilings`), majorants d'une délibération `importante` complète (30 appels) < 3 €, borne économique du cas M = (59 − 10) // 3 = 16 avec 6 experts émergents, surcharge CEO 2 € absolue malgré l'escalade, budget de 6 appels ⇒ `coverage_first` puis `deliberation_budget_insufficient`. **Total : 401 verts** (`pytest` produit), 1 780 verts (racine). `ruff check`, `ruff format --check`, `mypy` verts (produit et racine). T23 : recherche du nom du banc d'essai connu et des identifiants des anciens cas dans les fichiers de l'incrément → 0.

## 12. Checklist

- [x] `src/aisos/` inchangé · [x] Phases 0–18 intactes · [x] 377 tests historiques verts · [x] 24 nouveaux tests verts · [x] Lint / format / mypy verts (produit + racine) · [x] Rapport appels / coût par scénario · [x] Aucun problème scellé demandé, consulté ni reconstruit ; fixtures synthétiques · [x] Aucune règle sectorielle, aucune préférence logiciel / build · [x] Aucun expert ajouté arbitrairement ; aucun « tous les archétypes » · [x] Aucune majorité comme vérité ; aucun score · [x] Aucune source inventée · [x] Aucune recommandation forcée (`wait` / `do_nothing` légitimes) · [x] Aucune exécution · [x] Budget dur, aucune relance illimitée · [x] Écart de plafonds déclaré · [x] ARP complet · [x] PR vers `develop`, **non fusionnée** · [ ] Revue du Chief AI Architect · [ ] Validation CEO

## 13. Questions ouvertes

1. **Plafonds par défaut** : ratifier 16 / 1,50 € (`courante`) et 30 / 3 € (`importante`), ou les ramener vers les a priori du §6.1 en acceptant qu'une mission `courante` s'arrête au rapport de situation (Tour 0) ?
2. **Fournisseur de recherche** au benchmark : `none` (recherche déclarée indisponible, comportement prouvé) ou `anthropic_web_search` (non exercé en CI) ?
3. Ordre de fusion : #143 puis #144.

## 14. Recommandation de Claude Code

**INCREMENT 2 CODE FREEZE v1 — READY FOR INDEPENDENT BENCHMARK.** Ne modifier aucun prompt, seuil, plafond ni logique avant les résultats complets du benchmark indépendant (nouveau jeu de problèmes scellés, créé hors de cette session). Fusionner #143 puis #144 seulement après revue du Chief AI Architect et validation CEO ; ne pas commencer l'incrément 3. V1 n'est pas terminé.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
