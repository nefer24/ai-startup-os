"""Consolidation robuste et scalable des options atomiques (incrément 2, audits v1.2 B2 / v1.3
B6-B8).

Propriété garantie : **une inflation d'options atomiques ne provoque jamais un appel LLM
monolithique** et **la nature (`kind`) est un signal de structuration, pas une frontière
non révisable**. La chaîne est :

1. **précompression déterministe** — les options dont le libellé normalisé est identique et dont
   les natures sont *compatibles* sont fusionnées avant tout appel ; le groupe conserve ses
   natures d'origine (`source_kinds`) ;
2. **lots bornés inter-natures** — les groupes sont triés par libellé (les formulations voisines
   de natures différentes sont adjacentes) puis découpés en lots de taille bornée, soumis au
   greffier sous une représentation compacte (`identifiant : libellé [nature]`) ;
3. **méta-consolidation** — si plusieurs lots ont été nécessaires, une passe bornée fusionne les
   familles équivalentes issues de lots différents, y compris entre natures compatibles ;
4. **nature canonique** — chaque famille porte `canonical_kind` (déclarée par le greffier si elle
   figure parmi les natures d'origine, sinon la plus fréquente) et `source_kinds` (trace).

Garde déterministe : une famille ne réunit **jamais** une stratégie d'action (`build`, `buy`,
`integrate`, `simplify`, `test`) et une stratégie de non-action (`wait`, `do_nothing`) — « agir »
et « ne rien faire / différer » restent distincts ; `other` est compatible avec tout. Entre deux
natures d'action, le jugement est sémantique et revient au greffier (acheter ≠ construire quand
cela change dépendances, coût ou contrôle : c'est à lui de le dire).

Ce module est **déterministe** (aucun appel LLM). L'orchestrateur (`app.missions`) fait les appels
sous budget, borne les relances (une par lot, journalisée) et n'emploie **jamais** le repli
« chaque option devient une famille » après une erreur : un lot irrécupérable laisse ses options
**non consolidées**, le statut devient `failed` et la porte qualité bloque la recommandation.

Le module fournit aussi les **exigences de couverture stratégique** de la comparaison (B7) : les
familles qu'aucune tentative — initiale ou relance — ne peut sacrifier, déduites de données déjà
présentes dans le pipeline (natures, désaccords internes, citation dans la demande, dimensions
critiques, non-action), jamais de mots-clés métier.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Any

from app.mission_schemas import ConsolidationOutput

CONSOLIDATION_BATCH_SIZE = 16
META_CHUNK_SIZE = 32
SHORT_LABEL_CHARS = 90
ACTION_KINDS = frozenset({"build", "buy", "integrate", "simplify", "test"})
NON_ACTION_KINDS = frozenset({"wait", "do_nothing"})
WILDCARD_KIND = "other"
_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_SPACES = re.compile(r"\s+")


def normalize_label(text: str) -> str:
    """Forme canonique d'un libellé : minuscules, sans accents ni ponctuation, espaces réduits."""
    stripped = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in stripped if not unicodedata.combining(c))
    stripped = _PUNCT.sub(" ", stripped.lower())
    return _SPACES.sub(" ", stripped).strip()


def short_label(text: str, limit: int = SHORT_LABEL_CHARS) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def kinds_compatible(a: str, b: str) -> bool:
    """Deux natures peuvent-elles appartenir à une même famille ? (garde déterministe)"""
    if a == b or WILDCARD_KIND in (a, b):
        return True
    return (a in NON_ACTION_KINDS) == (b in NON_ACTION_KINDS)


def canonical_kind(source_kinds: list[str], declared: str = "") -> str:
    """Nature canonique : la nature déclarée si elle est d'origine, sinon la plus fréquente."""
    concrete = [k for k in source_kinds if k != WILDCARD_KIND]
    if declared and declared != WILDCARD_KIND and declared in source_kinds:
        return declared
    if not concrete:
        return WILDCARD_KIND
    counts = Counter(concrete)
    best = max(counts.values())
    return next(k for k in concrete if counts[k] == best)


def premerge_options(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fusion déterministe des doublons exacts (même libellé normalisé, natures compatibles).

    Retourne des **groupes** : `group_id`, `member_ids`, `source_kinds` (ordre d'apparition),
    `kind` (canonique), `label` (court), `expert_ids`. Un groupe à un membre est une option
    ordinaire. Deux libellés identiques de natures incompatibles restent deux groupes.
    """
    groups: list[dict[str, Any]] = []
    index: dict[str, list[dict[str, Any]]] = {}
    for o in options:
        key = normalize_label(o["label"])
        target = None
        for g in index.get(key, []):
            # Fusion déterministe seulement si les natures sont égales ou si l'une est `other` :
            # deux natures concrètes différentes sous un même libellé (acheter / construire…)
            # restent deux groupes, adjacents dans le même lot, et c'est au greffier de juger.
            if all(k == o["kind"] or WILDCARD_KIND in (k, o["kind"]) for k in g["source_kinds"]):
                target = g
                break
        if target is None:
            target = {
                "group_id": o["option_id"],
                "member_ids": [],
                "source_kinds": [],
                "kind": o["kind"],
                "label": short_label(o["label"]),
                "expert_ids": [],
                "dimensions": [],
            }
            groups.append(target)
            index.setdefault(key, []).append(target)
        target["member_ids"].append(o["option_id"])
        if o["kind"] not in target["source_kinds"]:
            target["source_kinds"].append(o["kind"])
        if o["expert_id"] not in target["expert_ids"]:
            target["expert_ids"].append(o["expert_id"])
        if o.get("dimension") and o["dimension"] not in target["dimensions"]:
            target["dimensions"].append(o["dimension"])
    for g in groups:
        g["kind"] = canonical_kind(g["source_kinds"])
    return groups


def plan_batches(
    groups: list[dict[str, Any]], batch_size: int = CONSOLIDATION_BATCH_SIZE
) -> list[list[dict[str, Any]]]:
    """Lots bornés inter-natures : groupes triés par libellé puis nature, découpés en lots.

    Un seul groupe au total = aucune consolidation à faire (famille directe, sans appel).
    """
    if len(groups) <= 1:
        return []
    ordered = sorted(groups, key=lambda g: (normalize_label(g["label"]), g["kind"]))
    size = max(2, batch_size)
    return [ordered[i : i + size] for i in range(0, len(ordered), size)]


def plan_consolidation(
    options: list[dict[str, Any]], batch_size: int = CONSOLIDATION_BATCH_SIZE
) -> dict[str, int]:
    """Plan d'appels (sans relance) : lots + passes de méta-consolidation.

    `nominal` = lots + méta ; `worst_case` = nominal + 2 par lot (une relance scindée par lot, au
    plus) — la méta-passe ne se relance pas. Sert à réserver le pire cas borné du cœur (B8).
    """
    groups = premerge_options(options)
    batches = plan_batches(groups, batch_size)
    meta = 0
    if len(batches) > 1:
        # Familles au pire = nombre de groupes ; méta en tranches bornées.
        meta = max(1, -(-len(groups) // META_CHUNK_SIZE))
    nominal = len(batches) + meta
    return {
        "groups": len(groups),
        "batches": len(batches),
        "meta": meta,
        "nominal": nominal,
        "max_retries": len(batches),
        "worst_case": nominal + 2 * len(batches),
    }


def estimate_consolidation_calls(
    options: list[dict[str, Any]], batch_size: int = CONSOLIDATION_BATCH_SIZE
) -> int:
    """Nombre d'appels planifiés pour consolider (lots + méta-passes), sans relance."""
    return plan_consolidation(options, batch_size)["nominal"]


def build_batch_prompt(items: list[dict[str, Any]]) -> str:
    """Prompt compact d'un lot : identifiant : libellé court [natures d'origine]."""
    lines = [
        "Options atomiques (identifiant : libellé [nature(s) déclarée(s)]). La nature est un "
        "signal, pas une frontière : deux formulations substantiellement identiques de natures "
        "différentes forment UNE famille (indique alors la nature canonique) ; « agir » et "
        "« ne rien faire / différer » restent toujours distincts, de même que des stratégies "
        "réellement opposées (immédiat vs différé, refonte complète vs correctif minimal, acheter "
        "vs construire quand cela change dépendances, coût ou contrôle)."
    ]
    for g in items:
        dup = (
            f" (x{len(g['member_ids'])} formulations identiques)"
            if len(g["member_ids"]) > 1
            else ""
        )
        lines.append(f"- {g['group_id']} : {g['label']} [{'/'.join(g['source_kinds'])}]{dup}")
    lines += [
        "",
        "Regroupe uniquement les options réellement équivalentes ; conserve les variantes et les "
        "désaccords internes ; indique les non-fusions motivées. Utilise exactement les "
        "identifiants ci-dessus. Aucun résumé libre : JSON compact.",
    ]
    return "\n".join(lines)


def build_meta_prompt(families: list[dict[str, Any]]) -> str:
    """Prompt compact de méta-consolidation : familles issues de lots différents."""
    lines = [
        "Familles issues de lots séparés (identifiant : libellé [nature canonique], nombre "
        "d'options). Fusionne uniquement les familles réellement équivalentes, y compris entre "
        "natures compatibles ; « agir » et « ne rien faire / différer » restent distincts."
    ]
    for f in families:
        lines.append(
            f"- {f['temp_id']} : {f['label']} [{f['kind']}] ({len(f['option_ids'])} option(s))"
        )
    lines += [
        "",
        "Les identifiants sont ceux des familles. Conserve les autres telles quelles. "
        "JSON compact, sans résumé libre.",
    ]
    return "\n".join(lines)


def _family(
    label: str,
    parts: list[dict[str, Any]],
    *,
    declared_kind: str,
    variants: list[dict[str, str]],
    internal: list[str],
    source: str,
) -> dict[str, Any]:
    source_kinds: list[str] = []
    for p in parts:
        for k in p.get("source_kinds", [p.get("kind", WILDCARD_KIND)]):
            if k not in source_kinds:
                source_kinds.append(k)
    return {
        "label": short_label(label),
        "kind": canonical_kind(source_kinds, declared_kind),
        "source_kinds": source_kinds,
        "option_ids": [m for p in parts for m in p.get("member_ids", p.get("option_ids", []))],
        "group_ids": [g for p in parts for g in p.get("group_ids", [p.get("group_id")]) if g],
        "dimensions": list(dict.fromkeys(d for p in parts for d in p.get("dimensions", []) if d)),
        "variants": variants,
        "internal_disagreements": list(dict.fromkeys(internal)),
        "source": source,
    }


def _split_incompatible(
    label: str,
    parts: list[dict[str, Any]],
    *,
    declared_kind: str,
    variants: list[dict[str, str]],
    internal: list[str],
    source: str,
    notes: list[str],
) -> list[dict[str, Any]]:
    """Garde : une famille mêlant action et non-action est scindée (journalisé)."""
    action = [p for p in parts if p["kind"] in ACTION_KINDS]
    non_action = [p for p in parts if p["kind"] in NON_ACTION_KINDS]
    wild = [p for p in parts if p["kind"] not in ACTION_KINDS | NON_ACTION_KINDS]
    if not action or not non_action:
        return [
            _family(
                label,
                parts,
                declared_kind=declared_kind,
                variants=variants,
                internal=internal,
                source=source,
            )
        ]
    notes.append(f"famille « {label} » scindée : action et non-action ne se fusionnent pas")
    out = []
    for sub in (action + wild, non_action):
        ids = {m for p in sub for m in p.get("member_ids", p.get("option_ids", []))}
        out.append(
            _family(
                label,
                sub,
                declared_kind=declared_kind,
                variants=[v for v in variants if v["option_id"] in ids],
                internal=internal,
                source=source + "+scission",
            )
        )
    return out


def families_from_batch(
    output: ConsolidationOutput, items: list[dict[str, Any]], notes: list[str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Familles d'un lot à partir de la sortie du greffier, identifiants validés.

    Les identifiants inconnus sont ignorés ; un groupe non cité par le greffier devient une famille
    à lui seul (c'est son jugement, pas un repli après erreur). Retourne (familles, non-fusions).
    """
    by_id = {g["group_id"]: g for g in items}
    assigned: set[str] = set()
    families: list[dict[str, Any]] = []
    for fam in output.families:
        gids = [i for i in fam.option_ids if i in by_id and i not in assigned]
        if not gids:
            continue
        assigned.update(gids)
        parts = [by_id[g] for g in gids]
        variants = [
            {"option_id": v.option_id, "difference": v.difference}
            for v in fam.variants
            if v.option_id in gids
        ]
        families += _split_incompatible(
            fam.label or parts[0]["label"],
            parts,
            declared_kind=fam.kind,
            variants=variants,
            internal=list(fam.internal_disagreements),
            source="greffier",
            notes=notes,
        )
    for g in items:
        if g["group_id"] not in assigned:
            families.append(
                _family(
                    g["label"],
                    [g],
                    declared_kind=g["kind"],
                    variants=[],
                    internal=[],
                    source="greffier_non_rattachee",
                )
            )
    not_merged = [
        {"option_ids": [i for i in n.option_ids if i in by_id], "reason": n.reason}
        for n in output.not_merged_because
        if any(i in by_id for i in n.option_ids)
    ]
    return families, not_merged


def merge_families_from_meta(
    output: ConsolidationOutput, families: list[dict[str, Any]], notes: list[str]
) -> list[dict[str, Any]]:
    """Applique une méta-consolidation : fusion de familles équivalentes (natures compatibles)."""
    by_temp = {f["temp_id"]: f for f in families}
    assigned: set[str] = set()
    merged: list[dict[str, Any]] = []
    for fam in output.families:
        tids = [i for i in fam.option_ids if i in by_temp and i not in assigned]
        if not tids:
            continue
        assigned.update(tids)
        parts = [by_temp[t] for t in tids]
        merged += _split_incompatible(
            fam.label or parts[0]["label"],
            parts,
            declared_kind=fam.kind,
            variants=[v for p in parts for v in p["variants"]],
            internal=[d for p in parts for d in p["internal_disagreements"]]
            + list(fam.internal_disagreements),
            source="greffier+meta" if len(parts) > 1 else parts[0]["source"],
            notes=notes,
        )
    for f in families:
        if f["temp_id"] not in assigned:
            merged.append({k: v for k, v in f.items() if k != "temp_id"})
    return merged


def direct_family(group: dict[str, Any]) -> dict[str, Any]:
    """Famille d'un groupe unique (aucun autre groupe à consolider) : aucun appel nécessaire."""
    return _family(
        group["label"],
        [group],
        declared_kind=group["kind"],
        variants=[],
        internal=[],
        source="seule_option",
    )


def finalize_families(
    families: list[dict[str, Any]], options: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Numérote les familles (F1…), ajoute soutiens et natures, construit la trace atomique."""
    by_option = {o["option_id"]: o for o in options}
    final: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []
    for i, f in enumerate(families, start=1):
        fid = f"F{i}"
        variant_ids = {v["option_id"] for v in f.get("variants", [])}
        group_ids = set(f.get("group_ids", []))
        source_kinds = list(
            dict.fromkeys(
                [by_option[o]["kind"] for o in f["option_ids"] if o in by_option]
                + list(f.get("source_kinds", []))
            )
        )
        final.append(
            {
                "family_id": fid,
                "label": f["label"],
                "kind": f["kind"],
                "canonical_kind": f["kind"],
                "source_kinds": source_kinds,
                "option_ids": list(f["option_ids"]),
                "variants": list(f.get("variants", [])),
                "internal_disagreements": list(f.get("internal_disagreements", [])),
                "supporting_experts": sorted(
                    {by_option[o]["expert_id"] for o in f["option_ids"] if o in by_option}
                ),
                "dimensions": sorted(
                    {by_option[o].get("dimension", "") for o in f["option_ids"] if o in by_option}
                    - {""}
                ),
                "source": f.get("source", "greffier"),
            }
        )
        for oid in f["option_ids"]:
            role = (
                "variant"
                if oid in variant_ids
                else ("member" if (oid in group_ids or not group_ids) else "premerged_duplicate")
            )
            trace.append({"option_id": oid, "family_id": fid, "role": role})
    return final, trace


# --- Comparaison : couverture stratégique et sélection stratifiée --------------------------------
COMPARISON_MAX_FAMILIES = 12


def _cited(label: str, normalized_text: str) -> bool:
    """Le libellé apparaît-il, mot pour mot, dans un texte normalisé de la demande ?"""
    key = normalize_label(label)
    if len(key) < 3:
        return False
    return re.search(rf"(?<!\w){re.escape(key)}(?!\w)", normalized_text) is not None


def coverage_requirements(
    families: list[dict[str, Any]],
    *,
    request_texts: list[str],
    critical_dimensions: set[str],
) -> dict[str, Any]:
    """Exigences de couverture stratégique de la comparaison (B7, révisé B9).

    Deux concepts distincts — c'est la correction B9 :

    * **hard** — familles dont la présence *individuelle* est indispensable : stratégies citées mot
      pour mot dans la demande / le cadrage / la préférence CEO (ce que le CEO demande de comparer),
      et un désaccord interne *unique* qui disparaîtrait autrement ;
    * **requirements** — contraintes de *représentation*, satisfaites par AU MOINS une famille
      appropriée : chaque nature canonique, chaque dimension présumée critique, la non-action /
      attente, les minorités matérielles (par nature), un désaccord interne, une stratégie
      multi-dimensionnelle. Appartenir à un tel groupe ne rend **pas** une famille obligatoire.

    Les candidats de chaque exigence sont ordonnés par un ordre lexicographique déterministe et
    documenté (pas un score) : désaccord interne, portée multi-dimensions, nombre de soutiens,
    identifiant. Tout est déduit de données déjà présentes dans le pipeline : aucun mot-clé métier.
    """
    hard: dict[str, list[str]] = {}
    texts = [normalize_label(t) for t in request_texts if t and t.strip()]

    def _pref(f: dict[str, Any]) -> tuple[int, int, int, int]:
        return (
            0 if f.get("internal_disagreements") else 1,
            -len(set(f.get("dimensions", []))),
            -len(f.get("supporting_experts", [])),
            int(f["family_id"][1:]),
        )

    for f in families:
        labels = [f["label"], *f.get("option_labels", [])]
        if any(_cited(lab, t) for lab in labels for t in texts):
            hard.setdefault(f["family_id"], []).append("citée dans la demande ou le cadrage")
    with_disagreement = [f for f in families if f.get("internal_disagreements")]
    if len(with_disagreement) == 1:
        fid = with_disagreement[0]["family_id"]
        hard.setdefault(fid, []).append("désaccord interne unique : disparaîtrait autrement")

    requirements: list[dict[str, Any]] = []

    def _req(req_id: str, label: str, candidates: list[dict[str, Any]]) -> None:
        if candidates:
            requirements.append(
                {
                    "id": req_id,
                    "label": label,
                    "candidates": [c["family_id"] for c in sorted(candidates, key=_pref)],
                }
            )

    kinds: list[str] = list(dict.fromkeys(f["kind"] for f in families))
    for kind in kinds:
        _req(
            f"kind:{kind}", f"nature {kind} représentée", [f for f in families if f["kind"] == kind]
        )
    for dim in sorted(critical_dimensions):
        _req(
            f"critical_dimension:{dim}",
            f"dimension critique « {dim} » représentée",
            [f for f in families if dim in set(f.get("dimensions", []))],
        )
    _req(
        "non_action",
        "non-action / attente représentée",
        [f for f in families if f["kind"] in NON_ACTION_KINDS],
    )
    minorities = [
        f
        for f in families
        if len(f.get("supporting_experts", [])) == 1
        and (
            f.get("internal_disagreements") or (set(f.get("dimensions", [])) & critical_dimensions)
        )
    ]
    for kind in list(dict.fromkeys(f["kind"] for f in minorities)):
        _req(
            f"minority:{kind}",
            f"minorité matérielle de nature {kind} représentée",
            [f for f in minorities if f["kind"] == kind],
        )
    _req("internal_disagreement", "désaccord interne représenté", with_disagreement)
    _req(
        "multi_dimension",
        "stratégie multi-dimensionnelle représentée",
        [f for f in families if len(set(f.get("dimensions", []))) >= 2],
    )
    return {"hard": hard, "requirements": requirements}


def select_families_for_attempt(
    families: list[dict[str, Any]],
    coverage: dict[str, Any],
    *,
    cap: int,
) -> dict[str, Any]:
    """Sélection stratifiée sous plafond dur (B9) : hard → couverture → facultatives.

    1. les familles *hard* sont retenues ; si elles dépassent à elles seules le plafond, le conflit
       est déclaré (`hard_conflict = True`) et **aucune** sélection normale n'est produite — la
       comparaison n'est pas réalisable sous le plafond, fail-closed ;
    2. chaque exigence de couverture est satisfaite par UNE famille (les hard comptent) : couverture
       gloutonne déterministe, en préférant à chaque pas la candidate qui satisfait le plus
       d'exigences encore ouvertes, puis l'ordre de préférence de l'exigence ; le plafond n'est
       jamais dépassé — une exigence qui ne peut plus être satisfaite est listée ;
    3. les places restantes vont aux facultatives par soutien puis identifiant.
    Retourne retenues, écartées (avec motif), la sélection expliquée famille par famille, les
    exigences avec la famille qui les satisfait, et le conflit éventuel.
    """
    by_id = {f["family_id"]: f for f in families}
    hard: dict[str, list[str]] = coverage.get("hard", {})
    requirements: list[dict[str, Any]] = coverage.get("requirements", [])
    selection: dict[str, dict[str, Any]] = {}
    if len(hard) > cap:
        return {
            "retained": [],
            "deferred": [],
            "selection": {fid: {"role": "hard", "reasons": why} for fid, why in hard.items()},
            "requirements": requirements,
            "unsatisfied": [],
            "hard_conflict": True,
            "hard_count": len(hard),
        }
    retained_ids: list[str] = []
    for fid in sorted(hard, key=lambda x: int(x[1:])):
        retained_ids.append(fid)
        selection[fid] = {"role": "hard", "reasons": list(hard[fid])}

    def _satisfied(req: dict[str, Any]) -> str | None:
        return next((c for c in req["candidates"] if c in retained_ids), None)

    for req in requirements:
        req["satisfied_by"] = _satisfied(req)
    open_reqs = [r for r in requirements if r["satisfied_by"] is None]
    while open_reqs and len(retained_ids) < cap:
        req = open_reqs[0]
        # Candidate préférée : celle qui satisfait le plus d'exigences encore ouvertes, puis
        # l'ordre de préférence propre à l'exigence (désaccord, multi-dimensions, soutien, id).
        best = max(
            req["candidates"],
            key=lambda c: (
                sum(1 for r in open_reqs if c in r["candidates"]),
                -req["candidates"].index(c),
            ),
        )
        retained_ids.append(best)
        satisfied_now = [r["id"] for r in open_reqs if best in r["candidates"]]
        selection[best] = {
            "role": "coverage",
            "reasons": [
                next(r["label"] for r in requirements if r["id"] == rid) for rid in satisfied_now
            ],
        }
        for r in open_reqs:
            if best in r["candidates"]:
                r["satisfied_by"] = best
        open_reqs = [r for r in open_reqs if r["satisfied_by"] is None]
    unsatisfied = [r["id"] for r in open_reqs]
    optional = sorted(
        [f for f in families if f["family_id"] not in retained_ids],
        key=lambda f: (
            -len(f.get("supporting_experts", [])),
            -len(f.get("option_ids", [])),
            int(f["family_id"][1:]),
        ),
    )
    for f in optional:
        if len(retained_ids) >= cap:
            break
        retained_ids.append(f["family_id"])
        selection[f["family_id"]] = {
            "role": "optional",
            "reasons": ["place disponible sous le plafond ; retenue par soutien"],
        }
    deferred = []
    for f in families:
        if f["family_id"] in retained_ids:
            continue
        reason = (
            "au-delà du plafond de familles comparées ; ni indispensable ni nécessaire à la "
            "couverture stratégique (représentée par une autre famille) ; conservée dans le "
            "rapport et la synthèse, non comparée"
        )
        selection[f["family_id"]] = {"role": "deferred", "reasons": [reason]}
        deferred.append(
            {"family_id": f["family_id"], "label": f["label"], "kind": f["kind"], "reason": reason}
        )
    retained = sorted((by_id[i] for i in retained_ids), key=lambda f: int(f["family_id"][1:]))
    return {
        "retained": retained,
        "deferred": deferred,
        "selection": selection,
        "requirements": requirements,
        "unsatisfied": unsatisfied,
        "hard_conflict": False,
        "hard_count": len(hard),
    }


def build_compact_comparison_prompt(
    *,
    problem: str,
    constraints: list[str],
    families: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    unknowns: list[str],
) -> str:
    """Prompt de comparaison sur une représentation compacte des familles retenues."""
    parts = [f"Problème compris : {short_label(problem, 400)}"]
    if constraints:
        parts.append("Contraintes : " + " ; ".join(short_label(c, 120) for c in constraints[:10]))
    parts.append("Familles stratégiques à comparer (identifiant : libellé [nature] — soutiens) :")
    for f in families:
        parts.append(
            f"- {f['family_id']} : {f['label']} [{f['kind']}] — "
            f"{len(f.get('supporting_experts', []))} soutien(s), "
            f"{len(f.get('option_ids', []))} option(s)"
            + (
                " — désaccords internes : "
                + " ; ".join(short_label(d, 80) for d in f["internal_disagreements"][:3])
                if f.get("internal_disagreements")
                else ""
            )
        )
    parts.append("Preuves disponibles :")
    if evidence:
        for e in evidence[:20]:
            parts.append(
                f"- {e['id']} {short_label(str(e.get('claim', '')), 120)} — "
                f"{e.get('provenance', '')} — source : {e.get('source') or 'aucune'} — "
                f"fiabilité {e.get('reliability', 'unknown')}"
            )
    else:
        parts.append("- aucune preuve externe")
    if unknowns:
        parts.append(
            "Inconnues restantes : " + " ; ".join(short_label(u, 80) for u in unknowns[:12])
        )
    parts += [
        "",
        "Compare CHAQUE famille listée sur les critères communs, au format JSON demandé (une ligne "
        "par famille, tous les critères renseignés, valeurs qualitatives courtes).",
    ]
    return "\n".join(parts)
