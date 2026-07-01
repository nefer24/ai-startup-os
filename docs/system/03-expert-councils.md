# Expert Councils

> Aucune décision importante ne naît d'une intelligence isolée. Les Conseils d'Experts rassemblent plusieurs perspectives spécialisées pour délibérer, se critiquer mutuellement et produire une recommandation argumentée — jamais une décision. La décision demeure toujours entre les mains de l'humain.

## Pourquoi les Conseils d'Experts existent

Un Conseil d'Experts est le mécanisme par lequel AI-SOS refuse la décision solitaire. Un agent unique, aussi compétent soit-il dans son domaine, raisonne à partir d'un cadre limité : il possède des angles morts, des biais implicites et une tendance à privilégier les solutions familières. Confier une orientation importante à une seule intelligence isolée revient à accepter ses lacunes sans contrepoids.

Le Conseil corrige cette fragilité par la confrontation organisée des points de vue. Là où un agent isolé voit une réponse évidente, plusieurs Agents spécialisés voient des tensions, des compromis et des conséquences non anticipées. La divergence n'est pas un défaut à supprimer : elle est la matière première d'une réflexion solide.

Ce refus de la décision solitaire s'inscrit dans les principes fondateurs d'AI-SOS :

- **Intelligence collective** : la qualité d'une recommandation croît avec la diversité des angles qui l'ont éprouvée.
- **Spécialisation** : chaque membre apporte une expertise distincte plutôt qu'une opinion générale.
- **Validation humaine** : le Conseil prépare le jugement humain, il ne le remplace pas.

Il existe autant de Conseils que de domaines de responsabilité — architecture, sécurité, données, produit, expérience utilisateur, qualité, et les grands domaines techniques et d'intelligence artificielle. Chaque domaine dispose ainsi d'une enceinte propre où ses questions importantes sont délibérées avant d'atteindre l'humain.

## Relation entre Conseils et Départements

Un Conseil d'Experts et un Département ne sont pas la même chose, et cette distinction est structurante. Un **Département** est une instance permanente qui regroupe des Agents spécialisés partageant une même famille d'expertise ; il constitue le rattachement principal et durable d'un agent. Un **Conseil d'Experts** est une instance **transverse** qui réunit, le temps d'une délibération, des Agents issus de plusieurs Départements autour d'une question importante. Un Conseil n'est **pas** un Département : il ne possède ni effectif permanent au sens d'un rattachement, ni périmètre organisationnel propre. Il se forme pour délibérer, produit une recommandation, puis se dissout.

Qui peuple un Conseil ? Des **Agents spécialisés détachés de leurs Départements** le temps de la délibération. Ces agents demeurent rattachés à leur Département d'origine ; leur participation à un Conseil est une **contribution transverse** qui ne modifie pas leur rattachement principal. Le Conseil rassemble ainsi la diversité d'expertises nécessaire à la question posée, en puisant dans un ou plusieurs Départements selon les enjeux qu'elle soulève.

À chaque grand domaine de responsabilité correspond conceptuellement un Conseil. Cette correspondance domaine ↔ Conseil est directe mais non rigide : une même question peut mobiliser plusieurs Conseils, et un Conseil peut convier des expertises issues de domaines voisins. À titre indicatif :

| Domaine | Conseil correspondant | Départements sollicités (à titre indicatif) |
| --- | --- | --- |
| Architecture et direction technique | Conseil d'architecture | Engineering, Infrastructure |
| Sécurité et risque | Conseil de sécurité | Security |
| Données et modélisation | Conseil des données | Engineering, Infrastructure |
| Produit et priorisation | Conseil produit | Product, Business |
| Expérience utilisateur | Conseil d'expérience utilisateur | UX, Product |
| Qualité et exigences | Conseil de qualité | Engineering, Product |
| Intelligence artificielle | Conseil d'intelligence artificielle | Research, Engineering |

Le détail des Départements, de leur structure et du rattachement des agents figure dans [`04-departments.md`](./04-departments.md).

## Conseils par domaine

La liste des Conseils est **indicative et extensible** : elle reflète les grands domaines de responsabilité de l'organisation et peut s'enrichir de nouveaux Conseils à mesure que de nouveaux domaines émergent, dans le cadre de gouvernance décrit dans [`09-agent-creation.md`](./09-agent-creation.md). Cette liste demeure cohérente avec les Conseils recensés dans le dossier `councils/` du dépôt :

- **Conseil d'architecture** — architecture de haut niveau et direction technique.
- **Conseil de sécurité** — sécurité et maîtrise des risques.
- **Conseil des données** — modélisation et organisation des données.
- **Conseil produit** — direction et priorisation du produit.
- **Conseil d'expérience utilisateur** — expérience et facilité d'usage.
- **Conseil de qualité** — exigences de qualité et validation.
- **Conseil d'intelligence artificielle** — intelligence artificielle et apprentissage.
- **Conseil de conception applicative** — conception des composants applicatifs, côté fondations comme côté interface.

Aucune de ces enceintes n'est un Département : ce sont des lieux de délibération transverse, convoqués au besoin, qui puisent leurs membres dans les Départements concernés.

## Composition d'un Conseil

Un Conseil réunit plusieurs Agents spécialisés dont les rôles se complètent. Sa composition n'est pas figée : elle s'adapte à la nature de la question traitée, tout en respectant une structure stable.

### Membres permanents

Les membres permanents représentent le cœur d'expertise du domaine. Ils garantissent la continuité, la mémoire des délibérations passées et la cohérence des recommandations dans le temps. Ils sont présents à chaque session du Conseil et portent la responsabilité principale de la qualité de la recommandation produite.

### Experts invités

Lorsqu'une question déborde les frontières d'un seul domaine, le Conseil convie des experts invités issus d'autres domaines ou Départements. Un Conseil d'architecture peut ainsi inviter une expertise de sécurité ou de données ; un Conseil produit peut solliciter un regard sur l'expérience utilisateur. Les experts invités apportent un éclairage ciblé sur les aspects de la décision qui touchent leur spécialité, sans se substituer aux membres permanents.

### Facilitation par l'Orchestrateur

L'[`Orchestrateur`](./02-orchestrator.md) assure la facilitation du Conseil. Il ne tranche pas et n'impose pas de position : son rôle est de veiller au bon déroulement de la délibération. Il convoque les membres pertinents, cadre la question, s'assure que chaque perspective peut s'exprimer, empêche qu'une voix domine indûment et garantit que le mouvement délibératif progresse vers une recommandation. Sa neutralité est la condition de l'équité du débat.

## Facilitation et responsabilité

La délibération d'un Conseil distingue deux fonctions qui ne doivent jamais se confondre : celle du **facilitateur** et celle des **membres**.

- **Le facilitateur** est l'[`Orchestrateur`](./02-orchestrator.md). Il est **neutre** et **garant du processus** : il cadre la question, ouvre et clôt les phases de délibération, veille au respect du quorum, du critère de convergence et du time-box, et s'assure que chaque perspective peut s'exprimer sans qu'aucune ne domine indûment. Le facilitateur ne porte **aucune** position sur le fond ; il ne juge pas la valeur des options et ne pèse pas dans la recommandation. Sa responsabilité est celle de la **qualité du processus**, non celle du contenu.
- **Les membres** sont les Agents spécialisés qui délibèrent. Ils sont **responsables du contenu** : la pertinence des options, la solidité des arguments, l'identification des risques et, en définitive, la **qualité de la recommandation** produite. C'est à eux, et non au facilitateur, qu'incombe le fond de la délibération.

Cette séparation protège l'équité du débat : le garant du processus n'a pas d'intérêt dans son issue, et ceux qui ont un avis sur le fond n'ont pas la main sur les règles du jeu.

Lorsque plusieurs Conseils siègent en parallèle, la fonction de facilitateur peut être **déléguée**. L'Orchestrateur confie alors la facilitation d'un Conseil à un facilitateur délégué, qui exerce le même rôle neutre de garant du processus et rend compte à l'Orchestrateur. La délégation porte sur la fonction de facilitation, jamais sur la responsabilité du contenu, qui demeure celle des membres.

## Comment ils débattent

La délibération d'un Conseil suit un mouvement structuré en trois temps, qui transforme des positions initiales en une réflexion collective éprouvée.

### Débat

Chaque membre expose sa lecture de la question, ses hypothèses et l'orientation qu'il privilégie. Cette première phase vise l'exhaustivité : faire émerger le plus grand nombre d'options et de considérations pertinentes, sans jugement prématuré. La richesse des propositions à ce stade détermine la qualité de tout ce qui suit.

### Critique

Les positions exposées sont soumises à un examen mutuel. Les membres cherchent activement les faiblesses, les hypothèses fragiles, les risques négligés et les conséquences indésirables de chaque option. La critique n'est pas dirigée contre les personnes mais contre les idées : elle est l'expression du soin, non de l'hostilité. C'est par cette épreuve que les angles morts individuels sont révélés.

### Amélioration

À la lumière des critiques, les options sont retravaillées, combinées ou écartées. Les membres ajustent leurs positions, intègrent les objections valides et construisent des propositions plus robustes que celles initialement avancées. Ce mouvement peut se répéter : débattre, critiquer et améliorer jusqu'à ce que les options survivantes satisfassent le critère de convergence défini plus bas, dans les limites d'itérations et de temps du Conseil.

Ce cycle délibératif est décrit dans son ensemble dans le [`flux de décision`](./08-decision-flow.md).

## Taille et protocole de conclusion

Pour rester délibérant, un Conseil obéit à des bornes explicites de taille et de conclusion. Ces bornes évitent deux dérives symétriques : l'enceinte pléthorique où plus personne ne s'écoute, et la délibération sans fin qui ne conclut jamais.

### Taille bornée et sous-comités

Un Conseil a une **taille bornée**. Au-delà d'un certain nombre de membres, la délibération perd en qualité : les tours de parole s'allongent, les échanges se diluent et la confrontation des idées s'appauvrit. Lorsqu'une question exige davantage d'expertises que le Conseil ne peut en accueillir utilement, il forme des **sous-comités** : des groupes restreints qui approfondissent un aspect délimité de la question, puis restituent leurs conclusions au Conseil plénier. Le sous-comité prépare la délibération ; il ne se substitue pas au Conseil ni à sa recommandation.

### Quorum

Une délibération n'est valide que si un **quorum** est réuni : un nombre et une diversité minimaux de membres présents, garantissant que les perspectives essentielles au domaine sont effectivement représentées. En deçà du quorum, le Conseil ne conclut pas ; le facilitateur convoque les membres manquants ou reporte la délibération. Le quorum protège la recommandation contre le risque d'une conclusion tirée d'un échantillon d'expertises trop étroit.

### Critère de convergence objectif

La conclusion du cycle débat → critique → amélioration ne repose pas sur une appréciation floue telle qu'un « examen sérieux », qui n'est pas décidable. Elle repose sur un **critère de convergence objectif** : la délibération est réputée aboutie lorsque les options survivantes ont résisté à un tour de critique sans qu'aucune objection de fond nouvelle n'émerge, et que les objections soulevées ont été soit intégrées, soit explicitement consignées comme dissensions. Ce critère, observable et vérifiable, permet de déterminer sans ambiguïté si le Conseil peut conclure.

### Itérations bornées et time-box

Le cycle débat → critique → amélioration est **borné** de deux manières : par un **nombre maximal d'itérations** et par une **limite de temps conceptuelle** (time-box). Ces bornes garantissent qu'un Conseil conclut toujours, y compris en l'absence de consensus.

En cas d'**absence de convergence** lorsque les bornes sont atteintes — critère de convergence non satisfait au terme du time-box ou du nombre maximal d'itérations —, le Conseil ne force pas un accord artificiel. Il applique le protocole de conclusion suivant :

- **Présentation à parité** : les options concurrentes sont présentées **à parité**, chacune accompagnée de ses raisons et de ses risques, sans qu'aucune ne soit indûment privilégiée.
- **Escalade** : la question est **escaladée** à la validation humaine, à qui il revient de trancher entre les options présentées.

Ce protocole prolonge la manière dont le Conseil gère les désaccords, décrite ci-dessous, et garantit qu'une délibération se termine toujours par une transparence accrue envers l'humain, jamais par un blocage.

## Comment ils produisent une recommandation

Au terme de la délibération, le Conseil formule une **recommandation**. Il est essentiel de rappeler ce qu'une recommandation n'est pas : ce n'est pas une décision, ni une instruction d'exécution. C'est une proposition argumentée, destinée à la validation humaine.

Une recommandation complète expose au minimum :

- **Les options considérées** : l'éventail des orientations réellement examinées, y compris celles qui ont été écartées, afin que l'humain voie le champ des possibles et non une seule voie.
- **Les raisons** : les arguments qui soutiennent l'option privilégiée, ainsi que les motifs pour lesquels les autres ont été jugées moins adaptées.
- **Les risques** : les incertitudes, les compromis acceptés, les conséquences possibles et les conditions dans lesquelles la recommandation pourrait se révéler inadaptée.

Cette forme sert un objectif précis : donner à l'humain de quoi décider en connaissance de cause. Une recommandation qui masquerait ses alternatives ou dissimulerait ses risques trahirait le principe de validation humaine, en réduisant le choix à une simple ratification.

## Comment ils gèrent les désaccords

Le consensus n'est pas une exigence. Un Conseil sain produit parfois des désaccords, et ceux-ci sont traités comme une information précieuse plutôt que comme un échec.

- **Dissensions** : lorsqu'un membre maintient une objection de fond, celle-ci est consignée et transmise avec la recommandation. Une objection persistante signale à l'humain un point de vigilance.
- **Positions minoritaires** : une option soutenue par une minorité n'est pas écartée au seul motif de sa faible adhésion. Sa présentation accompagne la recommandation, avec ses arguments propres, afin que l'humain puisse en juger la valeur.
- **Absence de consensus** : si le Conseil ne parvient pas à converger vers une orientation privilégiée, il ne force pas un accord artificiel. Il présente les options concurrentes à parité, avec leurs raisons et leurs risques respectifs.
- **Escalade vers l'humain** : le désaccord irréductible ou l'enjeu jugé particulièrement sensible sont explicitement remontés à la validation humaine. L'escalade n'est pas un aveu de faiblesse : c'est le fonctionnement normal d'un système où l'humain décide.

En toute circonstance, un désaccord non résolu se traduit par une transparence accrue envers l'humain, jamais par une décision imposée par le Conseil.

## Relation avec l'Orchestrateur et le CEO

Le Conseil d'Experts s'inscrit dans une chaîne de responsabilité claire, dans laquelle chaque niveau joue un rôle distinct et non interchangeable.

L'[`Orchestrateur`](./02-orchestrator.md) se tient en amont et autour du Conseil. Il identifie qu'une question relève d'une délibération collective, convoque le Conseil approprié, facilite sa délibération et recueille la recommandation produite. Il coordonne les Conseils entre eux et avec les Départements, mais il ne se substitue à aucun d'eux et ne transforme jamais une recommandation en décision.

Le **CEO** — l'humain — se tient à l'aboutissement de la chaîne. C'est à lui que la recommandation est destinée, et c'est lui seul qui décide. Il peut approuver la recommandation, en retenir une variante, la renvoyer pour approfondissement ou la refuser. Le Conseil éclaire son jugement ; il ne le contraint pas.

Cette relation exprime la règle de gouvernance d'AI-SOS : **les agents recommandent, l'humain décide**. Le Conseil est puissant dans sa capacité à délibérer et à raisonner collectivement, et volontairement dépourvu de tout pouvoir de décision finale.

## Traçabilité des délibérations

Chaque délibération de Conseil laisse une trace documentée. La documentation n'est pas un sous-produit administratif : elle est un principe fondateur d'AI-SOS et une condition de l'amélioration continue.

La traçabilité couvre :

- **La question posée** et le contexte qui a motivé la convocation du Conseil.
- **Les options considérées** et le déroulement de la délibération — débat, critiques, améliorations successives.
- **La recommandation** finale, ses raisons et ses risques, ainsi que les dissensions et positions minoritaires éventuelles.
- **La suite donnée** : la décision humaine, sa justification, et son rattachement à la recommandation d'origine.

Ces éléments sont archivés durablement. L'archivage sert plusieurs finalités : rendre chaque décision explicable après coup, permettre aux Conseils futurs de s'appuyer sur les délibérations passées, et nourrir l'amélioration continue en confrontant les recommandations à leurs résultats réels.

Le détail du parcours complet, de l'analyse initiale à l'amélioration, est décrit dans le [`flux de décision`](./08-decision-flow.md).
