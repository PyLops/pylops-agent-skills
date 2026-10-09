"""Print the README tables for one eval suite from `claude plugin eval` results.

Reads the `aggregate-result.json` of one run per agent model and prints, in
the layout used by the eval findings READMEs (`plugins/*/evals/README.md`):

- the results table (score with and without the plugin, and Δ, per case);
- the cost table (mean agent cost, wall time and turns per run, per case);
- per model: how often the skill was called, grader pass counts on the fire
  cases (overall, and split by whether the skill was loaded), negative cases
  where the skill fired, errors, judge cost and wall time.

Cases whose name contains "-neg-" are negative cases; the others are fire
cases. Each argument is LABEL=RESULTS_DIR, with LABEL the model name as it
should appear in the tables (with its version, e.g. "Haiku 5.5"):

    python scripts/eval_tables.py \
        "Opus 5.5=plugins/pylops/evals/results/<timestamp>" \
        "Haiku 5.5=plugins/pylops/evals/results/<timestamp>"
"""

import json
import sys
from pathlib import Path


# column order of the per-model grader table
GROUPS = ("with", "with, skill loaded", "with, skill not loaded", "without")


def fmt(x):
    return f"{x:.2f}"


def fmt_delta(x):
    s = f"{x:+.2f}".replace("-", "−")
    return "0.00" if s in ("+0.00", "−0.00") else s


def is_neg(name):
    return "-neg-" in name


def skill_grader(graders, with_only):
    """The `tool_used: Skill` grader: with_only=True is the fire-case trigger,
    with_only=False the scored "must not fire" check of a negative case."""
    return next(
        (
            g
            for g in graders
            if g["explanation"].startswith("Skill called")
            and g["withOnly"] == with_only
        ),
        None,
    )


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def load(arg):
    label, path = arg.split("=", 1)
    path = Path(path)
    if path.is_dir():
        path = path / "aggregate-result.json"
    data = json.loads(path.read_text())
    return label, data, {c["name"]: c for c in data["cases"]}


def results_table(runs, names):
    fire = [n for n in names if not is_neg(n)]
    span = f"`{fire[0][:6]}`–`{fire[-1][:6]}`"
    print("| Case | " + " | ".join(f"{lb} with | {lb} without | {lb} Δ" for lb, _, _ in runs) + " |")
    print("| ---- | " + " | ".join("---- | ---- | ----" for _ in runs) + " |")
    for n in names:
        row = []
        for _, _, cases in runs:
            a = cases[n]["aggregates"]
            row += [fmt(a["score"]), fmt(a["scoreWithout"]), fmt_delta(a["delta"])]
        print(f"| `{n}` | " + " | ".join(row) + " |")
    for title, sel in (("Mean (all cases)", names), (f"Mean (fire cases {span})", fire)):
        cells = [
            f" | | **{fmt_delta(mean([cases[n]['aggregates']['delta'] for n in sel]))}**"
            for _, _, cases in runs
        ]
        print(f"| **{title}** |" + " |".join(cells) + " |")
    print()
    for lb, _, cases in runs:
        w = mean([cases[n]["aggregates"]["score"] for n in fire])
        wo = mean([cases[n]["aggregates"]["scoreWithout"] for n in fire])
        print(f"{lb}: mean score on fire cases with {w:.3f}, without {wo:.3f}")


def cost_table(runs, names):
    arms = ("with", "without")
    print("| Case | " + " | ".join(f"{lb} {a}" for lb, _, _ in runs for a in arms) + " |")
    print("| ---- | " + " | ".join("----" for _ in runs for _ in arms) + " |")
    fire, total = {}, {}
    for n in names:
        row = []
        for lb, _, cases in runs:
            for a in arms:
                rs = cases[n]["arms"][a]
                cost = mean([r["costUsd"] for r in rs])
                row.append(
                    f"${cost:.2f} · {mean([r['durationSeconds'] for r in rs]):.0f} s"
                    f" · {mean([r['turns'] for r in rs]):.1f}"
                )
                total[lb, a] = total.get((lb, a), 0) + sum(r["costUsd"] for r in rs)
                if not is_neg(n):
                    fire[lb, a] = fire.get((lb, a), 0) + cost
        print(f"| `{n}` | " + " | ".join(row) + " |")
    for title, d in (("Fire cases, sum per run", fire), ("Whole suite, all runs per arm", total)):
        print(f"| **{title}** | " + " | ".join(f"**${d[lb, a]:.2f}**" for lb, _, _ in runs for a in arms) + " |")


def grader_counts(runs, names):
    for lb, data, cases in runs:
        print(f"\n## {lb}  (model override: {data['suite'].get('modelOverride')}, "
              f"judge: {data['suite'].get('judgeModel')})")
        counts, scores, trig, neg_fired, judge = {}, {}, {}, {}, {"fire": [], "neg": []}
        for n in names:
            for arm, rs in cases[n]["arms"].items():
                for r in rs:
                    judge["neg" if is_neg(n) else "fire"].append(r["judgeCostUsd"])
                    if is_neg(n):
                        g = skill_grader(r["graders"], with_only=False)
                        if arm == "with" and g is not None:
                            neg_fired.setdefault(n, []).append(not g["passed"])
                        continue
                    t = skill_grader(r["graders"], with_only=True)
                    run_groups = [arm]
                    if arm == "with" and t is not None:
                        trig.setdefault(n, []).append(t["passed"])
                        run_groups.append("with, skill loaded" if t["passed"] else "with, skill not loaded")
                    for grp in run_groups:
                        scores.setdefault(grp, []).append(r["score"])
                        for g in r["graders"]:
                            if g["scored"]:
                                c = counts.setdefault((grp, g["name"]), [0, 0])
                                c[0] += bool(g["passed"])
                                c[1] += 1
        fired = [x for v in trig.values() for x in v]
        print(f"skill called on fire cases: {sum(fired)}/{len(fired)}  "
              + ", ".join(f"{n[:6]} {sum(v)}/{len(v)}" for n, v in trig.items()))
        print("skill fired on negative cases: "
              + ", ".join(f"{n[:6]} {sum(v)}/{len(v)}" for n, v in neg_fired.items()))
        groups = [g for g in GROUPS if g in scores]
        for grp in groups:
            print(f"mean score, fire runs, {grp}: {mean(scores[grp]):.3f} ({len(scores[grp])} runs)")
        grader_names = sorted({k[1] for k in counts})
        print("\n| Fire runs | " + " | ".join(groups) + " |")
        print("| --------- | " + " | ".join("----" for _ in groups) + " |")
        for gn in grader_names:
            cells = [f"{counts[g, gn][0]}/{counts[g, gn][1]}" if (g, gn) in counts else "–" for g in groups]
            print(f"| `{gn}` | " + " | ".join(cells) + " |")
        errors = [
            f"{c['name'][:6]} [{arm}]: {r['error']}"
            for c in data["cases"] for arm, rs in c["arms"].items() for r in rs if r["error"]
        ]
        print("\nerrors:", errors or "none")
        for k, v in judge.items():
            if v:
                print(f"judge cost per {k} run: ${min(v):.2f}–{max(v):.2f}")
        print(f"agent cost (both arms, judge excluded): ${data['costUsd']:.2f}, "
              f"judge: ${sum(judge['fire'] + judge['neg']):.2f}, wall time {data['durationSeconds']} s")


def main(args):
    if not args:
        sys.exit(__doc__)
    runs = [load(a) for a in args]
    names = [c["name"] for c in runs[0][1]["cases"]]
    for lb, _, cases in runs[1:]:
        if set(cases) != set(names):
            sys.exit(f"{lb}: different cases from {runs[0][0]}")
    results_table(runs, names)
    print()
    cost_table(runs, names)
    grader_counts(runs, names)


if __name__ == "__main__":
    main(sys.argv[1:])
