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


DELIVERABLE_CANDIDATE_NOTICE = (
    "Ce livrable est **candidat**. L'approbation ne déclenche **aucun déploiement, aucune "
    "livraison externe, aucune modification automatique du repo**."
)

DELIVERABLE_TYPES = [
    "technical_spec",
    "functional_spec",
    "architecture",
    "test_plan",
    "documentation",
    "readme",
    "launch_strategy",
    "audit_report",
    "implementation_plan",
    "system_prompt",
    "checklist",
    "prototype_text",
    "pseudo_code",
]


def render_deliverable_produce(client: SolutionPlansAPIClient) -> None:
    """Livrable — choisir une entreprise IA approuvée et produire un livrable encadré."""
    st.header("1. Choisir une entreprise IA approuvée")
    st.caption(DELIVERABLE_CANDIDATE_NOTICE)
    try:
        companies = client.list_specialized_companies()
    except APIError as exc:
        st.error(f"Impossible de récupérer les entreprises IA : {exc}")
        return

    approved = [c for c in companies if c.get("status") == "approved"]
    if not approved:
        st.info(
            "Aucune entreprise IA approuvée. Approuvez d'abord une entreprise IA "
            "(onglet précédent)."
        )
        return

    labels = {
        int(c["id"]): f"#{c['id']} — {c.get('ai_company_name') or c.get('source_title', '')}"
        for c in approved
    }
    company_id = st.selectbox(
        "Entreprise IA approuvée", list(labels.keys()), format_func=lambda i: labels[i]
    )
    chosen = next(c for c in approved if int(c["id"]) == company_id)
    if chosen.get("delivery_contract"):
        st.markdown(f"**Contrat de livraison :** {chosen['delivery_contract'][:200]}")

    st.subheader("2. Demander un livrable encadré")
    with st.form("produce_deliverable"):
        deliverable_type = st.selectbox("Type de livrable", DELIVERABLE_TYPES)
        title = st.text_input("Titre du livrable")
        instructions = st.text_area("Instructions")
        constraints = st.text_area(
            "Contraintes", value="Version limitée, pas de code complet, pas de déploiement."
        )
        submitted = st.form_submit_button("Produire le livrable candidat")

    if not submitted:
        return
    if not title.strip() or not instructions.strip():
        st.error("Le titre et les instructions sont obligatoires.")
        return
    produce_spinner = (
        "L'entreprise IA produit le livrable (Planner → Synthèse → Producer → Qualité)…"
    )
    with st.spinner(produce_spinner):
        try:
            deliverable = client.create_company_deliverable(
                int(company_id),
                deliverable_type,
                title.strip(),
                instructions.strip(),
                constraints.strip(),
            )
        except APIError as exc:
            st.error(f"Échec de la production : {exc}")
            return
    if deliverable.get("status") == "draft":
        st.warning(
            "Livrable enregistré en **brouillon** : la production a échoué "
            f"(clé API manquante ?). Erreur : {deliverable.get('error', '')}"
        )
    else:
        st.success(f"Livrable candidat #{deliverable.get('id')} produit.")
    st.session_state["selected_deliverable_company_id"] = int(company_id)
    st.session_state["selected_deliverable_id"] = deliverable.get("id")


def render_deliverables_list(client: SolutionPlansAPIClient) -> None:
    """Livrable — lister les livrables candidats de l'entreprise IA sélectionnée."""
    st.header("3. Livrables candidats")
    company_id = st.session_state.get("selected_deliverable_company_id")
    if company_id is None:
        st.info("Produisez un livrable ci-dessus pour voir la liste.")
        return
    try:
        deliverables = client.list_company_deliverables(int(company_id))
    except APIError as exc:
        st.error(f"Impossible de récupérer les livrables : {exc}")
        return

    if not deliverables:
        st.info("Aucun livrable pour cette entreprise IA.")
        return

    for item in deliverables:
        st.markdown(
            f"**#{item.get('id')}** · {status_badge(item.get('status', ''))} · "
            f"`{item.get('deliverable_type')}`\n\n**{item.get('title', '')}**"
        )
    ids = [int(item["id"]) for item in deliverables]
    current = st.session_state.get("selected_deliverable_id")
    default_index = ids.index(current) if current in ids else 0
    selected = st.selectbox("Sélectionner un livrable à détailler", ids, index=default_index)
    st.session_state["selected_deliverable_id"] = selected


def render_deliverable_detail(client: SolutionPlansAPIClient) -> None:
    """Livrable — détail complet du livrable sélectionné."""
    st.header("4. Détail du livrable sélectionné")
    deliverable_id = st.session_state.get("selected_deliverable_id")
    if deliverable_id is None:
        st.info("Sélectionnez un livrable dans la liste.")
        return
    try:
        item = client.get_deliverable(int(deliverable_id))
    except APIError as exc:
        st.error(f"Impossible de récupérer le livrable : {exc}")
        return

    st.subheader(f"#{item.get('id')} — {item.get('title', '')}")
    st.write(f"**Statut :** {status_badge(item.get('status', ''))}")
    st.write(
        f"**Type :** `{item.get('deliverable_type')}` · "
        f"**Entreprise IA :** {item.get('company_name', '')} (#{item.get('company_id')})"
    )
    if item.get("error"):
        st.error(f"Erreur historisée : {item['error']}")

    _section("Contenu du livrable", item.get("content", ""))
    _section("Notes de production", item.get("production_notes", ""))
    _section("Revue qualité", item.get("quality_review", ""))
    _section("Risques", item.get("risks", ""))
    _section("Notes de validation CEO", item.get("ceo_validation_notes", ""))

    render_deliverable_actions(client, item)


def render_deliverable_actions(client: SolutionPlansAPIClient, item: dict[str, Any]) -> None:
    """Livrable — actions de gouvernance CEO (approuver / demander révision)."""
    st.header("5. Validation CEO")
    st.caption(DELIVERABLE_CANDIDATE_NOTICE)
    deliverable_id = int(item["id"])
    col_approve, col_revision = st.columns(2)
    with col_approve:
        if st.button("✅ Approuver ce livrable"):
            _act(
                lambda: client.approve_deliverable(deliverable_id),
                "Livrable approuvé (aucun déploiement, aucune livraison, aucune modif repo).",
            )
    with col_revision:
        if st.button("🟠 Demander une révision", key="deliverable_revision"):
            _act(
                lambda: client.request_deliverable_revision(deliverable_id),
                "Révision demandée.",
            )


VERSION_CANDIDATE_NOTICE = (
    "Une version approuvée **ne déclenche aucun déploiement, aucune livraison externe, aucune "
    "modification automatique du repo**. Le livrable original n'est jamais écrasé."
)


def render_version_iterate(client: SolutionPlansAPIClient) -> None:
    """Itération — choisir un livrable et produire une nouvelle version candidate."""
    st.header("1. Choisir un livrable et demander une révision")
    st.caption(VERSION_CANDIDATE_NOTICE)
    deliverable_id_input = st.number_input(
        "ID du livrable à itérer (voir l'onglet « Produire un livrable encadré »)",
        min_value=1,
        step=1,
        value=st.session_state.get("selected_deliverable_id", 1) or 1,
    )
    deliverable_id = int(deliverable_id_input)
    try:
        current = client.get_deliverable(deliverable_id)
    except APIError as exc:
        st.warning(f"Livrable introuvable ou API injoignable : {exc}")
        return
    st.markdown(f"**Livrable #{current.get('id')} — {current.get('title', '')}** (V1)")
    _section("Contenu actuel (V1)", current.get("content", ""))

    with st.form("iterate_deliverable"):
        revision_instructions = st.text_area("Instructions de révision")
        constraints = st.text_area(
            "Contraintes", value="Ne pas ajouter de code complet. Garder une version MVP."
        )
        focus_areas = st.text_input("Focus areas", value="clarté, architecture, risques, tests")
        submitted = st.form_submit_button("Produire une nouvelle version candidate")

    if not submitted:
        return
    if not revision_instructions.strip():
        st.error("Les instructions de révision sont obligatoires.")
        return
    with st.spinner("Itération en cours (Analyst → Producer → Comparator → Qualité)…"):
        try:
            version = client.create_deliverable_version(
                deliverable_id,
                revision_instructions.strip(),
                constraints.strip(),
                focus_areas.strip(),
            )
        except APIError as exc:
            st.error(f"Échec de l'itération : {exc}")
            return
    if version.get("status") == "draft":
        st.warning(
            "Version enregistrée en **brouillon** : la génération a échoué "
            f"(clé API manquante ?). Erreur : {version.get('error', '')}"
        )
    else:
        st.success(
            f"Version V{version.get('version_number')} candidate produite (#{version.get('id')})."
        )
    st.session_state["iterate_deliverable_id"] = deliverable_id
    st.session_state["selected_version_id"] = version.get("id")


def render_versions_list(client: SolutionPlansAPIClient) -> None:
    """Itération — historique des versions + comparaison."""
    st.header("2. Versions et comparaison")
    deliverable_id = st.session_state.get("iterate_deliverable_id")
    if deliverable_id is None:
        st.info("Produisez une version ci-dessus pour voir l'historique.")
        return
    try:
        comparison = client.compare_deliverable_versions(int(deliverable_id))
        versions = client.list_deliverable_versions(int(deliverable_id))
    except APIError as exc:
        st.error(f"Impossible de récupérer les versions : {exc}")
        return

    st.markdown("**Comparaison des versions (V1 = livrable original) :**")
    for row in comparison:
        st.markdown(
            f"- **V{row.get('version_number')}** · {status_badge(row.get('status', ''))}"
            f"{' — ' + row['change_summary'] if row.get('change_summary') else ''}"
        )

    if not versions:
        st.info("Aucune nouvelle version (le livrable original reste la V1).")
        return
    ids = [int(v["id"]) for v in versions]
    current = st.session_state.get("selected_version_id")
    default_index = ids.index(current) if current in ids else 0
    selected = st.selectbox(
        "Sélectionner une version à détailler",
        ids,
        index=default_index,
        format_func=lambda i: _version_label(versions, i),
    )
    st.session_state["selected_version_id"] = selected


def _version_label(versions: list[dict[str, Any]], version_id: int) -> str:
    """Libellé lisible d'une version (#id — Vn)."""
    number = next(v["version_number"] for v in versions if v["id"] == version_id)
    return f"#{version_id} — V{number}"


def render_version_detail(client: SolutionPlansAPIClient) -> None:
    """Itération — détail complet de la version sélectionnée."""
    st.header("3. Détail de la version sélectionnée")
    version_id = st.session_state.get("selected_version_id")
    if version_id is None:
        st.info("Sélectionnez une version dans la liste.")
        return
    try:
        version = client.get_deliverable_version(int(version_id))
    except APIError as exc:
        st.error(f"Impossible de récupérer la version : {exc}")
        return

    st.subheader(f"Version V{version.get('version_number')} — #{version.get('id')}")
    st.write(f"**Statut :** {status_badge(version.get('status', ''))}")
    st.write(
        f"**Livrable :** #{version.get('deliverable_id')} · "
        f"**Source :** V{version.get('source_version_id') or 1}"
    )
    if version.get("error"):
        st.error(f"Erreur historisée : {version['error']}")

    _section("Contenu de la version", version.get("content", ""))
    _section("Résumé des changements", version.get("change_summary", ""))
    _section("Comparaison à la version précédente", version.get("comparison_to_previous", ""))
    _section("Revue qualité", version.get("quality_review", ""))
    _section("Risques", version.get("risks", ""))
    _section("Notes de validation CEO", version.get("ceo_validation_notes", ""))

    render_version_actions(client, version)


def render_version_actions(client: SolutionPlansAPIClient, version: dict[str, Any]) -> None:
    """Itération — actions de gouvernance CEO (approuver / demander révision)."""
    st.header("4. Validation CEO")
    st.caption(VERSION_CANDIDATE_NOTICE)
    version_id = int(version["id"])
    col_approve, col_revision = st.columns(2)
    with col_approve:
        if st.button("✅ Approuver cette version"):
            _act(
                lambda: client.approve_deliverable_version(version_id),
                "Version approuvée (aucun déploiement, aucune livraison, aucune modif repo).",
            )
    with col_revision:
        if st.button("🟠 Demander une révision", key="version_revision"):
            _act(
                lambda: client.request_deliverable_version_revision(version_id),
                "Révision demandée.",
            )


REFERENCE_NOTICE = (
    "La référence officielle est une **décision CEO**. Elle ne déclenche aucun déploiement, "
    "aucune livraison externe, aucune modification automatique du repo."
)


def render_reference_consolidate(client: SolutionPlansAPIClient) -> None:
    """Référence — choisir une version approuvée d'un livrable et la consolider en référence."""
    st.header("1. Choisir un livrable et une version approuvée")
    st.caption(REFERENCE_NOTICE)
    deliverable_id_input = st.number_input(
        "ID du livrable",
        min_value=1,
        step=1,
        value=st.session_state.get("selected_deliverable_id", 1) or 1,
        key="reference_deliverable_id",
    )
    deliverable_id = int(deliverable_id_input)
    try:
        versions = client.list_deliverable_versions(deliverable_id)
    except APIError as exc:
        st.warning(f"Impossible de récupérer les versions : {exc}")
        return

    approved = [v for v in versions if v.get("status") == "approved"]
    if not approved:
        st.info(
            "Aucune version **approuvée** pour ce livrable. Approuvez d'abord une version "
            "(onglet « Itérer sur un livrable »)."
        )
        return

    labels = {int(v["id"]): f"#{v['id']} — V{v.get('version_number')}" for v in approved}
    version_id = st.selectbox(
        "Version approuvée", list(labels.keys()), format_func=lambda i: labels[i]
    )
    reason = st.text_input("Raison de la consolidation")
    if st.button("📌 Définir comme version de référence"):
        try:
            reference = client.set_deliverable_reference(int(version_id), reason.strip())
        except APIError as exc:
            st.error(f"Consolidation impossible : {exc}")
            return
        st.success(
            f"Version V{reference.get('reference_version_number')} définie comme référence active."
        )
        st.session_state["reference_deliverable_id_active"] = deliverable_id


def render_reference_active(client: SolutionPlansAPIClient) -> None:
    """Référence — afficher la référence active du livrable."""
    st.header("2. Référence active")
    deliverable_id = st.session_state.get("reference_deliverable_id_active") or int(
        st.session_state.get("reference_deliverable_id", 0) or 0
    )
    if not deliverable_id:
        st.info("Consolidez une référence ci-dessus pour l'afficher.")
        return
    try:
        reference = client.get_deliverable_reference(int(deliverable_id))
    except APIError as exc:
        st.info(f"Aucune référence active pour ce livrable ({exc}).")
        return

    st.subheader(
        f"Référence active — V{reference.get('reference_version_number')} "
        f"(version #{reference.get('reference_version_id')})"
    )
    st.write(
        f"**Défini par :** {reference.get('set_by')} · **Statut :** "
        f"{status_badge(reference.get('status', ''))}"
    )
    _section("Raison", reference.get("reason", ""))
    _section("Contenu (snapshot figé)", reference.get("content_snapshot", ""))
    _section("Résumé des changements (snapshot)", reference.get("change_summary_snapshot", ""))


def render_reference_history(client: SolutionPlansAPIClient) -> None:
    """Référence — historique des changements de référence."""
    st.header("3. Historique des références")
    deliverable_id = st.session_state.get("reference_deliverable_id_active") or int(
        st.session_state.get("reference_deliverable_id", 0) or 0
    )
    if not deliverable_id:
        st.info("Consolidez une référence pour voir l'historique.")
        return
    try:
        history = client.list_deliverable_reference_history(int(deliverable_id))
    except APIError as exc:
        st.error(f"Impossible de récupérer l'historique : {exc}")
        return
    if not history:
        st.info("Aucune référence consolidée pour ce livrable.")
        return
    for row in history:
        st.markdown(
            f"- **V{row.get('reference_version_number')}** · "
            f"{status_badge(row.get('status', ''))} · {row.get('created_at', '')}"
            f"{' — ' + row['reason'] if row.get('reason') else ''}"
        )


EXPLOITATION_NOTICE = (
    "AI-SOS utilise **uniquement la référence officielle active** choisie par le CEO. Cette "
    "action **ne change pas la référence**, ne déploie rien, ne livre rien et ne modifie pas "
    "le repo. La sortie reste **candidate** jusqu'à validation CEO."
)

EXPLOITATION_NEXT_STEP_TYPES = [
    "implementation_plan",
    "technical_spec",
    "test_plan",
    "production_checklist",
    "mvp_backlog",
    "api_spec",
    "user_validation_plan",
    "derived_documentation",
    "delivery_strategy",
    "system_prompt",
]


def render_exploitation_create(client: SolutionPlansAPIClient) -> None:
    """Exploitation — choisir un livrable, afficher sa référence active et produire une suite."""
    st.header("1. Exploiter la référence officielle d'un livrable")
    st.caption(EXPLOITATION_NOTICE)
    deliverable_id_input = st.number_input(
        "ID du livrable",
        min_value=1,
        step=1,
        value=st.session_state.get("exploitation_deliverable_id", 1) or 1,
        key="exploitation_deliverable_id",
    )
    deliverable_id = int(deliverable_id_input)

    try:
        reference = client.get_deliverable_reference(deliverable_id)
    except APIError:
        st.info(
            "Aucune référence active pour ce livrable. Consolidez d'abord une version approuvée "
            "(onglet « Consolider une référence »)."
        )
        return

    st.subheader(
        f"Référence active — V{reference.get('reference_version_number')} "
        f"(reference_id #{reference.get('id')}, version #{reference.get('reference_version_id')})"
    )
    _section("Contenu de référence (snapshot)", reference.get("content_snapshot", ""))
    _section("Résumé des changements (snapshot)", reference.get("change_summary_snapshot", ""))

    with st.form("submit_exploitation"):
        next_step_type = st.selectbox("Type de prochaine étape", EXPLOITATION_NEXT_STEP_TYPES)
        title = st.text_input("Titre de la prochaine étape")
        instructions = st.text_area("Instructions")
        constraints = st.text_area("Contraintes", value="Ne pas modifier le repo. Ne pas déployer.")
        acceptance_focus = st.text_input("Critères d'acceptation à privilégier")
        submitted = st.form_submit_button("Produire une exploitation candidate depuis la référence")

    if not submitted:
        return
    if not title.strip() or not instructions.strip():
        st.error("Le titre et les instructions sont obligatoires.")
        return
    with st.spinner("AI-SOS exploite la référence (Analyst → Planner → Producer → Reviewer)…"):
        try:
            exploitation = client.create_reference_exploitation(
                deliverable_id,
                next_step_type,
                title.strip(),
                instructions.strip(),
                constraints.strip(),
                acceptance_focus.strip(),
            )
        except APIError as exc:
            st.error(f"Exploitation impossible : {exc}")
            return
    if exploitation.get("status") == "draft":
        st.warning(
            "Exploitation enregistrée en **brouillon** : la génération LLM a échoué "
            f"(clé API manquante ?). Erreur : {exploitation.get('error', '')}"
        )
    else:
        st.success(f"Exploitation candidate #{exploitation.get('id')} créée depuis la référence.")
    st.session_state["exploitation_deliverable_id_active"] = deliverable_id
    st.session_state["selected_exploitation_id"] = exploitation.get("id")


def render_exploitations_list(client: SolutionPlansAPIClient) -> None:
    """Exploitation — lister les exploitations du livrable et en sélectionner une."""
    st.header("2. Exploitations du livrable")
    deliverable_id = st.session_state.get("exploitation_deliverable_id_active") or int(
        st.session_state.get("exploitation_deliverable_id", 0) or 0
    )
    if not deliverable_id:
        st.info("Produisez une exploitation ci-dessus pour la retrouver ici.")
        return
    try:
        exploitations = client.list_reference_exploitations(int(deliverable_id))
    except APIError as exc:
        st.error(f"Impossible de récupérer les exploitations : {exc}")
        return
    if not exploitations:
        st.info("Aucune exploitation pour ce livrable.")
        return
    for item in exploitations:
        st.markdown(
            f"- **#{item.get('id')}** · `{item.get('next_step_type')}` · "
            f"{status_badge(item.get('status', ''))} · V{item.get('reference_version_number')} "
            f"· {item.get('title', '')}"
        )
    ids = [int(item["id"]) for item in exploitations]
    current = st.session_state.get("selected_exploitation_id")
    default_index = ids.index(current) if current in ids else 0
    selected = st.selectbox("Sélectionner une exploitation à détailler", ids, index=default_index)
    st.session_state["selected_exploitation_id"] = selected


def render_exploitation_detail(client: SolutionPlansAPIClient) -> None:
    """Exploitation — détail complet + provenance + actions CEO."""
    st.header("3. Détail de l'exploitation sélectionnée")
    exploitation_id = st.session_state.get("selected_exploitation_id")
    if exploitation_id is None:
        st.info("Sélectionnez une exploitation dans la liste.")
        return
    try:
        item = client.get_reference_exploitation(int(exploitation_id))
    except APIError as exc:
        st.error(f"Impossible de récupérer l'exploitation : {exc}")
        return

    st.subheader(f"#{item.get('id')} — {item.get('title', '')}")
    st.write(f"**Statut :** {status_badge(item.get('status', ''))}")
    st.write(
        f"**Provenance :** référence #{item.get('reference_id')} · "
        f"version #{item.get('reference_version_id')} · "
        f"V{item.get('reference_version_number')} · type `{item.get('next_step_type')}`"
    )
    if item.get("error"):
        st.error(f"Erreur historisée : {item['error']}")

    _section("Plan d'exploitation", item.get("exploitation_plan", ""))
    _section("Candidat de sortie", item.get("candidate_output", ""))
    _section("Revue qualité", item.get("quality_review", ""))
    _section("Risques", item.get("risks", ""))
    _section("Notes de validation CEO", item.get("ceo_validation_notes", ""))
    _section("Notes de provenance", item.get("provenance_notes", ""))
    _section("Contenu de référence utilisé (snapshot)", item.get("reference_content_snapshot", ""))

    render_exploitation_actions(client, item)


def render_exploitation_actions(client: SolutionPlansAPIClient, item: dict[str, Any]) -> None:
    """Exploitation — actions de gouvernance CEO (approuver / demander révision)."""
    st.markdown("**Validation CEO**")
    st.caption(EXPLOITATION_NOTICE)
    exploitation_id = int(item["id"])
    col_approve, col_revision = st.columns(2)
    with col_approve:
        if st.button("✅ Approuver cette exploitation"):
            _act(
                lambda: client.approve_reference_exploitation(exploitation_id),
                "Exploitation approuvée (aucune exécution déclenchée).",
            )
    with col_revision:
        if st.button("🟠 Demander une révision", key="exploitation_revision"):
            _act(
                lambda: client.request_reference_exploitation_revision(exploitation_id),
                "Révision demandée.",
            )


COORDINATED_NOTICE = (
    "Ces livrables sont **candidats et coordonnés**. Ils ne déclenchent aucun déploiement, aucune "
    "livraison externe et aucune modification automatique du repo. **Le CEO valide le lot.**"
)

COORDINATED_DELIVERABLE_TYPES = [
    "mvp_backlog",
    "technical_implementation_plan",
    "test_plan",
    "api_spec",
    "api_test_plan",
    "validation_checklist",
    "technical_spec",
    "text_architecture",
    "technical_risks",
    "user_documentation",
    "operator_guide",
    "delivery_checklist",
    "system_prompt",
    "evaluation_plan",
    "product_plan",
    "short_roadmap",
]


def render_coordinated_create(client: SolutionPlansAPIClient) -> None:
    """Coordonnés — choisir une exploitation approuvée et produire un lot cohérent."""
    st.header("1. Coordonner un lot depuis une exploitation approuvée")
    st.caption(COORDINATED_NOTICE)
    exploitation_id_input = st.number_input(
        "ID de l'exploitation",
        min_value=1,
        step=1,
        value=st.session_state.get("selected_exploitation_id", 1) or 1,
        key="coordinated_exploitation_id",
    )
    exploitation_id = int(exploitation_id_input)

    try:
        exploitation = client.get_reference_exploitation(exploitation_id)
    except APIError as exc:
        st.warning(f"Impossible de récupérer l'exploitation : {exc}")
        return

    st.write(f"**Statut de l'exploitation :** {status_badge(exploitation.get('status', ''))}")
    st.write(
        f"**Provenance :** livrable #{exploitation.get('deliverable_id')} · "
        f"référence #{exploitation.get('reference_id')} · "
        f"version #{exploitation.get('reference_version_id')} · "
        f"V{exploitation.get('reference_version_number')}"
    )
    if exploitation.get("status") != "approved":
        st.info(
            "L'exploitation doit être **approuvée** avant de coordonner un lot. Approuvez-la "
            "d'abord (onglet « Exploiter une référence »)."
        )
        return

    with st.form("submit_coordinated"):
        title = st.text_input("Titre du lot")
        objective = st.text_area("Objectif du lot")
        requested = st.multiselect("Livrables demandés (2 à 5)", COORDINATED_DELIVERABLE_TYPES)
        coordination_instructions = st.text_area(
            "Instructions de coordination",
            value="Les livrables doivent être cohérents entre eux et éviter les contradictions.",
        )
        constraints = st.text_area(
            "Contraintes",
            value="Ne pas écrire le code complet. Ne pas modifier le repo. Ne pas déployer.",
        )
        acceptance_focus = st.text_input("Critères d'acceptation à privilégier")
        submitted = st.form_submit_button("Produire un lot de livrables coordonnés")

    if not submitted:
        return
    if not title.strip() or not objective.strip():
        st.error("Le titre et l'objectif sont obligatoires.")
        return
    if not 2 <= len(requested) <= 5:
        st.error("Sélectionnez entre 2 et 5 livrables.")
        return
    with st.spinner("AI-SOS coordonne le lot (Reader → Planner → Producer → Cohérence → Qualité)…"):
        try:
            batch = client.create_coordinated_deliverable_batch(
                exploitation_id,
                title.strip(),
                objective.strip(),
                requested,
                coordination_instructions.strip(),
                constraints.strip(),
                acceptance_focus.strip(),
            )
        except APIError as exc:
            st.error(f"Coordination impossible : {exc}")
            return
    if batch.get("status") == "draft":
        st.warning(
            "Lot enregistré en **brouillon** : la génération LLM a échoué "
            f"(clé API manquante ?). Erreur : {batch.get('error', '')}"
        )
    else:
        st.success(f"Lot coordonné #{batch.get('id')} créé depuis l'exploitation.")
    st.session_state["coordinated_exploitation_id_active"] = exploitation_id
    st.session_state["selected_batch_id"] = batch.get("id")


def render_coordinated_list(client: SolutionPlansAPIClient) -> None:
    """Coordonnés — lister les lots d'une exploitation et en sélectionner un."""
    st.header("2. Lots coordonnés de l'exploitation")
    exploitation_id = st.session_state.get("coordinated_exploitation_id_active") or int(
        st.session_state.get("coordinated_exploitation_id", 0) or 0
    )
    if not exploitation_id:
        st.info("Produisez un lot ci-dessus pour le retrouver ici.")
        return
    try:
        batches = client.list_coordinated_deliverable_batches(int(exploitation_id))
    except APIError as exc:
        st.error(f"Impossible de récupérer les lots : {exc}")
        return
    if not batches:
        st.info("Aucun lot pour cette exploitation.")
        return
    for batch in batches:
        st.markdown(
            f"- **#{batch.get('id')}** · {status_badge(batch.get('status', ''))} · "
            f"{batch.get('title', '')}"
        )
    ids = [int(batch["id"]) for batch in batches]
    current = st.session_state.get("selected_batch_id")
    default_index = ids.index(current) if current in ids else 0
    selected = st.selectbox("Sélectionner un lot à détailler", ids, index=default_index)
    st.session_state["selected_batch_id"] = selected


def render_coordinated_detail(client: SolutionPlansAPIClient) -> None:
    """Coordonnés — détail du lot, items et actions CEO."""
    st.header("3. Détail du lot sélectionné")
    batch_id = st.session_state.get("selected_batch_id")
    if batch_id is None:
        st.info("Sélectionnez un lot dans la liste.")
        return
    try:
        batch = client.get_coordinated_deliverable_batch(int(batch_id))
        items = client.list_coordinated_deliverable_items(int(batch_id))
    except APIError as exc:
        st.error(f"Impossible de récupérer le lot : {exc}")
        return

    st.subheader(f"#{batch.get('id')} — {batch.get('title', '')}")
    st.write(f"**Statut :** {status_badge(batch.get('status', ''))}")
    st.write(
        f"**Provenance :** exploitation #{batch.get('exploitation_id')} · "
        f"livrable #{batch.get('deliverable_id')} · référence #{batch.get('reference_id')} · "
        f"V{batch.get('reference_version_number')}"
    )
    if batch.get("error"):
        st.error(f"Erreur historisée : {batch['error']}")

    _section("Plan de coordination", batch.get("coordination_plan", ""))
    _section("Revue de cohérence inter-livrables", batch.get("coherence_review", ""))
    _section("Risques", batch.get("risks", ""))
    _section("Notes de validation CEO", batch.get("ceo_validation_notes", ""))
    _section("Notes de provenance", batch.get("provenance_notes", ""))

    st.markdown(f"**Items du lot ({len(items)})**")
    for item in items:
        with st.expander(
            f"[{item.get('order_index')}] {item.get('item_type')} — {item.get('title', '')}"
        ):
            _section("Contenu", item.get("content", ""))
            _section("Dépendances", item.get("dependencies", ""))
            _section("Notes de cohérence", item.get("consistency_notes", ""))
            _section("Notes de validation", item.get("validation_notes", ""))

    render_coordinated_actions(client, batch)


def render_coordinated_actions(client: SolutionPlansAPIClient, batch: dict[str, Any]) -> None:
    """Coordonnés — actions de gouvernance CEO (approuver / demander révision du lot)."""
    st.markdown("**Validation CEO du lot**")
    st.caption(COORDINATED_NOTICE)
    batch_id = int(batch["id"])
    col_approve, col_revision = st.columns(2)
    with col_approve:
        if st.button("✅ Approuver le lot"):
            _act(
                lambda: client.approve_coordinated_deliverable_batch(batch_id),
                "Lot approuvé (aucune exécution déclenchée).",
            )
    with col_revision:
        if st.button("🟠 Demander une révision du lot", key="coordinated_revision"):
            _act(
                lambda: client.request_coordinated_deliverable_batch_revision(batch_id),
                "Révision du lot demandée.",
            )


ITEM_VALIDATION_NOTICE = (
    "La validation item par item **ne valide pas automatiquement le lot**. Elle ne déclenche "
    "aucune régénération, aucun déploiement, aucune livraison externe et aucune modification "
    "automatique du repo."
)


def render_coordinated_item_validation(client: SolutionPlansAPIClient) -> None:
    """Coordonnés — validation CEO item par item (Phase 11) + résumé + historique des décisions."""
    st.header("4. Validation item par item")
    st.caption(ITEM_VALIDATION_NOTICE)
    batch_id = st.session_state.get("selected_batch_id")
    if batch_id is None:
        st.info("Sélectionnez un lot ci-dessus pour valider ses items.")
        return
    try:
        summary = client.get_coordinated_batch_item_validation_summary(int(batch_id))
        items = client.list_coordinated_deliverable_items(int(batch_id))
    except APIError as exc:
        st.error(f"Impossible de récupérer la validation : {exc}")
        return

    st.write(
        f"**Statut du lot :** {status_badge(summary.get('batch_status', ''))} "
        "(inchangé par la validation item par item)"
    )
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total", summary.get("total_items", 0))
    col2.metric("Approuvés", summary.get("approved_items", 0))
    col3.metric("Refusés", summary.get("rejected_items", 0))
    col4.metric("Révision", summary.get("revision_requested_items", 0))
    col5.metric("Candidats", summary.get("candidate_items", 0))
    if summary.get("all_items_approved"):
        st.info("Tous les items sont approuvés — le lot **reste inchangé** (décision CEO séparée).")

    for item in items:
        item_id = int(item["id"])
        with st.expander(
            f"[{item.get('order_index')}] {item.get('item_type')} — "
            f"{item.get('title', '')} · {status_badge(item.get('status', ''))}"
        ):
            _section("Contenu", item.get("content", ""))
            _section("Dépendances", item.get("dependencies", ""))
            _section("Notes de cohérence", item.get("consistency_notes", ""))
            _section("Notes de validation", item.get("validation_notes", ""))

            reason = st.text_input("Raison", key=f"item_reason_{item_id}")
            ceo_notes = st.text_input("Notes CEO", key=f"item_notes_{item_id}")
            col_a, col_r, col_v = st.columns(3)
            with col_a:
                if st.button("✅ Approuver", key=f"item_approve_{item_id}"):
                    _act(
                        lambda i=item_id, r=reason, n=ceo_notes: (
                            client.approve_coordinated_deliverable_item(i, r, n)
                        ),
                        "Item approuvé (lot inchangé).",
                    )
            with col_r:
                if st.button("⛔ Refuser", key=f"item_reject_{item_id}"):
                    _act(
                        lambda i=item_id, r=reason, n=ceo_notes: (
                            client.reject_coordinated_deliverable_item(i, r, n)
                        ),
                        "Item refusé (lot inchangé).",
                    )
            with col_v:
                if st.button("🟠 Révision", key=f"item_revision_{item_id}"):
                    _act(
                        lambda i=item_id, r=reason, n=ceo_notes: (
                            client.request_coordinated_deliverable_item_revision(i, r, n)
                        ),
                        "Révision d'item demandée (aucune régénération).",
                    )

            try:
                decisions = client.list_coordinated_deliverable_item_decisions(item_id)
            except APIError as exc:
                st.warning(f"Historique indisponible : {exc}")
                decisions = []
            if decisions:
                st.markdown("**Historique des décisions (récent d'abord)**")
                for decision in decisions:
                    st.markdown(
                        f"- {status_badge(decision.get('new_status', ''))} "
                        f"(← {decision.get('previous_status', '')}) · "
                        f"{decision.get('decided_by', '')} · {decision.get('created_at', '')}"
                        f"{' — ' + decision['reason'] if decision.get('reason') else ''}"
                    )


REGENERATION_NOTICE = (
    "Cette régénération **ne remplace pas l'item original**. Elle ne modifie pas le lot, ne touche "
    "pas aux autres items, ne déploie rien, ne livre rien et ne modifie pas le repo."
)


def render_coordinated_item_regeneration(client: SolutionPlansAPIClient) -> None:
    """Coordonnés — régénération guidée d'un item `revision_requested` (Phase 12)."""
    st.header("5. Régénération guidée d'un item")
    st.caption(REGENERATION_NOTICE)
    batch_id = st.session_state.get("selected_batch_id")
    if batch_id is None:
        st.info("Sélectionnez un lot ci-dessus pour régénérer un item en révision.")
        return
    try:
        items = client.list_coordinated_deliverable_items(int(batch_id))
    except APIError as exc:
        st.error(f"Impossible de récupérer les items : {exc}")
        return
    in_revision = [it for it in items if it.get("status") == "revision_requested"]
    if not in_revision:
        st.info(
            "Aucun item au statut `revision_requested`. Demandez une révision d'item "
            "(section « Validation item par item ») pour en régénérer un."
        )
        return

    labels = {
        int(it["id"]): f"#{it['id']} — {it.get('item_type')} ({it.get('title')})"
        for it in in_revision
    }
    item_id = st.selectbox(
        "Item en révision à régénérer", list(labels.keys()), format_func=lambda i: labels[i]
    )
    selected = next(it for it in in_revision if int(it["id"]) == int(item_id))
    _section("Contenu original", selected.get("content", ""))
    _section("Dépendances", selected.get("dependencies", ""))
    _section("Notes de cohérence", selected.get("consistency_notes", ""))
    _section("Notes de validation", selected.get("validation_notes", ""))

    try:
        history = client.list_coordinated_deliverable_item_decisions(int(item_id))
    except APIError:
        history = []
    if history:
        st.markdown("**Historique des décisions**")
        for decision in history:
            st.markdown(
                f"- {status_badge(decision.get('new_status', ''))} · "
                f"{decision.get('created_at', '')}"
                f"{' — ' + decision['reason'] if decision.get('reason') else ''}"
            )

    with st.form(f"regenerate_item_{item_id}"):
        revision_instructions = st.text_area("Instructions de révision")
        constraints = st.text_area(
            "Contraintes",
            value="Ne pas changer le périmètre MVP. Ne pas modifier le repo. Ne pas déployer.",
        )
        acceptance_focus = st.text_input("Critères d'acceptation à privilégier")
        submitted = st.form_submit_button("Régénérer uniquement cet item")

    if submitted:
        if not revision_instructions.strip():
            st.error("Les instructions de révision sont obligatoires.")
        else:
            with st.spinner("AI-SOS régénère l'item (Analyst → Planner → Producer → Quality)…"):
                try:
                    regeneration = client.create_coordinated_item_regeneration(
                        int(item_id),
                        revision_instructions.strip(),
                        constraints.strip(),
                        acceptance_focus.strip(),
                    )
                except APIError as exc:
                    st.error(f"Régénération impossible : {exc}")
                    regeneration = None
            if regeneration is not None:
                if regeneration.get("status") == "draft":
                    st.warning(
                        "Régénération en **brouillon** : génération LLM en échec "
                        f"(clé API ?). Erreur : {regeneration.get('error', '')}"
                    )
                else:
                    st.success(f"Régénération candidate #{regeneration.get('id')} créée.")

    _render_regeneration_list(client, int(item_id))


def _render_regeneration_list(client: SolutionPlansAPIClient, item_id: int) -> None:
    """Affiche les régénérations d'un item + actions CEO."""
    try:
        regenerations = client.list_coordinated_item_regenerations(item_id)
    except APIError as exc:
        st.error(f"Impossible de récupérer les régénérations : {exc}")
        return
    if not regenerations:
        return
    st.markdown(f"**Régénérations de l'item ({len(regenerations)})**")
    for regen in regenerations:
        regen_id = int(regen["id"])
        with st.expander(f"Régénération #{regen_id} · {status_badge(regen.get('status', ''))}"):
            _section("Contenu régénéré", regen.get("regenerated_content", ""))
            _section("Plan de régénération", regen.get("regeneration_plan", ""))
            _section("Revue qualité", regen.get("quality_review", ""))
            _section("Risques", regen.get("risks", ""))
            _section("Notes de validation CEO", regen.get("ceo_validation_notes", ""))
            _section("Notes de provenance", regen.get("provenance_notes", ""))
            _section("Contenu original snapshoté", regen.get("source_item_content_snapshot", ""))
            col_a, col_r, col_v = st.columns(3)
            with col_a:
                if st.button("✅ Approuver", key=f"regen_approve_{regen_id}"):
                    _act(
                        lambda i=regen_id: client.approve_coordinated_item_regeneration(i),
                        "Régénération approuvée (item original inchangé).",
                    )
            with col_r:
                if st.button("⛔ Refuser", key=f"regen_reject_{regen_id}"):
                    _act(
                        lambda i=regen_id: client.reject_coordinated_item_regeneration(i),
                        "Régénération refusée.",
                    )
            with col_v:
                if st.button("🟠 Révision", key=f"regen_revision_{regen_id}"):
                    _act(
                        lambda i=regen_id: client.request_coordinated_item_regeneration_revision(i),
                        "Révision de la régénération demandée.",
                    )


def render_observability_summary(client: SolutionPlansAPIClient) -> None:
    """Observabilité — résumé (compteurs, durée moyenne, répartitions)."""
    st.header("1. Résumé")
    st.caption(
        "Lecture seule : ces vues journalisent l'exécution du runtime "
        "(appels LLM et événements produit) sans rien déclencher."
    )
    try:
        summary = client.get_observability_summary()
    except APIError as exc:
        st.error(f"Impossible de récupérer le résumé : {exc}")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Appels LLM", summary.get("total_llm_calls", 0))
    col2.metric("Succès", summary.get("successful_llm_calls", 0))
    col3.metric("Échecs", summary.get("failed_llm_calls", 0))
    col4.metric("Durée moy. (ms)", summary.get("average_duration_ms", 0))

    st.metric("Événements produit", summary.get("total_events", 0))
    calls_by_phase = summary.get("llm_calls_by_phase", {})
    events_by_phase = summary.get("events_by_phase", {})
    if calls_by_phase:
        st.write("**Appels LLM par phase :** ", calls_by_phase)
    if events_by_phase:
        st.write("**Événements par phase :** ", events_by_phase)
    latest_error = summary.get("latest_error")
    if latest_error:
        st.warning(f"Dernière erreur LLM : {latest_error}")


def render_observability_llm_calls(client: SolutionPlansAPIClient) -> None:
    """Observabilité — journal des appels LLM (récent d'abord), filtrable."""
    st.header("2. Journal des appels LLM")
    col_status, col_phase = st.columns(2)
    status = col_status.text_input(
        "Filtrer par statut (success / error)", key="obs_llm_status"
    ).strip()
    phase = col_phase.text_input("Filtrer par phase (ex. phase1)", key="obs_llm_phase").strip()
    limit = int(
        st.number_input("Limite", min_value=1, max_value=500, value=50, key="obs_llm_limit")
    )
    try:
        calls = client.list_llm_call_logs(limit=limit, status=status, phase=phase)
    except APIError as exc:
        st.error(f"Impossible de récupérer le journal LLM : {exc}")
        return
    if not calls:
        st.info("Aucun appel LLM journalisé (avec ces filtres).")
        return
    for call in calls:
        marker = "✅" if call.get("status") == "success" else "❌"
        with st.expander(
            f"{marker} #{call.get('id')} · {call.get('phase')} · {call.get('agent_name')} "
            f"· {call.get('operation_type')} · {call.get('duration_ms')} ms"
        ):
            st.write(
                f"**Fournisseur :** {call.get('provider')} · **Modèle :** {call.get('model')} "
                f"· **Statut :** {status_badge(call.get('status', ''))}"
            )
            st.caption(f"Horodatage : {call.get('created_at', '')}")
            _section("Prompt (aperçu tronqué)", call.get("prompt_preview", ""))
            _section("Réponse (aperçu tronqué)", call.get("response_preview", ""))
            if call.get("error"):
                _section("Erreur", call.get("error", ""))


def render_observability_events(client: SolutionPlansAPIClient) -> None:
    """Observabilité — journal des événements produit (récent d'abord), filtrable."""
    st.header("3. Journal des événements produit")
    col_phase, col_entity = st.columns(2)
    phase = col_phase.text_input("Filtrer par phase", key="obs_evt_phase").strip()
    entity_type = col_entity.text_input(
        "Filtrer par type d'entité (ex. solution_plan)", key="obs_evt_entity"
    ).strip()
    limit = int(
        st.number_input("Limite", min_value=1, max_value=500, value=50, key="obs_evt_limit")
    )
    try:
        events = client.list_product_event_logs(limit=limit, phase=phase, entity_type=entity_type)
    except APIError as exc:
        st.error(f"Impossible de récupérer les événements : {exc}")
        return
    if not events:
        st.info("Aucun événement produit journalisé (avec ces filtres).")
        return
    for event in events:
        st.markdown(
            f"- **{event.get('event_type')}** · {event.get('phase')} · "
            f"{event.get('entity_type')} #{event.get('entity_id')} · "
            f"{status_badge(event.get('status', ''))} · {event.get('created_at', '')}"
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

    (
        tab_create,
        tab_improve,
        tab_company,
        tab_deliverable,
        tab_version,
        tab_reference,
        tab_exploitation,
        tab_coordinated,
        tab_observability,
    ) = st.tabs(
        [
            "Créer une solution",
            "Améliorer une solution existante",
            "Composer une entreprise IA spécialisée",
            "Produire un livrable encadré",
            "Itérer sur un livrable",
            "Consolider une référence",
            "Exploiter une référence",
            "Livrables coordonnés",
            "Observabilité",
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
    with tab_deliverable:
        render_deliverable_produce(client)
        render_deliverables_list(client)
        render_deliverable_detail(client)
    with tab_version:
        render_version_iterate(client)
        render_versions_list(client)
        render_version_detail(client)
    with tab_reference:
        render_reference_consolidate(client)
        render_reference_active(client)
        render_reference_history(client)
    with tab_exploitation:
        render_exploitation_create(client)
        render_exploitations_list(client)
        render_exploitation_detail(client)
    with tab_coordinated:
        render_coordinated_create(client)
        render_coordinated_list(client)
        render_coordinated_detail(client)
        render_coordinated_item_validation(client)
        render_coordinated_item_regeneration(client)
    with tab_observability:
        render_observability_summary(client)
        render_observability_llm_calls(client)
        render_observability_events(client)


if __name__ == "__main__":
    main()
