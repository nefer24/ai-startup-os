"""Authentification deterministe en memoire (Phase 17).

Tracabilite : docs/api/02-authentication.md. **Aucun OIDC reel, aucun JWT reel** : ce cœur
associe des jetons opaques a des `Principal` deja etablis, pour les tests et l'integration.
L'authentification OIDC/JWT reelle (DT-07) sera un adaptateur ulterieur, non present ici.
"""

from __future__ import annotations

from aisos.domain.errors import UnauthenticatedError
from aisos.security.interfaces import Principal


class StaticAuthenticator:
    """Registre jeton -> Principal (deterministe, sans crypto, sans OIDC).

    Implemente le Protocol `aisos.security.interfaces.Authenticator`.
    """

    def __init__(self, tokens: dict[str, Principal] | None = None) -> None:
        self._tokens: dict[str, Principal] = dict(tokens or {})

    def register(self, token: str, principal: Principal) -> None:
        self._tokens[token] = principal

    async def authenticate(self, token: str) -> Principal:
        principal = self._tokens.get(token)
        if principal is None:
            raise UnauthenticatedError("jeton inconnu ou absent")
        return principal
