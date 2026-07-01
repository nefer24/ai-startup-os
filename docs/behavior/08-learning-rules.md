# Learning Rules

> Ce document décrit le comportement observable de l'apprentissage dans AI-SOS : comment l'organisation tire des enseignements de ses cycles, mesure la qualité de ses **décisions**, améliore ses agents et se prémunit contre la dérive. Il s'agit d'un apprentissage **comportemental et organisationnel**, décrit en termes de séquences, de conditions et de règles — jamais d'entraînement de modèle, de jeu de données ni de mécanique technique. Ce document prolonge la mémoire organisationnelle (voir [`../system/06-memory.md`](../system/06-memory.md)) et les principes fondateurs (voir [`../system/10-system-principles.md`](../system/10-system-principles.md)). Il s'articule avec les règles de mise à jour de la mémoire (voir [`./06-memory-update-rules.md`](./06-memory-update-rules.md)) et les règles de création d'agents (voir [`./07-agent-creation-rules.md`](./07-agent-creation-rules.md)). Constante fondatrice : **le CEO est la seule autorité de validation** ; aucun agent ne se ré-autorise seul hors de son domaine, et les évolutions importantes sont validées par le CEO.

## Vue d'ensemble

L'apprentissage est l'**étape 7** du processus de décision en sept étapes constitutionnelles (Article XI) : l'**amélioration continue**. C'est elle qui referme la boucle et réalimente l'étape 1 (Analyse) du cycle suivant. Le référentiel de ce flux est le document [`../system/08-decision-flow.md`](../system/08-decision-flow.md), dont le présent document est la déclinaison comportementale. Une fois qu'une décision a été prise par l'autorité humaine puis exécutée, AI-SOS ne referme pas le cycle sans en extraire un enseignement. Ce qui a été appris est déposé dans la mémoire organisationnelle afin que le cycle suivant démarre plus averti que le précédent.

Cet apprentissage obéit à quatre invariants comportementaux :

- **Observation avant conclusion** : on n'apprend qu'à partir de résultats constatés, jamais d'une intuition non vérifiée.
- **Traçabilité** : tout enseignement inscrit en mémoire porte son origine (quel cycle, quel écart observé, quelle décision humaine).
- **Prudence de généralisation** : un enseignement tiré d'un cas ne devient une règle générale que lorsqu'il est confirmé par la répétition.
- **Autorité préservée** : l'apprentissage peut proposer des évolutions, mais leur adoption importante relève du CEO, seule autorité de validation ; aucun agent n'élargit son propre domaine au motif qu'il a « appris ».

## Comment AI-SOS apprend

L'apprentissage suit une boucle observable en quatre temps, déclenchée à la clôture d'un cycle.

### 1. Observer les résultats

Une fois la décision exécutée, l'organisation observe ce qui s'est réellement produit : le problème a-t-il été résolu, l'effet attendu s'est-il matérialisé, des conséquences non prévues sont-elles apparues ? Cette observation porte sur des faits constatables, datés et attribuables au cycle concerné. Elle ne s'arrête pas à la clôture immédiate de l'exécution : certaines conséquences n'apparaissent qu'à **long horizon** (voir plus bas, « Conséquences à long horizon »).

### 2. Comparer à la recommandation et à la décision

Le résultat observé est confronté à ce qui avait été recommandé et prévu. On mesure l'**écart** entre l'attendu et le constaté : la recommandation était-elle juste, partiellement juste, ou erronée ? Mais la comparaison ne s'arrête pas à la recommandation : on évalue aussi la qualité de la **décision** elle-même, c'est-à-dire la pertinence du raisonnement au moment où il a été tenu, indépendamment du hasard qui a suivi (voir « Mesure de la qualité »). Cette comparaison est le cœur de l'apprentissage — sans point de référence, il n'y a pas d'enseignement.

### 3. Tirer un enseignement

De l'écart naît une leçon exprimée en langage clair : ce qui a bien fonctionné et mérite d'être reproduit, ce qui a échoué et doit être évité, la condition qui distingue les deux. L'enseignement est formulé de manière à être réutilisable par un futur cycle, sans se réduire à une anecdote isolée.

### 4. L'inscrire en mémoire organisationnelle

L'enseignement validé est capitalisé dans la mémoire organisationnelle, selon les règles de mise à jour de la mémoire (voir [`./06-memory-update-rules.md`](./06-memory-update-rules.md)). Il devient alors une connaissance disponible pour l'ensemble de l'organisation, et non la propriété d'un seul agent.

> **Condition de bouclage** : un cycle n'est considéré comme pleinement clos que lorsque son enseignement a été formulé et inscrit — ou explicitement jugé sans enseignement notable.

## Mesure de la qualité

Pour apprendre, l'organisation a besoin d'indicateurs conceptuels lui disant si ses décisions s'améliorent. Ces indicateurs sont observés dans la durée, pas seulement cycle par cycle. Pour rester exploitables, ils doivent être **rendus opérationnels** : sans échelle, sans fenêtre de tendance et sans seuils, la détection de dérive resterait inerte. Les valeurs numériques concrètes ne figurent pas ici : elles sont centralisées et versionnées dans [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md), qui reste la source unique des chiffres.

### Écart recommandation / résultat

Indicateur central : la distance entre ce qui avait été recommandé et ce qui s'est réellement produit.

- **Échelle de mesure.** L'écart est qualifié sur une échelle ordonnée et stable — par exemple : *nul* (résultat conforme), *faible*, *modéré*, *fort*, *inversé* (le résultat contredit la recommandation). Chaque cycle place son écart sur cette échelle selon des critères constatables, de sorte que deux cycles soient comparables.
- **Fenêtre temporelle de tendance.** Une valeur isolée ne signifie rien ; l'écart est lu sur une **fenêtre glissante** d'un nombre défini de cycles récents (fenêtre dont la longueur est fixée dans [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md)). C'est la position de la fenêtre, non le point du jour, qui fait foi.
- **Seuils.** Deux régimes qualitatifs orientent la réaction. Un écart **« faible et stable »** sur la fenêtre signale une organisation calibrée : rien à déclencher. Un écart qui **« se creuse »** — moyenne qui monte d'un cran d'échelle sur la fenêtre, ou franchissement d'un seuil d'alerte — déclenche une revue de calibrage. Les bornes qui séparent ces régimes sont définies dans [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md).

### Qualité de la décision, au-delà de la recommandation

Une bonne décision peut produire un mauvais résultat, et une mauvaise décision un bon résultat : le hasard n'est pas la compétence. L'apprentissage distingue donc explicitement la **qualité de la décision** (le raisonnement était-il fondé au moment où il a été tenu, compte tenu de ce qui était alors connaissable ?) du **résultat** (ce qui s'est produit ensuite). On n'inscrit pas comme « bonne pratique » une décision mal fondée qui a réussi par chance, ni comme « erreur » une décision bien fondée qu'un aléa a fait échouer.

- **Contrefactuels.** L'évaluation couvre aussi les recommandations **rejetées** par le décideur. Lorsqu'une alternative écartée aurait, à l'observation, produit un meilleur résultat, cet écart contrefactuel est mesuré et inscrit : il enseigne autant que les décisions retenues, et évite que l'organisation ne juge sa qualité uniquement sur les chemins qu'elle a effectivement empruntés.
- **Conséquences à long horizon.** Certaines décisions ne révèlent leur qualité qu'après la clôture d'exécution. L'observation reste donc ouverte au-delà du cycle : un enseignement peut être **révisé** lorsqu'une conséquence tardive contredit l'appréciation initiale (voir « Enseignement contredit plus tard »).
- **Scoring des décisions validées par politique.** Toutes les décisions ne passent pas par le CEO : certaines sont pré-approuvées par politique (voir [`11-decision-classification-and-policies.md`](./11-decision-classification-and-policies.md)). Ces décisions font l'objet du **même scoring de qualité** que les autres. Leur suivi agrégé alimente l'audit a posteriori des politiques : une politique dont les décisions se dégradent est un signal de recalibrage ou de remontée au CEO.

### Adoption

Dans quelle mesure les recommandations produites sont-elles effectivement retenues par le décideur humain, puis suivies dans l'exécution ? Un taux d'adoption durablement faible peut signaler que les recommandations manquent leur cible, indépendamment de leur justesse — ou, au contraire, alimenter la mesure contrefactuelle ci-dessus.

### Coût de délibération

L'effort mobilisé pour aboutir à une recommandation : nombre d'itérations, d'escalades, de boucles de coordination. Un coût qui augmente sans gain de qualité est un signal de friction à corriger.

### Comportement de suivi

Les indicateurs sont suivis dans le temps plutôt qu'interprétés isolément. Une valeur ponctuelle ne déclenche rien ; une **tendance** lue sur la fenêtre (dégradation persistante, oscillation anormale) déclenche une revue. Le suivi vise la reproductibilité : dans des conditions comparables, l'organisation doit produire des décisions de qualité comparable.

## Comment les agents sont améliorés

L'apprentissage ne reste pas à l'état de mémoire passive : il alimente l'amélioration des agents spécialisés.

### Des retours consolidés vers une nouvelle version

Les enseignements concernant un même agent sont **consolidés** : on ne modifie pas un agent sur la foi d'un incident unique, mais lorsqu'un faisceau de retours convergents désigne un ajustement utile de son contrat de rôle. Cette consolidation produit une proposition d'évolution.

### Versioning du contrat de rôle

Toute évolution retenue donne lieu à une **nouvelle version du contrat de rôle** de l'agent. La version précédente est conservée : on sait ce qui a changé, quand et pourquoi. Ce versioning garantit la reproductibilité et permet, en cas de régression, de revenir à un état antérieur connu.

### Règles de mise à jour d'un agent

La mise à jour d'un agent suit les règles de création et de modification décrites dans le document frère (voir [`./07-agent-creation-rules.md`](./07-agent-creation-rules.md)). En particulier : le périmètre d'un agent ne s'étend pas de lui-même ; une évolution qui élargirait son domaine est une décision, pas un simple ajustement.

### Tri des évolutions : mineur vs important

Toute évolution de contrat de rôle est d'abord **qualifiée** — mineure ou importante — car les deux ne suivent pas le même chemin d'autorité. Cette qualification n'est pas laissée à l'agent concerné, qui serait juge et partie.

- **Qui qualifie.** L'autorité qui classe une évolution est l'**Orchestrateur**, selon les classes de décisions définies dans [`11-decision-classification-and-policies.md`](./11-decision-classification-and-policies.md). Un ajustement mineur (précision d'une formulation, correction d'un enseignement erroné, sans effet sur le périmètre) peut être appliqué dans le cadre courant ; une évolution importante — changement de périmètre, de mandat ou de comportement structurant — est **soumise au CEO**, seule autorité de validation.
- **Plafond de portée cumulée.** Le risque n'est pas seulement une évolution importante déguisée en mineure ; c'est l'**accumulation** de petits ajustements qui, mis bout à bout, déplacent silencieusement un périmètre. Un **plafond cumulé** encadre donc la somme des ajustements mineurs appliqués à un même agent sur une fenêtre donnée : au-delà de ce plafond, une remontée au CEO devient obligatoire, même si chaque pas pris isolément semblait mineur. Ce mécanisme est aligné sur le « plafond de portée cumulée » de [`11-decision-classification-and-policies.md`](./11-decision-classification-and-policies.md) ; la valeur du plafond et de la fenêtre est fixée dans [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md).

### Validation requise pour les évolutions importantes

Toute **évolution importante** — changement de périmètre, de mandat ou de comportement structurant d'un agent — est soumise à la validation du CEO. Aucun agent ne se ré-autorise seul hors de son domaine, et aucun ne franchit ce seuil par cumul d'ajustements mineurs.

## Comment la dérive est évitée

Un système qui apprend peut aussi mal apprendre : il peut glisser hors de sa spécialité, accumuler des habitudes non fondées ou propager un savoir faux. AI-SOS s'en prémunit par plusieurs mécanismes.

> **Au-delà de la bonne foi.** La dérive décrite ici est une dérive **de bonne foi** : un système qui se trompe sans intention. Elle ne suffit pas à couvrir le risque réel. La malveillance, la **collusion** entre agents, la **complaisance** (sycophantie — dire ce que l'autorité veut entendre) et l'**empoisonnement de la mémoire** relèvent d'un modèle de menace dédié, traité dans [`14-integrity-and-threat-model.md`](./14-integrity-and-threat-model.md). Le présent document s'appuie sur ce modèle de menace et ne le duplique pas.

### Détection du drift

L'organisation surveille les signaux de **dérive** : un agent qui répond de plus en plus souvent hors de son domaine, un écart recommandation/résultat qui se dégrade sans cause identifiée, des décisions qui s'éloignent progressivement des principes fondateurs. La détection repose sur des tendances lues sur la fenêtre, comparées à l'état de référence versionné, selon les seuils de [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md).

### Recadrage sur la spécialité

Lorsqu'une dérive de périmètre est constatée, l'agent est **recadré** sur sa spécialité telle que définie par son contrat de rôle. Ce qui débordait est soit retiré, soit — s'il est jugé utile — redirigé vers l'agent ou le département compétent, jamais absorbé silencieusement.

### Revalidation périodique

Les contrats de rôle et les enseignements consolidés font l'objet d'une **revalidation périodique** : on vérifie qu'ils restent alignés avec les principes du système et avec la réalité observée. Un enseignement qui n'est plus confirmé par les cycles récents perd sa valeur de règle. Cette revalidation a un **propriétaire** — l'Orchestrateur, sous le contrôle du CEO pour toute conséquence importante — et une **fréquence** définie ; propriétaire et fréquence sont fixés dans [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md).

### Quarantaine d'un savoir faux

Lorsqu'un enseignement se révèle faux, il est placé en **quarantaine** : marqué comme non fiable, retiré de la circulation active, et non utilisé pour de nouvelles décisions le temps que la correction soit établie. La quarantaine empêche un savoir douteux de continuer à influencer les cycles pendant son examen.

## Règles de l'apprentissage

### Ce qu'on apprend

- Les écarts entre recommandation et résultat, dans les deux sens (succès reproductible comme échec évitable).
- La **qualité des décisions**, distincte de leurs résultats, y compris pour les recommandations rejetées (contrefactuels) et les décisions validées par politique.
- Les conditions qui distinguent un bon résultat d'un mauvais.
- Les frictions de coordination récurrentes, signalées par le coût de délibération.
- Les signaux faibles de dérive, avant qu'ils ne deviennent des problèmes.

### Ce qu'on ne généralise pas trop vite

- Un enseignement issu d'un cas unique reste un cas, pas une règle, tant qu'il n'est pas confirmé par la répétition.
- Une corrélation observée n'est pas tenue pour une cause sans vérification.
- Un succès dans un contexte donné n'est pas transposé à un contexte différent sans examen de ses conditions.
- Un bon résultat n'est pas confondu avec une bonne décision : on n'ancre pas une pratique sur un coup de chance.
- Une évolution importante d'agent n'est pas décidée sur un signal isolé.

### Traçabilité des enseignements

- Tout enseignement inscrit porte son origine : cycle concerné, écart observé, décision humaine associée.
- Toute évolution d'agent est rattachée à sa version de contrat de rôle et aux retours qui l'ont motivée, y compris le décompte cumulé des ajustements mineurs vis-à-vis du plafond.
- Un enseignement mis en quarantaine ou corrigé conserve la trace de son état antérieur, pour la reproductibilité et l'audit.

## Exemple concret

**Cycle N.** Une demande porte sur le lancement d'une nouvelle offre. La recommandation consolidée préconise un déploiement complet et immédiat. Après décision humaine et exécution, l'observation révèle que l'adoption a été bien plus lente que prévu : l'écart recommandation/résultat est important.

**Enseignement.** La comparaison montre que le problème réel — la maturité insuffisante du marché ciblé — avait été sous-estimé au cadrage. La décision, elle-même, était mal fondée (une information disponible avait été négligée), et non simplement malchanceuse. L'enseignement formulé : « pour ce type d'offre, vérifier la maturité du marché avant de recommander un déploiement complet ; privilégier une mise en marché progressive tant que ce point n'est pas établi ». Il est inscrit en mémoire organisationnelle avec son origine.

**Cycle N+1.** Une demande comparable se présente. La mémoire fournit l'enseignement au cadrage. L'organisation questionne d'emblée la maturité du marché et recommande une mise en marché progressive. L'écart recommandation/résultat, cette fois, se réduit — signe que l'apprentissage a produit un gain de qualité reproductible.

## Cas limites

### Bonne décision, mauvais résultat (chance vs compétence)

Une décision bien fondée, prise avec tout ce qui était alors connaissable, aboutit à un mauvais résultat à cause d'un aléa imprévisible. L'organisation ne l'inscrit pas comme une erreur de méthode : elle sépare la qualité du raisonnement de l'issue. À l'inverse, une décision mal fondée qui réussit par chance n'est pas érigée en bonne pratique. Ce tri protège la mémoire contre les fausses leçons tirées du hasard.

### Apprentissage d'une erreur

Une décision s'est révélée franchement erronée. L'organisation ne cherche pas de coupable mais l'enseignement : quelle condition, non vue au cadrage, aurait changé la décision ? L'erreur devient une règle d'évitement, inscrite et tracée. Un échec sans enseignement extrait est un échec doublé.

### Accumulation d'ajustements mineurs

Un agent reçoit, cycle après cycle, une série d'ajustements chacun jugé mineur. Pris isolément, aucun ne déplace son périmètre ; leur somme, si. Le plafond de portée cumulée se déclenche : la prochaine modification, même mineure en apparence, est remontée au CEO pour examen d'ensemble. On évite ainsi qu'un glissement de mandat ne s'installe par petites touches sans validation.

### Dérive détectée sur un agent

La surveillance signale qu'un agent répond de plus en plus hors de son domaine. Il est recadré sur sa spécialité ; ce qui débordait est redirigé vers l'agent compétent. Si le besoin ainsi révélé est réel et récurrent, il remonte comme proposition d'évolution — création ou extension d'agent — soumise à la validation du CEO, jamais auto-accordée. Si la dérive n'est pas de bonne foi, elle relève du modèle de menace (voir [`14-integrity-and-threat-model.md`](./14-integrity-and-threat-model.md)).

### Savoir faux déjà propagé

Un enseignement inscrit puis diffusé se révèle faux après avoir déjà influencé plusieurs cycles. Il est immédiatement mis en quarantaine. On identifie les décisions qui s'en sont servies, on évalue leur impact, et on émet une correction. La mémoire conserve la trace de l'enseignement erroné et de sa rétractation, afin qu'il ne soit pas ré-appris par mégarde.

### Enseignement contredit plus tard

Un enseignement tenu pour fiable est contredit par des cycles ultérieurs, ou par une conséquence à long horizon apparue après la clôture d'exécution. Plutôt que de trancher brutalement, l'organisation examine les conditions : l'enseignement était-il faux, ou seulement valable dans un contexte plus étroit qu'on ne le croyait ? Il est alors soit corrigé, soit restreint à son domaine réel de validité, soit retiré. La revalidation périodique existe précisément pour rattraper ces cas, et toute modification garde sa trace.
