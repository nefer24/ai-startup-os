# Cadre de mesure de la valeur métier

AI-SOS doit pouvoir mesurer **la valeur qu'il produit**, et pas seulement son bon fonctionnement
technique. Ce cadre définit **quoi** mesurer, **comment**, et surtout **contre quoi** — car la
mesure de valeur ne vaut que si elle échappe à l'auto-complaisance.

## Principe fondateur : une mesure externe, pas auto-notée

> Piège identifié (Revue n°1 & n°2) : les auto-évaluations du système finissent toujours au vert
> (les audits internes se notaient tous ~95/100). Une métrique de valeur **jugée par le système
> sur lui-même n'a aucun signal.**

Règle : **la qualité et l'utilité se mesurent contre un banc de référence externe** — un jeu de
demandes réelles dont la **réponse attendue est connue et indépendante du système** (« banc gold »).
Le système ne se note jamais lui-même sur la valeur.

## Les quatre dimensions demandées

### 1. Qualité des recommandations
- **Définition** : la recommandation est-elle complète, argumentée, sans erreur factuelle ?
- **Mesure** : score sur le banc gold (comparaison à une réponse de référence + grille de critères :
  options considérées, argumentation, avocat du diable, absence d'hallucination).
- **Évaluateur** : externe (banc gold + revue humaine échantillonnée), **jamais l'agent lui-même**.
- **Indicateur** : *taux de recommandations de qualité acceptable* (≥ seuil sur le banc).

### 2. Utilité métier
- **Définition** : la recommandation **résout-elle réellement** la demande ?
- **Mesure** : sur le banc gold, correspondance à l'issue attendue ; en production, signal du CEO
  (une recommandation `APPROUVE` sans ajustement est un signal fort d'utilité ; `REJETTE` un signal
  d'inutilité).
- **Indicateur** : *taux d'utilité* = recommandations jugées utiles / total.

### 3. Taux d'acceptation
- **Définition** : que fait le CEO de la recommandation ?
- **Mesure** : distribution des issues `Approuve / Ajuste / Reporte / Rejette` (données déjà
  produites par le flux de décision).
- **Nuance critique** : un taux d'acceptation de 100 % n'est **pas** un but — il signalerait un CEO
  passif ou un système trivial. On mesure aussi l'**ampleur des ajustements** : beaucoup d'`Ajuste`
  lourds = recommandations médiocres même si « acceptées ».
- **Indicateur** : *taux d'approbation sans ajustement* et *ampleur moyenne des ajustements*.

### 4. Impact réel
- **Définition** : la décision a-t-elle produit l'effet attendu, a posteriori ?
- **Mesure** : suivi différé (l'effet gouverné a-t-il tenu ? a-t-il fallu revenir dessus ?). En
  phase Slice, approximé par le banc gold ; en production, mesuré sur horizon réel.
- **Indicateur** : *taux de décisions non regrettées* (pas de retour arrière ultérieur).

## Métrique de synthèse : le coût par recommandation utile

La seule métrique qui **relie valeur et gouvernance économique** (ADR-0009) :

```
coût par recommandation utile = coût LLM total (ledger ADR-0009) / nombre de recommandations utiles (dim. 2)
```

C'est l'indicateur nord de la valeur : il dit si le moteur crée **plus** de valeur qu'il ne
consomme. Il n'a de sens que lorsque ADR-0009 (comptabilité des coûts) est en place.

## Métriques de gouvernance-valeur (spécifiques à AI-SOS)

Au-delà des quatre dimensions, deux métriques mesurent si la **gouvernance elle-même** est utile
(et pas seulement présente) :

- **Taux d'escalade justifiée** — quand l'agent doute et escalade au CEO, avait-il *raison* ?
  Un système qui escalade tout est inutile ; un qui n'escalade jamais est dangereux. Mesuré sur le
  banc gold (l'escalade était-elle appropriée ?). *La bonne valeur est intermédiaire.*
- **Taux de rattrapage adverse** — sur les cas dégénérés (scénarios F de la Slice), la gouvernance
  a-t-elle refusé/borné/escaladé ? Cible : **100 %**. C'est la métrique de robustesse de la
  gouvernance.

## Tableau récapitulatif

| Dimension | Indicateur clé | Source de vérité | Cible / lecture |
| --- | --- | --- | --- |
| Qualité | taux de qualité acceptable | banc gold + revue humaine | à établir, tendance ↑ |
| Utilité | taux d'utilité | banc gold + signal CEO | à établir, tendance ↑ |
| Acceptation | approbation sans ajustement ; ampleur des ajustements | flux de décision | ni 0 % ni 100 % |
| Impact | taux de décisions non regrettées | suivi différé | tendance ↑ |
| **Économie-valeur** | **coût par recommandation utile** | ledger ADR-0009 ÷ utilité | tendance ↓ |
| Gouvernance | taux d'escalade justifiée | banc gold | intermédiaire optimal |
| Gouvernance | taux de rattrapage adverse | scénarios F (Slice) | **100 %** |

## Mise en œuvre progressive

1. **Slice (M1)** — instrumenter la collecte (les données existent déjà : issues, audit) ;
   calculer le *taux de rattrapage adverse* et un *coût par recommandation* sur un mini-banc.
2. **M3–M4** — constituer un **banc gold** représentatif ; calculer qualité/utilité/escalade
   justifiée contre ce banc.
3. **M6** — intégrer ces métriques au re-scoring du projet, en remplacement des auto-audits.

## Ce que ce cadre change

Il ajoute au projet une **cinquième dimension d'évaluation** (décision du CEO) : la valeur produite,
mesurée **de l'extérieur**. Combiné à la robustesse technique déjà éprouvée, il permet de répondre à
la question qui compte désormais : *« ce noyau crée-t-il réellement de la valeur, et à quel coût ? »*
