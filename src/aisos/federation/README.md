# `aisos.federation` — La fédération gouvernée (E6)

La fédération **coordonne** plusieurs organisations intelligentes autonomes ; elle ne remplace pas,
ne fusionne pas, et ne décide jamais à la place des CEOs. Chaque organisation conserve son CEO, son
orchestrateur, son audit, sa mémoire et son raisonnement ; **l'information peut circuler sous
consentement gouverné, mais le pouvoir de décision reste toujours local.** Aucun super-CEO, aucun
super-orchestrateur, aucune autorité centrale.

## Périmètre gelé — contrats de référence (E6 clôturé)

L'étape **E6 (la fédération gouvernée)** est officiellement close. Les contrats produits par E6 sont
**gelés** et constituent la **fondation de pluralité gouvernée** d'AI-SOS — des références stables sur
lesquelles E7 (auto-évolution gouvernée) s'appuiera sans les rouvrir. Chacun est une **donnée
immuable** (Pydantic `ImmutableModel`, frozen), **sans pouvoir** : aucune méthode de décision, de
gouvernance, d'écriture, de raisonnement ni d'intégration.

- **Identité fédérable** (`identity.py`) : `FederatedOrganizationIdentity` / `FederationStatus`
  représentent une organisation autonome comme participante fédérable ; identité **immuable**
  rattachée à son **CEO local** (autorité non-CEO refusée) ; aucune coordination, aucun pouvoir
  fédéral (`tests/unit/test_federated_organization_identity.py`).
- **Consentement** (`consent.py`) : `FederationConsent` / `DirectionalConsent` (+ `ArtifactType`,
  `ConsentDirection`, `ConsentStatus`) enregistrent le **consentement gouverné des deux côtés** —
  source à exposer, destination à recevoir, **distincts**, chacun porté par son **CEO local** ; aucune
  transmission, aucun échange (`tests/unit/test_federation_governed_consent.py`).
- **Exposition** (`exposure.py`) : `ExposableFederatedArtifact` / `ExposureStatus` — la **source**
  déclare un artefact exposable **sous consentement source** ; aucune transmission ; **jamais le
  contenu réel** (référence / résumé contrôlé) (`tests/unit/test_federated_artifact_exposure.py`).
- **Réception** (`reception.py`) : `ReceivedFederatedArtifact` / `ReceptionStatus` — la **destination**
  déclare une réception comme **entrée informationnelle** **sous consentement destination** ; **aucune
  intégration** mémoire/audit/catalogue, aucun raisonnement déclenché
  (`tests/unit/test_federated_artifact_reception.py`).
- **Coordination** (`coordination.py`) : `GovernedFederatedCoordination` / `CoordinationStatus` — un
  **lien vérifiable** entre exposition et réception (cohérence source/destination/consentement/type/
  statuts) ; **jamais une autorité** : elle constate, ne gouverne pas
  (`tests/unit/test_governed_federated_coordination.py`).
- **Consultation** (`consultation.py`) : `GovernedFederatedConsultation` / `ConsultationStatus` — une
  **lecture informationnelle** d'un artefact coordonné, liée à une coordination valide ; **aucune
  intégration, aucune décision, aucun raisonnement automatique**
  (`tests/unit/test_governed_federated_consultation.py`).

**Frontière information / pouvoir figée** : l'**information circule** (identités, consentements,
artefacts exposés/reçus, coordinations, consultations) ; **le pouvoir ne circule jamais**. Chaque
organisation reste **souveraine** — son CEO est seul décideur, son audit / sa mémoire / son
raisonnement lui sont propres ; les organisations restent **distinctes** (aucune fusion). **La
fédération coordonne — elle ne remplace pas, ne fusionne pas, ne décide pas à la place des CEOs.**

**Toute évolution future de ces contrats doit respecter cette fondation de référence et ne peut être
réalisée que par une décision explicite du CEO.** Voir
[`../../../docs/reports/E6-FEDERATION-CLOSURE.md`](../../../docs/reports/E6-FEDERATION-CLOSURE.md).
