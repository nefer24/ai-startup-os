# Plan M1 — Premier branchement réel gouverné d'un fournisseur LLM

> **Statut du document** : **Accepted / Ratifié par le CEO** (porte **M1-001**, 2026-07-03).
> **Date** : 2026-07-03.
> **Nature** : **planification uniquement**. Ce document n'écrit aucun code, n'active aucun
> fournisseur, ne déclare aucune clé, n'effectue aucun appel réseau et **ne modifie aucune
> gouvernance**. Il décrit *ce qui devra être fait* pour brancher un LLM réel de façon
> gouvernée — pas *le faire*.
> **Prérequis** : jalon M0 clôturé (cf. [`M0_LLM_READINESS_REPORT.md`](M0_LLM_READINESS_REPORT.md)).

---

## Ratification CEO — M1-001

- **Décision** : **APPROVED** (ouverture du jalon **M1**, item **M1-001**), 2026-07-03.
- **Référence** : M1-001.
- **Justification** : M1 peut commencer parce que le jalon **M0 est clôturé** et que les garanties
  fondatrices sont **établies et prouvées par test** — *record/replay déterministe* (« replay
  never calls model »), *audit source unique* (append-only, hash-chaîné), *activation CEO-only*
  (refus par défaut, impossible sans `RealLLMActivationDecision.granted`) et *no automatic
  decision* (l'agent recommande, le CEO décide). Le présent plan préserve ces invariants et borne
  le risque du premier appel réel (fournisseur unique, budget/timeout stricts, appel réel opt-in
  hors CI, critères de refus explicites).
- **Portée de la décision** : cette ratification **ouvre la conception et le branchement
  contrôlé** de M1. Elle **n'active aucun fournisseur**, n'introduit aucune clé et n'autorise
  aucun appel réseau. La première ligne de code réel reste conditionnée à cette ratification (à
  présent acquise) ; la première **activation** réelle restera conditionnée à une
  `RealLLMActivationDecision.granted` émise par le CEO au moment voulu.
- **Décision différée** : le choix du fournisseur cible (OpenAI vs Anthropic) reste une décision
  CEO ultérieure — non tranchée par la présente ratification (cf. §3).

---

## 1. Objectif de M1

Réaliser le **premier appel à un fournisseur LLM réel** dans AI-SOS, **derrière le port
existant `LLMProvider`**, en respectant tous les invariants prouvés en M0 : le CEO reste seul
décideur, chaque interaction réelle est **enregistrée** (record) puis **rejouable** (replay)
sans rappeler le modèle, chaque activation est **auditée**, et rien n'est activé sans décision
CEO explicite.

M1 n'est **pas** une mise en production. C'est la première **confrontation au réel** du contrat
construit en M0 : prouver que le squelette d'adaptateur (`LLMProviderAdapter`), la barrière
d'activation (`RealLLMActivationGuard`) et le mécanisme record/replay fonctionnent contre un
vrai modèle, en environnement contrôlé, sous budget et timeout stricts.

**But mesurable** : obtenir au moins une interaction réelle enregistrée, la rejouer à
l'identique hors ligne (sans réseau), et vérifier que l'audit et la gouvernance se comportent
exactement comme sous stub.

**Hors périmètre M1** : API REST, persistance durable (base réelle), haute disponibilité,
multi-tenant, streaming, orchestration multi-agents réelle, exposition externe. Ces éléments
restent pour des jalons ultérieurs.

---

## 2. Conditions d'entrée depuis M0

M1 ne peut démarrer que si **toutes** les conditions suivantes, héritées de M0, sont vérifiées.
Elles le sont à la clôture de M0 (référence : rapport M0) :

| Condition d'entrée | État M0 |
|---|---|
| Port `LLMProvider` stable (`STUB`/`RECORD`/`REPLAY`) | ✅ livré (#36) |
| Record/replay déterministe, *replay never calls model* | ✅ prouvé (#36) |
| `LLMInteractionStore` (port append-only) | ✅ livré (#40) |
| Persistance mémoire survivant au rollback | ✅ livré (#41) |
| Squelette `LLMProviderAdapter` (désactivé, refuse tout appel) | ✅ livré (#42) |
| Barrière d'activation `RealLLMActivationGuard` (CEO-only, refus par défaut) | ✅ livré (#43) |
| Audit source unique, append-only, hash-chaîné | ✅ livré (#38) |
| `RealLLMProviderConfig` : budget/timeout/`api_key_env` (nom seul) | ✅ livré (#42) |
| ADR-0009/0010/0011 ratifiées | ✅ Accepted |

**Porte d'entrée M1** : aucune ligne de code réel n'est écrite tant que le CEO n'a pas ratifié
ce plan. La ratification de ce document est elle-même la première condition d'entrée de M1.

---

## 3. Fournisseur cible proposé

`ProviderName` déclare aujourd'hui `openai` et `anthropic` (noms seuls, aucun SDK importé).

**Proposition** : cibler **un seul** fournisseur pour le premier branchement, afin de réduire la
surface de risque. Le choix précis (OpenAI vs Anthropic) est une **décision CEO** ; ce plan ne
tranche pas et ne préinstalle rien.

Critères de sélection à soumettre au CEO :

- Disponibilité d'un modèle avec **version explicitement épinglable** (`model_version`), condition
  du déterminisme du replay (ADR-0010).
- Support de paramètres de génération reproductibles (p.ex. température fixée), compatibles avec
  la validation `parameters` du replay.
- Modèle de coût et de quota compatible avec un budget strict (§6).
- Conditions contractuelles/licence acceptables pour un usage gouverné.

**Décision par défaut recommandée** : commencer par le fournisseur dont un modèle Claude récent
est disponible avec version épinglée, cohérent avec la pile AI-SOS. À confirmer par le CEO au
moment de M1 — **aucun** choix n'est câblé ici.

Le branchement passera **obligatoirement** par le port `LLMProvider` : le backend réel sera une
implémentation de `complete()` à l'intérieur de `LLMProviderAdapter` (aujourd'hui
`RealLLMProviderNotWiredError`), jamais un appel direct depuis le cœur.

---

## 4. Gestion des secrets

Invariant M0 à préserver : **aucun secret dans le code**. `RealLLMProviderConfig.api_key_env`
porte le **nom** d'une variable d'environnement, jamais la clé.

Plan M1 :

- La clé réelle est fournie **exclusivement** via la variable d'environnement nommée par
  `api_key_env` (p.ex. `AISOS_LLM_API_KEY`), résolue **à l'exécution** par l'adaptateur.
- Le code ne lit jamais une clé littérale ; il lit `os.environ[config.api_key_env]` au moment de
  l'appel, et échoue proprement (erreur explicite, sans divulguer la valeur) si absente.
- **Aucune** clé n'apparaît dans les logs, l'audit, les messages d'erreur, les enregistrements
  record/replay, ni les tests. Les scans anti-secret existants
  (`test_llm_real_provider_adapter.py`, `test_llm_real_provider_activation.py`) sont **étendus**
  au nouveau code d'adaptateur réel.
- Rotation : documenter qu'une rotation de clé se fait par changement de la variable
  d'environnement, sans redéploiement du code ; hors périmètre : coffre-fort/rotation
  automatisée (jalon ultérieur, RR3 du rapport M0).
- Le payload d'audit d'activation continue de ne consigner que le **nom** `api_key_env`
  (comportement déjà en place dans `RealLLMActivationGuard`).

---

## 5. Activation CEO-only

La barrière `RealLLMActivationGuard` (M0) est le **point d'entrée unique** de toute activation.
M1 la **consomme**, ne la contourne pas.

Séquence gouvernée proposée :

1. Le CEO soumet une `RealLLMActivationRequest` (principal CEO, `RealLLMProviderConfig`
   `enabled=True` et complète, justification).
2. `RealLLMActivationGuard.evaluate(...)` : refuse si l'acteur n'est pas le CEO **ou** si la
   config n'est pas active/valide ; sinon **autorise** et **produit** un événement d'audit
   CEO-only (`bounds.updated`).
3. Un **composant racine** (nouveau en M1, hors cœur) reçoit la `RealLLMActivationDecision`.
   **Seulement si `granted`**, il instancie `LLMProviderAdapter(decision.activated_config)` et
   le met à disposition en mode `RECORD`.
4. Aucun chemin alternatif n'instancie un adaptateur réel actif. Un test de gouvernance vérifie
   que **toute** activation passe par une décision `granted`.

**Invariant à prouver en M1** : il est **impossible** d'obtenir un `LLMProviderAdapter` réel
actif sans une `RealLLMActivationDecision.granted == True` émanant du CEO. Le risque RR7 du
rapport M0 (câblage contournant la garde) est neutralisé par ce test.

Désactivation : couper l'accès réel = ne plus fournir de décision `granted` / repasser la config
`enabled=False`. À documenter comme geste CEO réversible.

---

## 6. Budget et timeouts

Bornes économiques (ADR-0009). `RealLLMProviderConfig` porte déjà `timeout_ms`, `token_budget`,
`cost_budget_eur`.

Plan M1 :

- **Timeout dur** : l'appel réel respecte `config.timeout_ms` (> 0, validé). Dépassement ⇒
  interruption + statut d'échec explicite, jamais un blocage indéfini.
- **Budget de jetons** : l'application des bornes reste au **point unique** existant —
  `AgentRuntime` réutilisant `DefaultManifestEnforcer.within_budget()`. M1 ne réimplémente pas
  la vérification de budget ; il **raccorde** le coût réel observé à ce point d'application.
  Dépassement ⇒ `RuntimeStatus.BUDGET_EXCEEDED` (comportement déjà prouvé sous stub).
- **Budget de coût** : `cost_budget_eur` sert de plafond ; un appel dont le coût estimé/observé
  dépasse le plafond est refusé/interrompu et escaladé, jamais silencieusement dépassé.
- **Valeurs M1 conservatrices** : timeout court, `token_budget` bas, `cost_budget_eur` faible —
  M1 est un test contrôlé, pas une charge de production. Valeurs exactes à fixer par le CEO à
  l'activation.
- **Défaut conservateur** : en cas de doute (coût inconnu, quota incertain), on **escalade au
  CEO** plutôt que d'appeler — cohérent avec l'invariant *governance before execution*.

---

## 7. Record obligatoire

Tout appel réel en M1 se fait en mode **`RECORD`**, sans exception.

- L'adaptateur réel est **toujours** encapsulé dans `RecordingLLMProvider(inner=adapter,
  store=...)`. Le cœur n'appelle jamais l'adaptateur réel « nu ».
- Chaque interaction réelle produit un `LLMInteractionRecord` écrit dans le
  `LLMInteractionStore` (append-only), indexé par `prompt_hash` (calculé sur `prompt` + `step`),
  avec `model`/`model_version`/`parameters`.
- L'écriture de l'interaction est **directe (hors transaction)** afin de **survivre à un
  rollback** (garantie M0), condition du rejeu après incident.
- **Sans record réussi, pas de résultat exploité** : si l'enregistrement échoue, l'interaction
  est considérée comme non fiable (on ne peut pas la rejouer/auditer) et l'appel est traité
  comme un échec gouverné.
- Aucun secret n'entre dans l'enregistrement (prompt/réponse/métadonnées uniquement).

---

## 8. Replay obligatoire

Le déterminisme est un critère d'acceptation, pas une option.

- Après une campagne `RECORD`, la **même** requête rejouée en mode **`REPLAY`** doit renvoyer
  l'interaction enregistrée **sans aucun appel réseau** (invariant *replay never calls model*,
  déjà prouvé sous stub, à **re-prouver contre des données réelles**).
- `ReplayLLMProvider(store)` valide `model_version` et `parameters` : un décalage produit une
  **erreur explicite** (`ModelVersionMismatchError` / `ParametersMismatchError`), jamais un
  résultat silencieux ; une absence produit `ReplayMissError`.
- **Test hors ligne** : la suite de replay M1 doit passer **réseau coupé** (ou fournisseur
  configuré indisponible) pour prouver qu'aucun appel réel n'a lieu au rejeu.
- Un enregistrement réalisé avant un crash simulé doit être **rejouable après reprise** (rejoue
  la garantie *no rollback loss* de M0, avec données réelles).

---

## 9. Audit obligatoire

Source unique de vérité (ADR-0011), append-only, hash-chaînée.

- **Activation** : chaque autorisation CEO produit un événement d'audit `bounds.updated`
  (acteur `ceo:<subject>`, payload sans secret) — déjà en place dans la garde.
- **Appels réels** : chaque interaction réelle (ou tentative refusée/échouée) doit être
  **traçable** via le journal d'audit unique et/ou le store d'interactions, sans divergence entre
  les deux magasins (garantie M0 : deux magasins distincts, aucune duplication).
- **Aucun secret** dans l'audit (nom de variable d'env uniquement).
- La chaîne de hachage reste **vérifiable** (`verify_chain().valid`) après toute la campagne M1.
- Un refus (non-CEO, budget dépassé, timeout, config invalide) est **audité ou explicitement
  tracé** selon le point de contrôle, mais ne produit **jamais** une entrée d'activation.

---

## 10. Scénarios de test

Tests à écrire en M1 (au-delà des tests M0 qui doivent rester verts). Objectif : couvrir le
chemin réel comme le chemin dégénéré.

- **T1 — Activation CEO valide** : CEO + config active ⇒ décision `granted`, adaptateur réel
  instancié en `RECORD`, audit `bounds.updated` produit, chaîne valide.
- **T2 — Record d'un appel réel** (test d'intégration, marqué, exécuté sur décision, avec clé
  réelle en variable d'env, budget minimal) ⇒ interaction enregistrée, indexée par `prompt_hash`.
- **T3 — Replay hors ligne** : rejouer T2 réseau coupé ⇒ même réponse, **aucun** appel réel.
- **T4 — Determinisme** : `model_version`/`parameters` divergents ⇒ erreurs explicites.
- **T5 — Survie au rollback** : interaction réelle enregistrée puis rollback d'orchestration ⇒
  interaction préservée, replay réussit.
- **T6 — Budget/timeout** : appel dépassant `token_budget` ⇒ `BUDGET_EXCEEDED` ; appel dépassant
  `timeout_ms` ⇒ interruption + échec explicite.
- **T7 — Aucune décision automatique** : le LLM réel produit une **recommandation**, jamais une
  décision ; toute tentative de décider est escaladée au CEO (rejoue F8 avec un vrai modèle).
- **T8 — Aucun secret** : scans anti-secret étendus au code d'adaptateur réel ; aucun secret dans
  logs/audit/records.
- **T9 — Contournement impossible** : aucun chemin n'instancie un adaptateur réel actif sans
  `RealLLMActivationDecision.granted`.

Note : T2 (appel réel) est **opt-in**, isolé derrière un marqueur (p.ex. `integration` /
`real_llm`), **désactivé** en CI par défaut, exécuté uniquement sur décision explicite avec clé
fournie. La CI standard reste **sans réseau** et rejoue T3 depuis des enregistrements fixés.

---

## 11. Scénarios d'échec

À traiter explicitement — un échec ne doit jamais dégrader la gouvernance :

- **E1 — Clé absente/invalide** : variable d'env manquante ⇒ échec explicite, sans divulguer de
  valeur ; aucune activation « à moitié ».
- **E2 — Réseau indisponible / timeout** : ⇒ interruption propre, statut d'échec, escalade ;
  jamais de blocage.
- **E3 — Réponse non conforme** (vide, tronquée, format inattendu) : ⇒ traitée comme faible/échec
  par le Quality Gate déterministe, escalade au CEO, jamais acceptée telle quelle.
- **E4 — Dépassement de budget/coût** : ⇒ `BUDGET_EXCEEDED`, appel refusé/interrompu.
- **E5 — Le modèle tente de « décider »** : ⇒ ignoré comme décision (schéma `Recommendation` sans
  champ décisionnel), escalade CEO.
- **E6 — Échec d'enregistrement (record)** : ⇒ interaction non fiable, appel traité comme échec ;
  on ne rejoue jamais une interaction non enregistrée.
- **E7 — Divergence replay** (`model_version`/`parameters`) : ⇒ erreur explicite, pas de résultat
  silencieux.
- **E8 — Activation par un non-CEO** : ⇒ refus par la garde, aucun audit d'activation, aucun
  adaptateur actif.

---

## 12. Critères d'acceptation

M1 est **accepté** si **tous** les points suivants sont vrais :

1. Au moins **une interaction réelle** enregistrée en mode `RECORD` derrière le port.
2. Cette interaction est **rejouée à l'identique hors ligne** (réseau coupé), sans appel réel.
3. **Aucune activation** réelle n'a eu lieu sans `RealLLMActivationDecision.granted` du CEO.
4. **Aucun secret** dans le code, les logs, l'audit ou les enregistrements (scans verts).
5. **Budget et timeout** appliqués au point unique existant ; dépassements gérés (T6).
6. **Aucune décision automatique** : le modèle recommande, le CEO décide (T7).
7. **Audit** source unique, append-only, chaîne vérifiable après campagne.
8. **Tous les tests M0 restent verts** (aucune régression, Vertical Slice F1–F10 comprise).
9. `ruff` + `ruff format` + `mypy` strict + `pytest` + CI GitHub Actions **verts** (la CI
   standard reste sans réseau).

---

## 13. Critères de refus

M1 est **refusé** (et le branchement suspendu) si **l'un** des points suivants survient :

- Un appel réel a lieu **sans** décision CEO `granted` (contournement de la garde).
- Un secret apparaît dans le code, les logs, l'audit ou un enregistrement.
- Un appel réel se produit **en dehors** du mode `RECORD` (interaction non enregistrée).
- Le replay **rappelle le modèle** (violation de *replay never calls model*).
- Le replay renvoie un résultat **silencieusement** faux sur `model_version`/`parameters`
  divergents (absence d'erreur explicite).
- Le budget ou le timeout est **dépassé silencieusement**.
- Le modèle produit une **décision** traitée comme telle (au lieu d'une recommandation escaladée).
- L'audit **diverge** (double-write, entrée d'activation sur refus, chaîne invalide).
- Une régression casse un invariant M0 ou la Vertical Slice.

Tout critère de refus déclenché ⇒ retour en conception, **sans** maintenir un fournisseur réel
actif.

---

## 14. Risques restants

Hérités du rapport M0 (RR1–RR7) et propres à M1 :

- **RR1 — Comportement réel non maîtrisé** : latence, erreurs, réponses non conformes, coûts
  effectifs découverts en M1 ; d'où budget/timeout stricts et campagne contrôlée.
- **RR2 — Persistance non durable** : le replay après *arrêt de processus* reste hors périmètre ;
  M1 prouve la survie au rollback intra-processus, pas la durabilité disque.
- **RR3 — Gestion des secrets partielle** : variable d'env uniquement ; pas de coffre-fort ni de
  rotation automatisée.
- **RR7 — Câblage de la garde** : le nouveau composant racine consommant `activated_config` doit
  être conçu pour **ne pas** pouvoir contourner la garde ; neutralisé par le test T9/critère 3.
- **Nouveau — Coût réel** : un appel réel engage un coût financier ; le plafond `cost_budget_eur`
  doit être bas et surveillé.
- **Nouveau — Dépendance externe** : introduire un SDK/HTTP réel élargit la surface de sécurité et
  de supply-chain ; à isoler strictement derrière l'adaptateur, hors du cœur.
- **Nouveau — Reproductibilité du modèle** : même version épinglée, un fournisseur peut faire
  évoluer un modèle ; d'où la validation stricte `model_version`/`parameters` au replay.

---

## 15. Recommandation finale

**Recommandation : ouvrir M1 en tant que jalon de conception et de branchement contrôlé, sous
réserve de ratification CEO de ce plan — sans activer aucun fournisseur avant cette
ratification.**

Argumentation :

1. Les **conditions d'entrée** (§2) sont satisfaites : M0 fournit port, record/replay, store,
   persistance, squelette d'adaptateur, barrière d'activation CEO-only et audit source unique,
   tous couverts par des tests.
2. Le plan **préserve tous les invariants M0** (record obligatoire, replay sans rappel du modèle,
   audit unique, activation CEO-only, aucune décision automatique, gouvernance avant exécution).
3. Le **risque réel est borné** : un seul fournisseur, budget/timeout stricts, appel réel opt-in
   isolé hors CI, critères de refus explicites suspendant le branchement en cas de dérive.
4. La **valeur** est claire : prouver que le contrat M0 tient face à un vrai modèle, condition de
   tout usage futur.

**Réserve** : ce plan **n'active rien**. La première ligne de code réel de M1 ne doit être écrite
qu'après ratification explicite du CEO de ce document, et la première activation réelle qu'après
une `RealLLMActivationDecision.granted` du CEO au moment voulu. Aucun fournisseur, aucune clé,
aucun appel réseau n'est introduit par le présent document.

---

*Plan soumis à la revue du Chief AI Architect et à la validation du CEO. Aucune fusion, aucune
activation, aucun code avant autorisation explicite.*
