# AI Review Package

**Pull Request :** #142 — *OT-V1 — Décision 026, Operational Target V1 et audit de préparation du premier incrément*
**Branche :** `claude/ai-sos-orion-handoff-a2w904` → `develop`
**Auteur :** Claude Code (Chief System Architect)
**Date :** 2026-09-05

## 1. Executive Summary

Cette Pull Request est **purement documentaire**. Elle inscrit dans le système documentaire du dépôt la **cible opérationnelle d'AI-SOS V1** et sa **définition de « terminé » par tests d'acceptation comportementaux** (T01–T26), sous la forme d'une **Décision 026** (statut *proposée*, qui prend effet à la fusion) et d'un **document canonique**. Elle joint un **audit ciblé** du code existant au regard du premier objectif (T02–T06) et des fondations (T11, T25), une **proposition du premier incrément de code minimal** — **non codé** dans ce lot — et un **verdict NOT READY** motivé par trois éléments qui relèvent du CEO. **Aucun code produit modifié, `src/aisos/` inchangé, `product/` inchangé, aucune phase ouverte.**

## 2. Objectifs

Définir la destination avant la route : dire ce qu'AI-SOS doit **savoir faire** sur des problèmes jamais vus pour être honnêtement déclaré « fonctionnel », ratifier les points doctrinaux restés non tranchés (contestation de la demande, largeur/profondeur des cellules, définition d'un expert, recherche externe, capacité d'action, exécution sous mandat), et établir précisément — test par test — l'écart entre le code actuel et cette cible, avec le plus petit incrément qui améliore des tests nommés.

## 3. Fichiers modifiés

Modifiés : `DECISIONS.md` (Décision 026, append-only), `TRACEABILITY.md` (entrée OT-V1).
Ajoutés : `docs/strategy/AI-SOS-OPERATIONAL-TARGET-V1.md`, `docs/reports/OT-V1-FIRST-INCREMENT-READINESS.md`, `reviews/packages/PR-142-operational-target-v1.md` (ce document).
`HANDOFF-AI-SOS-ORION.md` (commit pré-existant du 7 juillet 2026 sur cette branche, périmé, hors mandat) a été **retiré du diff par un commit de revert** sur instruction du CEO : son historique Git est conservé (commit d'ajout puis commit d'annulation), mais **il ne fait plus partie des fichiers modifiés par la PR**.
**Aucun fichier de `product/`, `src/`, `tests/`, `docs/` gelé (`00-vision`, `policies`, `behavior`, `components`) modifié.**

## 4. Changements importants

- **Décision 026** (8 clauses) : (1) cible opérationnelle et DONE par tests — V1 = 19 tests (T01–T16, T23, T25, T26), seuil **≥ 17/19** (au plus 2 échecs, hors noyau) dont les 8 non négociables T02, T06, T09, T12, T13, T14, T15, T25 tous réussis, 3 bancs d'essai, expérience de profondeur réalisée ; (2) droit de contestation de la demande, classé structurante, remonté au CEO ; (3) largeur (dimensions) / profondeur (angles) ; 10 angles de 4B-R = **catalogue ouvert**, interdiction de « 10 → 3 » arbitraire, nombre par classe **déterminé expérimentalement** ; (4) définition d'un expert (indépendance initiale, attribuabilité, réactivité, persistance) ; (5) recherche externe = capacité légitime (levée doctrinale ciblée de la Voie A) ; (6) capacité d'action = verbe distinct de l'outil ; (7) exécution sous mandat et manifeste — **légitimité doctrinale, pas autorisation runtime** ; (8) ce qui ne change pas (CEO seule autorité, classes de décision, corpus gelé, `src/aisos/`, aucune règle nommant un projet, aucun bloc sans test).
- **Document canonique** : formulation de la cible ; capacités observables ; définitions normatives ; protocole 360° (A–H) ; désaccords/consensus ; budget adaptatif et escalade ; **T01–T26** ; V1/V1.5/V2 + portes ; bancs d'essai ; protocole expérimental (A, B, C, D, E, B+, E' ; H1–H5) ; **matrice** test → état → preuve (code, lignes) → écart → réutilisable → modification minimale ; ce qu'il ne faut pas construire ; checklist DONE.
- **Rapport de préparation** : audit de 12 composants ; bilan réutilisé / étendu sans rupture / non réutilisé-mais-conservé (**rien n'est supprimé**) ; incrément 1 « Cadrage + Exploration indépendante + Cartographie + Rapport de situation » (1 + N + N courts + 0–1 appels LLM, un appel isolé par expert, composition par règles codées avec une borne de coût **expérimentale, temporaire et non doctrinale**, cartographie sans pouvoir d'orientation — partie déterministe codée, partie sémantique par auto-qualification des experts puis greffier au schéma fermé —, rapport `candidate` soumis au CEO) ; tests à améliorer ; 11 risques doctrinaux ; verdict.

## 5. Raisons des choix

- **Statut « proposée », effet à la fusion** : une décision rédigée par Claude ne peut pas s'auto-ratifier ; la fusion par le CEO est l'acte de ratification, conformément à la Décision 016 et à la Constitution.
- **Tests d'acceptation comportementaux plutôt que fonctionnalités** : le réalignement a montré que les phases se succédaient sans cible observable ; un test « réussi sur un problème jamais vu » est le seul critère qui ne se satisfait pas de lui-même.
- **Catalogue ouvert plutôt que quota** : « 10 » n'avait qu'une origine de commit (`8fe1032`) ; « 3 » n'en aurait pas davantage. La profondeur se découvre (divergence, incertitude, irréversibilité) et se mesure (protocole expérimental).
- **`src/aisos/` réutilisé par spécification, jamais par import** : `product/pyproject.toml` déclare le produit isolé du noyau ; importer briserait cette isolation et est interdit par le mandat.
- **Verdict NOT READY** : coder l'incrément avant ratification reproduirait la dérive de `product/` PHASE 0 ; juger T02–T06 sans problèmes scellés serait juger sur des cas déjà vus ; le plafond de budget appartient au CEO.

## 6. Alternatives étudiées

- *Coder immédiatement l'incrément 1 dans ce lot* — rejeté : interdit par le mandat, et doctrine non ratifiée.
- *Fixer la profondeur par défaut à 3* — rejeté : confusion largeur/profondeur déjà corrigée ; aucune mesure ne l'appuie.
- *Écrire une roadmap par phases (19, 20…)* — rejeté : la Décision 026 §8 interdit d'engager un bloc « parce qu'il figure dans une roadmap ».
- *Importer `DefaultPolicyEngine` dans `product/`* — rejeté : isolation déclarée du produit ; port par spécification dans un incrément ultérieur (T16).
- *Supprimer le commit de handoff pré-existant par réécriture d'historique* — rejeté : le CEO a demandé son retrait du diff, réalisé par **revert** (historique conservé, fichier absent des changements de la PR).

## 7. Risques

- Lecture de la clause 7 comme une autorisation d'exécuter (la décision dit explicitement le contraire).
- Réintroduction d'un quota d'experts par un futur incrément, y compris par la borne de coût de l'incrément 1 (garde-fou : borne déclarée expérimentale, temporaire, non doctrinale ; test T05 « courant → ≤ 2 » ; expérience obligatoire).
- Multiplication de documents de méthode (la 026 §8 borne le corpus à : décision, document canonique, protocole, un rapport par porte).

## 8. Impact sur la Constitution

Aucun article modifié. La Décision 026 **prolonge** l'article X (les agents recommandent, ne décident jamais : la contestation remonte au CEO ; l'artefact reste `candidate`), l'article VI et XIII (capacités avant outils, neutralité technologique), l'article XI (boucle circulaire : vérifier, apprendre, réévaluer) et les politiques 03 (non-devinette → recherche du fait), 06 (équipe minimale suffisante → axe largeur), 07/08 (classes et pré-approbation → validation directe ou par politique). La seule levée est **ciblée** (Voie A : recherche externe) et **doctrinale**.

## 9. Impact sur l'architecture

Aucun changement de code. Le rapport de préparation identifie les extensions **sans rupture** à venir (client LLM : system prompt, `max_tokens` par appel, usage ; `LLMCallLog` : tokens, coût ; schémas Pydantic structurés ; 2 tables nouvelles) et les composants réutilisés tels quels (`EXPERT_ARCHETYPES`, prompts de rôle, observabilité, Approval Engine, espace projet). Elles ne sont **pas** réalisées ici.

## 10. Compatibilité

Totale : aucun fichier de `product/` modifié (la CI produit ne se déclenche pas) ; `src/aisos/` intact ; `DECISIONS.md` append-only ; corpus gelé intact. Phases 0–18 et leurs 335 tests non touchés.

## 11. Tests effectués

- Documentaire : cohérence des références de lignes vérifiée sur `develop@d65707f` (`llm.py:22-46`, `config.py:24`, `agents.py:66-129`, `improvement_agents.py:102-214`, `company_agents.py:58-131`, `:277-300`, `deliverable_agents.py:118-189`, `observability.py:40-150`, `db.py:495-560`, `main.py:439-455`, `src/aisos/policies/engine.py:88-304`).
- Invariant T23 : `grep -rni maestrosala product/` → **0 occurrence**.
- Git : branche recréée depuis `origin/develop` (`d65707f`) ; commit pré-existant rebasé (cherry-pick `-x`) puis **annulé par revert** sur instruction du CEO ; `git diff --stat origin/develop...HEAD` = 5 fichiers, tous relevant du mandat.
- Audit de cohérence post-revue (grep sur les 5 fichiers) : aucune occurrence résiduelle de « 16/18 » ou « 18 tests » ; aucun nombre d'experts présenté comme défaut ; T12 reformulé partout (tests, checklist, capacités, banc d'essai A, matrice) ; facilitateur : opérations déterministes / sémantiques distinguées dans le document canonique et le rapport ; aucune référence à un banc d'essai dans une règle produit (`product/` : 0 occurrence).
- Aucun test de code exécuté (aucun code modifié).

## 12. Checklist

- [x] Aucun code produit modifié · [x] `src/aisos/` inchangé · [x] Corpus gelé inchangé · [x] `DECISIONS.md` append-only · [x] TRACEABILITY mise à jour · [x] ARP produit · [x] PR vers `develop`, non fusionnée · [x] Aucune phase ouverte · [x] Aucune règle nommant un banc d'essai · [x] Premier incrément **non codé** · [x] Correction post-revue appliquée (19 tests / seuil 17, T12, profondeur expérimentale, facilitateur, handoff retiré) · [ ] Revue du Chief AI Architect · [ ] Validation CEO

## 13. Questions ouvertes

1. *(Résolue)* Le retrait de `HANDOFF-AI-SOS-ORION.md` a été demandé par le CEO et effectué par revert.
2. Qui rédige et scelle les **trois problèmes jamais vus** (CEO ou Orion) et où sont-ils conservés hors dépôt ?
3. *(Résolue par le CEO)* Plafond dur **2,00 €/mission + 12 appels LLM** ; `max_tokens` configurable par type d'appel ; estimation avant appel et refus/arrêt si dépassement possible ; tokens et coût journalisés.
4. *(Résolue par le CEO)* Classe initiale = **« importante provisoire / non déterminée »**, jamais « importante » définitive par défaut ; le cadrage peut et doit l'escalader selon les risques découverts.

## 14. Recommandation de Claude Code

**Verdict documentaire : READY FOR CEO RATIFICATION** (les cinq incohérences signalées par le CEO sont corrigées ; aucune incohérence connue ne subsiste). **Verdict d'implémentation : NOT READY** (inchangé) — deux prérequis restent : la ratification par fusion et les trois problèmes scellés jamais vus (le budget et la classe initiale sont désormais fixés par le CEO). **Fusionner après revue** pour ratifier la Décision 026 et le document canonique — c'est le premier des trois prérequis du premier incrément. **Ne pas** demander de code tant que les problèmes scellés et le plafond de budget n'existent pas : le verdict reste **NOT READY** jusque-là, et il bascule en READY dès que ces trois éléments sont réunis, sans autre décision technique requise du CEO.
