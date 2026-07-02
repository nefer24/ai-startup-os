# security

Interfaces de sécurité et de permissions : authentification OIDC/JWT de la CEO,
comptes de service, RBAC et manifest d'agent. Cette couche définit les contrats
d'autorisation ; elle ne contient aucune implémentation ni logique métier.

## Contenu

Squelette uniquement :

- Contrats d'authentification de la CEO (OIDC/JWT).
- Contrats de comptes de service (identités non humaines).
- Contrats RBAC (rôles et permissions).
- Contrat de manifest d'agent (permissions déclarées, moindre privilège).

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/implementation/08-security-and-permissions.md`](../../../docs/implementation/08-security-and-permissions.md)
- [`../../../docs/api/02-authentication.md`](../../../docs/api/02-authentication.md)

## Invariant de gouvernance

La sécurité fait respecter les bornes CEO-only : seule la CEO détient l'autorité
de décision. Les agents et comptes de service opèrent sous moindre privilège,
dans les limites de leur manifest et des politiques pré-approuvées.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
