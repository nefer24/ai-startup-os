# Security & Permissions

> Ce document définit le modèle de sécurité d'AI-SOS : une identité humaine unique (le CEO), des comptes de service pour les processus, des permissions par agent appliquées à l'exécution, et la traduction technique de chaque invariant de gouvernance en contrôle vérifiable.

## Position dans la baseline

La sécurité est le lieu où la gouvernance cesse d'être une convention pour devenir une **contrainte structurelle**. Ce document applique les invariants du corpus gelé ([`../BASELINE-v1.0.md`](../BASELINE-v1.0.md)) et le modèle de menace comportemental ([`../behavior/14-integrity-and-threat-model.md`](../behavior/14-integrity-and-threat-model.md)). Les technologies (OIDC/JWT, RBAC) relèvent de DT-07, proposition à entériner par le CEO.

## Modèle d'identité

Il n'existe qu'**un seul humain** dans AI-SOS : le **CEO**. Tout le reste est un processus.

| Rôle | Nature | Portée |
| --- | --- | --- |
| `ceo` | Humain (OIDC/JWT, MFA recommandé) | Toutes les décisions, la configuration des bornes, le registre des politiques pré-approuvées, l'activation du Conseil Stratégique, l'administration des agents |
| `orchestrator-svc` | Compte de service (jeton court) | Exécution des graphes, écritures runtime (transitions, événements), ordonnancement |
| `agent-runtime` | Compte de service (jeton court) | Exécution des nœuds d'agents, **strictement limité au manifest** de l'agent courant |
| `auditor-ro` | Rôle technique en lecture seule | Lecture de l'audit et des événements — **ce n'est pas un humain supplémentaire** : c'est un accès en lecture que le CEO utilise ou accorde à un outil |

Aucun de ces rôles, hormis `ceo`, ne peut valider une décision, activer un Conseil Stratégique ou modifier une borne.

## Matrice d'autorisation

| Ressource / action | `ceo` | `orchestrator-svc` | `agent-runtime` | `auditor-ro` |
| --- | :---: | :---: | :---: | :---: |
| Résoudre une décision (Approuve/Ajuste/Reporte/Rejette) | ✅ | ⛔ | ⛔ | ⛔ |
| Activer le Conseil Stratégique Dynamique | ✅ | ⛔ (propose seulement) | ⛔ | ⛔ |
| Modifier une borne / un seuil | ✅ | ⛔ | ⛔ | ⛔ |
| Créer / suspendre une politique pré-approuvée | ✅ | ⛔ | ⛔ | ⛔ |
| Créer / retirer un agent | ✅ | ⛔ (propose) | ⛔ | ⛔ |
| Exécuter un graphe / écrire une transition | ⛔ | ✅ | ⛔ | ⛔ |
| Exécuter un nœud d'agent (dans son manifest) | ⛔ | ⛔ | ✅ | ⛔ |
| Appliquer une politique pré-approuvée (runtime) | ⛔ | ✅ (avec référence de politique) | ⛔ | ⛔ |
| Lire l'audit / les événements | ✅ | ✅ | partiel | ✅ |

Les lignes réservées à `ceo` sont **strictement** exclusives : aucun compte de service n'y a de chemin d'accès (voir « Application des invariants »).

## Permissions par agent

La fiche d'agent (Phases 1–2, [`../../agents/`](../../agents/)) devient un **manifest appliqué à l'exécution** :

| Dimension | Contrôle |
| --- | --- |
| Outils autorisés | Liste blanche ; tout appel hors liste = refus + événement d'audit |
| Portées mémoire | Lecture/écriture par portée (projet/utilisateur/organisationnelle) ; refus par défaut |
| Budget de tokens | Plafond par tâche ([`../behavior/13-bounds-and-thresholds.md`](../behavior/13-bounds-and-thresholds.md)) ; dépassement = arrêt + escalade |
| Domaines réseau | Egress restreint aux domaines déclarés |

Principe de **moindre privilège** : ce qui n'est pas explicitement autorisé est refusé. Tout dépassement produit un **événement d'audit** et déclenche l'**escalade** (Spécialiste → Orchestrateur → CEO).

## Application des invariants de gouvernance par la technique

| Invariant (corpus gelé) | Contrôle technique |
| --- | --- |
| Aucun agent ne décide | L'endpoint `resolve` exige le rôle `ceo` ; l'interrupt LangGraph ne reprend que sur une décision signée CEO ; contrainte de schéma `validated_by ≠ agent` ([`./04-data-model.md`](./04-data-model.md)) |
| Délégation uniquement vers politiques pré-approuvées | Le contournement d'interrupt exige une **référence de politique active** vérifiée par le moteur de politiques ; sinon interrupt CEO obligatoire |
| Structurante/critique → CEO | Contrainte CHECK + routage déterministe : ces classes ne peuvent emprunter l'arête de politique pré-approuvée |
| Seuils fixés par le CEO seul | `PUT /v1/config/bounds/{key}` exige `ceo` + versionnage + événement signé |
| Conseil Stratégique activé par le CEO | `activate` exige `ceo` ; l'Orchestrateur ne peut que créer une **proposition** |
| Audit immuable | Privilèges SQL (pas d'UPDATE/DELETE) + chaînage de hachés + vérification périodique |
| Tout doute → CEO | Défaut conservateur codé dans le moteur de politiques (classe élevée, validation CEO) |

## Modèle de menace technique

Reprise des menaces de [`../behavior/14-integrity-and-threat-model.md`](../behavior/14-integrity-and-threat-model.md), avec le contrôle porteur :

| Menace | Contrôle technique |
| --- | --- |
| Complaisance / collusion d'agents | Diversité du contrôle indépendant (avocat du diable, verificateurs distincts) ; journalisation des votes ; backstop → CEO |
| Prompt injection via une demande entrante | Séparation instructions/données, sandbox des outils, filtrage des entrées, egress restreint |
| Exfiltration par un agent | Egress contrôlé par manifest ; aucun secret dans les prompts ; portées mémoire minimales |
| Compromission du compte CEO | MFA, journal des connexions, confirmation renforcée pour les actions critiques |
| Altération de l'audit | Append-only + chaîne de hachés + vérification périodique + privilèges restreints |
| Escalade de privilège d'un compte de service | Jetons courts, portée minimale, aucun chemin vers les endpoints `ceo` |

## Secrets et données

- **Secrets** : gestionnaire de secrets / variables d'environnement ; **jamais** en base ni dans les prompts ; rotation régulière.
- **Chiffrement** : TLS en transit ; chiffrement au repos des schémas et du stockage objet ([`./06-storage-strategy.md`](./06-storage-strategy.md)).
- **Minimisation** : réduire les données personnelles collectées et journalisées ; pas de contenu sensible en clair dans les logs.

## Justification des choix

- **OIDC/JWT plutôt qu'une authentification maison** : standard éprouvé, MFA délégable à un fournisseur d'identité, pas de gestion de mots de passe en propre — la surface de compromission de l'unique humain doit être minimale.
- **Comptes de service à jetons courts plutôt que clés longues** : limite la fenêtre d'exploitation d'un jeton fuité ; aligné sur le moindre privilège.
- **Permissions dans le manifest d'agent plutôt qu'en dur dans le code** : rend les permissions auditables, versionnées et modifiables par gouvernance (décision du CEO), sans redéploiement.
- **Contrôles doublés (endpoint + schéma)** : un invariant aussi central que « aucun agent ne décide » ne doit pas reposer sur une seule barrière ; la contrainte SQL tient même si une erreur applicative laisse passer un appel.
- **RBAC minimal plutôt qu'un système de rôles riche** : avec un seul humain, la complexité d'un RBAC étendu serait une surface de bug inutile ; la simplicité est ici une propriété de sécurité.

## Questions ouvertes (CEO)

1. **Entérinement de DT-07** (OIDC/JWT, RBAC minimal, permissions par manifest, audit chaîné) — future décision 017+.
2. **Fournisseur d'identité** pour l'OIDC du CEO et politique MFA.
3. **Gestion des clés** (KMS interne vs service géré) pour le chiffrement au repos.
4. **Périmètre du rôle `auditor-ro`** : usage interne uniquement, ou exposable à un outil tiers de revue.
5. **Politique de confirmation renforcée** : quelles actions du CEO exigent une double confirmation (retrait d'agent, suspension de politique, modification de borne critique).
