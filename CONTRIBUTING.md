# Contributing

Run Python commands from the repository root. Running from `sim/` can make `sim/trace.py` shadow Python's standard-library `trace` module.

## Run the self-tests

The offline self-tests need Python 3.10 or later on any OS. They do not need the simulator, a GPU, or Ollama.

```sh
python scripts/run_selftests.py
```

The runner executes 17 suites and prints one line for each: detector, eval, motion, phase6, phase6a, phase7, scan, search, step4_act, step4_gemma, step4_inhand_points, step4_map, step4_memory, step4_refplans, step4_rules, step4_tidy_e1, and trace.

A name filter runs a subset:

```sh
python scripts/run_selftests.py step4
```

Modules use standard-library imports first. Heavy packages such as `ai2thor`, `ultralytics`, `torch`, and `numpy` are imported only where needed. Preserve this so offline tests continue to run with plain Python.

## Keep the research contracts visible

- Keep L1, L2, and L3 visible in data, prompts, and evaluation.
- Use English and Persian by default.
- Keep LLM providers behind the interface in `sim/llm.py`.
- Keep every knowledge-base and memory write auditable, including what was written and why.
- Keep honest-agent simulator reads inside the gateway in `sim/honest.py`.

The static checks in `sim/_step4_rules_selftest.py` enforce the honest-agent access rule. Simulator truth shown in the console is for display only. It must not become input to the honest agent.

See [the metrics guide](docs/metrics.md) for scoring rules.

## Run simulator code

Any script that opens an AI2-THOR controller must run on Linux or WSL with the display variables set. On WSL with NVIDIA, these are `DISPLAY=:0` and `MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA`.

Use one controller at a time on an 8 GB GPU. Stop the console before running another simulator script. See [setup](docs/setup.md) for the environment and rendering requirements.

## Keep the HTTP API versions together

Every new endpoint requires a matching version bump in both places:

| Constant | File | Current value |
| --- | --- | --- |
| `WEBAPP_API` | `sim/webapp.py` | `7` |
| `UI_API` | `sim/web/app.js` | `7` |

A page served by an older server can otherwise show an empty panel without an error.

## Understand generated files

The console writes git-ignored state to `sim/knowledge_base.json`, `sim/memory.db`, `sim/trace.db`, `sim/loop_reports.jsonl`, audit logs, `sim/captures/`, and `sim/step4/console_*`.

The knowledge base starts empty when its file is missing. Knowledge-base and memory writes must retain their attribution to the action that caused them.

## Find research design notes

Some code comments cite design notes as `docs/<name>.md`. Those notes belong to the [MISE research repository's documentation](https://github.com/ArashNasrEsfahani/MISE/tree/main/docs), where they exist.
