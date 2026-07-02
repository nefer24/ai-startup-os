# Policy Result Schema

> Format standard des résultats produits par le moteur de politiques : classification, routage, éligibilité, quality gate et défaut conservateur, en traduction fidèle du contrat interne du composant.

Ce document fige les **schémas de sortie** du moteur de politiques, en cohérence stricte avec [`../components/04-policy-engine.md`](../components/04-policy-engine.md). Il n'introduit aucun code métier ni choix technologique : il traduit en types abstraits les interfaces `classify`, `route`, `evaluate_policy` et `quality_gate`, ainsi que le défaut conservateur, selon [`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md) et [`../policies/09-quality-gate-policy.md`](../policies/09-quality-gate-policy.md). Les erreurs éventuelles suivent le format de [`./05-error-catalog.md`](./05-error-catalog.md). Types associés : voir [`./01-domain-schemas.md`](./01-domain-schemas.md). Le moteur **classe, route et évalue ; il ne décide jamais et ne fixe jamais les seuils** — il les lit dans la configuration approuvée par le CEO.

## Classification

Sortie de `classify(request)` : la classe **proposée** à partir des trois axes et des critères observables, avant ou après contrôle indépendant.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `request_id` | UUID | oui | référence une demande existante | Demande évaluée. |
| `complexity` | enum{faible,modéré,élevé,critique} | oui | issu de la politique de complexité (01) | Niveau de complexité évalué. |
| `risk` | enum{faible,modéré,élevé,critique} | oui | issu de la politique de risque (02) ; impose le plancher de classe | Niveau de risque évalué. |
| `uncertainty` | enum{faible,modéré,élevé,critique} | oui | issu de la politique d'incertitude (03) | Niveau d'incertitude évalué. |
| `derived_class` | enum{courante,importante,structurante,critique} | oui | = axe le plus contraignant (max, jamais moyenne) ; ≥ plancher de risque | Classe retenue par préséance inter-axes. |
| `precedence_axis` | enum{complexity,risk,uncertainty} | oui | nomme l'axe qui fixe `derived_class` | Axe déterminant de la préséance. |
| `rationale` | array<string> | oui | ≥ 1 critère observable cité (impact, irréversibilité, portée, engagement) | Justifications concrètes du rattachement. |
| `independent_check` | enum{confirmé,requalifié_haut,absent} | non | `absent` ⇒ remontée CEO (backstop) | Résultat du contrôle indépendant de classe. |
| `protocol_version` | string | oui | version du protocole de classification | Traçabilité du protocole appliqué. |
| `policy_version` | string | oui | version de la config de bornes/politiques lue | Traçabilité de la configuration. |

```json
{
  "request_id": "3f2a9c1e-7b04-4d8e-9a11-2c6d5f0e8b73",
  "complexity": "modéré",
  "risk": "élevé",
  "uncertainty": "modéré",
  "derived_class": "structurante",
  "precedence_axis": "risk",
  "rationale": ["risque élevé impose au moins structurante", "engagement durable créant un précédent"],
  "independent_check": "confirmé",
  "protocol_version": "classif-1.0",
  "policy_version": "bounds-2026.02"
}
```

## ValidationRouting

Sortie de `route(classification)` : le mode de validation déduit de la classe confirmée.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `mode` | enum{ceo_direct,preapproved_policy} | oui | structurante/critique ⇒ `ceo_direct` (jamais `preapproved_policy`) | Mode de validation retenu. |
| `policy_ref` | object{policy_id:UUID, version:string} | conditionnel | **obligatoire si** `mode = preapproved_policy` ; nul sinon | Politique pré-approuvée appliquée. |
| `reason` | string | oui | explicite le lien classe → mode | Justification du routage. |

```json
{
  "mode": "ceo_direct",
  "policy_ref": null,
  "reason": "Classe structurante : validation directe du CEO obligatoire, aucune politique éligible."
}
```

## PolicyEligibility

Sortie de `evaluate_policy(decision, policy)` : éligibilité d'une politique candidate pour une décision.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `policy_id` | UUID | oui | référence le registre versionné | Politique évaluée. |
| `eligible` | boolean | oui | `true` exige `within_caps=true` ET politique active | Verdict d'éligibilité. |
| `within_caps` | boolean | oui | plafond unitaire ET cumulé respectés | Respect des plafonds. |
| `cumulative_usage` | number | oui | ≥ 0 ; mesuré sur `window` | Portée cumulée consommée (anti-fractionnement). |
| `window` | string | oui | fenêtre glissante de rattachement | Fenêtre du plafond cumulé. |
| `rejection_reason` | enum{inactive,out_of_scope,cap_exceeded,class_not_delegable,conflict} | conditionnel | **obligatoire si** `eligible=false` ; nul sinon | Motif de non-éligibilité. |

```json
{
  "policy_id": "0a5c8e2d-1f34-49b7-8c60-9d2e7a4b1f05",
  "eligible": false,
  "within_caps": false,
  "cumulative_usage": 10500,
  "window": "30d",
  "rejection_reason": "cap_exceeded"
}
```

## QualityGateResult

Sortie de `quality_gate(recommendation)` : verdict de présentabilité au CEO.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `passed` | boolean | oui | `passed=false` ⇒ `returned_to_deliberation=true` | Recommandation présentable ou non. |
| `score` | number | non | dans l'intervalle de la config ; le moteur **ne fixe pas** le seuil | Score agrégé indicatif. |
| `criteria` | array<object{name:string, satisfied:boolean}> | oui | couvre documentation, cohérence de fond, désaccords, traçabilité, confiance, risques, avocat du diable, lacune critique | État de chaque critère observable. |
| `failures` | array<string> | conditionnel | non vide si `passed=false` ; vide sinon | Critères manquants consignés. |
| `returned_to_deliberation` | boolean | oui | `true` ⇔ `passed=false` | Renvoi en délibération (rien n'atteint le CEO). |

```json
{
  "passed": false,
  "score": 0.62,
  "criteria": [
    {"name": "documentation_complete", "satisfied": true},
    {"name": "coherence_de_fond", "satisfied": false},
    {"name": "avocat_du_diable", "satisfied": false}
  ],
  "failures": ["coherence_de_fond", "avocat_du_diable"],
  "returned_to_deliberation": true
}
```

## ConservativeDefault

Sortie émise lorsque le défaut conservateur FORT s'applique : tout doute porte la classe au minimum à structurante et route vers le CEO.

| Champ | Type logique | Obligatoire | Contrainte / invariant | Description |
| --- | --- | --- | --- | --- |
| `triggered` | boolean | oui | `true` ⇒ `forced_mode = ceo_direct` | Le défaut conservateur a été appliqué. |
| `reason` | string | oui | doute, entrée incomplète, seuils absents, absence de contrôle indépendant | Cause du repli conservateur. |
| `forced_class` | enum{structurante,critique} | oui | jamais inférieure à structurante | Classe imposée par le repli. |
| `forced_mode` | enum{ceo_direct} | oui | valeur unique `ceo_direct` | Mode forcé vers le CEO. |

```json
{
  "triggered": true,
  "reason": "Axes incomplets : incertitude traitée comme élevée, remontée au CEO.",
  "forced_class": "structurante",
  "forced_mode": "ceo_direct"
}
```

## Invariants

- **Défaut conservateur ⇒ `ceo_direct`.** Dès que `ConservativeDefault.triggered=true`, `forced_class ≥ structurante` et `forced_mode = ceo_direct` : le doute atteint toujours le CEO.
- **Structurante/critique jamais déléguées.** `derived_class ∈ {structurante, critique}` ⇒ `ValidationRouting.mode = ceo_direct` ; aucune `policy_ref` admise.
- **Éligibilité conditionnée.** `PolicyEligibility.eligible=true` exige `within_caps=true` **ET** politique active ; toute violation force `eligible=false` avec `rejection_reason`.
- **Quality gate échoué ⇒ retour délibération.** `passed=false` implique `returned_to_deliberation=true` et un `failures` non vide ; rien ne passe au CEO.
- **Préséance, jamais moyenne.** `derived_class` suit l'axe le plus contraignant ; `precedence_axis` le nomme ; le plancher de risque est un minimum.
- **Le moteur ne fixe pas les seuils.** `score` et les plafonds sont lus dans la config CEO-only ; le moteur classe, route et évalue, il ne décide jamais.
- **Déterminisme.** À entrées et configuration identiques, ces sorties sont identiques ; aucune part d'aléatoire ne modifie une classe.
- **Traçabilité.** `protocol_version` et `policy_version` accompagnent toute classification pour rejeu et audit.

## Erreurs possibles

Les erreurs suivent le format standard de [`./05-error-catalog.md`](./05-error-catalog.md) :

- **Axes ou critères manquants** → `validation.invalid_input` traité comme incertitude élevée → `ConservativeDefault` déclenché → remontée CEO.
- **Politique inactive/expirée** → `policy.inactive` ; jamais d'éligibilité.
- **Plafond cumulé dépassé** → `policy.cap_exceeded` → interrupt CEO, même si chaque cas isolé restait sous son plafond unitaire.
- **Tentative de délégation d'une structurante/critique** → `policy.class_not_delegable` (rejet structurel).
- **Deux politiques en conflit** → `policy.conflict` → remontée CEO ; aucune ne prime.
- **Seuils absents de la config** → défaut conservateur appliqué plutôt que décision sur seuil indéfini.
- **Absence d'instance de contrôle indépendante** → backstop : `independent_check=absent` → remontée CEO.
- **Recommandation « bien rangée mais fausse »** → `quality_gate.not_passed` sur le critère de cohérence de fond → retour délibération.

## Questions ouvertes (CEO)

- Quels **seuils de confiance minimaux par classe** entériner pour le `score` du quality gate, conformément à [`../behavior/09-error-handling.md`](../behavior/09-error-handling.md) et aux bornes calibrées par le CEO ?
- Faut-il exposer le `score` de `QualityGateResult` dans le dossier CEO, ou seulement le verdict `passed` et les `failures` ?
- Quelle **unité commune de portée** et quelle **fenêtre** normaliser dans `cumulative_usage`/`window` lorsque les décisions sont hétérogènes (dépense, temps, effet sur tiers) ?
- Le champ `precedence_axis` doit-il pouvoir désigner plusieurs axes ex æquo, ou toujours un axe unique par convention de priorité ?
- Faut-il consigner un `ConservativeDefault` distinct dans l'audit à chaque déclenchement, ou l'agréger à l'événement `classification.done` correspondant ?
