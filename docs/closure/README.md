# docs/closure — Revues officielles de clôture

Ce répertoire contient les **documents officiels de clôture** des phases du programme AI-SOS.

## Contenu

- **`C0-OFFICIAL-CLOSURE-REVIEW.md`** — source Markdown de la **revue officielle de clôture C0**
  (consolidation du socle E1–E8). Document de clôture et **aide à la décision** : il documente et
  recommande, il **ne décide pas** à la place du CEO.
- **`C0-OFFICIAL-CLOSURE-REVIEW.pdf`** — artefact PDF officiel exporté depuis la source Markdown.

> Le **Markdown est la source de vérité** ; le **PDF est l'artefact officiel** de clôture. En cas de
> divergence, la source Markdown fait foi et le PDF doit être régénéré.

## Statut à la clôture de C0

- Phase **C0 complète** (C0.1 → C0.9 + C0.R mergés dans `develop`).
- **E9 : fermé.**
- Aucune décision de direction prise dans ce lot : les options (Voie A — stabiliser/release ;
  Voie B — ouvrir la phase produit C1/E9) sont présentées ; **la décision appartient au CEO**.

## Méthode de génération du PDF

Le PDF est généré à partir de la source Markdown via une conversion **Markdown → HTML (avec CSS
d'impression) → PDF**. L'outil de rendu utilisé pour cette clôture est **WeasyPrint** (HTML/CSS → PDF,
pur Python), après un rendu Markdown par la bibliothèque `markdown`. Pour régénérer le PDF après une
modification de la source, réappliquer la même chaîne de conversion.
