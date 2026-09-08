"""Exploration OT-V1 (incrément 1) — prompts du Tour 0, de l'auto-qualification et du greffier.

Ce module ne fait **aucun appel** : il construit les prompts et documente les règles d'isolement.
L'orchestrateur (`app.missions`) fait les appels, tient le budget et le journal.

Règles d'isolement du Tour 0 : chaque expert reçoit le **même dossier de cadrage**, l'entrée du
demandeur, et **sa propre fiche de perspective** ; il ne reçoit aucun exposé d'un autre expert. Le
prompt complet de chaque expert est conservé au journal avec son empreinte pour le prouver.

Après clôture du Tour 0 (toutes les positions persistées), chaque expert reçoit la liste
**anonymisée** des autres positions et qualifie la sienne (identique / variante / différente). Ce
qui reste ambigu est confié à un **greffier** au schéma fermé : il regroupe et qualifie, sans
préférence, sans classement, sans recommandation.
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.mission_composition import ExpertSpec
from app.mission_framing import INPUT_TYPE_LABELS

EXPERT_CALL_TYPE = "expert_tour0"
SELF_QUAL_CALL_TYPE = "self_qualification"
CLERK_CALL_TYPE = "clerk"

EXPERT_SYSTEM = (
    "Tu es une perspective spécialisée mobilisée au premier tour d'une étude. Tu travailles SEUL : "
    "tu ne connais la position d'aucune autre perspective et tu ne dois pas en supposer. Ta valeur "
    "vient de ton angle propre, de ton honnêteté et de ta précision.\n\n"
    "Règles :\n"
    "1. Prends une position claire depuis ton angle, avec ton raisonnement.\n"
    "2. Propose une ou plusieurs OPTIONS réellement différentes. Les options de non-action sont "
    "légitimes et attendues quand elles sont pertinentes : attendre (wait), tester d'abord (test), "
    "acheter ou intégrer l'existant (buy / integrate), simplifier (simplify), ne rien faire "
    "(do_nothing).\n"
    "3. Déclare tes hypothèses, tes risques, ce que tu IGNORES et ce que tu voudrais VÉRIFIER.\n"
    "4. Formule tes objections éventuelles à la demande ou à une approche évidente, en précisant "
    "leur nature : solution, hypothesis, fact, value.\n"
    "5. Preuves : tu n'as accès à aucune recherche externe. N'invente JAMAIS une citation, une "
    "source, un chiffre précis ou une référence. Ce qui vient de ta connaissance générale doit "
    "être "
    'marqué status = "model_knowledge" ; ce qui devrait être vérifié, status = "unverified". '
    "N'utilise \"verified\" que pour un fait présent dans l'entrée du demandeur, en citant ce "
    "passage comme source.\n"
    "6. Reste proportionné : une situation simple appelle une réponse courte.\n\n"
    "Réponds STRICTEMENT en JSON, sans texte autour, en JSON compact (sans indentation ni "
    "retours à la ligne décoratifs), avec exactement cette structure :\n"
    "{\n"
    '  "position": "…",\n'
    '  "reasoning": "…",\n'
    '  "assumptions": ["…"],\n'
    '  "risks": ["…"],\n'
    '  "unknowns": ["…"],\n'
    '  "to_verify": ["…"],\n'
    '  "options": [{"label": "…", "summary": "…", '
    '"kind": "build|integrate|buy|wait|test|simplify|do_nothing|other"}],\n'
    '  "objections": [{"text": "…", "target": "…", '
    '"nature": "solution|hypothesis|fact|value|other"}],\n'
    '  "evidence": [{"claim": "…", "source": "…", '
    '"status": "verified|unverified|model_knowledge"}]\n'
    "}"
)


def build_expert_prompt(
    *,
    spec: ExpertSpec,
    framing_dossier: str,
    input_type: str,
    input_text: str,
    context_text: str,
    ceo_preference: str,
) -> str:
    """Prompt d'un expert du Tour 0 : entrée + dossier de cadrage + sa fiche. Rien d'autre."""
    parts = [
        "=== TA FICHE DE PERSPECTIVE ===",
        f"Identifiant : {spec.expert_id}",
        f"Dimension étudiée : {spec.dimension}",
        f"Angle : {spec.angle_title}",
        f"Ce que tu regardes en priorité : {spec.angle_of_analysis}",
        f"Ton rôle : {spec.debate_role}",
    ]
    if spec.expected_objections:
        parts.append(f"Objections que tu cherches typiquement : {spec.expected_objections}")
    if spec.contradicts_preference and ceo_preference.strip():
        parts.append(
            "Mandat particulier : le demandeur a exprimé une préférence ; ton rôle est de "
            "construire la meilleure objection possible à cette préférence, si elle est fondée. "
            f"Préférence exprimée : {ceo_preference.strip()}"
        )
    parts += [
        "",
        "=== ENTRÉE DU DEMANDEUR ===",
        f"Nature : {INPUT_TYPE_LABELS.get(input_type, input_type)}",
        input_text.strip(),
    ]
    if context_text.strip():
        parts += ["", "=== DOSSIER / CONTEXTE FOURNI ===", context_text.strip()]
    parts += [
        "",
        "=== DOSSIER DE CADRAGE (identique pour toutes les perspectives) ===",
        framing_dossier,
        "",
        "Produis ton exposé initial au format JSON demandé.",
    ]
    return "\n".join(parts)


SELF_QUAL_SYSTEM = (
    "Le premier tour d'une étude est clos. Tu es l'une des perspectives qui y ont participé. On te "
    "montre maintenant, de façon ANONYME, les positions initiales des autres perspectives. Ta "
    "seule "
    "tâche : qualifier la relation entre TA position et chacune des autres.\n"
    "- identical : même orientation de fond, différences de formulation seulement ;\n"
    "- variant : même famille d'approche avec une différence réelle (périmètre, condition, "
    "séquence) ;\n"
    "- different : approche réellement différente ou incompatible.\n"
    "Tu ne révises pas ta position, tu ne juges pas les autres, tu ne recommandes rien.\n\n"
    "Réponds STRICTEMENT en JSON : "
    '{"relations": [{"other_id": "P2", "relation": "identical|variant|different", '
    '"reason": "…"}]}'
)


def build_self_qualification_prompt(
    *, own_label: str, own_position: str, others: list[tuple[str, str]]
) -> str:
    """Prompt d'auto-qualification : sa position + les autres positions anonymisées."""
    parts = [f"Ta position ({own_label}) :", own_position.strip(), "", "Autres positions :"]
    for label, position in others:
        parts.append(f"- {label} : {position.strip()}")
    parts += ["", "Qualifie ta relation à chacune des autres positions, au format JSON demandé."]
    return "\n".join(parts)


CLERK_SYSTEM = (
    "Tu es le GREFFIER d'une étude. Tu n'es pas un décideur : tu n'exprimes aucune préférence, "
    "tu ne "
    "classes rien, tu ne recommandes rien, tu n'ajoutes aucun avis. Tu ne fais que deux choses :\n"
    "1. regrouper les options qui sont réellement équivalentes (même orientation de fond), en "
    "motivant chaque regroupement ; une option sans équivalent reste seule ;\n"
    "2. qualifier la NATURE de chaque désaccord observable entre positions : solution (quoi "
    "faire), "
    "hypothesis (une supposition diverge), fact (un fait vérifiable diverge), value (un arbitrage "
    "de valeurs ou d'appétence au risque).\n"
    "Toute sortie qui hiérarchise, préfère ou recommande est une faute.\n\n"
    "Réponds STRICTEMENT en JSON, sans texte autour :\n"
    '{"groups": [{"option_ids": ["E1-O1", "E3-O2"], "label": "…", "motivation": "…"}],\n'
    ' "disagreements": [{"between": ["P1", "P2"], '
    '"nature": "solution|hypothesis|fact|value|other", '
    '"description": "…"}]}'
)


def build_clerk_prompt(
    *,
    options: list[dict[str, Any]],
    positions: list[tuple[str, str]],
    ambiguities: list[dict[str, Any]],
) -> str:
    """Prompt du greffier : options identifiées, positions anonymisées, ambiguïtés à qualifier."""
    parts = ["Options proposées (identifiant : libellé — résumé) :"]
    for opt in options:
        parts.append(f"- {opt['option_id']} : {opt['label']} — {opt.get('summary', '')}")
    parts += ["", "Positions (anonymisées) :"]
    for label, position in positions:
        parts.append(f"- {label} : {position.strip()}")
    if ambiguities:
        parts += ["", "Ambiguïtés résiduelles après auto-qualification :"]
        for amb in ambiguities:
            parts.append(f"- {amb.get('detail', '')}")
    parts += ["", "Produis regroupements motivés et désaccords qualifiés, au format JSON demandé."]
    return "\n".join(parts)


def prompt_fingerprint(system: str, prompt: str) -> str:
    """Empreinte SHA-256 du couple (system, prompt), conservée au journal."""
    return hashlib.sha256((system + "\n␞\n" + prompt).encode("utf-8")).hexdigest()
