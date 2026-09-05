# AI Review Package

**Pull Request :** #143 — *OT-V1 — Incrément 1 : mission de cadrage (Cadrage → Composition → Tour 0 → Cartographie → Rapport)*
**Branche :** `product/mvp` → `develop`
**Auteur :** Claude Code (Chief System Architect)
**Date :** 2026-09-05 (ARP v2, après audit du Chief AI Architect)
**Commits :** départ `b8c2771` (develop, PR #142 fusionnée) → freeze v1 `b1fe105` → **freeze v2 `9e62b9b`**

## 1. Executive Summary

Premier **incrément** de code construit à rebours des tests d'acceptation de la cible opérationnelle (Décision 026). Il ajoute au produit une **mission de cadrage** : entrée unique (problème / idée / objectif / solution existante) → **cadrage** structuré (dimensions émergentes, inconnues, contestation non forcée, classe provisoire escaladable) → **composition** par règles codées (dimensions → cellules → profondeur modeste → contrainte par le budget ; catalogue ouvert ; perspective contraire seulement si pertinente) → **Tour 0** avec un appel **isolé** par expert → **cartographie** sans pouvoir d'orientation (déterministe + auto-qualification des experts + greffier au schéma fermé) → **rapport de situation `candidate`** sans recommandation. Le tout sous **plafonds CEO** (12 appels, 2,00 €, estimation avant appel, arrêt propre, tokens et coût journalisés). `src/aisos/` inchangé ; phases 0–18 intactes ; **366 tests verts** (335 historiques + 31) ; lint, format et typage verts. **Ce n'est pas une phase et V1 n'est pas terminé.**

**Statut du holdout (décision post-audit).** Les trois problèmes précédemment dits « scellés » étaient connus de la session de développement : ils sont **contaminés** et **ne seront pas utilisés pour l'évaluation aveugle de cet incrément**. Un **nouveau jeu de problèmes scellés sera créé indépendamment APRÈS le code freeze v2**, et **la session de développement n'y aura aucun accès avant l'évaluation**. Les fixtures de test ne reproduisent aucun ancien cas : elles sont purement synthétiques (dimensions alpha / beta / gamma / delta / omega, hypothèses H*, inconnues U*, signaux S*, positions « synthétique distincte n° »).

## 2. Objectifs

Améliorer de façon mesurable les tests nommés par le mandat : T04, T05, T26, T14, T13, T25, T24 (améliorés) ; T02, T06, T10, T23 (partiellement) — sans simuler ce qui appartient aux incréments suivants (recherche externe, confrontation, steelman, révision, porte qualité indépendante, classification automatique, exécution).

## 3. Fichiers modifiés

Ajoutés : `product/app/mission_schemas.py`, `mission_budget.py`, `mission_framing.py`, `mission_composition.py`, `mission_exploration.py`, `mission_cartography.py`, `mission_report.py`, `missions.py` ; `product/tests/test_missions_otv1.py`, `test_ui_mission_client.py` ; `reviews/packages/PR-143-otv1-increment-1.md`.
Modifiés : `product/app/llm.py` (chemin structuré), `observability.py` (tokens / coût / type d'appel / mission), `db.py` (2 tables, 5 colonnes nullable, ajout idempotent), `config.py` (plafonds, `max_tokens` par type, barème), `schemas.py`, `main.py` (8 endpoints), `product_status.py` (1 capacité), `ui/api_client.py`, `ui/streamlit_app.py` (onglet), `product/README.md`, `TRACEABILITY.md`.
**Aucun fichier de `src/`, `docs/` gelé, ni des 32 agents historiques modifié.**

## 4. Changements importants

- **Client LLM étendu sans rupture** : `complete(prompt)` conservé ; `complete_structured(system, prompt, call_type, max_tokens) -> LLMResponse(text, usage)` ; `ObservedLLMClient.complete_structured` refuse tout repli silencieux sur `complete`.
- **Budget** : `BudgetLedger.check_before_call` majore le coût (tokens du prompt estimés pessimistement + `max_tokens` au barème) et lève `BudgetExceededError` si un plafond pourrait être dépassé ; `record` calcule le coût réel sur l'usage ; borne économique d'experts = (appels restants − 1 réservé) // 2 ⇒ 5 avec 12 appels ; budget insuffisant pour explorer ⇒ arrêt propre et rapport partiel.
- **Cadrage** : `FramingOutput` (problème compris, objectif, contraintes, hypothèses, inconnues, dimensions avec criticité / inconnues / angles, contestation `none|raised`, signaux d'escalade, classe suggérée). Classe initiale `importante_provisoire`.
- **Contrat d'escalade (post-audit)** : un cadrage ne peut plus produire des signaux d'escalade substantiels sans effet. Le schéma marque `suggested_class_missing` ; le prompt rend `suggested_class` **obligatoire** en présence de signaux ; l'orchestrateur applique, à défaut, une **escalade d'un rang** (`NEXT_CLASS`) si la classe est provisoire, et la **soumet au CEO** si la classe est déclarée (jamais écrasée). Aucun classifieur automatique T16.
- **Composition** : profondeur initiale par criticité (1 / 2 / 3) bornée par la classe et par `mission_max_angles_per_cell` (3, **expérimental, temporaire, paramétrable, non doctrinal**) ; réduction journalisée par criticité ; `build_expert_cells` non appelé ; « Synthétiseur / arbitre » exclu du Tour 0.
- **T26 (post-audit)** : la composition distingue **préférence déclarée** et **besoin pertinent de contradiction** (`contradiction_pertinence` : dimension de criticité élevée, signaux d'escalade, contestation soulevée, angle critique appelé par le cadrage). Sans besoin pertinent : composition inchangée, journal « pas d'opposition artificielle ». Avec besoin : une perspective **déjà naturellement critique** (Red Team, risques / sécurité, conformité) porte le mandat ; sinon un contradicteur est ajouté si la cellule et le budget le permettent, ou substitué **uniquement à un angle venu du catalogue par défaut** — jamais à un angle appelé par le cadrage ; à défaut, le mandat est confié à l'angle le plus critique disponible. La justification est journalisée dans tous les cas. La préférence n'est transmise qu'à la perspective mandatée.
- **Tour 0** : prompt = entrée + dossier de cadrage identique + fiche propre ; `call_planned` journalise le prompt complet et son SHA-256 ; `tour0_closed` avant toute auto-qualification.
- **Cartographie** : déterministe (identifiants `E{i}-O{j}`, comptages, regroupement par identifiants déclarés, indice de divergence, agrégats) ; sémantique déléguée (auto-qualification identique / variante / différente ; greffier seulement sur ambiguïté résiduelle ; `ClerkOutput` sans champ interdit).
- **Rapport** : `candidate`, établi / supposé / inconnu / non vérifié / contesté ; 14 champs, « non encore délibéré » explicite ; Markdown déterministe ; actions CEO (approve / request-revision / reject) sans exécution, 409 hors `candidate`.

## 5. Raisons des choix

- **Réutilisation par spécification, pas par import** de `src/aisos/` : isolation déclarée du produit.
- **Composition contrainte par le budget en amont** : ordre doctrinal (dimensions → profondeur → budget), pas de gaspillage d'appels.
- **Escalade d'un rang par défaut plutôt que classe fixe** : solution minimale et explicite qui respecte la classe déclarée par le CEO et évite « risque majeur détecté, classe inchangée faute d'un champ facultatif ».
- **Pertinence de la contradiction lue dans le cadrage** : évite l'automatisme « préférence ⇒ Red Team » tout en garantissant qu'une préférence ne fait jamais pencher la composition vers l'alignement.
- **Aucune recommandation dans le rapport** : sans tours de critique, une recommandation serait une simulation de T11.

## 6. Alternatives étudiées

- *Refactoriser les 32 agents vers le chemin structuré* — rejeté : hors périmètre.
- *Rejeter (erreur de validation) un cadrage qui signale sans classer* — rejeté : perdrait le cadrage entier ; l'escalade par défaut conserve l'information et compense le manquement.
- *Forcer systématiquement un Red Team dès qu'une préférence existe* — rejeté après audit : opposition artificielle.
- *Cartographie 100 % LLM* — rejeté : pouvoir d'orientation du facilitateur ; *100 % déterministe* — rejeté : jugements sémantiques prétendus mécaniques.
- *Nombre d'experts par classe* — rejeté : interdit par la Décision 026.

## 7. Risques

- Barème de coût **configuré** (3 / 15 €/M) à aligner sur la grille réelle avant mission réelle.
- Le faux client prouve le **mécanisme** ; la qualité réelle des cadrages et exposés sera jugée sur le nouveau jeu de problèmes scellés, créé indépendamment.
- Le rattachement des angles libres du cadrage au catalogue est par mots-clés (journalisé) ; un angle non reconnu devient un angle libre, jamais perdu.
- L'escalade par défaut est d'un rang : un cadrage qui signale sans classer sur une mission déjà `structurante` provisoire aboutit à `critique` ; c'est le comportement conservateur voulu (`behavior/13`).

## 8. Impact sur la Constitution

Conforme à l'article X : le rapport reste `candidate`, aucune action CEO ne déclenche d'exécution, la contestation et l'escalade remontent au CEO, la classe déclarée par le CEO n'est jamais écrasée. Conforme aux politiques 03 (inconnues déclarées, preuves typées, jamais `verified` sans source), 06 (largeur par dimensions), 07 (classe provisoire escaladable, défaut conservateur), 13 (bornes dures). Facilitation neutre (`behavior/04`) : structure sans orienter. Décision 026 §3 : aucun quota d'experts ; §8 : aucune règle nommant un projet.

## 9. Impact sur l'architecture

Extension additive : nouveau chemin LLM, 2 tables, 5 colonnes nullable, 8 endpoints, 8 modules. Aucune infrastructure de workflow générique, aucune classification automatique, aucun exécuteur, aucun accès externe.

## 10. Compatibilité

335 tests historiques inchangés et verts ; invariants « zéro LLM » des phases 14–18 conservés ; `complete(prompt)` inchangé ; bases existantes migrées par ajout de colonnes nullable au démarrage. CI produit : `ruff check .`, `ruff format --check .`, `mypy`, `pytest` — tous verts en local.

## 11. Tests effectués

31 tests ajoutés (`test_missions_otv1.py` 27, `test_ui_mission_client.py` 4), sans clé, sans réseau, fixtures synthétiques abstraites : Tour 0 isolé (N experts = N appels ; aucun exposé d'un autre dans un prompt ; journal probant ; auto-qualification après clôture) ; deux cadrages → deux compositions ; cas simple ≤ 2 experts ; borne expérimentale / non doctrinale, borne économique 5, ≤ 12 appels ; **T26** : besoin pertinent avec angle critique existant → mandat confié, composition inchangée ; sans besoin pertinent → aucune perspective ajoutée ; besoin pertinent sans angle critique → contradicteur substitué à un angle du catalogue, angles du cadrage conservés ; contestation portée quand produite, absente sinon ; ≥ 3 inconnues comptées ; classe provisoire, escaladée par le cadrage, déclarée conservée ; **escalade par défaut** : signaux sans classe → `structurante` (provisoire) / soumise au CEO (déclarée `courante` → `importante` proposée) ; schéma : `suggested_class_missing` ; ≥ 3 groupes d'options, non-action reconnue, divergence > 0 ; greffier seulement sur ambiguïté ; schéma greffier sans champ interdit ; preuve `verified` sans source rétrogradée ; tokens/coût par appel et par mission ; 13e appel refusé et arrêt dur intégré ; arrêt avant 2 € ; rapport partiel cohérent ; `candidate` jusqu'à action CEO, approbation sans appel, 409 ensuite ; client historique compatible ; lignes `Mission` persistées ; client UI (4). **Total : 366 verts.** T23 : recherche automatique du nom du banc d'essai connu et des termes des anciens cas dans `app/`, `ui/`, `tests/` → 0.

## 12. Checklist

- [x] `src/aisos/` inchangé · [x] Phases 0–18 intactes (335 tests) · [x] Aucune règle nommant un banc d'essai · [x] Anciens cas écartés du holdout ; aucun nouveau cas demandé ni consulté · [x] Fixtures synthétiques · [x] Contrat d'escalade corrigé et testé · [x] T26 pertinent, non automatique, testé · [x] Aucune recommandation simulée · [x] Aucune exécution · [x] Budget : estimation avant appel, arrêt propre, journalisation · [x] Lint / format / mypy / tests verts · [x] ARP v2 · [x] PR vers `develop`, non fusionnée · [ ] Revue du Chief AI Architect · [ ] Validation CEO

## 13. Questions ouvertes

1. Barème de coût réel du modèle configuré (variables d'environnement) avant la première mission réelle.
2. Qui crée le nouveau jeu de problèmes scellés (tiers indépendant) et où est-il conservé hors dépôt ?

## 14. Recommandation de Claude Code

**INCREMENT 1 CODE FREEZE v2 — READY FOR INDEPENDENT SEALED HOLDOUT GENERATION** au commit `9e62b9b` : ne modifier aucun prompt, seuil ni logique de composition avant les résultats complets de l'évaluation. Fusionner après revue et validation CEO ; ne pas commencer l'incrément 2 ; ne pas faire créer les nouveaux cas par la session de développement. V1 n'est pas terminé.
