"""Let the agent build its own floor map of a kitchen by walking it (needs the simulator: Linux or WSL2).

    python scripts/build_map.py FloorPlan1        # writes sim/step4/FloorPlan1.map.json (+ .map.png, .map_report.json)

The agent explores depth-first with MoveAhead and 90-degree turns, using only its own pose and whether each move
succeeded; the simulator's list of reachable positions is read once, after the build, to report coverage. The honest
agent plans its walks on this map. Maps for FloorPlan1, FloorPlan15 and FloorPlan17 ship with the repository.
"""
import json
import os
import sys
import time

SIM = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sim")
sys.path.insert(0, SIM)
from thor_actions import ThorAgent  # noqa: E402
import honest                       # noqa: E402
import honest_map as hm             # noqa: E402

OUT = os.path.join(SIM, "step4")
scene = sys.argv[1] if len(sys.argv) > 1 else "FloorPlan1"
t0 = time.time()
thor = ThorAgent(scene, grid_size=0.25)          # no vision needed to map: pose + move success only
h = honest.HonestAgent(thor, detector=object(), mode="honest")   # stub detector: never called while mapping
h.reset_episode("build-map")
log = lambda m: print(f"[{time.time() - t0:6.1f}s] {m}", flush=True)
p0 = h.pose()
log(f"start pose {p0['position']} yaw {p0['rotation']['y']}")
gm = hm.explore(h, scene, log=log)
log(f"build {gm.info['status']}: free={len(gm.free)} blocked_edges={len(gm.blocked_edges)} sends={gm.info['sends']}")
gm.info["built_s"] = round(time.time() - t0, 1)
gm.info["config"] = {"gridSize": 0.25, "snapToGrid": False, "agentMode": "default", "scene": scene}
os.makedirs(OUT, exist_ok=True)
path = gm.save(os.path.join(OUT, f"{scene}.map.json"))
log(f"saved {path}")

# walking check on the agent's own map: to the farthest cell (by its own A*) and back
start = gm.cell_of(gm.info["start"]["x"], gm.info["start"]["z"])
far = max(gm.free, key=lambda c: len(gm.astar(start, [c]) or []))
r1 = hm.walk_path(h, gm, gm.astar(start, [far]))
r2 = hm.walk_path(h, gm, None, goals=[start])
log(f"walk to farthest {far}: {r1}; back: {r2}")

# report only: the simulator's reachable positions, read once after the build
ref = h.reachable_positions()
cov = hm.coverage(gm, ref)
cov["missed_reference"] = [list(c) for c in cov["missed_reference"]]
hm.render_png(gm, os.path.join(OUT, f"{scene}.map.png"), ref,
              title=f"{scene}: own map {cov['matched']}/{cov['reference_cells']} reachable cells ({cov['coverage']:.0%})")
gm.save(path)                                        # blocked edges learned while walking
report = {"scene": scene, "info": gm.info, "coverage": cov, "walk_far": {**r1, "cell": list(r1["cell"])},
          "walk_back": {**r2, "cell": list(r2["cell"])}, "audit": h.audit.summary(),
          "violations": h.audit.invalid, "elapsed_s": round(time.time() - t0, 1)}
json.dump(report, open(os.path.join(OUT, f"{scene}.map_report.json"), "w"), indent=1, default=str)
print(json.dumps({k: v for k, v in cov.items() if k != "missed_reference"}, indent=1))
print("audit", h.audit.summary())
thor.stop()
