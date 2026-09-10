"""Rapport de situation OT-V1 — assemblage déterministe, sans appel LLM.

Le rapport dit clairement ce qui est **établi**, **supposé**, **inconnu**, **non vérifié** et
**contesté**. Il préserve les alternatives distinctes, les hypothèses, les risques, les désaccords,
les inconnues, ce qui reste à rechercher, et l'état du budget (appels, tokens, coût). Les 14 champs
de la cible sont présents.

* Incrément 1 (cadrage seul) : les champs que la mission ne permet pas de produire honnêtement sont
  marqués « non encore délibéré » ; aucune recommandation n'est simulée.
* Incrément 2 (délibération probante) : lorsque la synthèse a produit une recommandation, les
  14 champs sont remplis à partir d'elle — options = familles stratégiques réellement examinées,
  preuves étiquetées par provenance, désaccords résiduels conservés, confiance justifiée. La
  recommandation reste une **recommandation** : le statut demeure `candidate` jusqu'à une action
  explicite du CEO (Décision 026). Une délibération interrompue (budget, information externe
  manquante) est dite telle quelle : rapport partiel, champs non produits explicites.
"""

from __future__ import annotations

from typing import Any

from app.mission_schemas import FramingOutput

NOT_DELIBERATED = "non encore délibéré (confrontation, steelman, révision non réalisés)"
NOT_VERIFIED = "non vérifié (aucune recherche externe réalisée)"
NEEDS_RESEARCH = "nécessite recherche"


def _deliberation_gap(deliberation: dict[str, Any] | None, stop_reason: str) -> str:
    """Formule honnête de ce qui manque quand aucune recommandation n'a été produite."""
    if not deliberation or not deliberation.get("steps_done"):
        if stop_reason:
            return f"délibération non réalisée (arrêt : {stop_reason})"
        return NOT_DELIBERATED
    done = ", ".join(deliberation.get("steps_done", []))
    reason = deliberation.get("stop", {}).get("reason", "")
    if stop_reason:
        return f"délibération interrompue après {done} (arrêt : {stop_reason})"
    return f"délibération partielle ({done}) — {reason or 'synthèse non produite'}"


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
    deliberation: dict[str, Any] | None = None,
    recommendation: dict[str, Any] | None = None,
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

    delib = deliberation or {}
    produced = bool(recommendation) and (recommendation or {}).get("status") == "produced"
    research_items = delib.get("research", [])
    external_found = [r for r in research_items if r.get("status") == "found"]
    external_missing = [r for r in research_items if r.get("status") != "found"]
    evidence_note = (
        f"{len(external_found)} preuve(s) externe(s) sourcée(s) ; "
        f"{len(external_missing)} question(s) factuelle(s) non résolue(s)"
        if research_items
        else NOT_VERIFIED
    )

    if produced and recommendation is not None:
        rec = recommendation
        families = delib.get("consolidation", {}).get("families", [])
        rec_options = rec.get("options") or [
            {"family_id": f["family_id"], "label": f["label"], "kind": f["kind"]} for f in families
        ]
        fam_by_id = {f["family_id"]: f for f in families}
        options_out = [
            {
                **o,
                "supporters": fam_by_id.get(o.get("family_id", ""), {}).get(
                    "supporting_experts", []
                ),
                "option_ids": fam_by_id.get(o.get("family_id", ""), {}).get("option_ids", []),
            }
            for o in rec_options
        ]
        fourteen: dict[str, Any] = {
            "01_probleme_compris": rec.get("problem_understood")
            or (framing.problem_understood if framing else ""),
            "02_objectif": rec.get("objective")
            or (framing.assumed_objective if framing else "")
            or "non précisé",
            "03_contraintes": rec.get("constraints") or constraints,
            "04_hypotheses": rec.get("assumptions")
            or [{"text": a, "status": "unverified"} for a in assumptions],
            "05_options_examinees": options_out,
            "06_preuves": {
                "labeled": rec.get("evidence", []),
                "all_with_provenance": delib.get("evidence", []),
                "verified_from_input": [e for e in evidence if e["status"] == "verified"],
                "unverified_or_model_knowledge": unverified,
                "note": evidence_note,
            },
            "07_arguments_pour": rec.get("advantages", []),
            "08_arguments_contre": rec.get("disadvantages", []),
            "09_risques": rec.get("risks", []),
            "10_recommandation": {
                "status": "recommandation produite — décision réservée au CEO",
                **rec.get("recommendation", {}),
                "requires_ceo_decision": True,
                "ceo_decision_mandatory_by_class": rec.get("ceo_decision_mandatory_by_class"),
                "ceo_arbitration_required": rec.get("ceo_arbitration_required"),
                "decision_ready": rec.get("decision_ready"),
                "quality_blocked": rec.get("quality_blocked"),
                "quality_gate_status": rec.get("quality_gate_status"),
                "information_insufficient": rec.get("information_insufficient"),
                "quality_gate": rec.get("gate", {}),
            },
            "11_niveau_de_confiance": rec.get("confidence", {}),
            "12_desaccords_residuels": rec.get("residual_disagreements", []),
            "13_conditions_de_changement": rec.get("change_conditions", []),
            "14_prochaine_action": [rec.get("next_action", "")]
            + (
                ["arbitrage CEO requis : un désaccord résiduel porte sur des valeurs"]
                if rec.get("ceo_arbitration_required")
                else []
            ),
        }
    else:
        gap = _deliberation_gap(deliberation, stop_reason)
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
                "all_with_provenance": delib.get("evidence", []),
                "verified_from_input": [e for e in evidence if e["status"] == "verified"],
                "unverified_or_model_knowledge": unverified,
                "note": evidence_note,
            },
            "07_arguments_pour": gap,
            "08_arguments_contre": {
                "status": gap,
                "matiere": [
                    d for d in cartography.get("disagreements", []) if d.get("source") != "greffier"
                ],
            },
            "09_risques": [
                {"text": r["text"], "experts": r["experts"], "qualification": "non hiérarchisé"}
                for r in cartography.get("risks", [])
            ],
            "10_recommandation": {
                "status": "aucune recommandation : " + gap,
                "etat_de_la_matiere": state_line,
                "budget_request": delib.get("budget_request") or {},
            },
            "11_niveau_de_confiance": "non applicable : aucune recommandation produite",
            "12_desaccords_residuels": delib.get("residual_disagreements")
            or cartography.get("disagreements", []),
            "13_conditions_de_changement": gap,
            "14_prochaine_action": [
                "vérifier les éléments listés « à rechercher »" if to_research else "",
                _budget_request_next_action(delib.get("budget_request") or {}),
                "reprendre la délibération (confrontation / steelman / révision / synthèse)",
            ],
        }
        fourteen["14_prochaine_action"] = [x for x in fourteen["14_prochaine_action"] if x]

    report = {
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
        "risks": [
            {"text": r["text"], "experts": r["experts"], "qualification": "non hiérarchisé"}
            for r in cartography.get("risks", [])
        ],
        "to_research": to_research,
        "composition": {
            "cells": composition.get("cells", []),
            "uncovered_dimensions": composition.get("uncovered_dimensions", []),
            "bounds": composition.get("bounds", {}),
            "experts_total": cartography.get("experts_total", 0),
            "experts_answered": cartography.get("experts_answered", 0),
        },
        "budget": budget,
        "recommendation_produced": produced,
        "deliberation": _deliberation_summary(delib) if deliberation is not None else None,
        "fourteen_fields": fourteen,
    }
    return report


def _deliberation_summary(delib: dict[str, Any]) -> dict[str, Any]:
    """Vue compacte et auditable de la délibération (le détail complet reste dans la mission)."""
    st = delib.get("steelman", {})
    return {
        "steps_done": delib.get("steps_done", []),
        "steps_skipped": delib.get("steps_skipped", []),
        "stop": delib.get("stop", {}),
        "objections": [
            {
                "id": o["id"],
                "from": o["from"],
                "target": o["target"],
                "act": o["act"],
                "nature": o["nature"],
                "text": o["text"],
                "status": o["status"],
                "depends_on_fact": o.get("depends_on_fact", False),
            }
            for o in delib.get("confrontation", {}).get("objections", [])
        ],
        "steelman": {
            k: st.get(k)
            for k in (
                "required",
                "reason",
                "status",
                "target",
                "contradictor",
                "recognition",
                "strawman_flags",
                "missing_points",
            )
            if k in st
        },
        "research": [
            {
                "id": r["id"],
                "question": r["question"],
                "status": r["status"],
                "provider": r["provider"],
                "source": r.get("source", ""),
                "date": r.get("date", ""),
                "reliability": r.get("reliability", "unknown"),
                "provenance": r.get("provenance", ""),
                "note": r.get("note", ""),
            }
            for r in delib.get("research", [])
        ],
        "revisions": [
            {
                "label": r["label"],
                "decision": r["decision"],
                "called": r.get("called", False),
                "triggered_by": r.get("triggered_by", []),
                "reason": r.get("reason", ""),
                "changed": r["revised_position"] != r["previous_position"],
                "unexplained_change": r.get("unexplained_change", False),
            }
            for r in delib.get("revisions", [])
        ],
        "families": [
            {
                "family_id": f["family_id"],
                "label": f["label"],
                "kind": f["kind"],
                "option_ids": f["option_ids"],
                "variants": f.get("variants", []),
                "internal_disagreements": f.get("internal_disagreements", []),
                "supporting_experts": f.get("supporting_experts", []),
                "source": f.get("source", ""),
            }
            for f in delib.get("consolidation", {}).get("families", [])
        ],
        "consolidation_status": delib.get("consolidation", {}).get("status", ""),
        "unconsolidated_option_ids": delib.get("consolidation", {}).get(
            "unconsolidated_option_ids", []
        ),
        "not_merged_because": delib.get("consolidation", {}).get("not_merged_because", []),
        "consolidation_notes": delib.get("consolidation", {}).get("notes", []),
        "comparison": delib.get("comparison", {}),
        "gate": delib.get("gate", {}),
        "residual_disagreements": delib.get("residual_disagreements", []),
        "budget_request": delib.get("budget_request") or {},
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


def _render_deliberation(report: dict[str, Any]) -> list[str]:
    d = report.get("deliberation") or {}
    lines: list[str] = ["", "## 15. Délibération (trace)"]
    if not d:
        lines.append("- _aucune délibération réalisée_")
        return lines
    stop = d.get("stop", {})
    lines.append(
        f"- Étapes réalisées : {', '.join(d.get('steps_done', [])) or 'aucune'} — arrêt : "
        f"{stop.get('reason', '')}"
    )
    for s in d.get("steps_skipped", []):
        lines.append(f"- Étape sautée « {s['step']} » : {s['reason']}")
    objections = d.get("objections", [])
    lines += ["", f"### Actes de confrontation ({len(objections)})"]
    lines += _bullets(
        [
            {
                "text": f"{o['id']} {o['from']} → {o['target'] or '—'} [{o['act']}/{o['nature']}] "
                f"{o['text']}",
                "status": o["status"],
            }
            for o in objections
        ],
        "aucun acte substantiel (convergence déclarée, aucun désaccord fabriqué)",
    )
    st = d.get("steelman", {})
    lines += ["", "### Steelman"]
    if st.get("required"):
        lines.append(
            f"- Requis ({st.get('reason')}) — statut **{st.get('status')}** — cible "
            f"{st.get('target', '')} par {st.get('contradictor', '')} — reconnaissance : "
            f"{st.get('recognition', 'n/a')}"
        )
        if st.get("strawman_flags"):
            lines.append("- Signaux de strawman : " + " ; ".join(st["strawman_flags"]))
        if st.get("missing_points"):
            lines.append("- Points manquants signalés : " + " ; ".join(st["missing_points"]))
    else:
        lines.append("- Non requis pour cette classe et cette divergence.")
    research = d.get("research", [])
    lines += ["", f"### Recherche ciblée ({len(research)})"]
    lines += _bullets(
        [
            {
                "text": f"{r['id']} « {r['question']} » — {r['provider']} — source : "
                f"{r['source'] or 'aucune'} — fiabilité {r['reliability']}",
                "status": r["status"],
            }
            for r in research
        ],
        "aucun désaccord pertinent ne dépendait d'un fait vérifiable",
    )
    revisions = d.get("revisions", [])
    lines += ["", "### Révisions (positions → décision → cause)"]
    lines += _bullets(
        [
            {
                "text": f"{r['label']} : {r['decision']}"
                + (f" (déclenché par {', '.join(r['triggered_by'])})" if r["triggered_by"] else "")
                + (" — non appelé : aucune information nouvelle" if not r["called"] else "")
                + (f" — {r['reason']}" if r["called"] and r["reason"] else ""),
            }
            for r in revisions
        ],
        "aucune révision",
    )
    families = d.get("families", [])
    lines += ["", f"## 16. Familles stratégiques ({len(families)}) et comparaison"]
    if d.get("consolidation_status") and d["consolidation_status"] != "ok":
        lines.append(
            f"- ⚠ Consolidation : statut **{d['consolidation_status']}**"
            + (
                f" — options non consolidées : {', '.join(d['unconsolidated_option_ids'])}"
                if d.get("unconsolidated_option_ids")
                else ""
            )
        )
    comp_status = (d.get("comparison") or {}).get("status")
    if comp_status and comp_status != "ok":
        lines.append(f"- ⚠ Comparaison : statut **{comp_status}** (aucune comparaison valide)")
    for nc in (d.get("comparison") or {}).get("not_compared", []):
        lines.append(f"- Non comparée {nc['family_id']} {nc['label']} : {nc['reason']}")
    for f in families:
        lines.append(
            f"- **{f['family_id']}** {f['label']} [{f['kind']}] — options "
            f"{', '.join(f['option_ids'])} — soutenue par "
            f"{', '.join(f['supporting_experts']) or '—'}"
            + (
                f" — désaccords internes : {' ; '.join(f['internal_disagreements'])}"
                if f.get("internal_disagreements")
                else ""
            )
        )
    for n in d.get("not_merged_because", []):
        lines.append(f"- Non fusionnées {', '.join(n['option_ids'])} : {n['reason']}")
    comp = d.get("comparison", {})
    if comp.get("rows"):
        criteria = list(comp.get("criteria", []))
        lines += ["", "| Famille | " + " | ".join(criteria) + " |"]
        lines.append("| --- |" + " --- |" * len(criteria))
        for row in comp["rows"]:
            cells = [
                f"{row['assessments'].get(c, {}).get('value', '—')} "
                f"_[{row['assessments'].get(c, {}).get('basis', '—')}]_"
                for c in criteria
            ]
            lines.append(f"| {row['family_id']} | " + " | ".join(cells) + " |")
    gate = d.get("gate", {})
    if gate:
        lines += ["", "### Porte qualité"]
        lines.append(f"- Passée : **{gate.get('passed')}**")
        for k, v in gate.get("checks", {}).items():
            lines.append(f"- {k} : {v}")
        for issue in gate.get("issues", []):
            lines.append(f"- ⚠ {issue}")
    if d.get("budget_request"):
        lines += ["", "### Demande de budget", *budget_request_lines(d["budget_request"])]
    return lines


def budget_request_lines(br: dict[str, Any]) -> list[str]:
    """Lignes d'une demande de budget selon sa cause réelle (B14-prime — E).

    « Dimensions critiques non couvertes » n'apparaît que si la liste existe et n'est pas vide ;
    un arrêt pour délibération non finançable expose appels restants, cycle minimal, déficit et
    étape de détection, sans jamais mentionner de dimension critique absente.
    """
    uncovered = br.get("uncovered_critical_dimensions") or []
    if uncovered:
        return [
            f"- Dimensions critiques non couvertes : {', '.join(uncovered)} — "
            f"≈ {br.get('additional_calls_estimate')} appel(s) supplémentaire(s) — "
            f"{br.get('advice')}"
        ]
    return [
        "- Délibération non finançable : "
        f"{br.get('remaining_calls')} appel(s) restant(s) pour un cycle minimal estimé à "
        f"{br.get('minimal_deliberation_calls')} — déficit ≈ "
        f"{br.get('additional_calls_estimate')} appel(s) — détecté à l'étape "
        f"« {br.get('detected_at_step', 'deliberation')} » — {br.get('advice')}"
    ]


def _budget_request_next_action(br: dict[str, Any]) -> str:
    if not br:
        return ""
    if br.get("uncovered_critical_dimensions"):
        return "relever le plafond ou réduire le périmètre (dimension critique non couverte)"
    return (
        f"relever le plafond d'appels (délibération non finançable : déficit ≈ "
        f"{br.get('additional_calls_estimate')} appel(s))"
    )


def _render_cost_exposure(b: dict[str, Any]) -> list[str]:
    """Coût connu / exposition incertaine / borne potentielle / plafond CEO (B12).

    L'exposition est une borne supérieure sur des tentatives fournisseur au coût inconnu, jamais
    une facture ; elle n'est détaillée que si elle existe.
    """
    known = float(b.get("known_cost_eur", b.get("cost_eur", 0.0)) or 0.0)
    uncertain = float(b.get("uncertain_cost_upper_bound_eur", 0.0) or 0.0)
    potential = float(b.get("potential_total_cost_upper_bound_eur", known + uncertain) or 0.0)
    cap = float(b.get("max_cost_eur", 0.0) or 0.0)
    line = (
        f"**Coût fournisseur :** connu {known:.4f} € · exposition incertaine ≤ {uncertain:.4f} € "
        f"· borne supérieure potentielle ≤ {potential:.4f} € · plafond CEO {cap:.2f} €"
    )
    if uncertain <= 0:
        return [line]
    n = int(b.get("uncertain_attempts", 0) or 0)
    return [
        line,
        f"_Exposition incertaine : {n} tentative(s) fournisseur échouée(s) sans usage rapporté, "
        "dont le traitement n'est pas exclu (borne pré-appel, pas un coût facturé). Le plafond "
        "s'applique à la borne supérieure potentielle._",
    ]


def render_situation_report_markdown(report: dict[str, Any]) -> str:
    """Rendu Markdown déterministe du rapport de situation."""
    f = report["fourteen_fields"]
    ep = report["epistemic"]
    b = report["budget"]
    cls = report["class"]
    produced = bool(report.get("recommendation_produced"))
    banner = (
        "> Recommandation **produite par les agents** : ils recommandent, ils ne décident pas. "
        "Le rapport reste `candidate` jusqu'à une action explicite du CEO ; aucune exécution."
        if produced
        else "> Ce rapport ne contient aucune recommandation : la délibération n'a pas été menée "
        "à terme. Il reste `candidate` jusqu'à une action explicite du CEO."
    )
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
        *_render_cost_exposure(b),
        "",
        banner,
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
        f"## 9. Alternatives distinctes au Tour 0 ({len(report['alternatives'])})"
        + (" — option de non-action présente" if report["non_action_option_present"] else ""),
    ]
    for g in report["alternatives"]:
        lines.append(
            f"- **{g['group_id']}** {g['label']} — nature : {', '.join(g['kinds'])} — "
            f"soutenue par {', '.join(g['supporters'])} ({g['source']})"
        )
    if not report["alternatives"]:
        lines.append("- _aucune option structurée (exposés indisponibles)_")
    lines += ["", "## 10. Comparaison initiale (avant délibération)"]
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
    lines += ["", "## 12. Risques"]
    lines += _bullets(f["09_risques"] if produced else report["risks"])
    lines += ["", "## 13. À rechercher"]
    lines += _bullets(report["to_research"])
    lines += _render_deliberation(report) if report.get("deliberation") is not None else []
    lines += ["", "## 14. Recommandation, confiance, conditions"]
    rec = f["10_recommandation"]
    if produced:
        conf = f["11_niveau_de_confiance"] or {}
        lines += [
            f"- **{rec.get('kind', '')}** — {rec.get('statement', '')}",
            f"- Famille visée : {rec.get('family_id', '') or '—'} — motif : "
            f"{rec.get('rationale', '')}",
            "- Décision réservée au CEO : oui"
            + (
                " (obligatoire pour la classe)"
                if rec.get("ceo_decision_mandatory_by_class")
                else ""
            )
            + (" — **arbitrage de valeurs requis**" if rec.get("ceo_arbitration_required") else ""),
            f"- Information suffisante pour décider : {not rec.get('information_insufficient')}",
            f"- Porte qualité : {rec.get('quality_gate', {}).get('passed', 'non exécutée')} "
            f"(statut {rec.get('quality_gate_status', 'pending')})",
            f"- Prête pour décision (decision_ready) : {bool(rec.get('decision_ready'))}"
            + (" — bloquée par la porte qualité" if rec.get("quality_blocked") else ""),
            f"- Niveau de confiance : {conf.get('level', '')} — {conf.get('justification', '')}",
            "- Arguments pour :",
        ]
        lines += [f"  - {a}" for a in f["07_arguments_pour"]] or ["  - _aucun_"]
        lines.append("- Arguments contre :")
        lines += [f"  - {a}" for a in f["08_arguments_contre"]] or ["  - _aucun_"]
        lines.append("- Désaccords résiduels conservés :")
        lines += [
            f"  - [{d.get('nature')}] {' / '.join(d.get('between', []))} : {d.get('description')}"
            for d in f["12_desaccords_residuels"]
        ] or ["  - _aucun_"]
        lines.append("- Conditions de changement :")
        lines += [f"  - {x}" for x in f["13_conditions_de_changement"]] or ["  - _aucune_"]
        lines.append("- Prochaine action :")
        lines += [f"  - {a}" for a in f["14_prochaine_action"] if a]
    else:
        lines += [
            f"- Recommandation : {rec['status']}",
            f"- État de la matière : {rec['etat_de_la_matiere']}",
            f"- Niveau de confiance : {f['11_niveau_de_confiance']}",
            f"- Conditions de changement : {f['13_conditions_de_changement']}",
            "- Prochaines actions :",
        ] + [f"  - {a}" for a in f["14_prochaine_action"]]
    return "\n".join(lines) + "\n"
