"""Interface CEO minimale (Streamlit) de la fabrique de solutions AI-SOS.

Responsabilité unique : **rendre utilisable**. Le CEO soumet un problème / une idée /
un objectif, consulte les plans candidats, approuve un plan ou demande une révision —
sans `curl`. Toute la logique métier (équipe IA, persistance) reste côté API FastAPI :
cette interface ne fait qu'appeler l'API via `SolutionPlansAPIClient`.

Lancement :
    Terminal 1 : cd product && .venv/bin/uvicorn app.main:app --reload
    Terminal 2 : cd product && .venv/bin/streamlit run ui/streamlit_app.py
"""

from __future__ import annotations

import os
from typing import Any

import streamlit as st

from ui.api_client import DEFAULT_API_URL, APIError, SolutionPlansAPIClient

FOUNDING_PHRASE = (
    "Chaque problème, chaque idée ou chaque objectif mérite une équipe d'experts. "
    "AI-SOS crée cette équipe pour l'analyser, le structurer et le transformer en "
    "solution concrète."
)

IMPROVEMENT_PHRASE = (
    "Lorsqu'une solution existe déjà, AI-SOS l'analyse, identifie ses faiblesses, propose "
    "des améliorations et la fait évoluer afin de la rendre plus performante, plus "
    "différenciante et plus unique."
)

INPUT_TYPES = ["problem", "idea", "objective"]

STATUS_LABELS = {
    "candidate": "🟡 Candidat",
    "approved": "🟢 Approuvé",
    "revision_requested": "🟠 Révision demandée",
    "draft": "🔴 Brouillon (échec de génération)",
}


def status_badge(status: str) -> str:
    """Libellé lisible d'un statut de gouvernance."""
    return STATUS_LABELS.get(status, status)


def get_client() -> SolutionPlansAPIClient:
    """Construit le client API à partir de la variable d'environnement `AI_SOS_API_URL`."""
    api_url = os.environ.get("AI_SOS_API_URL", DEFAULT_API_URL)
    return SolutionPlansAPIClient(base_url=api_url)


def render_submit(client: SolutionPlansAPIClient) -> None:
    """Section 1 — Soumettre une entrée CEO et générer un plan candidat."""
    st.header("1. Soumettre une entrée CEO")
    with st.form("submit_input"):
        input_type = st.selectbox("Type d'entrée", INPUT_TYPES, index=0)
        title = st.text_input("Titre")
        description = st.text_area("Description")
        submitted = st.form_submit_button("Générer le plan candidat")

    if not submitted:
        return
    if not title.strip() or not description.strip():
        st.error("Le titre et la description sont obligatoires.")
        return
    with st.spinner("L'équipe IA travaille (Analyste → Architecte → Relecteur risques)…"):
        try:
            plan = client.create_plan(input_type, title.strip(), description.strip())
        except APIError as exc:
            st.error(f"Échec de l'appel API : {exc}")
            return
    if plan.get("status") == "draft":
        st.warning(
            "Plan enregistré en **brouillon** : la génération LLM a échoué "
            f"(clé API manquante ?). Erreur : {plan.get('error', '')}"
        )
    else:
        st.success(f"Plan candidat #{plan.get('id')} créé.")
    st.session_state["selected_plan_id"] = plan.get("id")


def render_plans_list(client: SolutionPlansAPIClient) -> list[dict[str, Any]]:
    """Section 2 — Lister les plans candidats existants."""
    st.header("2. Plans candidats")
    try:
        plans = client.list_plans()
    except APIError as exc:
        st.error(f"Impossible de récupérer les plans : {exc}")
        return []

    if not plans:
        st.info("Aucun plan pour l'instant. Soumettez une première entrée ci-dessus.")
        return []

    for plan in plans:
        summary = (plan.get("candidate_plan") or plan.get("description") or "").strip()
        short = summary[:140] + ("…" if len(summary) > 140 else "")
        st.markdown(
            f"**#{plan.get('id')}** · `{plan.get('input_type')}` · "
            f"{status_badge(plan.get('status', ''))} · {plan.get('created_at', '')}\n\n"
            f"**{plan.get('title', '')}** — {short}"
        )
    ids = [int(plan["id"]) for plan in plans]
    current = st.session_state.get("selected_plan_id")
    default_index = ids.index(current) if current in ids else 0
    selected = st.selectbox("Sélectionner un plan à détailler", ids, index=default_index)
    st.session_state["selected_plan_id"] = selected
    return plans


def render_plan_detail(client: SolutionPlansAPIClient) -> None:
    """Section 3 — Détail complet du plan sélectionné."""
    st.header("3. Détail du plan sélectionné")
    plan_id = st.session_state.get("selected_plan_id")
    if plan_id is None:
        st.info("Sélectionnez un plan dans la liste.")
        return
    try:
        plan = client.get_plan(int(plan_id))
    except APIError as exc:
        st.error(f"Impossible de récupérer le plan : {exc}")
        return

    st.subheader(f"#{plan.get('id')} — {plan.get('title', '')}")
    st.write(f"**Statut :** {status_badge(plan.get('status', ''))}")
    st.write(f"**Type :** `{plan.get('input_type')}` · **Modèle :** {plan.get('llm_model', '')}")
    st.write(
        f"**Créé :** {plan.get('created_at', '')} · **Mis à jour :** {plan.get('updated_at', '')}"
    )

    if plan.get("error"):
        st.error(f"Erreur historisée : {plan['error']}")

    _section("Texte original (description CEO)", plan.get("description", ""))
    _section("Analyse (Analyste)", plan.get("analysis", ""))
    _section("Plan de solution candidat (Architecte)", plan.get("candidate_plan", ""))
    _section("Hypothèses (Relecteur risques)", plan.get("assumptions", ""))
    _section("Risques (Relecteur risques)", plan.get("risks", ""))
    _section("Expertises nécessaires", plan.get("expertise_needs", ""))

    render_ceo_actions(client, plan)


def _section(title: str, content: str) -> None:
    """Affiche un bloc titre + contenu (placeholder si vide)."""
    st.markdown(f"**{title}**")
    st.write(content.strip() if content and content.strip() else "_(vide)_")


def render_ceo_actions(client: SolutionPlansAPIClient, plan: dict[str, Any]) -> None:
    """Section 4 — Actions de gouvernance CEO (approuver / demander révision)."""
    st.header("4. Validation CEO")
    st.caption(
        "L'approbation change le statut du plan. **Aucune exécution n'est déclenchée** : "
        "la mise en œuvre reste une décision humaine ultérieure. Le plan n'est jamais "
        "présenté comme une solution finale."
    )
    plan_id = int(plan["id"])
    col_approve, col_revision = st.columns(2)
    with col_approve:
        if st.button("✅ Approuver ce plan"):
            _act(
                lambda: client.approve_plan(plan_id),
                "Plan approuvé (aucune exécution déclenchée).",
            )
    with col_revision:
        if st.button("🟠 Demander une révision"):
            _act(lambda: client.request_revision(plan_id), "Révision demandée.")


def _act(action: Any, success_message: str) -> None:
    """Exécute une action CEO et affiche le résultat, avec rafraîchissement."""
    try:
        action()
    except APIError as exc:
        st.error(f"Action impossible : {exc}")
        return
    st.success(success_message)
    st.rerun()


def render_improvement_submit(client: SolutionPlansAPIClient) -> None:
    """Amélioration — soumettre une solution existante et générer une version améliorée."""
    st.header("1. Soumettre une solution existante")
    st.caption(IMPROVEMENT_PHRASE)
    with st.form("submit_improvement"):
        title = st.text_input("Titre de la solution existante")
        description = st.text_area("Description de la solution existante")
        context = st.text_area("Contexte / marché / utilisateurs visés")
        improvement_goals = st.text_area("Objectifs d'amélioration")
        constraints = st.text_area("Contraintes éventuelles")
        notes = st.text_area("Notes libres (optionnel)")
        submitted = st.form_submit_button("Analyser et proposer une amélioration")

    if not submitted:
        return
    if not title.strip() or not description.strip():
        st.error("Le titre et la description de la solution existante sont obligatoires.")
        return
    spinner_msg = (
        "L'équipe d'amélioration travaille "
        "(Analyste → Faiblesses → Améliorations → Différenciation)…"
    )
    with st.spinner(spinner_msg):
        try:
            improvement = client.create_improvement(
                title.strip(),
                description.strip(),
                context.strip(),
                improvement_goals.strip(),
                constraints.strip(),
                notes.strip(),
            )
        except APIError as exc:
            st.error(f"Échec de l'appel API : {exc}")
            return
    if improvement.get("status") == "draft":
        st.warning(
            "Amélioration enregistrée en **brouillon** : la génération LLM a échoué "
            f"(clé API manquante ?). Erreur : {improvement.get('error', '')}"
        )
    else:
        st.success(f"Amélioration candidate #{improvement.get('id')} créée.")
    st.session_state["selected_improvement_id"] = improvement.get("id")


def render_improvements_list(client: SolutionPlansAPIClient) -> None:
    """Amélioration — lister les améliorations candidates existantes."""
    st.header("2. Améliorations candidates")
    try:
        improvements = client.list_improvements()
    except APIError as exc:
        st.error(f"Impossible de récupérer les améliorations : {exc}")
        return

    if not improvements:
        st.info("Aucune amélioration pour l'instant. Soumettez une solution existante ci-dessus.")
        return

    for item in improvements:
        summary = (item.get("improved_solution_candidate") or item.get("description") or "").strip()
        short = summary[:140] + ("…" if len(summary) > 140 else "")
        st.markdown(
            f"**#{item.get('id')}** · {status_badge(item.get('status', ''))} · "
            f"{item.get('created_at', '')}\n\n**{item.get('title', '')}** — {short}"
        )
    ids = [int(item["id"]) for item in improvements]
    current = st.session_state.get("selected_improvement_id")
    default_index = ids.index(current) if current in ids else 0
    selected = st.selectbox("Sélectionner une amélioration à détailler", ids, index=default_index)
    st.session_state["selected_improvement_id"] = selected


def render_improvement_detail(client: SolutionPlansAPIClient) -> None:
    """Amélioration — détail complet de l'amélioration sélectionnée."""
    st.header("3. Détail de l'amélioration sélectionnée")
    improvement_id = st.session_state.get("selected_improvement_id")
    if improvement_id is None:
        st.info("Sélectionnez une amélioration dans la liste.")
        return
    try:
        item = client.get_improvement(int(improvement_id))
    except APIError as exc:
        st.error(f"Impossible de récupérer l'amélioration : {exc}")
        return

    st.subheader(f"#{item.get('id')} — {item.get('title', '')}")
    st.write(f"**Statut :** {status_badge(item.get('status', ''))}")
    st.write(
        f"**Créé :** {item.get('created_at', '')} · **Mis à jour :** {item.get('updated_at', '')}"
    )
    if item.get("error"):
        st.error(f"Erreur historisée : {item['error']}")

    _section("Solution existante (description CEO)", item.get("description", ""))
    _section("Contexte", item.get("context", ""))
    _section("Objectifs d'amélioration", item.get("improvement_goals", ""))
    _section("Analyse de la solution existante", item.get("existing_solution_analysis", ""))
    _section("Forces identifiées", item.get("identified_strengths", ""))
    _section("Faiblesses identifiées", item.get("identified_weaknesses", ""))
    _section("Améliorations proposées", item.get("proposed_improvements", ""))
    _section("Version améliorée candidate", item.get("improved_solution_candidate", ""))
    _section("Éléments différenciants", item.get("differentiation", ""))
    _section("Risques / hypothèses", item.get("risks", ""))
    _section("Expertises nécessaires", item.get("expertise_needs", ""))

    render_improvement_actions(client, item)


def render_improvement_actions(client: SolutionPlansAPIClient, item: dict[str, Any]) -> None:
    """Amélioration — actions de gouvernance CEO (approuver / demander révision)."""
    st.header("4. Validation CEO")
    st.caption(
        "L'approbation change le statut. **Aucune exécution n'est déclenchée** et l'amélioration "
        "n'est jamais présentée comme une solution finale : la mise en œuvre reste humaine."
    )
    improvement_id = int(item["id"])
    col_approve, col_revision = st.columns(2)
    with col_approve:
        if st.button("✅ Approuver cette amélioration"):
            _act(
                lambda: client.approve_improvement(improvement_id),
                "Amélioration approuvée (aucune exécution déclenchée).",
            )
    with col_revision:
        if st.button("🟠 Demander une révision", key="improvement_revision"):
            _act(
                lambda: client.request_improvement_revision(improvement_id),
                "Révision demandée.",
            )


def main() -> None:
    """Point d'entrée de l'interface CEO."""
    st.set_page_config(page_title="AI-SOS — Fabrique de solutions", page_icon="🧭")
    st.title("AI-SOS — Fabrique de solutions")
    st.caption(FOUNDING_PHRASE)

    client = get_client()
    st.sidebar.write(f"**API :** {client.base_url}")
    try:
        client.health()
        st.sidebar.success("API joignable")
    except APIError:
        st.sidebar.error("API injoignable — lancez FastAPI (uvicorn app.main:app).")

    tab_create, tab_improve = st.tabs(["Créer une solution", "Améliorer une solution existante"])
    with tab_create:
        render_submit(client)
        render_plans_list(client)
        render_plan_detail(client)
    with tab_improve:
        render_improvement_submit(client)
        render_improvements_list(client)
        render_improvement_detail(client)


if __name__ == "__main__":
    main()
