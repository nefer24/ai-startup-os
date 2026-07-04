# orchestrator

Interfaces de l'Orchestrateur, le superviseur qui coordonne le traitement d'une
requête. L'Orchestrateur peut proposer l'activation du Conseil Stratégique mais
ne l'active jamais lui-même. Aucune logique métier n'est implémentée ici.

## Contenu

Squelette uniquement :

- Interfaces de supervision du cycle de traitement d'une requête.
- Contrats de proposition (recommandation) d'activation du Conseil Stratégique.
- Points d'intégration vers le workflow, les politiques et les agents.

## Traçabilité

Chaque élément est traçable vers une spécification existante :

- [`../../../docs/components/01-orchestrator.md`](../../../docs/components/01-orchestrator.md)
- [`../../../docs/runtime/02-main-request-workflow.md`](../../../docs/runtime/02-main-request-workflow.md)

## Périmètre gelé — contrats de référence (E2 clôturé)

L'étape **E2 (composition gouvernée)** est officiellement close. Les contrats produits par E2 sont
**gelés** et constituent désormais la **fondation de composition** d'AI-SOS — des références stables
sur lesquelles E3 (évolution gouvernée des capacités) s'appuiera sans les rouvrir :

- **Contrat de capacité** (`capability.py`) : une capacité **EST** un `DeliberationPort` doté d'un
  `descriptor` ; elle recommande, ne décide ni ne gouverne jamais. Immuable, `@runtime_checkable`,
  n'importe pas `aisos.agents` (prouvé par `tests/unit/test_capability_contract.py`).
- **Registre de capacités** (`registry.py`) : catalogue **passif**, en lecture seule, déterministe
  (ordre d'insertion), identifiants uniques. Aucune API de mutation/sélection ; retours immuables
  (`tests/unit/test_capability_registry.py`).
- **Composition déterministe** (`composition.py`) : fonction **pure** — problème + registre ⇒
  organisation ; sélectionne uniquement des capacités présentes ; n'importe ni `aisos.audit`/
  `aisos.events`, ni `aisos.agents` (`tests/unit/test_deterministic_composition.py`).
- **Instanciation gouvernée** (`instantiation.py`) : instancie une organisation **connue** sous
  **politique CEO pré-approuvée** et **avec audit** ; refus déterministe sinon ; **n'exécute pas**
  les capacités ; réutilise les primitives existantes (`tests/unit/test_governed_instantiation.py`).

**Double frontière figée** : l'**instanciation déléguée** (sous politique pré-approuvée) appartient
à l'orchestrateur (E2.4) ; la **création gouvernée** d'une capacité (décision CEO) appartient à E3.

**Toute évolution future de ces contrats doit respecter cette fondation de référence et ne peut être
réalisée que par une décision explicite du CEO.** Voir
[`../../../docs/reports/E2-COMPOSITION-CLOSURE.md`](../../../docs/reports/E2-COMPOSITION-CLOSURE.md).

## Périmètre gelé — contrats de référence (E3 clôturé)

L'étape **E3 (évolution gouvernée des capacités)** est officiellement close. Les contrats produits
par E3 sont **gelés** et constituent la **fondation d'évolution** d'AI-SOS — des références stables
sur lesquelles E4 (mémoire) s'appuiera sans les rouvrir :

- **Création gouvernée** (`creation.py`) : le **CEO seul** inscrit une nouvelle capacité conforme au
  contrat E2.1, **sous audit** ; refus déterministe hors canal CEO ; le registre n'est jamais muté
  en place (`tests/unit/test_governed_capability_creation.py`).
- **Dépréciation gouvernée** (`deprecation.py`) : le CEO retire une capacité de la disponibilité
  opérationnelle, **sans la détruire** ; l'existence historique est préservée ; audité
  (`tests/unit/test_governed_capability_deprecation.py`).
- **Catalogue vivant** (`catalog.py`) : `CatalogState` distingue **historique** (append-only),
  **actif** (opérationnel) et **transitions** (journal auditable) ; `GovernedCatalog` réutilise la
  création et la dépréciation ; déterministe, jamais muté en place, surface de lecture E2 stable
  (`tests/unit/test_governed_catalog_evolution.py`).
- **Conseil Stratégique consultatif** (`strategic_council.py`) : organe **exclusivement composé
  d'agents IA** (cerveau gelé, consulté via port injecté) qui **recommande** (créer / déprécier / ne
  rien changer) ; **ne décide, n'écrit, ne gouverne, ne s'auto-active jamais**
  (`tests/unit/test_strategic_council.py`).

**Frontière recommandation / décision figée** : le Conseil **recommande** ; le **CEO décide** (via
les gestes gouvernés). Le catalogue n'évolue que par ce canal gouverné, sous acte CEO audité.

**Toute évolution future de ces contrats doit respecter cette fondation de référence et ne peut être
réalisée que par une décision explicite du CEO.** Voir
[`../../../docs/reports/E3-CAPABILITY-EVOLUTION-CLOSURE.md`](../../../docs/reports/E3-CAPABILITY-EVOLUTION-CLOSURE.md).

## Invariant de gouvernance

L'Orchestrateur recommande, il ne décide pas : l'activation du Conseil
Stratégique relève de la CEO, seule autorité humaine et seul décideur. Toute
action reste bornée par les politiques pré-approuvées.

> Aucune logique métier ; uniquement le squelette conforme aux spécifications.
