# Policy Evaluation Workflow

> Workflow d'évaluation des politiques à l'exécution — le moteur de politiques déterministe de la couche core — qui classe, route, teste l'éligibilité d'une politique pré-approuvée et exécute le quality gate, indépendamment de LangGraph.

Ce document spécifie le **workflow runtime** du moteur de politiques : la traduction, en états et transitions traduisibles en LangGraph (DT-02), du contrat interne de [`../components/04-policy-engine.md`](../components/04-policy-engine.md). Il respecte la Baseline v1.0 ([`../BASELINE-v1.0.md`](../BASELINE-v1.0.md)) et les politiques 07–09 sans introduire de code ni de nouveau choix technologique. Le moteur vit **hors du graphe** : il alimente les nœuds de routage et l'arête conditionnelle de politique, sans en dépendre. Il **classe, route et évalue ; il ne décide jamais et ne fixe jamais les seuils** — il les lit dans la configuration approuvée par le CEO seul. Ses sorties suivent [`../contracts/06-policy-result-schema.md`](../contracts/06-policy-result-schema.md).

## États

Le moteur est **sans état propre** et **déterministe** : à entrées et configuration identiques, sorties identiques. Les trois évaluations d'axes peuvent s'exécuter en parallèle (fan-out), puis sont agrégées par préséance.

```text
                              request + recommandation
                                        │
                                    ┌───────┐
                                    │ Reçu  │
                                    └───┬───┘
                                        ▼  (fan-out parallèle)
                 ┌──────────────────────┼──────────────────────┐
                 ▼                      ▼                       ▼
        ┌────────────────┐   ┌────────────────┐      ┌────────────────┐
        │ Éval. complexité│  │  Éval. risque  │      │Éval. incertitude│
        └────────┬───────┘   └───────┬────────┘      └───────┬────────┘
                 └──────────────────┬─┴───────────────────────┘
                                    ▼
                       ┌────────────────────────┐
                       │ Préséance inter-axes    │  (max, jamais moyenne)
                       └───────────┬────────────┘
                                   ▼
                       ┌────────────────────────┐
                       │ Classification (4 cl.)  │  doute ─▶ défaut conservateur
                       └───────────┬────────────┘                 │
                                   ▼                               ▼
                       ┌────────────────────────┐         ┌──────────────┐
                       │  Routage (mode valid.)  │         │  ceo_direct  │
                       └───┬────────────────┬───┘         │ (forcé)      │
              structurante/│                │courante /    └──────────────┘
                 critique  │                │importante
                    ceo_direct              ▼
                       │       ┌────────────────────────┐  inéligible ─▶ ceo_direct
                       │       │ Éligibilité de politique│  (active + plafonds
                       │       │ (active+plafonds+fenêtre)│   + fenêtre cumulée)
                       │       └───────────┬────────────┘
                       │                   ▼ éligible
                       └──────────▶┌────────────────────────┐  échoué ─▶ retour
                                   │      QualityGate        │  délibération
                                   └───────────┬────────────┘
                                               ▼ passé
                                        ┌────────────┐
                                        │  Résultat  │
                                        └────────────┘
```

| État | Signification | Sortie |
| --- | --- | --- |
| **Reçu** | demande + recommandation admises | → 3 évaluations d'axes |
| **Éval. complexité / risque / incertitude** | niveaux issus des politiques 01–03 | → Préséance inter-axes |
| **Préséance inter-axes** | agrégation par l'axe le plus contraignant | → Classification |
| **Classification** | rattachement à l'une des 4 classes + `precedence_axis` | → Routage ; → défaut conservateur |
| **Routage** | `mode ∈ {ceo_direct, preapproved_policy}` | → Éligibilité (délégation) ; → QualityGate (ceo_direct) |
| **Éligibilité de politique** | active + plafonds unitaire/cumulé + fenêtre glissante | → QualityGate ; → ceo_direct (inéligible) |
| **QualityGate** | vérification de maturité de la recommandation | → Résultat ; → retour délibération |
| **Résultat** | `Classification` + `ValidationRouting` (+ `PolicyEligibility`) + `QualityGateResult` | terminal |

Le suivi d'une décision « en vol » (report, aggravation, révocation de politique) est porté par l'état du flux d'orchestration, pas par le moteur : celui-ci se contente de ré-évaluer à chaque point de contrôle. Dès qu'une re-classification fait sortir un cas des classes éligibles ou franchir un plafond, le traitement par politique **cesse**, même si une validation par politique avait démarré.

## Transitions

Les transitions sont déterministes : chaque sortie repose sur des critères nommés et vérifiables, jamais sur une appréciation de convenance. Le moteur ré-évalue à chaque point de contrôle plutôt que de conserver une décision « en vol ».

- **Agrégation par préséance** : la classe retenue suit **l'axe le plus contraignant** (max), jamais une moyenne ; `precedence_axis` nomme l'axe déterminant. Le plancher de risque est un minimum, jamais un plafond.
- **Structurante/critique → `ceo_direct` forcé** : ces classes ne passent jamais par l'éligibilité de politique ; le routage vers le CEO est structurel.
- **Défaut conservateur FORT** : tout doute (entrée incomplète, seuils absents, contrôle indépendant absent) porte la classe au minimum à **structurante** et route vers le CEO ; le doute ne descend jamais la classe.
- **Politique inéligible → `ceo_direct`** : politique inactive/expirée, hors périmètre, plafond cumulé dépassé ou classe non délégable ⇒ application par politique **arrêtée**, remontée au CEO.
- **Re-classification en vol** : une classe qui s'aggrave en cours de traitement abandonne tout routage allégé déjà engagé et reroute vers le CEO avec les garanties de sa nouvelle classe.
- **QualityGate échoué → retour délibération** : une recommandation sous le seuil (documentation, cohérence de fond, avocat du diable de façade, lacune critique) est renvoyée en délibération, jamais présentée au CEO. Une classe critique passe systématiquement par la porte qualité, et l'avocat du diable est obligatoire pour structurante et critique.
- **Interdiction de sous-qualifier** : abaisser une classe pour éviter le CEO, ou fractionner une décision structurante en fragments courants, est une anomalie traitée par requalification vers le haut puis remontée au CEO.

## Entrées et sorties

Tout ce qui influence une évaluation vit soit dans l'entrée, soit dans le registre de politiques et la configuration de bornes, tous deux versionnés — jamais dans un cache décisionnel opaque. C'est ce qui rend le moteur rejouable à l'identique pour l'audit.

| Sens | Élément | Contrainte |
| --- | --- | --- |
| Entrée | demande (`request`) | axes complexité/risque/incertitude évalués (politiques 01–03) |
| Entrée | recommandation | rubriques observables consignées (documentation, risques, désaccords) |
| Entrée | registre de politiques versionné | lu, jamais écrit par le moteur (`PreapprovedPolicy`) |
| Entrée | `BoundsConfig` CEO-only | seuils, plafonds, fenêtre et unité de portée cumulée |
| Sortie | `Classification` | `derived_class` = axe le plus contraignant ; ≥ plancher de risque |
| Sortie | `ValidationRouting` | `mode` ; `policy_ref` obligatoire si `preapproved_policy` |
| Sortie | `PolicyEligibility` | présente en cas de délégation ; `eligible` exige `within_caps` + active |
| Sortie | `QualityGateResult` | `passed=false` ⇒ `returned_to_deliberation=true` |

Les schémas exacts (champs, contraintes, invariants) figurent dans [`../contracts/06-policy-result-schema.md`](../contracts/06-policy-result-schema.md). Toute classification référence `protocol_version` et `policy_version` pour le rejeu et l'audit.

## Erreurs

Posture **conservatrice par défaut** : toute situation ambiguë, incomplète ou hors cadre se résout **vers le CEO**, jamais vers un routage allégé. Les erreurs suivent le format standard de [`../contracts/06-policy-result-schema.md`](../contracts/06-policy-result-schema.md).

| Situation | Traitement | Résultat |
| --- | --- | --- |
| Entrée incomplète (axes/critères manquants) | traitée comme incertitude élevée | `ConservativeDefault` → CEO |
| Politique inactive ou expirée | non applicable ; ne « revit » pas seule | `policy.rejected` → CEO |
| Plafond cumulé dépassé (fenêtre glissante) | application par politique arrêtée | `policy.rejected` → interrupt CEO |
| Seuils absents de la config | défaut conservateur appliqué | route vers le CEO |
| Deux politiques en conflit | ambiguïté ; aucune ne prime | `policy.rejected` → CEO |
| Absence d'instance de contrôle indépendante | backstop | `independent_check=absent` → CEO |
| QualityGate sous le seuil | retour en délibération | `quality_gate.failed`, rien au CEO |

Une erreur ne dégrade jamais la gouvernance ; au pire, elle sur-sollicite l'unique décideur, ce qui est le côté sûr. Une politique révoquée « en vol » ne peut fonder l'achèvement d'une validation : la validation est suspendue et remontée au CEO. Une recommandation « bien rangée mais fausse » (rubriques présentes mais raisonnement incohérent) échoue sur le critère de cohérence de fond du gate.

## Événements

Chaque acte de gouvernance produit un événement immuable vers l'audit (DT-06), enveloppe commune de [`../contracts/02-event-catalog.md`](../contracts/02-event-catalog.md), de sorte qu'une décision passée reste interprétable : on peut reconstituer la classe retenue, le mode de validation, la politique éventuellement appliquée et le verdict du gate.

| Événement | Signification |
| --- | --- |
| `classification.done` | classe proposée puis confirmée par contrôle indépendant |
| `policy.evaluated` | politique candidate jugée éligible pour une décision |
| `policy.rejected` | politique inactive, hors périmètre, ou plafond/fenêtre dépassé → CEO |
| `quality_gate.passed` | recommandation conforme, présentable au CEO |
| `quality_gate.failed` | recommandation renvoyée en délibération (critères manquants consignés) |
| `conservative_default.applied` | un doute a porté la classe à structurante et routé vers le CEO |

Toute décision validée par politique référence l'identifiant et la version de la politique appliquée (`policy.applied`), jamais une politique absente du registre ou sans version active. Les validations par politique restent soumises à un audit a posteriori par échantillonnage, destiné à détecter les misclassifications : décision qui aurait dû être remontée au CEO mais traitée par politique, condition mal appréciée, plafond franchi sans détection.

## Invariants

Ces invariants sont, autant que possible, rendus **structurels** par les contraintes de schéma du modèle de données ([`../contracts/06-policy-result-schema.md`](../contracts/06-policy-result-schema.md)) : ils ne dépendent pas de la seule discipline du code applicatif, mais du fait que le graphe n'offre qu'un chemin de reprise (endpoint CEO) et une exception (arête de politique), toutes deux journalisées.

- **Structurante/critique jamais déléguées** : `derived_class ∈ {structurante, critique}` ⇒ `mode = ceo_direct` ; aucune `policy_ref` admise. Aucune politique, ni combinaison, ne les couvre.
- **Délégation ⇔ politique active et dans ses plafonds** : `eligible=true` exige `within_caps=true` **ET** politique active, pour une classe éligible (courante, ou importante en cadre étroit).
- **Défaut conservateur FORT** : le doute ne descend jamais la classe et **atteint toujours le CEO** ; la charge de la preuve pèse sur la recommandation.
- **Le moteur ne fixe pas les seuils** : il les **lit** ; seul le CEO crée, assouplit ou reconduit une politique et fixe les seuils de routage (CEO-only).
- **Le gate ne décide pas** : il conditionne la présentation, jamais la validation ; une décision pré-approuvée n'est jamais exemptée de documentation, de traçabilité ni d'auditabilité.
- **Contrôle indépendant** : l'auteur ne contrôle jamais sa propre classe ni son franchissement du gate ; à défaut d'instance indépendante, remontée au CEO (backstop, jamais d'auto-contrôle).
- **Indépendant de LangGraph** : la logique de gouvernance vit dans la couche core ; elle ne dépend d'aucun construct du graphe d'exécution.
- **Déterminisme et rejouabilité** : à entrées et configuration identiques, classification et routage sont identiques ; toute évaluation est reproductible pour l'audit.
- **Classification préalable au gate** : le niveau d'exigence du quality gate dépend de la classe déterminée en amont ; une décision pré-approuvée n'est jamais exemptée de documentation, de traçabilité ni d'auditabilité.

## Questions ouvertes (CEO)

Ces points relèvent de la décision du CEO ; le moteur applique par défaut la posture conservatrice tant qu'ils ne sont pas tranchés et calibrés dans [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md).

1. **Cadre étroit** : comment délimiter le cadre autorisant une politique à valider une décision « importante » sans qu'il ne s'élargisse jusqu'à vider la classe de sa substance (articulation avec [`../policies/08-preapproved-policy.md`](../policies/08-preapproved-policy.md)) ?
2. **Portée cumulée** : quelle unité commune de portée et quelle fenêtre de rattachement pour le plafond cumulé lorsque les décisions sont hétérogènes (dépense, temps, effet sur des tiers) ?
3. **Seuils du quality gate** : quels seuils de confiance minimaux par classe le CEO entérine-t-il pour le `score`, conformément à [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) ?
4. **Fréquence de re-classification** : à quelle fréquence exécuter le point de contrôle de re-classification des décisions validées par politique pour capter une aggravation sans surveiller inutilement des cas stables ?
5. **Échantillonnage de l'audit a posteriori** : quel taux retenir pour détecter les misclassifications sans surcharge, et à quelle fréquence de revalidation par défaut ?
6. **Frontière structurante/critique** : où placer la frontière opérationnelle entre structurante et critique, alors que les deux exigent déjà le CEO et l'avocat du diable ?
7. **Notification** : faut-il notifier systématiquement le CEO de chaque application de politique, ou seulement des remontées, re-classifications et résultats d'audit ?
