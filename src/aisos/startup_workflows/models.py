"""Modèles déclaratifs de workflows Startup OS (C0.9 — Startup OS Minimal Workflows réaligné).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.9),
docs/strategy/AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md,
docs/workflows/C0-9-startup-os-minimal-workflows.md, docs/behavior/03-orchestrator-workflow.md.

Mission produit : AI-SOS est **d'abord une fabrique de solutions**. C0.9 se limite a **orchestrer
minimalement** : modeliser un **squelette controle** de workflow Startup OS (probleme/idee/objectif
→
**plan de solution candidat**, ou solution existante → **plan d'amelioration candidat**) — **sans**
produire de solution finale, creer d'equipe IA, decider, appliquer, deployer, executer d'etape,
appeler un LLM, ecrire l'audit ou la memoire, persister, ni ouvrir E9.

Formule centrale : *orchestrer minimalement != executer ; un workflow C0.9 **decrit** un chemin
candidat « entree → etapes → resultat candidat » qui **exige la validation du CEO** avant toute
action.* Tout est **immuable, declaratif et deterministe** : un workflow est une **donnee** scellee
par une empreinte, jamais un moteur. Le resultat est **candidat, non final** ; le **CEO reste seul
decideur metier**.

Frontieres (orchestrer minimalement n'est ni executer, ni decider, ni produire) :
  * **kinds « plan »** : `StartupWorkflowKind` nomme des **plans candidats**
    (PROBLEM/IDEA/OBJECTIVE_TO_SOLUTION_PLAN, EXISTING_SOLUTION_IMPROVEMENT_PLAN) — jamais
    CREATE/BUILD/DEPLOY_SOLUTION, CREATE_TEAM, RUN_AGENTS ni LIVE_EXECUTION ;
  * **statut declaratif** : `CEO_VALIDATED` **n'applique rien**, ne cree ni solution ni equipe IA,
    ne declenche E7 ni n'ouvre E9 ;
  * **etapes declaratives** : un `StartupWorkflowStep` **decrit** une etape ; il n'est **pas**
    execute par un agent (aucune methode execute/run/apply) ;
  * **resultat candidat** : `StartupWorkflowCandidateResult` porte un `non_final_notice` obligatoire
    et `requires_ceo_validation=True` ; ce n'est jamais une solution operationnelle ;
  * **references declaratives** : `StartupWorkflowReference` **pointe** (par chaine) vers un
  contexte
    memoire/audit/decision CEO/readiness LLM/record/trace/recommandation — sans l'importer ni le
    resoudre ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme workflow ; `content_hash`
    scelle le workflow.

C0.9 ne rouvre aucun contrat E1..E8, ne modifie ni C0.1..C0.8, n'importe aucun module actif
(`llm_readiness`, `operational_memory`, `operational_audit`, `ceo_decision`, `access`, …),
n'introduit aucun LLM reel, RAG, embedding, vector store, DB, API web ni agent, et n'anticipe pas
C1.
E9 reste ferme. Le cerveau reste gele.
"""

from __future__ import annotations

import hashlib
from enum import StrEnum
from itertools import pairwise

from pydantic import field_validator, model_validator

from aisos.schemas.base import ImmutableModel


class StartupWorkflowKind(StrEnum):
    """Type **descriptif** d'un workflow Startup OS. Toujours un **plan candidat**, jamais un acte.

    `PROBLEM_TO_SOLUTION_PLAN` / `IDEA_TO_SOLUTION_PLAN` / `OBJECTIVE_TO_SOLUTION_PLAN` structurent
    un
    plan candidat vers une solution ; `EXISTING_SOLUTION_IMPROVEMENT_PLAN` structure un plan
    candidat
    d'amelioration. Ces valeurs disent **plan** : aucune ne cree, ne construit, ne deploie une
    solution, ne cree une equipe, ne lance d'agents ni n'execute quoi que ce soit.
    """

    PROBLEM_TO_SOLUTION_PLAN = "problem_to_solution_plan"
    IDEA_TO_SOLUTION_PLAN = "idea_to_solution_plan"
    OBJECTIVE_TO_SOLUTION_PLAN = "objective_to_solution_plan"
    EXISTING_SOLUTION_IMPROVEMENT_PLAN = "existing_solution_improvement_plan"


class StartupWorkflowStatus(StrEnum):
    """Statut **declaratif** d'un workflow. Jamais un declencheur d'effet.

    `DRAFT` (brouillon), `AWAITING_CEO_VALIDATION` (en attente du CEO), `CEO_VALIDATED` (le CEO a
    marque le plan comme valide — **statut declaratif uniquement** : n'applique rien, ne cree ni
    solution ni equipe IA, ne declenche E7, n'ouvre E9), `ARCHIVED` (declaratif, non destructif).
    """

    DRAFT = "draft"
    AWAITING_CEO_VALIDATION = "awaiting_ceo_validation"
    CEO_VALIDATED = "ceo_validated"
    ARCHIVED = "archived"


class StartupWorkflowStepKind(StrEnum):
    """Type **descriptif** d'une etape de workflow. Une etape **decrite**, jamais executee.

    Capture d'entree, normalisation de contexte, identification des hypotheses/risques, esquisse
    d'un
    plan candidat, esquisse des besoins d'expertise, demande de validation CEO. Ces etapes sont
    **declaratives** : aucune n'est executee par un agent et aucune ne produit d'effet.
    """

    CAPTURE_INPUT = "capture_input"
    NORMALIZE_CONTEXT = "normalize_context"
    IDENTIFY_ASSUMPTIONS = "identify_assumptions"
    IDENTIFY_RISKS = "identify_risks"
    OUTLINE_CANDIDATE_PLAN = "outline_candidate_plan"
    OUTLINE_EXPERTISE_NEEDS = "outline_expertise_needs"
    REQUEST_CEO_VALIDATION = "request_ceo_validation"


class StartupWorkflowReferenceKind(StrEnum):
    """Type **descriptif** d'une reference de workflow. Une etiquette, jamais un objet vivant.

    Pointe, de maniere declarative (par chaine), vers un contexte memoire operationnelle, un
    evenement d'audit operationnel, un enregistrement de decision CEO, une demande/reponse de
    readiness LLM, un enregistrement de persistance, une trace ou une recommandation. Ne resout,
    n'importe ni ne mute aucun objet.
    """

    OPERATIONAL_MEMORY_CONTEXT = "operational_memory_context"
    OPERATIONAL_AUDIT_EVENT = "operational_audit_event"
    CEO_DECISION_RECORD = "ceo_decision_record"
    LLM_READINESS_REQUEST = "llm_readiness_request"
    LLM_READINESS_RESPONSE = "llm_readiness_response"
    PERSISTENCE_RECORD = "persistence_record"
    TRACE = "trace"
    RECOMMENDATION = "recommendation"


class StartupWorkflowReference(ImmutableModel):
    """Reference **declarative** immuable attachee a un workflow. Une etiquette, jamais un objet.

    Champs : ``kind`` (`StartupWorkflowReferenceKind`), ``reference`` (chaine non vide — ex.
    ``"operational_memory_context://mem-1"``), ``label`` (optionnel). **Pointe** vers un contexte
    sans le resoudre, l'importer ni le muter.
    """

    kind: StartupWorkflowReferenceKind
    reference: str
    label: str = ""

    @field_validator("reference")
    @classmethod
    def _reference_not_blank(cls, value: str) -> str:
        """Une reference est explicite : la chaine de reference est non vide."""
        if not value:
            raise ValueError("la reference d'un workflow ne peut etre vide")
        return value


class StartupWorkflowInput(ImmutableModel):
    """Entree **declarative** immuable d'un workflow. Un contexte decrit, jamais un objet produit.

    Champs : ``id`` / ``organization_id`` (non vides), ``workflow_kind`` (`StartupWorkflowKind`),
    ``title`` / ``description`` / ``source_text`` (non vides), ``references`` (tuple declaratif).
    **Decrit** le probleme/idee/objectif/solution existante en entree ; ne cree **aucun** objet
    produit (`Problem` / `Idea` / `Objective` / `Solution` restent des concepts futurs).
    """

    id: str
    organization_id: str
    workflow_kind: StartupWorkflowKind
    title: str
    description: str
    source_text: str
    references: tuple[StartupWorkflowReference, ...] = ()

    @field_validator("id", "organization_id", "title", "description", "source_text")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Une entree est explicite : id, organisation, titre, description et texte non vides."""
        if not value:
            raise ValueError("id, organization_id, title, description et source_text sont requis")
        return value


class StartupWorkflowStep(ImmutableModel):
    """Etape **declarative** immuable d'un workflow. Decrite, jamais executee.

    Champs : ``id`` (non vide), ``kind`` (`StartupWorkflowStepKind`), ``title`` / ``description``
    (non vides), ``position`` (>= 1), ``requires_ceo_validation`` (defaut ``False``). N'expose
    **aucune** methode execute/run/apply/decide/approve/create_solution/create_team : c'est une
    **donnee** qui decrit une etape, jamais un acteur qui l'accomplit.
    """

    id: str
    kind: StartupWorkflowStepKind
    title: str
    description: str
    position: int
    requires_ceo_validation: bool = False

    @field_validator("id", "title", "description")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Une etape est explicite : id, titre et description non vides."""
        if not value:
            raise ValueError("id, title et description d'une etape sont requis")
        return value

    @field_validator("position")
    @classmethod
    def _position_positive(cls, value: int) -> int:
        """La position d'une etape est **1-indexee** : elle doit valoir au moins 1."""
        if value < 1:
            raise ValueError("la position d'une etape doit etre >= 1")
        return value


class StartupWorkflowCandidateResult(ImmutableModel):
    """Resultat **candidat, non final** d'un workflow. Jamais une solution operationnelle.

    Champs : ``summary`` (non vide), ``candidate_plan`` (plan candidat declaratif, non vide),
    ``expertise_needs`` (tuple d'expertises esquissees), ``risks`` (tuple de risques esquisses),
    ``requires_ceo_validation`` (defaut ``True`` — **doit rester** ``True``), ``non_final_notice``
    (**obligatoire et valide** : rappelle que le resultat est **candidat, non final, non applique**
    et **exige la validation du CEO**). Ce n'est **pas** une solution : il ne cree, n'applique, ne
    deploie rien ; il ne cree aucune equipe IA.
    """

    summary: str
    candidate_plan: str
    expertise_needs: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    requires_ceo_validation: bool = True
    non_final_notice: str

    @field_validator("summary", "candidate_plan", "non_final_notice")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Un resultat candidat est explicite : resume, plan et notice non vides."""
        if not value:
            raise ValueError("summary, candidate_plan et non_final_notice sont requis")
        return value

    @field_validator("non_final_notice")
    @classmethod
    def _notice_reasserts_non_final(cls, value: str) -> str:
        """La notice doit affirmer que le resultat est **candidat/non final** et **exige le CEO**.

        Verification **locale et deterministe** (aucun moteur semantique) : la notice doit marquer
        le
        caractere **non final** (« candidat » ou « non final »/« non applique ») **et** la
        **validation CEO**, sans affirmation dangereuse (« solution finale », « prete a executer/
        deployer », « application automatique », « approuve sans ceo »). Voir
        `_notice_asserts_non_final`.
        """
        if not _notice_asserts_non_final(value):
            raise ValueError(
                "non_final_notice doit rappeler que le resultat est candidat/non final, non "
                "applique, et qu'il exige la validation du CEO"
            )
        return value


# Delimiteurs de serialisation stables (caracteres de controle ASCII, absents d'un texte normal).
_FIELD_SEP = "\x1f"
_RECORD_SEP = "\x1e"
_GROUP_SEP = "\x1d"


def _serialize_references(references: tuple[StartupWorkflowReference, ...]) -> str:
    """Serialise les references de maniere **stable et deterministe**, dans l'ordre du tuple."""
    return _RECORD_SEP.join(
        _FIELD_SEP.join((ref.kind.value, ref.reference, ref.label)) for ref in references
    )


def _serialize_steps(steps: tuple[StartupWorkflowStep, ...]) -> str:
    """Serialise les etapes de maniere **stable et deterministe**, dans l'ordre du tuple."""
    return _RECORD_SEP.join(
        _FIELD_SEP.join(
            (
                step.id,
                step.kind.value,
                step.title,
                step.description,
                str(step.position),
                str(step.requires_ceo_validation),
            )
        )
        for step in steps
    )


def _serialize_result(result: StartupWorkflowCandidateResult) -> str:
    """Serialise le resultat candidat de maniere **stable et deterministe**."""
    return _FIELD_SEP.join(
        (
            result.summary,
            result.candidate_plan,
            _RECORD_SEP.join(result.expertise_needs),
            _RECORD_SEP.join(result.risks),
            str(result.requires_ceo_validation),
            result.non_final_notice,
        )
    )


def compute_workflow_hash(
    *,
    workflow_id: str,
    organization_id: str,
    kind: StartupWorkflowKind,
    status: StartupWorkflowStatus,
    workflow_input: StartupWorkflowInput,
    steps: tuple[StartupWorkflowStep, ...],
    candidate_result: StartupWorkflowCandidateResult,
    references: tuple[StartupWorkflowReference, ...] = (),
) -> str:
    """Calcule l'empreinte SHA-256 (hex) du contenu declaratif d'un workflow. Deterministe.

    Scelle l'identite (`workflow_id`, `organization_id`), le `kind`, le `status`, l'entree (id,
    workflow_kind, title, description, source_text, references), les etapes (id, kind, title,
    description, position, requires_ceo_validation), le resultat candidat (summary, candidate_plan,
    expertise_needs, risks, requires_ceo_validation, non_final_notice) et les references du
    workflow.
    Serialisation **explicite et stable** (delimiteurs de controle fixes), sans horloge, random,
    UUID
    ni JSON instable ; l'ordre des tuples est **conserve**.
    """
    input_part = _GROUP_SEP.join(
        (
            workflow_input.id,
            workflow_input.workflow_kind.value,
            workflow_input.title,
            workflow_input.description,
            workflow_input.source_text,
            _serialize_references(workflow_input.references),
        )
    )
    payload = "|".join(
        (
            workflow_id,
            organization_id,
            kind.value,
            status.value,
            "input:" + input_part,
            "steps:" + _serialize_steps(steps),
            "result:" + _serialize_result(candidate_result),
            "refs:" + _serialize_references(references),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class StartupWorkflow(ImmutableModel):
    """Workflow Startup OS **immuable et declaratif**. Un squelette candidat, jamais un moteur.

    Champs : ``id`` / ``organization_id`` (non vides), ``kind`` (`StartupWorkflowKind`), ``status``
    (`StartupWorkflowStatus`), ``input`` (`StartupWorkflowInput`), ``steps`` (>= 1 etape ; positions
    1-indexees strictement croissantes, sans doublon), ``candidate_result``
    (`StartupWorkflowCandidateResult`, dont ``requires_ceo_validation`` **doit valoir** ``True``),
    ``references`` (tuple declaratif), ``content_hash`` (**verifie**).

    Immuable (``frozen``) et deterministe. N'expose **aucune** methode d'execution, d'application,
    de
    decision, de deploiement, de creation de solution/equipe IA, d'appel LLM, d'ecriture audit/
    memoire, de declenchement E7 ni d'ouverture E9 : c'est une **donnee** qui **decrit** un chemin
    candidat exigeant la validation du CEO. Ne rouvre aucun contrat E1..E8.
    """

    id: str
    organization_id: str
    kind: StartupWorkflowKind
    status: StartupWorkflowStatus
    input: StartupWorkflowInput
    steps: tuple[StartupWorkflowStep, ...]
    candidate_result: StartupWorkflowCandidateResult
    references: tuple[StartupWorkflowReference, ...] = ()
    content_hash: str

    @field_validator("id", "organization_id", "content_hash")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Un workflow est explicite : id, organisation et empreinte non vides."""
        if not value:
            raise ValueError("id, organization_id et content_hash sont requis")
        return value

    @field_validator("steps")
    @classmethod
    def _steps_positions_strictly_increasing(
        cls, value: tuple[StartupWorkflowStep, ...]
    ) -> tuple[StartupWorkflowStep, ...]:
        """Au moins une etape ; positions **1-indexees strictement croissantes**, sans doublon."""
        if not value:
            raise ValueError("un workflow doit comporter au moins une etape")
        positions = [step.position for step in value]
        if positions[0] != 1:
            raise ValueError("la premiere etape doit avoir la position 1")
        for previous, current in pairwise(positions):
            if current <= previous:
                raise ValueError(
                    "les positions des etapes doivent etre strictement croissantes, sans doublon"
                )
        return value

    @model_validator(mode="after")
    def _requires_ceo_validation_and_seal(self) -> StartupWorkflow:
        """Le resultat **exige** la validation CEO ; ``content_hash`` scelle le workflow.

        Deux invariants : (1) ``candidate_result.requires_ceo_validation`` doit valoir ``True`` — un
        resultat de workflow n'est jamais auto-valide ; (2) l'empreinte doit correspondre au contenu
        declaratif du workflow, sinon il est refuse.
        """
        if not self.candidate_result.requires_ceo_validation:
            raise ValueError(
                "candidate_result.requires_ceo_validation doit etre True : un resultat de workflow "
                "exige toujours la validation du CEO"
            )
        expected = compute_workflow_hash(
            workflow_id=self.id,
            organization_id=self.organization_id,
            kind=self.kind,
            status=self.status,
            workflow_input=self.input,
            steps=self.steps,
            candidate_result=self.candidate_result,
            references=self.references,
        )
        if self.content_hash != expected:
            raise ValueError(
                "content_hash doit etre l'empreinte SHA-256 du contenu declaratif du workflow"
            )
        return self

    @classmethod
    def of(
        cls,
        *,
        workflow_id: str,
        organization_id: str,
        kind: StartupWorkflowKind,
        status: StartupWorkflowStatus,
        workflow_input: StartupWorkflowInput,
        steps: tuple[StartupWorkflowStep, ...],
        candidate_result: StartupWorkflowCandidateResult,
        references: tuple[StartupWorkflowReference, ...] = (),
    ) -> StartupWorkflow:
        """Construit un workflow en scellant automatiquement son empreinte. Sans effet de bord."""
        return cls(
            id=workflow_id,
            organization_id=organization_id,
            kind=kind,
            status=status,
            input=workflow_input,
            steps=steps,
            candidate_result=candidate_result,
            references=references,
            content_hash=compute_workflow_hash(
                workflow_id=workflow_id,
                organization_id=organization_id,
                kind=kind,
                status=status,
                workflow_input=workflow_input,
                steps=steps,
                candidate_result=candidate_result,
                references=references,
            ),
        )


# --- Validation d'une notice de resultat candidat non final (deterministe, sans semantique) ---

# Affirmations positives **dangereuses** : rejettent la notice meme si elle cite les mots-cles.
_DANGEROUS_NOTICE_PHRASES: tuple[str, ...] = (
    "solution finale",
    "prete a executer",
    "pret a executer",
    "prete a deployer",
    "pret a deployer",
    "application automatique",
    "approuve sans ceo",
    "sans validation ceo",
    "sans validation du ceo",
)

# La notice doit porter une variante de **chacun** des quatre groupes de garantie :
# (1) candidat, (2) non final, (3) non applique/aucune solution appliquee, (4) validation CEO.
_CANDIDATE_PHRASES: tuple[str, ...] = (
    "candidat",
    "candidate",
)
_NON_FINAL_PHRASES: tuple[str, ...] = (
    "non final",
    "non finale",
    "pas final",
    "pas finale",
)
_NON_APPLIED_PHRASES: tuple[str, ...] = (
    "non applique",
    "non appliquee",
    "pas applique",
    "pas appliquee",
    "aucune solution n'est appliquee",
    "aucune solution n est appliquee",
    "ne cree ni n'applique",
    "ne cree ni n applique",
    "ne cree pas de solution",
    "n'applique aucune solution",
    "n applique aucune solution",
)
_CEO_VALIDATION_PHRASES: tuple[str, ...] = (
    "validation ceo",
    "validation du ceo",
    "validation explicite du ceo",
    "necessite validation ceo",
    "necessite la validation du ceo",
    "exige la validation du ceo",
    "requiert validation ceo",
    "requiert la validation du ceo",
)

_ACCENT_FOLD = str.maketrans("àâäéèêëîïôöùûüç", "aaaeeeeiioouuuc")


def _normalize_notice(value: str) -> str:
    """Normalise une notice : minuscule, apostrophes droites, sans accent. Comparaison stable."""
    return value.lower().replace("\u2019", "'").translate(_ACCENT_FOLD)


def _notice_asserts_non_final(value: str) -> bool:
    """Vrai si la notice porte **les quatre** garanties, sans aucune formulation dangereuse.

    Deterministe et local (aucun moteur semantique) : (1) rejet immediat si une formulation
    dangereuse est presente ; (2) sinon, acceptation seulement si les quatre garanties sont
    presentes — **candidat**, **non final**, **non applique** (ou « aucune solution appliquee » /
    « ne cree pas de solution ») **et** **validation CEO**.
    """
    folded = _normalize_notice(value)
    if any(bad in folded for bad in _DANGEROUS_NOTICE_PHRASES):
        return False
    return (
        any(phrase in folded for phrase in _CANDIDATE_PHRASES)
        and any(phrase in folded for phrase in _NON_FINAL_PHRASES)
        and any(phrase in folded for phrase in _NON_APPLIED_PHRASES)
        and any(phrase in folded for phrase in _CEO_VALIDATION_PHRASES)
    )
