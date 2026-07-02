# AI Review Package

**Pull Request :** #013 — *Schemas & Event Contracts (Phase 8)*
**Branche :** `feature/schemas-event-contracts-phase8` → `develop`
**Auteur :** Claude Code (Chief Software Architect)
**Date :** 2026-07-02

## 1. Executive Summary

Cette Pull Request livre les **schémas formels et contrats d'événements d'AI-SOS** (Phase 8) : le dossier `docs/contracts/` (index + 10 documents) définissant les formats précis des entités, événements, payloads d'API, erreurs, résultats de politiques, mémoire, audit et décisions CEO, ainsi que la gouvernance de leur évolution. Les schémas sont **assez précis pour être traduits plus tard en Pydantic, OpenAPI et SQL**, mais **aucun fichier Python n'est créé**, **aucun code métier** n'est développé et **aucun choix technologique** n'est ajouté. Un **audit interne** (Conseil de Revue de cinq experts) a été mené : **score 94/100** ; à noter, **tous les exemples JSON sont valides** (contrôle automatique).

## 2. Objectifs

Fixer des contrats formels, cohérents et traduisibles, portant les invariants de gouvernance dans les schémas eux-mêmes, en respectant la Baseline v1.0 et les Phases 5–7.

## 3. Fichiers modifiés

Ajoutés (`docs/contracts/`) : `README.md`, `01-domain-schemas.md`, `02-event-catalog.md`, `03-event-versioning.md`, `04-api-schemas.md`, `05-error-catalog.md`, `06-policy-result-schema.md`, `07-memory-record-schema.md`, `08-audit-record-schema.md`, `09-human-decision-schema.md`, `10-schema-governance.md`.
Ajoutés (`reviews/packages/`) : le présent ARP et `PR-013-contracts-audit.md`.
**Aucun document du corpus gelé (Constitution, Phases 1–7) n'est modifié.**

## 4. Changements importants

- **Schémas des 7 entités** (Request, Agent, Council, Decision, Policy, Memory, AuditEvent) avec champs, types, obligatoires/optionnels, invariants et exemples JSON.
- **Catalogue officiel des événements** (enveloppe commune + 21 événements de gouvernance) et **versionnement** (`schema_version`, upcasting, coexistence).
- **Schémas d'API** (requêtes/réponses des endpoints /v1), **catalogue d'erreurs** (codes stables, http_status, retriable), **résultats du Policy Engine**, **enregistrements mémoire**, **entrées d'audit** (append-only chaîné), **décisions CEO** (4 issues + « En attente »).
- **Gouvernance des schémas** : un schéma est un contrat opposable ; l'affaiblissement d'un invariant est **irrecevable**.

## 5. Raisons des choix

- **Invariants encodés dans les schémas** : `validator ∈ {ceo, policy}`, structurante/critique ⇒ ceo, audit chaîné — la gouvernance devient une propriété du format.
- **Types logiques abstraits + exemples JSON valides** : garantissent la traduisibilité en Pydantic/OpenAPI/SQL sans imposer de code.
- **Méta-document de gouvernance (10)** : verrouille l'évolution des contrats dans le processus AI-SOS.

## 6. Alternatives étudiées

- **Écrire directement des modèles Pydantic** — rejeté : la consigne exclut le code Python ; les schémas restent des contrats descriptifs.
- **Un seul document monolithique de schémas** — rejeté : la séparation par domaine (entités, événements, API, erreurs, audit…) facilite l'évolution gouvernée.
- **Omettre le versionnement d'événements** — rejeté : l'audit immuable impose la lisibilité perpétuelle, donc un versionnement explicite.

## 7. Risques

- **Techniques :** faibles (Markdown ; exemples JSON validés).
- **De traduction :** divergence possible entre Pydantic/OpenAPI/SQL ; atténué par la méta-gouvernance (10) et les tests de conformité de schéma prévus en CI (Phase 6).
- **De calibration :** dimension d'embedding, fonction de hachage de l'audit — décisions du CEO.
- **De gouvernance :** aucun — les schémas renforcent les invariants.

## 8. Impact sur la Constitution

Aucun article modifié. Les schémas matérialisent les Articles VIII–XI (autorité unique, recommandation, gouvernance) dans des formats précis.

## 9. Impact sur l'architecture

La Phase 8 n'altère pas l'architecture ni les composants : elle en fixe les formats d'échange. Elle prépare directement la traduction future en Pydantic/OpenAPI/SQL.

## 10. Compatibilité

- **Phases 1–7 :** cohérentes ; schémas alignés sur le modèle de données (Phase 5) et les contrats de composants (Phase 7) ; renvois valides.
- **Décisions d'architecture :** conforme (001–016) ; applique l'ARP (012) et l'audit interne (013) ; DT proposées pour ratification (017+).

## 11. Tests effectués

- 10 documents + README ; sections finales (Invariants/Erreurs/Questions ouvertes) présentes dans 01–10.
- Aucun lien relatif cassé.
- **Tous les exemples JSON parsent sans erreur** (contrôle automatique).
- Titres H1 anglais, corps français ; aucune langue tierce ; aucun type Python.
- Aucun red-flag de gouvernance.
- Audit interne complet (5 experts) : voir `PR-013-contracts-audit.md`.

## 12. Checklist

- [x] Documentation ajoutée
- [x] Standards respectés (conventions de schéma uniformes)
- [x] Constitution respectée (non modifiée)
- [x] Baseline v1.0 + Phases 5–7 respectées (aucun code, aucun nouveau choix technologique)
- [x] Aucun conflit
- [x] Branche correcte (`feature/schemas-event-contracts-phase8`)
- [x] Pull Request correcte (base `develop`)

## 13. Questions ouvertes

- **Ratification des DT-01 à DT-08** (futures décisions 017+).
- **Dimension d'embedding** (07) et **fonction de hachage de l'audit** (08) à fixer par le CEO.
- **Alignement fin** des noms de champs entre Pydantic/OpenAPI/SQL à l'implémentation (tests de conformité).
- Le numéro de PR de cet ARP est **prévu à #013** ; à renommer si GitHub attribue un autre numéro.

## 14. Recommandation de Claude Code

Je recommande l'**adoption** de cette Pull Request. Elle réalise l'objectif de la Phase 8 — des schémas formels précis, cohérents et traduisibles, portant les invariants dans les contrats — sans code ni nouveau choix technologique. L'audit interne (94/100), avec des exemples JSON tous valides, confirme la solidité et la traduisibilité. Les questions ouvertes relèvent de décisions du CEO. Aucune fusion ne sera effectuée avant autorisation explicite du CEO.

## 15. Audit interne (décision 013)

Audit interne par un Conseil de Revue de cinq experts indépendants (gouvernance, cohérence des schémas, traduisibilité Pydantic/OpenAPI/SQL, erreurs/versionnement, avocat du diable). **Score : 94/100.** Rapport officiel : [`PR-013-contracts-audit.md`](./PR-013-contracts-audit.md).
