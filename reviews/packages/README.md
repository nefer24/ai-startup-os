# AI Review Packages (ARP)

> The official archive of AI Review Packages of AI-SOS.

Ce dossier contient les **AI Review Packages (ARP)** d'AI-SOS. L'ARP est un **livrable officiel** du projet, institué par la décision d'architecture [012](../../DECISIONS.md).

## Pourquoi l'ARP existe

Les outils externes (GitHub, connecteurs, plateformes IA, APIs, etc.) peuvent présenter des limitations techniques ou des délais de synchronisation. **La gouvernance d'AI-SOS ne doit jamais dépendre de ces limitations.**

L'AI Review Package rend chaque revue **autoportante** : il contient, dans un document unique et versionné, toutes les informations nécessaires à la revue d'architecture. Ainsi, la revue reste possible même si un outil externe est indisponible, incomplet ou désynchronisé.

## Rôle officiel

- Chaque **Pull Request** doit produire un ARP à partir du template officiel [`templates/review-package-template.md`](../../templates/review-package-template.md).
- Avant toute demande de revue au **Chief AI Architect**, **Claude Code** doit toujours produire l'ARP correspondant.
- L'ARP est la **source officielle d'information** lors des revues.
- Le **connecteur GitHub** devient un **outil de vérification complémentaire**, et non la source primaire.
- Le Chief AI Architect utilise l'ARP comme **référence principale** pour la revue d'architecture ; le CEO s'appuie sur l'ARP et la recommandation qu'il contient pour sa validation finale.

## Processus

1. Claude Code réalise le travail sur une branche `feature/*` (ou `bugfix/*`, etc.).
2. Claude Code rédige l'ARP à partir du template et le dépose dans ce dossier.
3. L'ARP accompagne la Pull Request (référencé dans sa description).
4. Le Chief AI Architect effectue sa revue en s'appuyant d'abord sur l'ARP.
5. Le CEO valide ; aucune fusion n'a lieu avant son autorisation explicite.

## Convention de nommage

Un ARP est nommé selon le numéro de la Pull Request qu'il documente :

```
reviews/packages/PR-<numéro>-<titre-court>.md
```

Exemple : `reviews/packages/PR-003-ai-review-package.md`.

Chaque ARP est conservé dans ce dossier afin d'assurer la traçabilité exigée par la Constitution : il constitue la mémoire durable des revues, indépendante de tout outil externe.

## Contenu d'un ARP

Chaque ARP contient obligatoirement les 14 sections définies par le template officiel : Executive Summary, Objectifs, Fichiers modifiés, Changements importants, Raisons des choix, Alternatives étudiées, Risques, Impact sur la Constitution, Impact sur l'architecture, Compatibilité, Tests effectués, Checklist, Questions ouvertes, et Recommandation de Claude Code.
