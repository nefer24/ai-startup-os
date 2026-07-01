# Governance

> How AI-SOS is governed as an intelligent organization.

This directory defines the governance of AI-SOS. It describes how decisions are made across agents and councils, how humans validate them, how new agents are created, how risks are managed, and how activity is audited. Governance ensures that important decisions are never taken by a single agent.

## Contents

- [`roles.md`](./roles.md) — the official roles (CEO, Chief AI Architect, Claude Code) and their responsibilities.
- [`git-workflow.md`](./git-workflow.md) — the official Git strategy and Pull Request governance.
- [`human-validation.md`](./human-validation.md) — how and when humans validate decisions.
- [`decision-process.md`](./decision-process.md) — how decisions move from proposal to approval.
- [`agent-creation.md`](./agent-creation.md) — how new specialized agents are proposed and created.
- [`risk-management.md`](./risk-management.md) — how risks are identified and mitigated.
- [`audit.md`](./audit.md) — how activity and decisions are traced and reviewed.

## Principe de délégation contrôlée

Le principe suivant est un **principe officiel de gouvernance AI-SOS** (décision d'architecture [004](../DECISIONS.md)) :

> **Principe de délégation contrôlée**
>
> « Les agents IA peuvent exécuter des actions importantes uniquement après une autorisation explicite de l'autorité humaine compétente.
>
> L'exécution peut être déléguée.
>
> La responsabilité ne l'est jamais. »

Ce principe encadre toute action importante réalisée par un agent — notamment la fusion d'une Pull Request, la création d'une release ou la création d'un nouvel agent. Il prolonge la gouvernance humaine de la Constitution : la puissance d'exécution des agents ne s'exerce jamais sans une décision humaine qui l'autorise et l'assume.
