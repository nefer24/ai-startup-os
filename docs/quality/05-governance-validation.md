# Governance Validation

> Validation AUTOMATIQUE des invariants de gouvernance d'AI-SOS : chaque invariant est prouvé par une contrainte et un test ; un invariant non prouvé est un défaut bloquant, jamais une simple lacune de couverture.

Ce document est le cœur de la Phase 12 (architecture de validation). Il ne crée aucun concept, n'introduit aucun choix technologique et n'écrit aucun code métier : il **prouve**, par des tests automatisés (DT-01 : Python 3.12+/pytest) et des contraintes en base (DT-05 : PostgreSQL 16), que chaque invariant constitutionnel tient à l'exécution. Il applique la [`../BASELINE-v1.0.md`](../BASELINE-v1.0.md), s'appuie sur les contraintes de [`../database/03-constraints-and-invariants.md`](../database/03-constraints-and-invariants.md), la stratégie de test de [`../database/10-database-testing.md`](../database/10-database-testing.md), et projette en critères de réussite les workflows de [`../runtime/06-policy-evaluation-workflow.md`](../runtime/06-policy-evaluation-workflow.md) et [`../runtime/07-human-interrupt-workflow.md`](../runtime/07-human-interrupt-workflow.md). Principe directeur, hérité de [`../database/10-database-testing.md`](../database/10-database-testing.md) : **un invariant non testé est un défaut**, pas une lacune arbitrable en revue.

## Objectifs

- **Prouver chaque invariant, pas seulement le déclarer.** Une contrainte `CHECK`, un trigger ou un privilège révoqué ne suffisent pas : un test doit démontrer qu'une violation est **rejetée**. La preuve est la démonstration active du refus, pas la simple présence du mécanisme.
- **Rendre la gouvernance structurelle.** Les invariants doivent tenir par construction (contrainte de schéma, graphe fermé, endpoint authentifié) et non par la discipline du code applicatif. La validation vérifie cette structuralité.
- **Couvrir 100 % des invariants.** Chaque invariant de la table maître ci-dessous possède au moins un test associé qui prouve le rejet d'une violation. Un invariant sans test est traité comme un **défaut bloquant** à la revue.
- **Tenir sous les deux angles, données et workflow.** Un invariant peut être porté par une contrainte de schéma (données) ou par la structure fermée d'un graphe (workflow) ; la validation couvre les deux angles et prouve que la barrière tient là où l'invariant vit réellement.
- **Faire de toute régression un blocage.** Les tests de gouvernance sont exécutés en étape dédiée et **bloquante** ([`../database/10-database-testing.md`](../database/10-database-testing.md)) : un invariant qui cesse d'être prouvé fait échouer la CI et interdit la fusion. La CI vérifie ; **seul le CEO autorise la fusion**.
- **Séparer preuve et exploitation.** L'audit (table d'événements) est la preuve opposable ; logs et traces ([`../implementation/07-observability.md`](../implementation/07-observability.md)) sont des vues. La validation de gouvernance s'appuie sur la preuve, jamais sur une vue falsifiable.

Ces objectifs traduisent une conviction unique : la gouvernance d'AI-SOS ne doit pas reposer sur la bonne volonté du code, mais sur des barrières qu'un test échoue à franchir. La frontière constitutionnelle « recommander ≠ décider » ([`../BASELINE-v1.0.md`](../BASELINE-v1.0.md)) n'est réputée tenue que si une tentative de la violer est **activement refusée** et **tracée**. Ce document ne réécrit donc aucun invariant : il organise la preuve de ceux déjà posés par les Phases 5 à 11.

## Scénarios

Chaque invariant est adossé à un test qui **tente une violation et attend un rejet**. Le tableau relie l'invariant, le test qui le prouve, le mécanisme sollicité et l'attendu.

| # | Invariant de gouvernance | Test (tentative de violation) | Mécanisme | Attendu |
| --- | --- | --- | --- | --- |
| 1 | Aucun agent ne valide (`validated_by ∈ {ceo, policy}`) | INSERT `decisions` avec `validated_by = 'agent'` | `CHECK` d'énumération | Rejet (`ck_decisions_validator_kind`) |
| 2 | Structurante/critique ⇒ CEO seul | INSERT `decisions` structurante `validated_by = 'policy'` | `CHECK` conditionnel | Rejet (`ck_decisions_high_class_ceo`) |
| 3 | Délégation ⇔ politique référencée | INSERT `validated_by='ceo'` avec `policy_id` non nul (et l'inverse) | `CHECK` d'équivalence + FK | Rejet (`ck_decisions_policy_iff_delegated`) |
| 4 | Politique approuvée par le CEO | INSERT `preapproved_policies` avec `approved_by IS NULL` ou `<> 'ceo'` | `NOT NULL` + `CHECK` | Rejet (`ck_policies_approved_by_ceo`) |
| 5 | Quatre issues canoniques, et quatre seulement | INSERT/UPDATE `decisions` avec `outcome` hors domaine | `CHECK` d'énumération | Rejet (`ck_decisions_outcome_domain`) |
| 6 | Conseil Stratégique activé par le CEO | INSERT conseil `strategic` actif sans `activated_by` / activé par service | `CHECK` conditionnel | 403 middleware + rejet (`ck_councils_strategic_activation`) |
| 7 | Audit immuable | `UPDATE`/`DELETE` sur `audit.audit_events` | Privilège révoqué + trigger | Rejet (`InsufficientPrivilege` / trigger) |
| 8 | Chaîne d'audit vérifiable et monotone | Altération d'un payload puis `verify_chain` | Séquence + trigger de chaînage | Rupture détectée au point exact (`audit.chain_broken`) |
| 9 | Bornes CEO-only, jamais permissives par défaut | Écriture de borne par non-CEO ; borne absente | `NOT NULL` `approved_by` + absence de `DEFAULT` permissif | 403 + rejet ; comportement restrictif par défaut |
| 10 | Résolution d'interrupt par le CEO seul | `resolve` tenté par agent / compte de service | Endpoint authentifié + schéma `validator.type ≠ agent` | 403 (`NonAutorisé`) + interrupt maintenu + anomalie auditée |
| 11 | Aucune exécution non validée | Recherche d'un chemin atteignant l'exécution sans résolution CEO ni arête de politique | Graphe fermé (`StateGraph`) | Impossible par construction ; test de couverture des arêtes |
| 12 | Quality gate non contournable | Présentation d'une recommandation `quality_gate` non franchi | Condition d'entrée d'inbox | Rejet (`QualityGateNonFranchi`) ; aucune entrée en inbox |

Ces scénarios se répartissent en deux familles de preuve, complémentaires et toutes deux bloquantes :

- **Preuve au niveau données** — les invariants 1 à 9 sont portés par les contraintes de [`../database/03-constraints-and-invariants.md`](../database/03-constraints-and-invariants.md) ; le test tente l'écriture interdite et attend le refus de la base (défense en profondeur : privilèges **et** triggers pour l'audit).
- **Preuve au niveau workflow** — les invariants 10 à 12 sont portés par la structure fermée des graphes ([`../runtime/07-human-interrupt-workflow.md`](../runtime/07-human-interrupt-workflow.md)) et le routage déterministe du moteur de politiques ([`../runtime/06-policy-evaluation-workflow.md`](../runtime/06-policy-evaluation-workflow.md)) ; le test cherche à atteindre l'exécution par un chemin illégitime et prouve qu'aucun n'existe.

Deux invariants transverses complètent la table et se prouvent par des scénarios de bout en bout plutôt que par une seule écriture refusée. Le **défaut conservateur FORT** ([`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md)) est prouvé en soumettant au moteur de politiques une entrée ambiguë ou incomplète et en vérifiant que la classe est portée au minimum à structurante et routée vers le CEO (`conservative_default.applied`), jamais descendue vers un routage allégé. La **non-délégation par fractionnement** est prouvée en empilant des décisions individuellement courantes jusqu'à approcher le plafond de portée cumulée ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) et en vérifiant que l'automatisation s'interrompt et remonte au CEO. Dans les deux cas, le test démontre que le doute atteint toujours l'autorité humaine.

Extrait illustratif — un agent ne peut jamais valider une décision (la contrainte rejette l'écriture) :

```python
@pytest.mark.governance
def test_agent_cannot_validate_decision(db):
    # ck_decisions_validator_kind interdit validated_by = 'agent'.
    with pytest.raises(CheckViolation):
        db.execute(
            "INSERT INTO core.decisions (id, request_id, class,"
            " validated_by) VALUES (gen_random_uuid(), %s, 'courante', 'agent')",
            (db.seed_request_id,),
        )
```

Extrait illustratif — une décision structurante ne peut être déléguée à une politique :

```sql
-- Doit échouer sur ck_decisions_high_class_ceo : structurante ⇒ validated_by = 'ceo'.
INSERT INTO core.decisions (id, request_id, class, validated_by, policy_id)
VALUES (gen_random_uuid(), :req, 'structurante', 'policy', :policy_id);
```

Extrait illustratif — l'audit refuse toute mutation ; la rupture de chaîne est détectée au bon maillon :

```python
@pytest.mark.governance
def test_audit_is_append_only_and_chain_detects_tampering(audit_admin_db):
    seq = audit_admin_db.append_audit_event(action="resolve_decision")
    with pytest.raises((InsufficientPrivilege, RaiseException)):
        audit_admin_db.execute("DELETE FROM audit.audit_events WHERE seq = %s", (seq,))
    audit_admin_db.tamper_payload(seq=seq)          # rôle de test réservé, jamais en prod
    result = audit_admin_db.verify_chain()
    assert result.ok is False and result.break_at == seq
```

Extrait illustratif — au niveau workflow, un non-CEO ne peut pas résoudre l'interrupt :

```python
@pytest.mark.governance
def test_only_ceo_resolves_interrupt(runtime):
    # DT-08 : l'endpoint authentifié refuse tout jeton non humain de rôle 'ceo'.
    resp = runtime.resolve(decision_id=runtime.pending_id, actor="agent",
                           outcome="Approuve")
    assert resp.status == 403                        # NonAutorisé
    assert runtime.state(runtime.pending_id) == "en_validation"   # interrupt maintenu
    assert runtime.last_audit_event().kind == "anomaly.flagged"   # tentative tracée
```

Un dernier scénario, structurel et non écrit comme une simple assertion, vérifie qu'**aucun chemin du graphe fermé n'atteint l'exécution** sans passer par la résolution CEO authentifiée ou l'arête de politique pré-approuvée ([`../runtime/07-human-interrupt-workflow.md`](../runtime/07-human-interrupt-workflow.md)) : la couverture des arêtes du `StateGraph` prouve qu'il n'existe qu'un chemin de reprise et une exception journalisée, toute autre transition étant impossible par construction.

L'exécution de ces scénarios est organisée en CI de façon à ce qu'aucun ne puisse être discrètement ignoré :

- **Marqueur `governance` dédié.** Les tests d'invariants portent un marqueur pytest exécuté en **étape séparée et bloquante**, distincte des tests fonctionnels, pour que leur échec soit immédiatement lisible.
- **Base jetable migrée à neuf.** Chaque suite part d'une base PostgreSQL 16 (DT-05) reconstruite depuis `upgrade head`, données factices par factories, sans fuite d'état ni dépendance à un service tiers réel.
- **Garde-fou anti-affaiblissement.** Un test dédié échoue si une révision de migration retire ou assouplit une contrainte d'invariant, avant même que le scénario correspondant ne soit rejoué.
- **Inventaire des invariants versionné.** La table maître est tenue comme un artefact de référence : ajouter un invariant impose d'ajouter son test ; en retirer un impose une décision explicite tracée.

## Critères de réussite

- **Couverture des invariants = 100 %.** Chaque invariant de la table maître possède au moins un test associé qui passe. Un invariant sans test est un défaut bloquant à la revue, jamais un point arbitrable.
- **Tous les tests de gouvernance passent.** Le marqueur `governance` est vert intégralement ; un seul test rouge bloque la fusion au même titre qu'un test fonctionnel rouge.
- **Aucune régression tolérée.** Un garde-fou anti-affaiblissement échoue si une migration retire ou assouplit une contrainte d'invariant : une migration affaiblissante est **irrecevable**, pas arbitrable en revue.
- **Preuve par le refus, pas par la présence.** Chaque test de contrainte démontre effectivement le rejet d'une violation ; un test qui se contenterait de vérifier l'existence d'un `CHECK` sans tenter la violation ne satisfait pas le critère (la présence de contrainte est un complément, pas la preuve principale).
- **Défense en profondeur prouvée pour l'audit.** Les deux barrières de l'immuabilité — privilège révoqué **et** trigger de rejet — sont testées séparément, de sorte que la défaillance d'une seule ne rende pas l'audit mutable.
- **Doute toujours résolu vers le CEO.** Les scénarios transverses prouvent que toute ambiguïté (entrée incomplète, contrôle indépendant absent, seuils manquants) porte la classe au minimum à structurante et route vers le CEO, jamais vers un routage allégé.
- **Rejouabilité pour l'audit.** À entrées et configuration identiques, la classification et le routage du moteur de politiques sont identiques ([`../runtime/06-policy-evaluation-workflow.md`](../runtime/06-policy-evaluation-workflow.md)) ; les tests de gouvernance sont déterministes et hermétiques (base jetable migrée à neuf, aucune dépendance réseau réelle).
- **Survie aux migrations.** Après `upgrade head` sur base vierge, un test de présence interroge le catalogue (`pg_constraint`, `information_schema`) pour confirmer que chaque contrainte d'invariant existe encore : les invariants sont portés par les migrations, pas seulement par le code applicatif ([`../database/10-database-testing.md`](../database/10-database-testing.md)).

Le tableau de bord de gouvernance ([`../implementation/07-observability.md`](../implementation/07-observability.md)) surveille en priorité ce qui touche à ces critères : chaîne d'audit invalide (alerte critique immédiate au CEO), échecs répétés du quality gate sur une même demande, approche des plafonds de portée cumulée des politiques. La validation en test et la surveillance en production instrumentent les mêmes invariants, sans jamais rendre au CEO une autorité qu'il n'a jamais perdue.

## Métriques

Les métriques de validation sont dérivées de l'observabilité de gouvernance ([`../implementation/07-observability.md`](../implementation/07-observability.md), DT-06) et de la suite de tests. La métrique reine est le **taux de couverture des invariants** : à la différence d'une couverture de lignes, elle se mesure sur un inventaire nommé d'invariants et n'admet qu'une seule valeur acceptable, 100 %.

| Métrique | Définition | Cible |
| --- | --- | --- |
| Nombre d'invariants recensés | Cardinal de la table maître (données + workflow) | Référence figée, révisée par version |
| Invariants couverts par test | Invariants ayant ≥ 1 test prouvant un rejet | = nombre d'invariants (100 %) |
| Taux de couverture des invariants | Couverts / recensés | 100 % (non négociable) |
| Taux de passage des tests `governance` | Tests verts / tests exécutés | 100 % |
| Régressions détectées | Contraintes retirées/assouplies interceptées par le garde-fou | 0 tolérée |
| Temps d'exécution de la suite `governance` | Durée de l'étape bloquante en CI | Borné, surveillé pour éviter la dérive |
| Anomalies de gouvernance auditées | Tentatives refusées consignées (`anomaly.flagged`) | Toutes tracées avant acquittement |
| Couverture de code `core`/`policies` | Lignes/branches couvertes sur les modules porteurs d'invariants | ≥ 95 % |
| Invariants sans test (dette de preuve) | Invariants recensés non encore adossés à un test | 0 (bloquant en revue) |

## Seuils de validation

- **Couverture des invariants de gouvernance = 100 %.** Seuil **non négociable et bloquant** : un invariant sans test prouvant le rejet d'une violation interdit la promotion, sans arbitrage possible.
- **Passage des tests de gouvernance = 100 %.** La suite `governance` est **bloquante** : un test rouge bloque la fusion.
- **Régressions tolérées = 0.** Toute contrainte d'invariant retirée ou assouplie fait échouer le garde-fou anti-affaiblissement ; la migration est irrecevable.
- **Couverture de code sur `core`/`policies` ≥ 95 %.** Renforcée là où vivent les invariants (décisions, politiques, bornes, audit), conformément à [`../database/10-database-testing.md`](../database/10-database-testing.md).
- **Chaîne d'audit vérifiable = condition permanente.** `verify_chain` doit rester vrai sur une chaîne saine et signaler le **point de rupture exact** sur une altération simulée ; un faux positif se corrige côté canonicalisation, jamais en désactivant le test.
- **Dette de preuve = 0.** Aucun invariant recensé ne peut rester sans test associé ; l'ajout d'un invariant sans son test est irrecevable en revue.
- **Aucune exemption au titre de la performance.** Aucun seuil de performance ([`./06-performance-testing.md`](./06-performance-testing.md)) ne peut justifier de désactiver, contourner ou assouplir un test de gouvernance : le côté sûr est toujours plus d'implication du CEO, jamais moins de preuve.

## Questions ouvertes (CEO)

1. **Politique de flakiness des tests de gouvernance** : un test d'invariant instable bloque-t-il la CI par défaut (position conservatrice retenue) ou est-il mis en quarantaine sous décision explicite, avec quelle traçabilité ([`../database/10-database-testing.md`](../database/10-database-testing.md)) ?
2. **Rôle d'administration de test** pour simuler une altération d'audit : périmètre exact et garantie qu'il n'existe jamais en production.
3. **Normalisation des codes SQLSTATE** des triggers pour un mapping direct vers le catalogue d'erreurs, afin que les assertions de test visent un code stable plutôt qu'une exception générique.
4. **Portée du contrôle « politique active + dans plafonds »** : quelle part reste applicative transactionnelle et quelle part est prouvée par contrainte/trigger côté base, et comment la couverture de test se répartit-elle entre les deux ([`../database/03-constraints-and-invariants.md`](../database/03-constraints-and-invariants.md)) ?
5. **Cadence de vérification complète de la chaîne d'audit** (`verify_chain` de bout en bout) en complément du contrôle à l'insertion : à quelle fréquence et sur quel volume de référence ?
6. **Entérinement de DT-05/DT-06** dont dépendent la matérialisation en base des contraintes et l'observabilité de gouvernance (propositions à confirmer, futures décisions 017+).
7. **Gouvernance de l'inventaire d'invariants** : quel processus encadre l'ajout ou le retrait d'un invariant de la table maître, et faut-il qu'un retrait passe par une décision explicite du CEO au registre des décisions ?

---

**Renvois** : [`../database/03-constraints-and-invariants.md`](../database/03-constraints-and-invariants.md) · [`../database/10-database-testing.md`](../database/10-database-testing.md) · [`../runtime/06-policy-evaluation-workflow.md`](../runtime/06-policy-evaluation-workflow.md) · [`../runtime/07-human-interrupt-workflow.md`](../runtime/07-human-interrupt-workflow.md) · [`../policies/07-decision-classification-policy.md`](../policies/07-decision-classification-policy.md) · [`../policies/09-quality-gate-policy.md`](../policies/09-quality-gate-policy.md) · [`../implementation/07-observability.md`](../implementation/07-observability.md) · [`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md) · [`./06-performance-testing.md`](./06-performance-testing.md)
