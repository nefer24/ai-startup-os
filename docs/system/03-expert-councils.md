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

## Composition d'un Conseil

Un Conseil réunit plusieurs Agents spécialisés dont les rôles se complètent. Sa composition n'est pas figée : elle s'adapte à la nature de la question traitée, tout en respectant une structure stable.

### Membres permanents

Les membres permanents représentent le cœur d'expertise du domaine. Ils garantissent la continuité, la mémoire des délibérations passées et la cohérence des recommandations dans le temps. Ils sont présents à chaque session du Conseil et portent la responsabilité principale de la qualité de la recommandation produite.

### Experts invités

Lorsqu'une question déborde les frontières d'un seul domaine, le Conseil convie des experts invités issus d'autres domaines ou Départements. Un Conseil d'architecture peut ainsi inviter une expertise de sécurité ou de données ; un Conseil produit peut solliciter un regard sur l'expérience utilisateur. Les experts invités apportent un éclairage ciblé sur les aspects de la décision qui touchent leur spécialité, sans se substituer aux membres permanents.

### Facilitation par l'Orchestrateur

L'[`Orchestrateur`](./02-orchestrator.md) assure la facilitation du Conseil. Il ne tranche pas et n'impose pas de position : son rôle est de veiller au bon déroulement de la délibération. Il convoque les membres pertinents, cadre la question, s'assure que chaque perspective peut s'exprimer, empêche qu'une voix domine indûment et garantit que le mouvement délibératif progresse vers une recommandation. Sa neutralité est la condition de l'équité du débat.

## Comment ils débattent

La délibération d'un Conseil suit un mouvement structuré en trois temps, qui transforme des positions initiales en une réflexion collective éprouvée.

### Débat

Chaque membre expose sa lecture de la question, ses hypothèses et l'orientation qu'il privilégie. Cette première phase vise l'exhaustivité : faire émerger le plus grand nombre d'options et de considérations pertinentes, sans jugement prématuré. La richesse des propositions à ce stade détermine la qualité de tout ce qui suit.

### Critique

Les positions exposées sont soumises à un examen mutuel. Les membres cherchent activement les faiblesses, les hypothèses fragiles, les risques négligés et les conséquences indésirables de chaque option. La critique n'est pas dirigée contre les personnes mais contre les idées : elle est l'expression du soin, non de l'hostilité. C'est par cette épreuve que les angles morts individuels sont révélés.

### Amélioration

À la lumière des critiques, les options sont retravaillées, combinées ou écartées. Les membres ajustent leurs positions, intègrent les objections valides et construisent des propositions plus robustes que celles initialement avancées. Ce mouvement peut se répéter : débattre, critiquer et améliorer jusqu'à ce que les options survivantes aient résisté à un examen sérieux.

Ce cycle délibératif est décrit dans son ensemble dans le [`flux de décision`](./08-decision-flow.md).

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
