# Reference

## Architecture

`sim/webapp.py` runs a standard-library HTTP server on port 8000. One Python process owns one AI2-THOR controller through `sim/thor_actions.py` and its `ThorAgent` class.

The console is served from `sim/web/index.html`, `app.js`, `honest.js`, and `style.css`. The `/trace` viewer uses `trace.html`, `trace.js`, and `trace.css`. The interface uses plain HTML, CSS, and JavaScript, with no build step, npm, or framework.

Modules are stdlib-first. Heavy dependencies are imported only where needed.

## Console controls

### Header

The header contains Run, Evaluate, and Setup tabs; state, fps, GPU, and scene indicators; an LLM on/off switch; a Trace link; a theme toggle; and Reset.

The theme follows the system until switched with the toggle. Reset can reload the scene and clear chat, or also erase the knowledge base, memory database, loop reports, and trace store. The latter is not recoverable.

### Run

Enter an instruction in English or Persian and select Run. The Agent switch selects Oracle or Honest.

| Mode | Information available to the agent |
| --- | --- |
| Oracle | The planner and executor read the simulator object list; perceived scene information restricts the planner to trained-detector observations from a look-around |
| Honest | Camera, depth, its own walked map, memory, and simulator-provided pose; all simulator reads pass through the audited gateway |

A fallback from perceived scene information to oracle information is reported as degraded.

Honest mode in this console release runs in FloorPlan1. Its ticket shows Executed, Goal, and Audit results, retries and failure causes per step, events, and the planner's note. The side panel has Map, Memory, Audit, and Simulator truth. Simulator truth is display-only and is never given to the agent. From the set selects a dataset instruction.

Oracle mode has Nav map, Objects, and Learning side panels.

| Control | Behaviour |
| --- | --- |
| Camera views | RGB, Depth, Detect, Map, Map+Nav, Instance, Semantic, and Normals |
| Display menu | Motion detail: fast, normal, or cinematic; resolution |
| Capture controls | Capture, All streams, GIF recording, and Save GIF |
| Image click | Inspect an object |
| Shift-click | Pick up an object |
| Held-object controls | Drop, throw, nudge, and spin |
| Manual drive | Rotate, strafe, move, look up or down, crouch, stand, and WASD keyboard drive |
| Plan panel | L1/L2/L3 chips, step status, good/bad plan ratings, and what the loop learned |
| Transcript | Planner, executor, and simulator supervision messages |

### Evaluate

| Sub-tab | Content |
| --- | --- |
| Instructions | Editable general instruction set with search and CSV export |
| Run & results | Evaluation runs and SR, PC, and TDS per level |
| Scene-grounded set | 102 read-only records across three kitchens |

See [metrics](metrics.md) for definitions and scoring rules.

### Setup

| Group | Controls |
| --- | --- |
| Scene | Scene picker, Materials, Lighting, Shuffle objects, Checkpoint, Restore, Open all, Close all, Lights on, Lights off |
| Perception | Planner senses full/perceived, inspection auto/off/always, Explore navigation, Scan & learn, look inside containers, Train detector |
| Planner | Model pickers and Ollama endpoint |
| Simulator | Health, manual drive step, and rotate sliders |
| Capture library | Saved captures |

### Trace viewer

The viewer is available at `/trace`.

| View | Content |
| --- | --- |
| Timeline | Every event, with filters for type, level, actor, scene, and time window |
| Runs | A waterfall and plan tree for each instruction |
| Lineage | Lineage view |
| Database | Database view |
| Stats | Statistics view |

Every knowledge-base and memory write is attributed to the action that caused it. The provenance follows the spirit of W3C PROV-O and OpenTelemetry spans.

## Agent modules

| Module | Responsibility |
| --- | --- |
| `sim/llm.py` | Provider interface: `LLMProvider`, `OllamaProvider`, `ClaudeProvider`, and `make_provider` |
| `sim/agent_llm.py` | Planner prompts and plan parsing |
| `sim/skills.py` | L1 and L2 prompt skill catalogue and `skills_manifest()` |
| `sim/levels.py`, `sim/eval.py` | Command levels and evaluation |
| `sim/improve.py` | `close_loop`: writes a procedure on success, a lesson on failure, or a fact |
| `sim/knowledge.py` | `KnowledgeBase`, stored in `sim/knowledge_base.json` |
| `sim/rag.py` | `HybridRAG`: keyword and vector retrieval with Ollama `nomic-embed-text`; keyword fallback |
| `sim/agentic_rag.py` | Chunkless retrieval: manifest, lexical probe, bounded expansion, Persian-aware normalization, and FA-to-EN object-type pivot |
| `sim/memory.py` | SQLite `Memory`: episodes, spatial beliefs, failure counters, nav cells, sightings, and `places_seen` |
| `sim/objmem.py` | `ObjectMemory` for the honest agent |
| `sim/select.py` | LinUCB contextual bandit for planning-arm selection |
| `sim/feedback.py` | Human plan ratings, taught facts, and corrections |
| `sim/search.py` | Search logic used with `ThorAgent.search_for` |
| `sim/perception.py` | Per-scene YOLO perception |
| `sim/yolo_recipe.py` | Detector training |
| `sim/honest.py` | `HonestAgent` and audited simulator gateway |
| `sim/honest_skills.py` | `HonestSkills` |
| `sim/honest_map.py` | Honest-agent mapping |
| `sim/honest_console.py` | Honest-agent console integration |

The default planner is `gemma4:e2b-it-q4_K_M`, Gemma 4 E2B in 4-bit form. The provider interface supports any Ollama model.

Loop writes include why, source, and confidence. Every write is logged to an audit file. Strategy rewards come from the environment and human ratings.

### Perception

Released detectors cover FloorPlan1, FloorPlan15, and FloorPlan17.

| Component | Coverage |
| --- | --- |
| Primary YOLO26s | 49 object classes, evaluated every frame |
| YOLO26m look-alike specialist | Fork, Spoon, ButterKnife, Knife, Spatula, SaltShaker, PepperShaker, Plate, Pot, and Pan |
| Seven state classifiers | Broken, cooked, dirty, filled, on, open, and sliced |

`TwoStageDetector` uses the specialist while the agent holds an object up. See [setup](setup.md) for downloads and per-scene training.

## ThorAgent

`ThorAgent` in `sim/thor_actions.py` has about 150 public methods.

```python
ThorAgent(
    scene="FloorPlan1",
    width=600,
    height=600,
    grid_size=0.25,
    rotate_degrees=30.0,
    look_degrees=30.0,
    visibility_distance=1.5,
    field_of_view=90.0,
    render_depth=False,
    render_instance_seg=False,
    render_semantic_seg=False,
    render_normals=False,
    agent_mode="default",
    snap_to_grid=False,
    **controller_kwargs
)
```

### Scene lists

| Constant | Scenes |
| --- | --- |
| `KITCHEN_SCENES` | FloorPlan1–30 |
| `LIVING_ROOM_SCENES` | FloorPlan201–230 |
| `BEDROOM_SCENES` | FloorPlan301–330 |
| `BATHROOM_SCENES` | FloorPlan401–430 |
| `ALL_SCENES` | All 120 rooms |

### Composite skills

Composite skills are generators. Each yield is one rendered frame for the GUI. Drain a skill to run it to completion:

```python
agent.drain(agent.pick_and_place("Apple", "Fridge"))
```

The return value is `True` or `False`, indicating the last action's success.

### Movement

| Methods | Purpose |
| --- | --- |
| `move_ahead(magnitude)`, `move_back(magnitude)`, `move_left(magnitude)`, `move_right(magnitude)` | Move the agent |
| `rotate_left(degrees)`, `rotate_right(degrees)` | Rotate the agent |
| `look_up(degrees)`, `look_down(degrees)` | Change the viewing angle |
| `crouch`, `stand` | Change posture |
| `teleport`, `teleport_full`, `teleport_to_random_reachable` | Teleport the agent |
| `reachable_positions` | Query reachable positions |
| `interactable_poses(object_id)` | Query poses for interacting with an object |

### Interaction by objectId

| Methods | Purpose |
| --- | --- |
| `pickup`, `put(receptacle_id)`, `drop`, `throw` | Pick up, place, drop, or throw an object |
| `move_held`, `rotate_held` | Move or rotate the held object |
| `open(openness)`, `close` | Open or close an object |
| `toggle_on`, `toggle_off` | Change an object's on/off state |
| `slice`, `cook`, `break_object`, `dirty`, `clean` | Change object state |
| `fill_with_liquid(liquid)`, `empty_liquid`, `use_up` | Fill, empty, or use up an object |
| `push`, `pull`, `directional_push(angle)` | Apply a push or pull |
| `do(action, **kwargs)` | Run any raw AI2-THOR action |

### Navigation helpers

| Methods | Purpose |
| --- | --- |
| `go_to` | Teleport to an interactable pose and centre the object |
| `walk_to`, `walk_to_point` | Walk using Move and Rotate primitives |
| `face_object`, `look_at_object`, `turn_to_object`, `aim_at_object` | Orient toward an object |
| `close_in` | Approach an object |
| `path_to`, `steps_to` | Query a path or step count |

### High-level skills by name or type

Names and types use fuzzy matching.

| Methods | Purpose |
| --- | --- |
| `goto`, `pick_up`, `put_in`, `pick_and_place` | Navigate, pick up, and place objects |
| `open_it`, `close_it`, `switch(name, on)` | Open, close, or switch an object |
| `slice_it` | Slice an object |
| `heat_object` | Open the microwave, insert, close, run, reopen, and retrieve |
| `cool_object` | Cool an object using the fridge |
| `wash_object` | Wash an object using the sink and faucet |
| `cook_food` | Cook food |
| `look_around`, `scan_for` | Look or scan as navigation helpers |
| `search_for` | Search until the object is seen, or record ruled-out places |
| `peek_inside` | Look inside a container |
| `open_all`, `close_all`, `switch_all` | Apply an operation across objects |
| `collect_all(object_type, receptacle)` | Collect objects of a type into a receptacle |

### Scene queries

| Methods | Purpose |
| --- | --- |
| `objects`, `object_by_id`, `objects_of_type` | Query objects |
| `visible_objects`, `pickupable_objects`, `receptacles`, `held_object` | Query object subsets or the held object |
| `agent_pose` | Read the agent pose |
| `resolve(name_or_id)`, `find`, `find_nearest`, `find_where(predicate)` | Resolve or find objects |
| `objects_near(target, radius)` | Query nearby objects |
| `objects_in_receptacle`, `whats_in`, `container_chain`, `contents_tree` | Query containment |
| `temperature` | Query temperature |
| `describe` | Produce a compact scene summary for a person or an LLM |
| `is_visible`, `count`, `type_list` | Query visibility, counts, or types |
| `distance_between`, `object_bounds` | Query distance or object bounds |

### State

| Methods | Purpose |
| --- | --- |
| `snapshot`, `diff_state`, `changed_since` | Record or compare state |
| `object_state(name, key)`, `verify(name, key, value)` | Read or verify a state value |
| `checkpoint`, `restore`, `restore_steps` | Save or restore state |

### Sensors and frames

| Methods | Purpose |
| --- | --- |
| `frame`, `depth_frame` | Read RGB or depth in metres |
| `instance_segmentation_frame`, `semantic_segmentation_frame`, `normals_frame` | Read segmentation or normals |
| `instance_masks`, `color_to_object_id` | Access masks and colour-to-object mapping |
| `set_sensors`, `change_resolution` | Configure sensors or resolution |
| `add_top_down_camera`, `map_view_camera_properties`, `update_third_party_camera` | Work with map and third-party cameras |
| `frame_of_kind`, `save_frame`, `capture` | Select or save frames |
| `object_in_frame(x, y)`, `object_in_frame_best` | Identify an object in the image |
| `coordinate_from_raycast`, `depth_backproject(box)` | Obtain spatial coordinates |
| `spawn_coordinates_above_receptacle`, `place_object_at_point` | Obtain placement coordinates or place an object |

### Perception and mapping

| Methods | Purpose |
| --- | --- |
| `detect_objects(detector)` | Detect objects |
| `whats_on(receptacle, detector)` | Detect objects on a receptacle |
| `scan_scene` | Build a per-scene YOLO dataset and navigation map |
| `explore_navigation` | Drive the reachable area into a discovered occupancy map |

### Scene variation

| Methods | Purpose |
| --- | --- |
| `reset(scene)` | Reset to a scene |
| `randomize_materials`, `randomize_lighting`, `randomize_colors` | Vary scene appearance |
| `random_spawn(seed)` | Shuffle objects using a seed |

### Recording and replay

| Methods | Purpose |
| --- | --- |
| `start_recording`, `stop_recording`, `save_gif(path)` | Record frames and save a GIF |
| `start_action_log`, `stop_action_log`, `replay(log)` | Record and replay actions |

### Diagnostics

| Methods | Purpose |
| --- | --- |
| `gpu_status` | Check whether rendering is GPU-accelerated |
| `scene`, `success`, `error` | Inspect the scene and action outcome |

## Honest-agent interfaces

The honest agent acts on screen points, retries up to three times, searches by asking a chooser, and tidies up by closing what it opened.

### HonestSkills

| Method | Interface |
| --- | --- |
| `start_episode` | Start an episode |
| `look_around` | Look around |
| `exec_step(step)` | Return `{ok, cause, retries, detail}` |
| `tidy_up` | Close what the agent opened |
| `viewpoints` | Viewpoints interface |

### HonestAgent

| Method | Interface |
| --- | --- |
| `reset_episode` | Reset the episode |
| `pose` | Read pose |
| `move(prim)` | Execute a movement primitive |
| `observe` | Observe through the gateway |
| `act(action, point, ...)` | Act at a screen point |
| `scoring()` | Context for goal checks |
| `meta()` | Read privileged state only inside scoring; access is audited |

## HTTP API

Endpoints use GET with query parameters and return JSON, except for the live MJPEG stream and viewer page described below. Endpoints without a supplied description are listed by name.

### Status and configuration

| Endpoint | Description |
| --- | --- |
| `/status` | State, fps, scene, pose, plan, log, detectors, honest, motion, and llm |
| `/defaults` | Endpoint, model, and scenes |

Other endpoints: `/llm`, `/models`, `/setmodel`, `/resolution`, `/setparam`.

### Scene and manual control

| Endpoint | Description |
| --- | --- |
| `/scene?name=FloorPlan201` | Load a scene |
| `/motion?speed=fast\|normal\|cinematic` | Set motion detail |

Other endpoints: `/drive?action=move_ahead|...&on=1|0`, `/action`, `/click`, `/held`, `/checkpoint`, `/restore`, `/randomize`, `/reset`, `/act_obj`.

### Instructions and honest mode

| Endpoint | Description |
| --- | --- |
| `/cmd?text=...&model=...&endpoint=...` | Run an instruction in oracle mode |
| `/honest?on=1\|0` | Switch honest mode on or off |
| `/honest_run?text=...` | Run an instruction in honest mode |

Other endpoints: `/honest_stop`, `/honest_look`, `/batch`, `/demo`.

### Views and captures

| Endpoint | Description |
| --- | --- |
| `/stream` | MJPEG stream of the live camera |
| `/view?mode=rgb\|depth\|detect\|map\|mapnav\|instance\|semantic\|normals` | Select a camera view |

Other endpoints: `/record?on=1|0`, `/save_gif`, `/capture`, `/gallery`, `/cap_img`.

### Perception and navigation

| Endpoint | Description |
| --- | --- |
| `/perception?mode=oracle\|perceived` | Select planner scene information |

Other endpoints: `/objects`, `/navmap`, `/explore`, `/scan`, `/train`, `/inspect`, `/perception_feedback`.

### Evaluation and datasets

| Endpoint | Description |
| --- | --- |
| `/general` | General instruction set |

Other endpoints: `/general_export`, `/eval_run`, `/eval_status`, `/eval_results`, `/dataset`.

### Learning, memory, and traces

| Endpoint | Description |
| --- | --- |
| `/trace` | Trace viewer |

Other endpoints: `/rating`, `/teach`, `/episodes`, `/export`, `/bandit`, `/loop`.

Every new endpoint requires a matching bump to `WEBAPP_API` in `sim/webapp.py` and `UI_API` in `sim/web/app.js`. Both are currently `7`. An older server can otherwise serve a page with an empty panel and no error.
