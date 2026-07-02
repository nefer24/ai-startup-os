# runtime

Assemblage d'exécution du système. En Phase 13, ce package est un placeholder :
il fixe les points d'assemblage et les contrats d'exécution, mais aucun workflow
n'y est implémenté et aucune logique métier n'y figure.

## Contenu

Squelette uniquement :

- Points d'assemblage du modèle d'exécution (câblage des composants).
- Contrats de cycle de vie d'exécution (démarrage, arrêt).
- Placeholder : aucun graphe ni workflow implémenté à ce stade.

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/implementation/02-runtime-model.md`](../../../docs/implementation/02-runtime-model.md)
- [`../../../docs/runtime/01-runtime-overview.md`](../../../docs/runtime/01-runtime-overview.md)

## Invariant de gouvernance

L'assemblage d'exécution devra préserver les bornes CEO-only et l'audit immuable :
aucun chemin d'exécution ne saurait contourner la décision de la CEO ni la
journalisation append-only.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
