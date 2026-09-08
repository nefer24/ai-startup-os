"""Délibération probante OT-V1 (incrément 2) — prompts et règles déterministes.

Ce module ne fait aucun appel LLM : il construit les prompts des tours de délibération et fournit
les règles **déterministes** (choix du contradicteur, détection de convergence prématurée,
détection de strawman, sélection des questions factuelles matérielles, arrêt). L'orchestrateur
(`app.missions`) enchaîne les étapes sous budget et journalise tout.

Mouvements (document canonique §4, `behavior/04`) :
  C — confrontation : chaque expert voit la carte (positions anonymisées, hypothèses, objections,
      inconnues, preuves) et produit des actes adressés à des positions identifiables ; `none` est
      légitime (aucun désaccord fabriqué) ;
  D — steelman : pour structurante / critique, ou en cas de convergence prématurée, un contradicteur
      désigné reconstruit la meilleure version de la position dominante, reconnue (ou non) par son
      tenant, PUIS la critique — trois objets séparés ;
  E — recherche ciblée : un désaccord qui dépend d'un fait vérifiable déclenche une recherche plutôt
      qu'un tour supplémentaire ;
  F — révision : maintenir / modifier / nuancer / abandonner, avec la cause ; jamais sous simple
      insistance ;
  G — consolidation (familles stratégiques), comparaison sur critères communs, synthèse en
      14 champs, porte qualité par une instance distincte.
"""

from __future__ import annotations

from typing import Any

from app.mission_budget import normalize_class
from app.mission_schemas import ConfrontationOutput, SteelmanOutput

CONFRONTATION_CALL_TYPE = "confrontation"
STEELMAN_CALL_TYPE = "steelman"
RECOGNITION_CALL_TYPE = "steelman_recognition"
REVISION_CALL_TYPE = "revision"
CONSOLIDATION_CALL_TYPE = "consolidation"
COMPARISON_CALL_TYPE = "comparison"
SYNTHESIS_CALL_TYPE = "synthesis"
GATE_CALL_TYPE = "quality_gate"

STEELMAN_CLASSES = frozenset({"structurante", "critique"})
CRITICAL_ANGLE_TITLES = frozenset(
    {"Red Team / adversaire", "Expert risques / sécurité", "Auditeur / conformité"}
)
COMPACT = (
    "Réponds STRICTEMENT en JSON, sans texte autour, en JSON compact (sans indentation ni retours "
    "à la ligne décoratifs)"
)

# --- C. Confrontation -----------------------------------------------------------------------
CONFRONTATION_SYSTEM = (
    "Le premier tour d'une étude est clos. Tu es l'une des perspectives qui y ont participé. "
    "Tu vois maintenant la CARTE : les autres positions (anonymisées), leurs hypothèses, leurs "
    "objections, les inconnues et les preuves disponibles.\n\n"
    "Ta tâche : réagir UNIQUEMENT là où tu as quelque chose de substantiel à dire. Chaque acte "
    "vise une position identifiable (P1, P2…) et précise sa nature : solution (quoi faire), "
    "hypothesis (une supposition diverge), fact (un fait vérifiable diverge), value (arbitrage "
    "de valeurs ou d'appétence au risque).\n"
    "Actes possibles : critique (objection motivée par un fait, un risque ou une contradiction), "
    "defend (tu défends ta position contre une objection), complement (tu ajoutes un élément), "
    "refute (tu montres qu'une position ne tient pas), third_way (tu proposes une voie que "
    "personne n'a formulée), none (tu n'as rien de substantiel à opposer).\n"
    "Règles : une simple opposition non argumentée n'est pas recevable ; ne fabrique aucun "
    "désaccord ; si tu es d'accord avec une position, dis-le (convergence_note) plutôt que "
    "d'inventer une critique ; si ton désaccord dépend d'un FAIT vérifiable, mets "
    "depends_on_fact = true et formule la question précise à rechercher (fact_question).\n\n"
    + COMPACT
    + ' : {"acts": [{"act": "critique|defend|complement|refute|third_way|none", "target": "P2", '
    '"nature": "solution|hypothesis|fact|value|other", "text": "…", "depends_on_fact": false, '
    '"fact_question": ""}], "convergence_note": "…"}'
)


def build_map_view(cartography: dict[str, Any], exclude_label: str = "") -> str:
    """Vue textuelle de la carte pour un expert : positions anonymisées et matière commune."""
    lines: list[str] = ["Positions initiales (anonymisées) :"]
    for p in cartography.get("positions", []):
        if not p.get("position") or p.get("label") == exclude_label:
            continue
        lines.append(f"- {p['label']} ({p.get('dimension', '')}) : {p['position']}")
    hyps = cartography.get("hypotheses", [])
    if hyps:
        lines.append("Hypothèses avancées : " + " ; ".join(h["text"] for h in hyps[:12]))
    unknowns = cartography.get("unknowns", [])
    if unknowns:
        lines.append("Inconnues déclarées : " + " ; ".join(u["text"] for u in unknowns[:12]))
    objections = [
        d for d in cartography.get("disagreements", []) if d.get("source") not in {"greffier"}
    ]
    if objections:
        lines.append(
            "Objections déjà formulées : "
            + " ; ".join(f"[{d.get('nature')}] {d.get('description')}" for d in objections[:12])
        )
    evidence = cartography.get("evidence", [])
    if evidence:
        lines.append(
            "Preuves disponibles : "
            + " ; ".join(f"{e['claim']} ({e['status']})" for e in evidence[:12])
        )
    options = cartography.get("options", [])
    if options:
        lines.append(
            "Options proposées : "
            + " ; ".join(f"{o['option_id']} {o['label']} [{o['kind']}]" for o in options[:20])
        )
    return "\n".join(lines)


def build_confrontation_prompt(*, own_label: str, own_position: str, map_view: str) -> str:
    parts = [
        f"Ta position initiale ({own_label}) :",
        own_position.strip(),
        "",
        "=== CARTE ===",
        map_view,
        "",
        "Produis tes actes de confrontation (ou aucun) au format JSON demandé.",
    ]
    return "\n".join(parts)


# --- D. Steelman ------------------------------------------------------------------------------
STEELMAN_SYSTEM = (
    "Tu es désigné CONTRADICTEUR d'une étude. Avant toute critique, tu dois construire la "
    "MEILLEURE version de la position visée : formulée de sorte que ses partisans la "
    "reconnaissent comme fidèle et même renforcée. Puis, séparément, tu exposes ses meilleurs "
    "scénarios d'échec et ta critique.\n"
    "Interdits : caricaturer, affaiblir ou déformer la position (homme de paille) ; mêler la "
    "critique au steelman ; reformuler de façon décorative sans en restituer les forces "
    "réelles.\n\n"
    + COMPACT
    + ' : {"target": "P1", "steelman": "…", "strengths": ["…"], "failure_scenarios": ["…"], '
    '"critique": "…"}'
)


def build_steelman_prompt(
    *, contradictor_label: str, target_label: str, target_position: str, target_arguments: str
) -> str:
    return "\n".join(
        [
            f"Tu es {contradictor_label}. Position visée : {target_label}.",
            f"Énoncé de la position : {target_position.strip()}",
            "Arguments et hypothèses de son tenant : "
            + (target_arguments.strip() or "(non détaillés)"),
            "",
            "Construis d'abord le steelman, puis les scénarios d'échec, puis ta critique.",
        ]
    )


RECOGNITION_SYSTEM = (
    "Une autre perspective a reformulé TA position sous sa meilleure forme (steelman). Dis "
    "honnêtement si cette reformulation te représente : yes (fidèle, voire renforcée), partial "
    "(fidèle mais incomplète : indique les points manquants), no (déformée ou affaiblie : indique "
    "ce qui est faux). Tu n'as rien à défendre ici, seulement à reconnaître ou non.\n\n"
    + COMPACT
    + ' : {"recognized": "yes|partial|no", "missing_points": ["…"], "comment": "…"}'
)


def build_recognition_prompt(
    *, own_label: str, own_position: str, steelman: str, strengths: list[str]
) -> str:
    return "\n".join(
        [
            f"Ta position ({own_label}) : {own_position.strip()}",
            "",
            "Reformulation proposée (steelman) :",
            steelman.strip(),
            "Forces attribuées : " + (" ; ".join(strengths) if strengths else "(aucune)"),
            "",
            "Cette reformulation te représente-t-elle ? Réponds au format JSON demandé.",
        ]
    )


def strawman_flags(steelman: SteelmanOutput) -> list[str]:
    """Contrôles déterministes d'un steelman décoratif ou déformé (avant reconnaissance)."""
    flags: list[str] = []
    text = steelman.steelman.strip()
    if len(text) < 80:
        flags.append("steelman trop court pour restituer une position")
    if not steelman.strengths:
        flags.append("aucune force attribuée à la position visée")
    if text and text == steelman.critique.strip():
        flags.append("le steelman est identique à la critique")
    lowered = text.lower()
    if any(m in lowered for m in ("naïf", "naïve", "absurde", "ridicule", "évidemment faux")):
        flags.append("vocabulaire dépréciatif dans le steelman")
    return flags


def select_contradictor(
    experts: list[dict[str, Any]], dominant_experts: list[str], labels: dict[str, str]
) -> str | None:
    """Désigne le contradicteur : hors de la position dominante, angle critique de préférence."""
    candidates = [e for e in experts if e["expert_id"] not in dominant_experts]
    if not candidates:
        return None
    critical = [e for e in candidates if e.get("angle") in CRITICAL_ANGLE_TITLES]
    chosen = (critical or candidates)[0]
    return str(chosen["expert_id"])


def is_premature_convergence(
    *, effective_class: str, divergence_index: float, objection_count: int
) -> bool:
    """Convergence immédiate sur un enjeu qui le justifie → contrôle de convergence (steelman)."""
    if objection_count > 0 or divergence_index > 0.0:
        return False
    cls = normalize_class(effective_class)
    return cls in STEELMAN_CLASSES or cls == "importante"


# --- E. Recherche ciblée : sélection des questions matérielles --------------------------------
def material_fact_questions(
    confrontations: dict[str, ConfrontationOutput | None],
    cartography: dict[str, Any],
    labels: dict[str, str],
    *,
    cap: int,
) -> list[dict[str, Any]]:
    """Questions factuelles dont dépend un désaccord pertinent (dédoublonnées, plafonnées)."""
    seen: set[str] = set()
    questions: list[dict[str, Any]] = []
    for expert_id, out in confrontations.items():
        if out is None:
            continue
        for act in out.acts:
            question = act.fact_question.strip()
            if not (act.depends_on_fact and question):
                continue
            key = " ".join(question.lower().split())
            if key in seen:
                continue
            seen.add(key)
            questions.append(
                {
                    "question": question,
                    "claim": act.text,
                    "raised_by": labels.get(expert_id, expert_id),
                    "target": act.target,
                    "nature": act.nature,
                }
            )
    # Objections typées « fait » au Tour 0 (cartographie) qui ne sont pas déjà couvertes.
    for d in cartography.get("disagreements", []):
        if d.get("nature") != "fact" or d.get("source") == "greffier":
            continue
        question = str(d.get("target") or d.get("description") or "").strip()
        key = " ".join(question.lower().split())
        if not question or key in seen:
            continue
        seen.add(key)
        questions.append(
            {
                "question": question,
                "claim": d.get("description", ""),
                "raised_by": str(d.get("source", "")),
                "target": "",
                "nature": "fact",
            }
        )
    return questions[:cap]


# --- F. Révision -------------------------------------------------------------------------------
REVISION_SYSTEM = (
    "Tu es une perspective d'une étude. Tu reçois : les objections qui te sont adressées, "
    "l'éventuelle critique issue d'un steelman, et les NOUVELLES PREUVES arrivées depuis ta "
    "position initiale. Décide : maintain (rien de nouveau ne justifie de changer), modify (une "
    "preuve ou un argument change ta position), nuance (ta position tient sous condition), "
    "abandon (ta position ne tient plus).\n"
    "Règles : tu changes d'avis devant une PREUVE ou un argument nouveau, jamais sous simple "
    "insistance ou répétition ; tu ne changes pas d'avis pour faire plaisir ; tu indiques "
    "exactement ce qui a déclenché ta décision (identifiants d'objections ou de preuves) et "
    "pourquoi.\n\n"
    + COMPACT
    + ' : {"decision": "maintain|modify|nuance|abandon", "revised_position": "…", "reason": "…", '
    '"triggered_by": ["OBJ-3", "EV-1"]}'
)


def build_revision_prompt(
    *,
    own_label: str,
    own_position: str,
    objections: list[dict[str, Any]],
    steelman_critique: str,
    new_evidence: list[dict[str, Any]],
) -> str:
    parts = [f"Ta position initiale ({own_label}) :", own_position.strip(), ""]
    parts.append("Objections qui te sont adressées :")
    if objections:
        for o in objections:
            parts.append(f"- {o['id']} [{o['nature']}] de {o['from']} : {o['text']}")
    else:
        parts.append("- aucune")
    if steelman_critique.strip():
        parts += ["", "Critique issue du steelman de ta position :", steelman_critique.strip()]
    parts.append("")
    parts.append("Nouvelles preuves arrivées depuis ta position initiale :")
    if new_evidence:
        for e in new_evidence:
            parts.append(
                f"- {e['id']} : {e['claim']} — source : {e.get('source') or 'aucune'} "
                f"(fiabilité {e.get('reliability', 'unknown')}, statut {e.get('status', '')})"
            )
    else:
        parts.append("- aucune")
    parts += ["", "Décide et justifie au format JSON demandé."]
    return "\n".join(parts)


# --- G. Consolidation, comparaison, synthèse, porte qualité ------------------------------------
CONSOLIDATION_SYSTEM = (
    "Tu es le GREFFIER d'une étude. Tu regroupes les options proposées en FAMILLES STRATÉGIQUES : "
    "une famille réunit uniquement des options réellement équivalentes (même orientation de fond). "
    "Les variantes conservées et les désaccords internes à une famille restent visibles. Deux "
    "options proches mais réellement différentes ne sont PAS fusionnées : indique pourquoi. Tu "
    "ne classes pas, tu ne préfères pas, tu ne recommandes pas.\n\n"
    + COMPACT
    + ' : {"families": [{"family_id": "F1", "label": "…", "kind": "build|integrate|buy|wait|test|'
    'simplify|do_nothing|other", "option_ids": ["E1-O1"], "variants": [{"option_id": "E2-O1", '
    '"difference": "…"}], "internal_disagreements": ["…"]}], "not_merged_because": '
    '[{"option_ids": ["E1-O1", "E3-O1"], "reason": "…"}]}'
)


def build_consolidation_prompt(
    *, options: list[dict[str, Any]], revised_positions: list[tuple[str, str]]
) -> str:
    parts = ["Options atomiques (identifiant : libellé [nature] — résumé) :"]
    for o in options:
        parts.append(f"- {o['option_id']} : {o['label']} [{o['kind']}] — {o.get('summary', '')}")
    parts += ["", "Positions après révision :"]
    for label, position in revised_positions:
        parts.append(f"- {label} : {position}")
    parts += ["", "Produis les familles, variantes, désaccords internes et non-fusions motivées."]
    return "\n".join(parts)


COMPARISON_SYSTEM = (
    "Tu compares des familles stratégiques sur des critères COMMUNS pertinents pour le problème. "
    "Noyau minimal lorsque pertinent : résultat attendu, coût, délai, risque, réversibilité, "
    "dépendances, qualité des preuves, principales inconnues ; le problème peut en appeler "
    "d'autres. Chaque appréciation est qualitative et indique sa BASE : evidence (preuve "
    "sourcée), inference, hypothesis, unknown, ceo_input, model_knowledge. Aucun score "
    "numérique. Le nombre de "
    "perspectives favorables à une option n'est jamais un critère : la preuve prime sur la "
    "majorité.\n\n"
    + COMPACT
    + ' : {"criteria": ["résultat attendu", "coût", "…"], "rows": [{"family_id": "F1", '
    '"assessments": {"coût": {"value": "…", "basis": "evidence|inference|hypothesis|unknown|'
    'ceo_input|model_knowledge"}}}], "notes": "…"}'
)


def build_comparison_prompt(
    *,
    problem: str,
    constraints: list[str],
    families: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    unknowns: list[str],
) -> str:
    parts = [f"Problème compris : {problem}"]
    if constraints:
        parts.append("Contraintes : " + " ; ".join(constraints))
    parts.append("Familles stratégiques :")
    for f in families:
        parts.append(
            f"- {f['family_id']} {f['label']} [{f['kind']}] — options {', '.join(f['option_ids'])}"
            + (
                f" — désaccords internes : {' ; '.join(f['internal_disagreements'])}"
                if f.get("internal_disagreements")
                else ""
            )
        )
    parts.append("Preuves disponibles :")
    if evidence:
        for e in evidence:
            parts.append(
                f"- {e['id']} {e['claim']} — {e.get('provenance', '')} — source : "
                f"{e.get('source') or 'aucune'} — fiabilité {e.get('reliability', 'unknown')}"
            )
    else:
        parts.append("- aucune preuve externe")
    if unknowns:
        parts.append("Inconnues restantes : " + " ; ".join(unknowns[:15]))
    parts += ["", "Compare les familles au format JSON demandé."]
    return "\n".join(parts)


SYNTHESIS_SYSTEM = (
    "Tu es le SYNTHÉTISEUR d'une étude, distinct des perspectives qui ont délibéré. Tu produis une "
    "recommandation DÉCISIONNELLE en 14 champs, à partir de la matière fournie (positions "
    "révisées, familles, comparaison, preuves, désaccords résiduels). Règles :\n"
    "- la recommandation peut être build, buy, integrate, simplify, test, wait, do_nothing, "
    "abandon ou other ; tu n'es jamais obligé de recommander de construire ;\n"
    "- la preuve prime sur la majorité ; une option majoritaire réfutée par un fait meurt ;\n"
    "- tu conserves les désaccords résiduels et les opinions minoritaires sérieuses ; tu ne "
    "fabriques pas de consensus ;\n"
    "- si l'information manque pour décider honnêtement, information_insufficient = true et la "
    "recommandation est de type test/wait avec la prochaine expérience à conduire ;\n"
    "- si un désaccord dépend de valeurs ou d'appétence au risque, tu le dis : il revient au CEO "
    ";\n"
    "- les preuves sont étiquetées par provenance : ceo_input, external, model_knowledge, "
    "inference, hypothesis ; aucune source inventée ;\n"
    "- la confiance (low|medium|high) est justifiée par la stabilité, les preuves, les "
    "inconnues.\n\n"
    + COMPACT
    + ' : {"problem_understood": "…", "objective": "…", "constraints": ["…"], "assumptions": '
    '[{"text": "…", "status": "verified|unverified"}], "options": [{"family_id": "F1", "label": '
    '"…", "kind": "…"}], "evidence": [{"claim": "…", "source": "…", "reliability": "…", '
    '"provenance": "ceo_input|external|model_knowledge|inference|hypothesis"}], "advantages": '
    '["…"], "disadvantages": ["…"], "risks": ["…"], "recommendation": {"kind": "build|buy|'
    'integrate|simplify|test|wait|do_nothing|abandon|other", "family_id": "F1", "statement": "…", '
    '"rationale": "…"}, "confidence": {"level": "low|medium|high", "justification": "…"}, '
    '"residual_disagreements": [{"between": ["P1", "P2"], "nature": "solution|hypothesis|fact|'
    'value|other", "description": "…"}], "change_conditions": ["…"], "next_action": "…", '
    '"information_insufficient": false}'
)


def build_synthesis_prompt(*, matter: str) -> str:
    return matter + "\n\nProduis la recommandation en 14 champs au format JSON demandé."


GATE_SYSTEM = (
    "Tu es la PORTE QUALITÉ d'une étude, instance distincte du synthétiseur. Tu ne réécris pas la "
    "recommandation : tu la contrôles. Vérifie : (1) conclusion_follows_options — la "
    "recommandation découle des familles réellement examinées ; (2) evidence_labeled — chaque "
    "preuve a une "
    "provenance et aucune source n'est inventée ; (3) minorities_preserved — les désaccords "
    "résiduels et minorités sérieuses figurent ; (4) steelman_done_if_required — le steelman a eu "
    "lieu quand il était requis ; (5) no_forced_consensus — aucun ralliement forcé ni décompte "
    "présenté comme décision ; (6) honest_about_gaps — les inconnues critiques sont déclarées et, "
    "si l'information manque, la recommandation est de type test/wait.\n\n"
    + COMPACT
    + ' : {"passed": true, "checks": {"conclusion_follows_options": true, '
    '"evidence_labeled": true, "minorities_preserved": true, "steelman_done_if_required": true, '
    '"no_forced_consensus": true, '
    '"honest_about_gaps": true}, "issues": ["…"]}'
)


def build_gate_prompt(
    *,
    recommendation_json: str,
    families: list[dict[str, Any]],
    residual: list[dict[str, Any]],
    steelman_required: bool,
    steelman_done: bool,
    unknowns: list[str],
) -> str:
    parts = ["Recommandation à contrôler (JSON) :", recommendation_json, ""]
    parts.append(
        "Familles examinées : " + " ; ".join(f"{f['family_id']} {f['label']}" for f in families)
    )
    parts.append(
        "Désaccords résiduels enregistrés par le facilitateur : "
        + (" ; ".join(d.get("description", "") for d in residual) or "aucun")
    )
    parts.append(f"Steelman requis : {steelman_required} — réalisé : {steelman_done}")
    if unknowns:
        parts.append("Inconnues critiques restantes : " + " ; ".join(unknowns[:10]))
    parts += ["", "Rends ton contrôle au format JSON demandé."]
    return "\n".join(parts)
