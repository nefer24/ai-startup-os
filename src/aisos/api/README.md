# api

Interfaces de l'API : contrats d'endpoints exposant le système. Les endpoints
sensibles sont réservés à la CEO (CEO-only). Cette couche déclare les contrats ;
elle ne contient aucun handler ni logique métier.

## Contenu

Squelette uniquement :

- Contrats d'endpoints (requêtes, décisions, agents, Conseils, mémoire, audit,
  flux d'événements).
- Marquage des endpoints sensibles comme CEO-only.
- Alignement avec les schémas d'API (formes de requête/réponse).

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/api/01-api-overview.md`](../../../docs/api/01-api-overview.md)
- [`../../../docs/api/04-decision-endpoints.md`](../../../docs/api/04-decision-endpoints.md)
- [`../../../docs/contracts/04-api-schemas.md`](../../../docs/contracts/04-api-schemas.md)

## Invariant de gouvernance

Les endpoints de décision sont CEO-only : la CEO est seule autorité humaine et
seul décideur. L'API expose les recommandations des agents mais ne leur délègue
aucune décision hors des politiques pré-approuvées.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
