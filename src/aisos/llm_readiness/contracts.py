"""Contrats d'appel LLM contrôlés (C0.8 — LLM Production Readiness réaligné).

Tracabilite : AI-SOS_Cahier_des_Charges_Consolidation_E1_E8 (phase C0), TRACEABILITY.md (C0.8),
docs/strategy/AI-SOS-vision-fondatrice-mission-produit-realignement-C0.md,
docs/llm/C0-8-llm-production-readiness.md, docs/implementation/08-security-and-permissions.md.

Mission produit : AI-SOS est **d'abord une fabrique de solutions**. C0.8 se limite a **preparer** :
poser des contrats d'appel LLM **controles, deterministes en test, desactivables et traçables**,
pour
que l'organisation IA puisse **plus tard** recevoir une intelligence reelle **sans perte de controle
humain** — **sans jamais** appeler un LLM reel, decider, valider, appliquer, muter, ecrire/reecrire
l'audit, ecrire la memoire, creer/ameliorer une solution, creer une equipe IA, declencher E7 ni
ouvrir E9.

Formule centrale : *preparer != activer une autonomie ; le LLM est un **fournisseur d'assistance
controlee**, jamais un decideur.* Une demande (`LLMReadinessRequest`) et une reponse
(`LLMReadinessResponse`) sont des **donnees immuables et declaratives** : elles **decrivent** une
assistance possible, elles ne **font** rien. La reponse ne decide pas, n'applique pas, **ne remplace
ni le CEO ni l'audit**.

Frontieres (preparer n'est ni appeler, ni decider, ni appliquer) :
  * **aucun provider reel** : aucun mode `LIVE_PRODUCTION` ; les modes sont `REPLAY_ONLY`,
    `DETERMINISTIC_TEST`, `DISABLED`, `PROVIDER_READY_DECLARATIVE` (declaratif) — aucun n'appelle un
    modele ; `model_label` / `provider_label` sont de simples **etiquettes**, jamais un client ;
  * **reponse non decisionnelle** : chaque reponse porte un `non_decision_notice` obligatoire
    rappelant que le LLM ne decide pas, n'applique pas, ne remplace pas le CEO ni l'audit ;
  * **references declaratives** : `LLMReadinessReference` **pointe** (par chaine) vers une reference
    d'audit, un contexte memoire, une decision CEO, un record, une recommandation, une trace, ou un
    **futur** contexte projet/solution/equipe — sans le resoudre, l'importer ni le muter ;
  * **immuable et deterministe** : fige (frozen) ; a memes champs, meme donnee ; `content_hash`
    scelle la reponse.

C0.8 ne rouvre aucun contrat E1..E8, ne modifie ni C0.1..C0.7, n'introduit aucun appel reseau, clef
d'API, embedding, vector store ni RAG, et n'anticipe pas C0.9. E9 reste ferme. Le cerveau reste
gele.
"""

from __future__ import annotations

import hashlib
from enum import StrEnum

from pydantic import field_validator, model_validator

from aisos.schemas.base import ImmutableModel


class LLMReadinessMode(StrEnum):
    """Mode d'execution **sur** d'une demande LLM. Aucun mode n'appelle un provider reel.

    `REPLAY_ONLY` (rejoue une reponse enregistree hors ligne), `DETERMINISTIC_TEST` (reponse
    deterministe de test), `DISABLED` (LLM eteint : aucune assistance), `PROVIDER_READY_DECLARATIVE`
    (declare qu'un provider **pourrait** etre branche plus tard, sans l'appeler). **Aucun**
    `LIVE_PRODUCTION` : C0.8 prepare, il n'active jamais un appel reel.
    """

    REPLAY_ONLY = "replay_only"
    DETERMINISTIC_TEST = "deterministic_test"
    DISABLED = "disabled"
    PROVIDER_READY_DECLARATIVE = "provider_ready_declarative"


class LLMReadinessPurpose(StrEnum):
    """Intention **d'assistance** descriptive d'une demande. Jamais une action ni une decision.

    Qualifie l'aide attendue : resume de contexte, aide a la reponse, au raisonnement, a la
    redaction, a l'identification de risques, a l'analyse d'une solution, a l'idee d'amelioration,
    au
    briefing du CEO. Ce sont des **intentions d'assistance controlee** ; aucune ne cree de solution,
    ne prend de decision ni ne declenche d'action.
    """

    CONTEXT_SUMMARY = "context_summary"
    QUESTION_ANSWERING_ASSISTANCE = "question_answering_assistance"
    REASONING_ASSISTANCE = "reasoning_assistance"
    DRAFTING_ASSISTANCE = "drafting_assistance"
    RISK_IDENTIFICATION_ASSISTANCE = "risk_identification_assistance"
    SOLUTION_ANALYSIS_ASSISTANCE = "solution_analysis_assistance"
    IMPROVEMENT_IDEA_ASSISTANCE = "improvement_idea_assistance"
    CEO_BRIEFING_ASSISTANCE = "ceo_briefing_assistance"


class LLMReadinessStatus(StrEnum):
    """Statut **declaratif** d'une reponse de readiness. Jamais une decision ni une application.

    `PRODUCED` : une assistance **non autoritaire** a ete produite dans un mode sur (replay /
    deterministe). `DECLINED` : aucune assistance produite (mode desactive ou demande non preparee).
    Aucun statut n'approuve, n'applique, ne declenche E7 ni n'ouvre E9.
    """

    PRODUCED = "produced"
    DECLINED = "declined"


class LLMReadinessReferenceKind(StrEnum):
    """Type **descriptif** d'une reference de readiness. Une etiquette, jamais un objet vivant.

    Pointe, de maniere declarative (par chaine), vers une reference d'audit, un contexte memoire,
    une
    decision CEO, un enregistrement de persistance, une recommandation, une trace, ou un **futur**
    contexte projet / solution / equipe. Ne resout ni ne mute aucun objet ; ne cree aucun objet
    produit actif.
    """

    AUDIT_REFERENCE = "audit_reference"
    MEMORY_CONTEXT = "memory_context"
    CEO_DECISION_RECORD = "ceo_decision_record"
    PERSISTENCE_RECORD = "persistence_record"
    RECOMMENDATION = "recommendation"
    TRACE = "trace"
    PROJECT_CONTEXT_FUTURE = "project_context_future"
    SOLUTION_CONTEXT_FUTURE = "solution_context_future"
    TEAM_CONTEXT_FUTURE = "team_context_future"


class LLMReadinessReference(ImmutableModel):
    """Reference **declarative** immuable attachee a une demande/reponse. Une etiquette, jamais un
    objet.

    Champs : ``kind`` (`LLMReadinessReferenceKind`), ``reference`` (chaine non vide — ex.
    ``"audit_reference://ev-1"``), ``label`` (optionnel). **Pointe** vers un contexte sans le
    resoudre, l'importer ni le muter.
    """

    kind: LLMReadinessReferenceKind
    reference: str
    label: str = ""

    @field_validator("reference")
    @classmethod
    def _reference_not_blank(cls, value: str) -> str:
        """Une reference est explicite : la chaine de reference est non vide."""
        if not value:
            raise ValueError("la reference d'une demande/reponse LLM ne peut etre vide")
        return value


class LLMReadinessRequest(ImmutableModel):
    """Demande LLM **controlee** immuable. Une donnee declarative, jamais un appel.

    Champs : ``id`` (non vide), ``organization_id`` (non vide), ``purpose`` (`LLMReadinessPurpose`),
    ``mode`` (`LLMReadinessMode`), ``prompt`` (texte de la demande d'assistance), ``context``
    (contexte fourni), ``references`` (tuple de `LLMReadinessReference` declaratives),
    ``safety_notice`` (rappel de securite/controle). La demande **decrit** une assistance possible ;
    elle n'appelle aucun modele, ne decide, n'applique et ne mute rien. La validite **de securite**
    (mode sur, prompt et notice presents, aucun verbe d'action interdit) est evaluee par
    `LLMReadinessPolicy`, jamais ici.
    """

    id: str
    organization_id: str
    purpose: LLMReadinessPurpose
    mode: LLMReadinessMode
    prompt: str = ""
    context: str = ""
    references: tuple[LLMReadinessReference, ...] = ()
    safety_notice: str = ""

    @field_validator("id", "organization_id")
    @classmethod
    def _identity_not_blank(cls, value: str) -> str:
        """Une demande est explicite : identifiant et organisation non vides."""
        if not value:
            raise ValueError("id et organization_id sont requis")
        return value


# Delimiteurs de serialisation stables (caracteres de controle ASCII, absents d'un texte normal).
_FIELD_SEP = "\x1f"
_RECORD_SEP = "\x1e"


def _serialize_references(references: tuple[LLMReadinessReference, ...]) -> str:
    """Serialise les references de maniere **stable et deterministe**, dans l'ordre du tuple."""
    return _RECORD_SEP.join(
        _FIELD_SEP.join((ref.kind.value, ref.reference, ref.label)) for ref in references
    )


def compute_response_hash(
    *,
    response_id: str,
    request_id: str,
    status: LLMReadinessStatus,
    content: str,
    model_label: str,
    provider_label: str,
    non_decision_notice: str,
    references: tuple[LLMReadinessReference, ...] = (),
) -> str:
    """Calcule l'empreinte SHA-256 (hex) du contenu declaratif d'une reponse. Deterministe.

    Scelle l'identite (`response_id`, `request_id`), le `status`, le `content`, les etiquettes
    (`model_label`, `provider_label`), le `non_decision_notice` et les `references` (serialisation
    explicite et stable, ordre du tuple conserve). Sans dependance externe ni horloge interne.
    """
    payload = "|".join(
        (
            response_id,
            request_id,
            status.value,
            content,
            model_label,
            provider_label,
            non_decision_notice,
            "refs:" + _serialize_references(references),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# --- Validation d'une notice reellement non decisionnelle (deterministe, sans semantique) ---

# Affirmations positives **dangereuses** : rejettent la notice meme si elle mentionne les mots-cles.
_DANGEROUS_NOTICE_PHRASES: tuple[str, ...] = (
    "remplace le ceo",
    "remplace l'audit",
    "fait foi",
    "decide pour",
    "valide la decision",
    "applique la decision",
)

# La notice doit porter une variante de **chacun** des trois groupes de non-affirmation.
_NON_DECISION_PHRASES: tuple[str, ...] = (
    "ne decide pas",
    "non decisionnel",
    "ne prend pas de decision",
)
_NON_REPLACE_CEO_PHRASES: tuple[str, ...] = (
    "ne remplace pas le ceo",
    "ne remplace ni le ceo",
    "ne se substitue pas au ceo",
    "ne se substitue ni au ceo",
    "ni le ceo",
    "ni au ceo",
)
_NON_REPLACE_AUDIT_PHRASES: tuple[str, ...] = (
    "ne remplace pas l'audit",
    "ne remplace jamais l'audit",
    "ne se substitue pas a l'audit",
    "ne se substitue jamais a l'audit",
    "ni l'audit",
    "ni a l'audit",
)

_ACCENT_FOLD = str.maketrans("àâäéèêëîïôöùûüç", "aaaeeeeiioouuuc")


def _normalize_notice(value: str) -> str:
    """Normalise une notice : minuscule, apostrophes droites, sans accent. Comparaison stable."""
    return value.lower().replace("\u2019", "'").translate(_ACCENT_FOLD)


def _notice_asserts_non_decision(value: str) -> bool:
    """Vrai si la notice affirme **les trois** interdits sans affirmation positive dangereuse.

    Deterministe et local : (1) rejet immediat si une formulation dangereuse est presente ; (2)
    sinon, acceptation seulement si une variante de non-decision **et** de non-remplacement du CEO
    **et** de non-remplacement de l'audit est presente.
    """
    folded = _normalize_notice(value)
    if any(bad in folded for bad in _DANGEROUS_NOTICE_PHRASES):
        return False
    return (
        any(phrase in folded for phrase in _NON_DECISION_PHRASES)
        and any(phrase in folded for phrase in _NON_REPLACE_CEO_PHRASES)
        and any(phrase in folded for phrase in _NON_REPLACE_AUDIT_PHRASES)
    )


class LLMReadinessResponse(ImmutableModel):
    """Reponse LLM **declarative** immuable et scellee. Une assistance non autoritaire, jamais un
    acte.

    Champs : ``id`` (non vide), ``request_id`` (non vide), ``status`` (`LLMReadinessStatus`),
    ``content`` (texte d'assistance, eventuellement vide si `DECLINED`), ``model_label`` /
    ``provider_label`` (**etiquettes** descriptives, non vides ; jamais un client reel),
    ``references`` (tuple declaratif), ``non_decision_notice`` (**obligatoire ET valide** : rappelle
    que le LLM ne decide pas et ne remplace ni le CEO ni l'audit), ``content_hash`` (**verifie**).

    Immuable (``frozen``) et deterministe. N'expose **aucune** methode de decision, d'application,
    de
    mutation ni de declenchement : c'est une **donnee**. Ne cree ni decision CEO, ni objet produit ;
    ne remplace ni le CEO ni l'audit. Ne rouvre aucun contrat E1..E8.
    """

    id: str
    request_id: str
    status: LLMReadinessStatus
    content: str = ""
    model_label: str
    provider_label: str
    references: tuple[LLMReadinessReference, ...] = ()
    non_decision_notice: str
    content_hash: str

    @field_validator("id", "request_id", "model_label", "provider_label", "content_hash")
    @classmethod
    def _text_not_blank(cls, value: str) -> str:
        """Une reponse est explicite : id, request_id, etiquettes et empreinte non vides."""
        if not value:
            raise ValueError(
                "id, request_id, model_label, provider_label et content_hash sont requis"
            )
        return value

    @field_validator("non_decision_notice")
    @classmethod
    def _notice_reasserts_non_decision(cls, value: str) -> str:
        """La notice doit affirmer l'invariant : le LLM **ne decide pas** et **ne remplace ni le CEO
        ni l'audit**.

        Verification **locale et deterministe** (aucun moteur semantique). Il ne suffit **pas** de
        mentionner « decide », « CEO » et « audit » : la notice doit porter une **formulation
        reellement non decisionnelle**. Elle est acceptee seulement si elle rappelle **les trois**
        interdits (non-decision, non-remplacement du CEO, non-remplacement de l'audit) et **aucune**
        affirmation positive dangereuse (« LLM decide », « valide/applique la decision », « remplace
        le CEO/l'audit », « fait foi »). Voir `_notice_asserts_non_decision`.
        """
        if not _notice_asserts_non_decision(value):
            raise ValueError(
                "non_decision_notice doit affirmer explicitement que le LLM ne decide pas et ne "
                "remplace ni le CEO ni l'audit (formulation reellement non decisionnelle requise)"
            )
        return value

    @model_validator(mode="after")
    def _seals_response(self) -> LLMReadinessResponse:
        """Verifie que ``content_hash`` scelle bien le contenu declaratif de la reponse."""
        expected = compute_response_hash(
            response_id=self.id,
            request_id=self.request_id,
            status=self.status,
            content=self.content,
            model_label=self.model_label,
            provider_label=self.provider_label,
            non_decision_notice=self.non_decision_notice,
            references=self.references,
        )
        if self.content_hash != expected:
            raise ValueError(
                "content_hash doit etre l'empreinte SHA-256 du contenu declaratif de la reponse"
            )
        return self

    @classmethod
    def of(
        cls,
        *,
        response_id: str,
        request_id: str,
        status: LLMReadinessStatus,
        model_label: str,
        provider_label: str,
        non_decision_notice: str,
        content: str = "",
        references: tuple[LLMReadinessReference, ...] = (),
    ) -> LLMReadinessResponse:
        """Construit une reponse en scellant automatiquement son empreinte. Sans effet de bord."""
        return cls(
            id=response_id,
            request_id=request_id,
            status=status,
            content=content,
            model_label=model_label,
            provider_label=provider_label,
            references=references,
            non_decision_notice=non_decision_notice,
            content_hash=compute_response_hash(
                response_id=response_id,
                request_id=request_id,
                status=status,
                content=content,
                model_label=model_label,
                provider_label=provider_label,
                non_decision_notice=non_decision_notice,
                references=references,
            ),
        )
