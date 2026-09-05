# AI Review Package

**Pull Request :** #143 — *OT-V1 — Incrément 1 : mission de cadrage (Cadrage → Composition → Tour 0 → Cartographie → Rapport)*
**Branche :** `product/mvp` → `develop`
**Auteur :** Claude Code (Chief System Architect)
**Date :** 2026-09-05
**Commits :** départ `b8c2771` (develop, PR #142 fusionnée) → fin `b1fe105`

## 1. Executive Summary

Premier **incrément** de code construit à rebours des tests d'acceptation de la cible opérationnelle (Décision 026). Il ajoute au produit une **mission de cadrage** : entrée unique (problème / idée / objectif / solution existante) → **cadrage** structuré (dimensions émergentes, inconnues, contestation non forcée, classe provisoire escaladable) → **composition** par règles codées (dimensions → cellules → profondeur modeste → contrainte par le budget ; catalogue ouvert ; contradicteur si préférence CEO) → **Tour 0** avec un appel **isolé** par expert → **cartographie** sans pouvoir d'orientation (déterministe + auto-qualification des experts + greffier au schéma fermé) → **rapport de situation `candidate`** sans recommandation. Le tout sous **plafonds CEO** (12 appels, 2,00 €, estimation avant appel, arrêt propre, tokens et coût journalisés). `src/aisos/` inchangé ; phases 0–18 intactes ; **362 tests verts** (335 historiques + 27) ; lint, format et typage verts. **Ce n'est pas une phase et V1 n'est pas terminé.**

## 2. Objectifs

Améliorer de façon mesurable les tests nommés par le mandat : T04, T05, T26, T14, T13, T25, T24 (améliorés) ; T02, T06, T10, T23 (partiellement) — sans simuler ce qui appartient aux incréments suivants (recherche externe, confrontation, steelman, révision, porte qualité indépendante, classification automatique, exécution).

## 3. Fichiers modifiés

Ajoutés : `product/app/mission_schemas.py`, `mission_budget.py`, `mission_framing.py`, `mission_composition.py`, `mission_exploration.py`, `mission_cartography.py`, `mission_report.py`, `missions.py` ; `product/tests/test_missions_otv1.py`, `test_ui_mission_client.py` ; `reviews/packages/PR-143-otv1-increment-1.md`.
Modifiés : `product/app/llm.py` (chemin structuré), `observability.py` (tokens / coût / type d'appel / mission), `db.py` (2 tables, 5 colonnes nullable, ajout idempotent), `config.py` (plafonds, `max_tokens` par type, barème), `schemas.py`, `main.py` (8 endpoints), `product_status.py` (1 capacité), `ui/api_client.py`, `ui/streamlit_app.py` (onglet), `product/README.md`, `TRACEABILITY.md`.
**Aucun fichier de `src/`, `docs/` gelé, ni des 32 agents historiques modifié.** 21 fichiers, +3 751 / −11.

## 4. Changements importants

- **Client LLM étendu sans rupture** : `complete(prompt)` conservé ; `complete_structured(system, prompt, call_type, max_tokens) -> LLMResponse(text, usage)` ; `ObservedLLMClient.complete_structured` refuse tout repli silencieux sur `complete`.
- **Budget** : `BudgetLedger.check_before_call` majore le coût (tokens du prompt estimés pessimistement + `max_tokens` au barème) et lève `BudgetExceededError` si un plafond pourrait être dépassé ; `record` calcule le coût réel sur l'usage ; borne économique d'experts = (appels restants − 1 réservé) // 2 ⇒ 5 avec 12 appels ; budget insuffisant pour explorer ⇒ arrêt propre et rapport partiel.
- **Cadrage** : `FramingOutput` (problème compris, objectif, contraintes, hypothèses, inconnues, dimensions avec criticité / inconnues / angles, contestation `none|raised`, signaux d'escalade, classe suggérée). Classe initiale `importante_provisoire` ; escalade appliquée si provisoire, **soumise au CEO** si déclarée.
- **Composition** : profondeur initiale par criticité (1 / 2 / 3) bornée par la classe et par `mission_max_angles_per_cell` (3, **expérimental, temporaire, paramétrable, non doctrinal**) ; réduction journalisée par criticité ; `build_expert_cells` non appelé ; « Synthétiseur / arbitre » exclu du Tour 0 ; avec préférence CEO, exactement une perspective « Red Team / adversaire » mandatée pour la contredire.
- **Tour 0** : prompt = entrée + dossier de cadrage identique + fiche propre ; `call_planned` journalise le prompt complet et son SHA-256 ; `tour0_closed` avant toute auto-qualification.
- **Cartographie** : déterministe (identifiants `E{i}-O{j}`, comptages, regroupement par identifiants déclarés, indice de divergence, agrégats) ; sémantique déléguée (auto-qualification identique / variante / différente ; greffier seulement sur ambiguïté résiduelle ; `ClerkOutput` sans champ interdit).
- **Rapport** : `candidate`, établi / supposé / inconnu / non vérifié / contesté ; 14 champs, « non encore délibéré » explicite ; Markdown déterministe ; actions CEO (approve / request-revision / reject) sans exécution, 409 hors `candidate`.

## 5. Raisons des choix

- **Réutilisation par spécification, pas par import** de `src/aisos/` : isolation déclarée du produit.
- **Composition contrainte par le budget en amont** plutôt que « planifier 10 puis couper » : c'est l'ordre doctrinal (dimensions → profondeur → budget), et cela évite de gaspiller des appels.
- **Auto-qualification avant greffier** : l'équivalence des positions est d'abord déclarée par leurs auteurs ; le greffier n'intervient que sur l'ambiguïté résiduelle, et son schéma ne peut pas exprimer de préférence.
- **Aucune recommandation dans le rapport** : sans tours de critique, une recommandation serait une simulation de T11.
- **Colonnes nullable + ajout idempotent** : les appels historiques restent inchangés ; les bases existantes ne cassent pas.

## 6. Alternatives étudiées

- *Refactoriser les 32 agents vers le chemin structuré* — rejeté : hors périmètre, risque de régression sans test amélioré.
- *Cartographie 100 % LLM* — rejeté : donnerait au facilitateur un pouvoir d'orientation ; *cartographie 100 % déterministe* — rejeté : prétendrait que des jugements sémantiques sont mécaniques.
- *Nombre d'experts par classe* — rejeté : interdit par la Décision 026 ; le nombre émerge des dimensions, de la criticité et du budget.
- *Rapport avec recommandation « provisoire »* — rejeté : simulation de T11.

## 7. Risques

- Barème de coût **configuré** (3 / 15 €/M) à aligner sur la grille réelle avant mission réelle ; l'estimation avant appel est pessimiste par construction.
- Le faux client prouve le **mécanisme** ; la qualité des cadrages et des exposés réels sera jugée sur les problèmes scellés.
- Le rattachement des angles libres du cadrage au catalogue est par mots-clés (simple, journalisé) ; un angle non reconnu devient un angle libre, jamais perdu.
- **Réserve d'honnêteté** : la session de développement est aussi l'auteur des problèmes scellés ; aucune règle, mot-clé, scénario ou test n'en découle (grep T23, fixtures abstraites), mais le CEO peut faire régénérer les cas par un tiers.

## 8. Impact sur la Constitution

Conforme à l'article X : le rapport reste `candidate`, aucune action CEO ne déclenche d'exécution, la contestation remonte au CEO, la classe déclarée par le CEO n'est jamais écrasée. Conforme aux politiques 03 (inconnues déclarées, preuves typées, jamais `verified` sans source), 06 (largeur par dimensions, quorum non simulé), 07 (classe provisoire escaladable), 13 (bornes dures). Facilitation neutre (`behavior/04`) : structure sans orienter.

## 9. Impact sur l'architecture

Extension additive : nouveau chemin LLM, 2 tables, 5 colonnes nullable, 8 endpoints, 8 modules. Aucune infrastructure de workflow générique, aucune classification automatique, aucun exécuteur, aucun accès externe.

## 10. Compatibilité

335 tests historiques inchangés et verts ; invariants « zéro LLM » des phases 14–18 conservés ; `complete(prompt)` inchangé ; bases existantes migrées par ajout de colonnes nullable au démarrage. CI produit : `ruff check .`, `ruff format --check .`, `mypy`, `pytest` — tous verts en local.

## 11. Tests effectués

27 tests ajoutés (`test_missions_otv1.py` 23, `test_ui_mission_client.py` 4), sans clé, sans réseau, fixtures abstraites : Tour 0 isolé (N experts = N appels ; aucun exposé d'un autre dans un prompt ; journal probant ; auto-qualification après clôture) ; deux cadrages → deux compositions ; cas simple ≤ 2 experts ; borne expérimentale / non doctrinale, borne économique 5, ≤ 12 appels ; préférence CEO → une perspective contradictrice, aucune sinon ; contestation portée quand produite, absente sinon ; ≥ 3 inconnues comptées ; classe provisoire, escalade, classe déclarée conservée ; ≥ 3 groupes d'options, non-action reconnue, divergence > 0 ; greffier seulement sur ambiguïté ; schéma greffier sans champ interdit ; preuve `verified` sans source rétrogradée ; tokens/coût par appel et par mission ; 13e appel refusé (registre) et arrêt dur intégré ; arrêt avant 2 € ; rapport partiel cohérent ; `candidate` jusqu'à action CEO, approbation sans appel, 409 ensuite ; client historique compatible ; lignes `Mission` persistées ; client UI (4). **Total : 362 verts.** T23 : `grep -rniI maestrosala product/app product/ui product/tests` → 0.

## 12. Checklist

- [x] `src/aisos/` inchangé · [x] Phases 0–18 intactes (335 tests) · [x] Aucune règle nommant un banc d'essai · [x] Problèmes scellés ni demandés, ni lus, ni reconstruits · [x] Aucune recommandation simulée · [x] Aucune exécution · [x] Budget : estimation avant appel, arrêt propre, journalisation · [x] Lint / format / mypy / tests verts · [x] ARP · [x] PR vers `develop`, non fusionnée · [ ] Revue du Chief AI Architect · [ ] Validation CEO

## 13. Questions ouvertes

1. Barème de coût réel du modèle configuré (à renseigner par variables d'environnement avant la première mission réelle).
2. Le CEO souhaite-t-il faire régénérer les problèmes scellés par un tiers avant l'évaluation, compte tenu de la réserve d'honnêteté ?

## 14. Recommandation de Claude Code

**INCREMENT 1 CODE FREEZE — READY FOR SEALED HOLDOUT EVALUATION** au commit `b1fe105` : ne modifier aucun prompt, seuil ni logique de composition avant les résultats complets. Fusionner après revue et validation CEO ; ne pas commencer l'incrément 2. V1 n'est pas terminé.
