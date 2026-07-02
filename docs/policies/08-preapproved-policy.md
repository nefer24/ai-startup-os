# Pre-Approved Policies

> Cette politique définit comment fonctionnent les **politiques pré-approuvées par le CEO** au sein d'AI-SOS. Une politique pré-approuvée est un cadre écrit, décidé par le CEO, qui autorise à l'avance le traitement de certaines décisions de faible portée sans nouvelle sollicitation. Le CEO reste la seule autorité humaine et le seul décideur : la validation graduée renvoie uniquement vers ces politiques qu'il a lui-même approuvées, jamais vers un autre humain (il n'en existe pas) ni vers un agent. Aucun agent ne reçoit d'autorité de décision. Voir [`../behavior/11-decision-classification-and-policies.md`](../behavior/11-decision-classification-and-policies.md).

## Objectif

L'objectif est de préciser ce qu'est une politique pré-approuvée, ce qu'elle peut couvrir, et comment elle vit dans le temps.

**Doctrine centrale : une politique pré-approuvée du CEO EST la validation humaine du CEO, exprimée par avance.** Lorsqu'une décision est traitée au titre d'une politique pré-approuvée, elle n'est pas validée « à la place » du CEO ni « automatiquement » sans lui : elle est validée **par une décision que le CEO a lui-même prise en amont, par écrit, et rendue réutilisable**. C'est à ce titre que la validation par politique pré-approuvée du CEO satisfait l'exigence de validation humaine (R5.1) : la signature humaine n'est pas absente, elle est **anticipée**. La politique ne remplace pas le CEO ; elle matérialise et diffère dans le temps une décision déjà prise par lui.

Une politique pré-approuvée permet ainsi d'éviter de solliciter le CEO pour chaque décision courante et répétitive, tout en garantissant qu'il conserve le contrôle : c'est lui qui décide, en amont et par écrit, des cas où une réponse peut être appliquée sans le consulter à nouveau.

Ce document couvre :

- les **critères** qui déterminent ce qu'une politique a le droit de couvrir ;
- les **règles** de format, de registre, de cycle de vie et de garde-fous cumulés ;
- des **exemples** d'application et de sortie de cadre ;
- les **cas limites** de conflit, de péremption et de révocation.

Il ne couvre pas la manière de classer une décision : cela relève de [`07-decision-classification-policy.md`](./07-decision-classification-policy.md).

## Critères

Une politique ne peut être créée que si les critères observables suivants sont réunis.

**Classes de portée éligibles.** La classification retient quatre classes de décision : **courante**, **importante**, **structurante** et **critique**. Seules deux classes sont éligibles à la validation par politique pré-approuvée du CEO :

- les décisions **courantes** : répétitives, à effet réversible et circonscrit ;
- les décisions **importantes**, mais **uniquement dans un cadre étroit explicitement défini par le CEO** : périmètre nommé, conditions serrées, plafond bas.

La classe visée doit être nommée explicitement selon la classification de [`07-decision-classification-policy.md`](./07-decision-classification-policy.md).

**Exclusion permanente des décisions structurantes et critiques.** Une politique ne peut **jamais** couvrir une décision **structurante** ou **critique** : engagement durable, effet difficilement réversible, impact sur la stratégie, sur la sécurité, sur les finances au-delà d'un seuil, ou sur des tiers de manière significative. Ces deux classes sont **toujours exclues**, sans exception, et restent remontées au CEO.

**Conditions vérifiables.** Le champ d'application doit reposer sur des conditions observables et vérifiables sans jugement discrétionnaire : on doit pouvoir répondre par oui ou par non à la question « ce cas entre-t-il dans la politique ? » à partir de faits constatables.

**Plafond de portée explicite.** Toute politique fixe un plafond de portée au-delà duquel elle ne s'applique plus (voir les seuils de référence dans [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)). En l'absence de plafond chiffrable, la politique n'est pas valide.

**Origine humaine unique — les seuils de routage relèvent du CEO seul.** Une politique n'existe que si le CEO l'a créée et approuvée. Aucune politique ne se crée d'elle-même : aucun agent ni aucun mécanisme ne peut en générer une, l'élargir, en abaisser les seuils ou la reconduire de sa propre initiative. **Seul le CEO crée ou assouplit une politique et fixe ses seuils de routage.** L'Orchestrateur applique les politiques **dans les limites fixées par le CEO** ; il ne fixe jamais les seuils.

## Règles

### Format d'une politique

Toute politique pré-approuvée comporte au minimum les éléments suivants :

- **Identifiant** : un identifiant unique et stable, permettant de la citer sans ambiguïté.
- **Classe couverte** : la classe de décision visée (courante, ou importante en cadre étroit), telle que définie dans [`07-decision-classification-policy.md`](./07-decision-classification-policy.md).
- **Conditions vérifiables** : la liste des conditions observables qui, toutes réunies, font qu'un cas entre dans le champ de la politique.
- **Plafond de portée** : la limite au-delà de laquelle la politique cesse de s'appliquer et la décision doit être remontée au CEO.
- **Échéance / revalidation** : la date ou la fréquence à laquelle le CEO doit revalider la politique pour qu'elle reste active (fréquence par défaut renvoyée à [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).
- **Version** : le numéro de version de la politique, incrémenté à chaque modification.

### Registre et versioning

Toutes les politiques sont consignées dans un **registre** unique et consultable. Chaque entrée porte son identifiant, sa version courante et son statut (active, expirée, révoquée). Toute modification produit une nouvelle version : les versions antérieures sont conservées pour l'historique et ne sont jamais écrasées silencieusement. Une politique absente du registre, ou sans version active, est réputée inexistante et ne peut fonder aucune validation.

### Cycle de vie

Le cycle de vie d'une politique suit toujours cet ordre :

1. **Création par le CEO** : le CEO rédige et approuve la politique ; elle est inscrite au registre.
2. **Application** : tant qu'elle est active et non périmée, la politique traite les cas qui remplissent ses conditions vérifiables, dans la limite de son plafond de portée.
3. **Revalidation périodique** : à l'échéance fixée, le CEO revalide la politique ; sans revalidation, elle expire et cesse de s'appliquer.
4. **Révocation** : le CEO peut révoquer une politique à tout moment ; elle cesse alors immédiatement de s'appliquer.

Aucune de ces étapes ne peut être accomplie par un agent. La création, la revalidation et la révocation sont des actes réservés au CEO.

### Décision « en vol » lorsque la politique change

Si une politique est modifiée, expire ou est révoquée alors qu'une décision est en cours de traitement sous son couvert (« en vol »), la décision ne peut **pas** s'appuyer sur une politique qui n'est plus active au moment de son application. Par défaut, une décision en vol dont la politique n'est plus valide est **suspendue et remontée au CEO** plutôt qu'appliquée sous une politique caduque. La règle est conservatrice : en cas de doute, on remonte.

### Plafond de portée cumulée

Au-delà du plafond propre à chaque politique, un **plafond de portée cumulée** empêche qu'un empilement de décisions de faible portée aboutisse, de fait, à valider une décision structurante par fractionnement. Ce garde-fou est **opérationnel** et repose sur deux paramètres :

- **une unité commune de portée** : les portées hétérogènes (dépense, temps engagé, effet sur des tiers, etc.) sont ramenées à une même unité de mesure afin d'être additionnées ;
- **une fenêtre temporelle de rattachement** : les cas survenus dans une même fenêtre glissante sont rattachés à une **même séquence de décision**, de sorte qu'une décision structurante découpée en fragments courants successifs soit reconstituée et détectée.

Lorsque, sur une même séquence, le cumul des portées ainsi mesuré dépasse le seuil de portée cumulée, l'application par politique **s'arrête** et la décision est **remontée au CEO**. Il ne doit jamais être possible de contourner l'exclusion des décisions structurantes en fractionnant une grande décision en plusieurs petites couvertes par des politiques distinctes. La valeur de l'unité, la fenêtre de rattachement et le seuil chiffré sont renvoyés à [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md).

### Re-classification sur le chemin de traitement

Le traitement par politique n'est **pas aveugle à l'aggravation** d'un cas dans le temps. Un **point de contrôle périodique de re-classification** est appliqué aux décisions validées par politique : un cas d'abord jugé courant peut, sous l'effet de circonstances nouvelles (répétition, montée de la portée, effet sur des tiers), devenir important hors cadre, structurant ou critique. Dès qu'une re-classification fait sortir un cas des classes éligibles ou franchir un plafond, le traitement par politique cesse et la décision est **remontée au CEO**. La fréquence de ce contrôle est renvoyée à [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md).

### Audit a posteriori

Les validations réalisées au titre d'une politique font l'objet d'un **audit a posteriori**. Un échantillon des décisions traitées par politique est réexaminé afin de détecter les cas de **misclassification** : décision qui aurait dû être remontée au CEO mais qui a été traitée par politique, condition mal appréciée, plafond franchi sans détection. Toute misclassification confirmée est signalée au CEO et peut motiver une revalidation ou une révocation de la politique concernée. L'audit ne rend pas au CEO l'autorité — il ne l'a jamais perdue — mais lui fournit la visibilité nécessaire pour l'exercer. Le **taux d'échantillonnage** de l'audit et la **fréquence de revalidation par défaut** sont renvoyés à [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md).

## Exemples

**Exemple 1 — politique courante appliquée.** Le CEO crée une politique couvrant le renouvellement à l'identique d'un abonnement outil récurrent en dessous d'un plafond de dépense donné. Un cas se présente : renouvellement du même abonnement, même montant, sous le plafond. Toutes les conditions vérifiables sont réunies et la portée reste sous le plafond. La décision est validée par la politique pré-approuvée du CEO, tracée et rattachée à l'identifiant de la politique. Le CEO n'est pas sollicité de nouveau, conformément à sa propre décision antérieure : sa validation avait été donnée par avance.

**Exemple 2 — décision qui sort du cadre, remontée au CEO.** Le même besoin de renouvellement se présente, mais le fournisseur propose cette fois un engagement pluriannuel dont le montant dépasse le plafond de la politique. Une condition n'est plus remplie (durée d'engagement) et le plafond de portée est franchi. La politique ne s'applique pas : la décision est **remontée au CEO** conformément à [`04-escalation-policy.md`](./04-escalation-policy.md), qui tranche lui-même.

## Cas limites

**Politique périmée.** Une politique dont l'échéance est passée sans revalidation est expirée. Un cas qui remplirait ses conditions n'est pas traité par politique : il est remonté au CEO. Une politique périmée ne « revit » pas d'elle-même ; seule une revalidation par le CEO la réactive.

**Deux politiques en conflit.** Si deux politiques actives donnent des réponses incompatibles pour un même cas, aucune ne prime automatiquement. Le conflit est traité comme une ambiguïté : la décision est remontée au CEO, qui tranche et, le cas échéant, corrige ou révoque l'une des politiques pour lever le conflit à la source.

**Portée cumulée dépassant le seuil.** Lorsque l'addition des portées de plusieurs décisions rattachées à une même séquence dépasse le seuil de portée cumulée, le traitement par politique s'interrompt même si chaque cas pris isolément resterait sous le plafond de sa politique. La décision est remontée au CEO. C'est le garde-fou contre la validation d'une décision structurante par fractionnement.

**Aggravation détectée en cours de traitement.** Un cas d'abord éligible franchit un plafond ou change de classe lors d'un point de contrôle de re-classification. Le traitement par politique cesse immédiatement et la décision est remontée au CEO, même si la validation par politique avait initialement démarré.

**Révocation d'une politique pendant une validation.** Si le CEO révoque une politique alors qu'une validation est en cours sous son couvert, la validation ne peut pas s'achever sur la base de la politique révoquée. Le traitement en vol est suspendu et la décision est remontée au CEO, conformément à la règle de la décision « en vol ».

## Questions ouvertes

- Comment moduler la fréquence de revalidation par défaut selon la classe couverte (courante ou importante en cadre étroit), et faut-il l'ajuster politique par politique ?
- Quel taux d'échantillonnage l'audit a posteriori doit-il retenir pour détecter les misclassifications de manière fiable sans surcharge ?
- Comment fixer la fenêtre temporelle de rattachement et l'unité commune de portée lorsque les décisions couvertes sont hétérogènes (dépense, temps, effet sur des tiers) ?
- Quelle articulation exacte entre le plafond de portée cumulée de cette politique et les seuils de [`09-quality-gate-policy.md`](./09-quality-gate-policy.md) et [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) ?
- Faut-il notifier systématiquement le CEO de chaque application de politique, ou seulement des remontées, des re-classifications et des résultats d'audit ?
