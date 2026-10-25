# Setup

The simulator requires Linux with an X display, or Windows 11 with WSL2 and WSLg. Use Python 3.10 and AI2-THOR 5.0.0.

Setup was verified on Windows 11 with WSL2 Ubuntu 22.04 and an NVIDIA RTX 4060 Laptop GPU with 8 GB of memory. Offline self-tests can run on any OS with Python 3.10 or later.

Run Python from the repository root. Running from `sim/` can make `sim/trace.py` shadow the standard-library `trace` module.

## Install the environment

1. On Windows, install Ubuntu from a real Windows terminal:

   ```powershell
   wsl --install -d Ubuntu-22.04
   ```

   This command hangs when run non-interactively.

2. Inside Ubuntu, install the system packages:

   ```sh
   sudo apt update && sudo apt install -y python3 python3-venv python3-pip python3-dev build-essential git mesa-utils libgl1 libglib2.0-0
   ```

3. Create and activate the Python environment:

   ```sh
   python3 -m venv ~/thor-env && source ~/thor-env/bin/activate && pip install --upgrade pip wheel
   ```

4. Install PyTorch first, matching your CUDA driver. On WSL with a CUDA 12.x driver, use:

   ```sh
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
   ```

   The default wheel may target a newer CUDA version than the driver supports.

5. Install the repository requirements from the repository root:

   ```sh
   pip install -r requirements.txt
   ```

Keep the virtual environment and AI2-THOR cache in the Linux home directory. Paths under `/mnt/c` or `/mnt/d` have slower cross-filesystem I/O. Keeping the repository under `/mnt/d` is fine.

A Conda environment is also provided:

```sh
conda env create -f environment.yml
```

Its name is `thor-ext`.

AI2-THOR downloads its Unity build on the first run. The download is about 770 MB and is stored in `~/.ai2thor`.

## Check WSL rendering

WSL2 renders through WSLg's X server and Mesa's D3D12 driver. Two environment variables are required:

| Variable | Value |
| --- | --- |
| `DISPLAY` | `:0` |
| `MESA_D3D12_DEFAULT_ADAPTER_NAME` | `NVIDIA` |

Without the adapter setting, Mesa can select the integrated GPU or CPU.

Check the renderer:

```sh
MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA DISPLAY=:0 glxinfo -B | grep -iE 'Device:|renderer string'
```

The output should name your NVIDIA GPU.

CloudRendering uses Vulkan and does not work on WSL2 with NVIDIA in this setup. There is no NVIDIA Vulkan ICD there, so it falls back to CPU rendering.

Do not install Linux NVIDIA drivers inside WSL. `nvidia-smi` inside WSL uses the Windows driver.

Keep the laptop display on during long or unattended runs. If the display turns off while the simulator starts, AI2-THOR can start without the GPU rendering path. Symptoms include software rendering, high CPU use, and rendering glitches.

## Set up Ollama

Install Ollama on Windows or Linux. Pull the default planner model:

```sh
ollama pull gemma4:e2b-it-q4_K_M
```

This is Gemma 4 E2B in 4-bit form.

Embeddings for retrieval are optional:

```sh
ollama pull nomic-embed-text
```

Hybrid retrieval falls back to keywords when embeddings are unavailable.

When Ollama runs on Windows and the console runs in WSL, set the Windows environment variable `OLLAMA_HOST=0.0.0.0` and restart Ollama. WSL reaches Windows through the gateway address shown by:

```sh
ip route show default
```

The launcher finds that address automatically. `OLLAMA_URL` overrides its choice.

From Windows PowerShell, use `http://127.0.0.1:11434`. PowerShell tries IPv6 `::1` first when given `localhost`.

Models larger than about 8 GB will not load alongside AI2-THOR on an 8 GB GPU.

## Download the detectors

Run this from the repository root:

```sh
python scripts/download_weights.py
```

This downloads 27 files for FloorPlan1, FloorPlan15, and FloorPlan17, about 406 MB in total.

A single kitchen needs about 136 MB:

```sh
python scripts/download_weights.py --kitchen FloorPlan1
```

List downloads without fetching them:

```sh
python scripts/download_weights.py --list
```

Weights are stored in the git-ignored `sim/weights/v3/` directory. Every file is checked against the published `SHA256SUMS`.

The releases are under [ArashNasr on Hugging Face](https://huggingface.co/ArashNasr):

| Resource | Repository names |
| --- | --- |
| Detectors | `ai2thor-kitchen-perception-floorplan1`, `ai2thor-kitchen-perception-floorplan15`, `ai2thor-kitchen-perception-floorplan17` |
| Perception datasets | `ai2thor-kitchen-dataset-floorplan1`, `ai2thor-kitchen-dataset-floorplan15`, `ai2thor-kitchen-dataset-floorplan17` |
| Instructions | `ai2thor-kitchen-instructions` |

Each released kitchen has a primary YOLO26s detector with 49 object classes, a YOLO26m look-alike specialist, and seven state classifiers.

## Start the console

On Windows, double-click `START-CONSOLE.bat`. It runs `scripts/start_console.sh` in WSL distribution `Ubuntu-22.04`, using `~/thor-env/bin/python`. It waits for the server and opens [http://localhost:8000](http://localhost:8000).

`WSLDISTRO` overrides the distribution. `THOR_PYTHON` overrides the Python path. The launcher accepts `--no-llm`.

On Linux or inside WSL, run:

```sh
PYTHON=~/thor-env/bin/python scripts/start_console.sh
```

The script sets the display and Mesa variables on WSL, finds Ollama, writes `sim/gui_config.json` from `sim/gui_config.example.json`, and starts `sim/webapp.py`.

Open [http://localhost:8000](http://localhost:8000). On the verified machine, the WSL IP URL stalled in browsers while `localhost` worked.

Use `--no-llm` or `WEBAPP_NO_LLM=1` for manual driving without Ollama. Nothing contacts Ollama in this mode.

Only one AI2-THOR controller should run at a time on an 8 GB GPU. Stop the console before running another simulator script.

## Choose a scene and agent

The Setup scene picker groups all 120 iTHOR rooms:

| Room type | Scenes |
| --- | --- |
| Kitchens | `FloorPlan1`–`FloorPlan30` |
| Living rooms | `FloorPlan201`–`FloorPlan230` |
| Bedrooms | `FloorPlan301`–`FloorPlan330` |
| Bathrooms | `FloorPlan401`–`FloorPlan430` |

Oracle mode reads simulator object information. Its planner can instead use perceived scene information from the trained detector. Any fallback to oracle information is reported as degraded.

Honest mode in this console release runs in FloorPlan1. It uses camera and depth observations, its own walked map, and memory. Maps and detectors ship for FloorPlan1, FloorPlan15, and FloorPlan17.

For other scenes, Scan & learn collects a per-scene YOLO dataset. It opens cabinets, fridges, and drawers to photograph their contents. Train detector trains the detector through `sim/yolo_recipe.py`.

A new walked map can be built with:

```sh
python scripts/build_map.py FloorPlan6
```

This requires the simulator. The map builder uses a depth-first walk with `MoveAhead` and 90-degree turns. It uses only its own pose and whether each move succeeded, then reports coverage. Maps live at `sim/step4/<scene>.map.json`.

## Check the offline code

```sh
python scripts/run_selftests.py
```

The runner executes 17 suites without the simulator, GPU, or Ollama. A subset can be selected by name:

```sh
python scripts/run_selftests.py step4
```

## Know what is saved

These console outputs are git-ignored:

| Path | Content |
| --- | --- |
| `sim/knowledge_base.json` | Knowledge base; starts empty when missing |
| `sim/memory.db` | Memory database |
| `sim/trace.db` | Trace store |
| `sim/loop_reports.jsonl` | Loop reports |
| Audit logs | Records of writes and audited access |
| `sim/captures/` | Captures |
| `sim/step4/console_*` | Honest-console files |

The header Reset control has two choices. **Scene + chat** reloads the scene and clears the transcript. **Everything** also wipes the knowledge base, memory database, loop reports, and trace store. That reset is not recoverable.

The console checks frames for colour casts and pure-white render corruption. On a glitch, it restarts the simulator in a fresh process, restores the scene and position, and reports the restart.
