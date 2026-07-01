# End-to-End Scenarios

> Ce document déroule des scénarios complets, du tout début jusqu'à la mise à jour de la mémoire, pour rendre visible le comportement observable de l'AI Startup OS. Chaque scénario suit la même trame : une demande arrive, le système décide d'activer ou non le Conseil Stratégique Dynamique, orchestre les instances concernées, laisse débattre les agents, produit une recommandation, sollicite la validation du CEO — seule autorité humaine et seul décideur — puis exécute et met à jour la mémoire. Toutes les instances autres que le CEO sont des agents IA consultatifs. On décrit ici uniquement ce qui se passe, jamais comment c'est implémenté.

Ces scénarios s'appuient sur les protocoles décrits chez les documents frères : le cycle de vie d'une demande (`./01-request-lifecycle.md`), l'activation du Conseil Stratégique (`./02-strategic-council-activation.md`), le travail de l'orchestrateur (`./03-orchestrator-workflow.md`), le protocole de débat (`./04-debate-protocol.md`) et le protocole de décision (`./05-decision-protocol.md`). Ils illustrent concrètement le flux de décision formalisé en Phase 2 (`../system/08-decision-flow.md`).

Convention de lecture : chaque étape est numérotée ; les branchements sont signalés par « Si / Sinon » ; chaque scénario se termine par un cas limite montrant une bifurcation du comportement.

---

## Scénario 1 — Création d'un SaaS (ex. pour restaurateurs) — AVEC activation du Conseil Stratégique Dynamique

Contexte : le CEO formule une demande large et ambiguë, du type « Je veux lancer un SaaS pour aider les restaurateurs à gérer leurs commandes et leur fidélité client ». La demande est stratégique, transverse et sans périmètre défini : elle déclenche l'activation du Conseil Stratégique Dynamique (voir `./02-strategic-council-activation.md`).

### Déroulé

1. Le CEO soumet la demande. Le système accuse réception et ouvre un dossier de traitement traçable (voir `./01-request-lifecycle.md`).
2. Le système qualifie la demande : ampleur élevée, incertitude élevée, impact stratégique. Le seuil d'activation du Conseil Stratégique Dynamique est franchi.
3. Le système compose dynamiquement le Conseil en fonction du problème posé. Pour un lancement de SaaS destiné aux restaurateurs, il convoque des agents couvrant : la **stratégie** (vision, positionnement), le **business** (modèle économique, canaux), le **produit** (périmètre fonctionnel, priorisation), la **finance** (coûts, tarification, seuil de rentabilité), l'**UX** (parcours utilisateur, ergonomie), le **marketing** (acquisition, message), et la **psychologie utilisateur** (motivations et freins des restaurateurs).
4. Le Conseil, rattaché au CEO et purement consultatif, cadre le problème : il reformule la demande en objectifs, identifie les inconnues et propose des axes d'exploration. Il ne décide rien.
5. L'orchestrateur (voir `./03-orchestrator-workflow.md`) traduit ces axes en missions et mobilise les instances d'exécution : Conseils d'Experts spécialisés, Départements (produit, finance, marketing) et Agents opérationnels.
6. Chaque instance produit son analyse : segmentation des restaurateurs, hypothèses de tarification, périmètre du produit minimum viable, parcours d'inscription, plan d'acquisition initial.
7. Les instances entrent en débat contradictoire (voir `./04-debate-protocol.md`). Exemple de tension : l'agent finance plaide pour un abonnement mensuel élevé afin d'atteindre la rentabilité vite ; l'agent psychologie utilisateur objecte que les petits restaurateurs sont sensibles au prix et exigent une preuve de valeur avant de payer.
8. Le débat converge vers un arbitrage : offre d'entrée à bas prix avec montée en gamme, produit centré d'abord sur la gestion des commandes puis la fidélité.
9. Le Conseil Stratégique synthétise l'ensemble en **une recommandation unique et argumentée**, assortie des risques et des alternatives écartées.
10. La recommandation est présentée au CEO pour **validation** (voir `./05-decision-protocol.md`). Le CEO est le seul à trancher.
    - **Si** le CEO valide : le système passe à l'exécution.
    - **Si** le CEO amende (ex. « garde tout, mais retire la fidélité de la v1 ») : la recommandation est renvoyée à l'orchestrateur pour ajustement, puis re-soumise.
    - **Si** le CEO rejette : le dossier est clôturé avec le motif, sans exécution.
11. Après validation, l'orchestrateur lance l'exécution : mise en place des livrables planifiés (spécifications produit, plan de tarification, plan marketing initial).
12. Le Conseil Stratégique Dynamique, sa mission accomplie, est **dissous**. Sa composition n'était valable que pour ce problème.
13. La mémoire est mise à jour : demande, composition du Conseil, points de débat, recommandation, décision du CEO et résultats sont archivés pour réutilisation future.

### Cas limite

Au moment de la validation, le CEO estime que le marché ciblé (restaurateurs) est trop concurrentiel et demande de pivoter vers les traiteurs événementiels. Comportement observable : le système ne réutilise pas la synthèse existante telle quelle. Comme le problème change de nature, le Conseil précédent est dissous et un **nouveau** Conseil Stratégique Dynamique est recomposé pour le nouveau périmètre (la psychologie utilisateur, le marketing et le business sont reconfigurés autour de la nouvelle cible). Le cycle recommence à l'étape 3, et la mémoire conserve la trace du pivot ainsi que la raison invoquée par le CEO.

---

## Scénario 2 — Analyse d'une entreprise

Contexte : le CEO demande « Analyse cette entreprise et dis-moi si elle est viable ». La demande est cadrée (objet précis, livrable clair : une analyse) mais peut rester lourde selon la profondeur attendue.

### Déroulé

1. Le CEO soumet la demande avec les éléments disponibles sur l'entreprise cible.
2. Le système qualifie la demande : périmètre défini, forte composante analytique. L'activation du Conseil Stratégique Dynamique est **conditionnelle**.
   - **Si** l'analyse est de routine (diagnostic standard) : le Conseil n'est **pas** activé ; l'orchestrateur mobilise directement les départements d'analyse.
   - **Si** l'analyse comporte un enjeu stratégique (acquisition, partenariat, investissement) : le Conseil Stratégique Dynamique est activé pour cadrer les critères de décision.
3. L'orchestrateur mobilise les Départements d'analyse : analyse financière, analyse de marché, analyse concurrentielle, analyse opérationnelle et analyse des risques.
4. Chaque département produit son diagnostic partiel à partir des données fournies, en signalant explicitement les données manquantes.
5. Les départements confrontent leurs conclusions en débat (voir `./04-debate-protocol.md`). Exemple : l'analyse financière juge l'entreprise saine, tandis que l'analyse de marché signale un déclin structurel du secteur.
6. Le système consolide une **recommandation** graduée (ex. « viable à court terme, fragile à trois ans ») avec le niveau de confiance et les hypothèses.
7. La recommandation est présentée au CEO pour validation ou pour orienter la suite (approfondir, arrêter, décider).
   - **Si** le CEO valide : la conclusion est actée et, le cas échéant, transmise pour action.
   - **Si** le CEO demande un approfondissement : l'orchestrateur relance les départements concernés avec des questions ciblées.
8. Après validation, l'exécution consiste à produire le rapport final et, si un Conseil avait été activé, celui-ci est dissous.
9. La mémoire est mise à jour : profil de l'entreprise analysée, méthode suivie, conclusions et décision du CEO.

### Cas limite

Les données fournies sont insuffisantes ou contradictoires pour conclure. Comportement observable : le système ne produit pas une recommandation faussement assurée. Il remonte au CEO un état intermédiaire indiquant les lacunes précises et propose des options (fournir plus de données, restreindre la question, ou accepter une analyse sous réserve). Aucune exécution engageante n'a lieu tant que le CEO n'a pas choisi. La mémoire enregistre l'insuffisance de données comme apprentissage.

---

## Scénario 3 — Création d'une stratégie marketing

Contexte : le CEO demande « Construis-moi la stratégie marketing pour lancer le produit ». La demande est transverse et créative ; elle mobilise plusieurs expertises coordonnées.

### Déroulé

1. Le CEO soumet la demande, en précisant si possible le produit, la cible et le budget.
2. Le système qualifie la demande : impact stratégique modéré à élevé.
   - **Si** la stratégie engage fortement le positionnement de l'entreprise : le Conseil Stratégique Dynamique est activé (agents stratégie, marketing, business, psychologie utilisateur).
   - **Sinon** (campagne circonscrite) : l'orchestrateur mobilise directement le Département marketing.
3. L'orchestrateur répartit le travail : définition des cibles, proposition de valeur et message, choix des canaux, plan de contenu, budget et indicateurs de succès.
4. Les Conseils d'Experts et Agents produisent chacun leur contribution (personas, tunnel d'acquisition, calendrier, estimation budgétaire).
5. Débat contradictoire (voir `./04-debate-protocol.md`). Exemple : l'agent orienté croissance rapide privilégie la publicité payante ; l'agent orienté crédibilité privilégie le contenu organique et les partenariats, plus lents mais durables.
6. Le débat aboutit à un dosage argumenté (mix payant/organique par phases) et à une **recommandation** unique.
7. La recommandation, incluant budget et indicateurs, est soumise au CEO pour validation.
   - **Si** validation graduée applicable : le CEO a pré-approuvé une politique (ex. « toute stratégie sous X de budget peut être lancée sans revalidation »). Dans ce cas, seul le CEO peut avoir défini cette politique, et le système l'applique automatiquement dans les bornes fixées.
   - **Sinon** : validation explicite du CEO requise.
8. Après validation, l'orchestrateur déclenche l'exécution : production des livrables marketing et lancement planifié.
9. Si un Conseil Stratégique avait été activé, il est dissous.
10. La mémoire est mise à jour : stratégie retenue, budget, indicateurs et arbitrages de débat.

### Cas limite

Le budget demandé par la recommandation dépasse le plafond de la politique de validation graduée pré-approuvée par le CEO. Comportement observable : le système n'exécute **pas** automatiquement. Il détecte le dépassement de seuil, suspend l'exécution et escalade au CEO pour validation explicite. La validation graduée ne s'applique que dans les limites définies par le CEO ; hors de ces limites, l'autorité humaine reprend systématiquement la main. La mémoire enregistre l'escalade et la décision finale.

---

## Scénario 4 — Résolution d'un problème juridique

Contexte : le CEO demande « Nous avons un problème juridique avec un contrat, aide-moi à le résoudre ». La demande a un fort niveau de risque et exige des expertises spécialisées.

### Déroulé

1. Le CEO soumet la demande avec le contexte du litige.
2. Le système qualifie la demande : risque élevé, expertise spécialisée requise.
   - **Si** l'enjeu est stratégique pour l'entreprise (réputation, survie, gros montant) : le Conseil Stratégique Dynamique est activé et intègre un axe juridique.
   - **Sinon** : l'orchestrateur mobilise directement le Conseil d'Experts juridiques.
3. L'orchestrateur mobilise les Agents juridiques et, en appui, les départements concernés (finance pour l'exposition financière, opérations pour l'impact métier).
4. Les agents juridiques établissent le diagnostic : nature du litige, obligations, risques, options (négociation, mise en conformité, contentieux).
5. Débat contradictoire (voir `./04-debate-protocol.md`). Exemple : un agent recommande une transaction rapide pour limiter le risque ; un autre recommande de contester, jugeant la position solide.
6. Le système consolide une **recommandation** hiérarchisant les options par risque et coût, avec les conséquences de chacune.
7. La recommandation est **obligatoirement** soumise au CEO. En matière juridique, aucune action engageante n'est prise sans validation humaine explicite ; la validation graduée ne s'applique pas aux décisions à risque élevé, sauf politique très restrictive définie par le CEO lui-même.
   - **Si** le CEO choisit une option : l'orchestrateur exécute (préparation des documents, communication, suivi).
   - **Si** le CEO demande un second avis : les agents approfondissent l'option retenue.
8. Après validation, exécution et suivi ; si un Conseil Stratégique avait été activé, il est dissous.
9. La mémoire est mise à jour : nature du problème, options examinées, décision du CEO et issue.

### Cas limite — dimension multi-juridiction

Le litige révèle que le contrat engage des parties dans plusieurs pays, soumis à des droits différents et potentiellement contradictoires. Comportement observable : l'orchestrateur ne traite pas le problème comme mono-juridiction. Il recompose la mobilisation pour couvrir chaque juridiction concernée et ajoute une étape de réconciliation où les analyses par pays sont confrontées afin d'exposer les conflits de droit. La recommandation présentée au CEO expose explicitement les divergences entre juridictions et l'absence de solution uniforme, au lieu de masquer la complexité. Le CEO tranche en connaissance de cause. La mémoire conserve le caractère multi-juridiction comme précédent.

---

## Ce que ces scénarios démontrent

À travers ces quatre parcours, plusieurs invariants du comportement du système apparaissent, quels que soient la demande ou le domaine :

- **Une seule autorité, le CEO.** Le CEO est le seul décideur humain. Aucune instance ne prend de décision engageante à sa place. Toutes les autres — Conseil Stratégique Dynamique, Conseils d'Experts, Départements, Agents — sont des agents IA **consultatifs**.
- **Activation contextuelle du Conseil Stratégique.** Le Conseil Stratégique Dynamique n'est activé que lorsque l'ampleur ou l'incertitude le justifient. Il est composé dynamiquement selon le problème, rattaché au CEO, puis **dissous** une fois sa mission remplie.
- **Validation humaine systématique.** Toute recommandation remonte au CEO. La validation graduée n'existe que dans les limites de politiques **pré-approuvées par le CEO seul** ; hors de ces bornes, ou face à un risque élevé, l'autorité humaine reprend la main.
- **Débat avant recommandation.** Le système fait délibérément s'affronter des points de vue contradictoires (voir `./04-debate-protocol.md`) avant de converger vers une recommandation unique et argumentée.
- **Traçabilité.** Chaque demande produit un dossier suivi de bout en bout : composition des instances, points de débat, recommandation, décision du CEO et exécution.
- **Mémoire mise à jour.** Chaque scénario se termine par un enrichissement de la mémoire, y compris les cas limites, les pivots et les escalades, afin d'améliorer les traitements futurs.

Ces invariants prolongent, au niveau du comportement observable, le flux de décision formalisé en Phase 2 (`../system/08-decision-flow.md`) et les protocoles détaillés dans les documents frères (`./01-request-lifecycle.md`, `./02-strategic-council-activation.md`, `./03-orchestrator-workflow.md`, `./04-debate-protocol.md`, `./05-decision-protocol.md`).
