# Risk Policy

> Cette politique décrit comment AI-SOS évalue le **risque** d'une demande ou d'une décision. Elle fournit un vocabulaire commun et des règles observables pour transformer une intuition de danger en un niveau de risque explicite qui déclenche des garde-fous proportionnés. Les agents produisent cette évaluation à titre consultatif ; le **CEO reste la seule autorité et le seul décideur**, et il peut réviser tout niveau attribué.

## Objectif

L'objectif est de garantir qu'aucune demande ni décision ne progresse sans une lecture explicite de ce qu'elle peut coûter si elle tourne mal. Le risque n'est pas une opinion sur la qualité d'une idée : c'est une estimation structurée de l'ampleur, de la vraisemblance et de la réversibilité de ses conséquences négatives.

Cette politique poursuit trois buts :

1. Rendre le risque **observable** : chaque évaluation repose sur des critères nommés, pas sur un ressenti.
2. Rendre le risque **actionnable** : chaque niveau déclenche des garde-fous précis, connus à l'avance.
3. Rendre le risque **traçable** : l'évaluation et ses justifications sont conservées pour être relues, contestées et corrigées.

Le risque produit ici alimente directement la classification des décisions ([`07-decision-classification-policy.md`](./07-decision-classification-policy.md)) et se combine avec l'évaluation d'incertitude ([`03-uncertainty-policy.md`](./03-uncertainty-policy.md)) : le risque mesure la gravité des conséquences, l'incertitude mesure notre confiance dans nos propres estimations.

## Critères

Une évaluation de risque examine chaque demande ou décision selon les critères observables suivants. Aucun critère ne suffit seul ; ils se lisent ensemble.

- **Impact potentiel** — l'ampleur du dommage possible, décliné par nature :
  - *Financier* : perte, dépense engagée, manque à gagner, engagement contractuel.
  - *Réputationnel* : atteinte à la confiance des clients, partenaires ou du public.
  - *Humain* : effet sur des personnes (sécurité, bien-être, équité de traitement).
  - *Juridique* : non-conformité, responsabilité, litige, sanction.
  - *Sécurité / confidentialité* : exposition de données, d'accès ou de secrets.
- **Probabilité** — la vraisemblance que le dommage se produise réellement, estimée sur une échelle qualitative (rare, occasionnel, probable, quasi certain).
- **Irréversibilité** — la difficulté ou l'impossibilité de revenir en arrière une fois la décision exécutée. Une action annulable en un geste diffère radicalement d'une action définitive.
- **Portée** — le nombre de personnes, de clients, de systèmes ou de processus affectés. Un effet local n'a pas le même poids qu'un effet transversal.
- **Horizon temporel** — le moment où les conséquences se manifestent : immédiates, à court terme, ou latentes sur le long terme.
- **Détectabilité** — la facilité avec laquelle un problème serait repéré avant qu'il ne cause un dommage. Un risque invisible jusqu'à l'incident est plus dangereux qu'un risque signalé tôt.

Ces critères sont *observables* : pour chacun, l'agent doit pouvoir citer un élément concret de la demande qui justifie la valeur retenue, et non une appréciation générale.

## Règles

**Règle 1 — Combiner impact et probabilité.** Le niveau de risque se construit en croisant l'**impact potentiel** (le plus élevé parmi les natures listées) avec la **probabilité**. Le résultat se range dans l'un des quatre niveaux suivants :

- **Faible** : impact limité et probabilité basse. Conséquences mineures, locales, réversibles.
- **Modéré** : impact ou probabilité notable, mais dommage contenu et récupérable.
- **Élevé** : impact important, probabilité réelle, ou irréversibilité marquée.
- **Critique** : impact majeur (humain, juridique, financier de grande ampleur, ou sécurité/confidentialité) avec probabilité non négligeable, ou toute conséquence irréversible à large portée.

**Règle 2 — Rehausser selon les critères aggravants.** L'irréversibilité, une portée large, un horizon latent ou une faible détectabilité **relèvent** le niveau d'un cran au moins. Un impact modéré mais irréversible et difficilement détectable est traité comme élevé.

**Règle 3 — Ce que chaque niveau déclenche.**

- **Faible** : traitement normal. L'auto-validation par politique reste possible si les autres politiques l'autorisent.
- **Modéré** : garde-fous renforcés (vérification supplémentaire, second regard d'un agent consultatif) et documentation explicite de l'évaluation.
- **Élevé** : **avocat du diable obligatoire** ([`../behavior/14-integrity-and-threat-model.md`](../behavior/14-integrity-and-threat-model.md)) chargé de contester activement l'évaluation, plus passage par la porte qualité ([`09-quality-gate-policy.md`](./09-quality-gate-policy.md)). L'auto-validation par politique est **interdite** au-delà de ce seuil.
- **Critique** : **remontée obligatoire au CEO** ([`04-escalation-policy.md`](./04-escalation-policy.md)) pour décision explicite. Aucun agent ne peut valider seul un risque critique ; les agents fournissent l'analyse, le CEO tranche.

**Règle 4 — Interdiction d'auto-validation au-delà du seuil.** À partir du niveau **élevé**, aucune politique ne peut servir à s'auto-approuver : le franchissement exige soit un contrôle indépendant (élevé), soit la décision du CEO (critique). Ce seuil est une garantie contre l'auto-justification.

**Règle 5 — Le risque alimente la classification.** Le niveau de risque est une entrée de la classification des décisions ([`07-decision-classification-policy.md`](./07-decision-classification-policy.md)). Une décision ne peut être classée dans une catégorie moins contraignante que ce que son niveau de risque impose.

**Règle 6 — Rôle consultatif, autorité unique.** Les agents évaluent, contestent et recommandent. Ils n'ont jamais l'autorité de décider à la place du CEO. Toute évaluation de risque est une recommandation ; la décision finale, en particulier pour les niveaux élevé et critique, appartient au CEO seul.

## Exemples

**Exemple 1 — Risque faible, réversible.**
Un agent propose d'ajuster le libellé d'un message d'accueil interne visible seulement par l'équipe. Impact réputationnel et financier négligeables, portée limitée à un système interne, action immédiatement annulable, détectabilité immédiate. Croisement impact/probabilité : **faible**. Traitement normal, auto-validation par politique possible. Aucun avocat du diable, aucune remontée.

**Exemple 2 — Risque élevé, irréversible.**
Un agent propose de supprimer définitivement un ensemble de données clients jugées obsolètes. Impact potentiel juridique et de confidentialité important, portée large (nombreux clients), **irréversibilité totale**, détectabilité faible (l'erreur n'apparaîtrait qu'après coup). Le croisement donne un impact important et l'irréversibilité relève encore le niveau : **élevé**, voire **critique** compte tenu de la portée et de la nature des données. Déclenche l'avocat du diable obligatoire, la porte qualité, l'interdiction d'auto-validation, et une remontée au CEO si l'analyse confirme le caractère critique. Le CEO décide.

## Cas limites

- **Risque sous-évalué.** Un agent minimise l'impact ou la probabilité, par excès de confiance ou pour accélérer la décision. Parade : l'avocat du diable (dès le niveau élevé) a pour mission explicite de contester l'évaluation à la baisse, et toute évaluation doit citer des critères observables vérifiables. En cas de doute sur la fiabilité de l'estimation, traiter le risque comme d'un cran supérieur et relire via l'incertitude ([`03-uncertainty-policy.md`](./03-uncertainty-policy.md)).

- **Faible probabilité, impact catastrophique.** Un événement jugé rare mais dont l'impact serait majeur (humain, juridique, sécurité). La combinaison mécanique impact × probabilité pourrait le classer bas ; ce serait une erreur. Règle : un impact catastrophique irréversible impose un niveau **critique** indépendamment de la probabilité estimée, et donc une remontée au CEO ([`04-escalation-policy.md`](./04-escalation-policy.md)).

- **Risque qui n'apparaît qu'à l'exécution.** Un danger indétectable au moment de l'évaluation, qui ne se révèle qu'au cours de l'action. Parade : privilégier les étapes réversibles et incrémentales, exiger des points de contrôle observables pendant l'exécution, et prévoir une capacité d'arrêt. Une faible détectabilité relève le niveau de risque (Règle 2) précisément pour compenser cette cécité initiale.

## Questions ouvertes

- Comment calibrer les seuils entre niveaux (faible / modéré / élevé / critique) sans figer une grille qui deviendrait mécanique et contournable ? Le renvoi aux bornes et seuils configurables reste à préciser avec [`../behavior/14-integrity-and-threat-model.md`](../behavior/14-integrity-and-threat-model.md).
- Faut-il pondérer différemment les natures d'impact (par exemple, l'impact humain domine-t-il toujours l'impact financier) ?
- Comment réévaluer un risque en cours d'exécution lorsque de nouvelles informations le font changer de niveau, sans multiplier les remontées au CEO ?
- Quelle articulation exacte entre risque et incertitude ([`03-uncertainty-policy.md`](./03-uncertainty-policy.md)) lorsque l'incertitude est elle-même très élevée : traiter l'ignorance comme un facteur aggravant du risque, et jusqu'à quel point ?
