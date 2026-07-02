# Pre-Approved Policies

> Cette politique définit comment fonctionnent les **politiques pré-approuvées par le CEO** au sein d'AI-SOS. Une politique pré-approuvée est un cadre écrit, décidé par le CEO, qui autorise à l'avance le traitement automatique de certaines décisions de faible portée sans nouvelle intervention humaine. Le CEO reste la seule autorité humaine et le seul décideur : la validation graduée délègue uniquement vers ces politiques qu'il a lui-même approuvées, jamais vers un autre humain (il n'en existe pas) ni vers un agent. Aucun agent ne reçoit d'autorité de décision. Voir [`../behavior/11-decision-classification-and-policies.md`](../behavior/11-decision-classification-and-policies.md).

## Objectif

L'objectif est de préciser ce qu'est une politique pré-approuvée, ce qu'elle peut couvrir, et comment elle vit dans le temps.

Une politique pré-approuvée permet d'éviter de solliciter le CEO pour chaque décision courante et répétitive, tout en garantissant que ce dernier conserve le contrôle : c'est lui qui décide, en amont et par écrit, des cas où une réponse peut être appliquée sans le consulter à nouveau. La politique ne remplace pas le CEO ; elle **matérialise une décision déjà prise par lui** et rendue réutilisable.

Ce document couvre :

- les **critères** qui déterminent ce qu'une politique a le droit de couvrir ;
- les **règles** de format, de registre, de cycle de vie et de garde-fous cumulés ;
- des **exemples** d'application et de sortie de cadre ;
- les **cas limites** de conflit, de péremption et de révocation.

Il ne couvre pas la manière de classer une décision : cela relève de [`07-decision-classification-policy.md`](./07-decision-classification-policy.md).

## Critères

Une politique ne peut être créée que si les critères observables suivants sont réunis.

**Classe de portée éligible.** Une politique ne peut couvrir que des décisions de **faible portée** : des décisions courantes, répétitives, dont l'effet est réversible et circonscrit, éventuellement importantes mais uniquement dans un cadre étroit et clairement délimité. La classe visée doit être nommée explicitement selon la classification de [`07-decision-classification-policy.md`](./07-decision-classification-policy.md).

**Exclusion des décisions structurantes ou critiques.** Une politique ne peut **jamais** couvrir une décision structurante ou critique : engagement durable, effet difficilement réversible, impact sur la stratégie, sur la sécurité, sur les finances au-delà d'un seuil, ou sur des tiers de manière significative. Ces décisions restent, sans exception, remontées au CEO.

**Conditions vérifiables.** Le champ d'application doit reposer sur des conditions observables et vérifiables sans jugement discrétionnaire : on doit pouvoir répondre par oui ou par non à la question « ce cas entre-t-il dans la politique ? » à partir de faits constatables.

**Plafond de portée explicite.** Toute politique fixe un plafond de portée au-delà duquel elle ne s'applique plus (voir les seuils de référence dans [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)). En l'absence de plafond chiffrable, la politique n'est pas valide.

**Origine humaine unique.** Une politique n'existe que si le CEO l'a créée et approuvée. Une politique ne s'auto-crée jamais : aucun agent ni aucun mécanisme automatique ne peut en générer une, l'élargir ou la reconduire de sa propre initiative.

## Règles

### Format d'une politique

Toute politique pré-approuvée comporte au minimum les éléments suivants :

- **Identifiant** : un identifiant unique et stable, permettant de la citer sans ambiguïté.
- **Classe couverte** : la classe de décision visée, telle que définie dans [`07-decision-classification-policy.md`](./07-decision-classification-policy.md).
- **Conditions vérifiables** : la liste des conditions observables qui, toutes réunies, font qu'un cas entre dans le champ de la politique.
- **Plafond de portée** : la limite au-delà de laquelle la politique cesse de s'appliquer et la décision doit être remontée au CEO.
- **Échéance / revalidation** : la date ou la fréquence à laquelle le CEO doit revalider la politique pour qu'elle reste active.
- **Version** : le numéro de version de la politique, incrémenté à chaque modification.

### Registre et versioning

Toutes les politiques sont consignées dans un **registre** unique et consultable. Chaque entrée porte son identifiant, sa version courante et son statut (active, expirée, révoquée). Toute modification produit une nouvelle version : les versions antérieures sont conservées pour l'historique et ne sont jamais écrasées silencieusement. Une politique absente du registre, ou sans version active, est réputée inexistante et ne peut fonder aucune validation.

### Cycle de vie

Le cycle de vie d'une politique suit toujours cet ordre :

1. **Création par le CEO** : le CEO rédige et approuve la politique ; elle est inscrite au registre.
2. **Application** : tant qu'elle est active et non périmée, la politique traite automatiquement les cas qui remplissent ses conditions vérifiables, dans la limite de son plafond de portée.
3. **Revalidation périodique** : à l'échéance fixée, le CEO revalide la politique ; sans revalidation, elle expire et cesse de s'appliquer.
4. **Révocation** : le CEO peut révoquer une politique à tout moment ; elle cesse alors immédiatement de s'appliquer.

Aucune de ces étapes ne peut être accomplie par un agent. La création, la revalidation et la révocation sont des actes réservés au CEO.

### Décision « en vol » lorsque la politique change

Si une politique est modifiée, expire ou est révoquée alors qu'une décision est en cours de traitement sous son couvert (« en vol »), la décision ne peut **pas** s'appuyer sur une politique qui n'est plus active au moment de son application. Par défaut, une décision en vol dont la politique n'est plus valide est **suspendue et remontée au CEO** plutôt qu'appliquée sous une politique caduque. La règle est conservatrice : en cas de doute, on remonte.

### Plafond de portée cumulée

Au-delà du plafond propre à chaque politique, un **plafond de portée cumulée** empêche qu'un empilement de politiques de faible portée aboutisse, de fait, à automatiser une décision structurante. Lorsque plusieurs politiques s'appliqueraient à un même cas ou à une même séquence de cas, on additionne leur portée : si le cumul dépasse le seuil de portée cumulée (voir [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)), l'automatisation s'arrête et la décision est remontée au CEO. Il ne doit jamais être possible de contourner l'exclusion des décisions structurantes en fractionnant une grande décision en plusieurs petites couvertes par des politiques distinctes.

### Audit a posteriori

Les validations réalisées au titre d'une politique font l'objet d'un **audit a posteriori**. Un échantillon des décisions traitées par politique est réexaminé afin de détecter les cas de **misclassification** : décision qui aurait dû être remontée au CEO mais qui a été traitée automatiquement, condition mal appréciée, plafond franchi sans détection. Toute misclassification confirmée est signalée au CEO et peut motiver une revalidation ou une révocation de la politique concernée. L'audit ne rend pas au CEO l'autorité — il ne l'a jamais perdue — mais lui fournit la visibilité nécessaire pour l'exercer.

## Exemples

**Exemple 1 — politique courante appliquée.** Le CEO crée une politique couvrant le renouvellement à l'identique d'un abonnement outil récurrent en dessous d'un plafond de dépense donné. Un cas se présente : renouvellement du même abonnement, même montant, sous le plafond. Toutes les conditions vérifiables sont réunies et la portée reste sous le plafond. La décision est appliquée automatiquement, tracée et rattachée à l'identifiant de la politique. Le CEO n'est pas sollicité, conformément à sa propre décision antérieure.

**Exemple 2 — décision qui sort du cadre, remontée au CEO.** Le même besoin de renouvellement se présente, mais le fournisseur propose cette fois un engagement pluriannuel dont le montant dépasse le plafond de la politique. Une condition n'est plus remplie (durée d'engagement) et le plafond de portée est franchi. La politique ne s'applique pas : la décision est **remontée au CEO** conformément à [`04-escalation-policy.md`](./04-escalation-policy.md), qui tranche lui-même.

## Cas limites

**Politique périmée.** Une politique dont l'échéance est passée sans revalidation est expirée. Un cas qui remplirait ses conditions n'est pas traité automatiquement : il est remonté au CEO. Une politique périmée ne « revit » pas d'elle-même ; seule une revalidation par le CEO la réactive.

**Deux politiques en conflit.** Si deux politiques actives donnent des réponses incompatibles pour un même cas, aucune ne prime automatiquement. Le conflit est traité comme une ambiguïté : la décision est remontée au CEO, qui tranche et, le cas échéant, corrige ou révoque l'une des politiques pour lever le conflit à la source.

**Portée cumulée dépassant le seuil.** Lorsque l'addition des portées de plusieurs politiques applicables dépasse le seuil de portée cumulée, l'automatisation s'interrompt même si chaque politique prise isolément resterait sous son propre plafond. La décision est remontée au CEO. C'est le garde-fou contre l'automatisation d'une décision structurante par fractionnement.

**Révocation d'une politique pendant une validation.** Si le CEO révoque une politique alors qu'une validation est en cours sous son couvert, la validation ne peut pas s'achever sur la base de la politique révoquée. Le traitement en vol est suspendu et la décision est remontée au CEO, conformément à la règle de la décision « en vol ».

## Questions ouvertes

- Comment définir précisément la fréquence de revalidation par défaut selon la classe couverte, et faut-il la moduler par politique ?
- Quel taux d'échantillonnage l'audit a posteriori doit-il retenir pour détecter les misclassifications de manière fiable sans surcharge ?
- Comment mesurer et agréger la « portée cumulée » lorsque les décisions couvertes sont hétérogènes (dépense, temps, effet sur des tiers) ?
- Quelle articulation exacte entre le plafond de portée cumulée de cette politique et les seuils de [`09-quality-gate-policy.md`](./09-quality-gate-policy.md) et [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) ?
- Faut-il notifier systématiquement le CEO de chaque application de politique, ou seulement des remontées et des résultats d'audit ?
