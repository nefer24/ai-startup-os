# docs/release — Revues de release readiness (Voie A post-C0)

Ce répertoire contient les **revues de préparation à la release** produites pendant la Voie A post-C0
(phase de stabilisation / release readiness). Ces documents **préparent et cadrent** des décisions de
release ; ils **n'exécutent** aucune promotion ni action Git.

## Contenu

- **`C0-RELEASE-1-MAIN-PROMOTION-READINESS.md`** — source Markdown du lot **A1 — C0-RELEASE.1 Main
  Promotion Readiness** : revue de préparation à la promotion éventuelle de `develop` vers `main`.
  Elle vérifie, documente et recommande ; elle **ne promeut pas**.
- **`C0-RELEASE-1-MAIN-PROMOTION-READINESS.pdf`** — artefact PDF officiel exporté depuis la source
  Markdown.

> Le **Markdown est la source de vérité** ; le **PDF est l'artefact officiel**. En cas de divergence,
> la source Markdown fait foi et le PDF doit être régénéré.

## Statut à la rédaction de A1

- **C0 :** clôturé. **Voie A post-C0 :** ouverte. **A0 (VOIE-A-OPENING) :** fusionné.
- **C1 :** non ouvert. **E9 :** fermé.
- **Source de vérité :** `develop`. **`main` :** **non promu** (readiness préparée, pas exécutée).
- **A1 :** préparation, pas promotion. La promotion `develop → main` reste une **décision et une
  action CEO futures**.

## Méthode de génération du PDF

Le PDF est généré à partir de la source Markdown via la chaîne **Markdown → HTML (avec CSS
d'impression) → PDF (WeasyPrint, pur Python)**. Pour régénérer le PDF après modification de la source,
réappliquer la même chaîne de conversion.
