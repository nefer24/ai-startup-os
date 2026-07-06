# C0.2 — API Foundation (lecture seule)

> Phase **C0 — Consolidation du socle E1–E8**. E9 reste **fermé**.
> Responsabilité unique de C0.2 : **exposer**.

## Objet

C0.2 pose une **fondation API framework-agnostique** qui **expose en lecture seule** les
_read models_ de la **CEO Read Console** (C0.1). Elle ne fait qu'**exposer** : elle ne décide pas,
ne valide pas, ne refuse pas, ne commente pas, n'applique pas, ne mute pas, ne crée pas, ne supprime
pas, ne déclenche pas E7, n'ouvre pas E9, et n'écrit ni dans l'audit ni dans la mémoire.

Module : `src/aisos/api/read/` — `responses.py` (modèles de réponse), `routes.py` (descripteurs de
routes + catalogue), `service.py` (service de projection pur + provider en mémoire).

## Layering imposé

```
Domaine E1–E8  ──►  CEO Read Console view models (C0.1)  ──►  API response models (C0.2)
```

Jamais `API ──► mutation domaine`. Le module `aisos.api.read` importe **uniquement** la couche
`aisos.ceo_console` ; il **n'importe pas** `aisos.evolution` directement (garanti par test).

## Endpoints (GET / read-only uniquement)

| Méthode | Route                              | Ressource             | Nature visuelle    |
| ------- | ---------------------------------- | --------------------- | ------------------ |
| GET     | `/ceo-console`                     | `ceo_console`         | `READ_ONLY_CONTEXT` |
| GET     | `/ceo-console/organizations`       | `ceo_organization`    | `READ_ONLY_CONTEXT` |
| GET     | `/ceo-console/recommendations`     | `ceo_recommendation`  | `CONSULTATIVE`     |
| GET     | `/ceo-console/decisions`           | `ceo_decision`        | `DECISION`         |
| GET     | `/ceo-console/traces`              | `ceo_trace`           | `TRACE`            |
| GET     | `/ceo-console/audit-references`    | `ceo_audit_reference` | `AUDIT_REFERENCE`  |
| GET     | `/ceo-console/memory-contexts`     | `ceo_memory_context`  | `MEMORY_CONTEXT`   |
| GET     | `/ceo-console/closures`            | `ceo_closure`         | `CLOSURE`          |

Toutes les routes sont **`GET` / `READ_ONLY`**. La seule méthode déclarée (`APIReadOnlyMethod`) est
`GET` ; la seule nature d'endpoint (`APIEndpointNature`) est `READ_ONLY`. Aucun descripteur ne peut
nommer une action (`approve`, `reject`, `validate`, `decide`, `apply`, `mutate`, `create`, `delete`,
`trigger`, `open_e7`, `open_e9`, `write_audit`, `write_memory`, …) : le validateur les refuse.

## Garanties de gouvernance exposées

- **C0.2 expose uniquement la lecture** ; les endpoints sont **GET / read-only**.
- La **console CEO reste sans action** (aucun bouton, aucun handler de mutation).
- Les **recommandations** sont **consultatives** (`CONSULTATIVE`), jamais présentées comme des
  décisions.
- Les **décisions** sont **affichées mais non modifiables** (`DECISION`, lecture seule).
- L'**audit** est **affiché comme source de vérité** mais **jamais écrit** ni réécrit
  (`AUDIT_REFERENCE`).
- La **mémoire** est **affichée comme contexte** mais **jamais preuve** (`MEMORY_CONTEXT`), distincte
  de l'audit.
- Les **traces** et **clôtures** sont affichées en lecture seule (`TRACE`, `CLOSURE`).

## Ce que C0.2 n'introduit PAS (frontières)

- **Pas de serveur web / framework runtime** : la fondation est déclarative (aucun FastAPI, aucun
  serveur monté, aucune route montée). Une documentation OpenAPI **abstraite** est produite comme
  simple `dict` via `CEOConsoleReadRouteCatalog.to_openapi_abstract()`.
- **Pas d'authentification / RBAC** (relève de **C0.4**) : aucun login, session, JWT, middleware.
- **Pas de persistance réelle** (relève de **C0.3**) : aucun schéma DB, aucune migration, aucun
  repository SQL, aucun SQLAlchemy/Alembic. Le `InMemoryCEOConsoleReadProvider` est un _fake_ de
  lecture non durable, réservé aux tests/démonstration ; il n'est pas source de vérité.
- **Pas de workflow de décision CEO** (relève de **C0.5**) : aucun endpoint de validation/refus/
  commentaire/décision, aucune application de recommandation.
- **Pas d'audit opérationnel** (relève de **C0.6**) ni de **mémoire opérationnelle** (relève de
  **C0.7**).

## Invariants préservés

Contrats **E1–E8 inchangés** ; **C0.1 inchangé** ; **E9 fermé**. Aucune surface de pouvoir sur les
modèles de réponse ; immutabilité (`frozen`) et déterminisme garantis par test.
