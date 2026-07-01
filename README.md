# AI-SOS — Artificial Intelligence Solution Operating System

> A reusable framework for building and operating startups with specialized AI agents.

AI-SOS (Artificial Intelligence Solution Operating System) is a platform where specialized AI agents collaborate to design, build, and operate startups. It brings together agents, workflows, prompts, templates, and documentation into a single, coherent operating system for turning ideas into real products.

## Mission

Enable the autonomous creation and operation of startups by orchestrating specialized AI agents — each responsible for a distinct discipline — through well-defined workflows and shared context.

## Philosophy

- **Specialization** — every agent owns a clear discipline and does it well.
- **Collaboration** — agents work together through explicit, documented handoffs.
- **Consistency** — shared templates and standards keep every deliverable coherent.
- **Memory** — knowledge persists across time and projects so nothing is lost.
- **Evolvability** — the structure is designed to grow as the platform matures.

## AI-SOS Organization

AI-SOS is not only a set of agents — it is an intelligent organization. Important decisions are never made by a single agent: specialized agents debate, critique proposals, and identify risks before any important implementation, and a human always validates the final decision.

- **Agents** — specialized AI agents, each owning a distinct discipline. See [`agents/`](./agents/).
- **Orchestrator** — coordinates collaboration between agents: it prepares debates, organizes the work, detects missing skills, and can propose the creation of new agents. It never decides alone. See [`agents/Orchestrator/`](./agents/Orchestrator/).
- **Councils** — AI Expert Councils where several agents deliberate collectively before important decisions. See [`councils/`](./councils/).
- **Governance** — the human governance and decision process; final validation always belongs to a human. See [`governance/`](./governance/).

## Repository Structure

```
.
├── README.md                # This file
├── docs/                    # Core project documentation
├── agents/                  # Definitions for each specialized AI agent
├── councils/                # AI Expert Councils that deliberate before decisions
├── governance/              # Human governance and decision process
├── templates/               # Reusable Markdown templates
├── workflows/               # End-to-end operational workflows
└── memory/                  # Persistent knowledge across projects
```

### `docs/`

Core documentation describing the vision, principles, and operation of AI-SOS.

| Document | Purpose |
| --- | --- |
| [`00-vision.md`](./docs/00-vision.md) | Long-term vision and ambition |
| [`01-principles.md`](./docs/01-principles.md) | Foundational principles and values |
| [`02-architecture.md`](./docs/02-architecture.md) | High-level system architecture |
| [`03-workflow.md`](./docs/03-workflow.md) | How work moves through AI-SOS |
| [`04-roadmap.md`](./docs/04-roadmap.md) | Planned evolution and milestones |
| [`05-technology-stack.md`](./docs/05-technology-stack.md) | Technologies powering the platform |
| [`06-governance.md`](./docs/06-governance.md) | Decision-making and governance model |
| [`07-quality.md`](./docs/07-quality.md) | Quality standards and practices |
| [`08-security.md`](./docs/08-security.md) | Security posture and policies |
| [`09-documentation.md`](./docs/09-documentation.md) | Documentation standards and conventions |
| [`10-agent-lifecycle.md`](./docs/10-agent-lifecycle.md) | Lifecycle of an AI-SOS agent |
| [`11-memory.md`](./docs/11-memory.md) | Memory model and persistence |
| [`12-glossary.md`](./docs/12-glossary.md) | Shared vocabulary |

### `agents/`

Each specialized agent has its own directory containing `README.md`, `prompt.md`, `rules.md`, `inputs.md`, `outputs.md`, and `examples.md`.

- [`Orchestrator/`](./agents/Orchestrator/) — Orchestrator (coordinates the other agents)
- [`CEO/`](./agents/CEO/) — Chief Executive Officer
- [`ProductManager/`](./agents/ProductManager/) — Product Manager
- [`SoftwareArchitect/`](./agents/SoftwareArchitect/) — Software Architect
- [`BackendEngineer/`](./agents/BackendEngineer/) — Backend Engineer
- [`FrontendEngineer/`](./agents/FrontendEngineer/) — Frontend Engineer
- [`AndroidEngineer/`](./agents/AndroidEngineer/) — Android Engineer
- [`iOSEngineer/`](./agents/iOSEngineer/) — iOS Engineer
- [`DatabaseEngineer/`](./agents/DatabaseEngineer/) — Database Engineer
- [`AIEngineer/`](./agents/AIEngineer/) — AI Engineer
- [`QAEngineer/`](./agents/QAEngineer/) — QA Engineer
- [`DevOps/`](./agents/DevOps/) — DevOps Engineer
- [`CyberSecurity/`](./agents/CyberSecurity/) — Cyber Security Engineer
- [`Marketing/`](./agents/Marketing/) — Marketing
- [`Sales/`](./agents/Sales/) — Sales
- [`CustomerSuccess/`](./agents/CustomerSuccess/) — Customer Success

### `councils/`

AI Expert Councils that deliberate before important decisions. Each council contains `README.md`, `members.md`, `workflow.md`, `decision-template.md`, and `examples.md`: [Backend](./councils/BackendCouncil/), [Frontend](./councils/FrontendCouncil/), [Architecture](./councils/ArchitectureCouncil/), [AI](./councils/AICouncil/), [Security](./councils/SecurityCouncil/), [Database](./councils/DatabaseCouncil/), [Product](./councils/ProductCouncil/), [UX](./councils/UXCouncil/), and [Quality](./councils/QualityCouncil/).

### `governance/`

Human governance and the decision process: [human validation](./governance/human-validation.md), [decision process](./governance/decision-process.md), [agent creation](./governance/agent-creation.md), [risk management](./governance/risk-management.md), and [audit](./governance/audit.md).

### `templates/`

Reusable Markdown templates for common deliverables: [vision](./templates/vision-template.md), [architecture](./templates/architecture-template.md), [feature](./templates/feature-template.md), [database](./templates/database-template.md), [api](./templates/api-template.md), [decision](./templates/decision-template.md), [issue](./templates/issue-template.md), [bug](./templates/bug-template.md), and [meeting](./templates/meeting-template.md).

### `workflows/`

End-to-end processes that agents follow: [idea-to-product](./workflows/idea-to-product/), [feature-development](./workflows/feature-development/), [bug-fix](./workflows/bug-fix/), [release](./workflows/release/), and [deployment](./workflows/deployment/).

### `memory/`

Persistent knowledge across time and projects. Per-project memory lives under [`memory/projects/`](./memory/projects/).

## Status

This repository currently contains the **documentation structure**. The detailed content of each document will be authored progressively.
