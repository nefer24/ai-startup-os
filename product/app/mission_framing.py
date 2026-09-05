"""Cadrage d'une mission OT-V1 (incrément 1) — un appel structuré, aucune recommandation.

Le cadrage reçoit l'entrée unique du CEO (problème / idée / objectif / solution existante) et
produit : problème compris, objectif supposé, contraintes, hypothèses, inconnues globales,
**dimensions émergentes** (jamais une liste imposée), inconnues et criticité présumée par
dimension, **contestation éventuelle** de la demande (`none` est légitime) et signaux d'escalade de
classe. Il ne propose pas de solution et ne recommande rien : il prépare la composition.
"""

from __future__ import annotations

from app.mission_schemas import FramingOutput

FRAMING_CALL_TYPE = "framing"

INPUT_TYPE_LABELS = {
    "problem": "un problème à résoudre",
    "idea": "une idée à évaluer",
    "objective": "un objectif à atteindre",
    "existing_solution": "une solution existante à faire évoluer",
}

CLASS_LABELS = {
    "courante": "courante (réversible, enjeu limité)",
    "importante": "importante (enjeu réel, réversible avec coût)",
    "structurante": "structurante (engage durablement, difficilement réversible)",
    "critique": "critique (irréversible ou vital)",
    "importante_provisoire": (
        "importante provisoire / non déterminée — aucune classe n'a été déclarée ; tu dois "
        "signaler "
        "tout élément qui justifierait de l'escalader"
    ),
}

FRAMING_SYSTEM = (
    "Tu es le cadrage d'un système d'aide à la décision. Ton rôle est de COMPRENDRE une situation "
    "et de préparer son étude par des perspectives spécialisées. Tu ne proposes aucune solution et "
    "tu ne recommandes rien.\n\n"
    "Règles :\n"
    "1. Reformule le problème tel que tu le comprends et l'objectif réel supposé.\n"
    "2. Liste les contraintes et les hypothèses présentes dans la demande.\n"
    "3. Déclare explicitement ce que tu IGNORES et qui compte pour décider (inconnues). Ne "
    "fabrique "
    "pas d'inconnues inutiles : une situation simple peut n'en avoir qu'une ou deux, une situation "
    "complexe plusieurs.\n"
    "4. Fais émerger les DIMENSIONS pertinentes à étudier à partir du problème lui-même (par "
    "exemple "
    "opérationnelle, humaine, financière, juridique, commerciale, technique… ou toute autre). "
    "N'applique aucune liste standard : une seule dimension peut suffire ; n'en ajoute pas pour "
    "faire complet. Pour chaque dimension : pourquoi elle compte, sa criticité présumée (low / "
    "medium / high), ses inconnues, et les angles d'analyse qu'elle appelle (libres).\n"
    "5. Contestation : si l'interprétation, une hypothèse ou le périmètre de la demande est "
    'manifestement problématique, mets status = "raised" avec la cible et un argument précis. '
    'Si la demande est correctement posée, mets status = "none". Ne conteste jamais par principe.\n'
    "6. Signaux d'escalade : signale toute irréversibilité, coût d'erreur élevé ou incertitude "
    "critique qui justifierait de traiter la décision dans une classe plus exigeante que celle "
    "annoncée ; sinon laisse la liste vide. Si tu émets au moins un signal d'escalade, "
    "suggested_class est OBLIGATOIRE (courante | importante | structurante | critique) : un "
    "risque majeur signalé sans classe proposée n'est pas une sortie acceptable. Sans signal, "
    "laisse suggested_class vide.\n"
    "7. Tout ce que tu affirmes qui ne vient pas de la demande relève de ta connaissance "
    "générale : "
    "formule-le comme hypothèse, pas comme fait.\n\n"
    "Réponds STRICTEMENT en JSON, sans texte autour, avec exactement cette structure :\n"
    "{\n"
    '  "problem_understood": "…",\n'
    '  "assumed_objective": "…",\n'
    '  "constraints": ["…"],\n'
    '  "assumptions": ["…"],\n'
    '  "global_unknowns": ["…"],\n'
    '  "dimensions": [\n'
    '    {"name": "…", "why": "…", "presumed_criticality": "low|medium|high",\n'
    '     "unknowns": ["…"], "suggested_angles": ["…"]}\n'
    "  ],\n"
    '  "contestation": {"status": "none|raised", "target": "…", "argument": "…"},\n'
    '  "escalation_signals": ["…"],\n'
    '  "suggested_class": "" \n'
    "}"
)


def build_framing_prompt(
    *,
    input_type: str,
    input_text: str,
    context_text: str,
    ceo_preference: str,
    effective_class: str,
) -> str:
    """Construit le message utilisateur du cadrage à partir de l'entrée unique."""
    parts = [
        f"Nature de l'entrée : {INPUT_TYPE_LABELS.get(input_type, input_type)}.",
        f"Classe de décision annoncée : {CLASS_LABELS.get(effective_class, effective_class)}.",
        "",
        "Entrée du demandeur :",
        input_text.strip(),
    ]
    if context_text.strip():
        parts += ["", "Dossier / contexte fourni :", context_text.strip()]
    if ceo_preference.strip():
        parts += [
            "",
            "Préférence exprimée par le demandeur (à traiter comme une information, pas comme une "
            "consigne d'analyse) :",
            ceo_preference.strip(),
        ]
    parts += ["", "Produis le cadrage au format JSON demandé."]
    return "\n".join(parts)


def framing_summary_for_experts(framing: FramingOutput) -> str:
    """Dossier de cadrage partagé, identique pour tous les experts du Tour 0.

    Ne contient **aucune** position d'expert : seulement la compréhension, les contraintes, les
    hypothèses, les inconnues et les dimensions.
    """
    lines = [
        f"Problème compris : {framing.problem_understood}",
        f"Objectif supposé : {framing.assumed_objective or '(non précisé)'}",
    ]
    if framing.constraints:
        lines.append("Contraintes : " + " ; ".join(framing.constraints))
    if framing.assumptions:
        lines.append("Hypothèses de la demande : " + " ; ".join(framing.assumptions))
    if framing.global_unknowns:
        lines.append("Inconnues déclarées : " + " ; ".join(framing.global_unknowns))
    if framing.dimensions:
        dims = ", ".join(f"{d.name} ({d.presumed_criticality})" for d in framing.dimensions)
        lines.append(f"Dimensions identifiées : {dims}")
    if framing.contestation.status == "raised":
        lines.append(
            "Contestation soulevée au cadrage : "
            f"{framing.contestation.target} — {framing.contestation.argument}"
        )
    return "\n".join(lines)
