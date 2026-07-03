"""Resolution securisee du secret d'un futur fournisseur LLM reel (infrastructure).

Tracabilite : docs/api/02-authentication.md (secrets hors code), docs/adr/ADR-0010-determinisme-
interactions-llm.md, docs/reports/M1_GOVERNED_REAL_LLM_PLAN.md (§4 gestion des secrets).

Resout la cle d'un fournisseur LLM reel a partir du **NOM** d'une variable d'environnement
(`RealLLMProviderConfig.api_key_env`), **jamais** d'une cle en dur. AUCUN appel reseau, aucun
OpenAI, aucun Anthropic, aucun fournisseur active. La valeur resolue est encapsulee dans un
`Secret` dont la representation est **masquee** (`Secret(***)`) : elle ne peut pas fuir dans un
log, un message d'erreur, un audit ou un enregistrement record/replay — seul `reveal()` l'expose,
a l'instant de l'appel, cote adaptateur reel (non cable ici).
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from aisos.domain.errors import AISOSError
from aisos.infrastructure.llm.config import RealLLMProviderConfig

#: Nom de variable d'environnement POSIX valide : lettre/underscore puis alphanumeriques/underscore.
_ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class SecretResolutionError(AISOSError):
    """Racine des erreurs de resolution de secret. Ne consigne JAMAIS la valeur d'un secret."""

    code = "llm.secret_resolution"
    http_status = 500


class InvalidSecretNameError(SecretResolutionError):
    """Nom de variable d'environnement absent ou invalide (jamais une valeur de secret)."""

    code = "llm.secret_name_invalid"
    http_status = 422


class SecretNotFoundError(SecretResolutionError):
    """Variable d'environnement absente (ou vide) : aucun secret a resoudre. Aucune fuite."""

    code = "llm.secret_not_found"
    http_status = 503


class Secret:
    """Valeur de secret encapsulee dont la representation est **masquee**.

    `repr`/`str` renvoient `Secret(***)` : la valeur ne peut pas fuir dans un log, un f-string, un
    message d'erreur, un audit ou un enregistrement. Seul `reveal()` expose la valeur, a utiliser
    uniquement a l'instant de l'appel reel (cote adaptateur, non cable ici).
    """

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value

    def reveal(self) -> str:
        """Expose la valeur reelle. A n'appeler qu'au moment strict de l'usage (jamais a logger)."""
        return self._value

    def __repr__(self) -> str:
        return "Secret(***)"

    def __str__(self) -> str:
        return "Secret(***)"


@runtime_checkable
class SecretResolver(Protocol):
    """Port de resolution d'un secret a partir du NOM d'une variable d'environnement."""

    def resolve(self, name: str) -> Secret:
        """Resout le secret nomme `name`. Leve une erreur explicite (sans fuite) sinon."""
        ...


class EnvironmentSecretResolver:
    """Resolveur lisant le secret depuis l'environnement du processus (aucun reseau).

    L'environnement est injectable (tests) ; par defaut `os.environ`. Une variable absente **ou
    vide** est traitee comme un secret manquant (refus explicite).
    """

    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        self._environ: Mapping[str, str] = os.environ if environ is None else environ

    def resolve(self, name: str) -> Secret:
        _validate_secret_name(name)
        value = self._environ.get(name)
        if not value:
            # Absent ou vide : aucune valeur a divulguer ; le message ne porte que le NOM.
            raise SecretNotFoundError(
                f"secret introuvable : variable d'environnement '{name}' absente ou vide"
            )
        return Secret(value)


def _validate_secret_name(name: str) -> None:
    """Valide un nom de variable d'environnement. Le message ne contient jamais de secret."""
    if not name or not _ENV_NAME_RE.match(name):
        raise InvalidSecretNameError(
            f"nom de variable d'environnement invalide : {name!r} "
            "(attendu : lettre/underscore puis alphanumeriques/underscore)"
        )


def resolve_api_key(config: RealLLMProviderConfig, resolver: SecretResolver) -> Secret:
    """Resout la cle du fournisseur a partir de `config.api_key_env` **uniquement**.

    Ne branche aucun fournisseur, n'effectue aucun appel reseau : renvoie seulement le `Secret`
    masque, qu'un futur adaptateur reel `reveal()`ra a l'instant de l'appel. Refuse explicitement
    si aucune variable n'est declaree.
    """
    name = config.api_key_env
    if name is None:
        raise InvalidSecretNameError(
            "configuration sans `api_key_env` : aucune variable de secret declaree"
        )
    return resolver.resolve(name)
