"""Rapport de situation OT-V1 (incrément 1) — assemblage déterministe, sans appel LLM.

Le rapport dit clairement ce qui est **établi**, **supposé**, **inconnu**, **non vérifié** et
**contesté**. Il préserve les alternatives distinctes, les hypothèses, les risques, les désaccords,
les inconnues, ce qui reste à rechercher, et l'état du budget (appels, tokens, coût). Les 14 champs
de la cible sont présents, mais ceux que l'incrément ne permet pas encore de produire honnêtement
sont marqués « non encore délibéré », « non vérifié » ou « nécessite recherche » : aucune
recommandation finale n'est simulée. Le statut de la mission reste `candidate`.
"""

from __future__ import annotations

from typing import Any

from app.mission_schemas import FramingOutput

NOT_DELIBERATED = (
    "non encore délibéré (tours de critique, steelman et révision : incréments suivants)"
)
NOT_VERIFIED = "non vérifié (aucune recherche externe dans cet incrément)"
NEEDS_RESEARCH = "nécessite recherche"


def build_situation_report(
    *,
    mission_id: int,
    input_type: str,
    input_text: str,
    class_info: dict[str, Any],
    framing: FramingOutput | None,
    framing_error: str,
    composition: dict[str, Any],
    cartography: dict[str, Any],
    budget: dict[str, Any],
    stop_reason: str,
) -> dict[str, Any]:
    """Construit le rapport de situation à partir des artefacts persistés de la mission."""
    partial = bool(stop_reason)
    constraints = list(framing.constraints) if framing else []
    assumptions = list(framing.assumptions) if framing else []
    global_unknowns = list(framing.global_unknowns) if framing else []
    dim_unknowns = [
        {"dimension": d.name, "unknowns": list(d.unknowns)}
        for d in (framing.dimensions if framing else [])
        if d.unknowns
    ]
    contestation = (
        framing.contestation.model_dump()
        if framing
        else {"status": "none", "target": "", "argument": ""}
    )
    evidence = cartography.get("evidence", [])
    established = [
        {"text": c, "origin": "contrainte énoncée par le demandeur"} for c in constraints
    ] + [
        {"text": e["claim"], "origin": f"entrée du demandeur ({e['source']})"}
        for e in evidence
        if e["status"] == "verified"
    ]
    unverified = [
        {"text": e["claim"], "status": e["status"], "expert_id": e["expert_id"]}
        for e in evidence
        if e["status"] != "verified"
    ]
    to_research = [u["text"] for u in cartography.get("to_verify", [])]
    unknown_total = (
        len(global_unknowns)
        + sum(len(d["unknowns"]) for d in dim_unknowns)
        + len(cartography.get("unknowns", []))
    )
    verified_count = sum(1 for e in evidence if e["status"] == "verified")

    groups = cartography.get("option_groups", [])
    options_field = [
        {
            "group_id": g["group_id"],
            "label": g["label"],
            "kinds": g["kinds"],
            "supporters": g["supporting_experts"],
            "source": g["source"],
        }
        for g in groups
    ]
    if unknown_total >= 3 and verified_count == 0:
        state_line = (
            f"information insuffisante ({unknown_total} inconnue(s) déclarée(s), aucune preuve "
            "vérifiée) : l'étape naturelle avant toute délibération est de rechercher et vérifier"
        )
    else:
        state_line = "matière rassemblée ; la délibération n'a pas encore eu lieu"

    fourteen = {
        "01_probleme_compris": framing.problem_understood
        if framing
        else f"cadrage indisponible : {framing_error}",
        "02_objectif": (framing.assumed_objective if framing else "")
        or "non précisé par le cadrage",
        "03_contraintes": constraints,
        "04_hypotheses": [{"text": a, "status": "non vérifiée"} for a in assumptions]
        + [
            {"text": h["text"], "status": "non vérifiée", "experts": h["experts"]}
            for h in cartography.get("hypotheses", [])
        ],
        "05_options_examinees": options_field,
        "06_preuves": {
            "verified_from_input": [e for e in evidence if e["status"] == "verified"],
            "unverified_or_model_knowledge": unverified,
            "note": NOT_VERIFIED,
        },
        "07_arguments_pour": NOT_DELIBERATED,
        "08_arguments_contre": {
            "status": NOT_DELIBERATED,
            "matiere": [
                d for d in cartography.get("disagreements", []) if d.get("source") != "greffier"
            ],
        },
        "09_risques": [
            {"text": r["text"], "experts": r["experts"], "qualification": "non hiérarchisé"}
            for r in cartography.get("risks", [])
        ],
        "10_recommandation": {
            "status": "aucune recommandation : " + NOT_DELIBERATED,
            "etat_de_la_matiere": state_line,
        },
        "11_niveau_de_confiance": "non applicable : aucune délibération réalisée",
        "12_desaccords_residuels": cartography.get("disagreements", []),
        "13_conditions_de_changement": NOT_DELIBERATED,
        "14_prochaine_action": [
            "vérifier les éléments listés « à rechercher »" if to_research else "",
            "conduire les tours de critique / steelman / révision (incréments suivants)",
        ],
    }
    fourteen["14_prochaine_action"] = [x for x in fourteen["14_prochaine_action"] if x]

    return {
        "mission_id": mission_id,
        "status": "candidate",
        "partial": partial,
        "stop_reason": stop_reason,
        "input": {"type": input_type, "text_preview": input_text[:400]},
        "class": class_info,
        "framing_error": framing_error,
        "contestation": contestation,
        "escalation_signals": list(framing.escalation_signals) if framing else [],
        "epistemic": {
            "established": established,
            "assumed": fourteen["04_hypotheses"],
            "unknown": {
                "global": global_unknowns,
                "by_dimension": dim_unknowns,
                "from_experts": cartography.get("unknowns", []),
                "total": unknown_total,
            },
            "unverified": unverified,
            "contested": {
                "request_contestation": contestation,
                "disagreements": cartography.get("disagreements", []),
            },
        },
        "alternatives": options_field,
        "comparison": cartography.get("comparison", []),
        "non_action_option_present": cartography.get("non_action_option_present", False),
        "divergence_index": cartography.get("divergence_index", 0.0),
        "risks": fourteen["09_risques"],
        "to_research": to_research,
        "composition": {
            "cells": composition.get("cells", []),
            "uncovered_dimensions": composition.get("uncovered_dimensions", []),
            "bounds": composition.get("bounds", {}),
            "experts_total": cartography.get("experts_total", 0),
            "experts_answered": cartography.get("experts_answered", 0),
        },
        "budget": budget,
        "fourteen_fields": fourteen,
    }


def _bullets(items: list[Any], empty: str = "aucun") -> list[str]:
    if not items:
        return [f"- _{empty}_"]
    out: list[str] = []
    for item in items:
        if isinstance(item, dict):
            text = item.get("text") or item.get("label") or item.get("description") or str(item)
            suffix = ""
            if item.get("experts"):
                suffix = f" — {', '.join(item['experts'])}"
            elif item.get("supporters"):
                suffix = f" — soutenue par {', '.join(item['supporters'])}"
            if item.get("status"):
                suffix += f" _({item['status']})_"
            out.append(f"- {text}{suffix}")
        else:
            out.append(f"- {item}")
    return out


def render_situation_report_markdown(report: dict[str, Any]) -> str:
    """Rendu Markdown déterministe du rapport de situation."""
    f = report["fourteen_fields"]
    ep = report["epistemic"]
    b = report["budget"]
    cls = report["class"]
    lines: list[str] = [
        f"# Rapport de situation — mission {report['mission_id']}",
        "",
        f"**Statut :** `{report['status']}`"
        + (f" — **partiel** (arrêt : {report['stop_reason']})" if report["partial"] else ""),
        f"**Classe :** {cls.get('effective', '')}"
        + (" (provisoire, non déterminée)" if cls.get("provisional") else "")
        + (f" — escalade : {cls['escalation']}" if cls.get("escalation") else ""),
        f"**Budget :** {b.get('llm_calls_used', 0)}/{b.get('max_llm_calls', 0)} appels · "
        f"{b.get('cost_eur', 0.0):.4f} € / {b.get('max_cost_eur', 0.0):.2f} € · "
        f"{b.get('input_tokens', 0)} tokens entrée · {b.get('output_tokens', 0)} tokens sortie",
        "",
        "> Ce rapport ne contient aucune recommandation : la délibération (critique, steelman, "
        "révision) n'a pas encore eu lieu. Il reste `candidate` jusqu'à une action explicite du "
        "CEO.",
        "",
        "## 1. Problème compris",
        str(f["01_probleme_compris"]),
        "",
        "## 2. Objectif supposé",
        str(f["02_objectif"]),
        "",
        "## 3. Contestation de la demande",
    ]
    c = report["contestation"]
    if c.get("status") == "raised":
        lines.append(f"**Contestation soulevée** — cible : {c.get('target')} — {c.get('argument')}")
    else:
        lines.append(
            "Aucune contestation : la demande est jugée correctement posée par le cadrage."
        )
    if report.get("escalation_signals"):
        lines += ["", "Signaux d'escalade de classe :"]
        lines += _bullets(report["escalation_signals"])
    lines += ["", "## 4. Ce qui est établi"]
    lines += _bullets(ep["established"], "rien d'établi hors la demande")
    lines += ["", "## 5. Ce qui est supposé (non vérifié)"]
    lines += _bullets(ep["assumed"])
    unk = ep["unknown"]
    lines += ["", f"## 6. Ce qui est inconnu ({unk['total']})"]
    lines += _bullets(unk["global"])
    for d in unk["by_dimension"]:
        lines.append(f"- **{d['dimension']}** : " + " ; ".join(d["unknowns"]))
    lines += _bullets(unk["from_experts"], "") if unk["from_experts"] else []
    lines += ["", "## 7. Ce qui est non vérifié"]
    lines += _bullets(ep["unverified"], "aucune affirmation non vérifiée")
    lines += ["", "## 8. Dimensions et composition"]
    for cell in report["composition"]["cells"]:
        lines.append(
            f"- **{cell['dimension']}** (criticité {cell['criticality']}) : "
            + ", ".join(cell["angles"])
        )
    if report["composition"]["uncovered_dimensions"]:
        lines.append(
            "- _Non couvertes au Tour 0 (budget)_ : "
            + ", ".join(report["composition"]["uncovered_dimensions"])
        )
    bounds = report["composition"].get("bounds", {})
    if bounds:
        lines.append(
            f"- Bornes appliquées : {bounds.get('max_angles_per_cell')} angle(s)/cellule "
            f"({bounds.get('max_angles_per_cell_nature', '')}) ; "
            f"{bounds.get('max_experts_by_budget')} expert(s) max par le budget"
        )
    lines += [
        "",
        f"## 9. Alternatives distinctes ({len(report['alternatives'])})"
        + (" — option de non-action présente" if report["non_action_option_present"] else ""),
    ]
    for g in report["alternatives"]:
        lines.append(
            f"- **{g['group_id']}** {g['label']} — nature : {', '.join(g['kinds'])} — "
            f"soutenue par {', '.join(g['supporters'])} ({g['source']})"
        )
    if not report["alternatives"]:
        lines.append("- _aucune option structurée (exposés indisponibles)_")
    lines += ["", "## 10. Comparaison (champs non délibérés laissés explicites)"]
    lines.append("| Groupe | Soutiens | Nature | Coût | Délai | Réversibilité | Preuve |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for row in report["comparison"]:
        lines.append(
            f"| {row['group_id']} {row['label']} | {row['supporters']} | "
            f"{', '.join(row['kinds'])} | "
            f"{row['cost']} | {row['delay']} | {row['reversibility']} | {row['evidence']} |"
        )
    lines += [
        "",
        f"## 11. Désaccords conservés (indice de divergence {report['divergence_index']})",
    ]
    lines += _bullets(
        [
            {
                "text": (
                    f"[{d.get('nature')}] {d.get('description')} "
                    f"({' / '.join(d.get('between', []))})"
                )
            }
            for d in ep["contested"]["disagreements"]
        ],
        "aucun désaccord déclaré",
    )
    lines += ["", "## 12. Risques (non hiérarchisés)"]
    lines += _bullets(report["risks"])
    lines += ["", "## 13. À rechercher avant de délibérer"]
    lines += _bullets(report["to_research"])
    lines += [
        "",
        "## 14. Recommandation, confiance, conditions",
        f"- Recommandation : {f['10_recommandation']['status']}",
        f"- État de la matière : {f['10_recommandation']['etat_de_la_matiere']}",
        f"- Niveau de confiance : {f['11_niveau_de_confiance']}",
        f"- Conditions de changement : {f['13_conditions_de_changement']}",
        "- Prochaines actions :",
    ] + [f"  - {a}" for a in f["14_prochaine_action"]]
    return "\n".join(lines) + "\n"
