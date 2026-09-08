"""Consolidation robuste et scalable des options atomiques (incrément 2, audit v1.2 — B2).

Propriété garantie : **une inflation d'options atomiques ne provoque jamais un appel LLM
monolithique** qui tenterait de reproduire toutes les options textuellement. La chaîne est :

1. **précompression déterministe** — les options de même nature dont le libellé normalisé est
   identique (casse, accents, ponctuation, espaces) sont fusionnées avant tout appel ; chaque
   groupe est représenté par un identifiant unique, sa nature et un libellé court ;
2. **partition par nature** — une famille ne mêle jamais deux natures (`build` ≠ `buy`) : la
   consolidation sémantique n'a donc de sens qu'à l'intérieur d'une nature ; une nature à un seul
   groupe donne une famille sans appel ;
3. **lots bornés** — chaque nature est découpée en lots de taille bornée ; chaque lot est soumis
   au greffier sous une représentation compacte (`identifiant | nature | libellé court`), donc
   avec une sortie bornée ;
4. **méta-consolidation** — si une nature a nécessité plusieurs lots, une passe unique fusionne
   les familles équivalentes issues de lots différents (représentation compacte, une seule passe).

Ce module est **déterministe** (aucun appel LLM) : il prépare, valide et assemble. L'orchestrateur
(`app.missions`) fait les appels sous budget, borne les relances (une par lot, journalisée) et
n'emploie **jamais** le repli « chaque option devient une famille » après une erreur : un lot
irrécupérable laisse ses options **non consolidées**, le statut de la consolidation devient
`failed` et la porte qualité bloque la recommandation.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.mission_schemas import ConsolidationOutput

CONSOLIDATION_BATCH_SIZE = 16
SHORT_LABEL_CHARS = 90
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


def premerge_options(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fusion déterministe des doublons exacts (même nature, même libellé normalisé).

    Retourne des **groupes** : `group_id` (identifiant de la première option), `member_ids`,
    `kind`, `label` (court), `expert_ids`. Un groupe à un membre est une option ordinaire.
    """
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    order: list[tuple[str, str]] = []
    for o in options:
        key = (o["kind"], normalize_label(o["label"]))
        g = groups.get(key)
        if g is None:
            g = {
                "group_id": o["option_id"],
                "member_ids": [],
                "kind": o["kind"],
                "label": short_label(o["label"]),
                "expert_ids": [],
            }
            groups[key] = g
            order.append(key)
        g["member_ids"].append(o["option_id"])
        if o["expert_id"] not in g["expert_ids"]:
            g["expert_ids"].append(o["expert_id"])
    return [groups[k] for k in order]


def plan_batches(
    groups: list[dict[str, Any]], batch_size: int = CONSOLIDATION_BATCH_SIZE
) -> tuple[list[tuple[str, list[dict[str, Any]]]], list[dict[str, Any]]]:
    """Partition par nature puis en lots bornés.

    Retourne (`batches`, `singletons`) : `batches` = liste de (nature, groupes) à soumettre au
    greffier ; `singletons` = groupes seuls dans leur nature (famille sans appel).
    """
    by_kind: dict[str, list[dict[str, Any]]] = {}
    kinds: list[str] = []
    for g in groups:
        if g["kind"] not in by_kind:
            kinds.append(g["kind"])
        by_kind.setdefault(g["kind"], []).append(g)
    batches: list[tuple[str, list[dict[str, Any]]]] = []
    singletons: list[dict[str, Any]] = []
    size = max(2, batch_size)
    for kind in kinds:
        items = by_kind[kind]
        if len(items) == 1:
            singletons.append(items[0])
            continue
        for i in range(0, len(items), size):
            batches.append((kind, items[i : i + size]))
    return batches, singletons


def estimate_consolidation_calls(
    options: list[dict[str, Any]], batch_size: int = CONSOLIDATION_BATCH_SIZE
) -> int:
    """Nombre d'appels planifiés pour consolider (lots + méta-passes), sans relance."""
    batches, _ = plan_batches(premerge_options(options), batch_size)
    kinds_with_batches: dict[str, int] = {}
    for kind, _items in batches:
        kinds_with_batches[kind] = kinds_with_batches.get(kind, 0) + 1
    meta = sum(1 for n in kinds_with_batches.values() if n > 1)
    return len(batches) + meta


def build_batch_prompt(kind: str, items: list[dict[str, Any]]) -> str:
    """Prompt compact d'un lot : identifiant : libellé court (nature commune)."""
    lines = [
        f"Nature commune du lot : {kind}. Options atomiques (identifiant : libellé) :",
    ]
    for g in items:
        dup = (
            f" (x{len(g['member_ids'])} formulations identiques)"
            if len(g["member_ids"]) > 1
            else ""
        )
        lines.append(f"- {g['group_id']} : {g['label']}{dup}")
    lines += [
        "",
        "Regroupe uniquement les options réellement équivalentes ; conserve les variantes et les "
        "désaccords internes ; indique les non-fusions motivées. Utilise exactement les "
        "identifiants ci-dessus. Aucun résumé libre : JSON compact.",
    ]
    return "\n".join(lines)


def build_meta_prompt(kind: str, families: list[dict[str, Any]]) -> str:
    """Prompt compact de méta-consolidation : familles issues de lots différents (même nature)."""
    lines = [
        f"Nature commune : {kind}. Familles issues de lots séparés (identifiant : libellé, "
        "nombre d'options) :"
    ]
    for f in families:
        lines.append(f"- {f['temp_id']} : {f['label']} ({len(f['option_ids'])} option(s))")
    lines += [
        "",
        "Fusionne uniquement les familles réellement équivalentes (les identifiants sont ceux des "
        "familles). Conserve les autres telles quelles. JSON compact, sans résumé libre.",
    ]
    return "\n".join(lines)


def families_from_batch(
    output: ConsolidationOutput, items: list[dict[str, Any]], kind: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Familles d'un lot à partir de la sortie du greffier, identifiants validés.

    Les identifiants inconnus sont ignorés ; un groupe non cité par le greffier devient une famille
    à lui seul (le greffier ne l'a rattaché à rien : ce n'est pas un repli après erreur, c'est
    son jugement). Retourne (familles, non-fusions motivées).
    """
    by_id = {g["group_id"]: g for g in items}
    assigned: set[str] = set()
    families: list[dict[str, Any]] = []
    for fam in output.families:
        gids = [i for i in fam.option_ids if i in by_id and i not in assigned]
        if not gids:
            continue
        assigned.update(gids)
        option_ids = [m for gid in gids for m in by_id[gid]["member_ids"]]
        variants = [
            {"option_id": v.option_id, "difference": v.difference}
            for v in fam.variants
            if v.option_id in by_id and v.option_id in gids
        ]
        families.append(
            {
                "label": short_label(fam.label or by_id[gids[0]]["label"]),
                "kind": kind,
                "option_ids": option_ids,
                "group_ids": gids,
                "variants": variants,
                "internal_disagreements": list(fam.internal_disagreements),
                "source": "greffier",
            }
        )
    for g in items:
        if g["group_id"] in assigned:
            continue
        families.append(
            {
                "label": g["label"],
                "kind": kind,
                "option_ids": list(g["member_ids"]),
                "group_ids": [g["group_id"]],
                "variants": [],
                "internal_disagreements": [],
                "source": "greffier_non_rattachee",
            }
        )
    not_merged = [
        {"option_ids": [i for i in n.option_ids if i in by_id], "reason": n.reason}
        for n in output.not_merged_because
        if any(i in by_id for i in n.option_ids)
    ]
    return families, not_merged


def merge_families_from_meta(
    output: ConsolidationOutput, families: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Applique une méta-consolidation : fusion de familles équivalentes d'une même nature."""
    by_temp = {f["temp_id"]: f for f in families}
    assigned: set[str] = set()
    merged: list[dict[str, Any]] = []
    for fam in output.families:
        tids = [i for i in fam.option_ids if i in by_temp and i not in assigned]
        if not tids:
            continue
        assigned.update(tids)
        parts = [by_temp[t] for t in tids]
        merged.append(
            {
                "label": short_label(fam.label or parts[0]["label"]),
                "kind": parts[0]["kind"],
                "option_ids": [oid for p in parts for oid in p["option_ids"]],
                "group_ids": [g for p in parts for g in p["group_ids"]],
                "variants": [v for p in parts for v in p["variants"]],
                "internal_disagreements": list(
                    dict.fromkeys(
                        [d for p in parts for d in p["internal_disagreements"]]
                        + list(fam.internal_disagreements)
                    )
                ),
                "source": "greffier+meta" if len(parts) > 1 else parts[0]["source"],
            }
        )
    for f in families:
        if f["temp_id"] not in assigned:
            merged.append({k: v for k, v in f.items() if k != "temp_id"})
    return merged


def singleton_family(group: dict[str, Any]) -> dict[str, Any]:
    """Famille d'une nature qui ne compte qu'un seul groupe : aucun appel nécessaire."""
    return {
        "label": group["label"],
        "kind": group["kind"],
        "option_ids": list(group["member_ids"]),
        "group_ids": [group["group_id"]],
        "variants": [],
        "internal_disagreements": [],
        "source": "seule_de_sa_nature",
    }


def finalize_families(
    families: list[dict[str, Any]], options: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Numérote les familles (F1…), ajoute les soutiens et construit la trace atomique → famille."""
    by_option = {o["option_id"]: o for o in options}
    final: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []
    for i, f in enumerate(families, start=1):
        fid = f"F{i}"
        variant_ids = {v["option_id"] for v in f.get("variants", [])}
        final.append(
            {
                "family_id": fid,
                "label": f["label"],
                "kind": f["kind"],
                "option_ids": list(f["option_ids"]),
                "variants": list(f.get("variants", [])),
                "internal_disagreements": list(f.get("internal_disagreements", [])),
                "supporting_experts": sorted(
                    {by_option[o]["expert_id"] for o in f["option_ids"] if o in by_option}
                ),
                "source": f.get("source", "greffier"),
            }
        )
        for oid in f["option_ids"]:
            gid = next((g for g in f.get("group_ids", []) if g == oid), None)
            role = (
                "variant"
                if oid in variant_ids
                else (
                    "member"
                    if gid is not None or len(f.get("group_ids", [])) == 0
                    else "premerged_duplicate"
                )
            )
            trace.append({"option_id": oid, "family_id": fid, "role": role})
    return final, trace


# --- Comparaison : sélection déterministe des familles à comparer ---------------------------------
COMPARISON_MAX_FAMILIES = 12


def select_families_for_comparison(
    families: list[dict[str, Any]], cap: int = COMPARISON_MAX_FAMILIES
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Retient au plus `cap` familles : toutes si possible ; sinon les plus soutenues, avec au
    moins une famille par nature (les stratégies minoritaires sérieuses restent représentées) et
    celles portant un désaccord interne. Aucun score : un ordre déterministe, journalisé.
    Retourne (retenues, écartées avec motif)."""
    if len(families) <= cap:
        return list(families), []
    ranked = sorted(
        families,
        key=lambda f: (
            -len(f.get("supporting_experts", [])),
            -len(f.get("option_ids", [])),
            f["family_id"],
        ),
    )
    retained: list[dict[str, Any]] = []
    seen_kinds: set[str] = set()
    for f in ranked:  # une par nature d'abord
        if f["kind"] not in seen_kinds:
            retained.append(f)
            seen_kinds.add(f["kind"])
    for f in ranked:  # puis désaccords internes, puis soutien
        if len(retained) >= cap:
            break
        if f not in retained and f.get("internal_disagreements"):
            retained.append(f)
    for f in ranked:
        if len(retained) >= cap:
            break
        if f not in retained:
            retained.append(f)
    retained = retained[: max(cap, len(seen_kinds))]
    retained_ids = {f["family_id"] for f in retained}
    deferred = [
        {
            "family_id": f["family_id"],
            "label": f["label"],
            "kind": f["kind"],
            "reason": (
                "au-delà du plafond de familles comparées ; conservée dans le rapport et la "
                "synthèse, non comparée"
            ),
        }
        for f in families
        if f["family_id"] not in retained_ids
    ]
    retained.sort(key=lambda f: int(f["family_id"][1:]))
    return retained, deferred


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
