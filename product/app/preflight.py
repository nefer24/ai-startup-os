"""Pré-vol benchmark en ligne de commande (D20 — v1.3.6.2).

    python -m app.preflight [--expected <sha>] [--json]

Affiche l'identité du build tel qu'il serait exécuté par CE processus Python (commit, propreté de
l'arbre, fournisseur et version du SDK, empreintes de la politique de raisonnement et de la
configuration, plafonds) et le verdict MATCH / MISMATCH contre le freeze attendu.

Limite explicite : cette commande décrit le code présent sur le disque au moment où elle tourne ;
l'identité d'un serveur Uvicorn déjà lancé s'obtient par `GET /benchmark/preflight` ou
`GET /product/status` sur ce serveur — c'est lui qui répond avec SON commit.
"""

from __future__ import annotations

import argparse
import json
import sys

from app.build_identity import preflight, render_preflight
from app.config import get_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI-SOS benchmark preflight (D20)")
    parser.add_argument("--expected", default="", help="freeze attendu (SHA court ou complet)")
    parser.add_argument("--json", action="store_true", help="sortie JSON")
    args = parser.parse_args(argv)
    settings = get_settings()
    report = preflight(settings, args.expected or settings.mission_expected_freeze)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    else:
        print(render_preflight(report))
    return 0 if report["verdict"] in {"MATCH", "NO_EXPECTED_FREEZE"} and not report["reason"] else 1


if __name__ == "__main__":  # pragma: no cover - point d'entrée
    sys.exit(main())
