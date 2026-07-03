# Revue stratégique après la PR #52 — Faut-il connecter un vrai LLM maintenant ?

> **Statut** : avis stratégique **impartial**, demandé par le CEO après fusion de la PR #52.
> **Date** : 2026-07-03.
> **Nature** : analyse et recommandation. **Aucun code proposé.** Ce rapport n'hésite pas à dire
> que certaines PR étaient prématurées ni à recommander un changement de direction.
> **Méthode** : fondé sur l'état réel du dépôt (inventaire des modules et de leur contenu), pas
> sur les intentions.

---

## Constat de départ : une asymétrie nette

Un inventaire du cœur (`src/aisos/`) révèle une asymétrie qu'il faut nommer sans détour :

- **Ce qui est profondément construit** : la **plomberie de connexion LLM**. En M0 puis M1, six
  PR (#47→#52) ont empilé secrets → transport HTTP → adaptateur → client HTTP déterministe →
  contrat backend → backend déterministe, chacune à 100 % de couverture.
- **Ce qui n'existe pas encore** : le **cerveau**. Les packages `agents/`, `councils/`,
  `services/`, `runtime/` sont des **placeholders documentés** — littéralement « aucune
  définition exécutable » (Phase 13, squelette). Aucun Conseil d'Experts, aucun débat
  multi-tours, aucun département, aucun agent qui *raisonne*. La `Recommendation` — l'objet
  central du système — n'est produite nulle part par une vraie logique : elle sort du **stub**
  `src/aisos/slice/runtime.py`.

Autrement dit : **nous avons construit une prise de courant très soignée, à deux étages, pour un
appareil qui n'existe pas encore.** C'est le fait le plus important de cette revue.

---

## 1. Ce qui est désormais suffisamment solide

Ces briques sont réelles (logique + tests), pas des squelettes. Elles constituent un socle de
gouvernance de qualité.

- **Gouvernance & invariants** : audit source unique (hash-chaîné, append-only), activation
  CEO-only (refus par défaut), « no automatic decision », défaut conservateur (doute → CEO).
  Prouvés par 120 tests de gouvernance.
- **Ossature d'exécution** : orchestrateur (coordinator, dispatcher, lifecycle, resume, context),
  moteur de workflow (machine à états déterministe, sérialisation, checkpoints), moteur de
  politiques.
- **Déterminisme LLM** : port `LLMProvider`, record/replay (« replay never calls model »),
  `LLMInteractionStore`, validation `model_version`/`parameters`. Solide et bien pensé.
- **Plomberie de connexion (M1)** : résolution de secret sans fuite, abstraction réseau désactivée
  par défaut, adaptateur câblé, doubles déterministes pour les deux chemins. Techniquement
  irréprochable.
- **Vertical Slice adverse F1–F10** : preuve que la gouvernance refuse/borne/escalade les
  comportements dégénérés — mais **avec un agent simulé**.
- **Cadre de valeur** : métriques déterministes contre un benchmark externe.

**Verdict** : le socle *de gouvernance et de plomberie* est solide. Ce n'est pas là qu'est le
problème.

---

## 2. Ce qui reste faible ou incomplet

- **Le raisonnement n'existe pas.** Aucun composant ne transforme une requête en une
  recommandation *raisonnée*. Ce qui en tient lieu est un stub qui renvoie des réponses câblées.
- **Les Conseils sont absents.** `councils/` est un placeholder. Or les Conseils d'Experts
  (délibération multi-tours) et le Conseil Stratégique sont, d'après la documentation même
  (`docs/system/03`, `docs/behavior/04-debate-protocol`), le **cœur cognitif** du produit. Le
  protocole de débat n'est pas implémenté.
- **Les agents sont des placeholders.** `agents/` ne contient aucune exécution d'agent réelle ;
  le seul « AgentRuntime » vivant est le stub de la Slice.
- **La mémoire est partielle.** Le cœur mémoire existe (révision, quarantaine, provenance) mais
  **sans persistance durable ni embeddings** — `search_semantic` retombe sur du lexical. Pour un
  « cerveau », c'est un manque structurant.
- **Construction de prompt / synthèse** : inexistante hors Slice et hors `llm/`. Personne ne
  sait, dans le cœur, *quoi demander* à un modèle ni *comment agréger* plusieurs avis.
- **Départements, création d'agents, apprentissage** : documentés, non construits.

**Verdict** : ce qui manque n'est pas un détail — c'est **la moitié cognitive du système**.

---

## 3. Risques si l'on connecte un vrai LLM maintenant

- **Connecter un modèle à un cerveau vide ne produit aucune valeur.** Un LLM réel derrière
  l'adaptateur actuel répondrait à des prompts que personne ne construit intelligemment, sans
  débat, sans conseil, sans mémoire durable. On obtiendrait un « chatbot gouverné », pas AI-SOS.
- **Coût, latence, non-déterminisme réels** entreraient dans le système **avant** que la logique
  qui les justifie existe — on paierait pour observer un pipeline stub.
- **Fausse impression d'avancement.** « On a branché GPT/Claude » cacherait le fait que le
  produit ne sait toujours pas raisonner. Risque politique et stratégique élevé.
- **Sur-ajustement de l'intégration.** On figerait le contrat provider (déjà à deux étages) autour
  d'un cerveau imaginaire, puis il faudrait le refaire une fois le cerveau réel connu.

---

## 4. Risques si l'on attend trop longtemps

Pour rester impartial, l'inverse a aussi un coût — mais il est **plus faible ici**.

- **Contrats non confrontés au réel.** Le déterminisme record/replay n'a jamais vu un vrai
  modèle ; des surprises (formats, erreurs, latence) restent possibles. *Mais* ces surprises
  toucheraient une couche déjà bien isolée.
- **Effet tunnel cognitif.** Construire le cerveau « dans le vide », sans jamais tester contre un
  vrai modèle, pourrait produire des abstractions élégantes mais irréalistes. À surveiller.
- **Démobilisation.** Un jalon d'intégration « presque fini » qu'on gèle peut être frustrant.

**Mais** : rien de tout cela n'est urgent ni bloquant. Le risque d'attendre est **maîtrisable** ;
le risque de connecter trop tôt est **structurel**.

---

## 5. Ce qui manque au « cerveau » du système

Par ordre d'importance décroissante :

1. **Un agent qui raisonne réellement** : prend une tâche dans son manifeste (least privilege),
   construit une demande, produit une **recommandation argumentée** (jamais une décision) — le
   tout derrière le port `LLMProvider` (donc testable avec les doubles déjà construits).
2. **Le protocole de débat / Conseils d'Experts** : délibération multi-tours, avocat du diable,
   convergence ou escalade. C'est le différenciateur d'AI-SOS.
3. **La synthèse de recommandation** : agréger plusieurs avis d'agents/conseils en une
   recommandation unique soumise au CEO, avec traçabilité.
4. **Le Conseil Stratégique** : activé par le CEO seul, dissous après remise (déjà spécifié).
5. **Une mémoire réellement exploitable** : au minimum durable ; à terme sémantique. Sans mémoire,
   pas d'apprentissage, pas de contexte.
6. **La construction de prompt gouvernée** : ce que le système demande au modèle, borné et audité.

Point clé : **tout cela peut se construire sans un seul appel réseau**, en s'appuyant sur
`StubLLMProvider`, `DeterministicProviderBackend` et record/replay **déjà livrés**. Le cerveau n'a
pas besoin d'un vrai LLM pour être conçu, seulement d'un fournisseur déterministe — que nous avons.

---

## 6. Meilleure orientation pour les 5 à 10 prochaines PR

Une trajectoire « cerveau d'abord », entièrement hors réseau, contre les doubles existants :

1. **Agent Runtime réel (cœur)** — sortir l'exécution d'agent du stub de la Slice vers `agents/` :
   raisonnement borné, recommandation argumentée, derrière `LLMProvider`.
2. **Contrat de délibération d'un agent** — entrée (tâche + contexte mémoire) → sortie
   (recommandation + justification + incertitude).
3. **Conseil d'Experts — protocole de débat** (multi-tours, convergence/désaccord).
4. **Synthèse multi-agents → recommandation unique** (traçable, auditée).
5. **Conseil Stratégique** (activation CEO-only, dissolution après remise).
6. **Mémoire durable** (persistance derrière le port mémoire ; embeddings plus tard).
7. **Construction de prompt gouvernée** (bornée, auditée, sans fuite de secret).
8. **Slice « cerveau »** : rejouer F1–F10 avec un *vrai* raisonnement déterministe, plus un stub.
9–10. **Durcissement** (métriques de valeur sur le vrai raisonnement, adversarial).

Connecter un **vrai** LLM viendrait **après** cette séquence — et serait alors trivial, puisque le
cerveau consommerait déjà le port `LLMProvider`. À ce moment-là, il faudra **fusionner les deux
étages transport+backend** (voir §7) plutôt que d'en rajouter.

---

## 7. Recommandation claire

**Option retenue : phase intermédiaire — suspendre la marche de M1 vers le vrai LLM, et revenir au
cœur agent/cerveau — sans défaire l'existant.**

Concrètement :

- **Suspendre** (ne pas annuler) la progression M1 vers une activation réelle. La plomberie livrée
  est conservée et suffisante ; **arrêter d'en ajouter**.
- **Pivoter** les 5–10 prochaines PR vers le **cerveau** (§6), entièrement hors réseau, contre les
  doubles déterministes déjà construits.
- **Reporter** la connexion d'un vrai fournisseur *après* que le cerveau sache l'utiliser.

### Sur la question « certaines PR étaient-elles prématurées ? » — oui, en partie

Impartialement :

- **#47 (secrets), #48 (transport), #49 (câblage)** : **justifiées**. Contrats nécessaires,
  proprement isolés.
- **#50 (client HTTP déterministe)** : **utile mais en avance** — teste une plomberie sans
  consommateur réel.
- **#51 (contrat backend)** : introduit un **second étage d'abstraction** (`ProviderBackend`)
  au-dessus du transport HTTP. Deux couches font un travail proche, définies **avant** de connaître
  la forme d'un vrai fournisseur : **abstraction spéculative** (risque YAGNI).
- **#52 (backend déterministe)** : **miroir de #50 au second étage** — couverture redondante d'une
  couche elle-même spéculative.

Aucune de ces PR n'est *mauvaise* ou mal faite — la qualité d'exécution est constante. Mais **#51
et #52 ont anticipé un besoin non encore établi** et ont **dupliqué** un motif (double déterministe)
sur deux couches parallèles. Le signal à entendre n'est pas « c'était nul », c'est : **nous avons
commencé à sur-outiller la connexion pendant que le cerveau restait vide.** C'est précisément le
moment de corriger la trajectoire.

### Ce qu'il ne faut PAS faire

- Ne pas connecter un vrai LLM maintenant.
- Ne pas ajouter une troisième couche d'intégration (ni streaming, ni SDK, ni « provider registry »)
  tant que le cerveau ne les réclame pas.
- Ne pas défaire #47→#52 : les garder tels quels, gelés, jusqu'à ce que le cerveau les consomme —
  et, à ce moment, envisager de **collapser transport+backend** en une seule couche.

### En une phrase

> La gouvernance et la plomberie sont prêtes ; le cerveau ne l'est pas. Construire le cerveau
> d'abord — contre les doubles déterministes déjà livrés — puis connecter un vrai LLM *ensuite*.

---

*Avis soumis à la revue du Chief AI Architect et à la décision du CEO. Le CEO reste seul décideur
de l'orientation.*
