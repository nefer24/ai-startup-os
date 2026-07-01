# End-to-End Scenarios

> Ce document déroule des scénarios complets, du tout début jusqu'à la mise à jour de la mémoire, pour rendre visible le comportement observable de l'AI Startup OS. Chaque scénario suit la même trame : une demande émane d'un Utilisateur porteur d'un besoin et est prise en charge sous l'autorité du CEO ; le système décide, ou non, de **proposer** l'activation du Conseil Stratégique Dynamique — que **seul le CEO active** explicitement ; l'Orchestrateur mobilise les instances concernées, les Agents spécialisés débattent, une recommandation est produite, la validation du CEO — seule autorité humaine et seul décideur — est sollicitée, puis l'exécution a lieu et la mémoire est mise à jour. Toutes les instances autres que le CEO sont des agents IA consultatifs. On décrit ici uniquement ce qui se passe, jamais comment c'est implémenté.

Ces scénarios s'appuient sur les protocoles décrits dans les documents frères : le cycle de vie d'une demande ([`01-request-lifecycle.md`](./01-request-lifecycle.md)), l'activation du Conseil Stratégique ([`02-strategic-council-activation.md`](./02-strategic-council-activation.md)), le travail de l'Orchestrateur ([`03-orchestrator-workflow.md`](./03-orchestrator-workflow.md)), le protocole de débat ([`04-debate-protocol.md`](./04-debate-protocol.md)) et le protocole de décision ([`05-decision-protocol.md`](./05-decision-protocol.md)). Ils illustrent concrètement le flux de décision formalisé en Phase 2 ([`08-decision-flow.md`](../system/08-decision-flow.md)).

Convention de lecture : chaque étape est numérotée ; les branchements sont signalés par « Si / Sinon » ; chaque scénario se termine par un cas limite montrant une bifurcation du comportement.

---

## Scénario 1 — Création d'un SaaS (ex. pour restaurateurs) — AVEC activation du Conseil Stratégique Dynamique

Contexte : un Utilisateur porte un besoin large et ambigu, du type « Je veux lancer un SaaS pour aider les restaurateurs à gérer leurs commandes et leur fidélité client ». La demande est stratégique, transverse et sans périmètre défini : le système **propose** l'activation du Conseil Stratégique Dynamique, que le CEO devra **activer** explicitement (voir [`02-strategic-council-activation.md`](./02-strategic-council-activation.md)).

### Déroulé

1. La demande émane de l'Utilisateur et est prise en charge sous l'autorité du CEO. Le système accuse réception et ouvre un dossier de traitement traçable (voir [`01-request-lifecycle.md`](./01-request-lifecycle.md)).
2. Le système qualifie la demande : ampleur élevée, incertitude élevée, impact stratégique. Le seuil qui justifie de **proposer** l'activation du Conseil Stratégique Dynamique est franchi.
3. Le système **propose** au CEO l'activation du Conseil Stratégique Dynamique. **Seul le CEO l'active** : dès son accord, le Conseil est composé dynamiquement en fonction du problème posé. Pour un lancement de SaaS destiné aux restaurateurs, il convoque des agents couvrant : la **stratégie** (vision, positionnement), le **business** (modèle économique, canaux), le **produit** (périmètre fonctionnel, priorisation), la **finance** (coûts, tarification, seuil de rentabilité), l'**UX** (parcours utilisateur, ergonomie), le **marketing** (acquisition, message) et la **psychologie utilisateur** (motivations et freins des restaurateurs).
4. Le Conseil Stratégique Dynamique, rattaché au CEO et purement consultatif, travaille **en amont** : il cadre le problème, le reformule en objectifs, identifie les inconnues, fait délibérer ses agents et produit une **recommandation stratégique** unique et argumentée, assortie des risques et des priorités d'exploration. Il ne décide rien.
5. Le Conseil remet sa recommandation stratégique au CEO et est **dissous dès cette remise** : sa composition n'était valable que pour ce cadrage amont, et il ne survit pas à la suite du traitement.
6. Le CEO prend connaissance de la recommandation stratégique, arbitre les **priorités** et confie l'exécution à l'Orchestrateur (voir [`05-decision-protocol.md`](./05-decision-protocol.md)).
7. L'Orchestrateur (voir [`03-orchestrator-workflow.md`](./03-orchestrator-workflow.md)) traduit ces priorités en missions et mobilise les instances d'exécution : Conseils d'Experts spécialisés, Départements (produit, finance, marketing) et Agents spécialisés.
8. Chaque instance produit son analyse : segmentation des restaurateurs, hypothèses de tarification, périmètre du produit minimum viable, parcours d'inscription, plan d'acquisition initial.
9. Les instances entrent en débat contradictoire (voir [`04-debate-protocol.md`](./04-debate-protocol.md)). Exemple de tension : l'agent finance plaide pour un abonnement mensuel élevé afin d'atteindre la rentabilité vite ; l'agent psychologie utilisateur objecte que les petits restaurateurs sont sensibles au prix et exigent une preuve de valeur avant de payer.
10. Le débat converge vers un arbitrage : offre d'entrée à bas prix avec montée en gamme, produit centré d'abord sur la gestion des commandes puis la fidélité.
11. L'**Orchestrateur consolide** les contributions des Conseils d'Experts en **une recommandation finale opérationnelle**, argumentée, assortie des risques et des alternatives écartées.
12. La recommandation finale est présentée au CEO pour décision (voir [`05-decision-protocol.md`](./05-decision-protocol.md)). Le CEO est le seul à trancher, selon quatre issues canoniques :
    - **Approuve** : le système passe à l'exécution.
    - **Ajuste** (ex. « garde tout, mais retire la fidélité de la v1 ») : la recommandation est renvoyée à l'Orchestrateur pour ajustement, puis re-soumise.
    - **Reporte** : le dossier est mis en attente, sans exécution immédiate, avec le motif du report.
    - **Rejette** : le dossier est clôturé avec le motif, sans exécution.
13. Après approbation, l'Orchestrateur lance l'exécution : mise en place des livrables planifiés (spécifications produit, plan de tarification, plan marketing initial).
14. La mémoire est mise à jour : demande, composition du Conseil, recommandation stratégique amont, points de débat, recommandation finale consolidée par l'Orchestrateur, décision du CEO et résultats sont archivés pour réutilisation future.

### Cas limite

Après la remise de la recommandation stratégique, le CEO estime que le marché ciblé (restaurateurs) est trop concurrentiel et demande de pivoter vers les traiteurs événementiels. Comportement observable : le système ne réutilise pas la recommandation existante telle quelle. Comme le problème change de nature, le système **propose** au CEO l'activation d'un **nouveau** Conseil Stratégique Dynamique, que le CEO **active** pour recomposer le cadrage sur le nouveau périmètre (la psychologie utilisateur, le marketing et le business sont reconfigurés autour de la nouvelle cible). Le cycle recommence à l'étape 3, et la mémoire conserve la trace du pivot ainsi que la raison invoquée par le CEO. Cette réactivation n'est pas illimitée : une **borne de réactivation** encadre le nombre de pivots successifs afin d'éviter des cycles infinis (voir [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md)) ; au-delà, l'autorité du CEO est explicitement sollicitée pour statuer sur la poursuite.

---

## Scénario 2 — Analyse d'une entreprise

Contexte : un Utilisateur porte le besoin « Analyse cette entreprise et dis-moi si elle est viable ». La demande est cadrée (objet précis, livrable clair : une analyse) mais peut rester lourde selon la profondeur attendue.

### Déroulé

1. La demande émane de l'Utilisateur, avec les éléments disponibles sur l'entreprise cible, et est prise en charge sous l'autorité du CEO.
2. Le système qualifie la demande : périmètre défini, forte composante analytique. La **proposition** d'activation du Conseil Stratégique Dynamique est **conditionnelle**.
   - **Si** l'analyse est de routine (diagnostic standard) : le système ne propose **pas** le Conseil ; l'Orchestrateur mobilise directement les départements d'analyse.
   - **Si** l'analyse comporte un enjeu stratégique (acquisition, partenariat, investissement) : le système **propose** au CEO l'activation du Conseil Stratégique Dynamique, que **seul le CEO active** pour cadrer les critères de décision en amont.
3. L'Orchestrateur mobilise les Départements d'analyse : analyse financière, analyse de marché, analyse concurrentielle, analyse opérationnelle et analyse des risques.
4. Chaque département produit son diagnostic partiel à partir des données fournies, en signalant explicitement les données manquantes.
5. Les départements confrontent leurs conclusions en débat (voir [`04-debate-protocol.md`](./04-debate-protocol.md)). Exemple : l'analyse financière juge l'entreprise saine, tandis que l'analyse de marché signale un déclin structurel du secteur.
6. L'**Orchestrateur consolide** une **recommandation** graduée (ex. « viable à court terme, fragile à trois ans ») avec le niveau de confiance et les hypothèses.
7. La recommandation est présentée au CEO pour décision et pour orienter la suite (approfondir, arrêter, décider), selon les quatre issues canoniques.
   - **Si** le CEO **Approuve** : la conclusion est actée et, le cas échéant, transmise pour action.
   - **Si** le CEO **Ajuste** (demande d'approfondissement) : l'Orchestrateur relance les départements concernés avec des questions ciblées.
   - **Si** le CEO **Reporte** : la conclusion est mise en attente, sans action engageante.
   - **Si** le CEO **Rejette** : le dossier est clôturé avec le motif.
8. Après approbation, l'exécution consiste à produire le rapport final. Si un Conseil Stratégique Dynamique avait été activé, il avait déjà été **dissous dès la remise** de son cadrage amont.
9. La mémoire est mise à jour : profil de l'entreprise analysée, méthode suivie, conclusions et décision du CEO.

### Cas limite

Les données fournies sont insuffisantes ou contradictoires pour conclure. Comportement observable : le système ne produit pas une recommandation faussement assurée. Il remonte au CEO un état intermédiaire indiquant les lacunes précises et propose des options (fournir plus de données, restreindre la question, ou accepter une analyse sous réserve). Aucune exécution engageante n'a lieu tant que le CEO n'a pas choisi. La mémoire enregistre l'insuffisance de données comme apprentissage.

---

## Scénario 3 — Création d'une stratégie marketing

Contexte : un Utilisateur porte le besoin « Construis-moi la stratégie marketing pour lancer le produit ». La demande est transverse et créative ; elle mobilise plusieurs expertises coordonnées.

### Déroulé

1. La demande émane de l'Utilisateur, en précisant si possible le produit, la cible et le budget, et est prise en charge sous l'autorité du CEO.
2. Le système qualifie la demande : impact stratégique modéré à élevé.
   - **Si** la stratégie engage fortement le positionnement de l'entreprise : le système **propose** au CEO l'activation du Conseil Stratégique Dynamique, que **seul le CEO active** (agents stratégie, marketing, business, psychologie utilisateur) pour cadrer l'orientation en amont.
   - **Sinon** (campagne circonscrite) : l'Orchestrateur mobilise directement le Département marketing.
3. L'Orchestrateur répartit le travail : définition des cibles, proposition de valeur et message, choix des canaux, plan de contenu, budget et indicateurs de succès.
4. Les Conseils d'Experts et Agents spécialisés produisent chacun leur contribution (personas, tunnel d'acquisition, calendrier, estimation budgétaire).
5. Débat contradictoire (voir [`04-debate-protocol.md`](./04-debate-protocol.md)). Exemple : l'agent orienté croissance rapide privilégie la publicité payante ; l'agent orienté crédibilité privilégie le contenu organique et les partenariats, plus lents mais durables.
6. Le débat aboutit à un dosage argumenté (mix payant/organique par phases). L'**Orchestrateur consolide** une **recommandation** unique.
7. La recommandation, incluant budget et indicateurs, est soumise au CEO pour décision, selon les quatre issues canoniques (Approuve / Ajuste / Reporte / Rejette).
   - **Si** validation graduée applicable : le CEO a pré-approuvé une politique (ex. « toute stratégie sous X de budget peut être lancée sans revalidation »). Dans ce cas, seul le CEO peut avoir défini cette politique, et le système l'applique automatiquement dans les bornes fixées.
   - **Sinon** : décision explicite du CEO requise.
8. Après approbation, l'Orchestrateur déclenche l'exécution : production des livrables marketing et lancement planifié.
9. Si un Conseil Stratégique Dynamique avait été activé, il avait déjà été **dissous dès la remise** de son cadrage amont.
10. La mémoire est mise à jour : stratégie retenue, budget, indicateurs et arbitrages de débat.

### Cas limite

Le budget demandé par la recommandation dépasse le plafond de la politique de validation graduée pré-approuvée par le CEO. Comportement observable : le système n'exécute **pas** automatiquement. Il détecte le dépassement de seuil, suspend l'exécution et escalade au CEO pour décision explicite (voir [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md)). La validation graduée ne s'applique que dans les limites définies par le CEO ; hors de ces limites, l'autorité humaine reprend systématiquement la main. La mémoire enregistre l'escalade et la décision finale.

---

## Scénario 4 — Résolution d'un problème juridique

Contexte : un Utilisateur porte le besoin « Nous avons un problème juridique avec un contrat, aide-moi à le résoudre ». La demande a un fort niveau de risque et exige des expertises spécialisées. La dimension **multi-juridiction** (juridiction applicable, conflit de lois) est ici une dimension **transverse** à examiner d'emblée, et non un simple cas limite.

### Déroulé

1. La demande émane de l'Utilisateur, avec le contexte du litige, et est prise en charge sous l'autorité du CEO.
2. Le système qualifie la demande : risque élevé, expertise spécialisée requise, et interroge systématiquement la **juridiction applicable** (une ou plusieurs, avec risque de conflit de lois).
   - **Si** l'enjeu est stratégique pour l'entreprise (réputation, survie, gros montant) : le système **propose** au CEO l'activation du Conseil Stratégique Dynamique, que **seul le CEO active**, avec un axe juridique et la dimension multi-juridiction intégrée au cadrage amont.
   - **Sinon** : l'Orchestrateur mobilise directement le Conseil d'Experts juridiques.
3. L'Orchestrateur mobilise les Agents spécialisés juridiques et, en appui, les départements concernés (finance pour l'exposition financière, opérations pour l'impact métier). La couverture est dimensionnée selon les juridictions concernées.
4. Les Agents spécialisés juridiques établissent le diagnostic : nature du litige, juridiction(s) applicable(s), obligations, risques, options (négociation, mise en conformité, contentieux), en signalant tout conflit de lois potentiel.
5. Débat contradictoire (voir [`04-debate-protocol.md`](./04-debate-protocol.md)). Exemple : un agent recommande une transaction rapide pour limiter le risque ; un autre recommande de contester, jugeant la position solide ; un troisième soulève qu'une juridiction concurrente change l'analyse.
6. L'**Orchestrateur consolide** une **recommandation** hiérarchisant les options par risque et coût, avec les conséquences de chacune et l'exposition propre à chaque juridiction.
7. La recommandation est **obligatoirement** soumise au CEO. En matière juridique, aucune action engageante n'est prise sans décision humaine explicite ; la validation graduée ne s'applique pas aux décisions à risque élevé, sauf politique très restrictive définie par le CEO lui-même. Les quatre issues canoniques (Approuve / Ajuste / Reporte / Rejette) s'appliquent.
   - **Si** le CEO **Approuve** une option : l'Orchestrateur exécute (préparation des documents, communication, suivi).
   - **Si** le CEO **Ajuste** (demande un second avis) : les Agents spécialisés approfondissent l'option retenue.
   - **Si** le CEO **Reporte** ou **Rejette** : aucune action engageante n'est lancée, le motif est consigné.
8. Après approbation, exécution et suivi. Si un Conseil Stratégique Dynamique avait été activé, il avait déjà été **dissous dès la remise** de son cadrage amont.
9. La mémoire est mise à jour : nature du problème, juridictions en cause, options examinées, décision du CEO et issue.

### Cas limite

Le litige révèle une complexité multi-juridiction encore plus profonde : les parties sont soumises à des droits contradictoires sans règle de rattachement claire. Comportement observable : l'Orchestrateur recompose la mobilisation pour couvrir chaque juridiction concernée et ajoute une étape de réconciliation où les analyses par pays sont confrontées afin d'exposer les conflits de droit. La recommandation présentée au CEO expose explicitement les divergences entre juridictions et l'absence de solution uniforme, au lieu de masquer la complexité. Le CEO tranche en connaissance de cause. Cette recomposition reste encadrée par une **borne de réactivation** afin d'éviter une multiplication infinie des analyses (voir [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md)). La mémoire conserve le caractère multi-juridiction comme précédent.

---

## Ce que ces scénarios démontrent

À travers ces quatre parcours, plusieurs invariants du comportement du système apparaissent, quels que soient la demande ou le domaine :

- **Une seule autorité, le CEO.** Le CEO est le seul décideur humain. Aucune instance ne prend de décision engageante à sa place. Toutes les autres — Conseil Stratégique Dynamique, Conseils d'Experts, Départements, Agents spécialisés — sont des agents IA **consultatifs**.
- **Activation contextuelle et explicite du Conseil Stratégique.** Le système, via l'Orchestrateur, **propose** l'activation du Conseil Stratégique Dynamique lorsque l'ampleur ou l'incertitude le justifient ; **seul le CEO l'active**. Composé dynamiquement selon le problème et rattaché au CEO, il produit une **recommandation stratégique en amont** puis est **dissous dès sa remise** — il ne survit pas à l'orchestration et ne consolide pas la recommandation finale.
- **Consolidation par l'Orchestrateur.** La recommandation finale opérationnelle remontée au CEO est **consolidée par l'Orchestrateur** à partir des Conseils d'Experts, une fois le cadrage stratégique amont remis et le Conseil dissous.
- **Validation humaine systématique.** Toute recommandation remonte au CEO, qui tranche selon quatre issues canoniques : **Approuve / Ajuste / Reporte / Rejette**. La validation graduée n'existe que dans les limites de politiques **pré-approuvées par le CEO seul** ; hors de ces bornes, ou face à un risque élevé, l'autorité humaine reprend la main.
- **Débat avant recommandation.** Le système fait délibérément s'affronter des points de vue contradictoires (voir [`04-debate-protocol.md`](./04-debate-protocol.md)) avant de converger vers une recommandation unique et argumentée.
- **Bornes et seuils.** La réactivation du Conseil Stratégique Dynamique et les recompositions sont encadrées par des bornes qui empêchent les cycles infinis (voir [`13-bounds-and-thresholds.md`](./13-bounds-and-thresholds.md)).
- **Traçabilité.** Chaque demande produit un dossier suivi de bout en bout : composition des instances, points de débat, recommandation, décision du CEO et exécution.
- **Mémoire mise à jour.** Chaque scénario se termine par un enrichissement de la mémoire, y compris les cas limites, les pivots et les escalades, afin d'améliorer les traitements futurs.

Ces invariants prolongent, au niveau du comportement observable, le flux de décision formalisé en Phase 2 ([`08-decision-flow.md`](../system/08-decision-flow.md)) et les protocoles détaillés dans les documents frères ([`01-request-lifecycle.md`](./01-request-lifecycle.md), [`02-strategic-council-activation.md`](./02-strategic-council-activation.md), [`03-orchestrator-workflow.md`](./03-orchestrator-workflow.md), [`04-debate-protocol.md`](./04-debate-protocol.md), [`05-decision-protocol.md`](./05-decision-protocol.md)).
