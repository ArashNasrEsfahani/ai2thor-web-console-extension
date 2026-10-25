#!/usr/bin/env bash
# Start the AI2-THOR web console (Linux, or WSL2 on Windows).
#
#   scripts/start_console.sh              # planner on (needs Ollama)
#   scripts/start_console.sh --no-llm     # drive the simulator by hand only; nothing contacts Ollama
#
# Environment overrides:
#   PYTHON=~/thor-env/bin/python   the interpreter that has ai2thor + ultralytics (default: python3)
#   OLLAMA_URL=http://host:11434   where Ollama listens (default: auto-detected)
#   OLLAMA_MODEL=gemma4:e2b-it-q4_K_M
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
SIM="$HERE/sim"

# AI2-THOR needs an X display. On WSL2, WSLg provides :0 and Mesa's D3D12 driver renders on the GPU; force the
# NVIDIA adapter there (without it Mesa picks the integrated GPU or falls back to the CPU).
export DISPLAY="${DISPLAY:-:0}"
if grep -qi microsoft /proc/version 2>/dev/null; then
  export MESA_D3D12_DEFAULT_ADAPTER_NAME="${MESA_D3D12_DEFAULT_ADAPTER_NAME:-NVIDIA}"
  ON_WSL=1
else
  ON_WSL=0
fi

# Find Ollama: localhost first; on WSL, Ollama usually runs on Windows, reachable at the host's gateway address
# (start Ollama on Windows with OLLAMA_HOST=0.0.0.0 so it listens beyond localhost).
probe() { curl -s -m 3 "$1/api/version" >/dev/null 2>&1; }
if [ -z "${OLLAMA_URL:-}" ]; then
  OLLAMA_URL="http://127.0.0.1:11434"
  if ! probe "$OLLAMA_URL" && [ "$ON_WSL" = 1 ]; then
    HOSTIP="$(ip route show default 2>/dev/null | awk '{print $3; exit}')"
    [ -n "$HOSTIP" ] && probe "http://$HOSTIP:11434" && OLLAMA_URL="http://$HOSTIP:11434"
  fi
fi
export OLLAMA_URL                                  # the retriever's embeddings use the same Ollama (sim/rag.py)
if probe "$OLLAMA_URL"; then echo "Ollama: $OLLAMA_URL"; else echo "Ollama not reachable at $OLLAMA_URL (the console still runs; the planner needs it)"; fi

# Write the endpoint into sim/gui_config.json (created from the example the first time).
[ -f "$SIM/gui_config.json" ] || cp "$SIM/gui_config.example.json" "$SIM/gui_config.json"
"$PYTHON" - "$SIM/gui_config.json" "$OLLAMA_URL" "${OLLAMA_MODEL:-}" <<'PY'
import json, sys
path, endpoint, model = sys.argv[1], sys.argv[2], sys.argv[3]
cfg = json.load(open(path))
cfg["endpoint"] = endpoint
if model:
    cfg["model"] = model
json.dump(cfg, open(path, "w"), indent=2)
PY

[ -d "$SIM/weights/v3" ] || echo "No detector weights yet: run  $PYTHON scripts/download_weights.py  (needed for the honest agent)"
cd "$SIM"
echo "Starting the console: open http://localhost:8000"
exec "$PYTHON" webapp.py "$@"
