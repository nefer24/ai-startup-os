# docs/roadmap — Revues d'ouverture, roadmaps et cahiers des charges de phase

Ce répertoire contient les **documents d'ouverture officielle** et les **roadmaps** des phases du
programme AI-SOS, ainsi que leurs cahiers des charges.

## Contenu

- **`VOIE-A-POST-C0-OPENING-REVIEW.md`** — source Markdown de la **revue officielle d'ouverture de la
  Voie A post-C0** (phase de stabilisation / release readiness). Document de cadrage : il définit ce
  que la Voie A autorise, interdit, quels lots elle contient (A0→A8), avec quelles responsabilités
  uniques et quels garde-fous. **Consultatif** : la décision de direction appartient au CEO.
- **`VOIE-A-POST-C0-OPENING-REVIEW.pdf`** — artefact PDF officiel exporté depuis la source Markdown.

> Le **Markdown est la source de vérité** ; le **PDF est l'artefact officiel**. En cas de divergence,
> la source Markdown fait foi et le PDF doit être régénéré.

## Statut à l'ouverture de la Voie A

- **C0 :** clôturé (voir `docs/closure/`).
- **Voie A post-C0 :** **ouverte** (décision CEO actée).
- **C1 :** non ouvert. **E9 :** fermé.
- **Source de vérité :** `develop`. **`main` :** non promu (readiness préparée, pas exécutée).
- **Prochaine étape recommandée :** lot **A1 — C0-RELEASE.1 Main Promotion Readiness** (sous validation
  CEO).

## Méthode de génération du PDF

Le PDF est généré à partir de la source Markdown via la chaîne **Markdown → HTML (avec CSS
d'impression) → PDF (WeasyPrint, pur Python)**. Pour régénérer le PDF après une modification de la
source, réappliquer la même chaîne de conversion.
