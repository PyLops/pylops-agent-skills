# pylops-agent-skills
Agent skills for developers and scientists that use [PyLops](https://github.com/PyLops/pylops).

Each skill is a folder with a `SKILL.md` file (plus optional reference files)
following the open [Agent Skills](https://agentskills.io) format, so it can be
used by any coding agent that supports skills.

**Note**: skills for contributing to the PyLops
library itself live in the PyLops repository.

## Skills

| Skill | What it does |
|-------|--------------|
| `wrap-operator` | Turns your forward model (local code, a URL or maths) into a PyLops operator in your project: picks between composing existing operators, `FunctionOperator` or a `LinearOperator` subclass, checks the adjoint with the dot-test, and adds tests. Triggered by requests such as *"make my blurring function a PyLops operator"*. |

## Installation

### Any agent, via the `skills` CLI

The [`skills`](https://github.com/vercel-labs/skills) CLI installs the skills
into Claude Code, Codex, Cursor, GitHub Copilot, OpenCode and many other agents:

```bash
npx skills add PyLops/pylops-agent-skills --list         # list available skills
npx skills add PyLops/pylops-agent-skills                # interactive installation
npx skills add PyLops/pylops-agent-skills --skill wrap-operator -a codex -g    # direct installation
```

with `-a <agent>` to pick the target agent(s) and `-g` to install for your user
instead of the current project.

### Claude Code plugin marketplace

This repository is also a Claude Code plugin marketplace:

```
/plugin marketplace add PyLops/pylops-agent-skills
/plugin install pylops@pylops-agent-skills
```

Skills are then available as `/pylops:<skill-name>`.

### Manual

Copy a skill folder (e.g. `plugins/pylops/skills/wrap-operator/`) into the
skills directory your agent reads from (e.g. `.agents/skills/` or
`.claude/skills/`).

## Contributing

Add a skill as `plugins/pylops/skills/<skill-name>/SKILL.md`, with any
reference files next to it. 

Then bump `version` in `plugins/pylops/.claude-plugin/plugin.json` and check that the skill is picked up:

```bash
npx skills add . --list
claude plugin validate --strict . && claude plugin validate --strict plugins/pylops
```

**Note:** keep the instructions agent-agnostic: describe actions (e.g. "fetch the URL", "run the tests") rather than tool names of a specific agent.


## License

LGPL-2.1, see [LICENSE](LICENSE).
