# Unit Testing

> Tests unitaires d'AI-SOS : valider le cœur/domain et le moteur de politiques sans aucune I/O, de façon parfaitement déterministe — chaque règle de gouvernance porte au moins un test qui la prouve.

Ce domaine est la base de la pyramide de validation ([`./01-quality-overview.md`](./01-quality-overview.md)). Il opérationnalise la couche `unit` de la stratégie de tests ([`../engineering/05-testing-strategy.md`](../engineering/05-testing-strategy.md)) sur les modules du cœur — `policies` et `core/domain` — tels que délimités par les frontières de modules ([`../engineering/03-module-boundaries.md`](../engineering/03-module-boundaries.md)). Aucun nouveau choix technologique : pytest, pytest-asyncio, coverage.py, faux `LLMProvider` déterministe et horloge injectable sont déjà posés en Phase 6.

Les tests unitaires portent le marqueur pytest `unit` ; ceux qui prouvent un invariant portent en plus le marqueur `governance`, orthogonal à la couche et exécuté en étape dédiée et bloquante en CI ([`../engineering/06-ci-cd-strategy.md`](../engineering/06-ci-cd-strategy.md)). Le dossier `tests/` est le miroir de `src/aisos/`, ce qui rend visible qu'un module du cœur sans test unitaire associé est une lacune repérable par construction.

## Objectifs

- **Valider le cœur sans I/O.** Le domaine (`core/domain`) et le **moteur de politiques** (`policies`) sont testés sans base, sans réseau, sans LLM réel. Ces modules ne connaissent ni LangGraph ni Postgres ([`../engineering/03-module-boundaries.md`](../engineering/03-module-boundaries.md)) : ils sont testables en pure isolation, condition d'une suite rapide et stable.
- **Garantir le déterminisme.** Toute source de non-détermination est neutralisée : le faux `LLMProvider` scénarise les réponses sans appel réseau, l'horloge est injectée, les seeds sont fixés. Un même test produit toujours le même verdict.
- **Prouver les invariants au plus tôt.** Les invariants exprimables sans I/O — classification, préséance, défaut conservateur, quality gate, éligibilité de politique — sont prouvés dès la couche unitaire, avant même l'intégration. Un invariant testable ici mais non testé est un défaut bloquant.

### Périmètre et exclusions

Sont **inclus** dans la couche unitaire : le moteur de politiques (`Classifier`, `QualityGate`, `PolicyEngine`), les entités et types du domaine, les bornes détenues par `common`. Sont **exclus** et relèvent d'autres domaines : la persistance et les contraintes SQL ([`./03-integration-testing.md`](./03-integration-testing.md), [`../database/10-database-testing.md`](../database/10-database-testing.md)), les chemins de graphe LangGraph ([`./04-runtime-validation.md`](./04-runtime-validation.md)), les endpoints authentifiés ([`./08-security-testing.md`](./08-security-testing.md)). Cette séparation découle directement de la règle de dépendance : le cœur n'important aucun framework, il se teste seul ([`../engineering/03-module-boundaries.md`](../engineering/03-module-boundaries.md)).

## Scénarios

Cas centraux du moteur de politiques :

- **Classification (4 classes)** : courante / importante / structurante / critique, dérivées des axes complexité / risque / incertitude (politiques 01–03).
- **Préséance inter-axes** : l'axe le plus contraignant l'emporte ; jamais de moyenne ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)).
- **Défaut conservateur** : à niveau ambigu, la classe **monte** et le routage va au CEO ; le doute ne descend jamais la classe.
- **Quality gate** : critères et seuils de confiance par classe ([`../policies/09-quality-gate-policy.md`](../policies/09-quality-gate-policy.md)) ; une recommandation sous le seuil ne franchit pas la garde.
- **Éligibilité de politique pré-approuvée** : une décision courante peut être éligible à une politique référencée (référence + version) ([`../policies/08-preapproved-policy.md`](../policies/08-preapproved-policy.md)).
- **Structurante / critique jamais déléguées** : ces classes ne sont **jamais** éligibles à la délégation, quel que soit le contexte.
- **Entités du domaine** : construction, validation et invariants internes des entités (demande, recommandation, classe, verdict de gate) ; les DTO franchissant une frontière sont immuables.

Invariants d'entités vérifiés sans I/O :

| Entité | Invariant vérifié | Violation attendue |
| --- | --- | --- |
| Décision | `validator_type` ∈ {`ceo`, `policy`} ; jamais `agent` | Construction rejetée |
| Décision structurante/critique | `validator_type` ≠ `policy` | Construction rejetée |
| Recommandation | Options documentées avant présentation | Verdict de gate négatif |
| Verdict de classe | Immuable une fois produit | Mutation impossible (DTO gelé) |
| Éligibilité de politique | Référence + version présentes | Éligibilité refusée |

Table des cas attendus (au moins un test par ligne) :

| Cas | Entrée | Sortie attendue |
| --- | --- | --- |
| Décision douteuse | Axes ambigus, incertitude non bornée | Classe montée → route CEO |
| Préséance | Un axe critique, deux axes faibles | Classe = celle de l'axe le plus contraignant |
| Décision structurante | Axe structurant sur un seul critère | Jamais déléguée ; validation CEO obligatoire |
| Décision courante éligible | Axes faibles, politique référencée existante | Délégation autorisée (référence + version) |
| Recommandation incomplète | Options non documentées | Quality gate non franchi → renvoi en délibération |
| Confiance basse hors exception | Confiance sous le seuil, incertitude réductible | Gate non franchi |
| Tentative de délégation critique | Classe critique + éligibilité demandée | Refus au niveau du moteur de politiques |

Extrait illustratif — une décision douteuse est routée vers le CEO (défaut conservateur) :

```python
import pytest

@pytest.mark.unit
@pytest.mark.governance
def test_ambiguous_decision_routes_to_ceo(policy_engine):
    verdict = policy_engine.classify(
        complexity="ambiguous",
        risk="moderate",
        uncertainty="unbounded",   # incertitude non réductible
    )
    # Le doute fait MONTER la classe et route vers le CEO ; jamais de délégation.
    assert verdict.route == "ceo_validation"
    assert verdict.delegable is False
```

## Critères de réussite

- **Chaque règle du Policy Engine a un test** : classification, préséance, défaut conservateur, quality gate et éligibilité de politique sont chacun couverts par au moins un cas nominal et un cas limite.
- **Les branches critiques sont couvertes** : les chemins de délégation (éligible / non éligible) et d'escalade (montée de classe, route CEO) sont exercés explicitement, pas seulement les cas heureux.
- **Aucun appel réseau réel** : la suite unitaire n'atteint ni base, ni LLM, ni service tiers ; un test qui toucherait le réseau est un défaut de conception du test.
- **Déterminisme reproductible** : à seed et horloge fixés, un échec est reproductible à l'identique.
- **Cas de non-délégation prouvés** : une tentative de rendre une décision structurante ou critique délégable échoue au niveau du moteur de politiques.

### Déterminisme : faux LLMProvider et horloge injectable

Deux dépendances neutralisent la non-détermination et restent injectées dans tous les tests unitaires :

- **Faux `LLMProvider`** : implémentation déterministe de l'abstraction (DT-03), réponses scénarisées, aucun appel réseau. Le cœur ne dépend que de l'interface ; le faux fournisseur est injecté au montage du test.
- **Horloge injectable** : le temps est une dépendance, jamais l'horloge système. Les échéances (report, revalidation) sont testées en avançant une horloge simulée, jamais en attendant le temps réel.
- **Seeds fixes** : tout aléa (ordonnancement, choix) est piloté par une graine fixée, rendant chaque échec reproductible.
- **Factories déterministes** : les entités de test (demandes, recommandations, politiques) sont construites par des factories, jamais par des littéraux dispersés, ce qui garde les cas lisibles et stables entre tests.

### Isolation

Chaque test unitaire est **hermétique** : il ne partage aucun état mutable avec un autre, ne lit aucune variable d'environnement de production et ne dépend d'aucun ordre d'exécution. L'absence d'I/O rend cette isolation gratuite — il n'y a ni base à réinitialiser ni connexion à fermer. Un test unitaire qui exigerait un nettoyage de ressource externe trahirait une fuite de la couche d'intégration dans la couche unitaire et serait à reclasser.

### Chemins asynchrones

Le moteur de politiques est majoritairement synchrone et pur, ce qui simplifie sa preuve. Les rares fonctions du cœur exposées en asynchrone (par exemple une évaluation composée qui délègue à l'abstraction `LLMProvider`) sont testées avec **pytest-asyncio** (`asyncio_mode = "auto"`), toujours contre le faux fournisseur déterministe. Un test asynchrone unitaire ne doit ouvrir aucune boucle réseau réelle : l'`await` porte sur le faux `LLMProvider`, jamais sur un appel sortant. Cette règle maintient la couche unitaire hermétique même sur ses chemins `async`.

## Métriques

| Métrique | Cible | Sens |
| --- | --- | --- |
| Couverture de lignes (`policies`, `core/domain`) | Mesurée par coverage.py | Étendue de la preuve |
| Couverture de branches | Mesurée par coverage.py | Chemins délégation/escalade exercés |
| Nombre de cas par règle | ≥ 1 nominal + ≥ 1 limite | Densité de preuve par invariant |
| Temps d'exécution de la suite unitaire | Borné (indicatif) | Rapidité, condition d'un feedback court |
| Taux de passage | 100 % attendu en CI | Santé de la couche |
| Taux de passage gouvernance (marqueur `governance`) | 100 % (bloquant) | Invariants unitaires prouvés |
| Cas limites aux frontières de classes | ≥ 1 par frontière | Préséance et montée de classe couvertes |

## Seuils de validation

Seuils (indicatifs, à entériner par le CEO comme toute borne — [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)), cohérents avec l'ensemble de la Phase 12 ([`./01-quality-overview.md`](./01-quality-overview.md)) :

| Seuil | Valeur |
| --- | --- |
| Couverture globale | ≥ 85 % |
| Couverture renforcée `core/domain` et `policies` | ≥ 95 % |
| Tests de gouvernance unitaires | 100 % passants (bloquant) |
| Durée de la suite unitaire | Rapide (borne indicative, feedback court) |

La couverture est une condition nécessaire, non suffisante : un module à 95 % dont aucun test ne prouve un invariant reste défaillant. Le seuil renforcé sur `policies` reflète que la classification, la préséance et le quality gate portent la gouvernance.

### Justification des choix

- **Sans I/O au plus bas** : concentrer les invariants du cœur dans une couche sans base ni réseau garantit une suite rapide, hermétique et reproductible ; c'est la couche où la preuve de gouvernance est la moins coûteuse.
- **Un test par règle** : lier chaque règle du Policy Engine à un test rend la gouvernance auditable règle par règle, plutôt qu'à travers des scénarios agrégés difficiles à opposer.
- **Seuil renforcé ciblé** : imposer 95 % là où vivent les invariants est plus signifiant qu'un seuil uniforme ; la couverture sert la gouvernance, pas l'inverse.
- **Déterminisme par injection** : injecter le faux `LLMProvider` et l'horloge évite la fragilité des tests, condition pour que « gouvernance rouge = fusion bloquée » reste tenable sans faux positifs.

### Rappel de gouvernance

Un test unitaire vert **prouve une propriété**, il n'**autorise rien**. La couverture et le passage de la couche unitaire sont des conditions nécessaires à la fusion, jamais une permission : celle-ci reste soumise à l'AI Review Package, à l'audit interne et à la **validation explicite du CEO** ([`../engineering/06-ci-cd-strategy.md`](../engineering/06-ci-cd-strategy.md)). La couche unitaire prouve que le cœur respecte les invariants ; elle ne décide pas, comme aucun automate d'AI-SOS ne décide.

## Questions ouvertes (CEO)

1. **Valeurs de seuil** : 85 % global et 95 % renforcé sont indicatifs — le CEO les confirme-t-il ?
2. **Borne de durée** : quelle durée maximale de la suite unitaire fixer comme cible (feedback court) ?
3. **Cas limites de classification** : quels couples axes/classes servent de cas de référence figés, notamment aux frontières entre classes adjacentes ?
4. **Politique de flakiness** : un test de gouvernance unitaire instable bloque-t-il la CI par défaut (position conservatrice retenue) ou est-il mis en quarantaine sous décision explicite ?
