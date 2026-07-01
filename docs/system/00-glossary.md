# System Glossary

> Vocabulaire de référence de l'architecture conceptuelle d'AI-SOS.

Ce glossaire fixe les définitions communes du dossier `docs/system/` afin d'éviter toute divergence d'interprétation entre les documents qui le composent. Il complète, sans le remplacer, le glossaire général [`../12-glossary.md`](../12-glossary.md), auquel il convient de se référer pour le vocabulaire transverse au projet. Conformément à la convention éditoriale du dossier, les titres de niveau H1 sont rédigés en anglais tandis que le corps du texte est rédigé en français.

## Termes

### CEO
Autorité humaine finale du système. Le CEO fixe l'intention et détient le pouvoir de décision ultime : aucune orientation majeure ne s'impose sans son accord. Toutes les instances du système opèrent en dernier ressort sous son autorité.

### Executive Board
Instance de direction qui traduit l'intention du CEO en priorités actionnables. L'Executive Board arbitre entre les objectifs et fixe le cap donné aux autres instances, sans se substituer à l'autorité finale du CEO. Son fonctionnement est détaillé dans [`11-executive-board.md`](./11-executive-board.md).

### Orchestrateur
Rôle de coordination chargé d'articuler les échanges entre les Conseils d'Experts, les Départements et les Agents spécialisés. L'Orchestrateur ne décide jamais seul : il structure la circulation de l'information et prépare les éléments soumis à la validation humaine. Son rôle est décrit dans [`02-orchestrator.md`](./02-orchestrator.md).

### Conseils d'Experts
Instances de délibération qui confrontent les points de vue et élaborent des recommandations argumentées. Ils sont désignés « Conseils d'Experts IA » dans la Constitution : il s'agit de la même notion, sous une dénomination alternative. Leur fonctionnement est précisé dans [`03-expert-councils.md`](./03-expert-councils.md).

### Départements
Regroupements d'Agents spécialisés par domaine d'expertise, offrant une organisation cohérente des compétences du système. Chaque Département fédère les agents dont la spécialité relève d'un même champ. Voir [`04-departments.md`](./04-departments.md).

### Agent spécialisé
Acteur du système doté d'une spécialité précise, opérant au sein d'un Département. Il porte un périmètre défini d'expertise et agit dans les limites de son contrat de rôle. Voir [`05-specialized-agents.md`](./05-specialized-agents.md).

### Spécialité
Terme canonique désignant l'expertise d'un agent, entendue comme un ensemble cohérent de compétences. Les termes « compétences » et « expertise » sont employés comme synonymes de la spécialité tout au long du dossier. La spécialité délimite le champ légitime d'intervention d'un agent.

### Contrat de rôle
Ensemble structuré définissant, pour un agent, sa mission, sa spécialité, ses responsabilités, ses limites et ses permissions. Le contrat de rôle constitue la référence qui encadre l'action de l'agent. Toute action de l'agent doit rester conforme à ce contrat.

### Recommandation
Proposition argumentée issue d'une délibération, destinée à la validation humaine. Une recommandation n'est jamais une décision : elle éclaire un choix sans l'imposer. Elle expose les options, leurs justifications et, le cas échéant, une orientation privilégiée.

### Validation humaine
Acte par lequel une autorité humaine décide, sur la base d'une recommandation. La validation humaine est un acte, distinct d'un acteur : elle n'est pas incarnée par une instance particulière mais exercée par l'autorité compétente. Elle transforme une proposition en décision effective.

### Délégation contrôlée
Principe selon lequel l'exécution d'une tâche peut être déléguée, mais jamais la responsabilité qui s'y attache. L'autorité qui délègue demeure comptable du résultat. La délégation s'exerce dans un cadre défini par le contrat de rôle et les permissions.

### Action courante vs action importante
Distinction fondée sur les permissions attachées à une action. Une action courante s'inscrit dans le fonctionnement ordinaire et ne requiert pas d'autorisation particulière. Une action importante, en raison de sa portée, requiert une autorisation humaine préalable.

### Utilisateur
Porteur d'un besoin à l'origine d'une demande adressée au système. Sa demande est prise en charge sous l'autorité du CEO et de l'Executive Board. L'Utilisateur se distingue du CEO : il exprime un besoin, il ne détient pas l'autorité finale de décision.

### Débat
Phase de confrontation des options au sein des Conseils d'Experts. Le Débat permet d'éprouver les hypothèses et d'exposer les désaccords avant l'élaboration d'une recommandation. Il constitue le moment délibératif dont procède la qualité des recommandations produites.

### Escalade
Remontée d'une question hors domaine ou d'un blocage vers un niveau d'autorité supérieur. L'escalade suit un cheminement défini : du spécialiste vers l'Orchestrateur, puis, si nécessaire, vers le CEO. Elle garantit qu'aucune difficulté ne reste sans traitement approprié.

### Les cinq mémoires
Ensemble des cinq registres de mémoire du système : mémoire à court terme, mémoire à long terme, mémoire de projet, mémoire utilisateur et mémoire organisationnelle. Chacune répond à un horizon et à un usage distincts. Leur articulation est décrite dans [`06-memory.md`](./06-memory.md).

### Dérive (drift)
Écart progressif et non voulu du comportement d'un agent par rapport à sa spécialité. La dérive s'installe insensiblement et éloigne l'agent de son contrat de rôle. Sa détection et sa correction sont nécessaires au maintien de la cohérence du système.

### Versioning conceptuel
Suivi des versions successives d'un agent, d'une décision ou d'un savoir, afin d'assurer la reproductibilité. Le versioning conceptuel permet de retracer l'évolution d'un élément et de comprendre l'état dans lequel une décision a été prise. Il soutient la traçabilité et l'auditabilité du système.

### Propriétés systémiques
Qualités transverses du système, valables au-delà d'un composant isolé et caractérisant son comportement d'ensemble. Elles expriment ce que le système doit garantir globalement. Elles sont présentées dans [`10-system-principles.md`](./10-system-principles.md).
