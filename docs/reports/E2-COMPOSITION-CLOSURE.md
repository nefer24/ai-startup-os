# Clôture officielle de E2 (composition gouvernée) — Ouverture de E3

> **Statut** : décision officielle du CEO, ratifiée après revue indépendante d'Orion.
> **Date** : 2026-07-04.
> **Nature** : jalon de gouvernance. Aucun développement technique — formalisation administrative
> de la transition E2 → E3.
> **Référence** : Revue officielle de clôture de E2 (verdict ✅, recommandation de clôturer E2).

---

## 1. Décision du CEO

Après lecture complète de la Revue officielle de clôture de E2, examen des recommandations et revue
indépendante du Chief AI Architect (Orion), le CEO décide :

> ## ✅ E2 est officiellement clôturé. ✅ E3 est officiellement ouvert.

La revue démontre de manière satisfaisante que : le **contrat de capacité** est désormais une
fondation stable ; le **registre de capacités** est passif, déterministe et conforme à son rôle ;
la **composition gouvernée** est construite et validée ; l'**instanciation auditée sous politique
pré-approuvée** est correctement intégrée ; les **huit principes de construction** sont respectés ;
**aucune responsabilité appartenant à E3 n'a été anticipée** ; le **cerveau reste une capacité de
référence gelée** ; l'**orchestrateur reste un coordinateur gouverné** ; et le **CEO demeure
l'unique autorité décisionnelle**.

## 2. Décisions officielles

1. **E2 est officiellement verrouillé.**
2. **Les contrats établis pendant E2 sont gelés comme fondation de référence** (§3). Toute évolution
   future de ces contrats devra respecter cette fondation et **ne pourra être réalisée que par une
   décision explicite du CEO**.
3. **Les dettes des étages futurs restent affectées à leurs propriétaires**, conformément au
   principe de **Debt Ownership** (cf.
   [`../consolidation/01-TECHNICAL-DEBT.md`](../consolidation/01-TECHNICAL-DEBT.md)). En
   particulier, la *variance* de composition (produire des organisations différentes selon le
   problème) n'est **pas une dette de E2** : le mécanisme est complet et prouvé ; c'est une
   propriété que **E3 débloquera** en enrichissant le catalogue.
4. **E3 devient officiellement l'étape active du projet.** À partir de ce jalon, **toutes les
   futures PR relèvent de E3** — l'évolution gouvernée des capacités (création/dépréciation sous
   décision CEO) et le Conseil Stratégique qui la recommande.

## 3. Contrats de référence de E2 (périmètre gelé)

E2 est figé dans l'état suivant, qui constitue la **fondation de composition** d'AI-SOS. Chaque
contrat est déterministe, prouvé par test et sans effet de bord.

| Contrat | Rôle figé | Garantie | Preuve |
| --- | --- | --- | --- |
| **Contrat de capacité** (`orchestrator/capability.py`) | Une capacité **EST** un `DeliberationPort` doté d'un `descriptor` ; elle recommande, ne décide ni ne gouverne jamais | Immuable, `@runtime_checkable`, n'importe pas `aisos.agents` | `test_capability_contract.py` (11) |
| **Registre de capacités** (`orchestrator/registry.py`) | Catalogue **passif**, en lecture seule, déterministe (ordre d'insertion), identifiants uniques | Aucune API de mutation/sélection ; retours immuables | `test_capability_registry.py` (12) |
| **Composition déterministe** (`orchestrator/composition.py`) | Fonction **pure** : problème + registre ⇒ organisation ; sélectionne uniquement des capacités présentes | N'importe ni `aisos.audit`/`aisos.events`, ni `aisos.agents` | `test_deterministic_composition.py` (11) |
| **Instanciation gouvernée** (`orchestrator/instantiation.py`) | Instancie une organisation **connue** sous **politique CEO pré-approuvée** et **avec audit** ; n'exécute pas | Refus déterministe si politique non approuvée ; audit chaîné ; réutilise les primitives existantes | `test_governed_instantiation.py` (11) |

**La double frontière est posée et gelée** : l'**instanciation déléguée** (sous politique
pré-approuvée) appartient à l'orchestrateur (E2.4) ; la **création gouvernée** d'une capacité
(décision CEO) appartient à E3. E2 fait la première, jamais la seconde.

**Composants figés** : `src/aisos/orchestrator/capability.py`, `registry.py`, `composition.py`,
`instantiation.py`. Ces modules deviennent des **références stables** : toute capacité créée en E3
devra s'y conformer, et le chemin composition → instanciation les consommera sans les modifier.

## 4. Preuves à la clôture

| Contrôle | Résultat |
| --- | --- |
| Tests propres à E2 | ✅ **45 passent** (contrat 11 · registre 12 · composition 11 · instanciation 11) |
| Tests de gouvernance | ✅ **120 passent** (aucune régression du noyau) |
| Suite complète | ✅ **565 passent** |
| Typage / Lint | ✅ `mypy` strict (100 fichiers) · `ruff` + `format` · CI verte |
| Cerveau gelé | ✅ `src/aisos/agents/` inchangé depuis la purification (PR #62) |
| Gouvernance non déplacée | ✅ `capability.py` / `registry.py` / `composition.py` n'importent ni audit, ni événements, ni cerveau ; seule l'instanciation réutilise l'`AuditEngine` et la `PreapprovedPolicy` existants |

## 5. Cadre permanent applicable à toute évolution future

À partir de ce jalon, **toute** évolution respecte, sans exception :

1. **La Vision d'AI-SOS** et **la Constitution** ([`../00-vision.md`](../00-vision.md)).
2. **Le Cahier des charges de construction** — plan séquentiel E0 → E7 ; on ne monte pas d'un étage
   tant que le précédent n'est pas terminé et validé.
3. **La Discipline de développement** — les **huit principes** appliqués à toute proposition :
   *Vision Alignment · Responsibility Boundary · Construction Sequence · Dependency Justification ·
   Debt Ownership · Purpose of the Stage · Contract to Future Stages · New Capabilities Enabled*.
4. **Le principe de Debt Ownership** — une dette ne se traite que lorsque **son** étape est ouverte.
5. **Le contrat de référence du cerveau** (E1) — figé ; évolution réservée à une décision explicite
   du CEO.
6. **Les contrats de référence de E2** (§3) — figés ; évolution réservée à une décision explicite
   du CEO.

## 6. Prochaine étape active : E3 — Évolution gouvernée des capacités

E3 est ouvert. Son objet : faire passer AI-SOS d'un catalogue **fixe** à un catalogue qui **évolue
sous gouvernance**. E3 introduira la **création gouvernée d'une capacité** (décision CEO, auditée),
la **dépréciation** d'une capacité, et le **Conseil Stratégique** — instance consultative,
exclusivement composée d'agents IA, qui recommande ces évolutions sans jamais décider. C'est aussi
l'étage qui rendra démontrable la **variance** de composition (des organisations différentes selon
le problème), désormais possible dès que le catalogue comptera plusieurs capacités. E3 s'appuiera
**intégralement** sur les contrats figés de E2 (§3), sans les rouvrir.

**Pourquoi E3 ne peut commencer qu'après E2 :** on ne fait évoluer que ce qui existe. Créer une
capacité n'a de sens qu'avec un **contrat** (E2.1) auquel se conformer et un **registre** (E2.2) où
l'inscrire ; elle n'a de valeur que si une **composition** (E2.3) peut la mobiliser et une
**instanciation gouvernée** (E2.4) la déployer sous politique. La frontière *instancier / créer*
devait être posée (E2.4) avant d'être franchie (E3). E2 verrouillé, E3 devient possible.

---

*Jalon enregistré par la présente PR documentaire de gouvernance. Aucun développement technique.
Le CEO reste seul décideur ; cette PR officialise sa décision.*
