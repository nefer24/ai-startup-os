# agents

Interfaces d'exécution d'agent : manifest de capacités et exécution sous moindre
privilège. Un agent produit des recommandations ; il ne décide jamais. Aucune
logique métier n'est implémentée ici.

## Contenu

Squelette uniquement :

- Contrat de manifest d'agent (capacités, permissions déclarées).
- Interfaces d'exécution d'agent respectant le principe de moindre privilège.
- Points d'intégration vers politiques, mémoire et audit.

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/components/02-agent-runtime.md`](../../../docs/components/02-agent-runtime.md)

## Invariant de gouvernance

Un agent recommande, il ne décide jamais. Il opère sous moindre privilège, dans
les limites de son manifest et des politiques pré-approuvées ; la CEO demeure
seule autorité humaine et seule décideuse. Toute action est auditée de façon
immuable.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
