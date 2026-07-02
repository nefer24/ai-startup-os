# policies

Interfaces du Policy Engine : classification des décisions en quatre classes,
quality gate et politiques pré-approuvées. Cette couche core est indépendante du
framework et ne contient aucune logique métier.

## Contenu

Squelette uniquement :

- Contrats de classification des décisions (quatre classes).
- Interface de quality gate (contrôle de conformité avant remise).
- Contrats des politiques pré-approuvées encadrant la délégation.
- Modèle de résultat de politique (déclaratif).

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/components/04-policy-engine.md`](../../../docs/components/04-policy-engine.md)
- [`../../../docs/policies/07-decision-classification-policy.md`](../../../docs/policies/07-decision-classification-policy.md)
- [`../../../docs/contracts/06-policy-result-schema.md`](../../../docs/contracts/06-policy-result-schema.md)

## Invariant de gouvernance

La délégation ne s'opère qu'au travers de politiques pré-approuvées ; hors de ce
cadre, la décision revient à la CEO, seule autorité humaine. Le Policy Engine
classe et recommande, il ne se substitue jamais à la décision.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
