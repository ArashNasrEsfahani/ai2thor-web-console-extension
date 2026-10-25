# Command levels and evaluation metrics

The command hierarchy separates atomic actions, ordered procedures, and abstract goals. Each level has its own metric, implemented in `sim/levels.py` and `sim/eval.py`.

| Level | Command type | Metric |
| --- | --- | --- |
| L1 | Atomic: one command, one function | Success Rate (SR) |
| L2 | Sequential: an ordered chain | Procedural Correctness (PC) |
| L3 | Abstract goal: requires decomposition | Task Decomposition Score (TDS) |

## L1: success rate

Success Rate is the fraction of episodes that succeed:

$$
\mathrm{SR} = \frac{\text{successful episodes}}{\text{episodes}}
$$

## L2: procedural correctness

Procedural Correctness compares the predicted action sequence with the gold sequence. It uses normalized Levenshtein distance:

$$
\mathrm{PC} =
1 - \frac{\operatorname{Lev}(\text{predicted}, \text{gold})}
{\max(|\text{predicted}|, |\text{gold}|)}
$$

Here, $\operatorname{Lev}$ is the Levenshtein distance, and $|\cdot|$ is the sequence length. The comparison preserves action order.

## L3: task decomposition score

Task Decomposition Score is the F1 score over action sets. Let $A_{\mathrm{pred}}$ be the predicted set and $A_{\mathrm{gold}}$ the gold set:

$$
P = \frac{|A_{\mathrm{pred}} \cap A_{\mathrm{gold}}|}{|A_{\mathrm{pred}}|}
\qquad
R = \frac{|A_{\mathrm{pred}} \cap A_{\mathrm{gold}}|}{|A_{\mathrm{gold}}|}
$$

$$
\mathrm{TDS} = \frac{2PR}{P+R}
$$

This compares sets of actions rather than their order.

## Apply the applicability gate

A record is reported as **skipped**, not failed, when its required object is absent from the scene or its goal is already true at reset.

The command-line option `--gate on|off` controls this gate.

## Understand the scored actions

`search_for` is scored. It recalls the object's last sighting, consults the knowledge base or a containment prior, walks to candidate locations, and opens closed containers. It succeeds only when the object is actually seen. A failed search records a lesson naming the places it ruled out.

`look_around` and `scan_for` are navigation helpers and are not scored.

Use `--score-search off` to restore the older action space.

## Choose an instruction set

| File | Contents |
| --- | --- |
| `sim/dataset/general.json` | 281 scene-agnostic instructions in English and Persian: 562 language records |
| `sim/dataset/commands.jsonl` | 102 scene-grounded records across FloorPlan1–3 |
| `sim/dataset/scene_inventory.json` | A live scan of the 30 kitchens |

The general set has 109 L1, 108 L2, and 64 L3 instructions. Each instruction has a reference plan, an optional setup, and a text goal such as `Apple in Fridge` or `any Cabinet.isOpen = true`. Gold labels are derived from the reference plan.

In the Evaluate tab, Instructions provides the editable general set. Run & results starts evaluations and shows SR, PC, and TDS by level. Scene-grounded set contains the 102 read-only records.

## Run an evaluation

Evaluation requires the simulator. Run Python from the repository root in the configured Linux or WSL environment:

```sh
python sim/eval.py --models gemma4:e2b-it-q4_K_M --rag agentic --loop off --lang en --scenes FloorPlan1
```

| Option | Values |
| --- | --- |
| `--rag` | `off`, `keyword`, `hybrid`, `probe`, `agentic`, `full` |
| `--loop` | `on`, `off` |
| `--perception` | `oracle`, `perceived` |
| `--lang` | `en`, `fa`, `all` |
| `--gate` | `on`, `off` |

The example is an evaluation command, not a reported result.
