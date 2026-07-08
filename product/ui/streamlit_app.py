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

import json
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


COMPANY_CANDIDATE_NOTICE = (
    "Cette entreprise IA est **candidate**. Elle n'est pas encore exécutée. Aucune production "
    "ni livraison ne commence sans validation CEO explicite."
)


def render_company_compose(client: SolutionPlansAPIClient) -> None:
    """Entreprise IA — choisir une source approuvée et composer une entreprise IA spécialisée."""
    st.header("1. Choisir une source approuvée")
    st.caption(
        "Seule une source **approuvée** (plan ou amélioration) peut être entreprise. "
        + COMPANY_CANDIDATE_NOTICE
    )
    source_type = st.selectbox(
        "Type de source",
        ["solution_plan", "solution_improvement"],
        format_func=lambda value: {
            "solution_plan": "Plan de solution",
            "solution_improvement": "Amélioration de solution",
        }[value],
    )
    try:
        sources = (
            client.list_plans() if source_type == "solution_plan" else client.list_improvements()
        )
    except APIError as exc:
        st.error(f"Impossible de récupérer les sources : {exc}")
        return

    approved = [s for s in sources if s.get("status") == "approved"]
    if not approved:
        st.info(
            "Aucune source approuvée pour ce type. Approuvez d'abord un plan ou une amélioration."
        )
        return

    labels = {int(s["id"]): f"#{s['id']} — {s.get('title', '')}" for s in approved}
    source_id = st.selectbox(
        "Source approuvée", list(labels.keys()), format_func=lambda i: labels[i]
    )
    chosen = next(s for s in approved if int(s["id"]) == source_id)
    summary = (
        chosen.get("candidate_plan") or chosen.get("improved_solution_candidate") or ""
    ).strip()
    if summary:
        st.markdown(f"**Résumé de la source :** {summary[:200]}")

    compose_spinner = (
        "AI-SOS compose l'entreprise IA "
        "(Architect → Départements/Spécialités → Débat → Livraison/Gouvernance)…"
    )
    if st.button("Composer l'entreprise IA spécialisée"):
        with st.spinner(compose_spinner):
            try:
                company = client.create_specialized_company(source_type, int(source_id))
            except APIError as exc:
                st.error(f"Échec de la composition : {exc}")
                return
        if company.get("status") == "draft":
            st.warning(
                "Entreprise IA enregistrée en **brouillon** : la composition a échoué "
                f"(clé API manquante ?). Erreur : {company.get('error', '')}"
            )
        else:
            st.success(f"Entreprise IA spécialisée candidate #{company.get('id')} composée.")
        st.session_state["selected_company_id"] = company.get("id")


def render_companies_list(client: SolutionPlansAPIClient) -> None:
    """Entreprise IA — lister les entreprises IA spécialisées candidates."""
    st.header("2. Entreprises IA spécialisées candidates")
    try:
        companies = client.list_specialized_companies()
    except APIError as exc:
        st.error(f"Impossible de récupérer les entreprises IA : {exc}")
        return

    if not companies:
        st.info("Aucune entreprise IA pour l'instant. Composez-en une depuis une source approuvée.")
        return

    for company in companies:
        st.markdown(
            f"**#{company.get('id')}** · {status_badge(company.get('status', ''))} · "
            f"source `{company.get('source_type')}` #{company.get('source_id')}\n\n"
            f"**{company.get('ai_company_name') or company.get('source_title', '')}**"
        )
    ids = [int(company["id"]) for company in companies]
    current = st.session_state.get("selected_company_id")
    default_index = ids.index(current) if current in ids else 0
    selected = st.selectbox("Sélectionner une entreprise IA à détailler", ids, index=default_index)
    st.session_state["selected_company_id"] = selected


def _render_expert_cells(raw_cells: str) -> None:
    """Affiche les cellules d'experts (JSON) : ≥ 10 experts par spécialité."""
    try:
        cells = json.loads(raw_cells) if raw_cells else []
    except (json.JSONDecodeError, ValueError):
        st.write("_(cellules non lisibles)_")
        return
    if not cells:
        st.write("_(aucune cellule)_")
        return
    for cell in cells:
        experts = cell.get("experts", [])
        st.markdown(
            f"**{cell.get('department', '')} → {cell.get('specialty', '')}** "
            f"— {len(experts)} experts"
        )
        for expert in experts:
            st.markdown(
                f"- **{expert.get('name', '')}** · rôle de débat : {expert.get('debate_role', '')} "
                f"· angle : {expert.get('angle_of_analysis', '')} · objections : "
                f"{expert.get('expected_objections', '')}"
            )


def render_company_detail(client: SolutionPlansAPIClient) -> None:
    """Entreprise IA — détail complet de l'entreprise sélectionnée."""
    st.header("3. Détail de l'entreprise IA sélectionnée")
    company_id = st.session_state.get("selected_company_id")
    if company_id is None:
        st.info("Sélectionnez une entreprise IA dans la liste.")
        return
    try:
        company = client.get_specialized_company(int(company_id))
    except APIError as exc:
        st.error(f"Impossible de récupérer l'entreprise IA : {exc}")
        return

    st.subheader(f"#{company.get('id')} — {company.get('ai_company_name', '')}")
    st.write(f"**Statut :** {status_badge(company.get('status', ''))}")
    st.write(
        f"**Source :** `{company.get('source_type')}` #{company.get('source_id')} — "
        f"{company.get('source_title', '')}"
    )
    if company.get("error"):
        st.error(f"Erreur historisée : {company['error']}")

    _section("Mission", company.get("company_mission", ""))
    _section("Objectif", company.get("company_goal", ""))
    _section("Départements", company.get("departments", ""))
    st.markdown("**Cellules d'experts (≥ 10 experts par spécialité)**")
    _render_expert_cells(company.get("expert_cells", ""))
    _section("Protocole de débat contradictoire", company.get("debate_protocol", ""))
    _section("Coordination interne", company.get("coordination_model", ""))
    _section("Workflow de production", company.get("production_workflow", ""))
    _section("Livrables concrets", company.get("concrete_deliverables", ""))
    _section("Contrat de livraison", company.get("delivery_contract", ""))
    _section("Points de validation CEO", company.get("ceo_validation_points", ""))
    _section("Notes de gouvernance", company.get("governance_notes", ""))
    _section("Risques", company.get("risks", ""))

    render_company_actions(client, company)


def render_company_actions(client: SolutionPlansAPIClient, company: dict[str, Any]) -> None:
    """Entreprise IA — actions de gouvernance CEO (approuver / demander révision)."""
    st.header("4. Validation CEO")
    st.caption(COMPANY_CANDIDATE_NOTICE)
    company_id = int(company["id"])
    col_approve, col_revision = st.columns(2)
    with col_approve:
        if st.button("✅ Approuver cette entreprise IA"):
            _act(
                lambda: client.approve_specialized_company(company_id),
                "Entreprise IA approuvée (aucune exécution ni production déclenchée).",
            )
    with col_revision:
        if st.button("🟠 Demander une révision", key="company_revision"):
            _act(
                lambda: client.request_specialized_company_revision(company_id),
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

    tab_create, tab_improve, tab_company = st.tabs(
        [
            "Créer une solution",
            "Améliorer une solution existante",
            "Composer une entreprise IA spécialisée",
        ]
    )
    with tab_create:
        render_submit(client)
        render_plans_list(client)
        render_plan_detail(client)
    with tab_improve:
        render_improvement_submit(client)
        render_improvements_list(client)
        render_improvement_detail(client)
    with tab_company:
        render_company_compose(client)
        render_companies_list(client)
        render_company_detail(client)


if __name__ == "__main__":
    main()
