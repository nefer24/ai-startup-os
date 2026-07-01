# AI Review Package

**Pull Request :** #003 — *Introduce the AI Review Package (ARP)* (décision d'architecture 012)
**Branche :** `feature/ai-review-package` → `develop`
**Auteur :** Claude Code (Documentation Engineer & Software Engineer)
**Date :** 2026-07-01

## 1. Executive Summary

Cette Pull Request institue l'**AI Review Package (ARP)** comme livrable officiel d'AI-SOS (décision d'architecture 012). Elle crée le dossier d'archivage `reviews/packages/`, le template officiel `templates/review-package-template.md`, intègre la nouvelle règle dans le workflow de gouvernance, enregistre la décision 012 au registre, et fournit ce document — le **premier ARP** du projet, qui documente sa propre Pull Request à titre de démonstration et de mise en conformité immédiate.

## 2. Objectifs

Rendre la gouvernance d'AI-SOS **indépendante des limitations et des délais de synchronisation des outils externes** (GitHub, connecteurs, APIs, plateformes IA). L'ARP fournit, dans un document unique et versionné, toutes les informations nécessaires à la revue d'architecture, afin que celle-ci reste possible et fiable même si un outil externe est indisponible ou désynchronisé. À partir de cette décision, l'ARP devient la source officielle d'information lors des revues, le connecteur GitHub n'étant qu'un outil de vérification complémentaire.

## 3. Fichiers modifiés

| Statut | Fichier |
|---|---|
| A | `templates/review-package-template.md` — template officiel de l'ARP (14 sections) |
| A | `reviews/packages/README.md` — fonctionnement officiel de l'ARP |
| A | `reviews/packages/PR-003-ai-review-package.md` — ce document (premier ARP) |
| M | `governance/git-workflow.md` — ARP ajouté au processus de PR + section dédiée |
| M | `DECISIONS.md` — ajout de la section « Décision 012 — AI Review Package (ARP) » |
| M | `reviews/README.md` — référence du sous-dossier `packages/` |

## 4. Changements importants

- **Template ARP** : 14 sections obligatoires (Executive Summary → Recommandation de Claude Code), conformes à la décision 012.
- **Processus de PR** : le workflow passe de 7 à 8 étapes ; l'étape « Production de l'AI Review Package » précède désormais la revue du Chief AI Architect.
- **Nouvelle règle** : avant toute demande de revue, Claude Code doit toujours produire un ARP ; l'ARP est la source officielle, GitHub un complément.
- **Traçabilité** : convention de nommage `reviews/packages/PR-<numéro>-<titre-court>.md` et archivage durable des ARP.

## 5. Raisons des choix

- **Un template unique et exhaustif** garantit des revues homogènes et comparables dans le temps.
- **L'archivage versionné dans le dépôt** (plutôt que dans un outil externe) rend l'ARP durable et indépendant des connecteurs, conformément à l'intention de la décision 012.
- **Produire l'ARP de cette PR elle-même** applique immédiatement la règle et fournit un exemple de référence réutilisable.
- **Intégration dans `governance/git-workflow.md`** : le workflow Git est la source de vérité du processus ; la règle y est donc rendue opposable, et non isolée dans un document annexe.

## 6. Alternatives étudiées

- **Se reposer uniquement sur la description de la PR GitHub** — rejeté : dépendant d'un outil externe, non versionné dans le dépôt, contraire à l'objectif de la décision 012.
- **Un ARP sous forme de commentaire de PR** — rejeté : non archivé durablement, difficile à retrouver et à auditer.
- **Ne pas produire d'ARP pour cette PR (seulement le template)** — rejeté : la règle devient active dès la décision 012 ; produire le premier ARP démontre la conformité.
- **Checklist en caractères `□`** (comme dans la décision) — remplacée par des cases Markdown `- [ ]`, rendues et cochables sur GitHub, tout en conservant les mêmes libellés.

## 7. Risques

- **Risques techniques :** faibles. Modifications exclusivement documentaires (Markdown), sans code ni exécution.
- **Risques architecturaux :** faibles. La décision renforce la gouvernance sans modifier la Constitution ni l'organisation des agents/conseils.
- **Risques de maintenance :** un ARP par PR représente une charge rédactionnelle récurrente ; à surveiller pour éviter que l'ARP ne devienne formel. Le template atténue ce risque en standardisant l'effort.

## 8. Impact sur la Constitution

- **Articles concernés :** aucun article n'est modifié. La décision **prolonge** l'Article X (Gouvernance), l'Article XI (Processus de décision) et l'Article XII (Principes de qualité : documentation, traçabilité, explication).
- **Principes concernés :** Documentation (Principe 4), Validation humaine (Principe 5) et le Principe de délégation contrôlée (décision 004). Aucun principe n'est contredit ; tous sont renforcés.

## 9. Impact sur l'architecture

Aucun impact sur une architecture logicielle (le dépôt reste documentaire). Impact sur le **processus** :

```
... → Ouverture PR → [NOUVEAU] Production ARP → Revue Chief AI Architect → Validation CEO → Fusion
```

L'ARP s'insère comme artefact obligatoire entre l'ouverture de la PR et la revue.

## 10. Compatibilité

- **Documents de gouvernance** : `governance/git-workflow.md` mis à jour (8 étapes) ; cohérent avec `governance/roles.md` et `governance/README.md`.
- **Templates** : ajout non intrusif d'un nouveau template ; les templates existants sont inchangés.
- **`.github/PULL_REQUEST_TEMPLATE.md`** : non modifié ici ; il reste compatible mais pourra ultérieurement renvoyer explicitement à l'ARP (question ouverte).
- **PR ouvertes** : aucune autre PR ouverte à ce jour ; pas de rétro-compatibilité à assurer.

## 11. Tests effectués

- `git status` / `git diff --cached` : périmètre limité aux 6 fichiers attendus ; aucune suppression ni renommage de fichiers existants.
- Relecture des liens relatifs internes (template ↔ `reviews/packages/` ↔ `governance/git-workflow.md` ↔ `DECISIONS.md`).
- Vérification de la cohérence de la numérotation des étapes du workflow (1→8).
- Vérification que la Constitution (`docs/00-vision.md`) n'est pas modifiée.

## 12. Checklist

- [x] Documentation mise à jour
- [x] Standards respectés
- [x] Constitution respectée
- [x] Aucun conflit
- [x] Branche correcte
- [x] Pull Request correcte

## 13. Questions ouvertes

- Faut-il faire référence explicitement à l'ARP dans `.github/PULL_REQUEST_TEMPLATE.md` (ex. un champ « Lien vers l'ARP ») ?
- La convention de nommage doit-elle inclure la date en plus du numéro de PR (`PR-003-YYYYMMDD-...`) ?
- Un ARP est-il également requis pour les `hotfix/*` urgents, ou un format allégé est-il admis dans ce cas ?
- Le numéro de PR de ce document est **prévu à #003** ; à confirmer/renommer si GitHub attribue un autre numéro.

## 14. Recommandation de Claude Code

Je recommande l'**adoption** de cette Pull Request. Elle met en œuvre fidèlement la décision d'architecture 012, sans modifier la Constitution ni supprimer de contenu existant, avec un risque technique faible. Elle renforce la traçabilité et l'indépendance de la gouvernance vis-à-vis des outils externes, et applique la nouvelle règle dès sa propre revue. Sous réserve des questions ouvertes de la section 13 (mineures), la PR est prête pour la revue du Chief AI Architect puis la validation du CEO.
