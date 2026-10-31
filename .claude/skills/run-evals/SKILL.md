---
name: run-evals
description: Run the eval suite of one skill of this repository with a chosen agent model, record the results in the plugin's evals README (tables from scripts/eval_tables.py) and open a PR. Use when the user asks to "run the evals", "run the <skill> evals with <model>", "add <model> to the eval findings" or invokes /run-evals.
---

Goal: one skill's evals run with one agent model, the findings README updated
with that model's final run, and a PR opened. Follow the repository README
("Evals" and "Table Generation") and the rules below.

## 1. Ask what to run

Skip any question the user already answered.

- **Skill**: list the skills that have evals with
  `ls plugins/*/evals/*/ -d` (skip `results`). Each folder is `plugins/<plugin>/evals/<skill>/`;
  the case prefix is the start of its case names (e.g. `sns-`, `sip-`, `dbg-`).
- **Model(s)**: the agent model, as a **full model ID** (e.g. `claude-opus-5-5`,
  `claude-sonnet-5-5`, `claude-haiku-5-5`, `claude-haiku-4-5-20251001`), never an
  alias. Label it with its version ("Opus 5.5").
- **Judge**: default `sonnet`; use `opus` when the agent is Sonnet. The judge must
  differ from the agent model.

Use AskUserQuestion for what is missing.

## 2. Preflight

- `python -c "import pylops; print(pylops.__file__)"` (and `pyproximal` for the
  `pyproximal` plugin) must print a path inside `site-packages` (regular, not
  editable, install); otherwise stop and tell the user.
- Never run `mpiexec`/`mpirun` locally. Plugins whose evals need MPI: tell the user
  to run them themselves.
- `git status`: note unrelated untracked files (leave them out of the commit).

## 3. Run

From `plugins/<plugin>` (cwd does not persist: use `cd` in the same command), in the background:

```bash
claude plugin eval . --case '<prefix>-*' --model <full-model-id> --ablation with-without \
  --judge-model <sonnet|opus> --allow-tools "Write,Bash" -j 4 --no-publish
```

- Always `--no-publish`: the report stays local, nothing is uploaded unless the user asks.
- Several models: launch each at least 5 s apart (same-second starts share a results
  folder and one run is lost). Map folders to models from each run's own
  `Report: …/results/<timestamp>/report.html` line, never by "newest folder".
- Wait for the completion notification, do not poll. Exit code 1 only means some
  graders failed. If a run errored or was partial, tell the user before recording it.

## 4. Tables

Use `scripts/eval_tables.py`, never hand-transcribed numbers:

```bash
python scripts/eval_tables.py "<Model X.Y>=<results dir>" ...
```

Give the new run first, then every model already in the README (folders are in its
"Reports" list), all of the same suite. Check the printed `--model` values match the
labels.

## 5. Update `plugins/<plugin>/evals/README.md`

Only the section of the chosen skill. The README shows **one final run per model**:
no run history, no intermediate runs, no run numbers in prose.

- Add the model's columns (or replace them if the model is already there) in the
  results, fire-runs grader-count and cost tables, copying the script's tables.
- Update the "Results" intro (number of models, judge), the "never fired on the
  negative cases (n/N runs…)" sentence, the Reports list (model, `--model`,
  `--judge-model`, report link) and the cost notes (judge cost per run, with-plugin
  overhead, suite cost with judge = agent + judge cost from the script).
- Add a Findings paragraph for the model. Ground every claim in the data: grader
  counts from the script, and for solver/method/SNR specifics read the answers in
  `aggregate-result.json` (`cases[].arms.with|without[].graders[].evidence`). Do not
  claim what you did not check.
- If a replaced model's old results folder is no longer linked, ask the user before
  deleting it.
- If the repository README's eval section lists models or counts that changed, fix it.

## 6. Branch and PR

- `git checkout -b eval-<skill>-<model-slug> main` (stash nothing; leave unrelated
  untracked files alone).
- Commit the README and the new results folder only (`aggregate-result.json`,
  `report.html`), message ending with the Co-Authored-By line from the session
  attribution reminder.
- `git push -u origin <branch>` and `gh pr create --base main` with a short body: the
  Δ per case, fire-case mean with vs without, negative-case firing, and the PR
  attribution footer from the session reminder.
- Report the PR link and any caveats (failed graders, errors, unchecked details).
