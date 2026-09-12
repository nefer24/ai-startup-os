"""Garde déterministe « la preuve prime sur la majorité » (E1 — v1.3.6).

Constat (Holdout #9) : la synthèse a justifié sa recommandation et sa confiance d'abord par « les
15 positions convergent, sans réfutation factuelle ». Doctrine : EVIDENCE BEATS MAJORITY. La
convergence de perspectives (instances d'un même modèle sur le même dossier) est une information
descriptive, jamais une preuve de vérité ni de supériorité d'une option.

Le contrôle porte uniquement sur les champs décisionnels (`recommendation.rationale`,
`confidence.justification`). Il ne cherche pas le mot « convergence » : il cherche son USAGE comme
support de vérité ou de décision — une phrase qui réunit (1) un marqueur de consensus portant sur
des positions / perspectives / experts et (2) un connecteur de justification ou de conclusion, sans
(3) marqueur de séparation explicite entre le constat de convergence et la preuve.

Acceptable : « Plusieurs perspectives convergent vers cette hypothèse, mais la recommandation
repose principalement sur X, Y et Z. » Non acceptable : « 15 experts convergent, donc cette
stratégie est la meilleure. »
"""

from __future__ import annotations

import re
import unicodedata

_SENTENCE_SPLIT = re.compile(r"(?<=[.;!?])\s+|\s*;\s*|\n+")
_SUBJECTS = r"(positions?|perspectives?|experts?|avis|voix|participants?|angles?|contributions?)"
_QUANTIFIERS = (
    r"(\d+|toutes?|tous|l'?ensemble|la totalite|la plupart|la majorite|une majorite|la quasi"
    r"[- ]?totalite|chacune?|l'?unanimite)"
)
_CONVERGENCE_VERBS = (
    r"(convergent|converge|s'?accordent|concordent|se rejoignent|partagent|soutiennent|"
    r"rejettent|refusent|ecartent|recommandent|preferent|jugent|estiment|confirment)"
)
_CONSENSUS_PATTERNS = [
    # « 15 positions convergent », « toutes les perspectives rejettent »
    re.compile(rf"\b{_QUANTIFIERS}\s+(les\s+|des\s+)?{_SUBJECTS}\b[^.;]*\b{_CONVERGENCE_VERBS}\b"),
    # « la convergence (forte, non réfutée) des positions », « le consensus des experts »
    re.compile(
        rf"\b(convergence|consensus|unanimite|majorite|accord general)\b[^.;]{{0,60}}\b(des|"
        rf"entre|de)\s+(les\s+)?{_SUBJECTS}\b"
    ),
    # « les positions convergent » sans quantificateur explicite
    re.compile(rf"\b(les|ces)\s+{_SUBJECTS}\b[^.;]{{0,40}}\b{_CONVERGENCE_VERBS}\b"),
    re.compile(r"\b(consensus|unanimite|unanimement|majoritairement|a l'?unanimite)\b"),
]
_SUPPORT_PATTERNS = re.compile(
    r"\b(donc|par consequent|ce qui (montre|prouve|etablit|confirme|justifie|demontre)|"
    r"prouve|prouvent|demontre|demontrent|etablit|etablissent|confirme|confirment|justifie|"
    r"justifient|suffit|suffisent|garantit|garantissent|repose (sur|principalement sur)|"
    r"fonde(e|es)? sur|etay(e|ee|ees|ent)|sans refutation|non refute(e|es)?|aucune refutation|"
    r"est la meilleure|la meilleure (option|strategie|voie)|superieure?|l'?emporte|"
    r"valide la recommandation|justification (centrale|principale)|constitue la preuve|"
    r"en atteste|atteste)\b"
)
_SEPARATION_PATTERNS = re.compile(
    r"\b(independamment|a titre descriptif|signal descriptif|n'?est pas une preuve|ne (prouve|"
    r"demontre|suffit) pas|ne constitue pas une preuve|mais la recommandation repose|"
    r"la recommandation repose (principalement|d'?abord|avant tout) sur|au[- ]dela de (la|cette) "
    r"convergence|quelle que soit (la|cette) convergence|ne vaut pas preuve|sans valeur "
    r"probante|information descriptive)\b"
)


def _fold(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text or "")
    stripped = "".join(c for c in stripped if not unicodedata.combining(c))
    return " ".join(stripped.lower().replace("\u2019", "'").split())


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT.split(text or "") if s and s.strip()]


def _mentions_consensus(folded: str) -> bool:
    return any(p.search(folded) for p in _CONSENSUS_PATTERNS)


def consensus_as_evidence(text: str) -> list[str]:
    """Phrases où la convergence sert de support de vérité / de décision (liste vide = conforme).

    Une phrase est signalée si elle contient un marqueur de consensus portant sur des positions
    ET un connecteur de justification (donc, prouve, étayée, sans réfutation, la meilleure…), SANS
    marqueur de séparation (indépendamment, n'est pas une preuve, mais la recommandation repose
    sur…). Les phrases purement descriptives ne sont jamais signalées.
    """
    flagged: list[str] = []
    for sentence in _sentences(text):
        folded = _fold(sentence)
        if not _mentions_consensus(folded):
            continue
        if _SEPARATION_PATTERNS.search(folded):
            continue
        if _SUPPORT_PATTERNS.search(folded):
            flagged.append(sentence[:200])
    return flagged


def claims_superiority(text: str) -> bool:
    """La formulation prétend-elle à la supériorité d'une option (hors « test / attente ») ?"""
    folded = _fold(text)
    return (
        re.search(
            r"\b(la meilleure (option|strategie|voie|solution)|est la meilleure|"
            r"superieure? (a|aux)|l'?emporte (sur|nettement)|domine (les|toutes)|optimale?)\b",
            folded,
        )
        is not None
    )
