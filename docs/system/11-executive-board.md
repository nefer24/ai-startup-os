# The Executive Board

> L'Executive Board est l'instance de direction humaine d'AI-SOS. Placé sous l'autorité du CEO, il traduit l'intention et la vision de ce dernier en priorités et en orientations claires, puis veille à leur cohérence d'ensemble. Il cadre le travail sans jamais s'y substituer : il recommande et oriente, mais la décision finale demeure celle du CEO. Les agents recommandent, l'humain décide.

## Position dans l'organisation

L'Executive Board occupe le deuxième niveau de la hiérarchie d'AI-SOS, immédiatement sous le CEO et au-dessus de l'Orchestrateur, conformément à l'Article VIII de la Constitution (Human CEO → Executive Board → Orchestrateur → Conseils d'Experts → Départements → Agents spécialisés).

Il constitue une instance de direction humaine rattachée au CEO. À ce titre, il n'est pas un agent : il prolonge et relaie la volonté humaine au sommet de l'organisation, servant de charnière entre l'intention du CEO et la mise en mouvement du travail assurée plus bas par l'Orchestrateur. Sa position détaillée dans l'architecture générale est présentée dans [`01-system-overview.md`](./01-system-overview.md).

## Mission

La mission de l'Executive Board est de traduire l'intention et la vision du CEO en priorités et en orientations exploitables par l'organisation, puis d'assurer la cohérence d'ensemble des travaux qui en découlent.

Il ne fixe pas les intentions — celles-ci appartiennent au CEO — mais il les met en forme : il transforme une direction stratégique en un cadre lisible, où chaque priorité est explicite et chaque orientation alignée avec les objectifs et les contraintes du plus haut niveau. Sa mission se résume en trois engagements :

- **Traduire** la vision du CEO en priorités et en orientations claires.
- **Cadrer** le travail de l'organisation dans le respect de l'intention humaine.
- **Assurer la cohérence** d'ensemble, afin que les travaux menés en dessous restent alignés entre eux et avec les objectifs fixés.

## Composition

L'Executive Board est une instance humaine. Il peut inclure le Chief AI Architect ainsi que d'autres responsables désignés par le CEO, selon les besoins de gouvernance.

Sa composition s'articule avec les rôles officiels de gouvernance décrits dans [`../governance/roles.md`](../governance/roles.md), où sont définies l'autorité et les responsabilités du CEO, du Chief AI Architect et des autres rôles. L'Executive Board n'introduit pas de nouvelle autorité concurrente : il réunit et coordonne, au service du CEO, les responsables désignés dont l'expertise éclaire le cadrage des priorités et la cohérence stratégique.

## Responsabilités

L'Executive Board porte des responsabilités de direction et de cadrage, distinctes de toute responsabilité de décision finale, laquelle demeure celle du CEO :

- **Arbitrage des priorités** : hiérarchiser les orientations et déterminer ce qui doit être traité en priorité, à partir de la vision du CEO.
- **Cohérence stratégique** : veiller à ce que les travaux menés dans l'organisation restent alignés entre eux et avec les objectifs du plus haut niveau.
- **Lien entre la volonté du CEO et le travail de l'Orchestrateur** : transmettre à l'Orchestrateur un cadre de priorités clair et recueillir les points qui doivent remonter vers le CEO.
- **Préparation de la décision humaine** : réunir et mettre en forme les éléments qui permettront au CEO de décider en connaissance de cause.

Ces responsabilités s'exercent toujours dans le respect de la validation humaine : l'Executive Board oriente et recommande, il ne se substitue pas à la décision du CEO.

## Entrées / Sorties

L'Executive Board reçoit :

- **L'intention et la vision du CEO** : les objectifs, orientations et contraintes fixés au sommet de l'organisation.
- **Les recommandations remontées** : les synthèses et propositions issues du travail de l'Orchestrateur, des Conseils d'Experts et des Départements.

Il produit :

- **Un ensemble de priorités** : ce qui doit être traité, dans quel ordre et avec quel niveau d'importance.
- **Un cadre d'orientation** : les principes et les limites qui guident le travail de l'Orchestrateur et, en dessous, celui de toute l'organisation.

Sa sortie majeure n'est pas une décision finale mais un cadre : un ensemble de priorités et d'orientations qui prépare et sert la validation humaine exercée par le CEO.

## Frontière avec l'Orchestrateur

La frontière entre l'Executive Board et l'Orchestrateur est nette et sans chevauchement.

L'Executive Board fixe **le QUOI est prioritaire et POURQUOI** : il détermine les orientations, hiérarchise les priorités et en explicite les raisons, au nom de l'intention du CEO. L'Orchestrateur, lui, organise **le COMMENT** : il assure la coordination du travail, compose les équipes d'Agents spécialisés et de Conseils d'Experts, séquence les étapes et fait converger les contributions vers une recommandation (voir [`02-orchestrator.md`](./02-orchestrator.md)).

Ainsi, l'un donne la direction et l'autre met en mouvement l'intelligence collective pour la suivre. Le Board ne coordonne pas le travail des agents ; l'Orchestrateur ne fixe pas les priorités stratégiques. Cette séparation garantit qu'aucune des deux instances n'empiète sur le rôle de l'autre.

## Résolution des conflits Board ↔ Orchestrateur

Des divergences peuvent apparaître entre l'Executive Board et l'Orchestrateur, notamment lorsque les contraintes de coordination rencontrent les priorités fixées.

Sur les priorités et les orientations, le Board prime : il appartient à l'Executive Board de dire ce qui est prioritaire et pourquoi, et l'Orchestrateur inscrit son travail dans ce cadre. Mais le Board ne tranche pas de sa propre autorité un désaccord de fond : tout désaccord qui ne peut être résolu au niveau du cadrage est remonté au CEO, à qui revient la décision finale au titre de la validation humaine (Article X de la Constitution : l'humain décide).

Aucune des deux instances ne force une issue au mépris de la gouvernance. Le conflit non résolu remonte fidèlement, il n'est ni dissimulé ni imposé.

## Place dans le flux de décision

L'Executive Board intervient à deux moments du processus de décision d'AI-SOS, décrit en détail dans [`08-decision-flow.md`](./08-decision-flow.md) : en amont, au cadrage des priorités, lorsqu'il traduit l'intention du CEO en orientations pour l'organisation ; et en aval, à la remontée vers le CEO, lorsqu'il contribue à préparer les recommandations en vue de la validation humaine.

Entre ces deux moments, le travail de coordination et de délibération se déroule sous la conduite de l'Orchestrateur et au sein des Conseils d'Experts. L'Executive Board n'interrompt pas ce cheminement : il en fixe le cadre au départ et en éclaire la restitution à l'arrivée, laissant au CEO la décision finale.

## Ce que l'Executive Board ne fait pas

Pour préserver la gouvernance humaine, le rôle de l'Executive Board est délibérément borné :

- **Il ne se substitue pas au CEO** pour les décisions finales importantes : il recommande et cadre, il ne décide pas à sa place.
- **Il ne fixe pas l'intention** : la vision et les objectifs appartiennent au CEO ; le Board les traduit, il ne les crée pas.
- **Il ne coordonne pas le travail des agents** : la coordination relève de l'Orchestrateur.
- **Il n'émet pas d'avis spécialisé** à la place des Conseils d'Experts et n'en réécrit pas les conclusions.
- **Il ne détient pas la responsabilité finale** : celle-ci demeure humaine et appartient au CEO, qui exerce la validation humaine.

Ces limites définissent la valeur de l'Executive Board : en cadrant les priorités et en assurant la cohérence stratégique sans jamais confisquer la décision, il garantit que la volonté du CEO irrigue toute l'organisation, dans le respect du principe fondateur selon lequel les agents recommandent et l'humain décide.

---

## Références croisées

- [`00-glossary.md`](./00-glossary.md) — définitions des termes d'AI-SOS.
- [`01-system-overview.md`](./01-system-overview.md) — vision globale et architecture générale.
- [`02-orchestrator.md`](./02-orchestrator.md) — rôle et fonctionnement de l'Orchestrateur.
- [`08-decision-flow.md`](./08-decision-flow.md) — processus de décision d'AI-SOS.
- [`../governance/roles.md`](../governance/roles.md) — rôles officiels de gouvernance.
