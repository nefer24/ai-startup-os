"""Cartographie OT-V1 (incrément 1) — le facilitateur structure, il n'oriente pas.

Deux catégories d'opérations, strictement séparées :

* **déterministes** (ce module, aucun appel LLM) : identifiants d'options, comptages, regroupements
  par identifiants ou rattachements explicitement déclarés, indice de divergence, agrégation des
  hypothèses / inconnues / risques / preuves, détection des ambiguïtés résiduelles ;
* **sémantiques** (jamais tranchées ici) : l'équivalence réelle de deux options, la nature d'un
  désaccord, le rapprochement d'hypothèses formulées différemment. Elles viennent de
  l'auto-qualification des experts, puis, si ambiguïté résiduelle, du greffier au schéma fermé
  (`app.mission_exploration`). Ce module ne fait qu'**intégrer** ces déclarations, attribuées et
  motivées, sans les compléter par un jugement propre.

La carte ne contient aucune préférence, aucun classement, aucune recommandation.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.mission_schemas import ClerkOutput, ExpertOutput, SelfQualificationOutput

NON_ACTION_KINDS = frozenset({"wait", "test", "buy", "simplify", "do_nothing", "integrate"})


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def anonymize_labels(expert_ids: list[str]) -> dict[str, str]:
    """Attribue à chaque expert un label de position anonyme (P1, P2…), dans l'ordre d'exposé."""
    return {expert_id: f"P{i}" for i, expert_id in enumerate(expert_ids, start=1)}


def collect_options(expert_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Identifie chaque option (`E{i}-O{j}`) et la rattache à son expert et sa dimension."""
    options: list[dict[str, Any]] = []
    for res in expert_results:
        output: ExpertOutput | None = res.get("output")
        if output is None:
            continue
        for j, opt in enumerate(output.options, start=1):
            options.append(
                {
                    "option_id": f"{res['expert_id']}-O{j}",
                    "expert_id": res["expert_id"],
                    "dimension": res["dimension"],
                    "angle": res["angle"],
                    "label": opt.label,
                    "summary": opt.summary,
                    "kind": opt.kind,
                }
            )
    return options


def relations_table(
    self_qual: dict[str, SelfQualificationOutput | None], labels: dict[str, str]
) -> list[dict[str, Any]]:
    """Table des relations déclarées (expert → position anonyme), attribuées."""
    inverse = {v: k for k, v in labels.items()}
    rows: list[dict[str, Any]] = []
    for expert_id, output in self_qual.items():
        if output is None:
            continue
        for rel in output.relations:
            other_expert = inverse.get(rel.other_id, "")
            rows.append(
                {
                    "from_expert": expert_id,
                    "from_label": labels.get(expert_id, ""),
                    "to_label": rel.other_id,
                    "to_expert": other_expert,
                    "relation": rel.relation,
                    "reason": rel.reason,
                }
            )
    return rows


def residual_ambiguities(relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ambiguïtés que l'auto-qualification n'a pas levées (→ greffier).

    Deux cas : une relation « variant » (ni identique ni différente) ; une incohérence entre les
    deux sens d'une même paire (A dit identique à B, B dit différent de A).
    """
    ambiguities: list[dict[str, Any]] = []
    by_pair: dict[tuple[str, str], str] = {}
    for row in relations:
        if not row["to_expert"]:
            continue
        by_pair[(row["from_expert"], row["to_expert"])] = row["relation"]
        if row["relation"] == "variant":
            ambiguities.append(
                {
                    "type": "variant",
                    "between": [row["from_label"], row["to_label"]],
                    "detail": (
                        f"{row['from_label']} qualifie {row['to_label']} de variante : "
                        f"{row['reason'] or 'sans précision'}"
                    ),
                }
            )
    seen: set[tuple[str, str]] = set()
    for (a, b), rel in by_pair.items():
        if (b, a) in seen:
            continue
        seen.add((a, b))
        back = by_pair.get((b, a))
        if back is not None and {rel, back} == {"identical", "different"}:
            ambiguities.append(
                {
                    "type": "inconsistent",
                    "between": [a, b],
                    "detail": f"{a} dit « {rel} » de {b} mais {b} dit « {back} » de {a}",
                }
            )
    return ambiguities


def position_clusters(expert_ids: list[str], relations: list[dict[str, Any]]) -> list[list[str]]:
    """Regroupe les positions déclarées mutuellement compatibles (identical non contredit)."""
    parent = {e: e for e in expert_ids}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    by_pair = {
        (r["from_expert"], r["to_expert"]): r["relation"] for r in relations if r["to_expert"]
    }
    for (a, b), rel in by_pair.items():
        if rel != "identical" or a not in parent or b not in parent:
            continue
        if by_pair.get((b, a)) == "different":
            continue  # incohérence : laissée au greffier, pas fusionnée
        parent[find(a)] = find(b)
    groups: dict[str, list[str]] = {}
    for e in expert_ids:
        groups.setdefault(find(e), []).append(e)
    return sorted(groups.values(), key=lambda g: (-len(g), g[0]))


def group_options(options: list[dict[str, Any]], clerk: ClerkOutput | None) -> list[dict[str, Any]]:
    """Groupes d'options : regroupements du greffier (attribués, motivés) puis singletons."""
    known = {o["option_id"]: o for o in options}
    groups: list[dict[str, Any]] = []
    assigned: set[str] = set()
    if clerk is not None:
        for g in clerk.groups:
            ids = [i for i in g.option_ids if i in known and i not in assigned]
            if not ids:
                continue
            assigned.update(ids)
            groups.append(
                {
                    "group_id": f"G{len(groups) + 1}",
                    "label": g.label or known[ids[0]]["label"],
                    "option_ids": ids,
                    "source": "greffier",
                    "motivation": g.motivation,
                    "kinds": sorted({known[i]["kind"] for i in ids}),
                    "supporting_experts": sorted({known[i]["expert_id"] for i in ids}),
                    "dimensions": sorted({known[i]["dimension"] for i in ids}),
                }
            )
    # Regroupement déterministe par libellé strictement identique (identifiant connu), puis
    # singletons. Aucun rapprochement sémantique n'est fait ici.
    by_label: dict[str, list[str]] = {}
    for o in options:
        if o["option_id"] in assigned:
            continue
        by_label.setdefault(_norm(o["label"]), []).append(o["option_id"])
    for ids in by_label.values():
        groups.append(
            {
                "group_id": f"G{len(groups) + 1}",
                "label": known[ids[0]]["label"],
                "option_ids": ids,
                "source": "libellé identique" if len(ids) > 1 else "singleton",
                "motivation": "",
                "kinds": sorted({known[i]["kind"] for i in ids}),
                "supporting_experts": sorted({known[i]["expert_id"] for i in ids}),
                "dimensions": sorted({known[i]["dimension"] for i in ids}),
            }
        )
    return groups


def _aggregate(expert_results: list[dict[str, Any]], attr: str) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    original: dict[str, str] = {}
    holders: dict[str, list[str]] = {}
    for res in expert_results:
        output: ExpertOutput | None = res.get("output")
        if output is None:
            continue
        for item in getattr(output, attr):
            key = _norm(item)
            if not key:
                continue
            counter[key] += 1
            original.setdefault(key, item)
            holders.setdefault(key, []).append(res["expert_id"])
    return [
        {"text": original[k], "count": counter[k], "experts": holders[k]}
        for k, _ in counter.most_common()
    ]


def build_cartography(
    *,
    expert_results: list[dict[str, Any]],
    self_qual: dict[str, SelfQualificationOutput | None],
    clerk: ClerkOutput | None,
    labels: dict[str, str],
) -> dict[str, Any]:
    """Assemble la carte : options, groupes, relations, divergence, agrégats, preuves."""
    expert_ids = [r["expert_id"] for r in expert_results]
    answered = [r["expert_id"] for r in expert_results if r.get("output") is not None]
    options = collect_options(expert_results)
    relations = relations_table(self_qual, labels)
    ambiguities = residual_ambiguities(relations)
    clusters = position_clusters(answered, relations)
    largest = len(clusters[0]) if clusters else 0
    divergence = 0.0 if len(answered) <= 1 else round(1 - largest / len(answered), 3)

    evidence: list[dict[str, Any]] = []
    for res in expert_results:
        output: ExpertOutput | None = res.get("output")
        if output is None:
            continue
        for ev in output.evidence:
            evidence.append(
                {
                    "expert_id": res["expert_id"],
                    "claim": ev.claim,
                    "source": ev.source,
                    "status": ev.status,
                }
            )
    evidence_counts = dict(Counter(e["status"] for e in evidence))

    disagreements: list[dict[str, Any]] = []
    if clerk is not None:
        for d in clerk.disagreements:
            disagreements.append(
                {
                    "source": "greffier",
                    "between": d.between,
                    "nature": d.nature,
                    "description": d.description,
                }
            )
    for res in expert_results:
        output = res.get("output")
        if output is None:
            continue
        for obj in output.objections:
            disagreements.append(
                {
                    "source": res["expert_id"],
                    "between": [labels.get(res["expert_id"], res["expert_id"])],
                    "nature": obj.nature,
                    "description": obj.text,
                    "target": obj.target,
                }
            )
    for row in relations:
        if row["relation"] == "different":
            disagreements.append(
                {
                    "source": row["from_expert"],
                    "between": [row["from_label"], row["to_label"]],
                    "nature": "solution",
                    "description": row["reason"] or "positions déclarées différentes",
                }
            )

    groups = group_options(options, clerk)
    return {
        "experts_total": len(expert_ids),
        "experts_answered": len(answered),
        "position_labels": labels,
        "positions": [
            {
                "expert_id": r["expert_id"],
                "label": labels.get(r["expert_id"], ""),
                "dimension": r["dimension"],
                "angle": r["angle"],
                "position": r["output"].position if r.get("output") is not None else "",
                "parse_error": r.get("parse_error", ""),
            }
            for r in expert_results
        ],
        "options": options,
        "option_groups": groups,
        "distinct_option_groups": len(groups),
        "non_action_option_present": any(o["kind"] in NON_ACTION_KINDS for o in options),
        "relations": relations,
        "residual_ambiguities": ambiguities,
        "clerk_used": clerk is not None,
        "position_clusters": clusters,
        "divergence_index": divergence,
        "hypotheses": _aggregate(expert_results, "assumptions"),
        "unknowns": _aggregate(expert_results, "unknowns"),
        "risks": _aggregate(expert_results, "risks"),
        "to_verify": _aggregate(expert_results, "to_verify"),
        "evidence": evidence,
        "evidence_counts": evidence_counts,
        "disagreements": disagreements,
        "comparison": [
            {
                "group_id": g["group_id"],
                "label": g["label"],
                "supporters": len(g["supporting_experts"]),
                "kinds": g["kinds"],
                "dimensions": g["dimensions"],
                "cost": "non encore délibéré",
                "delay": "non encore délibéré",
                "reversibility": "non encore délibéré",
                "evidence": "non vérifié (aucune recherche externe dans cet incrément)",
            }
            for g in groups
        ],
    }
