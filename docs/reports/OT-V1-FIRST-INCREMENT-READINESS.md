# Operational Target V1 — Audit ciblé et verdict de préparation du premier incrément

> **Statut** : rapport de préparation, remis au CEO ; **aucun code produit n'est modifié par ce rapport**.
> **Date** : 2026-09-05.
> **Nature** : audit ciblé du code existant au regard des tests T02–T06 (premier objectif) et des
> fondations T11 / T25, proposition du **premier incrément de code minimal**, risques de régression
> doctrinale, et **verdict READY / NOT READY**.
> **Références** : [Décision 026](../../DECISIONS.md) ;
> [`docs/strategy/AI-SOS-OPERATIONAL-TARGET-V1.md`](../strategy/AI-SOS-OPERATIONAL-TARGET-V1.md) (cible,
> tests, matrice §11) ; code `product/` à `develop@d65707f` ; `src/aisos/` (référence, inchangé).
> **Règle de ce mandat** : le premier incrément n'est **pas** codé ici.

---

## 1. Objet, périmètre, méthode

Le premier objectif retenu est **« AI-SOS comprend un problème jamais vu, en fait émerger les dimensions,
compose une équipe proportionnée, explore plusieurs options de façon indépendante et rend un rapport de
situation exploitable »** — soit les tests **T02, T03, T04, T05, T06**, adossés aux fondations **T11**
(recommandation décisionnelle) et **T25** (honnêteté des preuves).

Méthode : lecture du code (pas des documents) de chaque composant susceptible de servir ou de bloquer ces
tests ; pour chacun : rôle actuel, ce qui sert la cible, ce qui la bloque, décision **conserver / étendre /
ne pas toucher**, et test qui justifie chaque modification. **Aucun composant n'est retiré pour des raisons
d'élégance** : tout retrait du chemin d'exécution est justifié par un test nommé et se fait **sans
suppression** (les phases 0–18 restent intactes et testées).

---

## 2. Audit ciblé, composant par composant

### 2.1 Phase 1 — `product/app/agents.py` (Analyste, Architecte de solution, Relecteur risques)

| Constat | Preuve | Effet sur la cible |
| --- | --- | --- |
| Chaîne séquentielle **1 → 2 → 3**, chaque agent voit la sortie du précédent | `solution_plans.py:25-31` | Aucune indépendance initiale : l'Architecte raisonne **dans** le cadre de l'Analyste ; le Relecteur critique un plan qu'il n'a pas concurrencé. Bloque **T06** (options réellement différentes) |
| L'Analyste « clarifie et structure » et produit des « zones d'incertitude » **en prose** | `agents.py:66-83` | Les inconnues existent mais ne sont ni structurées, ni comptées, ni distinguées des hypothèses. Bloque **T02** (≥ 3 inconnues explicites, jugeables) |
| L'Architecte produit **« un plan de solution candidat »** (singulier) | `agents.py:95-105` | Une seule option par mission. Bloque **T06**, **T10**, **T13** (l'option nulle n'est jamais offerte) |
| Le Relecteur renvoie `assumptions / risks / expertise_needs` en JSON de trois chaînes | `agents.py:116-129` | `expertise_needs` est la **seule** trace d'une notion de dimension ; elle n'est jamais réutilisée pour composer quoi que ce soit. Sert **T04** comme point d'ancrage |
| Prompts de rôle (`ANALYST_ROLE`, `ARCHITECT_ROLE`, `RISK_ROLE`) : courts, en français, sans system prompt | `agents.py:1-40` | Réutilisables comme **lentilles** d'experts du Tour 0 (angles « analyse », « architecture », « risque ») |

**Décision** : **conserver** intégralement (Phase 1 continue de fonctionner et reste testée) ; **étendre**
en réutilisant les rôles comme lentilles dans le nouveau chemin de cadrage. Justification : T02, T04, T06.

### 2.2 Phase 3 — `product/app/improvement_agents.py` (quatre lentilles d'amélioration)

| Constat | Preuve | Effet sur la cible |
| --- | --- | --- |
| Quatre agents fixes : `ExistingSolutionAnalyst`, `WeaknessReviewer`, `ImprovementArchitect`, `DifferentiationReviewer`, toujours dans le même ordre | `improvement_agents.py:102-214` | Composition **fixe à 4** quelle que soit la solution. Bloque **T05** (équipe différente selon le problème) |
| L'entrée « solution existante » est un **texte saisi** (`ImprovementInput`) | `improvement_agents.py:51-61` | Aucune lecture de dépôt, de docs, de backlog. Bloque **T02** (constats retrouvés seul) et **T12** |
| Le pipeline « améliore » ce qu'on lui donne ; il ne peut pas conclure « ne rien changer » ni contester l'objectif | `improvement_agents.py:149-180` | Bloque **T13**, **T14** |
| `WeaknessReviewer` et `DifferentiationReviewer` sont d'authentiques lentilles critiques | `improvement_agents.py:128-147`, `:182-214` | Réutilisables comme angles « faiblesses » et « différenciation » d'une cellule |

**Décision** : **conserver** ; **étendre** par réutilisation des lentilles. La lecture réelle d'une
solution (capacité *lire*) n'est **pas** dans le premier incrément : T02 sera d'abord évalué sur un dossier
fourni au cadrage (texte + extraits), la lecture autonome venant avec la capacité *chercher* (incrément 2).

### 2.3 Phase 4B-R — `product/app/company_agents.py` et `specialized_companies.py` (fabrique d'entreprises IA, cellules d'experts)

| Constat | Preuve | Effet sur la cible |
| --- | --- | --- |
| `EXPERT_ARCHETYPES` : dix angles décrits en cinq champs (angle, rôle de débat, objections attendues, contribution attendue) | `company_agents.py:58-130` | **Le meilleur actif du dépôt pour la profondeur** : c'est déjà un catalogue d'angles. Sert **T05**, **T06**, **T26** |
| `build_expert_cells` **stampe les 10 archétypes sur chaque spécialité, sans appel LLM** ; `EXPERTS_PER_SPECIALTY = len(EXPERT_ARCHETYPES)` est un invariant testé | `company_agents.py:277-300`, `:131` | Les « experts » n'ont ni contexte isolé, ni position, ni révision : ils ne satisfont **aucune** des quatre propriétés d'un expert (Décision 026 §4). Bloque **T05** (10 experts sur un problème courant) et **T26** |
| `DebateProtocolArchitect` génère un **texte** de protocole de débat ; rien ne l'exécute | `company_agents.py:303-338` | Le débat est décrit, jamais tenu. Bloque **T06**, **T07** |
| `generate_specialized_company` : 4 appels LLM séquentiels + expansion déterministe | `specialized_companies.py:115-192` | Coût connu (4 appels) ; aucun appel « par expert » |

**Décision** : **conserver** la fabrique 4B-R telle quelle (les tests d'invariant « 10 par spécialité »
restent verts pour cette phase) ; **réutiliser `EXPERT_ARCHETYPES` comme catalogue ouvert** dans le
résolveur d'équipe du nouveau chemin ; **ne pas appeler `build_expert_cells`** depuis ce nouveau chemin.
Justification : T05 et T26 exigent une profondeur découverte, pas un quota ; la Décision 026 §3 interdit
aussi bien « 10 systématique » que « 3 systématique ».

### 2.4 Phase 5 — `product/app/deliverable_agents.py` (planificateur, synthétiseur de cellules, producteur, relecteur qualité)

| Constat | Preuve | Effet sur la cible |
| --- | --- | --- |
| `ExpertCellSynthesizer` : **« pas un appel par expert »**, une synthèse des cellules **en un seul appel** | `deliverable_agents.py:118-135` | Plusieurs « voix » générées par un seul contexte : sorties corrélées. Contraire à la règle « un expert = un contexte isolé au Tour 0 ». Bloque **T06** |
| `QualityGovernanceReviewer` relit le contenu **dans la même chaîne**, sans autorité de refus ; ses sorties sont des notes pour le CEO | `deliverable_agents.py:159-189` | Porte qualité **non indépendante** au sens de `policies/09`. Bloque **T11** |

**Décision** : **conserver** (Phase 5 reste intacte) ; **ne pas réutiliser** le synthétiseur mono-appel
pour le Tour 0 (T06) ; **réutiliser le prompt** du relecteur qualité comme base d'une porte qualité tenue
par une instance distincte de la synthèse (T11), dans un incrément ultérieur.

### 2.5 Client LLM — `product/app/llm.py`, `product/app/config.py`

| Constat | Preuve | Effet sur la cible |
| --- | --- | --- |
| `max_tokens` **global = 256** | `config.py:24`, `llm.py:37` | Aucune sortie en 14 champs, aucun rapport de situation avec citations ne tient en 256 tokens. Bloque **T02**, **T11** |
| Pas de **system prompt** (tout est concaténé dans un message utilisateur) | `llm.py:35-39` | Le rôle, les règles d'honnêteté (T25) et le format de preuve ne peuvent pas être séparés du contenu |
| Un nouveau client Anthropic **par appel** ; pas de timeout, pas de retry | `llm.py:34` | Acceptable pour V1 (volume faible) ; à surveiller quand une mission fait 10–60 appels |
| `message.usage` **jeté** ; seul le texte est retourné | `llm.py:40-45` | Aucun coût ni tokens journalisés. Bloque **T24** et empêche de mesurer l'expérience de profondeur |
| Interface `LLMClient.complete(prompt) -> str` | `llm.py:14-20` | Interface minimale, **partout** utilisée (32 agents) : l'étendre sans la casser est possible par un **nouveau** protocole optionnel |

**Décision** : **étendre sans rupture** — ajouter un protocole `complete_structured(system, prompt,
max_tokens) -> (text, usage)` (nom indicatif) implémenté par `AnthropicLLMClient` et par
`ObservedLLMClient`, en **conservant** `complete(prompt)` pour les phases 1–18. Justification : T02, T11,
T24, T25.

### 2.6 Parsing — `product/app/agent_utils.py`

`parse_json_fields(raw, fields) -> dict[str, str] | None` (`agent_utils.py:45`) n'accepte que des
**chaînes plates** ; les listes (inconnues, options, désaccords) et les objets (preuve = énoncé + source +
fiabilité) ne sont pas représentables. Il fonctionne bien pour le format « 1 prompt → 1 JSON plat ».

**Décision** : **conserver** ; **ajouter** une validation Pydantic des sorties structurées du nouveau
chemin (schémas de rapport de situation, de fiche d'expert, d'exposé, de carte). Justification : T02
(inconnues comptables), T06 (options distinctes), T25 (preuves typées).

### 2.7 Persistance — `product/app/db.py`

17 tables, `create_all`, pas de migration. Aucune table ne représente une **mission**, un **cadrage**, une
**position d'expert** ni un **journal de délibération**. `LLMCallLog` (`db.py:537-560`) journalise phase,
agent, previews, statut, durée — **ni tokens ni coût**. `Project` / `ProjectLink` (`db.py:495-535`) offrent
un conteneur générique (`entity_type`, `entity_id`) qui peut rattacher un nouvel objet sans modifier les
tables existantes.

**Décision** : **ajouter** (jamais modifier) : une table de mission de cadrage et une table de journal
(exposés du Tour 0, carte, rapport) ; **ajouter** deux colonnes nullable à `LLMCallLog` (tokens
entrée/sortie, coût estimé). Justification : T02, T05 (journal de composition), T06 (exposés isolés
horodatés), T24.

### 2.8 Observabilité — `product/app/observability.py`

`ObservedLLMClient` (`observability.py:40-103`) et `observed(...)` (`:104`) journalisent chaque appel par
agent ; `log_product_event` (`:123`) journalise les événements. C'est **exactement** le mécanisme qui
permettra de **prouver** l'isolement du Tour 0 (un appel par expert, horodaté, sans que le prompt d'un
expert contienne l'exposé d'un autre) et de compter les appels par mission.

**Décision** : **réutiliser tel quel** ; étendre uniquement pour porter tokens/coût (2.5). Les tests
d'observabilité existants (« les lectures ne polluent pas ») restent intacts.

### 2.9 Approval Engine — endpoints `/approve`, `/request-revision`, services `set_*_status`

Toute validation est une **action explicite du CEO** sur un artefact persisté
(`main.py:439-455` pour Phase 1 ; même motif aux lignes 497, 573, 651 ; Phases 11–13 pour lots et items).
Aucune exécution n'est déclenchée par une approbation. Ce motif est **conforme** à l'article X et à la
frontière « raisonner / décider ».

**Décision** : **réutiliser le motif** : le rapport de situation du nouveau chemin naît en statut
`candidate` et n'acquiert de statut `approved` que par action CEO ; **aucun classifieur automatique de
délégation** dans le premier incrément (T16 viendra après). Justification : ne pas régresser l'invariant
« AI-SOS ne valide rien seul ».

### 2.10 Espace projet — `product/app/projects.py`, dashboard, export, snapshot (Phases 14–18)

Le `Project` accepte des liens vers tout `entity_type` connu (`projects.py:173-201`) ; dashboard, export
Markdown et snapshot sont déterministes, sans LLM, testés avec un client qui lève s'il est appelé.

**Décision** : **réutiliser** comme conteneur : une mission de cadrage devient un `entity_type`
supplémentaire liable à un projet ; l'export Markdown existant sert de modèle de rendu au rapport de
situation. Aucun changement des invariants « zéro LLM » des phases 14–18.

### 2.11 `src/aisos/` — modules réutilisables (référence, **inchangé**)

`product/pyproject.toml` déclare explicitement le produit « *isolated from src/aisos (reference spec)* » ;
`src/aisos/policies/engine.py` importe `aisos.domain`, `aisos.schemas` (`engine.py:18-27`). Importer le
noyau depuis `product/` briserait cette isolation et est interdit par les contraintes du mandat.

| Module | Ce qui est réutilisable | Comment |
| --- | --- | --- |
| `policies/engine.py::DefaultPolicyEngine` (`:88-303`) | Les **quatre classes**, la **préséance** complexité / risque / incertitude, le défaut conservateur, l'interdiction de déléguer structurante/critique | **Comme spécification** : porter dans `product/` un classifieur minimal à quatre classes (une centaine de lignes), avec les mêmes règles, testé contre les mêmes cas — pas un import |
| `policies/engine.py::quality_gate` (`:304`) | Les critères d'une porte qualité | Spécification de la porte indépendante (T11, incrément ultérieur) |
| `security/authorization.py::DefaultManifestEnforcer` | Refus par défaut, outils autorisés, egress | Spécification pour V1.5 (T19) — **rien à porter maintenant** |
| `audit/hashing.py` | Chaînage d'empreintes | Optionnel, plus tard, pour le journal de délibération |
| `llm/replay.py` | Record / replay d'appels | Idée réutilisable pour rejouer une délibération en test ; le produit a déjà `FakeLLMClient` |

**Décision** : **ne pas toucher** `src/aisos/` ; **porter par spécification** le seul classifieur à quatre
classes, dans un incrément ultérieur (T16). Le premier incrément se contente d'**enregistrer** une classe
déclarée au cadrage (CEO) ou, à défaut, une classe **« importante provisoire / non déterminée »** — jamais une
« importante » définitive par défaut — que le cadrage **peut et doit escalader** selon les risques découverts ;
sans délégation.

### 2.12 Invariant « aucune règle ne nomme un projet » (T23)

Vérifié à `d65707f` : **0 occurrence** de tout banc d'essai dans `product/` (recherche insensible à la
casse). Cet invariant existe de fait ; il doit devenir un **test automatisé** dès le premier incrément.

---

## 3. Bilan : réutilisable / à étendre / non réutilisé (et pourquoi)

**Réutilisé tel quel** : `EXPERT_ARCHETYPES` (catalogue d'angles) ; prompts de rôle des Phases 1, 3, 5
(lentilles) ; `ObservedLLMClient` / `observed` / `log_product_event` ; motif Approval Engine
(`candidate` → action CEO) ; `Project` / `ProjectLink` ; rendu Markdown déterministe (Phase 16) ;
`FakeLLMClient` et le motif « client qui lève » des tests ; `parse_json_fields` pour les phases existantes.

**Étendu sans rupture** : client LLM (system prompt, `max_tokens` par appel, usage) ; `LLMCallLog`
(tokens, coût) ; schémas Pydantic (sorties structurées).

**Non réutilisé par le nouveau chemin, mais conservé et testé** (justification par test) :
`build_expert_cells` (T05/T26 : profondeur découverte, pas quota) ; `ExpertCellSynthesizer` mono-appel
(T06 : indépendance initiale) ; `DebateProtocolArchitect` (T06 : un protocole se tient, il ne se décrit
pas) ; chaînes séquentielles 1→2→3 comme **mode d'exploration** (T06 : options non corrélées).

**Rien n'est supprimé.**

---

## 4. Proposition du premier incrément de code minimal

**Nom** : *Cadrage + Exploration indépendante + Cartographie + Rapport de situation*
(**incrément 1** ; **non codé dans ce mandat**).

**Tests visés** : **T02** (partiel : inconnues explicites sur dossier fourni), **T04**, **T05**, **T06**
(partiel : ≥ 3 options réellement différentes au Tour 0, désaccords conservés — sans tours de critique),
**T10** (partiel : matrice options × critères remplie à partir des exposés, sans jugement du facilitateur), **T13/T14** (champs présents), **T23** (test automatisé),
**T24** (partiel : tokens et coût journalisés), **T25** (format de preuve, sans recherche externe),
**T26** (journal de composition). **Hors périmètre** : T03/T08 (recherche externe = incrément 2),
T07/T09 (tours C-D-F = incrément 3), T11 complet (porte indépendante = incrément 3), T16 (classifieur).

**Ce qu'il fait, dans l'ordre (une mission) :**

1. **Cadrage** — entrée unique (type : problème / idée / objectif / solution existante ; texte ; dossier
   optionnel ; classe déclarée par le CEO ou, à défaut, **« importante provisoire / non déterminée »** —
   jamais « importante » définitive par défaut : le cadrage **peut et doit l'escalader** selon les risques
   découverts (irréversibilité, coût d'erreur, incertitude critique), et l'escalade est journalisée ;
   plafond d'appels et d'euros — **décision CEO** : plafond dur **2,00 € par mission et 12 appels LLM**).
   Un appel LLM produit une **sortie structurée** : problème compris, **contestation éventuelle de la
   demande** (T14), **dimensions émergentes** avec criticité présumée et inconnues par dimension (T04),
   **inconnues globales** (T02).
2. **Composition** — règles codées : dimensions → cellules (largeur ≤ 7, `policies/06`) ; par cellule,
   angles choisis dans le catalogue ouvert (`EXPERT_ARCHETYPES` + angles proposés par le cadrage) selon
   la criticité présumée et la classe. La composition conceptuelle reste : *dimensions pertinentes →
   profondeur nécessaire découverte → contrainte par le budget CEO*. Pour contenir le coût du prototype,
   l'incrément applique une **borne expérimentale temporaire de 3 angles par cellule au Tour 0 — non
   doctrinale, paramétrable, destinée à être remplacée par les résultats du protocole §10 du document
   canonique** ; elle n'est **ni un défaut ni un quota** (une cellule peut n'avoir qu'un angle ; aucune
   valeur n'est présentée comme « le nombre d'experts »), et l'approfondissement au-delà relève des
   incréments suivants (tours C–F). **Journal de composition** (dimension → angles → justification ; angle
   contraire obligatoire si une préférence CEO est déclarée) (T05, T26). La proportionnalité est testée
   par T05 (un problème courant mobilise ≤ 2 experts), sans nombre fixe.
3. **Exploration indépendante (Tour 0)** — **un appel isolé par expert**, même dossier de cadrage, fiche
   d'expert (domaine, angle, a priori, objections) ; sortie structurée : position, justifications,
   hypothèses, risques, ce qu'il faudrait savoir, **preuves** au format « énoncé + source + fiabilité »
   (T25 : une preuve sans source est marquée « non sourcée », jamais inventée). Chaque appel est
   journalisé par `observed(...)` avec le nom de l'expert (T06 : preuve d'isolement).
4. **Cartographie** — sans pouvoir d'orientation. Opérations **réellement déterministes**, codées :
   comptage des soutiens, indice de divergence, bornes et budget, journalisation, regroupement par
   identifiants connus, matrice options × critères communs (T10). Opérations **sémantiques** (deux options
   sont-elles équivalentes ? quelle est la nature d'un désaccord ? deux hypothèses sont-elles la même ?)
   réalisées en deux temps : (i) **auto-qualification par les experts** — une fois le Tour 0 clos et toutes
   les positions horodatées, chaque expert reçoit la liste anonymisée des autres positions et qualifie la
   sienne (identique / variante / différente) et type ses objections (appel court, N appels) ; (ii) pour ce
   qui reste ambigu, un **appel de greffier** au **schéma fermé** (options, hypothèses, désaccords typés —
   **aucun champ** de préférence, de classement ni de recommandation), chaque regroupement étant attribué,
   motivé et **contestable** par l'expert concerné dans les incréments suivants (phase C). Les exposés bruts
   restent joints. **Aucun « résumé » libre** : le facilitateur structure, il n'oriente pas.
5. **Rapport de situation** — objet persisté en statut `candidate`, rendu Markdown déterministe (modèle
   Phase 16), 14 champs pré-remplis là où le Tour 0 le permet (recommandation = « à délibérer » ou
   « rechercher / tester d'abord » si l'information manque — T13), **désaccords conservés**, coût et
   nombre d'appels affichés. Le CEO l'approuve, demande une révision, ou le rejette (motif Approval
   Engine) ; **rien n'est exécuté**.

**Surface de code (ordre de grandeur, indicatif)** : un module de cadrage, un module de composition, un
module d'exploration, un module de cartographie, un module de rapport ; 2 tables nouvelles + 2 colonnes
nullable ; 3 à 4 endpoints (`POST` créer une mission de cadrage, `GET` mission, `POST` approuver / demander
révision) ; une section Streamlit via le client HTTP ; **aucune** modification des phases 0–18 hors le
client LLM étendu sans rupture. Appels LLM par mission : **1 (cadrage) + N (Tour 0, N = experts) + N (auto-qualification, courts) + 0–1
(greffier)** ; coût attendu **0,10–2 €** avec `max_tokens` 4–8 k par appel (les appels courts en moins).

**Tests du code (sans réseau, sans clé)** : faux client structuré ; isolement du Tour 0 (aucun prompt
d'expert ne contient un exposé d'un autre ; N appels journalisés avec N noms distincts) ; deux cadrages
différents → deux compositions différentes ; problème courant → ≤ 2 experts ; contestation présente quand
le dossier contient une hypothèse fausse injectée ; ≥ 3 inconnues comptées ; options distinctes comptées ;
preuve sans source marquée « non sourcée » ; tokens et coût présents dans `LLMCallLog` ; **0 occurrence**
d'un nom de banc d'essai dans `product/` ; phases 0–18 : suite existante (335) inchangée et verte ;
phases 14–18 : toujours **zéro LLM**.

**Ce que l'incrément ne fait pas** : pas de recherche externe, pas de tours de critique, pas de steelman,
pas de porte qualité indépendante, pas de classification automatique, pas de délégation, pas d'exécution,
pas de lecture autonome de dépôt, pas de multi-LLM, pas de nouvelle table de gouvernance documentaire, pas
de nouvel onglet au-delà d'une section.

---

## 5. Tests qui doivent s'améliorer (mesurables avant / après)

| Test | Avant (d65707f) | Après incrément 1 — attendu | Comment on le mesure |
| --- | --- | --- | --- |
| T02 | 0 inconnue structurée ; prose | ≥ 3 inconnues pertinentes sur un dossier fourni ; constats majeurs cités | Jugement CEO sur un problème **scellé** ; comptage des inconnues |
| T04 | 0 dimension calculée | 4/4 dimensions d'un problème ambigu, sans liste imposée | Problème scellé mêlant 4 dimensions non nommées |
| T05 | Composition fixe 3 / 4 / 10 | Deux problèmes → deux équipes ; courant → ≤ 2 experts | Journal de composition de deux missions |
| T06 | 1 option ; 0 désaccord | ≥ 3 options réellement différentes ; ≥ 1 désaccord conservé | Juge indépendant sur la carte ; comptage |
| T10 | 1 stratégie | Matrice options × critères communs | Présence et cohérence de la matrice |
| T13 / T14 | Impossible | Champs « contestation » et « ne rien construire / rechercher d'abord » présents et utilisés quand le dossier l'exige | Cas injectés |
| T23 | Invariant de fait, non testé | Test automatisé « 0 référence à un banc d'essai » | CI produit |
| T24 | Ni tokens ni coût | Tokens et coût par appel et par mission | `LLMCallLog` |
| T25 | Pas de format de preuve | Preuve = énoncé + source + fiabilité ; « non sourcée » explicite | Échantillon de 20 preuves |
| T26 | Aucun journal | Justification par dimension ; angle contraire si préférence déclarée | Journal de composition |

**Non améliorés volontairement par cet incrément** : T03, T07, T08, T09, T11 (complet), T12 (jugement
item par item sur un backlog réellement lu), T15–T22. Si, après exécution sur les problèmes scellés, **aucun** des tests du tableau ne
s'améliore de façon observable, l'incrément est un échec et l'approche est réévaluée avant l'incrément 2
(critère d'arrêt, Décision 026 §8).

---

## 6. Risques de régression doctrinale

| # | Risque | Où il se matérialiserait | Garde-fou |
| --- | --- | --- | --- |
| R1 | **Le facilitateur oriente le résultat** : un regroupement sémantique ou un « résumé » glisse vers une recommandation implicite | Étape 4 | Opérations déterministes codées ; opérations sémantiques déléguées aux experts (auto-qualification) puis à un greffier au **schéma fermé** sans champ de préférence, de classement ni de recommandation ; regroupements attribués, motivés, contestables ; exposés bruts joints ; test : le schéma de la carte ne contient aucun champ de recommandation ; aucun résumé libre |
| R2 | **Retour du quota** : un nombre d'experts par défaut réapparaît (10 ou 3), y compris via la borne de coût de l'incrément | Étape 2 | Profondeur fonction de la criticité et de la classe ; la borne de 3 est déclarée **expérimentale, temporaire, non doctrinale**, paramétrée et jamais présentée comme défaut ; test « courant → ≤ 2 » (T05) ; expérience §10 avant tout défaut |
| R3 | **Faux experts** : les appels du Tour 0 partagent un contexte (un seul appel multi-voix « pour économiser ») | Étape 3 | Test d'isolement (N appels, N noms, aucun exposé cité par un autre) ; règle 026 §4 |
| R4 | **Contestation cosmétique** : le champ « contestation » est toujours vide ou toujours rempli | Étape 1 | Cas injectés dans les tests (hypothèse fausse → contestation ; dossier sain → aucune) ; jugement CEO sur problème scellé |
| R5 | **Preuves fabriquées** : des « sources » plausibles sans accès externe | Étape 3 | Sans capacité *chercher*, toute source est marquée « non vérifiée / mémoire du modèle » ; T25 audit d'échantillon ; system prompt d'honnêteté |
| R6 | **L'artefact devient une décision** : le rapport `candidate` est traité comme validé, ou déclenche quelque chose | Étape 5 | Motif Approval Engine ; test « approuver ne déclenche aucun appel ni action » ; article X |
| R7 | **Dérive vers l'exécution** : tentation d'ajouter *lire un dépôt* ou *coder* « puisque le cadrage existe » | Portée | Interdits explicites du mandat ; incréments justifiés par tests nommés ; 026 §7 (légitimité ≠ autorisation) |
| R8 | **Règle nommant un banc d'essai** : un prompt ou un test cite le projet servant de banc | Tout `product/` | Test automatisé T23 en CI |
| R9 | **Régression des phases 0–18** : extension du client LLM ou des schémas qui casse l'existant | Client, DB | `complete(prompt)` conservé ; colonnes nullable ; suite des 335 tests inchangée |
| R10 | **Coût non borné** : `max_tokens` 8 k × N experts sans plafond | Étape 3 | Plafond dur fixé par le CEO : **2,00 €/mission et 12 appels** ; `max_tokens` configurable **par type d'appel** (cadrage, exposé, auto-qualification, greffier) ; **estimation avant chaque appel** et refus/arrêt si l'appel peut dépasser le plafond ; tokens et coût journalisés ; arrêt dur avec rapport partiel et incertitudes déclarées (T24 partiel) |
| R11 | **Nouvelle couche documentaire** : multiplication de documents de méthode | Dépôt | 026 §8 : Décision, document canonique, protocole, un rapport par porte — rien d'autre |

---

## 7. Verdict

### **NOT READY — décision / information manquante**

La proposition d'incrément est **cohérente, minimale et entièrement justifiée par des tests nommés** ; les
composants réutilisables sont identifiés ; aucune modification de `src/aisos/` n'est nécessaire ; aucune
interdiction du mandat n'est franchie. **Mais trois éléments, qui ne relèvent pas de Claude, manquent
avant de coder :**

1. **Ratification de la Décision 026.** Tant que la Pull Request qui la porte n'est pas fusionnée dans
   `develop`, le droit de contestation (T14), l'axe profondeur (T05/T26), la légitimité de la recherche
   externe (incrément 2) et la notion de capacité d'action n'ont **aucune autorité doctrinale** ; coder
   l'incrément 1 reviendrait à implémenter une doctrine non ratifiée — exactement la dérive que le
   réalignement a dénoncée pour `product/` PHASE 0.
2. **Trois problèmes scellés, jamais vus.** Les tests T02, T04, T05, T06 n'ont de sens que sur des
   problèmes **que ni les prompts, ni les tests du code, ni Claude n'ont vus**. Claude a lu l'intégralité
   du dépôt et des bancs d'essai : **il ne peut pas être l'auteur des problèmes scellés.** Il faut que le
   CEO (ou Orion) rédige et scelle hors dépôt **au moins trois problèmes** (un courant, un importante, un
   structurant ; natures différentes), avec pour chacun les constats majeurs attendus — la grille de
   jugement de T02 et T04.
3. ~~**Couloir de budget du premier incrément.**~~ **Résolu par décision CEO (2026-09-05)** : plafond dur
   **2,00 € par mission et 12 appels LLM** ; `max_tokens` **configurable par type d'appel** ; **estimation
   avant appel** et refus ou arrêt si l'appel peut dépasser le plafond ; tokens et coût journalisés. Le CEO a
   également fixé la **classe initiale** : *importante provisoire / non déterminée*, jamais « importante »
   définitive par défaut, à escalader par le cadrage selon les risques découverts. Conséquence
   expérimentale (non doctrinale) : avec 1 appel de cadrage + N exposés + N auto-qualifications + 0–1
   greffier, le plafond de 12 appels borne l'incrément 1 à **N ≤ 5 experts par mission** ; cette borne découle
   du budget, pas d'une règle de profondeur, et sera revue avec le protocole §10.

**Ce qui devient READY dès que les deux éléments restants existent** (ratification par fusion ; trois
problèmes scellés) : l'incrément 1 tel que décrit au §4, sur la
branche produit habituelle, en PR vers `develop`, avec ARP, sans fusion sans validation CEO.

**Ce qui n'est pas demandé au CEO** : aucun choix technique (le client, les tables, les schémas relèvent de
l'incrément), aucun nombre d'experts (interdit avant l'expérience), aucune décision sur MaestroSala (banc
d'essai, pas backlog).
