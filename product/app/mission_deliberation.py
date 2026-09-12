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

import re
import unicodedata
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

# --- Garde-fou épistémique (audit v1.3) : hypothèses conditionnelles explicites ------------------
EPISTEMIC_RULE = (
    "Calibration épistémique : distingue (1) fait fourni, (2) calcul conditionnel explicite "
    "(« X si Y », « à volume constant »), (3) hypothèse comportementale (« parce que Y restera "
    "vrai »), (4) prévision, (5) inférence du modèle. Un calcul conditionnel donné avec sa "
    "condition est VALIDE sous cette condition : ne le requalifie jamais en erreur ou en "
    "incohérence ; dis plutôt qu'il est insuffisant pour estimer l'effet net si la condition "
    "peut changer. Seule une hypothèse comportementale (la condition présentée comme prédiction) "
    "peut être contestée comme telle ; une inconnue déclarée reste un scénario conditionnel, pas "
    "une prévision."
)
EPISTEMIC_LABELS = {
    "conditional_calculation": "calcul conditionnel (valide sous sa condition)",
    "behavioural_hypothesis": "hypothèse comportementale (condition présentée comme prédiction)",
    "declared_unknown": "inconnue déclarée (scénario conditionnel, pas une prévision)",
    "forecast": "prévision",
    "statement": "affirmation",
}
_COND_RE = re.compile(
    r"\b(si\b|a condition|en supposant|sous l hypothese|toutes choses egales|"
    r"a [a-z]+ constant(?:e|s|es)?\b|constant(?:e|s|es)?\b|inchang(?:e|ee|es|ees)\b)",
)
_BEHAV_RE = re.compile(
    r"\b(parce que|car|puisque|etant donne que)\b.*"
    r"\b(restera|resteront|sera|seront|va |vont |demeurera)\b"
)
_UNKNOWN_RE = re.compile(
    r"\b(ne connait pas|ne connaissons pas|inconnu|on ignore|incertain|pas connu|sans savoir)\b"
)
_FORECAST_RE = re.compile(
    r"\b(prevoit|prevision|prevu|devrait|devraient|anticip|projette|projection)\b"
)


def _fold(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in stripped if not unicodedata.combining(c))
    return re.sub(r"[^\w\s]", " ", stripped.lower())


def classify_epistemic(text: str) -> str:
    """Classe épistémique déterministe d'un énoncé (garde-fou, pas un jugement de validité).

    `behavioural_hypothesis` prime sur `conditional_calculation` : « X parce que Y restera vrai »
    présente la condition comme une prédiction, contestable ; « X si Y » ne l'est pas.
    """
    folded = " " + _fold(text) + " "
    if _UNKNOWN_RE.search(folded):
        return "declared_unknown"
    if _BEHAV_RE.search(folded):
        return "behavioural_hypothesis"
    if _COND_RE.search(folded):
        return "conditional_calculation"
    if _FORECAST_RE.search(folded):
        return "forecast"
    return "statement"


def epistemic_tag(text: str) -> str:
    """Étiquette lisible ajoutée à un énoncé dans la matière soumise aux instances."""
    return EPISTEMIC_LABELS[classify_epistemic(text)]


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
    "depends_on_fact = true, formule la question précise à rechercher (fact_question) et indique "
    "où la réponse se trouve (fact_source) : internal (données propres du demandeur : ses "
    "clients, ses contrats, ses marges), external (sources publiques), either.\n"
    + EPISTEMIC_RULE
    + "\n\n"
    + COMPACT
    + ' : {"acts": [{"act": "critique|defend|complement|refute|third_way|none", "target": "P2", '
    '"nature": "solution|hypothesis|fact|value|other", "text": "…", "depends_on_fact": false, '
    '"fact_question": "", "fact_source": "internal|external|either"}], "convergence_note": "…"}'
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
        lines.append(
            "Hypothèses avancées : "
            + " ; ".join(f"{h['text']} [{epistemic_tag(h['text'])}]" for h in hyps[:12])
        )
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


# --- D bis. Steelman de l'alternative écartée (B17 — v1.3.6) -----------------------------------
ALTERNATIVE_STEELMAN_SYSTEM = (
    "Tu es désigné AVOCAT d'une alternative que la demande met explicitement sur la table et "
    "qu'aucune perspective de l'étude ne défend. Ta tâche : construire la MEILLEURE défense "
    "possible de cette alternative — ses forces réelles, les conditions sous lesquelles elle "
    "serait le bon choix, ce que ses adversaires sous-estiment — puis, séparément, ses meilleurs "
    "scénarios d'échec. Tu ne la critiques pas ici (un contradicteur distinct le fera) ; tu ne "
    "caricatures ni n'affaiblis rien ; tu n'inventes aucun fait : les conditions de succès sont "
    "formulées comme conditions, pas comme certitudes.\n\n"
    + COMPACT
    + ' : {"target": "ALT", "steelman": "…", "strengths": ["…"], "failure_scenarios": ["…"], '
    '"critique": ""}'
)
ALTERNATIVE_CHALLENGE_SYSTEM = (
    "Une alternative que la demande mettait sur la table a été défendue sous sa meilleure forme "
    "par un avocat désigné (steelman). Tu es un CONTRADICTEUR distinct. Deux tâches, séparées : "
    "(1) reconnaissance — cette défense est-elle la version la plus forte et fidèle de "
    "l'alternative ? yes (forte et fidèle), partial (forte mais incomplète : indique les points "
    "manquants), no (faible, déformée ou décorative) ; (2) critique — la meilleure objection "
    "à cette version FORTE (pas à une version affaiblie), avec les scénarios où elle échoue. Une "
    "objection non argumentée n'est pas recevable ; tu n'inventes aucun fait.\n\n"
    + COMPACT
    + ' : {"recognized": "yes|partial|no", "missing_points": ["…"], "critique": "…", '
    '"failure_scenarios": ["…"]}'
)


def build_alternative_steelman_prompt(
    *,
    advocate_label: str,
    alternative_label: str,
    alternative_kind: str,
    alternative_summaries: list[str],
    problem: str,
    positions_against: list[str],
) -> str:
    return "\n".join(
        [
            f"Tu es {advocate_label}, avocat désigné de l'alternative écartée.",
            f"Alternative à défendre : {alternative_label} [nature : {alternative_kind}]",
            "Formulations rencontrées dans l'étude : "
            + (" ; ".join(alternative_summaries) if alternative_summaries else "(aucune)"),
            f"Problème compris : {problem}",
            "Positions qui l'écartent (résumé) : "
            + (" | ".join(positions_against[:8]) if positions_against else "(aucune)"),
            "",
            "Construis d'abord la meilleure défense, puis ses scénarios d'échec.",
        ]
    )


def build_alternative_challenge_prompt(
    *,
    critic_label: str,
    alternative_label: str,
    steelman: str,
    strengths: list[str],
    failure_scenarios: list[str],
) -> str:
    return "\n".join(
        [
            f"Tu es {critic_label}, contradicteur distinct de l'avocat.",
            f"Alternative défendue : {alternative_label}",
            "Défense proposée (steelman) :",
            steelman.strip(),
            "Forces attribuées : " + (" ; ".join(strengths) if strengths else "(aucune)"),
            "Scénarios d'échec avancés par l'avocat : "
            + (" ; ".join(failure_scenarios) if failure_scenarios else "(aucun)"),
            "",
            "Reconnais (ou non) la force et la fidélité de cette défense, puis formule ta critique "
            "au format JSON demandé.",
        ]
    )


_STOPWORDS = frozenset(
    {
        "avec",
        "sans",
        "pour",
        "dans",
        "sur",
        "une",
        "des",
        "les",
        "aux",
        "par",
        "plus",
        "moins",
        "tout",
        "toute",
        "tous",
        "toutes",
        "cette",
        "cet",
        "ces",
        "leur",
        "leurs",
        "option",
        "options",
        "initiale",
        "initial",
        "proposition",
        "proposee",
        "proposé",
        "proposée",
        "directeur",
        "produit",
        "demandeur",
        "telle",
        "tel",
        "comme",
        "avant",
        "apres",
        "après",
        "entre",
        "vers",
        "afin",
        "dont",
        "donc",
        "mais",
        "elle",
        "elles",
    }
)


def _content_tokens(text: str) -> set[str]:
    """Jetons de contenu (≥ 4 caractères, sans mots vides), tronqués à 6 caractères (racine)."""
    folded = _fold(text)
    tokens = re.findall(r"[a-z0-9€]{4,}", folded)
    return {t[:6] for t in tokens if t not in _STOPWORDS}


def token_overlap(label: str, text: str) -> float:
    """Part des jetons de contenu de `label` présents dans `text` (0 si `label` est vide)."""
    lab = _content_tokens(label)
    if not lab:
        return 0.0
    txt = _content_tokens(text)
    return len(lab & txt) / len(lab)


def find_discarded_alternative(
    *,
    proposals: list[dict[str, Any]],
    option_groups: list[dict[str, Any]],
    options: list[dict[str, Any]],
    positions: list[dict[str, Any]],
    request_text: str,
    endorse_threshold: float = 0.5,
    match_threshold: float = 0.5,
) -> dict[str, Any] | None:
    """Alternative explicitement proposée par la demande et défendue par AUCUNE position (B17).

    Source des propositions : `explicit_proposals` du cadrage (générique : investissement,
    acquisition, attente, externalisation, abandon…) ; repli : options du Tour 0 dont le libellé
    recoupe fortement le texte de la demande. Une proposition est « écartée » si aucune position
    du Tour 0 ne l'endosse (recouvrement lexical du libellé dans la position ≥ seuil). Règle
    déterministe et documentée ; aucun mot-clé métier, aucune nature codée en dur.
    """
    candidates: list[dict[str, Any]] = []
    for p in proposals:
        label = str(p.get("label", "")).strip()
        if not label:
            continue
        matching = [
            o
            for o in options
            if token_overlap(label, o["label"]) >= match_threshold
            or (
                o.get("kind") == p.get("kind")
                and token_overlap(o["label"], label) >= match_threshold
            )
        ]
        candidates.append(
            {
                "label": label,
                "kind": str(p.get("kind", "other")),
                "source": "framing",
                "option_ids": [o["option_id"] for o in matching],
                "summaries": [o.get("summary", "") or o["label"] for o in matching][:5],
                "experts": sorted({o["expert_id"] for o in matching}),
            }
        )
    if not candidates:
        for g in option_groups:
            if token_overlap(g["label"], request_text) >= 0.75:
                members = [o for o in options if o["option_id"] in set(g["option_ids"])]
                candidates.append(
                    {
                        "label": g["label"],
                        "kind": str((g.get("kinds") or ["other"])[0]),
                        "source": "options",
                        "option_ids": list(g["option_ids"]),
                        "summaries": [o.get("summary", "") or o["label"] for o in members][:5],
                        "experts": sorted({o["expert_id"] for o in members}),
                    }
                )
    for cand in candidates:
        endorsed_by = [
            p["label"]
            for p in positions
            if token_overlap(cand["label"], p.get("position", "")) >= endorse_threshold
        ]
        cand["endorsed_by"] = endorsed_by
        if not endorsed_by:
            return cand
    return None


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
FACT_SOURCE_INTERNAL = "internal"
FACT_SOURCE_EXTERNAL = "external"
FACT_SOURCE_EITHER = "either"
_INTERNAL_MARKERS = re.compile(
    r"\b(nos|notre|en interne|interne(s)?|de l'entreprise|de la societe|chez nous|"
    r"nos clients|nos contrats|notre marge|nos donnees|nos equipes|dans l'entreprise|"
    r"du demandeur|de l'organisation)\b"
)


def classify_fact_source(question: str, *, declared: str = "either") -> str:
    """Où la réponse à une question factuelle se trouve (v1.3.6 — §9).

    La déclaration de la perspective (`fact_source`) prime ; à défaut (`either`), un repli lexical
    déterministe reconnaît une question sur les données propres du demandeur (« nos », « notre »,
    « en interne »…) comme `internal`. Tout le reste reste `either` : jamais de fait inventé, jamais
    de fournisseur web appelé pour une donnée interne.
    """
    declared = (declared or "either").strip().lower()
    if declared in {FACT_SOURCE_INTERNAL, FACT_SOURCE_EXTERNAL}:
        return declared
    if _INTERNAL_MARKERS.search(_fold(question)):
        return FACT_SOURCE_INTERNAL
    return FACT_SOURCE_EITHER


def material_fact_questions(
    confrontations: dict[str, ConfrontationOutput | None],
    cartography: dict[str, Any],
    labels: dict[str, str],
    *,
    cap: int,
) -> list[dict[str, Any]]:
    """Questions factuelles dont dépend un désaccord pertinent (dédoublonnées, plafonnées).

    Chaque question conserve sa **provenance de débat** : qui l'a soulevée (`raised_by`), quelle
    position elle vise (`target`) et, surtout, les **positions concernées** (`positions`) — celles
    dont la position dépend du fait : la cible d'un acte de confrontation, ou l'auteur d'une
    objection factuelle du Tour 0. Une même question soulevée par plusieurs actes est fusionnée et
    ses positions concernées sont réunies. C'est cette liste qui décide, plus tard, à qui la preuve
    est soumise en révision : jamais à tout le monde par défaut.
    """
    by_key: dict[str, dict[str, Any]] = {}
    order: list[str] = []

    def _add(
        question: str,
        claim: str,
        raised_by: str,
        target: str,
        nature: str,
        positions: list[str],
        source: str = "either",
    ) -> None:
        key = " ".join(question.lower().split())
        if not key:
            return
        entry = by_key.get(key)
        if entry is None:
            entry = {
                "question": question,
                "claim": claim,
                "raised_by": raised_by,
                "raised_by_all": [raised_by],
                "target": target,
                "nature": nature,
                "positions": [],
                "source": classify_fact_source(question, declared=source),
            }
            by_key[key] = entry
            order.append(key)
        elif raised_by not in entry["raised_by_all"]:
            entry["raised_by_all"].append(raised_by)
        for p in positions:
            if p and p not in entry["positions"]:
                entry["positions"].append(p)

    for expert_id, out in confrontations.items():
        if out is None:
            continue
        for act in out.acts:
            question = act.fact_question.strip()
            if not (act.depends_on_fact and question):
                continue
            _add(
                question,
                act.text,
                labels.get(expert_id, expert_id),
                act.target,
                act.nature,
                [act.target],
                getattr(act, "fact_source", "either"),
            )
    # Objections typées « fait » au Tour 0 (cartographie) qui ne sont pas déjà couvertes : la
    # position concernée est celle de leur auteur (sa position repose sur ce fait).
    for d in cartography.get("disagreements", []):
        if d.get("nature") != "fact" or d.get("source") == "greffier":
            continue
        question = str(d.get("target") or d.get("description") or "").strip()
        if not question:
            continue
        raised_by = labels.get(str(d.get("source", "")), str(d.get("source", "")))
        _add(question, d.get("description", ""), raised_by, "", "fact", [raised_by])
    return [by_key[k] for k in order][:cap]


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
    "ne classes pas, tu ne préfères pas, tu ne recommandes pas. Tu n'emploies que les "
    "identifiants fournis et tu ne recopies pas les libellés au-delà du nécessaire.\n\n"
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
    "- INTERDIT dans « rationale » et « confidence.justification » : invoquer le nombre de "
    "positions, une majorité, une unanimité, un consensus ou « l'absence de réfutation » comme "
    "raison de la recommandation ou de la confiance. Les perspectives sont des instances d'un "
    "même modèle sur le même dossier : leur convergence est une information descriptive, jamais "
    "une preuve. Si tu la mentionnes, sépare-la explicitement de la preuve (« plusieurs "
    "perspectives convergent ; indépendamment, la recommandation repose sur X, Y, Z ») ;\n"
    "- une question factuelle interne (données du demandeur) non résolue et déterminante pour "
    "le choix rend information_insufficient = true et figure dans la prochaine action comme "
    "information à obtenir du demandeur ;\n"
    "- tu conserves les désaccords résiduels et les opinions minoritaires sérieuses ; tu ne "
    "fabriques pas de consensus ;\n"
    "- si l'information manque pour décider honnêtement, information_insufficient = true et la "
    "recommandation est de type test/wait avec la prochaine expérience à conduire ;\n"
    "- si un désaccord dépend de valeurs ou d'appétence au risque, tu le dis : il revient au CEO "
    ";\n"
    "- les preuves sont étiquetées par provenance : ceo_input, external, model_knowledge, "
    "inference, hypothesis ; aucune source inventée ;\n"
    "- la confiance (low|medium|high) est justifiée par la stabilité, les preuves, les "
    "inconnues ;\n- "
    + EPISTEMIC_RULE
    + "\n\n"
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
    "présenté comme décision, et ni « rationale » ni « confidence.justification » n'invoquent "
    "une convergence, une majorité ou l'absence de réfutation comme preuve (la preuve prime sur "
    "la majorité) ; (6) honest_about_gaps — les inconnues critiques sont déclarées et, "
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
